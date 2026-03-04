"""
Centralized exception hierarchy for HookCut backend.

All service/task exceptions should be subclasses of HookCutError.
Routers catch these and convert to HTTPException via hookcut_exception_handler.
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class HookCutError(Exception):
    """Base exception for all HookCut errors."""
    status_code: int = 500
    detail: str = "An internal error occurred"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


# --- Video Errors ---

class VideoError(HookCutError):
    status_code = 400
    detail = "Video error"


class InvalidURLError(VideoError):
    detail = "Invalid YouTube URL"


class MetadataFetchError(VideoError):
    detail = "Could not fetch video metadata"


class VideoAccessibilityError(VideoError):
    detail = "Video is not accessible"


class VideoTooLongError(VideoError):
    status_code = 422
    detail = "Video exceeds maximum duration"


# --- Transcript Errors ---

class TranscriptError(HookCutError):
    status_code = 422
    detail = "Transcript error"


class TranscriptUnavailableError(TranscriptError):
    detail = "Could not retrieve transcript from any provider"


# --- LLM Errors ---

class LLMError(HookCutError):
    status_code = 502
    detail = "LLM provider error"


class LLMProviderError(LLMError):
    detail = "LLM provider request failed"


class HookEngineError(LLMError):
    status_code = 500
    detail = "Hook analysis engine failed"


# --- Billing Errors ---

class BillingError(HookCutError):
    status_code = 400
    detail = "Billing error"


class InsufficientCreditsError(BillingError):
    status_code = 402
    detail = "Insufficient credits"


class PaymentProcessingError(BillingError):
    status_code = 500
    detail = "Payment processing failed"


# --- Resource Not Found ---

class ResourceNotFoundError(HookCutError):
    status_code = 404
    detail = "Resource not found"


class SessionNotFoundError(ResourceNotFoundError):
    detail = "Session not found"


class ShortNotFoundError(ResourceNotFoundError):
    detail = "Short not found"


class UserNotFoundError(ResourceNotFoundError):
    detail = "User not found"


# --- Invalid State ---

class InvalidStateError(HookCutError):
    status_code = 400
    detail = "Invalid state for this operation"


class HooksNotReadyError(InvalidStateError):
    detail = "Hooks are not ready for selection"


class ShortNotReadyError(InvalidStateError):
    detail = "Short is not ready"


# --- Short Generation ---

class ShortGenerationError(HookCutError):
    status_code = 500
    detail = "Short generation failed"


# --- Storage ---

class StorageError(HookCutError):
    status_code = 500
    detail = "Storage operation failed"


# --- FastAPI Exception Handler ---

async def hookcut_exception_handler(_request: Request, exc: HookCutError) -> JSONResponse:
    """Register with: app.add_exception_handler(HookCutError, hookcut_exception_handler)"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
