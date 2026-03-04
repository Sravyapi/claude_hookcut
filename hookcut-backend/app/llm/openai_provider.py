from openai import OpenAI
from app.llm.provider import LLMProvider, LLMResponse
from app.config import get_settings


class OpenAIProvider(LLMProvider):
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"

    @property
    def name(self) -> str:
        return "openai"

    def generate(self, prompt: str, max_tokens: int = 4000) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        choice = response.choices[0]
        return LLMResponse(
            text=choice.message.content or "",
            provider="openai",
            model=self.model,
            input_tokens=response.usage.prompt_tokens if response.usage else None,
            output_tokens=response.usage.completion_tokens if response.usage else None,
        )
