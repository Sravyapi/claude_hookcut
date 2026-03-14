"""Tests for run_analysis Celery task — state transitions, error handling, credit refunds."""
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select, create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from tests.conftest import make_user, make_session, make_hook, TestSession, _cleanup
from app.models.session import AnalysisSession, Hook
from app.models.learning import LearningLog


# ─── Helpers / stubs ─────────────────────────────────────────────────────────


@dataclass
class FakeTranscriptResult:
    provider: str = "youtube_captions"
    text: str = "This is a test transcript with enough content to analyze."


@dataclass
class FakeHookCandidate:
    rank: int = 1
    hook_text: str = "Test hook text"
    start_time: str = "0:00"
    end_time: str = "0:30"
    start_seconds: float = 0.0
    end_seconds: float = 30.0
    hook_type: str = "Curiosity Gap"
    funnel_role: str = "curiosity_opener"
    cognitive_tension: str = "hidden_knowledge"
    scores: dict = field(default_factory=lambda: {
        "scroll_stop": 8, "curiosity_gap": 9, "stakes_intensity": 7,
        "emotional_voltage": 8, "standalone_clarity": 8,
        "thought_completeness": 8, "click_through_likelihood": 7,
        "linguistic_compression": 8, "novelty_delta": 7, "information_density": 8,
    })
    attention_score: float = 8.5
    virality_score: float = 7.0
    justification: str = "Strong curiosity gap"
    algorithm_dynamics: dict = field(default_factory=lambda: {
        "retention_mechanics": "High scroll-stop potential",
        "watch_time_effect": "",
        "scroll_interruption": "",
    })
    viewer_psychology: dict = field(default_factory=lambda: {
        "primary_trigger": "curiosity_loop",
        "mechanism": "Creates strong curiosity",
        "tension_created": "",
    })
    improvement_suggestion: Optional[str] = None
    primary_speaker: Optional[str] = None
    is_composite: bool = False


@dataclass
class FakeAnalysisResult:
    hooks: list = field(default_factory=lambda: [FakeHookCandidate(rank=i + 1) for i in range(5)])
    provider: str = "gemini"
    attempts: int = 1


def _fresh_db():
    """Return a new db session on the shared in-memory engine for post-task verification."""
    return TestSession()


def _run_task(session_id: str):
    """
    Invoke run_analysis synchronously, patching update_state on the task instance.

    The Celery task closes the db session it receives in its finally block.
    We pass a fresh session per call to avoid contaminating the test db fixture.
    The task's bind=True `self` is the task instance; we patch update_state on it.
    Returns (result, mock_update_state).
    """
    from app.tasks.analyze_task import run_analysis
    mock_update_state = MagicMock()
    with patch.object(run_analysis, "update_state", mock_update_state):
        result = run_analysis.__wrapped__(session_id)
    return result, mock_update_state


# ─── Successful flow ──────────────────────────────────────────────────────────


