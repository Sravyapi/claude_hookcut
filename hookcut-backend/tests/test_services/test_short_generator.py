"""Tests for ShortGenerator — video generation pipeline."""
import os
from unittest.mock import patch, MagicMock, call

import pytest

from app.services.short_generator import ShortGenerator, ShortResult
from app.exceptions import ShortGenerationError
from app.utils.ffmpeg_commands import FFmpegResult


# ─── Helpers ───

def _ok_ffmpeg(**kwargs) -> FFmpegResult:
    """Return a successful FFmpegResult."""
    defaults = dict(
        success=True,
        output_path="/tmp/output.mp4",
        error=None,
        duration_seconds=28.5,
        file_size_bytes=1_200_000,
    )
    defaults.update(kwargs)
    return FFmpegResult(**defaults)


def _fail_ffmpeg(error="ffmpeg error") -> FFmpegResult:
    return FFmpegResult(success=False, output_path="", error=error)


def _make_hook(**kwargs):
    base = {
        "hook_text": "This is the hook text",
        "hook_type": "Curiosity Gap",
        "start_seconds": 5.0,
        "end_seconds": 35.0,
        "start_time": "0:05",
        "end_time": "0:35",
        "attention_score": 8.5,
        "is_composite": False,
    }
    base.update(kwargs)
    return base


# ─── Shared patches used in most tests ───

_PATCH_EXTRACT = "app.services.short_generator.extract_segment"
_PATCH_CONCAT = "app.services.short_generator.concat_segments"
_PATCH_PROBE = "app.services.short_generator.probe_duration"
_PATCH_GEN_ASS = "app.services.short_generator.generate_ass_subtitles"
_PATCH_RENDER = "app.services.short_generator.render_short"
_PATCH_THUMB = "app.services.short_generator.extract_thumbnail"
_PATCH_PROVIDER = "app.services.short_generator.get_provider"
_PATCH_SETTINGS = "app.services.short_generator.get_settings"


def _mock_provider(caption_text="cleaned captions", title_text="Great Title"):
    mock_prov = MagicMock()
    mock_prov.generate.side_effect = [
        MagicMock(text=caption_text),
        MagicMock(text=title_text),
    ]
    return mock_prov


# ─── Test: generate() happy path ───

class TestGenerateHappyPath:
    def test_returns_short_result_with_expected_fields(self, tmp_path):
        hook = _make_hook()
        generator = ShortGenerator()

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg(output_path=str(tmp_path / "seg.mp4"))) as mock_extract,
            patch(_PATCH_PROBE, return_value=28.0),
            patch(_PATCH_GEN_ASS),
            patch(_PATCH_RENDER, return_value=_ok_ffmpeg(
                output_path=str(tmp_path / "out.mp4"),
                duration_seconds=28.0,
                file_size_bytes=900_000,
            )) as mock_render,
            patch(_PATCH_THUMB, return_value=_ok_ffmpeg(output_path=str(tmp_path / "thumb.jpg"))),
            patch(_PATCH_PROVIDER, return_value=_mock_provider()),
            patch(_PATCH_SETTINGS, return_value=MagicMock()),
            patch("os.path.getsize", return_value=1_000_000),
        ):
            result = generator.generate(
                youtube_url="https://www.youtube.com/watch?v=abc",
                hook=hook,
                session_id="sess-1",
                short_id="short-1",
                is_watermarked=True,
            )

        assert isinstance(result, ShortResult)
        assert result.duration_seconds == 28.0
        assert result.file_size_bytes == 900_000
        assert result.title == "Great Title"
        assert result.cleaned_captions == "cleaned captions"

    def test_progress_callbacks_are_called(self, tmp_path):
        hook = _make_hook()
        generator = ShortGenerator()
        progress_calls = []

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROBE, return_value=28.0),
            patch(_PATCH_GEN_ASS),
            patch(_PATCH_RENDER, return_value=_ok_ffmpeg()),
            patch(_PATCH_THUMB, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROVIDER, return_value=_mock_provider()),
            patch(_PATCH_SETTINGS, return_value=MagicMock()),
            patch("os.path.getsize", return_value=1_000_000),
        ):
            generator.generate(
                youtube_url="https://www.youtube.com/watch?v=abc",
                hook=hook,
                session_id="sess-1",
                short_id="short-1",
                is_watermarked=False,
                on_progress=lambda s, p, l: progress_calls.append((s, p)),
            )

        statuses = [s for s, _ in progress_calls]
        assert "downloading" in statuses
        assert "processing" in statuses

    def test_thumbnail_path_empty_string_when_extraction_fails(self, tmp_path):
        hook = _make_hook()
        generator = ShortGenerator()

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROBE, return_value=28.0),
            patch(_PATCH_GEN_ASS),
            patch(_PATCH_RENDER, return_value=_ok_ffmpeg()),
            patch(_PATCH_THUMB, return_value=_fail_ffmpeg("thumb error")),
            patch(_PATCH_PROVIDER, return_value=_mock_provider()),
            patch(_PATCH_SETTINGS, return_value=MagicMock()),
            patch("os.path.getsize", return_value=1_000_000),
        ):
            result = generator.generate(
                youtube_url="https://www.youtube.com/watch?v=abc",
                hook=hook,
                session_id="sess-1",
                short_id="short-1",
                is_watermarked=True,
            )

        assert result.thumbnail_path == ""


