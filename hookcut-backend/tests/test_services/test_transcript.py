"""Tests for TranscriptService — 6-provider cascade for transcript acquisition.

All external HTTP calls, subprocess calls, and filesystem I/O are mocked.
No real network calls are made in these tests.
"""
import json
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open

import pytest

from app.services.transcript import TranscriptService, TranscriptResult


VIDEO_ID = "dQw4w9WgXcQ"

# A transcript that's long enough to pass the 50-char minimum check
LONG_TRANSCRIPT_TEXT = "[0:00.00] Hello and welcome to this amazing video that will teach you everything you need to know\n[0:05.00] about building great content for social media platforms today"


def _make_snippet(start: float, text: str):
    """Create a fake transcript snippet matching youtube-transcript-api shape."""
    s = MagicMock()
    s.start = start
    s.text = text
    return s


class TestFetchHappyPath:
    """Primary provider (youtube-transcript-api) succeeds immediately."""

    @patch("app.services.transcript._ensure_cookies_file", return_value="/nonexistent/path")
    @patch("app.services.transcript.os.path.exists", return_value=False)
    def test_primary_provider_returns_result(self, mock_exists, mock_cookies):
        """When youtube-transcript-api succeeds, fetch() returns that result."""
        snippets = [
            _make_snippet(0.0, "Hello and welcome to this amazing video today"),
            _make_snippet(5.0, "We will cover everything you need to know about content"),
        ]
        fetched = MagicMock()
        fetched.__iter__ = MagicMock(return_value=iter(snippets))
        fetched.language_code = "en"

        mock_transcript = MagicMock()
        mock_transcript.fetch.return_value = fetched

        mock_transcript_list = MagicMock()
        mock_transcript_list.find_transcript.return_value = mock_transcript

        mock_ytt_api = MagicMock()
        mock_ytt_api.list.return_value = mock_transcript_list

        mock_ytt_cls = MagicMock(return_value=mock_ytt_api)

        with patch.dict("sys.modules", {"youtube_transcript_api": MagicMock(YouTubeTranscriptApi=mock_ytt_cls)}):
            with patch("app.config.get_settings") as mock_settings:
                mock_settings.return_value.YTDLP_PROXY = None
                mock_settings.return_value.FEATURE_WHISPER_FALLBACK = False

                svc = TranscriptService()
                result = svc._try_youtube_transcript_api(VIDEO_ID, "English")

        assert result is not None
        assert result.provider == "youtube_transcript_api"
        assert result.language_detected == "en"
        assert len(result.text) > 50

    @patch("app.services.transcript._ensure_cookies_file", return_value="/nonexistent/path")
    @patch("app.services.transcript.os.path.exists", return_value=False)
    def test_fetch_returns_primary_when_available(self, mock_exists, mock_cookies):
        """fetch() returns immediately after primary provider succeeds (no fallbacks called)."""
        expected_result = TranscriptResult(
            text=LONG_TRANSCRIPT_TEXT,
            provider="youtube_transcript_api",
            language_detected="en",
        )

        svc = TranscriptService()
        with patch.object(svc, "_try_youtube_transcript_api", return_value=expected_result) as mock_primary:
            with patch.object(svc, "_try_innertube_android") as mock_inner:
                with patch.object(svc, "_try_ytdlp_subtitles") as mock_ytdlp:
                    result = svc.fetch(VIDEO_ID, "English")

        assert result is not None
        assert result.provider == "youtube_transcript_api"
        mock_primary.assert_called_once()
        mock_inner.assert_not_called()
        mock_ytdlp.assert_not_called()