class TestRunAnalysisSuccess:
    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_returns_success_dict(
        self, mock_get_db, mock_ts_cls, mock_he_cls, mock_engine_mode, db
    ):
        user = make_user(db, user_id="at-succ-1")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult()
        mock_he_cls.return_value.analyze.return_value = FakeAnalysisResult()

        result, _ = _run_task(session_id)

        assert result["session_id"] == session_id
        assert result["hooks_count"] == 5
        assert result["provider"] == "gemini"
        assert result["attempts"] == 1

    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_hooks_saved_to_db(
        self, mock_get_db, mock_ts_cls, mock_he_cls, mock_engine_mode, db
    ):
        user = make_user(db, user_id="at-succ-2")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult()
        mock_he_cls.return_value.analyze.return_value = FakeAnalysisResult()

        _run_task(session_id)

        verify_db = _fresh_db()
        try:
            hooks = verify_db.execute(
                select(Hook).where(Hook.session_id == session_id)
            ).scalars().all()
            assert len(hooks) == 5
            ranks = sorted(h.rank for h in hooks)
            assert ranks == [1, 2, 3, 4, 5]
        finally:
            verify_db.close()

    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_session_status_becomes_hooks_ready(
        self, mock_get_db, mock_ts_cls, mock_he_cls, mock_engine_mode, db
    ):
        user = make_user(db, user_id="at-succ-3")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult()
        mock_he_cls.return_value.analyze.return_value = FakeAnalysisResult()

        _run_task(session_id)

        verify_db = _fresh_db()
        try:
            updated = verify_db.get(AnalysisSession, session_id)
            assert updated.status == "hooks_ready"
        finally:
            verify_db.close()

    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_learning_logs_created(
        self, mock_get_db, mock_ts_cls, mock_he_cls, mock_engine_mode, db
    ):
        user = make_user(db, user_id="at-succ-4")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult()
        mock_he_cls.return_value.analyze.return_value = FakeAnalysisResult()

        _run_task(session_id)

        verify_db = _fresh_db()
        try:
            logs = verify_db.execute(
                select(LearningLog).where(LearningLog.session_id == session_id)
            ).scalars().all()
            assert len(logs) == 5
            assert all(log.event_type == "hook_presented" for log in logs)
        finally:
            verify_db.close()


# ─── State transitions (update_state calls) ──────────────────────────────────


class TestStateTransitions:
    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_update_state_called_multiple_times(
        self, mock_get_db, mock_ts_cls, mock_he_cls, mock_engine_mode, db
    ):
        user = make_user(db, user_id="at-state-1")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult()
        mock_he_cls.return_value.analyze.return_value = FakeAnalysisResult()

        _, mock_update_state = _run_task(session_id)

        # Task calls update_state at: transcript fetch (10%), analyzing (40%),
        # saving hooks (80%), hooks ready (100%)
        assert mock_update_state.call_count >= 3

    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_first_update_state_has_progress_10(
        self, mock_get_db, mock_ts_cls, mock_he_cls, mock_engine_mode, db
    ):
        user = make_user(db, user_id="at-state-1b")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult()
        mock_he_cls.return_value.analyze.return_value = FakeAnalysisResult()

        _, mock_update_state = _run_task(session_id)

        first_call = mock_update_state.call_args_list[0]
        # update_state called as keyword args: update_state(state=..., meta={...})
        meta = first_call[1].get("meta") or {}
        assert meta.get("progress") == 10

    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_session_db_status_becomes_hooks_ready(
        self, mock_get_db, mock_ts_cls, mock_he_cls, mock_engine_mode, db
    ):
        user = make_user(db, user_id="at-state-2")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult()
        mock_he_cls.return_value.analyze.return_value = FakeAnalysisResult()

        _run_task(session_id)

        verify_db = _fresh_db()
        try:
            updated = verify_db.get(AnalysisSession, session_id)
            assert updated.status == "hooks_ready"
            # transcript_text set proves 'analyzing' stage was reached
            assert updated.transcript_text is not None
        finally:
            verify_db.close()


# ─── Session not found ────────────────────────────────────────────────────────


class TestSessionNotFound:
    @patch("app.tasks.analyze_task.get_db_session")
    def test_returns_error_when_session_missing(self, mock_get_db, db):
        task_db = _fresh_db()
        mock_get_db.return_value = task_db

        result, _ = _run_task("nonexistent-session-id")

        assert "error" in result
        assert "not found" in result["error"].lower()


# ─── Transcript failure ───────────────────────────────────────────────────────


