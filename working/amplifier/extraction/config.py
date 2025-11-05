#!/usr/bin/env python3
"""
Configuration for Memory Extraction system.
Supports environment variables and .env files with sensible defaults.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class MemoryExtractionConfig(BaseSettings):
    """Configuration for Memory Extraction system with environment variable support"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    # Feature flag - must be explicitly enabled
    memory_system_enabled: bool = Field(
        default=False, description="Enable memory extraction system (must be explicitly set to true)"
    )

    # Model configuration
    memory_extraction_model: str = Field(
        default="claude-3-5-haiku-20241022",
        description="Model for memory extraction (fast, efficient, cost-effective)",
    )

    # Extraction configuration
    memory_extraction_timeout: int = Field(
        default=120, description="Timeout in seconds for Claude Code SDK extraction operations"
    )

    memory_extraction_max_messages: int = Field(
        default=20, description="Maximum number of recent messages to process for extraction"
    )

    memory_extraction_max_content_length: int = Field(
        default=500, description="Maximum characters per message to process"
    )

    memory_extraction_max_memories: int = Field(
        default=10, description="Maximum number of memories to extract per session"
    )

    # Storage configuration (for future use)
    memory_storage_dir: Path = Field(
        default=Path(".data/memories"), description="Directory for storing extracted memories"
    )

    # API Keys (optional - SDK may provide these)
    anthropic_api_key: str | None = Field(
        default=None, description="Anthropic API key (optional, Claude Code SDK may provide)"
    )

    def ensure_storage_dir(self) -> Path:
        """Ensure storage directory exists and return it"""
        self.memory_storage_dir.mkdir(parents=True, exist_ok=True)
        return self.memory_storage_dir


# Singleton instance
_config: MemoryExtractionConfig | None = None


def get_config() -> MemoryExtractionConfig:
    """Get or create the configuration singleton"""
    global _config
    if _config is None:
        _config = MemoryExtractionConfig()
    return _config


def reset_config() -> None:
    """Reset configuration (useful for testing)"""
    global _config
    _config = None
