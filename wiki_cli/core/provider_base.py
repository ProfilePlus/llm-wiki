"""Base class for LLM providers."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(
        self,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int = 4096,
    ) -> str:
        """
        Complete a conversation.

        Args:
            system: System prompt
            messages: List of {"role": "user"|"assistant", "content": str}
            max_tokens: Maximum tokens to generate

        Returns:
            Assistant's response text
        """
        pass
