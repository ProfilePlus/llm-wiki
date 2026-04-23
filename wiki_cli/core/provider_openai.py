"""OpenAI-compatible provider implementation."""

from openai import AsyncOpenAI

from .provider_base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible API provider (supports custom base_url)."""

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int = 4096,
    ) -> str:
        # Prepend system message
        full_messages = [{"role": "system", "content": system}] + messages

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""