# ─── Test: watermark flag ───

class TestWatermarkFlag:
    def test_watermarked_short_passes_watermark_true_to_render(self, tmp_path):
        hook = _make_hook()
        generator = ShortGenerator()

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROBE, return_value=28.0),
            patch(_PATCH_GEN_ASS),
            patch(_PATCH_RENDER, return_value=_ok_ffmpeg()) as mock_render,
            patch(_PATCH_THUMB, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROVIDER, return_value=_mock_provider()),
            patch(_PATCH_SETTINGS, return_value=MagicMock()),
            patch("os.path.getsize", return_value=1_000_000),
        ):
            generator.generate(
                youtube_url="https://www.youtube.com/watch?v=abc",
                hook=hook,
                session_id="sess-1",
                short_id="short-1",
                is_watermarked=True,
            )

        _, kwargs = mock_render.call_args
        assert kwargs.get("watermark") is True

    def test_unwatermarked_short_passes_watermark_false_to_render(self, tmp_path):
        hook = _make_hook()
        generator = ShortGenerator()

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROBE, return_value=28.0),
            patch(_PATCH_GEN_ASS),
            patch(_PATCH_RENDER, return_value=_ok_ffmpeg()) as mock_render,
            patch(_PATCH_THUMB, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROVIDER, return_value=_mock_provider()),
            patch(_PATCH_SETTINGS, return_value=MagicMock()),
            patch("os.path.getsize", return_value=1_000_000),
        ):
            generator.generate(
                youtube_url="https://www.youtube.com/watch?v=abc",
                hook=hook,
                session_id="sess-1",
                short_id="short-1",
                is_watermarked=False,
            )

        _, kwargs = mock_render.call_args
        assert kwargs.get("watermark") is False


# ─── Test: caption style variations ───

