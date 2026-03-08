"""
Redis-based rate limiting middleware.
V0: No-op (no rate limiting in local dev).
V1: Enforces per-user rate limits via Redis.
"""
import logging
import re
from functools import lru_cache
from fastapi import HTTPException, Request
from app.config import get_settings

logger = logging.getLogger(__name__)

# Allow only alphanumeric, hyphens, and underscores in Redis key components
_SAFE_KEY_RE = re.compile(r"[^a-zA-Z0-9_\-]")

# Sentinel user_id assigned to all unauthenticated / V0 local requests.
# Using this as a Redis key component would bucket every anonymous caller
# together, so we fall back to the client IP instead.
_ANON_USER_ID = "v0_local_user"

# Lua script: atomically INCR and set EXPIRE on first call, then compare.
# Returns 1 if the request is allowed, 0 if the limit is exceeded.
# The EXPIRE is only set when count == 1 (first hit in the window) so the
# window is fixed (not sliding) and the key always expires even if the
# INCR and EXPIRE were previously non-atomic.
_RATE_LIMIT_LUA = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local count = redis.call("INCR", key)
if count == 1 then redis.call("EXPIRE", key, window) end
if count > limit then return 0 end
return 1
"""


def _sanitize_key_component(value: str) -> str:
    """Sanitize a value for safe use in a Redis key.

    Strips characters that could be used for Redis key injection
    (spaces, newlines, colons, etc.), keeping only alphanumeric,
    hyphens, and underscores.
    """
    return _SAFE_KEY_RE.sub("", value)


def _get_client_ip(request: Request) -> str:
    """Extract the real client IP, preferring X-Forwarded-For (set by proxies/Vercel)."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Header may be a comma-separated list; the first entry is the originating IP.
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimiter:
    def __init__(self):
        settings = get_settings()
        if not settings.FEATURE_V0_MODE:
            import redis
            self.redis = redis.from_url(settings.REDIS_URL)
            self._lua_script = self.redis.register_script(_RATE_LIMIT_LUA)
        else:
            self.redis = None
            self._lua_script = None

    def check(
        self,
        user_id: str,
        action: str,
        limit: int,
        window_seconds: int,
        request: Request | None = None,
    ):
        """
        Check rate limit. Raises HTTPException(429) if exceeded.
        V0: always passes.

        Key strategy:
        - Authenticated users  → keyed by user_id  (per-account bucket)
        - Unauthenticated      → keyed by client IP (per-IP bucket)

        Atomicity: uses a registered Lua script so INCR + conditional EXPIRE
        execute in a single round-trip with no race window.
        """
        if self.redis is None:
            return

        # Determine the identifier to use for the rate-limit bucket.
        if user_id == _ANON_USER_ID:
            # Fall back to IP so anonymous users don't share one global bucket.
            identifier = _get_client_ip(request) if request else "unknown"
            identifier = f"ip:{identifier}"
        else:
            identifier = f"user:{user_id}"

        safe_action = _sanitize_key_component(action)
        safe_identifier = _sanitize_key_component(identifier)
        key = f"rate:{safe_action}:{safe_identifier}"

        allowed = self._lua_script(keys=[key], args=[limit, window_seconds])

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {limit} {action} per "
                       f"{window_seconds // 60} minutes.",
            )


@lru_cache(maxsize=1)
def get_rate_limiter() -> RateLimiter:
    return RateLimiter()
