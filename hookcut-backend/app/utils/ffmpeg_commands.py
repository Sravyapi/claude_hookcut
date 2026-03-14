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

MIN_OUTPUT_FILE_SIZE_BYTES = 10000


def _detect_face_crop_x(video_path: str, sample_interval: float = 0.5) -> Optional[str]:
    """Detect face positions and build an FFmpeg expression for per-frame adaptive crop.

    Samples frames, detects faces with OpenCV Haar cascade, then:
    - If face positions are consistent (low variance): returns a static X offset
    - If face moves significantly (camera angle changes): returns an FFmpeg expression
      using `if(between(t,...),x1,x2)` to adapt the crop per time segment
    - Falls back to None (center crop) if detection rate is too low

    Returns an FFmpeg crop X expression string, or None for center crop.
    """
    try:
        os.environ.setdefault("OPENCV_OPENCL_RUNTIME", "disabled")
        import cv2
    except ImportError:
        logger.warning("opencv not installed — skipping face detection")
        return None

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.warning("Cannot open video for face detection: %s", video_path)
        return None

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    if frame_width == 0 or frame_height == 0:
        cap.release()
        return None

    # Skip if already portrait (9:16 or similar)
    if frame_height >= frame_width:
        cap.release()
        logger.info("Video is already portrait (%dx%d) — skipping face crop", frame_width, frame_height)
        return None

    frame_step = max(1, int(fps * sample_interval))
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    # Collect (time_seconds, face_center_x, face_area) per frame
    detections: list[tuple[float, int, int]] = []
    frames_with_faces = 0
    total_sampled = 0

    frame_idx = 0
    while frame_idx < total_frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break
        total_sampled += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30)
        )
        if len(faces) > 0:
            frames_with_faces += 1
            largest = max(faces, key=lambda f: f[2] * f[3])
            x, y, fw, fh = largest
            cx = x + fw // 2
            t = frame_idx / fps
            detections.append((t, cx, fw * fh))
        frame_idx += frame_step

    cap.release()

    if not detections:
        logger.info("No faces detected in %s — will use center crop", video_path)
        return None

    detection_rate = frames_with_faces / max(total_sampled, 1)
    if detection_rate < 0.20:
        logger.info(
            "Low face detection rate (%.0f%%) in %s — using center crop",
            detection_rate * 100, video_path,
        )
        return None

    crop_w = min(int(frame_height * 9 / 16), frame_width)
    center = frame_width // 2

    # Check if face position varies significantly
    xs = [cx for _, cx, _ in detections]
    x_range = max(xs) - min(xs)

    # If positions are consistent (range < 15% of frame), use static crop
    if x_range < frame_width * 0.15:
        # Use area-weighted average for more accurate centering on the speaker
        total_area = sum(area for _, _, area in detections)
        weighted_x = int(sum(cx * area for _, cx, area in detections) / total_area)
        # Only skip face crop if face is very close to center (within 3% of frame)
        # — even small offsets are noticeable in portrait crop
        if abs(weighted_x - center) < frame_width * 0.03:
            logger.info("Face at center (weighted=%d, center=%d) — center crop", weighted_x, center)
            return None
        x_offset = max(0, min(weighted_x - crop_w // 2, frame_width - crop_w))
        logger.info("Static face crop: weighted_x=%d x_offset=%d", weighted_x, x_offset)
        return str(x_offset)

    # Face moves significantly — build per-segment adaptive crop expression.
    # Group detections into time segments (~2s each) and compute per-segment X.
    duration = total_frames / fps
    segment_len = 2.0  # seconds per segment
    segments: list[tuple[float, float, int]] = []  # (start, end, x_offset)

    t = 0.0
    while t < duration:
        seg_end = min(t + segment_len, duration)
        # Find detections in this segment
        seg_detections = [(cx, area) for (dt, cx, area) in detections if t <= dt < seg_end]
        if seg_detections:
            # Size-weighted average for this segment
            total_area = sum(a for _, a in seg_detections)
            weighted_x = int(sum(cx * a for cx, a in seg_detections) / total_area)
        else:
            # No detections — use center
            weighted_x = center
        x_off = max(0, min(weighted_x - crop_w // 2, frame_width - crop_w))
        segments.append((t, seg_end, x_off))
        t = seg_end

    # Merge adjacent segments with similar X offsets (within 5% of frame width)
    merged: list[tuple[float, float, int]] = [segments[0]]
    for start, end, x_off in segments[1:]:
        prev_start, prev_end, prev_x = merged[-1]
        if abs(x_off - prev_x) < frame_width * 0.05:
            merged[-1] = (prev_start, end, prev_x)
        else:
            merged.append((start, end, x_off))

    # If only one segment after merging, use static
    if len(merged) == 1:
        x_off = merged[0][2]
        if abs((x_off + crop_w // 2) - center) < frame_width * 0.10:
            logger.info("Single merged segment near center — center crop")
            return None
        logger.info("Single merged segment: x_offset=%d", x_off)
        return str(x_off)

    # Build nested FFmpeg if(between(t,...)) expression
    # FFmpeg evaluates left to right: if(cond1,val1,if(cond2,val2,...,default))
    expr = str(merged[-1][2])  # default = last segment
    for start, end, x_off in reversed(merged[:-1]):
        expr = f"if(between(t,{start:.1f},{end:.1f}),{x_off},{expr})"

    logger.info(
        "Adaptive face crop: %d segments, x_range=%d (%.0f%% of frame), expr=%s",
        len(merged), x_range, x_range / frame_width * 100, expr[:120],
    )
    return expr

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
            os.chmod(_COOKIES_PATH, 0o600)
            logger.info("Decoded YOUTUBE_COOKIES_B64 to %s", _COOKIES_PATH)
        except Exception as e:
            logger.warning("Failed to decode YOUTUBE_COOKIES_B64: %s", e)
    return _COOKIES_PATH


def _validate_cobalt_url(url: str) -> str:
    """Validate a URL returned by the Cobalt API to prevent SSRF attacks.

    Raises ValueError if the URL is not a safe HTTPS URL.
    """
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Cobalt returned non-HTTPS URL: {url!r}")
    return url


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
    # Clean — crisp white, readable outline, subtle shadow for depth
    "clean": (
        "Style: Default,Arial,68,&H00FFFFFF,&H000000FF,&H00000000,&H96000000,"
        "-1,0,0,0,100,100,1,0,1,3.5,1.5,2,60,60,180,1"
    ),
    # Bold — high-impact, thick outline, strong shadow
    "bold": (
        "Style: Default,Impact,76,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,"
        "-1,0,0,0,100,100,2,0,1,5,2,2,50,50,160,1"
    ),
    # Neon — bright cyan text, dark outline glow
    "neon": (
        "Style: Default,Arial Black,68,&H00FFFF00,&H000000FF,&H00502000,&H00000000,"
        "-1,0,0,0,100,100,1,0,1,4,2,2,60,60,180,1"
    ),
    # Minimal — elegant, lighter weight, understated
    "minimal": (
        "Style: Default,Helvetica,56,&H00FFFFFF,&H000000FF,&H00222222,&H00000000,"
        "0,0,0,0,100,100,0,0,1,2,1,2,80,80,200,1"
    ),
}
VALID_CAPTION_STYLES = set(CAPTION_STYLES.keys())

# ─── Watermark Constants ───
WATERMARK_TEXT = "Made using HookCut"
WATERMARK_FONT_SIZE = 20
WATERMARK_OPACITY = 0.4

# ─── Aspect Ratio Presets ───
ASPECT_RESOLUTIONS = {
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}

ASPECT_RATIOS_FFMPEG = {
    "9:16": "9/16",
    "1:1": "1/1",
    "4:5": "4/5",
}


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
    prefer_high_res: bool = False,
) -> FFmpegResult:
    """Extract a video segment. Tries Cobalt API first (cloud-friendly), falls back to yt-dlp.

    Args:
        prefer_high_res: When True (interview mode), prefer 1080p for split-screen quality.
    """
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
    return _extract_segment_ytdlp(youtube_url, start_seconds, end_seconds, output_path, prefer_high_res=prefer_high_res)


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

        # Validate URL before fetching to prevent SSRF via malicious redirect URLs
        _validate_cobalt_url(download_url)

        # Step 2: Download full video via httpx streaming (redirects disabled after validation)
        with httpx.stream("GET", download_url, timeout=300, follow_redirects=False) as stream:
            stream.raise_for_status()
            with open(full_video_path, "wb") as f:
                for chunk in stream.iter_bytes(chunk_size=65536):
                    f.write(chunk)

        full_size = os.path.getsize(full_video_path)
        if full_size < MIN_OUTPUT_FILE_SIZE_BYTES:
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

        if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) >= MIN_OUTPUT_FILE_SIZE_BYTES:
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

        if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) >= MIN_OUTPUT_FILE_SIZE_BYTES:
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
    prefer_high_res: bool = False,
) -> FFmpegResult:
    """Extract a video segment using yt-dlp --download-sections. Never downloads full video."""
    # Interview mode: prefer 1080p for split-screen quality.
    # --download-sections often downgrades to muxed low-res formats when using
    # separate video+audio streams. For high-res, download full then trim with FFmpeg.
    if prefer_high_res:
        return _extract_segment_ytdlp_highres(youtube_url, start_seconds, end_seconds, output_path)

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
        if file_size < MIN_OUTPUT_FILE_SIZE_BYTES:  # Less than 10KB is certainly corrupt
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


def _extract_segment_ytdlp_highres(
    youtube_url: str,
    start_seconds: float,
    end_seconds: float,
    output_path: str,
) -> FFmpegResult:
    """Download high-res segment for interview split-screen.

    yt-dlp's --download-sections with separate video+audio streams often falls
    back to low-res muxed formats. This method downloads the full video at 720p
    (separate streams, properly merged), then trims with FFmpeg.
    """
    work_dir = os.path.dirname(output_path)
    full_path = os.path.join(work_dir, "full_highres.mp4")

    try:
        # Download full video — 720p h264 preferred, any codec as fallback
        cmd = [
            "yt-dlp",
            *_ytdlp_base_args(),
            "-f", "136+140/bestvideo[height>=720][height<=1080]+bestaudio/best[height>=720]",
            "--merge-output-format", "mp4",
            "-o", full_path,
            youtube_url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            logger.warning("High-res full download failed: %s — falling back to standard",
                           _extract_error_from_stderr(result.stderr)[:200])
            return _extract_segment_ytdlp(youtube_url, start_seconds, end_seconds, output_path, prefer_high_res=False)
        if not os.path.exists(full_path):
            return FFmpegResult(success=False, output_path=output_path, error="High-res download no file")

        full_probe = _probe_video_stream(full_path)
        logger.info(
            "High-res full: %sx%s codec=%s (%d bytes)",
            full_probe.get("width") if full_probe else "?",
            full_probe.get("height") if full_probe else "?",
            full_probe.get("codec_name") if full_probe else "?",
            os.path.getsize(full_path),
        )

        # Trim segment — copy mode for h264, re-encode for VP9/AV1
        codec = full_probe.get("codec_name", "") if full_probe else ""
        if codec == "h264":
            trim_cmd = [
                "ffmpeg", "-y", "-ss", str(start_seconds), "-to", str(end_seconds),
                "-i", full_path, "-c", "copy", "-movflags", "+faststart", output_path,
            ]
        else:
            trim_cmd = [
                "ffmpeg", "-y", "-ss", str(start_seconds), "-to", str(end_seconds),
                "-i", full_path,
                "-c:v", VIDEO_CODEC, "-preset", "fast", "-crf", CRF_QUALITY,
                "-c:a", AUDIO_CODEC, "-b:a", AUDIO_BITRATE,
                "-movflags", "+faststart", output_path,
            ]

        trim_result = subprocess.run(trim_cmd, capture_output=True, text=True, timeout=60)
        if trim_result.returncode != 0:
            return FFmpegResult(success=False, output_path=output_path,
                                error=f"Trim failed: {trim_result.stderr[:200]}")

        if not os.path.exists(output_path):
            return FFmpegResult(success=False, output_path=output_path, error="Trim no output")

        file_size = os.path.getsize(output_path)
        seg_probe = _probe_video_stream(output_path)
        logger.info(
            "High-res segment: %sx%s codec=%s (%d bytes)",
            seg_probe.get("width") if seg_probe else "?",
            seg_probe.get("height") if seg_probe else "?",
            seg_probe.get("codec_name") if seg_probe else "?", file_size,
        )
        return FFmpegResult(success=True, output_path=output_path, file_size_bytes=file_size)

    except subprocess.TimeoutExpired:
        return FFmpegResult(success=False, output_path=output_path, error="High-res timed out")
    except Exception as e:
        return FFmpegResult(success=False, output_path=output_path, error=str(e))
    finally:
        if os.path.exists(full_path):
            os.remove(full_path)


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


def _parse_timed_transcript_lines(
    transcript_text: str,
    start_seconds: float,
    end_seconds: float,
) -> list[dict]:
    """Extract transcript lines within a time range, offset to clip-relative timing.

    Parses lines like '[0:26.00] I know it's annoying.' and returns
    [{text, start, end}] with times relative to clip start (0-based).
    """
    import re
    pattern = re.compile(r"^\[(\d+):(\d+(?:\.\d+)?)\]\s*(.+)$")
    lines = []

    for line in transcript_text.split("\n"):
        m = pattern.match(line.strip())
        if not m:
            continue
        minutes = int(m.group(1))
        secs = float(m.group(2))
        abs_time = minutes * 60 + secs
        text = m.group(3).strip()
        if not text:
            continue
        if abs_time >= start_seconds - 0.5 and abs_time <= end_seconds + 0.5:
            lines.append({"text": text, "abs_time": abs_time})

    if not lines:
        return []

    # Convert to clip-relative timing with proper start/end for each line
    result = []
    for i, entry in enumerate(lines):
        rel_start = max(0.0, entry["abs_time"] - start_seconds)
        if i + 1 < len(lines):
            rel_end = max(0.0, lines[i + 1]["abs_time"] - start_seconds)
        else:
            rel_end = end_seconds - start_seconds
        result.append({"text": entry["text"], "start": rel_start, "end": rel_end})

    return result


def generate_ass_subtitles(
    caption_text: str,
    duration_seconds: float,
    output_path: str,
    style: str = "clean",
    transcript_text: str = "",
    start_seconds: float = 0.0,
    end_seconds: float = 0.0,
) -> str:
    """Generate an ASS subtitle file for short-form video captions.

    If transcript_text + start/end seconds are provided, uses the original
    transcript timing for accurate speech sync. Otherwise falls back to
    proportional word-count timing from caption_text.
    """
    style_line = CAPTION_STYLES.get(style, CAPTION_STYLES["clean"])

    # Try to use original transcript timing for accurate sync
    timed_lines = []
    if transcript_text and end_seconds > start_seconds:
        timed_lines = _parse_timed_transcript_lines(
            transcript_text, start_seconds, end_seconds
        )

    if timed_lines:
        # Use real transcript timing — group into display-friendly chunks
        display_lines = []
        for tl in timed_lines:
            words = tl["text"].split()
            if not words:
                continue
            # Split long lines into display chunks (3-7 words)
            chunks = _split_caption_lines(words)
            chunk_duration = (tl["end"] - tl["start"]) / max(len(chunks), 1)
            for j, chunk in enumerate(chunks):
                display_lines.append({
                    "text": chunk,
                    "start": tl["start"] + j * chunk_duration,
                    "end": tl["start"] + (j + 1) * chunk_duration,
                })
    else:
        # Fallback: proportional timing from cleaned caption text
        words = caption_text.split()
        if not words:
            words = [""]
        lines = _split_caption_lines(words)
        word_counts = [max(len(line.split()), 1) for line in lines]
        total_words = sum(word_counts)
        offsets = [0.0]
        for wc in word_counts:
            offsets.append(offsets[-1] + duration_seconds * wc / total_words)
        display_lines = [
            {"text": line, "start": offsets[i], "end": offsets[i + 1]}
            for i, line in enumerate(lines)
        ]

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

    for dl in display_lines:
        start_str = _seconds_to_ass_time(dl["start"])
        end_str = _seconds_to_ass_time(dl["end"])
        escaped = dl["text"].replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
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


def _ass_to_drawtext_filters(ass_path: str) -> list[str]:
    """Parse ASS subtitle file and convert to drawtext filter chains.

    Fallback for when libass is not available. Produces one drawtext filter
    per dialogue line with enable='between(t,start,end)'.
    """
    try:
        with open(ass_path, "r", encoding="utf-8") as f:
            content = f.read()

        filters = []
        for line in content.splitlines():
            if not line.startswith("Dialogue:"):
                continue
            # Format: Dialogue: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
            parts = line.split(",", 9)
            if len(parts) < 10:
                continue
            start_str = parts[1].strip()
            end_str = parts[2].strip()
            text = parts[9].strip()

            # Convert ASS time H:MM:SS.cc to seconds
            start_sec = _ass_time_to_seconds(start_str)
            end_sec = _ass_time_to_seconds(end_str)
            if start_sec is None or end_sec is None:
                continue

            # Escape special chars for drawtext
            escaped = (
                text.replace("\\", "\\\\")
                .replace("'", "'\\''")
                .replace(":", "\\:")
                .replace("%", "%%")
            )

            filters.append(
                f"drawtext=text='{escaped}'"
                f":fontsize=48:fontcolor=white:borderw=3:bordercolor=black"
                f":font=Arial"
                f":x=(w-text_w)/2:y=h-text_h-120"
                f":enable='between(t,{start_sec:.2f},{end_sec:.2f})'"
            )

        return filters
    except Exception as e:
        logger.warning("Failed to convert ASS to drawtext: %s", e)
        return []


def _ass_time_to_seconds(time_str: str) -> Optional[float]:
    """Convert ASS time format H:MM:SS.cc to seconds."""
    try:
        parts = time_str.split(":")
        h = int(parts[0])
        m = int(parts[1])
        s_parts = parts[2].split(".")
        s = int(s_parts[0])
        cs = int(s_parts[1]) if len(s_parts) > 1 else 0
        return h * 3600 + m * 60 + s + cs / 100.0
    except (ValueError, IndexError):
        return None


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


def _render_caption_pngs(ass_path: str, output_dir: str, style: str = "clean") -> list[dict]:
    """Render each caption line from ASS file as a transparent PNG using Pillow.

    Returns list of dicts: {path, start, end} for each caption image.
    Works on any FFmpeg — no libass/libfreetype required.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.warning("Pillow not installed — captions will be skipped")
        return []

    with open(ass_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Style config per preset
    style_config = {
        "clean": {"font_size": 64, "color": (255, 255, 255), "outline": (0, 0, 0), "outline_w": 4, "bold": True},
        "bold": {"font_size": 72, "color": (255, 255, 255), "outline": (0, 0, 0), "outline_w": 5, "bold": True},
        "neon": {"font_size": 64, "color": (0, 255, 255), "outline": (0, 0, 128), "outline_w": 3, "bold": True},
        "minimal": {"font_size": 52, "color": (255, 255, 255, 230), "outline": (51, 51, 51), "outline_w": 2, "bold": False},
    }
    cfg = style_config.get(style, style_config["clean"])

    # Try to find a good font
    font = None
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFCompact.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, cfg["font_size"])
                break
            except Exception as e:
                logger.warning("Failed to load font %s: %s", fp, e)
                continue
    if font is None:
        font = ImageFont.load_default()

    results = []
    for i, line in enumerate(content.splitlines()):
        if not line.startswith("Dialogue:"):
            continue
        parts = line.split(",", 9)
        if len(parts) < 10:
            continue
        start_sec = _ass_time_to_seconds(parts[1].strip())
        end_sec = _ass_time_to_seconds(parts[2].strip())
        text = parts[9].strip()
        if start_sec is None or end_sec is None or not text:
            continue

        # Create transparent image at Shorts resolution
        img = Image.new("RGBA", (SHORTS_WIDTH, SHORTS_HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Word-wrap text to fit width with padding
        max_text_width = SHORTS_WIDTH - 120  # 60px padding each side
        wrapped_lines = _wrap_text_pillow(draw, text, font, max_text_width)
        line_height = cfg["font_size"] + 8

        # Position: bottom-center, 180px from bottom
        total_text_height = len(wrapped_lines) * line_height
        y_start = SHORTS_HEIGHT - 180 - total_text_height

        for j, wline in enumerate(wrapped_lines):
            bbox = draw.textbbox((0, 0), wline, font=font)
            text_w = bbox[2] - bbox[0]
            x = (SHORTS_WIDTH - text_w) // 2
            y = y_start + j * line_height

            # Draw outline/stroke
            ow = cfg["outline_w"]
            outline_color = cfg["outline"]
            for dx in range(-ow, ow + 1):
                for dy in range(-ow, ow + 1):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((x + dx, y + dy), wline, font=font, fill=outline_color)

            # Draw main text
            draw.text((x, y), wline, font=font, fill=cfg["color"])

        png_path = os.path.join(output_dir, f"caption_{i:03d}.png")
        img.save(png_path)
        results.append({"path": png_path, "start": start_sec, "end": end_sec})

    return results


def _wrap_text_pillow(draw, text: str, font, max_width: int) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = []
    for word in words:
        test_line = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines if lines else [text]


def _build_render_cmd(
    input_path: str,
    output_path: str,
    subtitle_path: Optional[str] = None,
    watermark: bool = False,
    use_subtitles: bool = True,
    skip_loudnorm: bool = False,
    crop_x_expr: Optional[str] = None,
    aspect_ratio: str = "9:16",
    audio_normalization: bool = True,
) -> list[str]:
    """Build the FFmpeg render command with blur-fill background.

    Instead of black bars, creates a blurred+scaled version of the source as
    background, then overlays the face-cropped sharp foreground on top.
    This produces native-looking vertical shorts from landscape source video.
    """
    width, height = ASPECT_RESOLUTIONS.get(aspect_ratio, (1080, 1920))
    ar_ffmpeg = ASPECT_RATIOS_FFMPEG.get(aspect_ratio, "9/16")

    # Probe input to decide layout strategy
    video_info = _probe_video_stream(input_path)
    in_w = int(video_info.get("width", 1920)) if video_info else 1920
    in_h = int(video_info.get("height", 1080)) if video_info else 1080
    is_landscape = in_w > in_h

    # Audio filter: loudnorm can fail on short clips (<3s), so it's skippable
    if not audio_normalization or skip_loudnorm:
        af = "apad=pad_dur=0.3"
    else:
        af = "loudnorm=I=-14:TP=-1:LRA=11,apad=pad_dur=0.3"

    if not is_landscape:
        # Source is already portrait — just scale to fit, no crop needed
        vf_parts = [
            f"scale={width}:{height}:force_original_aspect_ratio=decrease",
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
        ]
        if use_subtitles and subtitle_path and os.path.exists(subtitle_path):
            if _has_subtitles_filter():
                sub_escaped = subtitle_path.replace("\\", "/").replace(":", "\\:")
                vf_parts.append(f"subtitles='{sub_escaped}'")
        if watermark:
            vf_parts.append(
                f"drawtext=text='{WATERMARK_TEXT}':fontsize={WATERMARK_FONT_SIZE}"
                f":fontcolor=white@{WATERMARK_OPACITY}:x=w-tw-20:y=h-th-20:font=Arial"
            )
        return [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", ",".join(vf_parts),
            "-af", af,
            "-c:v", VIDEO_CODEC, "-preset", ENCODER_PRESET, "-crf", CRF_QUALITY,
            "-c:a", AUDIO_CODEC, "-b:a", AUDIO_BITRATE,
            "-movflags", "+faststart",
            "-t", str(MAX_SHORT_DURATION_SECONDS),
            output_path,
        ]

    # ── Landscape → Portrait with blur-fill background ──
    # Background: scale source to fill the output frame (crop overflow), then blur
    # Foreground: face-aware crop to 9:16 aspect, scale to fit within output

    crop_w_expr = f"max(min(ih*{ar_ffmpeg},iw),2)"
    if crop_x_expr is None:
        crop_x_expr = f"(iw-{crop_w_expr})/2"

    # Build filter_complex graph:
    # [0:v] → split into bg + fg
    # bg: scale to fill output (may crop edges), apply heavy gaussian blur
    # fg: face-aware crop, scale to fit
    # overlay fg centered on bg
    filter_parts = []

    # Split input into two streams
    filter_parts.append("[0:v]split=2[bg_in][fg_in]")

    # Background: scale to fill (cover) the output dimensions, then blur heavily
    # scale2ref isn't needed — we just scale to fill and crop overflow
    filter_parts.append(
        f"[bg_in]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height}:(iw-{width})/2:(ih-{height})/2,"
        f"gblur=sigma=40[bg]"
    )

    # Foreground: face-aware crop to portrait aspect ratio, then scale to fit
    filter_parts.append(
        f"[fg_in]crop='{crop_w_expr}':ih:'{crop_x_expr}':0,"
        f"scale={width}:{height}:force_original_aspect_ratio=decrease[fg]"
    )

    # Overlay foreground centered on blurred background
    filter_parts.append(
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[composed]"
    )

    # Add subtitles and watermark on the composed output
    post_filters = []
    if use_subtitles and subtitle_path and os.path.exists(subtitle_path):
        if _has_subtitles_filter():
            sub_escaped = subtitle_path.replace("\\", "/").replace(":", "\\:")
            post_filters.append(f"subtitles='{sub_escaped}'")

    if watermark:
        post_filters.append(
            f"drawtext=text='{WATERMARK_TEXT}':fontsize={WATERMARK_FONT_SIZE}"
            f":fontcolor=white@{WATERMARK_OPACITY}:x=w-tw-20:y=h-th-20:font=Arial"
        )

    if post_filters:
        filter_parts.append(f"[composed]{','.join(post_filters)}[vout]")
        map_label = "[vout]"
    else:
        map_label = "[composed]"

    filter_complex = ";".join(filter_parts)

    return [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex", filter_complex,
        "-map", map_label,
        "-map", "0:a",
        "-af", af,
        "-c:v", VIDEO_CODEC, "-preset", ENCODER_PRESET, "-crf", CRF_QUALITY,
        "-c:a", AUDIO_CODEC, "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart",
        "-t", str(MAX_SHORT_DURATION_SECONDS),
        output_path,
    ]


def _overlay_caption_pngs(
    video_path: str,
    caption_pngs: list[dict],
    output_path: str,
) -> FFmpegResult:
    """Overlay Pillow-rendered caption PNGs onto video using FFmpeg overlay filter.

    Each caption PNG is a full-resolution transparent image composited with
    enable='between(t,start,end)' so it appears only during its time window.
    """
    if not caption_pngs:
        return FFmpegResult(success=False, output_path=output_path, error="No caption images")

    # Build filter_complex: chain overlays for each caption image
    inputs = ["-i", video_path]
    for cap in caption_pngs:
        inputs.extend(["-i", cap["path"]])

    # Build overlay chain: [0:v] -> overlay with [1:v] -> overlay with [2:v] -> ...
    filter_parts = []
    prev_label = "[0:v]"
    for i, cap in enumerate(caption_pngs):
        input_idx = i + 1
        out_label = f"[v{i}]" if i < len(caption_pngs) - 1 else "[vout]"
        enable = f"between(t,{cap['start']:.2f},{cap['end']:.2f})"
        filter_parts.append(
            f"{prev_label}[{input_idx}:v]overlay=0:0:enable='{enable}'{out_label}"
        )
        prev_label = out_label

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "0:a",
        "-c:v", VIDEO_CODEC, "-preset", ENCODER_PRESET, "-crf", CRF_QUALITY,
        "-c:a", AUDIO_CODEC, "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart",
        "-t", str(MAX_SHORT_DURATION_SECONDS),
        output_path,
    ]

    return _run_ffmpeg_render(cmd, output_path)


def render_short(
    input_path: str,
    subtitle_path: str,
    output_path: str,
    watermark: bool = False,
    caption_style: str = "clean",
    aspect_ratio: str = "9:16",
    audio_normalization: bool = True,
) -> FFmpegResult:
    """
    Single-pass FFmpeg render: 16:9 → 9:16 + audio normalization + captions + watermark.
    Uses Pillow PNG overlay when libass/drawtext are unavailable.
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

    # Face-aware crop: detect face position(s) and build adaptive crop expression
    crop_x_expr = _detect_face_crop_x(input_path)

    # Check if we need Pillow fallback for captions
    needs_pillow_captions = (
        subtitle_path
        and os.path.exists(subtitle_path)
        and not _has_subtitles_filter()
    )

    # Attempt 1: full pipeline (subtitles via libass + loudnorm)
    cmd = _build_render_cmd(input_path, output_path, subtitle_path, watermark, use_subtitles=True, crop_x_expr=crop_x_expr, aspect_ratio=aspect_ratio, audio_normalization=audio_normalization)
    result = _run_ffmpeg_render(cmd, output_path)
    if result.success:
        if needs_pillow_captions:
            # Render succeeded but without captions — overlay them via Pillow
            result = _apply_pillow_captions(output_path, subtitle_path, caption_style)
        return result

    # If render produced non-zero frames but still failed — don't retry
    # FFmpeg outputs "frame=    0" with variable whitespace, so use regex
    zero_frames = bool(result.error and re.search(r"frame=\s*0\s", result.error))
    if result.error and "frame=" in result.error and not zero_frames:
        return result

    # Attempt 2: skip loudnorm (it misbehaves on short clips ~3s or less)
    logger.warning("Render produced 0 frames, retrying without loudnorm")
    cmd = _build_render_cmd(input_path, output_path, subtitle_path, watermark, use_subtitles=True, skip_loudnorm=True, crop_x_expr=crop_x_expr, aspect_ratio=aspect_ratio, audio_normalization=audio_normalization)
    result = _run_ffmpeg_render(cmd, output_path)
    if result.success:
        if needs_pillow_captions:
            result = _apply_pillow_captions(output_path, subtitle_path, caption_style)
        return result

    # Attempt 3: skip both loudnorm and subtitles
    logger.warning("Retry without loudnorm failed, trying without subtitles too")
    cmd = _build_render_cmd(input_path, output_path, subtitle_path, watermark, use_subtitles=False, skip_loudnorm=True, crop_x_expr=crop_x_expr, aspect_ratio=aspect_ratio, audio_normalization=audio_normalization)
    result = _run_ffmpeg_render(cmd, output_path)
    if result.success:
        if needs_pillow_captions:
            result = _apply_pillow_captions(output_path, subtitle_path, caption_style)
        return result

    # Attempt 4: minimal pipeline with blur-fill (no crop, no loudnorm)
    logger.warning("All retries failed, trying minimal pipeline")
    width, height = ASPECT_RESOLUTIONS.get(aspect_ratio, (1080, 1920))
    # Still use blur-fill background even in fallback — avoids black bars
    minimal_filter = (
        f"[0:v]split=2[mbg][mfg];"
        f"[mbg]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height}:(iw-{width})/2:(ih-{height})/2,"
        f"gblur=sigma=40[mbg2];"
        f"[mfg]scale={width}:{height}:force_original_aspect_ratio=decrease[mfg2];"
        f"[mbg2][mfg2]overlay=(W-w)/2:(H-h)/2[mvout]"
    )
    cmd_minimal = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex", minimal_filter,
        "-map", "[mvout]",
        "-map", "0:a",
        "-c:v", VIDEO_CODEC, "-preset", ENCODER_PRESET, "-crf", CRF_QUALITY,
        "-c:a", AUDIO_CODEC, "-b:a", AUDIO_BITRATE,
        "-movflags", "+faststart",
        "-t", str(MAX_SHORT_DURATION_SECONDS),
        output_path,
    ]
    result = _run_ffmpeg_render(cmd_minimal, output_path)
    if result.success and needs_pillow_captions:
        result = _apply_pillow_captions(output_path, subtitle_path, caption_style)
    return result


def _apply_pillow_captions(
    video_path: str,
    subtitle_path: str,
    caption_style: str,
) -> FFmpegResult:
    """Overlay Pillow-rendered captions onto an already-rendered video."""
    import tempfile
    caption_dir = tempfile.mkdtemp(prefix="hookcut_captions_")
    try:
        caption_pngs = _render_caption_pngs(subtitle_path, caption_dir, style=caption_style)
        if not caption_pngs:
            logger.warning("No caption PNGs generated — video will have no captions")
            return FFmpegResult(
                success=True, output_path=video_path,
                duration_seconds=probe_duration(video_path),
                file_size_bytes=os.path.getsize(video_path) if os.path.exists(video_path) else None,
            )

        # Overlay onto video — write to temp, then replace original
        captioned_path = video_path + ".captioned.mp4"
        result = _overlay_caption_pngs(video_path, caption_pngs, captioned_path)
        if result.success:
            os.replace(captioned_path, video_path)
            result = FFmpegResult(
                success=True, output_path=video_path,
                duration_seconds=probe_duration(video_path),
                file_size_bytes=os.path.getsize(video_path) if os.path.exists(video_path) else None,
            )
        else:
            logger.warning("Pillow caption overlay failed: %s — video will have no captions", result.error)
            # Clean up failed output
            if os.path.exists(captioned_path):
                os.remove(captioned_path)
            result = FFmpegResult(
                success=True, output_path=video_path,
                duration_seconds=probe_duration(video_path),
                file_size_bytes=os.path.getsize(video_path) if os.path.exists(video_path) else None,
            )
        return result
    except Exception as e:
        logger.warning("Pillow caption rendering failed: %s — video will have no captions", e)
        return FFmpegResult(
            success=True, output_path=video_path,
            duration_seconds=probe_duration(video_path),
            file_size_bytes=os.path.getsize(video_path) if os.path.exists(video_path) else None,
        )


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


# ── Interview mode: split-screen rendering ──────────────────────────────────

# Interview layout values stored on Short.interview_layout
INTERVIEW_LAYOUT_SPLIT_2 = "split_2"
INTERVIEW_LAYOUT_SPLIT_3PLUS = "split_3plus"
INTERVIEW_LAYOUT_NORMAL = "normal"


def _build_active_speaker_expr(utterances: list[dict], speaker_label: str) -> str:
    """Build FFmpeg if(between(t,...)) expression for when a speaker is active."""
    segments = [u for u in utterances if u.get("speaker") == speaker_label]
    if not segments:
        logger.warning("No diarization segments found for '%s' — speaker border will be inactive", speaker_label)
        return "0"
    parts = [f"between(t,{u['start_ms']/1000:.2f},{u['end_ms']/1000:.2f})" for u in segments]
    # Chain with + (acts as OR in FFmpeg expressions)
    return "+".join(parts)


def render_interview_short(
    input_path: str,
    subtitle_path: str,
    output_path: str,
    speaker_faces: list,  # list[FaceRegion] — avoid circular import
    diarization_data: list[dict],
    watermark: bool = False,
    caption_style: str = "clean",
    aspect_ratio: str = "9:16",
    audio_normalization: bool = True,
) -> FFmpegResult:
    """Render a split-screen interview Short with active speaker emphasis.

    2-speaker: top/bottom vertical stack, each showing one speaker's face region.
    3+ speaker: top = active speaker (switches), bottom = full wide shot.
    Fallback: if filter graph fails, falls back to normal render_short.
    """
    width, height = ASPECT_RESOLUTIONS.get(aspect_ratio, (1080, 1920))
    panel_height = (height - 60) // 2  # 60px gap between panels

    # Probe input dimensions
    video_info = _probe_video_stream(input_path)
    if not video_info:
        return render_short(input_path, subtitle_path, output_path, watermark, caption_style, aspect_ratio, audio_normalization)

    in_w = int(video_info.get("width", 1920))
    in_h = int(video_info.get("height", 1080))

    # Split-screen needs landscape source
    if in_w <= in_h:
        logger.info("Source is portrait (%dx%d) — using normal render", in_w, in_h)
        return render_short(input_path, subtitle_path, output_path, watermark, caption_style, aspect_ratio, audio_normalization)

    if len(speaker_faces) == 2:
        vf = _build_2speaker_filter(
            speaker_faces, diarization_data, in_w, in_h,
            width, panel_height, subtitle_path,
        )
    else:
        vf = _build_3plus_filter(
            speaker_faces, diarization_data, in_w, in_h,
            width, panel_height, subtitle_path,
        )

    # Attempt 1: full split-screen + loudnorm
    af = "loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur=0.3" if audio_normalization else "apad=pad_dur=0.3"
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
    result = _run_ffmpeg_render(cmd, output_path)
    if result.success:
        return result

    # Attempt 2: split-screen without loudnorm
    logger.warning("Interview render attempt 1 failed, retrying without loudnorm")
    af_simple = "apad=pad_dur=0.3"
    cmd[cmd.index("-af") + 1] = af_simple
    result = _run_ffmpeg_render(cmd, output_path)
    if result.success:
        return result

    # Attempt 3: split-screen without captions
    logger.warning("Interview render attempt 2 failed, retrying without captions")
    # Subtitles are appended as ";[stacked]subtitles=..." — remove that segment
    if ";[stacked]subtitles=" in vf:
        vf_no_subs = vf.split(";[stacked]subtitles=")[0]
    elif ",subtitles=" in vf:
        vf_no_subs = vf.split(",subtitles=")[0]
    else:
        vf_no_subs = vf
    cmd[cmd.index("-vf") + 1] = vf_no_subs
    result = _run_ffmpeg_render(cmd, output_path)
    if result.success:
        return result

    # Attempt 4: fall back to normal render
    logger.warning("All interview render attempts failed, falling back to normal render")
    return render_short(input_path, subtitle_path, output_path, watermark, caption_style, aspect_ratio, audio_normalization)


def _build_2speaker_filter(
    faces: list, utterances: list[dict],
    in_w: int, in_h: int,
    out_w: int, panel_h: int,
    subtitle_path: str,
) -> str:
    """Build FFmpeg filter graph for 2-speaker interview split-screen.

    Layout: Top panel = zoomed close-up (face crop), Bottom panel = full frame.
    Works for both multi-camera interviews (camera cuts between speakers) and
    single-camera wide shots. The face crop follows whoever is on screen,
    creating a zoom + context effect.

    Active speaker gets a cyan border based on diarization timestamps.
    """
    fa, fb = faces[0], faces[1]
    gap = 30

    # Top panel: crop ~60% of frame centered on detected face — creates zoom effect
    crop_h = in_h
    crop_w = min(max(int(in_w * 0.6), 2), in_w)
    face_center_x = fa.x + fa.w // 2
    crop_x = max(0, min(face_center_x - crop_w // 2, in_w - crop_w))

    expr_a = _build_active_speaker_expr(utterances, fa.speaker_label)
    expr_b = _build_active_speaker_expr(utterances, fb.speaker_label)

    parts = [
        f"[0:v]split=2[src1][src2]",
        # Top: zoomed crop centered on detected face
        f"[src1]crop={crop_w}:{crop_h}:{crop_x}:0,scale={out_w}:{panel_h}[top]",
        # Bottom: full frame scaled to fit
        f"[src2]scale={out_w}:{panel_h}:force_original_aspect_ratio=decrease,"
        f"pad={out_w}:{panel_h}:(ow-iw)/2:(oh-ih)/2:black[bot]",
        # Active speaker borders
        f"[top]drawbox=x=0:y=0:w={out_w}:h={panel_h}:color=cyan@0.8:t=4:"
        f"enable='{expr_a}'[top_e]",
        f"[bot]drawbox=x=0:y=0:w={out_w}:h={panel_h}:color=cyan@0.8:t=4:"
        f"enable='{expr_b}'[bot_e]",
        f"[top_e]pad={out_w}:{panel_h + gap}:0:0:black[top_pad]",
        f"[bot_e]pad={out_w}:{panel_h + gap}:0:{gap}:black[bot_pad]",
        f"[top_pad][bot_pad]vstack=inputs=2[stacked]",
        ]

    # Add subtitles if available (FFmpeg auto-maps the last output pad)
    if subtitle_path and os.path.exists(subtitle_path):
        escaped_path = subtitle_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "'\\''")
        parts.append(f"[stacked]subtitles='{escaped_path}'[out]")

    return ";".join(parts)


def _build_3plus_filter(
    faces: list, utterances: list[dict],
    in_w: int, in_h: int,
    out_w: int, panel_h: int,
    subtitle_path: str,
) -> str:
    """Build FFmpeg filter for 3+ speakers: close-up of first speaker on top, wide shot on bottom."""
    fa = faces[0]
    gap = 30

    # Top panel: portrait crop centered on first speaker
    crop_h = in_h
    panel_aspect = out_w / panel_h
    crop_w = min(int(crop_h * panel_aspect), in_w)
    face_center_x = fa.x + fa.w // 2
    crop_x = max(0, min(face_center_x - crop_w // 2, in_w - crop_w))

    parts = [
        f"[0:v]split=2[src1][src2]",
        f"[src1]crop={crop_w}:{crop_h}:{crop_x}:0,scale={out_w}:{panel_h}[top]",
        # Bottom: full wide shot scaled to fit
        f"[src2]scale={out_w}:{panel_h}:force_original_aspect_ratio=decrease,pad={out_w}:{panel_h}:(ow-iw)/2:(oh-ih)/2:black[bot]",
        f"[top]pad={out_w}:{panel_h + gap}:0:0:black[top_pad]",
        f"[bot]pad={out_w}:{panel_h + gap}:0:{gap}:black[bot_pad]",
        f"[top_pad][bot_pad]vstack=inputs=2[stacked]",
    ]

    if subtitle_path and os.path.exists(subtitle_path):
        escaped_path = subtitle_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "'\\''")
        parts.append(f"[stacked]subtitles='{escaped_path}'[out]")

    return ";".join(parts)