class TestTranscriptFailure:
    @patch("app.tasks.analyze_task.CreditManager")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_transcript_unavailable_calls_refund_and_fail(
        self, mock_get_db, mock_ts_cls, mock_cm_cls, db
    ):
        user = make_user(db, user_id="at-trans-1")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = None  # All providers failed
        mock_cm_instance = MagicMock()
        mock_cm_cls.return_value = mock_cm_instance

        result, _ = _run_task(session_id)

        mock_cm_instance.refund_and_fail.assert_called_once()
        called_args = mock_cm_instance.refund_and_fail.call_args
        session_id_arg = called_args[0][0] if called_args[0] else called_args[1].get("session_id")
        assert session_id_arg == session_id
        assert "error" in result

    @patch("app.tasks.analyze_task.CreditManager")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_transcript_unavailable_returns_error(
        self, mock_get_db, mock_ts_cls, mock_cm_cls, db
    ):
        user = make_user(db, user_id="at-trans-2")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = None
        mock_cm_cls.return_value = MagicMock()

        result, _ = _run_task(session_id)

        assert result == {"error": "Transcript unavailable"}


# ─── LLM failure ─────────────────────────────────────────────────────────────


class TestLLMFailure:
    @patch("app.tasks.analyze_task.CreditManager")
    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_llm_failure_calls_refund_and_fail(
        self, mock_get_db, mock_ts_cls, mock_he_cls, mock_engine_mode, mock_cm_cls, db
    ):
        from app.exceptions import HookEngineError

        user = make_user(db, user_id="at-llm-1")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult()
        mock_he_cls.return_value.analyze.side_effect = HookEngineError("LLM failed")
        mock_cm_instance = MagicMock()
        mock_cm_cls.return_value = mock_cm_instance

        result, _ = _run_task(session_id)

        mock_cm_instance.refund_and_fail.assert_called_once()
        assert "error" in result

    @patch("app.tasks.analyze_task.CreditManager")
    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_llm_failure_no_hooks_saved(
        self, mock_get_db, mock_ts_cls, mock_he_cls, mock_engine_mode, mock_cm_cls, db
    ):
        from app.exceptions import HookEngineError

        user = make_user(db, user_id="at-llm-2")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult()
        mock_he_cls.return_value.analyze.side_effect = HookEngineError("LLM failed")
        mock_cm_cls.return_value = MagicMock()

        _run_task(session_id)

        verify_db = _fresh_db()
        try:
            hooks = verify_db.execute(
                select(Hook).where(Hook.session_id == session_id)
            ).scalars().all()
            assert len(hooks) == 0
        finally:
            verify_db.close()


# ─── Unexpected exception ─────────────────────────────────────────────────────


class TestUnexpectedException:
    @patch("app.tasks.analyze_task.CreditManager")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_unexpected_exception_calls_refund_and_fail(
        self, mock_get_db, mock_ts_cls, mock_cm_cls, db
    ):
        user = make_user(db, user_id="at-exc-1")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.side_effect = RuntimeError("Unexpected network error")
        mock_cm_instance = MagicMock()
        mock_cm_cls.return_value = mock_cm_instance

        result, _ = _run_task(session_id)

        mock_cm_instance.refund_and_fail.assert_called_once()
        assert "error" in result

    @patch("app.tasks.analyze_task.CreditManager")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_returns_friendly_error_not_raw_exception(
        self, mock_get_db, mock_ts_cls, mock_cm_cls, db
    ):
        user = make_user(db, user_id="at-exc-2")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.side_effect = RuntimeError("connection timeout")
        mock_cm_cls.return_value = MagicMock()

        result, _ = _run_task(session_id)

        assert "Traceback" not in result.get("error", "")
        assert result["error"] == "Analysis timed out. Please try again."


# ─── _friendly_error ─────────────────────────────────────────────────────────


