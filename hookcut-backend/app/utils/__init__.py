import logging

_logger = logging.getLogger(__name__)


def report_to_sentry(exc: Exception) -> None:
    """Best-effort Sentry exception capture. Silently no-ops if Sentry is not configured."""
    try:
        import sentry_sdk
        sentry_sdk.capture_exception(exc)
    except Exception as e:
        _logger.warning("Failed to report exception to Sentry: %s", e)
