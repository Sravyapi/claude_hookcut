"""Tests for AssemblyAI diarization service."""
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import asdict

from app.services.assemblyai_diarization import (
    AssemblyAIDiarizer,
    DiarizationResult,
    SpeakerUtterance,
    _ms_to_timestamp,
    LANGUAGE_MAP,
)
from app.exceptions import TranscriptError


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.ASSEMBLYAI_API_KEY = "test-api-key"
    settings.YTDLP_PROXY = ""
    return settings


@pytest.fixture
def sample_assemblyai_response():
    return {
        "status": "completed",
        "utterances": [
            {"speaker": "A", "start": 5000, "end": 12000, "text": "Hello, welcome to the show."},
            {"speaker": "B", "start": 12500, "end": 20000, "text": "Thanks for having me."},
            {"speaker": "A", "start": 20500, "end": 30000, "text": "So tell us about your project."},
            {"speaker": "B", "start": 30500, "end": 45000, "text": "Well, it started two years ago."},
        ],
    }


class TestMsToTimestamp:
    def test_zero(self):
        assert _ms_to_timestamp(0) == "0:00"

    def test_seconds(self):
        assert _ms_to_timestamp(5000) == "0:05"

    def test_minutes(self):
        assert _ms_to_timestamp(65000) == "1:05"

    def test_large(self):
        assert _ms_to_timestamp(3661000) == "61:01"


class TestLanguageMap:
    def test_english(self):
        assert LANGUAGE_MAP["English"] == "en"

    def test_hindi(self):
        assert LANGUAGE_MAP["Hindi"] == "hi"

    def test_telugu(self):
        assert LANGUAGE_MAP["Telugu"] == "te"


