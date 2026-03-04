from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        kwargs = {}
        if settings.DATABASE_URL.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        else:
            kwargs["pool_size"] = 5
            kwargs["pool_pre_ping"] = True
            connect_args["connect_timeout"] = 10
        _engine = create_engine(
            settings.DATABASE_URL, connect_args=connect_args, **kwargs
        )
        if settings.DATABASE_URL.startswith("sqlite"):
            @event.listens_for(_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.close()
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _session_factory


def init_db():
    settings = get_settings()
    if settings.DATABASE_URL.startswith("sqlite"):
        # Only auto-create tables for SQLite (dev mode).
        # PostgreSQL tables are managed by Alembic migrations.
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
