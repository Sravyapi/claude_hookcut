import logging
import os
from pydantic import model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Core
    DATABASE_URL: str = "sqlite:///hookcut.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    FRONTEND_URL: str = "http://localhost:3000"
    DEBUG: bool = False

    # LLM
    LLM_PRIMARY_PROVIDER: str = "gemini"  # "openai", "anthropic", or "gemini"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    WHISPER_API_KEY: str = ""  # Falls back to OPENAI_API_KEY if empty
    YOUTUBE_API_KEY: str = ""  # YouTube Data API v3 for reliable metadata

    # Auth (V1 — NextAuth.js)
    NEXTAUTH_SECRET: str = ""
    NEXTAUTH_URL: str = "http://localhost:3000"

    # Payments (V1)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    RAZORPAY_PLAN_ID_LITE: str = ""
    RAZORPAY_PLAN_ID_PRO: str = ""

    # Storage (V1)
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "hookcut-shorts"
    R2_PUBLIC_URL: str = ""

    # Feature Flags
    FEATURE_V0_MODE: bool = False
    FEATURE_WHISPER_FALLBACK: bool = True
    FEATURE_R2_STORAGE: bool = False

    # Monitoring
    SENTRY_DSN: str = ""
    POSTHOG_API_KEY: str = ""
    POSTHOG_HOST: str = "https://app.posthog.com"

    # Proxy (required for YouTube access from cloud servers)
    YTDLP_PROXY: str = ""  # Generic proxy URL (e.g., http://user:pass@proxy:port)
    WEBSHARE_PROXY_USERNAME: str = ""  # Webshare rotating proxy (recommended)
    WEBSHARE_PROXY_PASSWORD: str = ""

    # Operational
    TEMP_FILE_TTL_HOURS: int = 24
    MAX_CONCURRENT_ANALYSES: int = 10
    RATE_LIMIT_ANALYSES_PER_HOUR: int = 10
    RATE_LIMIT_API_PER_MINUTE: int = 50

    @model_validator(mode='after')
    def validate_required_settings(self) -> 'Settings':
        # Skip validation in test mode
        if os.getenv("TESTING") == "true":
            return self

        # At least one LLM key must be set
        if not any([self.GEMINI_API_KEY, self.ANTHROPIC_API_KEY, self.OPENAI_API_KEY]):
            raise ValueError(
                "At least one LLM API key must be configured "
                "(GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY)"
            )

        # Auth secret must be set
        if not self.NEXTAUTH_SECRET:
            raise ValueError("NEXTAUTH_SECRET must be set")

        # SQLite must use absolute path for Celery worker compatibility
        if self.DATABASE_URL.startswith("sqlite:///") and not self.DATABASE_URL.startswith("sqlite:////"):
            raise ValueError(
                "SQLite DATABASE_URL must use absolute path: sqlite:////absolute/path/hookcut.db"
            )

        # JWT secret must be strong enough for HS256
        if self.NEXTAUTH_SECRET and len(self.NEXTAUTH_SECRET) < 32:
            logger.warning(
                "NEXTAUTH_SECRET is shorter than 32 characters. "
                "HS256 requires at least 256 bits (32 bytes) for secure signing. "
                "Generate a stronger secret with: openssl rand -base64 48"
            )

        return self

    @property
    def effective_whisper_key(self) -> str:
        return self.WHISPER_API_KEY or self.OPENAI_API_KEY

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