class TestAssemblyAIDiarizer:

    @patch("app.services.assemblyai_diarization.get_settings")
    def test_init_raises_without_api_key(self, mock_get_settings):
        settings = MagicMock()
        settings.ASSEMBLYAI_API_KEY = ""
        mock_get_settings.return_value = settings
        with pytest.raises(TranscriptError, match="ASSEMBLYAI_API_KEY"):
            AssemblyAIDiarizer()

    @patch("app.services.assemblyai_diarization.get_settings")
    def test_init_succeeds_with_api_key(self, mock_get_settings, mock_settings):
        mock_get_settings.return_value = mock_settings
        diarizer = AssemblyAIDiarizer()
        assert diarizer.api_key == "test-api-key"

    @patch("app.services.assemblyai_diarization.get_settings")
    def test_parse_result(self, mock_get_settings, mock_settings, sample_assemblyai_response):
        mock_get_settings.return_value = mock_settings
        diarizer = AssemblyAIDiarizer()
        result = diarizer._parse_result(sample_assemblyai_response)

        assert isinstance(result, DiarizationResult)
        assert result.detected_speaker_count == 2
        assert len(result.utterances) == 4
        assert result.utterances[0].speaker == "Speaker A"
        assert result.utterances[1].speaker == "Speaker B"
        assert "[Speaker A] [0:05]" in result.transcript_text
        assert "[Speaker B] [0:12]" in result.transcript_text

    @patch("app.services.assemblyai_diarization.get_settings")
    def test_parse_result_empty_utterances(self, mock_get_settings, mock_settings):
        mock_get_settings.return_value = mock_settings
        diarizer = AssemblyAIDiarizer()
        with pytest.raises(TranscriptError, match="no speaker utterances"):
            diarizer._parse_result({"utterances": []})

    @patch("app.services.assemblyai_diarization.get_settings")
    def test_parse_result_three_speakers(self, mock_get_settings, mock_settings):
        mock_get_settings.return_value = mock_settings
        diarizer = AssemblyAIDiarizer()
        data = {
            "utterances": [
                {"speaker": "A", "start": 0, "end": 5000, "text": "Hello"},
                {"speaker": "B", "start": 5000, "end": 10000, "text": "Hi"},
                {"speaker": "C", "start": 10000, "end": 15000, "text": "Hey"},
            ]
        }
        result = diarizer._parse_result(data)
        assert result.detected_speaker_count == 3
        assert result.utterances[2].speaker == "Speaker C"

    @patch("app.services.assemblyai_diarization.get_settings")
    @patch("subprocess.run")
    def test_download_audio_failure(self, mock_run, mock_get_settings, mock_settings):
        mock_get_settings.return_value = mock_settings
        mock_run.return_value = MagicMock(returncode=1, stderr="download error")
        diarizer = AssemblyAIDiarizer()
        with pytest.raises(TranscriptError, match="Audio download failed"):
            diarizer._download_audio("test_video_id")

    @patch("app.services.assemblyai_diarization.get_settings")
    @patch("subprocess.run")
    def test_download_audio_timeout(self, mock_run, mock_get_settings, mock_settings):
        import subprocess
        mock_get_settings.return_value = mock_settings
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="yt-dlp", timeout=120)
        diarizer = AssemblyAIDiarizer()
        with pytest.raises(TranscriptError, match="timed out"):
            diarizer._download_audio("test_video_id")

    @patch("app.services.assemblyai_diarization.get_settings")
    @patch("app.services.assemblyai_diarization.httpx")
    def test_upload_audio(self, mock_httpx, mock_get_settings, mock_settings, tmp_path):
        mock_get_settings.return_value = mock_settings
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio data")

        mock_response = MagicMock()
        mock_response.json.return_value = {"upload_url": "https://cdn.assemblyai.com/upload/123"}
        mock_response.raise_for_status = MagicMock()
        mock_httpx.post.return_value = mock_response

        diarizer = AssemblyAIDiarizer()
        url = diarizer._upload_audio(str(audio_file))
        assert url == "https://cdn.assemblyai.com/upload/123"

    @patch("app.services.assemblyai_diarization.get_settings")
    @patch("app.services.assemblyai_diarization.httpx")
    def test_create_transcript(self, mock_httpx, mock_get_settings, mock_settings):
        mock_get_settings.return_value = mock_settings
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "transcript-123"}
        mock_response.raise_for_status = MagicMock()
        mock_httpx.post.return_value = mock_response

        diarizer = AssemblyAIDiarizer()
        tid = diarizer._create_transcript("https://cdn.assemblyai.com/upload/123", "English", 2)
        assert tid == "transcript-123"

        # Verify request body
        call_args = mock_httpx.post.call_args
        body = call_args.kwargs.get("json", {})
        assert body["speaker_labels"] is True
        assert body["speakers_expected"] == 2
        assert body["language_code"] == "en"

    @patch("app.services.assemblyai_diarization.get_settings")
    @patch("app.services.assemblyai_diarization.time.sleep")
    @patch("app.services.assemblyai_diarization.httpx")
    def test_poll_transcript_error(self, mock_httpx, mock_sleep, mock_get_settings, mock_settings):
        mock_get_settings.return_value = mock_settings
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "error", "error": "bad audio"}
        mock_response.raise_for_status = MagicMock()
        mock_httpx.get.return_value = mock_response

        diarizer = AssemblyAIDiarizer()
        with pytest.raises(TranscriptError, match="bad audio"):
            diarizer._poll_transcript("transcript-123")

    @patch("app.services.assemblyai_diarization.get_settings")
    @patch("app.services.assemblyai_diarization.time.sleep")
    @patch("app.services.assemblyai_diarization.time.monotonic")
    @patch("app.services.assemblyai_diarization.httpx")
    def test_poll_transcript_timeout(self, mock_httpx, mock_monotonic, mock_sleep, mock_get_settings, mock_settings):
        mock_get_settings.return_value = mock_settings
        # Simulate time passing beyond timeout
        mock_monotonic.side_effect = [0, 0, 301]
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "queued"}
        mock_response.raise_for_status = MagicMock()
        mock_httpx.get.return_value = mock_response

        diarizer = AssemblyAIDiarizer()
        with pytest.raises(TranscriptError, match="timed out"):
            diarizer._poll_transcript("transcript-123")


class TestSpeakerUtterance:
    def test_asdict(self):
        u = SpeakerUtterance(speaker="Speaker A", start_ms=5000, end_ms=12000, text="Hello")
        d = asdict(u)
        assert d["speaker"] == "Speaker A"
        assert d["start_ms"] == 5000
        assert d["end_ms"] == 12000
        assert d["text"] == "Hello"
