"""
Microtask framework and CLI entrypoints.

This package provides a minimal, working microtask orchestrator with
Claude Code SDK integration (and a deterministic local fallback),
following the project's implementation and modular design philosophies.

Public contract:
- `run_code_recipe(goal: str, out_dir: str | None = None) -> dict`
- CLI entry: `amp code "<goal>"` runs plan→implement→test→refine.
"""

from .orchestrator import MicrotaskOrchestrator
from .recipes.code import run_code_recipe

__all__ = ["MicrotaskOrchestrator", "run_code_recipe"]
