"""
Config Module - Central configuration management for Amplifier

This module provides centralized configuration management,
starting with path configuration and resolution.
"""

from .paths import PathConfig
from .paths import paths

__all__ = ["PathConfig", "paths"]
