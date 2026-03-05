import httpx
import logging
from app.llm.provider import LLMProvider, LLMResponse
from app.config import get_settings

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.GEMINI_API_KEY
        self.model = "gemini-2.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def name(self) -> str:
        return "gemini"

    def generate(self, prompt: str, max_tokens: int = 4000) -> LLMResponse:
        url = f"{self.base_url}/models/{self.model}:generateContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens * 2,  # Extra budget for thinking tokens
                "temperature": 0.7,
                "responseMimeType": "application/json",
            },
        }

        try:
            with httpx.Client(timeout=180) as client:
                resp = client.post(url, json=payload, headers=headers)
                if resp.status_code == 429:
                    raise RuntimeError(
                        "Gemini rate limit hit (429). Free tier allows ~15 requests/minute. "
                        "Wait 60 seconds and try again."
                    )
                resp.raise_for_status()
                data = resp.json()
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Gemini API request failed: {e}") from e

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            logger.error(
                f"Gemini response parsing failed. Raw response: {data!r}. Error: {e}"
            )
            raise RuntimeError(f"LLM response parsing failed: {e}") from e

        usage = data.get("usageMetadata", {})

        return LLMResponse(
            text=text,
            provider="gemini",
            model=self.model,
            input_tokens=usage.get("promptTokenCount"),
            output_tokens=usage.get("candidatesTokenCount"),
        )
