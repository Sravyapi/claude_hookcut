import base64
import json
import os
import re
import subprocess
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

# Cookies file path (shared with transcript.py)
_COOKIES_PATH = str(Path(__file__).parent.parent.parent / "cookies.txt")


def _ensure_cookies_file() -> str:
    """Write cookies from YOUTUBE_COOKIES_B64 env var to disk if not already present."""
    if os.path.exists(_COOKIES_PATH):
        return _COOKIES_PATH
    b64 = os.environ.get("YOUTUBE_COOKIES_B64", "")
    if b64:
        try:
            data = base64.b64decode(b64)
            with open(_COOKIES_PATH, "wb") as f:
                f.write(data)
            logger.info("Decoded YOUTUBE_COOKIES_B64 to %s", _COOKIES_PATH)
        except Exception as e:
            logger.warning("Failed to decode YOUTUBE_COOKIES_B64: %s", e)
    return _COOKIES_PATH


def _ytdlp_base_args() -> list[str]:
    """Common yt-dlp args that help bypass YouTube bot detection on server IPs."""
    settings = get_settings()
    args = [
        "--no-warnings",
        "--geo-bypass",
        "--retries", "3",
        "--no-playlist",
    ]
    # Use cookies file if available (most reliable bot bypass)
    cookies_path = _ensure_cookies_file()
    if os.path.exists(cookies_path):
        args.extend(["--cookies", cookies_path])
    else:
        # Without cookies, use mobile client (less likely to trigger bot check)
        args.extend(["--extractor-args", "youtube:player_client=mweb"])
    # YTDLP_PROXY must be a full proxy URL: http://user:pass@ip:port
    if settings.YTDLP_PROXY:
        args.extend(["--proxy", settings.YTDLP_PROXY])
    return args

# ─── Runtime capability detection ───
_subtitles_filter_available: Optional[bool] = None


def _has_subtitles_filter() -> bool:
    """Check if FFmpeg was compiled with libass (subtitles filter support)."""
    global _subtitles_filter_available
    if _subtitles_filter_available is None:
        try:
            result = subprocess.run(
                ["ffmpeg", "-filters"], capture_output=True, text=True, timeout=5
            )
            _subtitles_filter_available = "subtitles" in result.stdout
            if not _subtitles_filter_available:
                logger.warning(
                    "FFmpeg subtitles filter not available (libass missing). "
                    "Shorts will render without burned-in captions. "
                    "Fix: brew install libass && brew reinstall ffmpeg"
                )
        except Exception as e:
            logger.warning("FFmpeg subtitle filter check failed: %s", e)
            _subtitles_filter_available = False
    return _subtitles_filter_available


# ─── Video Constants ───
SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920
ASPECT_RATIO = "9/16"

# ─── Encoding Constants ───
VIDEO_CODEC = "libx264"
ENCODER_PRESET = "faster"
CRF_QUALITY = "23"
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "192k"
MAX_SHORT_DURATION_SECONDS = 60

# ─── Subtitle Constants ───
MIN_WORDS_PER_LINE = 3
MAX_WORDS_PER_LINE = 7
SUBTITLE_DURATION_DIVISOR = 3

# ─── Caption Style Presets ───
# ASS style format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour,
# BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle,
# BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
CAPTION_STYLES = {
    "clean": (
        "Style: Default,Arial,64,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,"
        "-1,0,0,0,100,100,0,0,1,4,0,2,60,60,180,1"
    ),
    "bold": (
        "Style: Default,Impact,72,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,"
        "-1,0,0,0,100,100,0,0,1,5,0,2,50,50,160,1"
    ),
    "neon": (
        "Style: Default,Arial Black,64,&H00FFFF00,&H000000FF,&H00800000,&H00000000,"
        "-1,0,0,0,100,100,0,0,1,3,2,2,60,60,180,1"
    ),
    "minimal": (
        "Style: Default,Helvetica,52,&H19FFFFFF,&H000000FF,&H00333333,&H00000000,"
        "0,0,0,0,100,100,0,0,1,2,1,2,80,80,200,1"
    ),
}
VALID_CAPTION_STYLES = set(CAPTION_STYLES.keys())

