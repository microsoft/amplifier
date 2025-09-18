"""Utilities for building the generation context."""

from __future__ import annotations

from pathlib import Path

from .plan_models import GenContext


def find_repo_root(start: Path | None = None) -> Path:
    """Walk upwards from *start* to locate the repository root."""
    current = start or Path.cwd()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() or (candidate / "Makefile").exists():
            return candidate
    return current


def derive_module_name(contract_path: Path) -> str:
    """Derive module name from filename (snake_case)."""
    stem = contract_path.stem
    # Strip suffix like .contract
    if "." in stem:
        stem = stem.split(".")[0]
    return stem.lower().replace("-", "_")


def build_context(contract_path: Path, spec_path: Path, module_name: str | None, force: bool) -> GenContext:
    repo_root = find_repo_root()
    tool_dir = Path(__file__).resolve().parent
    safe_name = derive_module_name(contract_path) if not module_name else module_name.lower().replace("-", "_")
    target_rel = Path("amplifier") / safe_name
    return GenContext(
        repo_root=repo_root,
        tool_dir=tool_dir,
        contract_path=contract_path,
        spec_path=spec_path,
        module_name=safe_name,
        target_rel=target_rel,
        force=force,
    )
