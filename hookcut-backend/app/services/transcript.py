import subprocess
import json
import os
import shutil
import tempfile
import logging
import http.cookiejar
from dataclasses import dataclass
from typing import Optional

from app.utils.ffmpeg_commands import _ensure_cookies_file, _COOKIES_PATH

logger = logging.getLogger(__name__)


@dataclass
class TranscriptResult:
    text: str
    provider: str  # "youtube_transcript_api", "ytdlp_subtitles", "whisper_api"
    language_detected: Optional[str] = None


class TranscriptService:
    """
    3-provider cascade for transcript acquisition.
    1. youtube-transcript-api (primary)
    2. yt-dlp subtitle extraction (fallback 1)
    3. OpenAI Whisper API (fallback 2)
    All fail → None returned, no credits deducted.
    """

    def fetch(self, video_id: str, language: str = "English") -> Optional[TranscriptResult]:
        result = self._try_youtube_transcript_api(video_id, language)
        if result:
            logger.info(f"Transcript via youtube-transcript-api for {video_id}")
            return result

        result = self._try_ytdlp_subtitles(video_id, language)
        if result:
            logger.info(f"Transcript via yt-dlp subtitles for {video_id}")
            return result

        from app.config import get_settings
        if get_settings().FEATURE_WHISPER_FALLBACK:
            result = self._try_whisper_api(video_id, language)
            if result:
                logger.info(f"Transcript via Whisper API for {video_id}")
                return result

        logger.warning(f"All transcript providers failed for {video_id}")
        return None

    def _try_youtube_transcript_api(
        self, video_id: str, language: str
    ) -> Optional[TranscriptResult]:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from app.config import get_settings

            settings = get_settings()

            # Strategy: cookies (most reliable) > proxy > direct
            cookies_path = _ensure_cookies_file()
            kwargs = {}
            if os.path.exists(cookies_path):
                import requests
                session = requests.Session()
                cj = http.cookiejar.MozillaCookieJar(cookies_path)
                cj.load(ignore_discard=True, ignore_expires=True)
                session.cookies = cj
                kwargs["http_client"] = session
                logger.info("Using cookies.txt for transcript fetch")
            elif settings.YTDLP_PROXY:
                from youtube_transcript_api.proxies import GenericProxyConfig
                kwargs["proxy_config"] = GenericProxyConfig(
                    http_url=settings.YTDLP_PROXY,
                    https_url=settings.YTDLP_PROXY,
                )
            ytt_api = YouTubeTranscriptApi(**kwargs)

            lang_codes = self._get_lang_codes(language)
            transcript_list = ytt_api.list(video_id)

            transcript = None
            for code in lang_codes:
                try:
                    transcript = transcript_list.find_transcript([code])
                    break
                except Exception:
                    logger.debug("Transcript variant %s not found for %s", code, video_id)
                    continue

            if transcript is None:
                try:
                    transcript = transcript_list.find_transcript(["en"])
                except Exception:
                    logger.debug("Transcript variant en not found for %s", video_id)
                    for t in transcript_list:
                        if t.is_generated:
                            transcript = t
                            break

            if transcript is None:
                return None

            fetched = transcript.fetch()
            lines = []
            for snippet in fetched:
                start = snippet.start
                minutes = int(start // 60)
                seconds = start % 60
                ts = f"[{minutes}:{seconds:05.2f}]"
                lines.append(f"{ts} {snippet.text}")

            text = "\n".join(lines)
            if len(text.strip()) < 50:
                return None

            return TranscriptResult(
                text=text,
                provider="youtube_transcript_api",
                language_detected=fetched.language_code,
            )
        except Exception as e:
            logger.warning(f"youtube-transcript-api failed for {video_id}: {e}")
            return None

    def _try_ytdlp_subtitles(
        self, video_id: str, language: str
    ) -> Optional[TranscriptResult]:
        work_dir = tempfile.mkdtemp(prefix="hookcut_subs_")
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            output_template = os.path.join(work_dir, "subs")

            from app.utils.ffmpeg_commands import _ytdlp_base_args
            cmd = [
                "yt-dlp",
                *_ytdlp_base_args(),
                "--write-auto-sub",
                "--sub-lang", "en",
                "--sub-format", "json3",
                "--skip-download",
                "--output", output_template,
                url,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                logger.warning(f"yt-dlp subtitles cmd failed for {video_id}: {result.stderr[:300]}")

            sub_file = None
            for f in os.listdir(work_dir):
                if f.endswith((".json3", ".vtt", ".srt")):
                    sub_file = os.path.join(work_dir, f)
                    break

            if sub_file is None:
                logger.warning(f"yt-dlp subtitles: no subtitle file found for {video_id}")
                return None

            if sub_file.endswith(".json3"):
                text = self._parse_json3(sub_file)
            else:
                with open(sub_file, "r", encoding="utf-8") as fh:
                    text = fh.read()

            if not text or len(text.strip()) < 50:
                return None

            return TranscriptResult(text=text, provider="ytdlp_subtitles")
        except Exception as e:
            logger.debug(f"yt-dlp subtitles failed for {video_id}: {e}")
            return None
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def _try_whisper_api(
        self, video_id: str, language: str
    ) -> Optional[TranscriptResult]:
        work_dir = tempfile.mkdtemp(prefix="hookcut_whisper_")
        try:
            from openai import OpenAI
            from app.config import get_settings
            settings = get_settings()

            url = f"https://www.youtube.com/watch?v={video_id}"
            audio_path = os.path.join(work_dir, "audio.m4a")

            # Download audio only (not full video)
            from app.utils.ffmpeg_commands import _ytdlp_base_args
            cmd = [
                "yt-dlp",
                *_ytdlp_base_args(),
                "-f", "bestaudio[ext=m4a]/bestaudio",
                "--output", audio_path,
                url,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0 or not os.path.exists(audio_path):
                return None

            # Whisper API: 25MB limit
            file_size = os.path.getsize(audio_path)
            if file_size > 25 * 1024 * 1024:
                logger.warning(f"Audio too large for Whisper: {file_size} bytes")
                return None

            client = OpenAI(api_key=settings.effective_whisper_key)
            with open(audio_path, "rb") as audio_file:
                whisper_resp = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )

            lines = []
            if hasattr(whisper_resp, "segments") and whisper_resp.segments:
                for seg in whisper_resp.segments:
                    start = seg["start"]
                    minutes = int(start // 60)
                    seconds = start % 60
                    ts = f"[{minutes}:{seconds:05.2f}]"
                    lines.append(f"{ts} {seg['text'].strip()}")
            else:
                lines.append(whisper_resp.text)

            text = "\n".join(lines)
            if len(text.strip()) < 50:
                return None

            return TranscriptResult(
                text=text,
                provider="whisper_api",
                language_detected=getattr(whisper_resp, "language", None),
            )
        except Exception as e:
            logger.debug(f"Whisper API failed for {video_id}: {e}")
            return None
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def _parse_json3(self, filepath: str) -> str:
        """Parse YouTube's json3 subtitle format into timestamped text."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        lines = []
        for event in data.get("events", []):
            start_ms = event.get("tStartMs", 0)
            start_sec = start_ms / 1000
            minutes = int(start_sec // 60)
            seconds = start_sec % 60

            segs = event.get("segs", [])
            text = "".join(seg.get("utf8", "") for seg in segs).strip()
            if text and text != "\n":
                ts = f"[{minutes}:{seconds:05.2f}]"
                lines.append(f"{ts} {text}")

        return "\n".join(lines)

    @staticmethod
    def _get_lang_codes(language: str) -> list[str]:
        mapping = {
            "English": ["en", "en-IN", "en-US", "en-GB"],
            "Hinglish": ["hi", "en-IN", "en"],
            "Hindi": ["hi", "hi-IN"],
            "Tamil": ["ta", "ta-IN"],
            "Telugu": ["te", "te-IN"],
            "Kannada": ["kn", "kn-IN"],
            "Malayalam": ["ml", "ml-IN"],
            "Marathi": ["mr", "mr-IN"],
            "Gujarati": ["gu", "gu-IN"],
            "Punjabi": ["pa", "pa-IN"],
            "Bengali": ["bn", "bn-IN"],
            "Odia": ["or", "or-IN"],
        }
        return mapping.get(language, ["en"])
