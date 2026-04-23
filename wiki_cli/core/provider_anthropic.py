"""Anthropic provider implementation."""

from anthropic import AsyncAnthropic

from .provider_base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic API provider."""

    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        self.client = AsyncAnthropic(api_key=api_key, base_url=base_url)
        self.model = model

    async def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int = 4096,
    ) -> str:
        response = await self.client.messages.create(
            model=self.model,
            system=system,
            messages=messages,
            max_tokens=max_tokens,
        )
        # Concatenate all text blocks
        parts = []
        for block in response.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "".join(parts)
