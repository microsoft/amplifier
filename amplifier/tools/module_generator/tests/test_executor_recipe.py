"""Tests for the plan execution recipe."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from pathlib import Path

import pytest

from amplifier.tools.module_generator.executor.recipe import execute_plan
from amplifier.tools.module_generator.plan_models import GenContext
from amplifier.tools.module_generator.plan_models import PlanBrick
from amplifier.tools.module_generator.plan_models import PlanDocument


@pytest.mark.asyncio
async def test_execute_plan_creates_brick(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / "Makefile").write_text("# dummy")

    contract_path = repo_root / "module.contract.md"
    contract_path.write_text("# Contract: demo_module\n## Purpose\nDemo\n", encoding="utf-8")

    spec_path = repo_root / "module.impl_spec.md"
    spec_path.write_text("# Implementation Spec: demo_module\n## Design Overview\nDemo\n", encoding="utf-8")

    brick_contract = repo_root / "ai_working" / "demo_module" / "loader.contract.md"
    brick_spec = repo_root / "ai_working" / "demo_module" / "loader.impl_spec.md"
    brick_contract.parent.mkdir(parents=True, exist_ok=True)
    brick_contract.write_text("# Contract: loader", encoding="utf-8")
    brick_spec.write_text("# Implementation Spec: loader", encoding="utf-8")

    target_dir = repo_root / "amplifier" / "demo_module" / "loader"

    ctx = GenContext(
        repo_root=repo_root,
        tool_dir=repo_root,
        contract_path=contract_path,
        spec_path=spec_path,
        module_name="demo_module",
        target_rel=repo_root / "amplifier" / "demo_module",
        force=True,
    )

    plan = PlanDocument(
        module="demo_module",
        bricks=[
            PlanBrick(
                name="loader",
                description="Load summaries",
                contract_path=brick_contract,
                spec_path=brick_spec,
                target_dir=target_dir,
            )
        ],
        created_at=datetime.now(UTC),
    )

    async def fake_generate_from_specs(**kwargs):
        module_dir_rel = kwargs["module_dir_rel"]
        cwd = Path(kwargs["cwd"])
        out_dir = cwd / module_dir_rel
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "__init__.py").write_text("# generated", encoding="utf-8")
        return ("session", 0.0, 0)

    monkeypatch.setattr(
        "amplifier.tools.module_generator.executor.run_submodule.generate_from_specs",
        fake_generate_from_specs,
    )

    await execute_plan(ctx, plan, dry_run=False)

    assert (target_dir / "__init__.py").exists()
