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
    render_short, render_interview_short, extract_thumbnail, probe_duration,
    INTERVIEW_LAYOUT_SPLIT_2, INTERVIEW_LAYOUT_SPLIT_3PLUS, INTERVIEW_LAYOUT_NORMAL,
)
from app.config import get_settings
from app.exceptions import ShortGenerationError
from app.utils.text import title_from_hook_text

logger = logging.getLogger(__name__)


@dataclass
class ShortResult:
    video_path: str
    thumbnail_path: str
    title: str
    cleaned_captions: str
    duration_seconds: Optional[float]
    file_size_bytes: Optional[int]
    interview_layout: Optional[str] = None


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
        hook: Optional[dict],
        session_id: str,
        short_id: str,
        is_watermarked: bool,
        language: str = "English",
        niche: str = "Generic",
        caption_style: str = "clean",
        transcript_text: str = "",
        aspect_ratio: str = "9:16",
        captions_enabled: bool = True,
        audio_normalization: bool = True,
        source_type: str = "ai",
        start_seconds: Optional[float] = None,
        end_seconds: Optional[float] = None,
        video_title: Optional[str] = None,
        interview_mode: bool = False,
        speaker_count: int = 2,
        diarization_data: Optional[list[dict]] = None,
        on_progress: Optional[Callable[[str, int, str], None]] = None,
    ) -> ShortResult:
        def _progress(status: str, pct: int, label: str):
            if on_progress:
                on_progress(status, pct, label)

        work_dir = tempfile.mkdtemp(prefix=f"hookcut_short_{short_id[:8]}_")

        try:
            # Step 1: Download segment (sequential — LLM calls wait until done
            # to avoid hitting Gemini concurrently with other in-flight shorts)
            _progress("downloading", 35, "Downloading segment...")
            if hook is not None:
                segment_path = self._extract_segments(youtube_url, hook, work_dir, prefer_high_res=interview_mode)
            else:
                # Manual clip: use start_seconds/end_seconds directly
                seg_path = os.path.join(work_dir, "segment.mp4")
                result = extract_segment(youtube_url, start_seconds or 0, end_seconds or 30, seg_path, prefer_high_res=interview_mode)
                if not result.success:
                    raise ShortGenerationError(f"Segment extraction failed: {result.error}")
                segment_path = seg_path

            # Step 2: Caption cleanup + title generation
            _progress("processing", 55, "Generating captions & title...")

            if hook is not None:
                hook_text = hook["hook_text"]
            elif captions_enabled and transcript_text:
                # For manual clips with captions, extract relevant portion
                hook_text = transcript_text
            else:
                hook_text = ""

            if captions_enabled and hook_text:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    caption_future = executor.submit(
                        self._clean_captions, hook_text, language
                    )
                    title_future = executor.submit(
                        self._generate_title,
                        hook_text, niche, language,
                        hook.get("hook_type", "") if hook else "",
                        hook.get("attention_score", 0.0) if hook else 0.0,
                        video_title=video_title or "",
                    )
                    cleaned_captions = caption_future.result()
                    title = title_future.result()
            else:
                cleaned_captions = ""
                # Always attempt LLM title generation — even without captions,
                # the video title provides enough context for a good title.
                title = self._generate_title(
                    hook_text or "", niche, language,
                    video_title=video_title or "",
                )

            # Step 3: Signal render start
            _progress("processing", 65, "Rendering video...")

            # Step 4: Generate ASS subtitles (only if captions enabled)
            segment_duration = probe_duration(segment_path) or 30.0
            segment_size = os.path.getsize(segment_path) if os.path.exists(segment_path) else 0
            logger.info(
                "Segment ready: path=%s size=%d bytes duration=%.1fs",
                segment_path, segment_size, segment_duration,
            )

            subtitle_path = os.path.join(work_dir, "captions.ass")
            if captions_enabled and cleaned_captions:
                hook_start = (hook.get("start_seconds", 0.0) or 0.0) if hook else (start_seconds or 0.0)
                hook_end = (hook.get("end_seconds", 0.0) or 0.0) if hook else (end_seconds or 0.0)
                generate_ass_subtitles(
                    cleaned_captions, segment_duration, subtitle_path,
                    style=caption_style,
                    transcript_text=transcript_text,
                    start_seconds=hook_start,
                    end_seconds=hook_end,
                )
            else:
                subtitle_path = None  # No captions

            # Step 5: Single-pass FFmpeg render
            output_path = os.path.join(work_dir, "output.mp4")
            interview_layout = None

            if interview_mode and diarization_data:
                from app.utils.face_mapping import detect_speaker_faces
                speaker_faces = detect_speaker_faces(segment_path, speaker_count)

                # Filter diarization to only utterances within this segment's time range
                # and adjust timestamps to be relative to segment start
                seg_start_ms = int((start_seconds or (hook.get("start_seconds", 0) if hook else 0)) * 1000)
                seg_end_ms = int((end_seconds or (hook.get("end_seconds", 30) if hook else 30)) * 1000)
                segment_diarization = []
                for u in diarization_data:
                    u_start = u.get("start_ms", 0)
                    u_end = u.get("end_ms", 0)
                    # Keep if overlaps with segment
                    if u_end > seg_start_ms and u_start < seg_end_ms:
                        segment_diarization.append({
                            "speaker": u["speaker"],
                            "start_ms": max(0, u_start - seg_start_ms),
                            "end_ms": min(seg_end_ms - seg_start_ms, u_end - seg_start_ms),
                            "text": u.get("text", ""),
                        })
                logger.info(
                    "Filtered diarization: %d/%d utterances for segment %d-%dms",
                    len(segment_diarization), len(diarization_data), seg_start_ms, seg_end_ms,
                )

                if speaker_faces:
                    interview_layout = INTERVIEW_LAYOUT_SPLIT_2 if len(speaker_faces) == 2 else INTERVIEW_LAYOUT_SPLIT_3PLUS
                    render_result = render_interview_short(
                        input_path=segment_path,
                        subtitle_path=subtitle_path or "",
                        output_path=output_path,
                        speaker_faces=speaker_faces,
                        diarization_data=segment_diarization,
                        watermark=is_watermarked,
                        caption_style=caption_style,
                        aspect_ratio=aspect_ratio,
                        audio_normalization=audio_normalization,
                    )
                else:
                    interview_layout = INTERVIEW_LAYOUT_NORMAL
                    logger.info("Face detection found no speakers — using normal render for short %s", short_id)
                    render_result = render_short(
                        input_path=segment_path,
                        subtitle_path=subtitle_path or "",
                        output_path=output_path,
                        watermark=is_watermarked,
                        caption_style=caption_style,
                        aspect_ratio=aspect_ratio,
                        audio_normalization=audio_normalization,
                    )
            else:
                render_result = render_short(
                    input_path=segment_path,
                    subtitle_path=subtitle_path or "",
                    output_path=output_path,
                    watermark=is_watermarked,
                    caption_style=caption_style,
                    aspect_ratio=aspect_ratio,
                    audio_normalization=audio_normalization,
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
                interview_layout=interview_layout,
            )

        except ShortGenerationError:
            raise
        except Exception as e:
            raise ShortGenerationError(f"Short generation failed: {e}")

    def _extract_segments(self, youtube_url: str, hook: dict, work_dir: str, prefer_high_res: bool = False) -> str:
        """Extract segment(s) using yt-dlp. Handles composite hooks."""
        is_composite = hook.get("is_composite", False)

        if is_composite and "+" in str(hook.get("start_time", "")):
            segments = parse_composite_timestamps(hook["start_time"], hook["end_time"])
            segment_paths = []
            for i, (start, end) in enumerate(segments):
                seg_path = os.path.join(work_dir, f"seg_{i}.mp4")
                result = extract_segment(youtube_url, start, end, seg_path, prefer_high_res=prefer_high_res)
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
            result = extract_segment(youtube_url, start, end, seg_path, prefer_high_res=prefer_high_res)
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
        video_title: str = "",
    ) -> str:
        """Use LLM to generate a catchy Short-optimized title."""
        try:
            settings = get_settings()
            provider = get_provider(settings.LLM_PRIMARY_PROVIDER)
            prompt = build_title_generation_prompt(
                hook_text, niche, language,
                hook_type=hook_type,
                attention_score=attention_score,
                video_title=video_title,
            )
            response = provider.generate(prompt, max_tokens=100)
            title = response.text.strip().strip('"').strip("'")
            if title:
                return title[:60]
            # Fallback: use hook text or video title
            if hook_text:
                return title_from_hook_text(hook_text)
            if video_title:
                return title_from_hook_text(video_title)
            return "Short"
        except Exception as e:
            logger.warning(f"Title generation failed: {e}")
            if hook_text:
                return title_from_hook_text(hook_text)
            if video_title:
                return title_from_hook_text(video_title)
            return "Short"


