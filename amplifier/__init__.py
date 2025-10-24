"""
Amplifier Tools - AI-powered productivity tools.

This package contains various tools for knowledge mining, synthesis, and content generation.
"""

__version__ = "0.1.0"

# Import and export key utilities for easier access
from amplifier.core.backend import BackendFactory
from amplifier.core.backend import get_backend
from amplifier.core.config import detect_backend
from amplifier.core.config import get_backend_config
from amplifier.core.config import get_backend_info
from amplifier.core.config import is_backend_available

__all__ = [
    "__version__",
    "get_backend",
    "BackendFactory",
    "get_backend_config",
    "detect_backend",
    "is_backend_available",
    "get_backend_info",
]
