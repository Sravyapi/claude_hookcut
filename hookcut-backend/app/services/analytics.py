import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
_posthog_client = None


def _get_client():
    global _posthog_client
    if _posthog_client is None:
        settings = get_settings()
        if settings.POSTHOG_API_KEY:
            import posthog
            posthog.project_api_key = settings.POSTHOG_API_KEY
            posthog.host = settings.POSTHOG_HOST
            _posthog_client = posthog
    return _posthog_client


def track(user_id: str, event: str, properties: dict | None = None):
    """Track an analytics event."""
    client = _get_client()
    if client:
        try:
            client.capture(user_id, event, properties or {})
        except Exception as e:
            logger.warning(f"PostHog tracking failed: {e}")


def identify(user_id: str, properties: dict | None = None):
    """Identify a user with properties."""
    client = _get_client()
    if client:
        try:
            client.identify(user_id, properties or {})
        except Exception as e:
            logger.warning(f"PostHog identify failed: {e}")
