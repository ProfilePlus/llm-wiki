"""Performance caching for MCP server."""

import time
from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Cache entry with TTL."""
    value: Any
    timestamp: float
    ttl: float

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return time.time() - self.timestamp > self.ttl


class WikiCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, default_ttl: float = 300):
        """
        Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache with optional custom TTL."""
        ttl = ttl if ttl is not None else self._default_ttl
        self._cache[key] = CacheEntry(
            value=value,
            timestamp=time.time(),
            ttl=ttl
        )

    def invalidate(self, key: str) -> None:
        """Remove key from cache."""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "size": len(self._cache)
        }
