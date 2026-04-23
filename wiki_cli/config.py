"""Configuration management for wiki CLI."""

import json
from pathlib import Path
from typing import Any

from .constants import DEFAULT_CONFIG


def get_config_path() -> Path:
    """Get the config file path (~/.wiki/config.json)."""
    return Path.home() / ".wiki" / "config.json"


def load_config() -> dict[str, Any]:
    """Load config from ~/.wiki/config.json, or return default if not exists."""
    config_path = get_config_path()
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]) -> None:
    """Save config to ~/.wiki/config.json."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