class TestFriendlyError:
    def test_transcript_keyword(self):
        from app.tasks.analyze_task import _friendly_error
        msg = _friendly_error(Exception("no transcript available"))
        assert "caption" in msg.lower() or "transcript" in msg.lower()

    def test_rate_limit_keyword(self):
        from app.tasks.analyze_task import _friendly_error
        msg = _friendly_error(Exception("rate limit exceeded"))
        assert "busy" in msg.lower() or "wait" in msg.lower()

    def test_timeout_keyword(self):
        from app.tasks.analyze_task import _friendly_error
        msg = _friendly_error(Exception("request timed out"))
        assert "timed out" in msg.lower() or "try again" in msg.lower()

    def test_api_key_keyword(self):
        from app.tasks.analyze_task import _friendly_error
        msg = _friendly_error(Exception("api key invalid"))
        assert "configuration" in msg.lower() or "support" in msg.lower()

    def test_http_401_keyword(self):
        from app.tasks.analyze_task import _friendly_error
        msg = _friendly_error(Exception("401 unauthorized"))
        assert "configuration" in msg.lower() or "support" in msg.lower()

    def test_sqlalchemy_keyword(self):
        from app.tasks.analyze_task import _friendly_error
        msg = _friendly_error(Exception("sqlalchemy error: data too long for column"))
        assert "save" in msg.lower() or "results" in msg.lower()

    def test_generic_fallback(self):
        from app.tasks.analyze_task import _friendly_error
        msg = _friendly_error(Exception("something completely unknown"))
        assert msg == "Analysis failed. Please try again."

    def test_429_keyword(self):
        from app.tasks.analyze_task import _friendly_error
        msg = _friendly_error(Exception("HTTP 429 too many requests"))
        assert "busy" in msg.lower() or "wait" in msg.lower()

    def test_caption_keyword(self):
        from app.tasks.analyze_task import _friendly_error
        msg = _friendly_error(Exception("auto caption not available"))
        assert "caption" in msg.lower() or "transcript" in msg.lower()


# ─── Engine mode branching ────────────────────────────────────────────────────


class TestEngineModeBranching:
    @patch("app.tasks.analyze_task.get_engine_mode", return_value="deterministic_only")
    @patch("app.tasks.analyze_task.DeterministicEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_deterministic_only_mode_uses_deterministic_engine(
        self, mock_get_db, mock_ts_cls, mock_det_cls, mock_engine_mode, db
    ):
        user = make_user(db, user_id="at-mode-1")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult()
        mock_det_cls.return_value.analyze.return_value = FakeAnalysisResult()

        _run_task(session_id)

        mock_det_cls.return_value.analyze.assert_called_once()

    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_with_deterministic_fallback")
    @patch("app.tasks.analyze_task.DeterministicEngine")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_llm_fallback_mode_uses_deterministic_on_llm_failure(
        self, mock_get_db, mock_ts_cls, mock_he_cls, mock_det_cls, mock_engine_mode, db
    ):
        from app.exceptions import HookEngineError

        user = make_user(db, user_id="at-mode-2")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult()
        mock_he_cls.return_value.analyze.side_effect = HookEngineError("LLM unavailable")
        mock_det_cls.return_value.analyze.return_value = FakeAnalysisResult()

        result, _ = _run_task(session_id)

        mock_det_cls.return_value.analyze.assert_called_once()
        assert result["hooks_count"] == 5

    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_llm_only_mode_uses_hook_engine(
        self, mock_get_db, mock_ts_cls, mock_he_cls, mock_engine_mode, db
    ):
        user = make_user(db, user_id="at-mode-3")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult()
        mock_he_cls.return_value.analyze.return_value = FakeAnalysisResult()

        _run_task(session_id)

        mock_he_cls.return_value.analyze.assert_called_once()

    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_with_deterministic_fallback")
    @patch("app.tasks.analyze_task.DeterministicEngine")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_llm_fallback_mode_tries_llm_first(
        self, mock_get_db, mock_ts_cls, mock_he_cls, mock_det_cls, mock_engine_mode, db
    ):
        user = make_user(db, user_id="at-mode-4")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult()
        mock_he_cls.return_value.analyze.return_value = FakeAnalysisResult()  # LLM succeeds

        result, _ = _run_task(session_id)

        mock_he_cls.return_value.analyze.assert_called_once()
        mock_det_cls.return_value.analyze.assert_not_called()
        assert result["hooks_count"] == 5


# ─── Transcript stored in session ────────────────────────────────────────────


