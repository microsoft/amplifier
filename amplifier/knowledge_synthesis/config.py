"""Configuration settings for synthesis caching."""

import os


class SynthesisCacheConfig:
    """Configuration for synthesis cache behavior."""

    def __init__(self):
        """Initialize cache configuration from environment variables."""
        self.enabled = os.getenv("SYNTHESIS_CACHE_ENABLED", "true").lower() == "true"
        self.max_size = int(os.getenv("SYNTHESIS_CACHE_MAX_SIZE", "1000"))
        self.ttl_seconds = int(os.getenv("SYNTHESIS_CACHE_TTL", "3600"))
