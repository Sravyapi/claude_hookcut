"""
Shared hook engine mode — persisted in Redis so web + Celery workers stay in sync.
"""

import logging
from functools import lru_cache

import redis

logger = logging.getLogger(__name__)
from app.config import get_settings

REDIS_KEY = "hookcut:hook_engine_mode"
DEFAULT_MODE = "llm_only"
VALID_MODES = {"llm_only", "deterministic_only", "llm_with_deterministic_fallback"}


@lru_cache(maxsize=1)
def _redis_client() -> redis.Redis:
    return redis.from_url(get_settings().REDIS_URL, decode_responses=True)


def get_engine_mode() -> str:
    try:
        mode = _redis_client().get(REDIS_KEY)
        return mode if mode in VALID_MODES else DEFAULT_MODE
    except Exception as e:
        logger.warning("Failed to read engine mode from Redis: %s", e)
        return DEFAULT_MODE


def set_engine_mode(mode: str) -> str:
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid mode: {mode}. Must be one of {VALID_MODES}")
    _redis_client().set(REDIS_KEY, mode)
    return mode