class TestTranscriptStored:
    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_transcript_text_saved_on_session(
        self, mock_get_db, mock_ts_cls, mock_he_cls, mock_engine_mode, db
    ):
        user = make_user(db, user_id="at-tr-1")
        session = make_session(db, user.id, status="pending")
        session_id = session.id

        transcript_text = "The quick brown fox jumps over the lazy dog."
        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult(
            text=transcript_text, provider="cf_worker"
        )
        mock_he_cls.return_value.analyze.return_value = FakeAnalysisResult()

        _run_task(session_id)

        verify_db = _fresh_db()
        try:
            updated = verify_db.get(AnalysisSession, session_id)
            assert updated.transcript_text == transcript_text
            assert updated.transcript_provider == "cf_worker"
        finally:
            verify_db.close()


# ─── Interview mode ──────────────────────────────────────────────────────────


class TestInterviewModeAnalysis:
    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_interview_mode_uses_diarization(
        self, mock_get_db, mock_he_cls, mock_engine_mode, db
    ):
        """When interview_mode=True, AssemblyAI diarizer is called instead of TranscriptService."""
        user = make_user(db, user_id="at-int-1")
        session = make_session(db, user.id, status="pending")
        session.interview_mode = True
        session.speaker_count = 2
        db.commit()
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_he_cls.return_value.analyze.return_value = FakeAnalysisResult()

        from app.services.assemblyai_diarization import DiarizationResult, SpeakerUtterance
        fake_diarize = DiarizationResult(
            utterances=[
                SpeakerUtterance("Speaker A", 0, 5000, "Hello"),
                SpeakerUtterance("Speaker B", 5000, 10000, "Hi there"),
            ],
            detected_speaker_count=2,
            transcript_text="[Speaker A] [0:00] Hello\n[Speaker B] [0:05] Hi there",
        )

        with patch("app.services.assemblyai_diarization.AssemblyAIDiarizer") as mock_diarizer_cls:
            mock_diarizer_cls.return_value.diarize.return_value = fake_diarize
            result, _ = _run_task(session_id)

        assert result["hooks_count"] == 5
        verify_db = _fresh_db()
        try:
            updated = verify_db.get(AnalysisSession, session_id)
            assert updated.transcript_provider == "assemblyai"
            assert updated.diarization_data is not None
            assert len(updated.diarization_data) == 2
        finally:
            verify_db.close()

    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_diarization_failure_falls_back_to_regular_transcript(
        self, mock_get_db, mock_ts_cls, mock_he_cls, mock_engine_mode, db
    ):
        """If diarization fails, falls back to regular transcript and sets interview_mode=False."""
        user = make_user(db, user_id="at-int-2")
        session = make_session(db, user.id, status="pending")
        session.interview_mode = True
        session.speaker_count = 2
        db.commit()
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult()
        mock_he_cls.return_value.analyze.return_value = FakeAnalysisResult()

        with patch("app.services.assemblyai_diarization.AssemblyAIDiarizer") as mock_diarizer_cls:
            mock_diarizer_cls.side_effect = Exception("API key missing")
            result, _ = _run_task(session_id)

        assert result["hooks_count"] == 5
        # Regular transcript service should have been called
        mock_ts_cls.return_value.fetch.assert_called_once()
        # interview_mode should be reset
        verify_db = _fresh_db()
        try:
            updated = verify_db.get(AnalysisSession, session_id)
            assert updated.interview_mode is False
        finally:
            verify_db.close()

    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_speaker_count_updated_when_mismatch(
        self, mock_get_db, mock_he_cls, mock_engine_mode, db
    ):
        """If AssemblyAI detects different speaker count, session is updated."""
        user = make_user(db, user_id="at-int-3")
        session = make_session(db, user.id, status="pending")
        session.interview_mode = True
        session.speaker_count = 2
        db.commit()
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_he_cls.return_value.analyze.return_value = FakeAnalysisResult()

        from app.services.assemblyai_diarization import DiarizationResult, SpeakerUtterance
        fake_diarize = DiarizationResult(
            utterances=[
                SpeakerUtterance("Speaker A", 0, 5000, "Hello"),
                SpeakerUtterance("Speaker B", 5000, 10000, "Hi"),
                SpeakerUtterance("Speaker C", 10000, 15000, "Hey"),
            ],
            detected_speaker_count=3,
            transcript_text="[Speaker A] Hello\n[Speaker B] Hi\n[Speaker C] Hey",
        )

        with patch("app.services.assemblyai_diarization.AssemblyAIDiarizer") as mock_diarizer_cls:
            mock_diarizer_cls.return_value.diarize.return_value = fake_diarize
            _run_task(session_id)

        verify_db = _fresh_db()
        try:
            updated = verify_db.get(AnalysisSession, session_id)
            assert updated.speaker_count == 3
        finally:
            verify_db.close()

    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_primary_speaker_stored_on_hooks(
        self, mock_get_db, mock_he_cls, mock_engine_mode, db
    ):
        """Hooks with primary_speaker set are stored correctly in DB."""
        user = make_user(db, user_id="at-int-4")
        session = make_session(db, user.id, status="pending")
        session.interview_mode = True
        session.speaker_count = 2
        db.commit()
        session_id = session.id

        task_db = _fresh_db()
        mock_get_db.return_value = task_db

        from app.services.assemblyai_diarization import DiarizationResult, SpeakerUtterance
        fake_diarize = DiarizationResult(
            utterances=[SpeakerUtterance("Speaker A", 0, 5000, "Hello")],
            detected_speaker_count=2,
            transcript_text="[Speaker A] Hello",
        )

        candidates_with_speaker = [
            FakeHookCandidate(rank=i + 1, primary_speaker="Speaker A" if i % 2 == 0 else "Speaker B")
            for i in range(5)
        ]
        mock_he_cls.return_value.analyze.return_value = FakeAnalysisResult(hooks=candidates_with_speaker)

        with patch("app.services.assemblyai_diarization.AssemblyAIDiarizer") as mock_diarizer_cls:
            mock_diarizer_cls.return_value.diarize.return_value = fake_diarize
            _run_task(session_id)

        verify_db = _fresh_db()
        try:
            hooks = verify_db.execute(
                select(Hook).where(Hook.session_id == session_id).order_by(Hook.rank)
            ).scalars().all()
            assert hooks[0].primary_speaker == "Speaker A"
            assert hooks[1].primary_speaker == "Speaker B"
        finally:
            verify_db.close()


