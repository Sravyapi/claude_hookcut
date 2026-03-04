"""Tests for AnalysisSession, Hook, and Short models."""
from tests.conftest import make_user, make_session, make_hook, make_short
from app.models.session import AnalysisSession, Hook, Short


class TestAnalysisSession:
    def test_create_session(self, db):
        make_user(db, user_id="s1")
        session = make_session(db, "s1")
        assert session.user_id == "s1"
        assert session.status == "hooks_ready"
        assert session.video_id == "dQw4w9WgXcQ"
        assert session.niche == "Generic"
        assert session.language == "English"

    def test_session_defaults(self, db):
        make_user(db, user_id="s2")
        session = make_session(db, "s2", status="pending")
        assert session.regeneration_count == 0
        assert session.credits_refunded is False
        assert session.is_watermarked is True
        assert session.credits_source == "free"

    def test_session_status_values(self, db):
        make_user(db, user_id="s3")
        for status in ("pending", "fetching_transcript", "analyzing",
                        "hooks_ready", "generating_shorts", "completed", "failed"):
            session = make_session(db, "s3", status=status, video_id=f"vid-{status}")
            assert session.status == status

    def test_session_credit_tracking(self, db):
        make_user(db, user_id="s4")
        session = make_session(db, "s4")
        session.paid_minutes_used = 3.0
        session.free_minutes_used = 2.0
        session.credits_source = "mixed"
        db.commit()
        db.refresh(session)
        assert session.paid_minutes_used == 3.0
        assert session.free_minutes_used == 2.0


class TestHook:
    def test_create_hook(self, db):
        make_user(db, user_id="h1")
        session = make_session(db, "h1")
        hook = make_hook(db, session.id)
        assert hook.session_id == session.id
        assert hook.rank == 1
        assert hook.attention_score == 8.5
        assert hook.hook_type == "Curiosity Gap"

    def test_hook_scores_json(self, db):
        make_user(db, user_id="h2")
        session = make_session(db, "h2")
        hook = make_hook(db, session.id)
        assert isinstance(hook.scores, dict)
        assert hook.scores["scroll_stop"] == 8
        assert hook.scores["curiosity_gap"] == 9

    def test_hook_selection(self, db):
        make_user(db, user_id="h3")
        session = make_session(db, "h3")
        hook = make_hook(db, session.id)
        assert hook.is_selected is False
        hook.is_selected = True
        db.commit()
        db.refresh(hook)
        assert hook.is_selected is True

    def test_session_hooks_relationship(self, db):
        make_user(db, user_id="h4")
        session = make_session(db, "h4")
        for i in range(5):
            make_hook(db, session.id, rank=i + 1, hook_text=f"Hook {i}")
        db.refresh(session)
        assert len(session.hooks) == 5

    def test_hook_composite_flag(self, db):
        make_user(db, user_id="h5")
        session = make_session(db, "h5")
        hook = make_hook(db, session.id)
        hook.is_composite = True
        db.commit()
        db.refresh(hook)
        assert hook.is_composite is True


class TestShort:
    def test_create_short(self, db):
        make_user(db, user_id="sh1")
        session = make_session(db, "sh1")
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id)
        assert short.session_id == session.id
        assert short.hook_id == hook.id
        assert short.status == "queued"
        assert short.is_watermarked is True

    def test_short_status_transitions(self, db):
        make_user(db, user_id="sh2")
        session = make_session(db, "sh2")
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id)
        for status in ("downloading", "processing", "uploading", "ready", "failed", "expired"):
            short.status = status
            db.commit()
            db.refresh(short)
            assert short.status == status

    def test_short_with_video_data(self, db):
        make_user(db, user_id="sh3")
        session = make_session(db, "sh3")
        hook = make_hook(db, session.id)
        short = make_short(db, session.id, hook.id, status="ready")
        short.title = "Epic Hook Short"
        short.duration_seconds = 28.5
        short.file_size_bytes = 5_000_000
        short.video_file_key = "shorts/sh3/video.mp4"
        db.commit()
        db.refresh(short)
        assert short.title == "Epic Hook Short"
        assert short.duration_seconds == 28.5
