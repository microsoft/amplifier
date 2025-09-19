"""CLI entry point for the module generator."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

import click

from .generator import GenerationResult
from .generator import ModuleGenerator
from .models import GenerationOptions
from .models import ModuleSpecBundle
from .models import find_repo_root
from .planner import PlanResult
from .sdk import ClaudeSessionManager
from .sdk import ClaudeUnavailableError
from .spec_loader import SpecLoaderError
from .spec_loader import load_spec_bundle

logger = logging.getLogger(__name__)


@click.command()
@click.argument("contract", type=click.Path(path_type=Path))
@click.argument("spec", type=click.Path(path_type=Path))
@click.option("--plan-only", is_flag=True, help="Only run the planning phase, skipping code generation.")
@click.option("--force", is_flag=True, help="Overwrite existing output directory if it exists.")
@click.option("--yes", "--non-interactive", is_flag=True, help="Automatically answer yes to confirmation prompts.")
@click.option(
    "--disable-subagents",
    is_flag=True,
    help="Disable explicit subagent usage (still available automatically via Claude).",
)
@click.option(
    "--plan-max-turns",
    type=int,
    default=60,
    show_default=True,
    help="Maximum turns allowed during the planning session.",
)
@click.option(
    "--generate-max-turns",
    type=int,
    default=120,
    show_default=True,
    help="Maximum turns allowed during the generation session.",
)
def cli(
    contract: Path,
    spec: Path,
    plan_only: bool,
    force: bool,
    yes: bool,
    disable_subagents: bool,
    plan_max_turns: int,
    generate_max_turns: int,
) -> None:
    """Generate a module from CONTRACT and SPEC markdown files."""

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level, logging.INFO)
    logging.basicConfig(level=level, format="%(message)s")

    try:
        bundle = load_spec_bundle(contract, spec)
    except SpecLoaderError as exc:
        raise click.ClickException(str(exc)) from exc

    _confirm_execution(bundle, plan_only=plan_only, force=force, auto_yes=yes)

    repo_root = find_repo_root(contract)
    session_manager = ClaudeSessionManager(repo_root=str(repo_root))

    options = GenerationOptions(
        plan_only=plan_only,
        force=force,
        yes=yes,
        enable_subagents=not disable_subagents,
        plan_permission_mode="acceptEdits",
        generate_permission_mode="acceptEdits",
        plan_max_turns=plan_max_turns,
        generate_max_turns=generate_max_turns,
    )

    if disable_subagents:
        options.allowed_tools_plan = [tool for tool in options.allowed_tools_plan if tool != "TodoWrite"]
        options.allowed_tools_generate = [tool for tool in options.allowed_tools_generate if tool != "TodoWrite"]

    generator = ModuleGenerator(session_manager)

    try:
        result = asyncio.run(generator.run(bundle, options))
    except ClaudeUnavailableError as exc:
        raise click.ClickException(str(exc)) from exc
    except FileExistsError as exc:
        raise click.ClickException(str(exc)) from exc

    _print_summary(result.plan, result.generation)


def _confirm_execution(bundle: ModuleSpecBundle, *, plan_only: bool, force: bool, auto_yes: bool) -> None:
    """Confirm major actions with the user unless running non-interactively."""

    if auto_yes:
        return

    target_dir = bundle.output_module_path
    action = "Plan only" if plan_only else f"Plan + generate into {target_dir}"
    prompt = f"About to run module generator for {bundle.module_name}. Action: {action}. Continue?"
    if not click.confirm(prompt, default=True):
        raise click.Abort()
    if target_dir.exists() and not plan_only and not force:
        click.echo(
            f"Target directory {target_dir} already exists. Re-run with --force to overwrite or remove manually.",
            err=True,
        )
        raise click.Abort()


def _print_summary(plan: PlanResult, generation: GenerationResult | None) -> None:
    """Emit a human-readable summary after the run completes."""

    click.echo("\nPlan output saved. Summary snippet:\n")
    click.echo(_trim(plan.text, 800))

    if generation is None:
        click.echo("\nPlan-only run complete. No files were generated.")
        return

    click.echo("\nGeneration finished. Key details:")
    if generation.session_id:
        click.echo(f"- Claude session: {generation.session_id}")
    click.echo(f"- Target directory: {generation.target_dir}")
    if generation.usage:
        total_cost = generation.usage.get("total_cost_usd")
        if total_cost is not None:
            click.echo(f"- Estimated cost: ${total_cost:.4f}")
    if generation.todos:
        completed = sum(1 for todo in generation.todos if todo.get("status") == "completed")
        click.echo(f"- Todos completed: {completed}/{len(generation.todos)}")


def _trim(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."
