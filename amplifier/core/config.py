#!/usr/bin/env python3
"""
Backend Configuration Module

Centralizes configuration for Amplifier backend abstraction layer.
Supports environment variables with sensible defaults for both Claude Code and Codex backends.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class BackendConfig(BaseSettings):
    """Configuration for Amplifier backend abstraction layer with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Backend selection
    amplifier_backend: str = Field(
        default="claude",
        description="AI backend to use: 'claude' or 'codex'. Default: claude (backward compatibility)",
    )

    amplifier_backend_auto_detect: bool = Field(
        default=True,
        description="Auto-detect backend if AMPLIFIER_BACKEND not set. Checks for .claude/ or .codex/ directories and CLI availability. Default: true",
    )

    # CLI paths (optional, auto-detected if not set)
    claude_cli_path: str | None = Field(
        default=None,
        description="Path to Claude CLI executable. Auto-detected if not set. Example: /usr/local/bin/claude",
    )

    codex_cli_path: str | None = Field(
        default=None,
        description="Path to Codex CLI executable. Auto-detected if not set. Example: /usr/local/bin/codex",
    )

    # Codex-specific configuration
    codex_profile: str = Field(
        default="development",
        description="Codex profile to use: 'development', 'ci', or 'review'. Default: development",
    )

    # Memory system (shared between backends)
    memory_system_enabled: bool = Field(
        default=True,
        description="Enable memory extraction system. Works with both Claude Code hooks and Codex MCP servers. Default: true",
    )

    @field_validator("amplifier_backend")
    @classmethod
    def validate_backend(cls, v: str) -> str:
        """Validate that backend is either 'claude' or 'codex'."""
        if v not in ["claude", "codex"]:
            raise ValueError(f"Invalid backend '{v}'. Must be 'claude' or 'codex'")
        return v

    @field_validator("codex_profile")
    @classmethod
    def validate_codex_profile(cls, v: str) -> str:
        """Validate that codex profile is valid."""
        valid_profiles = ["development", "ci", "review"]
        if v not in valid_profiles:
            raise ValueError(f"Invalid codex profile '{v}'. Must be one of: {', '.join(valid_profiles)}")
        return v

    def get_backend_cli_path(self, backend: str) -> str | None:
        """Get CLI path for specified backend.

        Args:
            backend: Backend name ("claude" or "codex")

        Returns:
            CLI path if configured, None otherwise
        """
        if backend == "claude":
            return self.claude_cli_path
        if backend == "codex":
            return self.codex_cli_path
        return None


# Global configuration instance
_backend_config: BackendConfig | None = None


def get_backend_config() -> BackendConfig:
    """Get or create the backend configuration singleton."""
    global _backend_config
    if _backend_config is None:
        _backend_config = BackendConfig()
    return _backend_config


def reload_backend_config() -> BackendConfig:
    """Reload backend configuration from environment variables."""
    global _backend_config
    _backend_config = BackendConfig()
    return _backend_config


def detect_backend() -> str:
    """Auto-detect available backend based on directories and CLI availability.

    Returns:
        Backend name: "claude" or "codex"

    Raises:
        RuntimeError: If no backend is available
    """
    # Check for Claude Code
    if Path(".claude").exists() and is_backend_available("claude"):
        return "claude"

    # Check for Codex
    if Path(".codex").exists() and is_backend_available("codex"):
        return "codex"

    raise RuntimeError(
        "No backend available. Ensure either:\n"
        "1. Claude Code is installed and .claude/ directory exists, or\n"
        "2. Codex is installed and .codex/ directory exists"
    )


def is_backend_available(backend: str) -> bool:
    """Check if specified backend is available and configured.

    Args:
        backend: Backend name ("claude" or "codex")

    Returns:
        True if backend is available, False otherwise
    """
    config = get_backend_config()

    if backend == "claude":
        # Check if .claude directory exists
        if not Path(".claude").exists():
            return False

        # Check CLI availability
        cli_path = config.get_backend_cli_path("claude") or "claude"
        return shutil.which(cli_path) is not None

    if backend == "codex":
        # Check if .codex directory exists
        if not Path(".codex").exists():
            return False

        # Check CLI availability
        cli_path = config.get_backend_cli_path("codex") or "codex"
        return shutil.which(cli_path) is not None

    return False


def get_backend_info(backend: str) -> dict[str, Any]:
    """Get information about specified backend for debugging and diagnostics.

    Args:
        backend: Backend name ("claude" or "codex")

    Returns:
        Dictionary with backend information
    """
    config = get_backend_config()
    info = {
        "backend": backend,
        "available": is_backend_available(backend),
        "config_directory": f".{backend}",
        "cli_path": config.get_backend_cli_path(backend),
    }

    # Try to get CLI version if available
    cli_path = info["cli_path"] or backend
    if shutil.which(cli_path):
        try:
            result = subprocess.run([cli_path, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                info["version"] = result.stdout.strip()
            else:
                info["version"] = "unknown"
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            info["version"] = "unknown"
    else:
        info["version"] = None

    # Backend-specific information
    if backend == "claude":
        info["hook_directory"] = ".claude/tools"
        info["agent_directory"] = ".claude/agents"
    elif backend == "codex":
        info["mcp_directory"] = ".codex/mcp_servers"
        info["agent_directory"] = ".codex/agents"
        info["profile"] = config.codex_profile

    return info


# Environment Variables Documentation:
"""
AMPLIFIER_BACKEND:
    Choose which AI backend to use: "claude" or "codex"
    - "claude": Use Claude Code (VS Code extension) with native hooks
    - "codex": Use Codex CLI with MCP servers
    Default: claude (for backward compatibility)
    Example: export AMPLIFIER_BACKEND=codex

AMPLIFIER_BACKEND_AUTO_DETECT:
    Auto-detect backend if AMPLIFIER_BACKEND not set
    Checks for .claude/ or .codex/ directories and CLI availability
    Default: true
    Example: export AMPLIFIER_BACKEND_AUTO_DETECT=false

CLAUDE_CLI_PATH:
    Path to Claude CLI executable (optional, auto-detected if not set)
    Only needed if Claude CLI is not in PATH
    Example: export CLAUDE_CLI_PATH=/usr/local/bin/claude

CODEX_CLI_PATH:
    Path to Codex CLI executable (optional, auto-detected if not set)
    Only needed if Codex CLI is not in PATH
    Example: export CODEX_CLI_PATH=/usr/local/bin/codex

CODEX_PROFILE:
    Codex profile to use when starting Codex
    Options: development, ci, review
    Default: development
    Example: export CODEX_PROFILE=ci

MEMORY_SYSTEM_ENABLED:
    Enable/disable memory extraction system
    Works with both Claude Code hooks and Codex MCP servers
    Default: true
    Example: export MEMORY_SYSTEM_ENABLED=false
"""
