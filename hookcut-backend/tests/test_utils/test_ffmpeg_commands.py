"""Tests for _extract_error_from_stderr and _build_render_cmd in ffmpeg_commands.py."""
import os
# Set env vars BEFORE any app imports (same as tests/conftest.py)
os.environ.setdefault("FEATURE_V0_MODE", "false")
os.environ.setdefault("NEXTAUTH_SECRET", "test-secret-for-jwt-signing-min-32chars!")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("TESTING", "true")

import pytest
from unittest.mock import patch

from app.utils.ffmpeg_commands import _extract_error_from_stderr, _build_render_cmd


class TestExtractErrorFromStderr:
    """Verify _extract_error_from_stderr captures real errors, not progress lines."""

    def test_skips_progress_lines_returns_real_error(self):
        stderr = (
            "Stream mapping:\n"
            "  Stream #0:0 -> #0:0 (h264 (native) -> h264 (libx264))\n"
            "[crop @ 0x600000c04000] Invalid too big or non positive size for width '0'\n"
            "Error initializing complex filters.\n"
            "frame=    0 fps=0.0 q=0.0 size=       0KiB time=N/A bitrate=N/A speed=N/A\n"
            "frame=    0 fps=0.0 q=0.0 size=       0KiB time=N/A bitrate=N/A speed=N/A\n"
        )
        result = _extract_error_from_stderr(stderr)
        # Should contain the real error, not the progress lines
        assert "Invalid too big or non positive size" in result
        assert "Error initializing complex filters" in result
        # Should NOT contain progress lines
        assert "frame=" not in result

    def test_skips_encoder_params_in_pass2(self):
        stderr = (
            "keyint=250 weightb=1 scenecut=40\n"
            "Some other diagnostic line\n"
            "mbtree=1 another_param=2\n"
            "Conversion failed!\n"
        )
        result = _extract_error_from_stderr(stderr)
        assert "Conversion failed!" in result
        assert "keyint" not in result

    def test_only_progress_lines_returns_fallback(self):
        stderr = (
            "frame=    0 fps=0.0 q=0.0 size=       0KiB time=N/A bitrate=N/A speed=N/A\n"
            "frame=    0 fps=0.0 q=0.0 size=       0KiB time=N/A bitrate=N/A speed=N/A\n"
        )
        result = _extract_error_from_stderr(stderr)
        # With only progress lines, pass 1 finds nothing, pass 2 skips them,
        # so we get the raw fallback (last 500 chars)
        assert len(result) > 0

    def test_real_error_among_noise(self):
        stderr = (
            "Input #0, mov,mp4,m4a,3gp,3g2,mj2, from '/tmp/segment.mp4':\n"
            "  Duration: 00:00:30.00, start: 0.000000\n"
            "  Stream #0:0: Video: h264 (avc1), yuv420p, 1280x720, 30 fps\n"
            "[Parsed_crop_0 @ 0x7f] Failed to configure output pad on filter\n"
            "Error reinitializing filters!\n"
            "frame=    0 fps=0.0 q=0.0 size=       0KiB time=N/A bitrate=N/A speed=N/A\n"
        )
        result = _extract_error_from_stderr(stderr)
        assert "Failed to configure" in result or "Error reinitializing" in result
        assert "frame=" not in result

    def test_empty_stderr(self):
        result = _extract_error_from_stderr("")
        assert result == ""

    def test_multiple_error_lines_returns_last_5(self):
        errors = "\n".join(f"Error line {i}" for i in range(10))
        result = _extract_error_from_stderr(errors)
        # Should contain the last 5 error lines
        assert "Error line 9" in result
        assert "Error line 5" in result
        assert "Error line 4" not in result


class TestBuildRenderCmd:
    """Verify crop filter in _build_render_cmd has dimension safety guard."""

    def test_crop_filter_has_max_guard(self):
        cmd = _build_render_cmd("/tmp/input.mp4", "/tmp/output.mp4")
        vf_arg = cmd[cmd.index("-vf") + 1]
        # The crop expression should have a max(..., 2) guard
        assert "max(min(" in vf_arg
        assert ",2)" in vf_arg

    def test_command_includes_required_flags(self):
        cmd = _build_render_cmd("/tmp/input.mp4", "/tmp/output.mp4")
        assert "-i" in cmd
        assert "/tmp/input.mp4" in cmd
        assert "/tmp/output.mp4" in cmd
        assert "-movflags" in cmd
