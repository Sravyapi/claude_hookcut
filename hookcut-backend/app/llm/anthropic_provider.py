from anthropic import Anthropic
from app.llm.provider import LLMProvider, LLMResponse
from app.config import get_settings


class AnthropicProvider(LLMProvider):
    def __init__(self):
        settings = get_settings()
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"

    @property
    def name(self) -> str:
        return "anthropic"

    def generate(self, prompt: str, max_tokens: int = 4000, json_mode: bool = False) -> LLMResponse:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = ""
        for block in response.content:
            if block.type == "text":
                text += block.text

        return LLMResponse(
            text=text,
            provider="anthropic",
            model=self.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