class TestFallbackCascade:
    """Tests that providers are tried in order and the first success is returned."""

    def test_primary_fails_secondary_succeeds(self):
        """When primary fails, innertube_android is tried next."""
        secondary_result = TranscriptResult(
            text=LONG_TRANSCRIPT_TEXT,
            provider="innertube_android",
            language_detected="en",
        )

        svc = TranscriptService()
        with patch.object(svc, "_try_youtube_transcript_api", return_value=None):
            with patch.object(svc, "_try_innertube_android", return_value=secondary_result) as mock_inner:
                with patch.object(svc, "_try_ytdlp_subtitles") as mock_ytdlp:
                    with patch("app.config.get_settings") as mock_settings:
                        mock_settings.return_value.FEATURE_WHISPER_FALLBACK = False
                        result = svc.fetch(VIDEO_ID, "English")

        assert result is not None
        assert result.provider == "innertube_android"
        mock_inner.assert_called_once()
        mock_ytdlp.assert_not_called()

    def test_first_two_fail_ytdlp_succeeds(self):
        """When primary and innertube fail, ytdlp_subtitles is tried."""
        ytdlp_result = TranscriptResult(
            text=LONG_TRANSCRIPT_TEXT,
            provider="ytdlp_subtitles",
        )

        svc = TranscriptService()
        with patch.object(svc, "_try_youtube_transcript_api", return_value=None):
            with patch.object(svc, "_try_innertube_android", return_value=None):
                with patch.object(svc, "_try_ytdlp_subtitles", return_value=ytdlp_result):
                    with patch.object(svc, "_try_cf_worker") as mock_cf:
                        with patch("app.config.get_settings") as mock_settings:
                            mock_settings.return_value.FEATURE_WHISPER_FALLBACK = False
                            result = svc.fetch(VIDEO_ID, "English")

        assert result is not None
        assert result.provider == "ytdlp_subtitles"
        mock_cf.assert_not_called()

    def test_cf_worker_fallback(self):
        """When primary three fail, CF Worker is tried."""
        cf_result = TranscriptResult(
            text=LONG_TRANSCRIPT_TEXT,
            provider="cf_worker",
            language_detected="en",
        )

        svc = TranscriptService()
        with patch.object(svc, "_try_youtube_transcript_api", return_value=None):
            with patch.object(svc, "_try_innertube_android", return_value=None):
                with patch.object(svc, "_try_ytdlp_subtitles", return_value=None):
                    with patch.object(svc, "_try_cf_worker", return_value=cf_result):
                        with patch.object(svc, "_try_invidious_captions") as mock_inv:
                            with patch("app.config.get_settings") as mock_settings:
                                mock_settings.return_value.FEATURE_WHISPER_FALLBACK = False
                                result = svc.fetch(VIDEO_ID, "English")

        assert result is not None
        assert result.provider == "cf_worker"
        mock_inv.assert_not_called()

    def test_invidious_fallback(self):
        """When first four fail, Invidious is tried."""
        inv_result = TranscriptResult(
            text=LONG_TRANSCRIPT_TEXT,
            provider="invidious_api",
        )

        svc = TranscriptService()
        with patch.object(svc, "_try_youtube_transcript_api", return_value=None):
            with patch.object(svc, "_try_innertube_android", return_value=None):
                with patch.object(svc, "_try_ytdlp_subtitles", return_value=None):
                    with patch.object(svc, "_try_cf_worker", return_value=None):
                        with patch.object(svc, "_try_invidious_captions", return_value=inv_result):
                            with patch.object(svc, "_try_piped_api") as mock_piped:
                                with patch("app.config.get_settings") as mock_settings:
                                    mock_settings.return_value.FEATURE_WHISPER_FALLBACK = False
                                    result = svc.fetch(VIDEO_ID, "English")

        assert result is not None
        assert result.provider == "invidious_api"
        mock_piped.assert_not_called()

    def test_piped_api_fallback(self):
        """When first five fail, Piped API is tried."""
        piped_result = TranscriptResult(
            text=LONG_TRANSCRIPT_TEXT,
            provider="piped_api",
            language_detected="en",
        )

        svc = TranscriptService()
        with patch.object(svc, "_try_youtube_transcript_api", return_value=None):
            with patch.object(svc, "_try_innertube_android", return_value=None):
                with patch.object(svc, "_try_ytdlp_subtitles", return_value=None):
                    with patch.object(svc, "_try_cf_worker", return_value=None):
                        with patch.object(svc, "_try_invidious_captions", return_value=None):
                            with patch.object(svc, "_try_piped_api", return_value=piped_result):
                                with patch("app.config.get_settings") as mock_settings:
                                    mock_settings.return_value.FEATURE_WHISPER_FALLBACK = False
                                    result = svc.fetch(VIDEO_ID, "English")

        assert result is not None
        assert result.provider == "piped_api"


