"""Tests for interview mode FFmpeg rendering."""
import pytest
from unittest.mock import patch, MagicMock

from app.utils.ffmpeg_commands import (
    _build_active_speaker_expr,
    render_interview_short,
)
from app.utils.face_mapping import FaceRegion


class TestBuildActiveSpeakerExpr:
    def test_empty_utterances(self):
        assert _build_active_speaker_expr([], "Speaker A") == "0"

    def test_no_matching_speaker(self):
        utterances = [
            {"speaker": "Speaker B", "start_ms": 1000, "end_ms": 5000},
        ]
        assert _build_active_speaker_expr(utterances, "Speaker A") == "0"

    def test_single_segment(self):
        utterances = [
            {"speaker": "Speaker A", "start_ms": 5000, "end_ms": 12000},
        ]
        result = _build_active_speaker_expr(utterances, "Speaker A")
        assert result == "between(t,5.00,12.00)"

    def test_multiple_segments(self):
        utterances = [
            {"speaker": "Speaker A", "start_ms": 5000, "end_ms": 12000},
            {"speaker": "Speaker B", "start_ms": 12500, "end_ms": 20000},
            {"speaker": "Speaker A", "start_ms": 20500, "end_ms": 30000},
        ]
        result = _build_active_speaker_expr(utterances, "Speaker A")
        assert "between(t,5.00,12.00)" in result
        assert "between(t,20.50,30.00)" in result
        assert "+" in result  # OR operator
        # Speaker B segments should NOT appear
        assert "12.50" not in result

    def test_filters_correct_speaker(self):
        utterances = [
            {"speaker": "Speaker A", "start_ms": 0, "end_ms": 5000},
            {"speaker": "Speaker B", "start_ms": 5000, "end_ms": 10000},
            {"speaker": "Speaker C", "start_ms": 10000, "end_ms": 15000},
        ]
        result = _build_active_speaker_expr(utterances, "Speaker B")
        assert result == "between(t,5.00,10.00)"


class TestRenderInterviewShort:
    @patch("app.utils.ffmpeg_commands._probe_video_stream")
    @patch("app.utils.ffmpeg_commands.render_short")
    def test_fallback_when_no_video_stream(self, mock_render, mock_probe):
        """Falls back to normal render when input has no video stream."""
        mock_probe.return_value = None
        mock_render.return_value = MagicMock(success=True)

        faces = [
            FaceRegion("Speaker A", 200, 100, 150, 150),
            FaceRegion("Speaker B", 1400, 100, 150, 150),
        ]
        result = render_interview_short(
            "/fake/input.mp4", "/fake/subs.ass", "/fake/output.mp4",
            faces, [], watermark=False,
        )
        mock_render.assert_called_once()

    @patch("app.utils.ffmpeg_commands._run_ffmpeg_render")
    @patch("app.utils.ffmpeg_commands._probe_video_stream")
    def test_2speaker_filter_graph(self, mock_probe, mock_run):
        """2-speaker layout produces correct FFmpeg filter."""
        mock_probe.return_value = {"width": 1920, "height": 1080, "codec_name": "h264"}
        mock_run.return_value = MagicMock(success=True)

        faces = [
            FaceRegion("Speaker A", 200, 100, 150, 150),
            FaceRegion("Speaker B", 1400, 100, 150, 150),
        ]
        utterances = [
            {"speaker": "Speaker A", "start_ms": 0, "end_ms": 5000},
            {"speaker": "Speaker B", "start_ms": 5000, "end_ms": 10000},
        ]

        result = render_interview_short(
            "/fake/input.mp4", "", "/fake/output.mp4",
            faces, utterances, watermark=False,
        )
        assert result.success

        # Check the FFmpeg command was called with a filter containing split and vstack
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        vf_idx = cmd.index("-vf")
        vf = cmd[vf_idx + 1]
        assert "split=2" in vf
        assert "vstack" in vf
        assert "drawbox" in vf

    @patch("app.utils.ffmpeg_commands._run_ffmpeg_render")
    @patch("app.utils.ffmpeg_commands._probe_video_stream")
    @patch("app.utils.ffmpeg_commands.render_short")
    def test_fallback_after_all_attempts(self, mock_render, mock_probe, mock_run):
        """Falls back to normal render after all split-screen attempts fail."""
        mock_probe.return_value = {"width": 1920, "height": 1080, "codec_name": "h264"}
        # All 3 attempts fail
        mock_run.return_value = MagicMock(success=False, error="filter error")
        mock_render.return_value = MagicMock(success=True)

        faces = [
            FaceRegion("Speaker A", 200, 100, 150, 150),
            FaceRegion("Speaker B", 1400, 100, 150, 150),
        ]
        render_interview_short(
            "/fake/input.mp4", "", "/fake/output.mp4",
            faces, [], watermark=False,
        )
        # Should have fallen back to normal render
        mock_render.assert_called_once()

    @patch("app.utils.ffmpeg_commands._run_ffmpeg_render")
    @patch("app.utils.ffmpeg_commands._probe_video_stream")
    def test_3plus_speaker_filter(self, mock_probe, mock_run):
        """3+ speaker layout uses wide shot on bottom."""
        mock_probe.return_value = {"width": 1920, "height": 1080, "codec_name": "h264"}
        mock_run.return_value = MagicMock(success=True)

        faces = [
            FaceRegion("Speaker A", 200, 100, 150, 150),
            FaceRegion("Speaker B", 900, 100, 150, 150),
            FaceRegion("Speaker C", 1400, 100, 150, 150),
        ]
        result = render_interview_short(
            "/fake/input.mp4", "", "/fake/output.mp4",
            faces, [], watermark=False,
        )
        assert result.success
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        vf_idx = cmd.index("-vf")
        vf = cmd[vf_idx + 1]
        assert "force_original_aspect_ratio=decrease" in vf

    @patch("app.utils.ffmpeg_commands._run_ffmpeg_render")
    @patch("app.utils.ffmpeg_commands._probe_video_stream")
    def test_audio_normalization_disabled(self, mock_probe, mock_run):
        """When audio_normalization=False, loudnorm is not in command."""
        mock_probe.return_value = {"width": 1920, "height": 1080, "codec_name": "h264"}
        mock_run.return_value = MagicMock(success=True)

        faces = [
            FaceRegion("Speaker A", 200, 100, 150, 150),
            FaceRegion("Speaker B", 1400, 100, 150, 150),
        ]
        render_interview_short(
            "/fake/input.mp4", "", "/fake/output.mp4",
            faces, [], audio_normalization=False,
        )
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        af_idx = cmd.index("-af")
        af = cmd[af_idx + 1]
        assert "loudnorm" not in af