class TestCaptionStyles:
    @pytest.mark.parametrize("style", ["clean", "bold", "neon", "minimal"])
    def test_caption_style_forwarded_to_render(self, style):
        hook = _make_hook()
        generator = ShortGenerator()

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROBE, return_value=28.0),
            patch(_PATCH_GEN_ASS),
            patch(_PATCH_RENDER, return_value=_ok_ffmpeg()) as mock_render,
            patch(_PATCH_THUMB, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROVIDER, return_value=_mock_provider()),
            patch(_PATCH_SETTINGS, return_value=MagicMock()),
            patch("os.path.getsize", return_value=1_000_000),
        ):
            generator.generate(
                youtube_url="https://www.youtube.com/watch?v=abc",
                hook=hook,
                session_id="sess-1",
                short_id="short-1",
                is_watermarked=True,
                caption_style=style,
            )

        _, kwargs = mock_render.call_args
        assert kwargs.get("caption_style") == style

    @pytest.mark.parametrize("style", ["clean", "bold", "neon", "minimal"])
    def test_caption_style_forwarded_to_generate_ass(self, style):
        hook = _make_hook()
        generator = ShortGenerator()

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROBE, return_value=28.0),
            patch(_PATCH_GEN_ASS) as mock_ass,
            patch(_PATCH_RENDER, return_value=_ok_ffmpeg()),
            patch(_PATCH_THUMB, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROVIDER, return_value=_mock_provider()),
            patch(_PATCH_SETTINGS, return_value=MagicMock()),
            patch("os.path.getsize", return_value=1_000_000),
        ):
            generator.generate(
                youtube_url="https://www.youtube.com/watch?v=abc",
                hook=hook,
                session_id="sess-1",
                short_id="short-1",
                is_watermarked=True,
                caption_style=style,
                captions_enabled=True,
            )

        _, kwargs = mock_ass.call_args
        assert kwargs.get("style") == style


# ─── Test: error handling ───

class TestErrorHandling:
    def test_raises_short_generation_error_when_segment_extract_fails(self):
        hook = _make_hook()
        generator = ShortGenerator()

        with patch(_PATCH_EXTRACT, return_value=_fail_ffmpeg("yt-dlp failed")):
            with pytest.raises(ShortGenerationError) as exc_info:
                generator.generate(
                    youtube_url="https://www.youtube.com/watch?v=abc",
                    hook=hook,
                    session_id="sess-1",
                    short_id="short-1",
                    is_watermarked=True,
                )
        assert "Segment extraction failed" in str(exc_info.value)

    def test_raises_short_generation_error_when_render_fails(self):
        hook = _make_hook()
        generator = ShortGenerator()

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROBE, return_value=28.0),
            patch(_PATCH_GEN_ASS),
            patch(_PATCH_RENDER, return_value=_fail_ffmpeg("render failed")) as mock_render,
            patch(_PATCH_PROVIDER, return_value=_mock_provider()),
            patch(_PATCH_SETTINGS, return_value=MagicMock()),
            patch("os.path.getsize", return_value=1_000_000),
        ):
            with pytest.raises(ShortGenerationError) as exc_info:
                generator.generate(
                    youtube_url="https://www.youtube.com/watch?v=abc",
                    hook=hook,
                    session_id="sess-1",
                    short_id="short-1",
                    is_watermarked=True,
                )
        assert "FFmpeg render failed" in str(exc_info.value)
        assert "render failed" in str(exc_info.value)

    def test_unexpected_exception_wrapped_in_short_generation_error(self):
        hook = _make_hook()
        generator = ShortGenerator()

        with patch(_PATCH_EXTRACT, side_effect=RuntimeError("unexpected boom")):
            with pytest.raises(ShortGenerationError) as exc_info:
                generator.generate(
                    youtube_url="https://www.youtube.com/watch?v=abc",
                    hook=hook,
                    session_id="sess-1",
                    short_id="short-1",
                    is_watermarked=True,
                )
        assert "Short generation failed" in str(exc_info.value)


# ─── Test: captions disabled ───

