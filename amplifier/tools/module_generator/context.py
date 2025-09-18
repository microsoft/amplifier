"""Context dataclass for module generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class GenContext:
    """Context for module generation."""

    repo_root: Path
    tool_dir: Path
    contract_path: Path
    spec_path: Path
    module_name: str
    target_rel: str  # e.g., "amplifier/idea_synthesizer"
    force: bool = False
