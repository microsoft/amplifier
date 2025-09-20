"""
Config command for Amplifier CLI v3.

This command manages configuration settings stored in .amplifier/config.yaml.

Contract:
    - Commands: get, set, list
    - Config file: .amplifier/config.yaml
    - Default settings: default_source, auto_update_check, github_repo
"""

import sys
from pathlib import Path
from typing import Any

import click
import yaml

from amplifier.cli.core import get_amplifier_dir
from amplifier.cli.core.decorators import handle_errors
from amplifier.cli.core.decorators import log_command
from amplifier.cli.core.output import get_output_manager

# Default configuration values
DEFAULT_CONFIG = {
    "default_source": "github",
    "auto_update_check": True,
    "github_repo": "microsoft/amplifier",
}


def get_config_path() -> Path:
    """Get the path to the config file.

    Returns:
        Path to .amplifier/config.yaml
    """
    return get_amplifier_dir() / "config.yaml"


def load_config() -> dict[str, Any]:
    """Load configuration from file or return defaults.

    Returns:
        Dictionary of configuration values
    """
    config_path = get_config_path()

    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}

    # Merge with defaults (defaults for missing keys)
    for key, value in DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = value

    return config


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file.

    Args:
        config: Dictionary of configuration values
    """
    config_path = get_config_path()

    # Ensure .amplifier directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=True)


@click.group()
@click.pass_context
def cmd(ctx: click.Context) -> None:
    """Manage Amplifier configuration settings."""
    pass


@cmd.command(name="get")
@click.argument("key")
@handle_errors()
@log_command("config get")
@click.pass_context
def get_config_value(ctx: click.Context, key: str) -> None:
    """Get a configuration value.

    \b
    Available keys:
        default_source      - Default source for installations (github/local)
        auto_update_check   - Whether to check for updates automatically
        github_repo        - GitHub repository for resources

    Example:
        amplifier config get default_source
    """
    output = ctx.obj.get("output", get_output_manager())

    config = load_config()

    if key not in config:
        output.error(f"Unknown configuration key: {key}")
        output.info(f"Available keys: {', '.join(sorted(config.keys()))}")
        sys.exit(1)

    value = config[key]

    # In quiet mode, just print the value
    if ctx.obj.get("quiet"):
        click.echo(value)
    else:
        output.success(f"{key}: {value}")


@cmd.command(name="set")
@click.argument("key")
@click.argument("value")
@handle_errors()
@log_command("config set")
@click.pass_context
def set_config_value(ctx: click.Context, key: str, value: str) -> None:
    """Set a configuration value.

    \b
    Available keys:
        default_source      - Default source for installations (github/local)
        auto_update_check   - Whether to check for updates automatically (true/false)
        github_repo        - GitHub repository for resources (owner/repo)

    Example:
        amplifier config set default_source local
        amplifier config set auto_update_check false
        amplifier config set github_repo microsoft/amplifier
    """
    output = ctx.obj.get("output", get_output_manager())

    config = load_config()

    # Use a variable with Any type for the converted value
    converted_value: Any = value

    # Validate and convert value based on key
    if key == "auto_update_check":
        # Convert string to boolean
        if value.lower() in ("true", "yes", "1", "on"):
            converted_value = True
        elif value.lower() in ("false", "no", "0", "off"):
            converted_value = False
        else:
            output.error(f"Invalid boolean value: {value}")
            output.info("Use 'true' or 'false' for auto_update_check")
            sys.exit(1)
    elif key == "default_source":
        # Validate source
        if value not in ("github", "local"):
            output.error(f"Invalid source: {value}")
            output.info("Valid sources: github, local")
            sys.exit(1)
    elif key == "github_repo":
        # Basic validation for repo format
        if "/" not in value:
            output.error(f"Invalid repository format: {value}")
            output.info("Use format: owner/repo (e.g., microsoft/amplifier)")
            sys.exit(1)
    elif key not in DEFAULT_CONFIG:
        output.warning(f"Setting custom configuration key: {key}")

    old_value = config.get(key, "not set")
    config[key] = converted_value
    save_config(config)

    if not ctx.obj.get("quiet"):
        if old_value == "not set":
            output.success(f"Set {key} = {converted_value}")
        else:
            output.success(f"Updated {key}: {old_value} → {converted_value}")


@cmd.command(name="list")
@handle_errors()
@log_command("config list")
@click.pass_context
def list_config(ctx: click.Context) -> None:
    """List all configuration settings.

    Shows all configuration keys and their current values.

    Example:
        amplifier config list
    """
    output = ctx.obj.get("output", get_output_manager())

    config = load_config()

    if ctx.obj.get("quiet"):
        # In quiet mode, simple key=value format
        for key, value in sorted(config.items()):
            click.echo(f"{key}={value}")
    else:
        output.info("📋 Configuration Settings")
        output.info("")

        # Find the longest key for alignment
        max_key_len = max(len(key) for key in config)

        for key, value in sorted(config.items()):
            # Highlight non-default values
            is_default = key in DEFAULT_CONFIG and DEFAULT_CONFIG[key] == value

            if is_default:
                output.info(f"  {key:<{max_key_len}} : {value}")
            else:
                # Show modified values in green
                output.success(f"  {key:<{max_key_len}} : {value} (modified)")

        output.info("")
        output.info(f"Config file: {get_config_path()}")
