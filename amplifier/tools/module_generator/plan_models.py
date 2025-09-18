"""Dataclasses describing planner outputs and execution context."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class GenContext:
    """Execution context resolved from CLI arguments."""

    repo_root: Path
    tool_dir: Path
    contract_path: Path
    spec_path: Path
    module_name: str
    target_rel: Path
    force: bool = False


@dataclass
class PlanBrick:
    """Represents a focused unit of work (brick) inside a module plan."""

    name: str
    description: str
    contract_path: Path
    spec_path: Path
    target_dir: Path
    type: str = "python_module"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "contract_path": str(self.contract_path),
            "spec_path": str(self.spec_path),
            "target_dir": str(self.target_dir),
            "type": self.type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanBrick:
        missing = {
            key for key in {"name", "description", "contract_path", "spec_path", "target_dir"} if key not in data
        }
        if missing:
            raise ValueError(f"Plan brick missing fields: {sorted(missing)}")
        return cls(
            name=data["name"],
            description=data["description"],
            contract_path=Path(data["contract_path"]),
            spec_path=Path(data["spec_path"]),
            target_dir=Path(data["target_dir"]),
            type=data.get("type", "python_module"),
        )


@dataclass
class PlanDocument:
    """A complete module generation plan persisted to disk."""

    module: str
    bricks: list[PlanBrick] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    claude_session: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "created_at": self.created_at.isoformat(),
            "claude_session": self.claude_session,
            "bricks": [brick.to_dict() for brick in self.bricks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlanDocument:
        if "module" not in data:
            raise ValueError("Plan document missing 'module'")
        created_raw = data.get("created_at")
        created_at = datetime.fromisoformat(created_raw) if created_raw else datetime.now(UTC)
        bricks = [PlanBrick.from_dict(item) for item in data.get("bricks", [])]
        return cls(
            module=data["module"],
            bricks=bricks,
            created_at=created_at,
            claude_session=data.get("claude_session"),
        )

    def ensure_minimum(self) -> None:
        if not self.bricks:
            raise ValueError("Plan document must contain at least one brick")

    def iter_bricks(self) -> Iterable[PlanBrick]:
        return iter(self.bricks)
