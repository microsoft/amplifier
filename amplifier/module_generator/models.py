"""Data models for the module generator CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic import Field

PermissionMode = Literal["default", "acceptEdits", "plan", "bypassPermissions"]


class ModuleSpecBundle(BaseModel):
    """Container for the contract/spec artifacts used to drive generation."""

    module_name: str = Field(..., description="Human-readable module name extracted from the contract heading")
    module_slug: str = Field(..., description="Filesystem-safe slug used for package directories")
    contract_path: Path = Field(..., description="Path to the contract markdown file")
    spec_path: Path = Field(..., description="Path to the implementation spec markdown file")
    contract_text: str = Field(..., description="Raw contract markdown content")
    spec_text: str = Field(..., description="Raw implementation spec markdown content")

    @property
    def output_module_path(self) -> Path:
        """Default location for generated module code within the repository."""

        repo_root = find_repo_root(self.contract_path)
        return repo_root / "amplifier" / self.module_slug

    @property
    def artifact_dir(self) -> Path:
        """Directory under ai_working for storing generator runs for this module."""

        repo_root = find_repo_root(self.contract_path)
        return repo_root / "ai_working" / "module_generator_runs" / self.module_slug


class GenerationOptions(BaseModel):
    """CLI switches and runtime options passed to the generator."""

    plan_only: bool = False
    force: bool = False
    yes: bool = False
    enable_subagents: bool = True
    plan_permission_mode: PermissionMode = Field("acceptEdits", description="Permission mode for planning session")
    generate_permission_mode: PermissionMode = Field(
        "acceptEdits", description="Permission mode for generation session"
    )
    allowed_tools_plan: list[str] = Field(
        default_factory=lambda: ["Read", "Grep", "Glob", "TodoWrite"],
        description="Tools permitted during the planning pass",
    )
    allowed_tools_generate: list[str] = Field(
        default_factory=lambda: ["Read", "Write", "Edit", "TodoWrite", "Bash"],
        description="Tools permitted during the generation pass",
    )
    plan_max_turns: int = Field(60, description="Maximum turns allowed during planning sessions")
    generate_max_turns: int = Field(120, description="Maximum turns allowed during generation sessions")


class ClaudeSessionResult(BaseModel):
    """Structured representation of a Claude session run via the SDK."""

    text: str = Field(..., description="Concatenated textual output from assistant messages")
    todos: list[dict] = Field(default_factory=list, description="TodoWrite payloads observed during the session")
    usage: dict | None = Field(default=None, description="Usage metrics reported by Claude")
    session_id: str | None = Field(default=None, description="Session UUID returned by the SDK, if available")


def find_repo_root(path: Path) -> Path:
    """Walk up the filesystem to find the repository root containing pyproject.toml."""

    current = path.resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("Unable to locate repository root (pyproject.toml not found)")
