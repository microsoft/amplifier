"""
Model Configuration Module

Defines model categories for Amplifier AI operations.
Uses environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class ModelConfig(BaseSettings):
    """Model configuration with fast, default, and thinking categories."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Model categories with sensible defaults
    amplifier_model_fast: str = "claude-3-5-haiku-20241022"
    amplifier_model_default: str = "claude-sonnet-4-20250514"
    amplifier_model_thinking: str = "claude-opus-4-1-20250805"

    def get_model(self, category: str = "default") -> str:
        """Get model by category name.

        Args:
            category: One of "fast", "default", or "thinking"

        Returns:
            Model identifier string
        """
        if category == "fast":
            return self.amplifier_model_fast
        if category == "thinking":
            return self.amplifier_model_thinking
        return self.amplifier_model_default


# Global instance for easy access
models = ModelConfig()