# ─── Watermark Constants ───
WATERMARK_TEXT = "HookCut"
WATERMARK_FONT_SIZE = 24
WATERMARK_OPACITY = 0.3


@dataclass
class FFmpegResult:
    success: bool
    output_path: str
    error: Optional[str] = None
    duration_seconds: Optional[float] = None
    file_size_bytes: Optional[int] = None


def _extract_error_from_stderr(stderr: str) -> str:
    """Extract meaningful error from FFmpeg/yt-dlp stderr (skip progress & encoder params)."""
    lines = stderr.strip().splitlines()

    # Skip patterns: progress output lines and verbose encoder params
    _skip_patterns = ["frame=", "size=", "bitrate=", "speed=",
                      "keyint=", "weightb=", "scenecut=", "mbtree="]
    # Error indicator patterns (prioritize lines containing these)
    _error_indicators = ["error", "invalid", "no such", "failed",
                         "conversion failed", "not found", "cannot", "unable"]

    # Pass 1: collect lines with error indicators (most useful)
    error_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if any(kw in lower for kw in _error_indicators):
            if not any(skip in lower for skip in _skip_patterns):
                error_lines.append(stripped)

    if error_lines:
        # Return last 5 error-indicator lines (most relevant are at the end)
        return " | ".join(error_lines[-5:])

    # Pass 2: fall back to last 5 non-progress, non-encoder-param lines
    tail_lines = []
    for line in reversed(lines):
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if any(skip in lower for skip in _skip_patterns):
            continue
        tail_lines.append(stripped)
        if len(tail_lines) >= 5:
            break
    if tail_lines:
        return " | ".join(reversed(tail_lines))

    # Fallback: last 500 chars
    return stderr[-500:]


def extract_segment(
    youtube_url: str,
    start_seconds: float,
    end_seconds: float,
    output_path: str,
) -> FFmpegResult:
    """Extract a video segment. Tries Cobalt API first (cloud-friendly), falls back to yt-dlp."""
    settings = get_settings()

    # Method 1: Cobalt API — works from cloud IPs (Railway, AWS, etc.)
    if settings.COBALT_API_URL:
        cobalt_result = _try_cobalt_segment(
            youtube_url, start_seconds, end_seconds, output_path
        )
        if cobalt_result.success:
            return cobalt_result
        logger.warning(
            "Cobalt download failed: %s. Falling back to yt-dlp.", cobalt_result.error
        )

    # Method 2: yt-dlp — works locally, often blocked from cloud IPs
    return _extract_segment_ytdlp(youtube_url, start_seconds, end_seconds, output_path)


