"""Tests for plan persistence helpers."""

from __future__ import annotations

from pathlib import Path

from amplifier.tools.module_generator.plan_models import PlanBrick
from amplifier.tools.module_generator.plan_models import PlanDocument
from amplifier.tools.module_generator.planner.store import load_plan
from amplifier.tools.module_generator.planner.store import save_plan


def test_save_and_load_plan(tmp_path: Path) -> None:
    plan = PlanDocument(
        module="demo_module",
        bricks=[
            PlanBrick(
                name="loader",
                description="Load data",
                contract_path=tmp_path / "ai_working" / "demo" / "loader.contract.md",
                spec_path=tmp_path / "ai_working" / "demo" / "loader.impl_spec.md",
                target_dir=tmp_path / "amplifier" / "demo" / "loader",
            )
        ],
    )

    path = save_plan(plan, tmp_path)
    assert path.exists()

    loaded = load_plan("demo_module", tmp_path)
    assert loaded is not None
    assert loaded.module == plan.module
    assert len(loaded.bricks) == 1
    assert loaded.bricks[0].name == "loader"
