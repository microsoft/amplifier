"""
Pytest configuration and shared fixtures for tests.

This file provides common fixtures and configuration for all tests,
following the modular design philosophy.
"""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
