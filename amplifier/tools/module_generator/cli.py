from __future__ import annotations

import asyncio
from pathlib import Path

import click

from .engine import build_context
from .engine import generate_phase
from .engine import generate_phase_with_pipeline
from .engine import plan_phase
from .engine import plan_phase_legacy


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
@click.option("--enhanced", is_flag=True, help="Use enhanced contract parsing and validation.", default=False)
@click.option("--pipeline", is_flag=True, help="Use multi-stage pipeline with checkpoints.", default=False)
@click.option("--resume", is_flag=True, help="Resume from last checkpoint if available.", default=False)
def generate_cmd(
    contract: Path,
    spec: Path,
    module_name: str | None,
    plan_only: bool,
    force: bool,
    yes: bool,
    enhanced: bool,
    pipeline: bool,
    resume: bool,
):
    """Generate a module from CONTRACT and SPEC files."""

    async def _run():
        ctx = build_context(contract, spec, module_name, force)

        # Use pipeline mode if requested
        if pipeline:
            if plan_only:
                # Just run planning phase with pipeline
                plan_text, session_id = await plan_phase(ctx)
            else:
                # Run full pipeline
                if not yes:
                    click.echo("\nUsing multi-stage pipeline with checkpoints.\n", err=True)
                    if not click.confirm("Continue with pipeline generation?", default=True):
                        return
                await generate_phase_with_pipeline(ctx)
        else:
            # Legacy mode
            plan_text, session_id = await plan_phase_legacy(ctx)
            if plan_only:
                return
            if not yes:
                click.echo("\nPlan preview above. Proceed with code generation?", err=True)
                if not click.confirm("Continue and allow writes?", default=False):
                    return
            await generate_phase(ctx, use_enhanced=enhanced)

    # No timeout - let the SDK handle timing with its max_turns setting
    asyncio.run(_run())


if __name__ == "__main__":
    cli()
