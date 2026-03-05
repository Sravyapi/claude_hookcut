"""
Redis-based rate limiting middleware.
V0: No-op (no rate limiting in local dev).
V1: Enforces per-user rate limits via Redis.
"""
import logging
import re
from functools import lru_cache
from fastapi import HTTPException
from app.config import get_settings

logger = logging.getLogger(__name__)

# Allow only alphanumeric, hyphens, and underscores in Redis key components
_SAFE_KEY_RE = re.compile(r"[^a-zA-Z0-9_\-]")


def _sanitize_key_component(value: str) -> str:
    """Sanitize a value for safe use in a Redis key.

    Strips characters that could be used for Redis key injection
    (spaces, newlines, colons, etc.), keeping only alphanumeric,
    hyphens, and underscores.
    """
    return _SAFE_KEY_RE.sub("", value)


class RateLimiter:
    def __init__(self):
        settings = get_settings()
        if not settings.FEATURE_V0_MODE:
            import redis
            self.redis = redis.from_url(settings.REDIS_URL)
        else:
            self.redis = None

    def check(self, user_id: str, action: str, limit: int, window_seconds: int):
        """
        Check rate limit. Raises HTTPException(429) if exceeded.
        V0: always passes.
        Uses a pipeline to make INCR and EXPIRE atomic, avoiding a race
        condition where the key could persist indefinitely if EXPIRE is
        never reached after a standalone INCR.
        """
        if self.redis is None:
            return

        safe_action = _sanitize_key_component(action)
        safe_user_id = _sanitize_key_component(user_id)
        key = f"ratelimit:{safe_action}:{safe_user_id}"
        with self.redis.pipeline() as pipe:
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            results = pipe.execute()
            current = results[0]

        if current > limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {limit} {action} per "
                       f"{window_seconds // 60} minutes.",
            )


@lru_cache(maxsize=1)
def get_rate_limiter() -> RateLimiter:
    return RateLimiter()
