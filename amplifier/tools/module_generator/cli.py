from __future__ import annotations

import asyncio
from pathlib import Path

import click

from .orchestrator import run_generation
from .orchestrator import run_plan_only
from .plan_models import PlanDocument


@click.group()
def cli() -> None:
    """Module generator (contract-first)."""


@cli.command("generate")
@click.argument("contract", type=click.Path(path_type=Path, exists=True, readable=True))
@click.argument("spec", type=click.Path(path_type=Path, exists=True, readable=True))
@click.option(
    "--module-name",
    default=None,
    help="Override module name (snake_case). Defaults from contract filename/header.",
)
@click.option("--plan-only", is_flag=True, help="Only produce and persist the plan (no writes).")
@click.option("--force", is_flag=True, help="Remove existing brick directories when regenerating.", default=False)
@click.option("--refresh-plan", is_flag=True, help="Ignore cached plan and create a new one.")
@click.option("--dry-run", is_flag=True, help="Run decomposition/spec generation without touching code.")
def generate_cmd(
    contract: Path,
    spec: Path,
    module_name: str | None,
    plan_only: bool,
    force: bool,
    refresh_plan: bool,
    dry_run: bool,
) -> None:
    """Generate a module from CONTRACT and SPEC files."""

    async def _run() -> None:
        if plan_only:
            plan = await run_plan_only(contract, spec, module_name, force)
            _print_plan_summary(plan)
            return

        plan = await run_generation(
            contract,
            spec,
            module_name,
            force=force,
            refresh_plan=refresh_plan,
            dry_run=dry_run,
        )
        _print_plan_summary(plan)

    asyncio.run(_run())


def _print_plan_summary(plan: PlanDocument) -> None:
    click.echo("\nPlan bricks:")
    for brick in plan.bricks:
        click.echo(f" - {brick.name}: {brick.description} -> {brick.target_dir}")
    if plan.claude_session:
        click.echo(f"\nPlan session: {plan.claude_session}")


if __name__ == "__main__":
    cli()
