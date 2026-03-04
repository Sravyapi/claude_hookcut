"""
Shared test fixtures for HookCut backend tests.
Uses SQLite in-memory database for speed and isolation.
"""
import os
import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, StaticPool
from sqlalchemy.orm import sessionmaker

# Set V0 mode OFF and a test secret before importing app code
os.environ["FEATURE_V0_MODE"] = "false"
os.environ["NEXTAUTH_SECRET"] = "test-secret-for-jwt-signing-min-32chars!"
os.environ["DATABASE_URL"] = "sqlite://"

# Import AFTER env vars are set
from app.models.base import Base
from app.models.user import User, CreditBalance, Subscription  # noqa: F401
from app.models.session import AnalysisSession, Hook, Short  # noqa: F401
from app.models.billing import Transaction  # noqa: F401
from app.models.learning import LearningLog  # noqa: F401
from app.dependencies import get_db, get_current_user_id
from app.main import create_app


# ─── Shared test engine (StaticPool ensures same connection) ───

_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_test_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


Base.metadata.create_all(bind=_test_engine)
TestSession = sessionmaker(bind=_test_engine, autocommit=False, autoflush=False)


# ─── Database fixture ───

TEST_USER_ID = "test-user-123"
TEST_USER_EMAIL = "test@hookcut.com"


def _cleanup(session):
    """Delete all rows from all tables in reverse FK order."""
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()


@pytest.fixture
def db():
    """Yield a database session, cleaning all rows after each test."""
    session = TestSession()
    try:
        yield session
    finally:
        _cleanup(session)
        session.close()


# ─── FastAPI test client fixtures ───

def _make_app(with_auth_override=True):
    """Create a FastAPI app with test database override."""
    application = create_app()

    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            _cleanup(session)
            session.close()

    application.dependency_overrides[get_db] = override_get_db

    if with_auth_override:
        async def override_get_current_user_id():
            return TEST_USER_ID
        application.dependency_overrides[get_current_user_id] = override_get_current_user_id

    return application


@pytest.fixture
def app():
    """Create a FastAPI app with dependency overrides for testing."""
    return _make_app(with_auth_override=True)


@pytest.fixture
def client(app):
    """HTTP test client with auth bypassed."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def unauthed_app():
    """FastAPI app without auth override — tests real JWT verification."""
    return _make_app(with_auth_override=False)


@pytest.fixture
def unauthed_client(unauthed_app):
    """HTTP test client that requires real JWT auth."""
    with TestClient(unauthed_app, raise_server_exceptions=False) as c:
        yield c


# ─── Data factory helpers ───

def make_user(db, user_id=None, email=None, currency="USD", plan_tier="free"):
    """Create a test user with credit balance."""
    user_id = user_id or str(uuid.uuid4())
    email = email or f"{user_id}@test.com"
    user = User(id=user_id, email=email, currency=currency, plan_tier=plan_tier)
    db.add(user)
    db.flush()
    balance = CreditBalance(user_id=user_id)
    db.add(balance)
    db.commit()
    return user


def make_session(
    db, user_id, video_id="dQw4w9WgXcQ", status="hooks_ready",
    minutes_charged=5.0, video_duration_seconds=300.0,
):
    """Create a test analysis session."""
    session = AnalysisSession(
        user_id=user_id,
        youtube_url=f"https://www.youtube.com/watch?v={video_id}",
        video_id=video_id,
        video_title="Test Video",
        video_duration_seconds=video_duration_seconds,
        niche="Generic",
        language="English",
        status=status,
        minutes_charged=minutes_charged,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def make_hook(db, session_id, rank=1, hook_text="Test hook", attention_score=8.5):
    """Create a test hook."""
    hook = Hook(
        session_id=session_id,
        rank=rank,
        hook_text=hook_text,
        start_time="0:00",
        end_time="0:30",
        start_seconds=0.0,
        end_seconds=30.0,
        hook_type="Curiosity Gap",
        funnel_role="curiosity_opener",
        scores={"scroll_stop": 8, "curiosity_gap": 9, "stakes_intensity": 7,
                "emotional_voltage": 8, "standalone_clarity": 8,
                "thematic_focus": 7, "thought_completeness": 8},
        attention_score=attention_score,
        platform_dynamics="High scroll-stop potential",
        viewer_psychology="Creates strong curiosity",
    )
    db.add(hook)
    db.commit()
    db.refresh(hook)
    return hook


def make_short(db, session_id, hook_id, status="queued"):
    """Create a test short."""
    short = Short(
        session_id=session_id,
        hook_id=hook_id,
        status=status,
        is_watermarked=True,
    )
    db.add(short)
    db.commit()
    db.refresh(short)
    return short