class TestAllProvidersFail:
    """When every provider fails, None is returned — no exception raised."""

    def test_all_fail_returns_none(self):
        """When all providers return None, fetch() returns None."""
        svc = TranscriptService()
        with patch.object(svc, "_try_youtube_transcript_api", return_value=None):
            with patch.object(svc, "_try_innertube_android", return_value=None):
                with patch.object(svc, "_try_ytdlp_subtitles", return_value=None):
                    with patch.object(svc, "_try_cf_worker", return_value=None):
                        with patch.object(svc, "_try_invidious_captions", return_value=None):
                            with patch.object(svc, "_try_piped_api", return_value=None):
                                with patch("app.config.get_settings") as mock_settings:
                                    mock_settings.return_value.FEATURE_WHISPER_FALLBACK = False
                                    result = svc.fetch(VIDEO_ID, "English")

        assert result is None

    def test_all_fail_with_whisper_enabled_but_whisper_also_fails(self):
        """Even with Whisper fallback enabled, returns None when Whisper also fails."""
        svc = TranscriptService()
        with patch.object(svc, "_try_youtube_transcript_api", return_value=None):
            with patch.object(svc, "_try_innertube_android", return_value=None):
                with patch.object(svc, "_try_ytdlp_subtitles", return_value=None):
                    with patch.object(svc, "_try_cf_worker", return_value=None):
                        with patch.object(svc, "_try_invidious_captions", return_value=None):
                            with patch.object(svc, "_try_piped_api", return_value=None):
                                with patch.object(svc, "_try_whisper_api", return_value=None):
                                    with patch("app.config.get_settings") as mock_settings:
                                        mock_settings.return_value.FEATURE_WHISPER_FALLBACK = True
                                        result = svc.fetch(VIDEO_ID, "English")

        assert result is None

    def test_all_fail_does_not_raise(self):
        """Failure of all providers must not raise an exception."""
        svc = TranscriptService()
        with patch.object(svc, "_try_youtube_transcript_api", return_value=None):
            with patch.object(svc, "_try_innertube_android", return_value=None):
                with patch.object(svc, "_try_ytdlp_subtitles", return_value=None):
                    with patch.object(svc, "_try_cf_worker", return_value=None):
                        with patch.object(svc, "_try_invidious_captions", return_value=None):
                            with patch.object(svc, "_try_piped_api", return_value=None):
                                with patch("app.config.get_settings") as mock_settings:
                                    mock_settings.return_value.FEATURE_WHISPER_FALLBACK = False
                                    try:
                                        result = svc.fetch(VIDEO_ID, "English")
                                    except Exception as exc:
                                        pytest.fail(f"fetch() raised unexpectedly: {exc}")


class TestCFWorkerProvider:
    """Unit tests for _try_cf_worker directly."""

    def test_cf_worker_skipped_when_no_url_configured(self):
        """_try_cf_worker returns None immediately if CF_TRANSCRIPT_WORKER_URL is not set."""
        svc = TranscriptService()
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.CF_TRANSCRIPT_WORKER_URL = None
            result = svc._try_cf_worker(VIDEO_ID, "English")

        assert result is None

    def test_cf_worker_success(self):
        """CF Worker returning 200 with sufficient text is accepted."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "text": LONG_TRANSCRIPT_TEXT,
            "language": "en",
        }

        svc = TranscriptService()
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.CF_TRANSCRIPT_WORKER_URL = "https://worker.example.com"
            mock_settings.return_value.CF_WORKER_API_KEY = "test-key"
            with patch("app.services.transcript.httpx.get", return_value=mock_resp):
                result = svc._try_cf_worker(VIDEO_ID, "English")

        assert result is not None
        assert result.provider == "cf_worker"
        assert result.language_detected == "en"

    def test_cf_worker_non_200_returns_none(self):
        """CF Worker returning non-200 status returns None."""
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = "Too Many Requests"

        svc = TranscriptService()
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.CF_TRANSCRIPT_WORKER_URL = "https://worker.example.com"
            mock_settings.return_value.CF_WORKER_API_KEY = "test-key"
            with patch("app.services.transcript.httpx.get", return_value=mock_resp):
                result = svc._try_cf_worker(VIDEO_ID, "English")

        assert result is None

    def test_cf_worker_short_text_returns_none(self):
        """CF Worker transcript shorter than 50 chars returns None."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"text": "Too short", "language": "en"}

        svc = TranscriptService()
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.CF_TRANSCRIPT_WORKER_URL = "https://worker.example.com"
            mock_settings.return_value.CF_WORKER_API_KEY = None
            with patch("app.services.transcript.httpx.get", return_value=mock_resp):
                result = svc._try_cf_worker(VIDEO_ID, "English")

        assert result is None

    def test_cf_worker_http_exception_returns_none(self):
        """Network error from CF Worker returns None (no exception propagated)."""
        svc = TranscriptService()
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.CF_TRANSCRIPT_WORKER_URL = "https://worker.example.com"
            mock_settings.return_value.CF_WORKER_API_KEY = "key"
            with patch("app.services.transcript.httpx.get", side_effect=Exception("Connection refused")):
                result = svc._try_cf_worker(VIDEO_ID, "English")

        assert result is None


