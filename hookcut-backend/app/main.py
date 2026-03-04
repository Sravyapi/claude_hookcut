import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import get_settings
from app.models.base import init_db

logger = logging.getLogger(__name__)
APP_VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    if settings.SENTRY_DSN:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                integrations=[FastApiIntegration()],
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
    )

    from app.exceptions import HookCutError, hookcut_exception_handler
    app.add_exception_handler(HookCutError, hookcut_exception_handler)

    origins = [settings.FRONTEND_URL]
    if settings.FEATURE_V0_MODE:
        origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.routers import analysis, shorts, tasks, user, billing, admin
    app.include_router(analysis.router, prefix="/api", tags=["analysis"])
    app.include_router(shorts.router, prefix="/api", tags=["shorts"])
    app.include_router(tasks.router, prefix="/api", tags=["tasks"])
    app.include_router(user.router, prefix="/api", tags=["user"])
    app.include_router(billing.router, prefix="/api", tags=["billing"])
    app.include_router(admin.router, prefix="/api", tags=["admin"])

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": APP_VERSION}

    if settings.DEBUG:
        @app.get("/debug-sentry")
        async def trigger_error():
            raise ValueError("Sentry test error")

    return app


app = create_app()


def get_app() -> FastAPI:
    """Factory for uvicorn: `uvicorn app.main:get_app --factory`"""
    return create_app()
