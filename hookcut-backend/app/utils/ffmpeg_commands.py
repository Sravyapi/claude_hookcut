import os
import subprocess
import logging
from dataclasses import dataclass
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


def _ytdlp_base_args() -> list[str]:
    """Common yt-dlp args that help bypass YouTube bot detection on server IPs."""
    args = [
        "--no-warnings",
        "--geo-bypass",
        "--extractor-args", "youtube:player_client=android_creator",
        "--retries", "3",
        "--no-playlist",
    ]
    settings = get_settings()
    # Webshare proxy or generic proxy for yt-dlp
    if settings.WEBSHARE_PROXY_USERNAME and settings.WEBSHARE_PROXY_PASSWORD:
        proxy_url = (
            f"http://{settings.WEBSHARE_PROXY_USERNAME}"
            f":{settings.WEBSHARE_PROXY_PASSWORD}"
            f"@p.webshare.io:80"
        )
        args.extend(["--proxy", proxy_url])
    elif settings.YTDLP_PROXY:
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
        except Exception:
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
    """Extract meaningful error from FFmpeg/yt-dlp stderr (skip verbose encoder params)."""
    lines = stderr.strip().splitlines()
    # FFmpeg errors are usually in the last few lines after "Conversion failed" or "Error"
    error_lines = []
    for line in reversed(lines):
        stripped = line.strip()
        if not stripped:
            continue
        # Stop collecting once we hit verbose encoder params
        if any(kw in stripped for kw in ["keyint=", "weightb=", "scenecut=", "mbtree="]):
            break
        error_lines.append(stripped)
        if len(error_lines) >= 5:
            break
    if error_lines:
        return " | ".join(reversed(error_lines))
    # Fallback: last 500 chars
    return stderr[-500:]


def extract_segment(
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
        "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]",
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
    time_per_line = duration_seconds / max(len(lines), 1)

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
        start = i * time_per_line
        end = min((i + 1) * time_per_line, duration_seconds)
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


def render_short(
    input_path: str,
    subtitle_path: str,
    output_path: str,
    watermark: bool = False,
) -> FFmpegResult:
    """
    Single-pass FFmpeg render: 16:9 → 9:16 + audio normalization + captions + watermark.
    """
    # Build video filter chain
    vf_parts = [
        # Center-crop 16:9 to 9:16
        f"crop=ih*{ASPECT_RATIO}:ih:(iw-ih*{ASPECT_RATIO})/2:0",
        # Scale to Shorts resolution
        f"scale={SHORTS_WIDTH}:{SHORTS_HEIGHT}:force_original_aspect_ratio=decrease",
        f"pad={SHORTS_WIDTH}:{SHORTS_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black",
    ]

    # Burn in captions (requires libass — gracefully skip if unavailable)
    if subtitle_path and os.path.exists(subtitle_path) and _has_subtitles_filter():
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

    # Audio filter: silence removal + normalization + padding
    af = (
        "silenceremove=start_periods=1:start_silence=0.3:start_threshold=-40dB,"
        "loudnorm=I=-14:TP=-1:LRA=11,"
        "apad=pad_dur=0.3"
    )

    cmd = [
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

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return FFmpegResult(
                success=False, output_path=output_path,
                error=f"FFmpeg render failed: {_extract_error_from_stderr(result.stderr)}"
            )
        duration = probe_duration(output_path)
        return FFmpegResult(
            success=True, output_path=output_path,
            duration_seconds=duration,
            file_size_bytes=os.path.getsize(output_path) if os.path.exists(output_path) else None,
        )
    except subprocess.TimeoutExpired:
        return FFmpegResult(
            success=False, output_path=output_path,
            error="FFmpeg render timed out after 300 seconds"
        )
    except Exception as e:
        return FFmpegResult(success=False, output_path=output_path, error=str(e))


def extract_thumbnail(input_path: str, output_path: str) -> FFmpegResult:
    """Extract the middle frame as a JPG thumbnail."""
    duration = probe_duration(input_path) or 5.0
    seek_time = duration / 2

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(seek_time),
        "-i", input_path,
        "-vframes", "1",
        "-q:v", "2",
        output_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
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
    except Exception:
        pass
    return None


def _seconds_to_ass_time(sec: float) -> str:
    """Convert seconds to ASS time format (H:MM:SS.cc)."""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    centiseconds = int((s % 1) * 100)
    return f"{h}:{m:02d}:{int(s):02d}.{centiseconds:02d}"
