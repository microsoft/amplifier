from __future__ import annotations

import asyncio
from pathlib import Path

import click

from .engine import build_context
from .engine import generate_phase
from .engine import plan_phase


@click.group()
def cli():
    """Module generator (contract-first)."""
    pass


@cli.command("generate")
@click.argument("contract", type=click.Path(path_type=Path, exists=True, readable=True))
@click.argument("spec", type=click.Path(path_type=Path, exists=True, readable=True))
@click.option(
    "--module-name", default=None, help="Override module name (snake_case). Defaults from contract filename/header."
)
@click.option("--plan-only", is_flag=True, help="Only produce and print the plan (read-only). No files are written.")
@click.option("--force", is_flag=True, help="Remove existing target directory if present (regenerate).", default=False)
@click.option("--yes", "-y", is_flag=True, help="Do not prompt to confirm generation.")
def generate_cmd(contract: Path, spec: Path, module_name: str | None, plan_only: bool, force: bool, yes: bool):
    """Generate a module from CONTRACT and SPEC files."""

    async def _run():
        ctx = build_context(contract, spec, module_name, force)
        plan_text, session_id = await plan_phase(ctx)
        if plan_only:
            return
        if not yes:
            click.echo("\nPlan preview above. Proceed with code generation?", err=True)
            if not click.confirm("Continue and allow writes?", default=False):
                return
        await generate_phase(ctx)

    # No timeout - let the SDK handle timing with its max_turns setting
    asyncio.run(_run())


if __name__ == "__main__":
    cli()