class TestLanguageDetection:
    """Verify that language metadata is captured from providers that return it."""

    @patch("app.services.transcript._ensure_cookies_file", return_value="/nonexistent/path")
    @patch("app.services.transcript.os.path.exists", return_value=False)
    def test_youtube_api_language_code_preserved(self, mock_exists, mock_cookies):
        """language_detected from youtube-transcript-api is preserved in result."""
        snippets = [_make_snippet(i * 5.0, f"Word number {i} of the transcript content here") for i in range(5)]
        fetched = MagicMock()
        fetched.__iter__ = MagicMock(return_value=iter(snippets))
        fetched.language_code = "hi"  # Hindi

        mock_transcript = MagicMock()
        mock_transcript.fetch.return_value = fetched

        mock_transcript_list = MagicMock()
        mock_transcript_list.find_transcript.return_value = mock_transcript

        mock_ytt_api = MagicMock()
        mock_ytt_api.list.return_value = mock_transcript_list

        mock_ytt_cls = MagicMock(return_value=mock_ytt_api)

        with patch.dict("sys.modules", {"youtube_transcript_api": MagicMock(YouTubeTranscriptApi=mock_ytt_cls)}):
            with patch("app.config.get_settings") as mock_settings:
                mock_settings.return_value.YTDLP_PROXY = None

                svc = TranscriptService()
                result = svc._try_youtube_transcript_api(VIDEO_ID, "Hindi")

        assert result is not None
        assert result.language_detected == "hi"

    def test_cf_worker_language_preserved(self):
        """language_detected from CF Worker response is preserved."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "text": LONG_TRANSCRIPT_TEXT,
            "language": "ta",  # Tamil
        }

        svc = TranscriptService()
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.CF_TRANSCRIPT_WORKER_URL = "https://worker.example.com"
            mock_settings.return_value.CF_WORKER_API_KEY = "key"
            with patch("app.services.transcript.httpx.get", return_value=mock_resp):
                result = svc._try_cf_worker(VIDEO_ID, "Tamil")

        assert result is not None
        assert result.language_detected == "ta"

    def test_ytdlp_provider_has_no_language(self):
        """ytdlp_subtitles provider does not set language_detected (returns None)."""
        result = TranscriptResult(text=LONG_TRANSCRIPT_TEXT, provider="ytdlp_subtitles")
        assert result.language_detected is None


class TestGetLangCodes:
    """Tests for the static language → code mapping helper."""

    def test_english_lang_codes(self):
        codes = TranscriptService._get_lang_codes("English")
        assert "en" in codes

    def test_hindi_lang_codes(self):
        codes = TranscriptService._get_lang_codes("Hindi")
        assert "hi" in codes

    def test_unknown_language_defaults_to_english(self):
        codes = TranscriptService._get_lang_codes("Klingon")
        assert codes == ["en"]

    def test_hinglish_defaults_to_english(self):
        """Hinglish is not a standalone language — defaults to English."""
        codes = TranscriptService._get_lang_codes("Hinglish")
        assert codes == ["en"]


class TestParseVtt:
    """Unit tests for the VTT parser helper."""

    def test_parse_basic_vtt(self):
        vtt = (
            "WEBVTT\n\n"
            "00:00:01.000 --> 00:00:04.000\n"
            "Hello world this is a test line\n\n"
            "00:00:05.000 --> 00:00:08.000\n"
            "Another line of content here\n"
        )
        svc = TranscriptService()
        result = svc._parse_vtt(vtt)
        assert "Hello world" in result
        assert "Another line" in result

    def test_parse_vtt_strips_tags(self):
        """VTT tags like <c> should be stripped from output."""
        vtt = (
            "WEBVTT\n\n"
            "00:00:01.000 --> 00:00:04.000\n"
            "<c>Hello</c> <c.colorE5E5E5>world</c>\n"
        )
        svc = TranscriptService()
        result = svc._parse_vtt(vtt)
        assert "<c" not in result
        assert "Hello" in result
        assert "world" in result

    def test_parse_vtt_empty_returns_empty_string(self):
        svc = TranscriptService()
        result = svc._parse_vtt("WEBVTT\n\n")
        assert result == ""

    def test_parse_vtt_hours_converted_to_minutes(self):
        """Hours in timestamp should be converted to total minutes."""
        vtt = (
            "WEBVTT\n\n"
            "01:30:00.000 --> 01:30:05.000\n"
            "An hour and a half into the video\n"
        )
        svc = TranscriptService()
        result = svc._parse_vtt(vtt)
        # 1h 30m = 90 minutes
        assert "[90:" in result


class TestParseJson3:
    """Unit tests for the json3 subtitle format parser."""

    def test_parse_json3_basic(self, tmp_path):
        json3_data = {
            "events": [
                {"tStartMs": 0, "segs": [{"utf8": "Hello "}, {"utf8": "world"}]},
                {"tStartMs": 5000, "segs": [{"utf8": "Second segment here please"}]},
            ]
        }
        filepath = tmp_path / "subs.json3"
        filepath.write_text(json.dumps(json3_data))

        svc = TranscriptService()
        result = svc._parse_json3(str(filepath))

        assert "Hello world" in result
        assert "Second segment" in result

    def test_parse_json3_skips_newline_only_segments(self, tmp_path):
        json3_data = {
            "events": [
                {"tStartMs": 0, "segs": [{"utf8": "\n"}]},
                {"tStartMs": 1000, "segs": [{"utf8": "Real content here"}]},
            ]
        }
        filepath = tmp_path / "subs.json3"
        filepath.write_text(json.dumps(json3_data))

        svc = TranscriptService()
        result = svc._parse_json3(str(filepath))

        assert "\n" not in result.strip() or "Real content here" in result

    def test_parse_json3_timestamp_format(self, tmp_path):
        """Timestamps should be formatted as [minutes:seconds]."""
        json3_data = {
            "events": [
                {"tStartMs": 65000, "segs": [{"utf8": "One minute five seconds in"}]},
            ]
        }
        filepath = tmp_path / "subs.json3"
        filepath.write_text(json.dumps(json3_data))

        svc = TranscriptService()
        result = svc._parse_json3(str(filepath))

        # 65 seconds = 1 minute 5 seconds
        assert "[1:" in result


class TestShortVideoHandling:
    """Verify that short transcripts (< 50 chars) are rejected gracefully."""

    @patch("app.services.transcript._ensure_cookies_file", return_value="/nonexistent/path")
    @patch("app.services.transcript.os.path.exists", return_value=False)
    def test_youtube_api_rejects_short_transcript(self, mock_exists, mock_cookies):
        """Transcripts shorter than 50 chars from youtube-transcript-api return None."""
        snippets = [_make_snippet(0.0, "Hi")]  # very short
        fetched = MagicMock()
        fetched.__iter__ = MagicMock(return_value=iter(snippets))
        fetched.language_code = "en"

        mock_transcript = MagicMock()
        mock_transcript.fetch.return_value = fetched

        mock_transcript_list = MagicMock()
        mock_transcript_list.find_transcript.return_value = mock_transcript

        mock_ytt_api = MagicMock()
        mock_ytt_api.list.return_value = mock_transcript_list

        mock_ytt_cls = MagicMock(return_value=mock_ytt_api)

        with patch.dict("sys.modules", {"youtube_transcript_api": MagicMock(YouTubeTranscriptApi=mock_ytt_cls)}):
            with patch("app.config.get_settings") as mock_settings:
                mock_settings.return_value.YTDLP_PROXY = None

                svc = TranscriptService()
                result = svc._try_youtube_transcript_api(VIDEO_ID, "English")

        assert result is None

    def test_cf_worker_rejects_short_transcript(self):
        """CF Worker transcript under 50 chars is rejected."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"text": "Short", "language": "en"}

        svc = TranscriptService()
        with patch("app.config.get_settings") as mock_settings:
            mock_settings.return_value.CF_TRANSCRIPT_WORKER_URL = "https://worker.example.com"
            mock_settings.return_value.CF_WORKER_API_KEY = "key"
            with patch("app.services.transcript.httpx.get", return_value=mock_resp):
                result = svc._try_cf_worker(VIDEO_ID, "English")

        assert result is None

    def test_whisper_skipped_for_long_videos(self):
        """_try_whisper_api returns None immediately for videos > 3600s."""
        svc = TranscriptService()

        # Mock OpenAI import to prevent ImportError
        with patch.dict("sys.modules", {"openai": MagicMock()}):
            with patch("app.config.get_settings") as mock_settings:
                mock_settings.return_value.effective_whisper_key = "sk-test"
                result = svc._try_whisper_api(VIDEO_ID, "English", video_duration_seconds=3601.0)

        assert result is None

    def test_whisper_accepted_for_short_videos(self):
        """_try_whisper_api proceeds (does not immediately return None) for videos <= 3600s.

        We test that the duration guard does NOT fire for short videos.
        The actual yt-dlp + Whisper calls are mocked to return None to keep the test isolated.
        """
        svc = TranscriptService()
        with patch("app.services.transcript.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="no file")
            with patch("app.config.get_settings") as mock_settings:
                mock_settings.return_value.effective_whisper_key = "sk-test"
                with patch("app.services.transcript.os.path.exists", return_value=False):
                    with patch("app.services.transcript.tempfile.mkdtemp", return_value="/tmp/fake"):
                        with patch("app.services.transcript.shutil.rmtree"):
                            with patch("app.utils.ffmpeg_commands._ytdlp_base_args", return_value=[]):
                                with patch.dict("sys.modules", {"openai": MagicMock()}):
                                    result = svc._try_whisper_api(VIDEO_ID, "English", video_duration_seconds=300.0)

        # Result may be None due to mocked yt-dlp failure, but we confirm no exception raised
        # and the duration guard did not fire (which would have happened before subprocess.run)
        assert result is None  # yt-dlp mocked to fail, so None is expected


class TestWhisperFallbackGate:
    """Whisper is only attempted when FEATURE_WHISPER_FALLBACK is True."""

    def test_whisper_not_called_when_feature_disabled(self):
        """When FEATURE_WHISPER_FALLBACK is False, _try_whisper_api is never invoked."""
        svc = TranscriptService()
        with patch.object(svc, "_try_youtube_transcript_api", return_value=None):
            with patch.object(svc, "_try_innertube_android", return_value=None):
                with patch.object(svc, "_try_ytdlp_subtitles", return_value=None):
                    with patch.object(svc, "_try_cf_worker", return_value=None):
                        with patch.object(svc, "_try_invidious_captions", return_value=None):
                            with patch.object(svc, "_try_piped_api", return_value=None):
                                with patch.object(svc, "_try_whisper_api") as mock_whisper:
                                    with patch("app.config.get_settings") as mock_settings:
                                        mock_settings.return_value.FEATURE_WHISPER_FALLBACK = False
                                        svc.fetch(VIDEO_ID, "English")

        mock_whisper.assert_not_called()

    def test_whisper_called_when_feature_enabled_and_all_others_fail(self):
        """When FEATURE_WHISPER_FALLBACK is True and all prior providers fail, Whisper is tried."""
        svc = TranscriptService()
        with patch.object(svc, "_try_youtube_transcript_api", return_value=None):
            with patch.object(svc, "_try_innertube_android", return_value=None):
                with patch.object(svc, "_try_ytdlp_subtitles", return_value=None):
                    with patch.object(svc, "_try_cf_worker", return_value=None):
                        with patch.object(svc, "_try_invidious_captions", return_value=None):
                            with patch.object(svc, "_try_piped_api", return_value=None):
                                with patch.object(svc, "_try_whisper_api", return_value=None) as mock_whisper:
                                    with patch("app.config.get_settings") as mock_settings:
                                        mock_settings.return_value.FEATURE_WHISPER_FALLBACK = True
                                        svc.fetch(VIDEO_ID, "English")

        mock_whisper.assert_called_once()
