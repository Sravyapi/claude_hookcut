import json
import logging
import uuid

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models.base import init_db

logger = logging.getLogger(__name__)
APP_VERSION = "0.1.0"


class _JSONFormatter(logging.Formatter):
    """Emit one JSON object per log line — makes Railway logs queryable by level/message (OBS-06)."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record),
        }
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def _configure_production_logging() -> None:
    """Replace the root handler with a JSON formatter when not in DEBUG mode."""
    handler = logging.StreamHandler()
    handler.setFormatter(_JSONFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    if not root.level:
        root.setLevel(logging.INFO)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response (HIGH-31)."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        response.headers["X-Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a correlation ID to every response (OBS-08)."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.config import get_settings as _gs
    if not _gs().DEBUG:
        _configure_production_logging()
    init_db()
    _validate_config_on_startup()
    yield


def _validate_config_on_startup() -> None:
    """Raise ValueError at startup if required production secrets are missing."""
    import os
    if os.environ.get("TESTING") == "true":
        return
    settings = get_settings()
    if not settings.FEATURE_V0_MODE:
        # Only enforce webhook secrets if the corresponding payment key is also set
        # (prevents blocking dev environments where Stripe/Razorpay aren't configured yet)
        if settings.STRIPE_SECRET_KEY and not settings.STRIPE_WEBHOOK_SECRET:
            raise ValueError("STRIPE_WEBHOOK_SECRET must be set when STRIPE_SECRET_KEY is configured")
        if settings.RAZORPAY_KEY_ID and not settings.RAZORPAY_WEBHOOK_SECRET:
            raise ValueError("RAZORPAY_WEBHOOK_SECRET must be set when RAZORPAY_KEY_ID is configured")


def create_app() -> FastAPI:
    settings = get_settings()

    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.celery import CeleryIntegration
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                integrations=[FastApiIntegration(), CeleryIntegration()],
                traces_sample_rate=0.1,
                environment="production",
            )
            logger.info("Sentry initialized")
        except Exception as e:
            logger.warning(f"Sentry init failed (non-fatal): {e}")

    app = FastAPI(
        title="HookCut API",
        description="Extract hook segments from YouTube videos and generate Shorts",
        version=APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )

    from app.exceptions import HookCutError, hookcut_exception_handler
    app.add_exception_handler(HookCutError, hookcut_exception_handler)

    origins = [settings.FRONTEND_URL]
    # HIGH-30: Only add localhost origins in DEBUG mode to avoid leaking dev CORS policy in prod
    if settings.DEBUG:
        origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # HIGH-31: Security response headers on every request
    app.add_middleware(SecurityHeadersMiddleware)

    # OBS-08: Correlation ID on every response
    app.add_middleware(RequestIDMiddleware)

    from app.routers import analysis, shorts, tasks, user, billing, admin, auth
    app.include_router(analysis.router, prefix="/api", tags=["analysis"])
    app.include_router(shorts.router, prefix="/api", tags=["shorts"])
    app.include_router(tasks.router, prefix="/api", tags=["tasks"])
    app.include_router(user.router, prefix="/api", tags=["user"])
    app.include_router(billing.router, prefix="/api", tags=["billing"])
    app.include_router(admin.router, prefix="/api", tags=["admin"])
    app.include_router(auth.router, prefix="/api", tags=["auth"])

    from app.dependencies import get_db

    @app.get("/api/health")
    async def health(db: Session = Depends(get_db)):
        checks: dict = {}
        overall = "healthy"

        # DB check
        try:
            db.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as e:
            logger.error(f"Health check DB error: {e}")
            checks["database"] = f"error: {str(e)[:100]}"
            overall = "degraded"

        # Redis check (lazy singleton, run in thread to avoid blocking event loop)
        try:
            if not hasattr(health, "_redis_client"):
                import redis as redis_lib
                health._redis_client = redis_lib.from_url(settings.REDIS_URL)
            import anyio
            await anyio.to_thread.run_sync(health._redis_client.ping)
            checks["redis"] = "ok"
        except Exception as e:
            logger.error(f"Health check Redis error: {e}")
            checks["redis"] = f"error: {str(e)[:100]}"
            overall = "degraded"
            # Reset client so next call retries connection
            if hasattr(health, "_redis_client"):
                del health._redis_client

        return {"status": overall, "checks": checks, "version": APP_VERSION}

    if settings.DEBUG:
        @app.get("/debug-sentry")
        async def trigger_error():
            raise ValueError("Sentry test error")

    return app


app = create_app()


def get_app() -> FastAPI:
    """Factory for uvicorn: `uvicorn app.main:get_app --factory`"""
    return app