def _try_cobalt_segment(
    youtube_url: str,
    start_seconds: float,
    end_seconds: float,
    output_path: str,
) -> FFmpegResult:
    """Download video via Cobalt API, then extract segment with FFmpeg locally.

    Cobalt tunnel URLs don't support HTTP range requests, so we download
    the full video first, then trim with FFmpeg (copy mode, no re-encode).
    The full video is cleaned up after extraction.
    """
    settings = get_settings()
    work_dir = os.path.dirname(output_path)
    full_video_path = os.path.join(work_dir, "cobalt_full.mp4")

    try:
        # Step 1: Get download URL from Cobalt
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if settings.COBALT_API_KEY:
            headers["Authorization"] = f"Api-Key {settings.COBALT_API_KEY}"

        resp = httpx.post(
            settings.COBALT_API_URL,
            json={
                "url": youtube_url,
                "videoQuality": "720",
                "youtubeVideoCodec": "h264",
            },
            headers=headers,
            timeout=30,
        )
        if resp.status_code != 200:
            return FFmpegResult(
                success=False, output_path=output_path,
                error=f"Cobalt API returned {resp.status_code}: {resp.text[:200]}",
            )

        data = resp.json()
        status = data.get("status")

        if status == "error":
            error_info = data.get("error", {})
            code = error_info.get("code", "unknown") if isinstance(error_info, dict) else str(error_info)
            return FFmpegResult(
                success=False, output_path=output_path,
                error=f"Cobalt error: {code}",
            )

        download_url = data.get("url")
        if not download_url:
            return FFmpegResult(
                success=False, output_path=output_path,
                error=f"Cobalt returned status '{status}' but no download URL",
            )

        logger.info("Cobalt returned %s URL for %s", status, youtube_url)

        # Step 2: Download full video via httpx streaming
        with httpx.stream("GET", download_url, timeout=300, follow_redirects=True) as stream:
            stream.raise_for_status()
            with open(full_video_path, "wb") as f:
                for chunk in stream.iter_bytes(chunk_size=65536):
                    f.write(chunk)

        full_size = os.path.getsize(full_video_path)
        if full_size < 10000:
            return FFmpegResult(
                success=False, output_path=output_path,
                error=f"Cobalt download too small ({full_size} bytes)",
            )
        logger.info("Cobalt downloaded %d bytes to %s", full_size, full_video_path)

        # Step 3: Extract segment — try copy first, fall back to re-encode
        duration = end_seconds - start_seconds

        # Attempt 1: copy mode (fast, preserves quality)
        cmd_copy = [
            "ffmpeg", "-y",
            "-ss", str(start_seconds),
            "-i", full_video_path,
            "-t", str(duration),
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            "-movflags", "+faststart",
            output_path,
        ]
        result = subprocess.run(cmd_copy, capture_output=True, text=True, timeout=60)

        if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) >= 10000:
            # Validate the segment has a decodable video stream
            probe = _probe_video_stream(output_path)
            if probe and probe.get("width"):
                logger.info("Cobalt segment extracted via copy (%d bytes)", os.path.getsize(output_path))
                return FFmpegResult(
                    success=True, output_path=output_path,
                    file_size_bytes=os.path.getsize(output_path),
                )
            logger.warning("Cobalt copy segment has no decodable video, re-encoding")

        # Attempt 2: re-encode (slower but guarantees clean keyframes)
        cmd_reencode = [
            "ffmpeg", "-y",
            "-ss", str(start_seconds),
            "-i", full_video_path,
            "-t", str(duration),
            "-c:v", VIDEO_CODEC, "-preset", ENCODER_PRESET, "-crf", "18",
            "-c:a", AUDIO_CODEC, "-b:a", AUDIO_BITRATE,
            "-movflags", "+faststart",
            output_path,
        ]
        result = subprocess.run(cmd_reencode, capture_output=True, text=True, timeout=120)

        if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) >= 10000:
            logger.info("Cobalt segment extracted via re-encode (%d bytes)", os.path.getsize(output_path))
            return FFmpegResult(
                success=True, output_path=output_path,
                file_size_bytes=os.path.getsize(output_path),
            )

        return FFmpegResult(
            success=False, output_path=output_path,
            error=f"FFmpeg segment extraction failed: {_extract_error_from_stderr(result.stderr)}",
        )

    except httpx.TimeoutException:
        return FFmpegResult(
            success=False, output_path=output_path,
            error="Cobalt download timed out",
        )
    except Exception as e:
        return FFmpegResult(
            success=False, output_path=output_path,
            error=f"Cobalt error: {e}",
        )
    finally:
        # Clean up full video to save disk space
        if os.path.exists(full_video_path):
            os.remove(full_video_path)


