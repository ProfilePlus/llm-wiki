"""Wiki context: config, active domain, provider."""

from pathlib import Path
from typing import Any

from .config import load_config


class WikiContext:
    """Context object passed to all commands."""

    def __init__(self):
        self.config = load_config()

    @property
    def data_dir(self) -> Path:
        """Get data directory as Path."""
        return Path(self.config["data_dir"])

    @property
    def active_domain(self) -> str | None:
        """Get active domain name."""
        return self.config.get("active_domain")

    @property
    def active_provider(self) -> str | None:
        """Get active provider name."""
        return self.config.get("active_provider")

    @property
    def domain_path(self) -> Path | None:
        """Get active domain path."""
        if not self.active_domain:
            return None
        return self.data_dir / self.active_domain

    @property
    def raw_path(self) -> Path | None:
        """Get active domain's raw/ path."""
        if not self.domain_path:
            return None
        return self.domain_path / "raw"

    @property
    def wiki_path(self) -> Path | None:
        """Get active domain's wiki/ path."""
        if not self.domain_path:
            return None
        return self.domain_path / "wiki"

    def get_provider_config(self, name: str | None = None) -> dict[str, Any] | None:
        """Get provider config by name (or active provider if name is None)."""
        if name is None:
            name = self.active_provider
        if not name:
            return None
        return self.config.get("providers", {}).get(name)

    def create_provider(self):
        """Create LLM provider instance from active provider config."""
        from .core.provider_anthropic import AnthropicProvider
        from .core.provider_openai import OpenAIProvider

        provider_config = self.get_provider_config()
        if not provider_config:
            raise ValueError("No active provider configured")

        provider_type = provider_config.get("type")
        api_key = provider_config.get("api_key")
        model = provider_config.get("model")
        base_url = provider_config.get("base_url")

        if provider_type == "anthropic":
            return AnthropicProvider(api_key=api_key, model=model, base_url=base_url)
        elif provider_type == "openai":
            return OpenAIProvider(api_key=api_key, model=model, base_url=base_url)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
