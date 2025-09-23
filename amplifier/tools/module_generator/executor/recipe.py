"""High-level recipe executor for module plans."""

from __future__ import annotations

from ..decomposer.specs import ensure_brick_specs
from ..parsers import parse_contract
from ..parsers import parse_impl_spec
from ..plan_models import GenContext
from ..plan_models import PlanDocument
from .run_submodule import run_brick
from .smoke import run_sample_script
from .verify import verify_plan_outputs


async def execute_plan(ctx: GenContext, plan: PlanDocument, *, dry_run: bool = False) -> None:
    module_contract = parse_contract(ctx.contract_path).raw
    module_spec = parse_impl_spec(ctx.spec_path, expected_name=ctx.module_name).raw

    if dry_run:
        for brick in plan.bricks:
            await ensure_brick_specs(ctx, brick, module_contract=module_contract, module_spec=module_spec)
        return

    max_attempts = 2
    failure_context: str | None = None

    for attempt in range(max_attempts):
        force = ctx.force or attempt > 0
        for brick in plan.bricks:
            await ensure_brick_specs(ctx, brick, module_contract=module_contract, module_spec=module_spec)
            await run_brick(ctx, brick, force=force, extra_context=failure_context)

        verify_plan_outputs(plan.bricks)
        success, output = await run_sample_script(ctx)
        if success:
            return

        failure_context = output[-4000:] if output else "Sample script failed without output."

    raise RuntimeError(
        "Sample verification script failed after retries. Last output:\n" + (failure_context or "<no output>")
    )
