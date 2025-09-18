"""High-level recipe executor for module plans."""

from __future__ import annotations

from ..decomposer.specs import ensure_brick_specs
from ..parsers import parse_contract
from ..parsers import parse_impl_spec
from ..plan_models import GenContext
from ..plan_models import PlanDocument
from .run_submodule import run_brick
from .verify import verify_plan_outputs


async def execute_plan(ctx: GenContext, plan: PlanDocument, *, dry_run: bool = False) -> None:
    module_contract = parse_contract(ctx.contract_path).raw
    module_spec = parse_impl_spec(ctx.spec_path, expected_name=ctx.module_name).raw

    for brick in plan.bricks:
        await ensure_brick_specs(ctx, brick, module_contract=module_contract, module_spec=module_spec)
        if dry_run:
            continue
        await run_brick(ctx, brick, force=ctx.force)

    if not dry_run:
        verify_plan_outputs(plan.bricks)
