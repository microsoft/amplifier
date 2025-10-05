"""
Configuration management for Amplifier CLI.

Handles loading mode manifests, parsing module lists, and managing
default configurations.
"""

import json
from pathlib import Path
from typing import Any

import yaml


class ConfigurationError(Exception):
    """Raised when there's an error in configuration."""

    pass


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file."""
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in {path}: {e}")
    except FileNotFoundError:
        raise ConfigurationError(f"Configuration file not found: {path}")
    except Exception as e:
        raise ConfigurationError(f"Error loading {path}: {e}")


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file."""
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in {path}: {e}")
    except FileNotFoundError:
        raise ConfigurationError(f"Configuration file not found: {path}")
    except Exception as e:
        raise ConfigurationError(f"Error loading {path}: {e}")


def load_mode_manifest(mode_name: str, config_dir: Path | None = None) -> dict[str, Any]:
    """
    Load a mode manifest by name.

    Args:
        mode_name: Name of the mode to load
        config_dir: Directory containing mode configurations (defaults to ~/.amplifier/modes)

    Returns:
        Dictionary containing the mode configuration

    Raises:
        ConfigurationError: If the manifest cannot be loaded
    """
    if config_dir is None:
        config_dir = Path.home() / ".amplifier" / "modes"

    # Try loading with different extensions
    for ext in [".yaml", ".yml", ".json"]:
        manifest_path = config_dir / f"{mode_name}{ext}"
        if manifest_path.exists():
            if ext == ".json":
                return load_json(manifest_path)
            return load_yaml(manifest_path)

    # If no mode file found, check if it's a built-in mode
    builtin_modes = get_builtin_modes()
    if mode_name in builtin_modes:
        return builtin_modes[mode_name]

    raise ConfigurationError(f"Mode manifest not found: {mode_name}")


def get_builtin_modes() -> dict[str, dict[str, Any]]:
    """
    Get built-in mode configurations.

    Returns:
        Dictionary of built-in modes
    """
    return {
        "default": {
            "name": "default",
            "description": "Default mode with basic functionality",
            "modules": [],
        },
        "development": {
            "name": "development",
            "description": "Development mode with coding tools",
            "modules": [
                "amplifier_mod_llm_openai",
                "amplifier_mod_tool_ultra_think",
                "amplifier_mod_agent_registry",
            ],
        },
        "writing": {
            "name": "writing",
            "description": "Writing mode with content creation tools",
            "modules": [
                "amplifier_mod_llm_claude",
                "amplifier_mod_tool_blog_generator",
                "amplifier_mod_philosophy",
            ],
        },
    }


def list_available_modes(config_dir: Path | None = None) -> list[str]:
    """
    List all available modes (both built-in and user-defined).

    Args:
        config_dir: Directory containing mode configurations

    Returns:
        List of available mode names
    """
    modes = set(get_builtin_modes().keys())

    if config_dir is None:
        config_dir = Path.home() / ".amplifier" / "modes"

    if config_dir.exists() and config_dir.is_dir():
        for file in config_dir.iterdir():
            if file.suffix in [".yaml", ".yml", ".json"]:
                modes.add(file.stem)

    return sorted(list(modes))


def parse_module_list(modules: list[str]) -> list[str]:
    """
    Parse and validate a list of module names.

    Args:
        modules: List of module names to parse

    Returns:
        Validated list of module names

    Raises:
        ConfigurationError: If module names are invalid
    """
    validated = []
    for module in modules:
        # Basic validation - module names should be valid Python module names
        if not module or not all(part.isidentifier() for part in module.split(".")):
            raise ConfigurationError(f"Invalid module name: {module}")
        validated.append(module)
    return validated


def get_default_config() -> dict[str, Any]:
    """
    Get default configuration settings.

    Returns:
        Dictionary with default configuration
    """
    return {
        "log_level": "INFO",
        "config_dir": str(Path.home() / ".amplifier"),
        "modes_dir": str(Path.home() / ".amplifier" / "modes"),
        "plugins_dir": str(Path.home() / ".amplifier" / "plugins"),
        "data_dir": str(Path.home() / ".amplifier" / "data"),
    }


def load_user_config() -> dict[str, Any]:
    """
    Load user configuration from ~/.amplifier/config.yaml.

    Returns:
        Dictionary with user configuration merged with defaults
    """
    config = get_default_config()
    user_config_path = Path.home() / ".amplifier" / "config.yaml"

    if user_config_path.exists():
        try:
            user_config = load_yaml(user_config_path)
            config.update(user_config)
        except ConfigurationError:
            # If user config is invalid, continue with defaults
            pass

    return config


def init_config_dirs() -> None:
    """Initialize configuration directories if they don't exist."""
    config = get_default_config()

    for key in ["config_dir", "modes_dir", "plugins_dir", "data_dir"]:
        dir_path = Path(config[key])
        dir_path.mkdir(parents=True, exist_ok=True)


def save_mode_manifest(mode_name: str, manifest: dict[str, Any], config_dir: Path | None = None) -> None:
    """
    Save a mode manifest to disk.

    Args:
        mode_name: Name of the mode
        manifest: Mode configuration to save
        config_dir: Directory to save the manifest in

    Raises:
        ConfigurationError: If the manifest cannot be saved
    """
    if config_dir is None:
        config_dir = Path.home() / ".amplifier" / "modes"

    config_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = config_dir / f"{mode_name}.yaml"

    try:
        with open(manifest_path, "w") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        raise ConfigurationError(f"Failed to save mode manifest: {e}")