class TestCaptionsDisabled:
    def test_no_ass_generated_when_captions_disabled(self):
        hook = _make_hook()
        generator = ShortGenerator()

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROBE, return_value=28.0),
            patch(_PATCH_GEN_ASS) as mock_ass,
            patch(_PATCH_RENDER, return_value=_ok_ffmpeg()),
            patch(_PATCH_THUMB, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROVIDER, return_value=_mock_provider()),
            patch(_PATCH_SETTINGS, return_value=MagicMock()),
            patch("os.path.getsize", return_value=1_000_000),
        ):
            generator.generate(
                youtube_url="https://www.youtube.com/watch?v=abc",
                hook=hook,
                session_id="sess-1",
                short_id="short-1",
                is_watermarked=True,
                captions_enabled=False,
            )

        mock_ass.assert_not_called()

    def test_empty_subtitle_path_passed_to_render_when_captions_off(self):
        hook = _make_hook()
        generator = ShortGenerator()

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROBE, return_value=28.0),
            patch(_PATCH_GEN_ASS),
            patch(_PATCH_RENDER, return_value=_ok_ffmpeg()) as mock_render,
            patch(_PATCH_THUMB, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROVIDER, return_value=_mock_provider()),
            patch(_PATCH_SETTINGS, return_value=MagicMock()),
            patch("os.path.getsize", return_value=1_000_000),
        ):
            generator.generate(
                youtube_url="https://www.youtube.com/watch?v=abc",
                hook=hook,
                session_id="sess-1",
                short_id="short-1",
                is_watermarked=True,
                captions_enabled=False,
            )

        _, kwargs = mock_render.call_args
        # subtitle_path is "" when captions are disabled (None → "")
        assert kwargs.get("subtitle_path") == ""


# ─── Test: manual clip (hook=None) ───

class TestManualClip:
    def test_manual_clip_uses_start_end_seconds_directly(self):
        generator = ShortGenerator()

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg()) as mock_extract,
            patch(_PATCH_PROBE, return_value=15.0),
            patch(_PATCH_GEN_ASS),
            patch(_PATCH_RENDER, return_value=_ok_ffmpeg()),
            patch(_PATCH_THUMB, return_value=_ok_ffmpeg()),
            patch(_PATCH_SETTINGS, return_value=MagicMock()),
            patch("os.path.getsize", return_value=500_000),
        ):
            generator.generate(
                youtube_url="https://www.youtube.com/watch?v=abc",
                hook=None,
                session_id="sess-1",
                short_id="short-1",
                is_watermarked=True,
                start_seconds=10.0,
                end_seconds=25.0,
                captions_enabled=False,
            )

        mock_extract.assert_called_once()
        args, _ = mock_extract.call_args
        assert args[1] == 10.0  # start_seconds
        assert args[2] == 25.0  # end_seconds

    def test_manual_clip_raises_if_segment_extraction_fails(self):
        generator = ShortGenerator()

        with patch(_PATCH_EXTRACT, return_value=_fail_ffmpeg("download error")):
            with pytest.raises(ShortGenerationError) as exc_info:
                generator.generate(
                    youtube_url="https://www.youtube.com/watch?v=abc",
                    hook=None,
                    session_id="sess-1",
                    short_id="short-1",
                    is_watermarked=True,
                    start_seconds=0.0,
                    end_seconds=30.0,
                    captions_enabled=False,
                )
        assert "Segment extraction failed" in str(exc_info.value)

    def test_manual_clip_title_uses_video_title_fallback(self):
        generator = ShortGenerator()

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROBE, return_value=20.0),
            patch(_PATCH_GEN_ASS),
            patch(_PATCH_RENDER, return_value=_ok_ffmpeg()),
            patch(_PATCH_THUMB, return_value=_ok_ffmpeg()),
            patch(_PATCH_SETTINGS, return_value=MagicMock()),
            patch("os.path.getsize", return_value=500_000),
        ):
            result = generator.generate(
                youtube_url="https://www.youtube.com/watch?v=abc",
                hook=None,
                session_id="sess-1",
                short_id="short-1",
                is_watermarked=True,
                captions_enabled=False,
                video_title="My Awesome Video",
            )

        assert result.title == "My Awesome Video - Clip"


# ─── Test: composite hook ───

