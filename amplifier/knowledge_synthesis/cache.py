"""Cache implementation for synthesis results."""

import time
from collections import OrderedDict
from typing import Any


class SynthesisCache:
    """LRU cache for synthesis results with TTL."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """Initialize cache with size limit and TTL."""
        self._cache = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0

    def get(self, key: str, patterns_hash: str) -> list[dict[str, Any]] | None:
        """Get cached result if valid."""
        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]
        if time.time() - entry["timestamp"] > self._ttl or entry["patterns_hash"] != patterns_hash:
            self._misses += 1
            del self._cache[key]
            return None

        self._hits += 1
        self._cache.move_to_end(key)
        return entry["value"]

    def put(self, key: str, patterns_hash: str, value: list[dict[str, Any]], metadata: dict[str, Any]) -> None:
        """Store result in cache with timestamp and metadata."""
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)

        self._cache[key] = {
            "value": value,
            "patterns_hash": patterns_hash,
            "timestamp": time.time(),
            "metadata": metadata,
        }
        self._cache.move_to_end(key)

    def get_stats(self) -> dict[str, int]:
        """Get cache performance statistics."""
        return {"size": len(self._cache), "max_size": self._max_size, "hits": self._hits, "misses": self._misses}
