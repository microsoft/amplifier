"""Alias package exposing modules from the `.codex` directory."""

from pathlib import Path

# Make this package resolve modules from the hidden .codex directory.
__path__ = [str(Path(__file__).resolve().parent.parent / ".codex")]
