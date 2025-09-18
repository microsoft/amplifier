"""Persistence helpers for plan documents."""

from __future__ import annotations

import json
from pathlib import Path

from ..plan_models import PlanDocument


def plan_storage_path(module: str, repo_root: Path) -> Path:
    return repo_root / "ai_working" / "module_generator" / "plans" / f"{module}.plan.json"


def save_plan(plan: PlanDocument, repo_root: Path) -> Path:
    path = plan_storage_path(plan.module, repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(plan.to_dict(), f, indent=2)
    return path


def load_plan(module: str, repo_root: Path) -> PlanDocument | None:
    path = plan_storage_path(module, repo_root)
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return PlanDocument.from_dict(data)
