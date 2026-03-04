from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 4000) -> LLMResponse:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


@lru_cache(maxsize=3)
def get_provider(provider_name: str) -> LLMProvider:
    if provider_name == "openai":
        from app.llm.openai_provider import OpenAIProvider
        return OpenAIProvider()
    elif provider_name == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    elif provider_name == "gemini":
        from app.llm.gemini_provider import GeminiProvider
        return GeminiProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")


def get_fallback_provider(primary: str) -> LLMProvider:
    """Return the alternative provider as fallback. Falls back to primary if no key configured."""
    from app.config import get_settings
    settings = get_settings()
    fallback_map = {"openai": "anthropic", "anthropic": "openai", "gemini": "anthropic"}
    fallback = fallback_map.get(primary, "anthropic")

    # Only use fallback if its API key is actually configured
    key_map = {"openai": settings.OPENAI_API_KEY, "anthropic": settings.ANTHROPIC_API_KEY, "gemini": settings.GEMINI_API_KEY}
    if key_map.get(fallback):
        return get_provider(fallback)

    logger.info(f"Fallback provider '{fallback}' has no API key, retrying with '{primary}'")
    return get_provider(primary)
