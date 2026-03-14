"""AssemblyAI diarization service for interview-mode transcripts."""
import os
import subprocess
import tempfile
import time
import logging
from dataclasses import dataclass

import httpx

from app.config import get_settings
from app.exceptions import TranscriptError

logger = logging.getLogger(__name__)

ASSEMBLYAI_BASE = "https://api.assemblyai.com/v2"
POLL_INTERVAL_SECONDS = 5
POLL_TIMEOUT_SECONDS = 300  # 5 minutes

# Map our language names to AssemblyAI language codes
LANGUAGE_MAP = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Bengali": "bn",
    "Marathi": "mr",
    "Gujarati": "gu",
    "Punjabi": "pa",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Japanese": "ja",
    "Korean": "ko",
    "Portuguese": "pt",
    "Italian": "it",
    "Dutch": "nl",
    "Russian": "ru",
    "Arabic": "ar",
}


@dataclass
class SpeakerUtterance:
    speaker: str       # "Speaker A", "Speaker B"
    start_ms: int
    end_ms: int
    text: str


@dataclass
class DiarizationResult:
    utterances: list[SpeakerUtterance]
    detected_speaker_count: int
    transcript_text: str  # "[Speaker A] [0:05] Hello...\n[Speaker B] [0:12] Thanks..."


class AssemblyAIDiarizer:

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.ASSEMBLYAI_API_KEY
        if not self.api_key:
            raise TranscriptError("ASSEMBLYAI_API_KEY is not configured")

    def diarize(self, video_id: str, language: str, speaker_count: int) -> DiarizationResult:
        """Download audio, upload to AssemblyAI, transcribe with speaker labels."""
        audio_path = self._download_audio(video_id)
        try:
            upload_url = self._upload_audio(audio_path)
            transcript_id = self._create_transcript(upload_url, language, speaker_count)
            result = self._poll_transcript(transcript_id)
            return self._parse_result(result)
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)

    def _download_audio(self, video_id: str) -> str:
        """Download audio via yt-dlp."""
        tmp = tempfile.mktemp(suffix=".mp3", prefix="hookcut_diarize_")
        url = f"https://www.youtube.com/watch?v={video_id}"
        cmd = [
            "yt-dlp",
            "-f", "bestaudio",
            "--extract-audio",
            "--audio-format", "mp3",
            "-o", tmp,
            url,
        ]
        settings = get_settings()
        if settings.YTDLP_PROXY:
            cmd.extend(["--proxy", settings.YTDLP_PROXY])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                raise TranscriptError(f"Audio download failed: {result.stderr[:200]}")
            if not os.path.exists(tmp):
                raise TranscriptError("Audio download produced no output file")
            return tmp
        except subprocess.TimeoutExpired:
            raise TranscriptError("Audio download timed out")

    def _upload_audio(self, audio_path: str) -> str:
        """Upload audio file to AssemblyAI and return the upload URL."""
        headers = {"authorization": self.api_key}
        with open(audio_path, "rb") as f:
            response = httpx.post(
                f"{ASSEMBLYAI_BASE}/upload",
                headers=headers,
                content=f,
                timeout=120,
            )
        response.raise_for_status()
        return response.json()["upload_url"]

    def _create_transcript(self, audio_url: str, language: str, speaker_count: int) -> str:
        """Create a transcript with speaker diarization enabled."""
        headers = {
            "authorization": self.api_key,
            "content-type": "application/json",
        }
        body: dict = {
            "audio_url": audio_url,
            "speech_models": ["universal-2"],
            "speaker_labels": True,
            "speakers_expected": speaker_count,
        }
        # AssemblyAI: language_detection=True is more reliable with speaker_labels
        # than specifying language_code directly (some combos return 400)
        lang_code = LANGUAGE_MAP.get(language)
        if lang_code and lang_code == "en":
            body["language_code"] = lang_code
        else:
            # For non-English or unknown, let AssemblyAI auto-detect
            body["language_detection"] = True

        response = httpx.post(
            f"{ASSEMBLYAI_BASE}/transcript",
            headers=headers,
            json=body,
            timeout=30,
        )
        if response.status_code != 200:
            logger.error(
                "AssemblyAI transcript creation failed: %d %s",
                response.status_code, response.text[:500],
            )
            response.raise_for_status()
        return response.json()["id"]

    def _poll_transcript(self, transcript_id: str) -> dict:
        """Poll until transcript is completed or timeout."""
        headers = {"authorization": self.api_key}
        start = time.monotonic()
        while time.monotonic() - start < POLL_TIMEOUT_SECONDS:
            response = httpx.get(
                f"{ASSEMBLYAI_BASE}/transcript/{transcript_id}",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            status = data.get("status")
            if status == "completed":
                return data
            if status == "error":
                raise TranscriptError(f"AssemblyAI transcription failed: {data.get('error', 'unknown')}")
            # Sleep is acceptable here: runs inside Celery worker, polling external API
            time.sleep(POLL_INTERVAL_SECONDS)
        raise TranscriptError("Diarization timed out after 5 minutes")

    def _parse_result(self, data: dict) -> DiarizationResult:
        """Parse AssemblyAI response into DiarizationResult."""
        raw_utterances = data.get("utterances", [])
        if not raw_utterances:
            raise TranscriptError("AssemblyAI returned no speaker utterances")

        # Map speaker labels: "A" → "Speaker A"
        speakers_seen: set[str] = set()
        utterances: list[SpeakerUtterance] = []
        for u in raw_utterances:
            speaker_label = u.get("speaker", "A")
            speaker_name = f"Speaker {speaker_label}"
            speakers_seen.add(speaker_label)
            utterances.append(SpeakerUtterance(
                speaker=speaker_name,
                start_ms=u.get("start", 0),
                end_ms=u.get("end", 0),
                text=u.get("text", ""),
            ))

        # Build formatted transcript
        lines = []
        for u in utterances:
            ts = _ms_to_timestamp(u.start_ms)
            lines.append(f"[{u.speaker}] [{ts}] {u.text}")
        transcript_text = "\n".join(lines)

        return DiarizationResult(
            utterances=utterances,
            detected_speaker_count=len(speakers_seen),
            transcript_text=transcript_text,
        )


def _ms_to_timestamp(ms: int) -> str:
    """Convert milliseconds to M:SS format."""
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"