class TestCompositeHook:
    def test_composite_hook_concats_multiple_segments(self):
        hook = _make_hook(
            is_composite=True,
            start_time="0:05+1:00",
            end_time="0:35+1:30",
        )
        generator = ShortGenerator()

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg()) as mock_extract,
            patch(_PATCH_CONCAT, return_value=_ok_ffmpeg()) as mock_concat,
            patch("app.services.short_generator.parse_composite_timestamps",
                  return_value=[(5.0, 35.0), (60.0, 90.0)]),
            patch(_PATCH_PROBE, return_value=60.0),
            patch(_PATCH_GEN_ASS),
            patch(_PATCH_RENDER, return_value=_ok_ffmpeg()),
            patch(_PATCH_THUMB, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROVIDER, return_value=_mock_provider()),
            patch(_PATCH_SETTINGS, return_value=MagicMock()),
            patch("os.path.getsize", return_value=2_000_000),
        ):
            generator.generate(
                youtube_url="https://www.youtube.com/watch?v=abc",
                hook=hook,
                session_id="sess-1",
                short_id="short-1",
                is_watermarked=True,
            )

        assert mock_extract.call_count == 2
        mock_concat.assert_called_once()

    def test_composite_hook_raises_if_concat_fails(self):
        hook = _make_hook(
            is_composite=True,
            start_time="0:05+1:00",
            end_time="0:35+1:30",
        )
        generator = ShortGenerator()

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg()),
            patch(_PATCH_CONCAT, return_value=_fail_ffmpeg("concat error")),
            patch("app.services.short_generator.parse_composite_timestamps",
                  return_value=[(5.0, 35.0), (60.0, 90.0)]),
        ):
            with pytest.raises(ShortGenerationError) as exc_info:
                generator.generate(
                    youtube_url="https://www.youtube.com/watch?v=abc",
                    hook=hook,
                    session_id="sess-1",
                    short_id="short-1",
                    is_watermarked=True,
                )
        assert "concatenation failed" in str(exc_info.value)


# ─── Test: LLM caption cleanup fallback ───

class TestLLMFallback:
    def test_caption_cleanup_falls_back_to_raw_text_on_llm_failure(self):
        hook = _make_hook()
        generator = ShortGenerator()

        mock_prov = MagicMock()
        mock_prov.generate.side_effect = Exception("LLM unavailable")

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROBE, return_value=28.0),
            patch(_PATCH_GEN_ASS),
            patch(_PATCH_RENDER, return_value=_ok_ffmpeg()),
            patch(_PATCH_THUMB, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROVIDER, return_value=mock_prov),
            patch(_PATCH_SETTINGS, return_value=MagicMock()),
            patch("os.path.getsize", return_value=1_000_000),
        ):
            result = generator.generate(
                youtube_url="https://www.youtube.com/watch?v=abc",
                hook=hook,
                session_id="sess-1",
                short_id="short-1",
                is_watermarked=True,
                captions_enabled=True,
            )

        # Falls back to raw hook_text
        assert result.cleaned_captions == hook["hook_text"]


# ─── Test: aspect ratio ───

class TestAspectRatio:
    def test_aspect_ratio_forwarded_to_render(self):
        hook = _make_hook()
        generator = ShortGenerator()

        with (
            patch(_PATCH_EXTRACT, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROBE, return_value=28.0),
            patch(_PATCH_GEN_ASS),
            patch(_PATCH_RENDER, return_value=_ok_ffmpeg()) as mock_render,
            patch(_PATCH_THUMB, return_value=_ok_ffmpeg()),
            patch(_PATCH_PROVIDER, return_value=_mock_provider()),
            patch(_PATCH_SETTINGS, return_value=MagicMock()),
            patch("os.path.getsize", return_value=1_000_000),
        ):
            generator.generate(
                youtube_url="https://www.youtube.com/watch?v=abc",
                hook=hook,
                session_id="sess-1",
                short_id="short-1",
                is_watermarked=True,
                aspect_ratio="1:1",
            )

        _, kwargs = mock_render.call_args
        assert kwargs.get("aspect_ratio") == "1:1"