def _extract_segment_ytdlp(
    youtube_url: str,
    start_seconds: float,
    end_seconds: float,
    output_path: str,
) -> FFmpegResult:
    """Extract a video segment using yt-dlp --download-sections. Never downloads full video."""
    cmd = [
        "yt-dlp",
        *_ytdlp_base_args(),
        "--download-sections", f"*{start_seconds}-{end_seconds}",
        "-f", "bestvideo[height<=720][vcodec^=avc1]+bestaudio/bestvideo[height<=720]+bestaudio/best[height<=720]",
        "--merge-output-format", "mp4",
        "-o", output_path,
        youtube_url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return FFmpegResult(
                success=False, output_path=output_path,
                error=f"yt-dlp failed: {_extract_error_from_stderr(result.stderr)}"
            )
        if not os.path.exists(output_path):
            return FFmpegResult(
                success=False, output_path=output_path,
                error="yt-dlp completed but output file not found"
            )
        # Validate file isn't corrupt/empty
        file_size = os.path.getsize(output_path)
        if file_size < 10000:  # Less than 10KB is certainly corrupt
            return FFmpegResult(
                success=False, output_path=output_path,
                error=f"Downloaded file too small ({file_size} bytes), likely corrupt"
            )
        # Validate the segment has a decodable video stream (matches Cobalt path)
        probe = _probe_video_stream(output_path)
        if not probe or not probe.get("width"):
            return FFmpegResult(
                success=False, output_path=output_path,
                error=f"yt-dlp segment has no decodable video stream ({file_size} bytes)"
            )
        logger.info(
            "yt-dlp segment: %sx%s codec=%s (%d bytes)",
            probe.get("width"), probe.get("height"), probe.get("codec_name"), file_size,
        )
        return FFmpegResult(
            success=True, output_path=output_path,
            file_size_bytes=file_size,
        )
    except subprocess.TimeoutExpired:
        return FFmpegResult(
            success=False, output_path=output_path,
            error="yt-dlp timed out after 300 seconds"
        )
    except Exception as e:
        return FFmpegResult(success=False, output_path=output_path, error=str(e))


def concat_segments(segment_paths: list[str], output_path: str) -> FFmpegResult:
    """Concatenate multiple video segments (for composite hooks)."""
    work_dir = os.path.dirname(output_path)
    filelist_path = os.path.join(work_dir, "filelist.txt")
    with open(filelist_path, "w") as f:
        for path in segment_paths:
            f.write(f"file '{path}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", filelist_path,
        "-c", "copy",
        output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return FFmpegResult(
                success=False, output_path=output_path,
                error=f"FFmpeg concat failed: {result.stderr[-1500:]}"
            )
        return FFmpegResult(success=True, output_path=output_path)
    except Exception as e:
        return FFmpegResult(success=False, output_path=output_path, error=str(e))


def generate_ass_subtitles(
    caption_text: str,
    duration_seconds: float,
    output_path: str,
    style: str = "clean",
) -> str:
    """Generate an ASS subtitle file from cleaned caption text.

    Produces short-form video captions styled for mobile viewing.
    Style presets: clean, bold, neon, minimal.
    """
    words = caption_text.split()
    if not words:
        words = [""]

    # Group words into display lines (3–7 words each, sentence-aware)
    lines = _split_caption_lines(words)

    # Allocate time proportionally to word count so longer lines get more screen time
    word_counts = [max(len(line.split()), 1) for line in lines]
    total_words = sum(word_counts)
    offsets = [0.0]
    for wc in word_counts:
        offsets.append(offsets[-1] + duration_seconds * wc / total_words)

    style_line = CAPTION_STYLES.get(style, CAPTION_STYLES["clean"])

    ass_content = (
        "[Script Info]\n"
        "Title: HookCut Captions\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {SHORTS_WIDTH}\n"
        f"PlayResY: {SHORTS_HEIGHT}\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"{style_line}\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    for i, line in enumerate(lines):
        start = offsets[i]
        end = offsets[i + 1]
        start_str = _seconds_to_ass_time(start)
        end_str = _seconds_to_ass_time(end)
        escaped = line.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
        ass_content += f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{escaped}\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    return output_path


def _split_caption_lines(words: list[str]) -> list[str]:
    """Split words into caption lines, breaking at punctuation when possible."""
    lines = []
    current: list[str] = []

    for word in words:
        current.append(word)
        at_break = word.rstrip().endswith((".", "!", "?", ",", ";", ":"))
        if len(current) >= MAX_WORDS_PER_LINE or (at_break and len(current) >= MIN_WORDS_PER_LINE):
            lines.append(" ".join(current))
            current = []

    if current:
        # Merge short trailing fragment into last line if it's very short
        if lines and len(current) <= 2:
            lines[-1] += " " + " ".join(current)
        else:
            lines.append(" ".join(current))

    return lines if lines else [""]


def _probe_video_stream(filepath: str) -> Optional[dict]:
    """Probe input file for video stream info (width, height, codec)."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,codec_name",
            "-of", "json",
            filepath,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            streams = data.get("streams", [])
            if streams:
                return streams[0]
    except Exception as e:
        logger.debug("Failed to get video stream info: %s", e)
    return None


def _build_render_cmd(
    input_path: str,
    output_path: str,
    subtitle_path: Optional[str] = None,
    watermark: bool = False,
    use_subtitles: bool = True,
    skip_loudnorm: bool = False,
) -> list[str]:
    """Build the FFmpeg render command. Separated for retry logic."""
    vf_parts = [
        # Center-crop 16:9 to 9:16 with safety guard (max 2px prevents 0-width crash)
        f"crop='max(min(ih*{ASPECT_RATIO},iw),2)':ih:'(iw-max(min(ih*{ASPECT_RATIO},iw),2))/2':0",
        # Scale to Shorts resolution
        f"scale={SHORTS_WIDTH}:{SHORTS_HEIGHT}:force_original_aspect_ratio=decrease",
        f"pad={SHORTS_WIDTH}:{SHORTS_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black",
    ]

    # Burn in captions (requires libass — gracefully skip if unavailable)
    if (
        use_subtitles
        and subtitle_path
        and os.path.exists(subtitle_path)
        and _has_subtitles_filter()
    ):
        # FFmpeg subtitles filter requires forward slashes and escaped colons
        sub_escaped = subtitle_path.replace("\\", "/").replace(":", "\\:")
        vf_parts.append(f"subtitles='{sub_escaped}'")

    # Watermark (free tier only)
    if watermark:
        vf_parts.append(
            f"drawtext=text='{WATERMARK_TEXT}':fontsize={WATERMARK_FONT_SIZE}"
            f":fontcolor=white@{WATERMARK_OPACITY}:x=w-tw-20:y=h-th-20:font=Arial"
        )

    vf = ",".join(vf_parts)

    # Audio filter: loudnorm can fail on short clips (<3s), so it's skippable
    if skip_loudnorm:
        af = "apad=pad_dur=0.3"
    else:
        af = "loudnorm=I=-14:TP=-1:LRA=11,apad=pad_dur=0.3"

    return [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf,
        "-af", af,
        "-c:v", VIDEO_CODEC, "-preset", ENCODER_PRESET, "-crf", CRF_QUALITY,
        "-c:a", AUDIO_CODEC, "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart",
        "-t", str(MAX_SHORT_DURATION_SECONDS),
        output_path,
    ]


def render_short(
    input_path: str,
    subtitle_path: str,
    output_path: str,
    watermark: bool = False,
) -> FFmpegResult:
    """
    Single-pass FFmpeg render: 16:9 → 9:16 + audio normalization + captions + watermark.
    Retries without subtitles if first attempt produces 0 frames.
    """
    # Validate input has a video stream
    video_info = _probe_video_stream(input_path)
    if not video_info:
        return FFmpegResult(
            success=False, output_path=output_path,
            error="Input file has no video stream (ffprobe found nothing)"
        )
    input_size = os.path.getsize(input_path) if os.path.exists(input_path) else 0
    logger.info(
        "Render input: %sx%s codec=%s size=%d bytes path=%s",
        video_info.get("width"), video_info.get("height"), video_info.get("codec_name"),
        input_size, input_path,
    )

    # Attempt 1: full pipeline (subtitles + loudnorm)
    cmd = _build_render_cmd(input_path, output_path, subtitle_path, watermark, use_subtitles=True)
    result = _run_ffmpeg_render(cmd, output_path)
    if result.success:
        return result

    # If render produced non-zero frames but still failed — don't retry
    # FFmpeg outputs "frame=    0" with variable whitespace, so use regex
    zero_frames = bool(result.error and re.search(r"frame=\s*0\s", result.error))
    if result.error and "frame=" in result.error and not zero_frames:
        return result

    # Attempt 2: skip loudnorm (it misbehaves on short clips ~3s or less)
    logger.warning("Render produced 0 frames, retrying without loudnorm")
    cmd = _build_render_cmd(input_path, output_path, subtitle_path, watermark, use_subtitles=True, skip_loudnorm=True)
    result = _run_ffmpeg_render(cmd, output_path)
    if result.success:
        return result

    # Attempt 3: skip both loudnorm and subtitles
    logger.warning("Retry without loudnorm failed, trying without subtitles too")
    cmd = _build_render_cmd(input_path, output_path, subtitle_path, watermark, use_subtitles=False, skip_loudnorm=True)
    result = _run_ffmpeg_render(cmd, output_path)
    if result.success:
        return result

    # Attempt 4: minimal pipeline (just scale + pad, no crop, no loudnorm)
    logger.warning("All retries failed, trying minimal pipeline")
    vf_minimal = (
        f"scale={SHORTS_WIDTH}:{SHORTS_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={SHORTS_WIDTH}:{SHORTS_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black"
    )
    cmd_minimal = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf_minimal,
        "-c:v", VIDEO_CODEC, "-preset", ENCODER_PRESET, "-crf", CRF_QUALITY,
        "-c:a", AUDIO_CODEC, "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart",
        "-t", str(MAX_SHORT_DURATION_SECONDS),
        output_path,
    ]
    return _run_ffmpeg_render(cmd_minimal, output_path)


def _run_ffmpeg_render(cmd: list[str], output_path: str) -> FFmpegResult:
    """Execute an FFmpeg render command and return structured result."""
    try:
        logger.info("FFmpeg cmd: %s", " ".join(cmd[:6]) + " ...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return FFmpegResult(
                success=False, output_path=output_path,
                error=f"FFmpeg render failed: {_extract_error_from_stderr(result.stderr)}"
            )
        # Verify output file exists and has content
        if not os.path.exists(output_path) or os.path.getsize(output_path) < 1000:
            return FFmpegResult(
                success=False, output_path=output_path,
                error="FFmpeg completed but output file missing or too small"
            )
        duration = probe_duration(output_path)
        return FFmpegResult(
            success=True, output_path=output_path,
            duration_seconds=duration,
            file_size_bytes=os.path.getsize(output_path),
        )
    except subprocess.TimeoutExpired:
        return FFmpegResult(
            success=False, output_path=output_path,
            error="FFmpeg render timed out after 300 seconds"
        )
    except Exception as e:
        return FFmpegResult(success=False, output_path=output_path, error=str(e))


def extract_thumbnail(input_path: str, output_path: str) -> FFmpegResult:
    """
    Extract the most visually interesting frame as a thumbnail.

    Uses FFmpeg's thumbnail filter which analyzes the full video in batches
    and selects the frame with the most visual interest (avoids blurry,
    dark, or monotone frames). Then applies a subtle contrast/saturation
    lift to make the thumbnail pop.
    """
    duration = probe_duration(input_path) or 5.0
    # Cap at 30 candidates — enough for quality selection, keeps extraction fast
    n_candidates = max(10, min(30, int(duration * 2)))

    vf = (
        f"thumbnail=n={n_candidates},"
        "eq=contrast=1.05:saturation=1.15:brightness=0.02"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf", vf,
        "-frames:v", "1",
        "-q:v", "2",
        output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            # Fallback: middle frame without enhancement
            fallback_cmd = [
                "ffmpeg", "-y",
                "-ss", str(duration / 2),
                "-i", input_path,
                "-vframes", "1",
                "-q:v", "2",
                output_path,
            ]
            fallback = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=30)
            if fallback.returncode != 0:
                return FFmpegResult(
                    success=False, output_path=output_path,
                    error=f"Thumbnail extraction failed: {result.stderr[:300]}"
                )
        return FFmpegResult(success=True, output_path=output_path)
    except Exception as e:
        return FFmpegResult(success=False, output_path=output_path, error=str(e))


def probe_duration(filepath: str) -> Optional[float]:
    """Get video duration using ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filepath,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception as e:
        logger.debug("Failed to probe duration: %s", e)
    return None


def _seconds_to_ass_time(sec: float) -> str:
    """Convert seconds to ASS time format (H:MM:SS.cc)."""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    centiseconds = int((s % 1) * 100)
    return f"{h}:{m:02d}:{int(s):02d}.{centiseconds:02d}"