# ─── Hooks cleared on regeneration ───────────────────────────────────────────


class TestHooksCleared:
    @patch("app.tasks.analyze_task.get_engine_mode", return_value="llm_only")
    @patch("app.tasks.analyze_task.HookEngine")
    @patch("app.tasks.analyze_task.TranscriptService")
    @patch("app.tasks.analyze_task.get_db_session")
    def test_existing_hooks_cleared_before_saving_new_ones(
        self, mock_get_db, mock_ts_cls, mock_he_cls, mock_engine_mode, db
    ):
        """On regeneration, old hooks should be replaced by the new set."""
        user = make_user(db, user_id="at-clear-1")
        session = make_session(db, user.id, status="pending")
        session_id = session.id
        # Pre-populate with stale hooks from a previous run
        for i in range(3):
            make_hook(db, session_id, rank=i + 1, hook_text=f"Old hook {i}")

        task_db = _fresh_db()
        mock_get_db.return_value = task_db
        mock_ts_cls.return_value.fetch.return_value = FakeTranscriptResult()
        mock_he_cls.return_value.analyze.return_value = FakeAnalysisResult(
            hooks=[FakeHookCandidate(rank=i + 1, hook_text=f"New hook {i}") for i in range(5)]
        )

        _run_task(session_id)

        verify_db = _fresh_db()
        try:
            hooks = verify_db.execute(
                select(Hook).where(Hook.session_id == session_id)
            ).scalars().all()
            assert len(hooks) == 5
            assert all("New hook" in h.hook_text for h in hooks)
        finally:
            verify_db.close()
