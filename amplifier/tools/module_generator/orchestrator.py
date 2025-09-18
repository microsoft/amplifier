"""Top-level orchestration for the module generator."""

from __future__ import annotations

from pathlib import Path

from .context import build_context
from .executor.recipe import execute_plan
from .plan_models import PlanDocument
from .planner.service import generate_plan
from .planner.store import load_plan
from .planner.store import plan_storage_path
from .planner.store import save_plan


async def run_plan_only(contract_path: Path, spec_path: Path, module_name: str | None, force: bool) -> PlanDocument:
    ctx = build_context(contract_path, spec_path, module_name, force)
    contract_text = ctx.contract_path.read_text(encoding="utf-8")
    spec_text = ctx.spec_path.read_text(encoding="utf-8")
    plan = await generate_plan(ctx, contract_text, spec_text)
    save_plan(plan, ctx.repo_root)
    return plan


async def run_generation(
    contract_path: Path,
    spec_path: Path,
    module_name: str | None,
    *,
    force: bool,
    refresh_plan: bool,
    dry_run: bool,
) -> PlanDocument:
    ctx = build_context(contract_path, spec_path, module_name, force)
    existing_plan = None if refresh_plan else load_plan(ctx.module_name, ctx.repo_root)

    if existing_plan is None:
        contract_text = ctx.contract_path.read_text(encoding="utf-8")
        spec_text = ctx.spec_path.read_text(encoding="utf-8")
        plan = await generate_plan(ctx, contract_text, spec_text)
        save_plan(plan, ctx.repo_root)
    else:
        plan = existing_plan

    await execute_plan(ctx, plan, dry_run=dry_run)
    return plan


def plan_path_for(module: str, repo_root: Path) -> Path:
    return plan_storage_path(module, repo_root)
