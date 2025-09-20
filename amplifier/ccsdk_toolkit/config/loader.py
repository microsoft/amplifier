"""Configuration loader for CCSDK toolkit."""

import json
from pathlib import Path
from typing import Union

from .models import AgentConfig
from .models import EnvironmentConfig


class ConfigLoader:
    """Utility for loading and managing configurations.

    Provides methods to load configurations from files or dictionaries,
    with validation and default handling.
    """

    @staticmethod
    def load_agent_config(source: Union[str, Path, dict]) -> AgentConfig:
        """Load agent configuration from various sources.

        Args:
            source: Path to JSON/YAML file, or dict with config

        Returns:
            Validated AgentConfig instance
        """
        if isinstance(source, dict):
            return AgentConfig(**source)

        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        if path.suffix in [".json", ".jsonl"]:
            with open(path) as f:
                data = json.load(f)
            return AgentConfig(**data)

        # For .txt or no extension, treat as system prompt
        return AgentConfig(name=path.stem, system_prompt=path.read_text())

    @staticmethod
    def load_environment_config(path: Path | None = None) -> EnvironmentConfig:
        """Load environment configuration.

        Args:
            path: Optional path to config file. If not provided,
                  uses defaults or looks for .ccsdk/config.json

        Returns:
            EnvironmentConfig instance
        """
        if path and path.exists():
            with open(path) as f:
                data = json.load(f)
            return EnvironmentConfig(**data)

        # Check default location
        default_path = Path.home() / ".ccsdk" / "config.json"
        if default_path.exists():
            with open(default_path) as f:
                data = json.load(f)
            return EnvironmentConfig(**data)

        # Return defaults
        return EnvironmentConfig()

    @staticmethod
    def save_config(config: Union[AgentConfig, EnvironmentConfig], path: Path):
        """Save configuration to file.

        Args:
            config: Configuration to save
            path: Path to save to
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(config.model_dump(), f, indent=2, default=str)
