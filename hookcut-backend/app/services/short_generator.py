import os
import tempfile
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable, Optional

from app.llm.provider import get_provider
from app.llm.prompts.caption_cleanup import build_caption_cleanup_prompt, build_title_generation_prompt
from app.utils.time_format import parse_composite_timestamps
from app.utils.ffmpeg_commands import (
    extract_segment, concat_segments, generate_ass_subtitles,
    render_short, extract_thumbnail, probe_duration,
)
from app.config import get_settings
from app.exceptions import ShortGenerationError

logger = logging.getLogger(__name__)


@dataclass
class ShortResult:
    video_path: str
    thumbnail_path: str
    title: str
    cleaned_captions: str
    duration_seconds: Optional[float]
    file_size_bytes: Optional[int]


class ShortGenerator:
    """
    Full Short generation pipeline:
    1. yt-dlp segment extraction
    2. LLM caption cleanup + title generation
    3. FFmpeg single-pass render (9:16, audio, captions, watermark)
    4. Thumbnail extraction
    """

    def generate(
        self,
        youtube_url: str,
        hook: dict,
        session_id: str,
        short_id: str,
        is_watermarked: bool,
        language: str = "English",
        niche: str = "Generic",
        caption_style: str = "clean",
        on_progress: Optional[Callable[[str, int, str], None]] = None,
    ) -> ShortResult:
        def _progress(status: str, pct: int, label: str):
            if on_progress:
                on_progress(status, pct, label)

        work_dir = tempfile.mkdtemp(prefix=f"hookcut_short_{short_id[:8]}_")

        try:
            # Step 1: Signal download start, then run yt-dlp + LLM calls in parallel
            _progress("downloading", 35, "Downloading segment...")
            with ThreadPoolExecutor(max_workers=3) as executor:
                segment_future = executor.submit(
                    self._extract_segments, youtube_url, hook, work_dir
                )
                caption_future = executor.submit(
                    self._clean_captions, hook["hook_text"], language
                )
                title_future = executor.submit(
                    self._generate_title,
                    hook["hook_text"], niche, language,
                    hook.get("hook_type", ""),
                    hook.get("attention_score", 0.0),
                )

                segment_path = segment_future.result()
                cleaned_captions = caption_future.result()
                title = title_future.result()

            # Step 2: Signal render start
            _progress("processing", 65, "Rendering video...")

            # Step 3: Generate ASS subtitles
            segment_duration = probe_duration(segment_path) or 30.0
            segment_size = os.path.getsize(segment_path) if os.path.exists(segment_path) else 0
            logger.info(
                "Segment ready: path=%s size=%d bytes duration=%.1fs",
                segment_path, segment_size, segment_duration,
            )
            subtitle_path = os.path.join(work_dir, "captions.ass")
            generate_ass_subtitles(cleaned_captions, segment_duration, subtitle_path, style=caption_style)

            # Step 5: Single-pass FFmpeg render
            output_path = os.path.join(work_dir, "output.mp4")
            render_result = render_short(
                input_path=segment_path,
                subtitle_path=subtitle_path,
                output_path=output_path,
                watermark=is_watermarked,
            )
            if not render_result.success:
                logger.error(
                    "FFmpeg render failed for short %s: %s (input=%s, size=%d)",
                    short_id, render_result.error, segment_path, segment_size,
                )
                raise ShortGenerationError(f"FFmpeg render failed: {render_result.error}")

            # Step 6: Extract thumbnail
            thumbnail_path = os.path.join(work_dir, "thumbnail.jpg")
            thumb_result = extract_thumbnail(output_path, thumbnail_path)
            if not thumb_result.success:
                logger.warning(f"Thumbnail extraction failed: {thumb_result.error}")
                thumbnail_path = ""

            return ShortResult(
                video_path=output_path,
                thumbnail_path=thumbnail_path,
                title=title,
                cleaned_captions=cleaned_captions,
                duration_seconds=render_result.duration_seconds,
                file_size_bytes=render_result.file_size_bytes,
            )

        except ShortGenerationError:
            raise
        except Exception as e:
            raise ShortGenerationError(f"Short generation failed: {e}")

    def _extract_segments(self, youtube_url: str, hook: dict, work_dir: str) -> str:
        """Extract segment(s) using yt-dlp. Handles composite hooks."""
        is_composite = hook.get("is_composite", False)

        if is_composite and "+" in str(hook.get("start_time", "")):
            segments = parse_composite_timestamps(hook["start_time"], hook["end_time"])
            segment_paths = []
            for i, (start, end) in enumerate(segments):
                seg_path = os.path.join(work_dir, f"seg_{i}.mp4")
                result = extract_segment(youtube_url, start, end, seg_path)
                if not result.success:
                    raise ShortGenerationError(
                        f"Segment extraction failed for part {i}: {result.error}"
                    )
                segment_paths.append(seg_path)

            combined_path = os.path.join(work_dir, "combined.mp4")
            concat_result = concat_segments(segment_paths, combined_path)
            if not concat_result.success:
                raise ShortGenerationError(
                    f"Segment concatenation failed: {concat_result.error}"
                )
            return combined_path
        else:
            start = hook.get("start_seconds", 0)
            end = hook.get("end_seconds", 30)
            seg_path = os.path.join(work_dir, "segment.mp4")
            result = extract_segment(youtube_url, start, end, seg_path)
            if not result.success:
                raise ShortGenerationError(f"Segment extraction failed: {result.error}")
            return seg_path

    def _clean_captions(self, hook_text: str, language: str) -> str:
        """Use LLM to clean transcript text for captions."""
        try:
            settings = get_settings()
            provider = get_provider(settings.LLM_PRIMARY_PROVIDER)
            prompt = build_caption_cleanup_prompt(hook_text, language)
            response = provider.generate(prompt, max_tokens=500)
            cleaned = response.text.strip()
            return cleaned if cleaned else hook_text
        except Exception as e:
            logger.warning(f"Caption cleanup failed, using raw text: {e}")
            return hook_text

    def _generate_title(
        self,
        hook_text: str,
        niche: str,
        language: str,
        hook_type: str = "",
        attention_score: float = 0.0,
    ) -> str:
        """Use LLM to generate a catchy Short-optimized title."""
        try:
            settings = get_settings()
            provider = get_provider(settings.LLM_PRIMARY_PROVIDER)
            prompt = build_title_generation_prompt(
                hook_text, niche, language,
                hook_type=hook_type,
                attention_score=attention_score,
            )
            response = provider.generate(prompt, max_tokens=100)
            title = response.text.strip().strip('"').strip("'")
            return title[:60] if title else _title_from_hook_text(hook_text)
        except Exception as e:
            logger.warning(f"Title generation failed: {e}")
            return _title_from_hook_text(hook_text)


def _title_from_hook_text(hook_text: str) -> str:
    """Generate a simple title from the first words of the hook when LLM is unavailable."""
    words = hook_text.split()
    title = " ".join(words[:8])
    if len(words) > 8:
        title = title.rstrip(".,;:!?") + "..."
    return title[:60] if title else "Short"
