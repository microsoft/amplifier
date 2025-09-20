"""
CLI entrypoints for the microtask engine.

Commands:
- `amp code "<goal>"` runs the code recipe with incremental persistence
- `amp list` lists recent runs
- `amp show <job_id>` prints run summary JSON
"""

from __future__ import annotations

import json
from pathlib import Path

import click

from .llm import is_sdk_available
from .models import MicrotaskError
from .recipes.code import run_code_recipe
from .recipes.ideas import run_ideas_recipe
from .recipes.summarize import run_summarize_recipe
from .store import DEFAULT_BASE
from .store import JobStore


@click.group()
def cli() -> None:
    """Amplifier Microtask CLI."""


@cli.command()
@click.argument("goal", nargs=-1)
@click.option("--out-dir", type=click.Path(file_okay=False, dir_okay=True), default=None, help="Where to store runs")
def code(goal: tuple[str, ...], out_dir: str | None) -> None:
    """Run plan→implement→test→refine for a coding goal."""
    goal_text = " ".join(goal).strip()
    if not goal_text:
        raise click.ClickException("Provide a goal, e.g., amp code 'add two numbers'")
    if not is_sdk_available():
        raise click.ClickException(
            "Claude Code SDK/CLI not available. Install with: 'pip install claude-code-sdk' and 'npm i -g @anthropic-ai/claude-code'."
        )
    try:
        result = run_code_recipe(goal_text, out_dir)
    except MicrotaskError as e:
        raise click.ClickException(str(e))
    click.echo(json.dumps(result, indent=2))


@cli.group()
def tool() -> None:
    """Generate and manage standalone tools."""


@tool.command("create")
@click.argument("name")
@click.option("--desc", required=True, help="Short description of the tool to generate")
@click.option("--template", type=click.Choice(["ideas", "summarize"], case_sensitive=False), default=None)
def tool_create(name: str, desc: str, template: str | None) -> None:
    """Create a new tool under cli_tools/<name> using Claude Code SDK."""
    if not is_sdk_available():
        raise click.ClickException(
            "Claude Code SDK/CLI not available. Install with: 'pip install claude-code-sdk' and 'npm i -g @anthropic-ai/claude-code'."
        )

    # Inline progress printing and surface job id early
    def _progress(evt: str, step: str, data: dict | None) -> None:
        if evt == "job" and data:
            click.echo(f"job_id: {data.get('job_id')}  artifacts: {data.get('artifacts_dir')}")
            return
        msg = {
            "start": f"▶ {step}...",
            "success": f"✔ {step}",
            "fail": f"✖ {step} failed",
        }.get(evt, f"• {step}")
        click.echo(msg)

    try:
        # Proxy run to recipe through progress-aware path by calling the recipe directly
        from .orchestrator import MicrotaskOrchestrator
        from .recipes.tool import step_generate_tool  # type: ignore
        from .recipes.tool import step_plan_tool  # type: ignore

        orch = MicrotaskOrchestrator()
        steps = [
            ("plan_tool", lambda llm, art: step_plan_tool(llm, art, name, desc, template)),
            ("generate_tool", lambda llm, art: step_generate_tool(llm, art, name, desc, template)),
        ]
        result_obj = orch.run("tool", steps, meta={"name": name, "desc": desc}, fail_fast=True, on_event=_progress)
        result = result_obj.model_dump()
    except MicrotaskError as e:
        raise click.ClickException(str(e))
    click.echo(json.dumps(result, indent=2))


@tool.command("install")
@click.argument("name")
def tool_install(name: str) -> None:
    """Install cli_tools/<name> into the current virtualenv (editable)."""
    base = Path("cli_tools") / name
    pyproject = base / "pyproject.toml"
    if not pyproject.exists():
        raise click.ClickException(f"No tool found at {base}. Did you run 'amp tool create {name}'?")
    import subprocess

    cmd = ["uv", "pip", "install", "-e", str(base)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise click.ClickException(f"Install failed:\n{proc.stdout}\n{proc.stderr}")
    click.echo(f"Installed {name} into current environment.")


@cli.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True, dir_okay=False))
@click.option("--purpose", default=None, help="Custom summarization goal")
def summarize(files: tuple[str, ...], purpose: str | None) -> None:
    """Run metacognitive summarization (plan→outline→extract→synthesize→refine)."""
    if not files:
        raise click.ClickException("Provide at least one file")
    if not is_sdk_available():
        raise click.ClickException(
            "Claude Code SDK/CLI not available. Install with: 'pip install claude-code-sdk' and 'npm i -g @anthropic-ai/claude-code'."
        )

    def _progress(evt: str, step: str, data: dict | None) -> None:
        if evt == "job" and data:
            click.echo(f"job_id: {data.get('job_id')}  artifacts: {data.get('artifacts_dir')}")
            return
        msg = {
            "start": f"▶ {step}...",
            "success": f"✔ {step} done",
            "fail": f"✖ {step} failed",
        }.get(evt, f"• {step}")
        click.echo(msg)

    try:
        result = run_summarize_recipe(list(files), progress=_progress)
    except MicrotaskError as e:
        raise click.ClickException(str(e))
    click.echo(json.dumps(result, indent=2))


@cli.command()
@click.option("--base", type=click.Path(file_okay=False, dir_okay=True), default=str(DEFAULT_BASE))
def list(base: str) -> None:  # type: ignore[override]
    """List runs in the job store."""
    base_path = Path(base)
    if not base_path.exists():
        click.echo("[]")
        return
    runs = []
    for child in sorted(base_path.iterdir()):
        state = child / "results.json"
        if state.exists():
            runs.append(json.loads(state.read_text()))
    click.echo(
        json.dumps(
            [{"job_id": r.get("job_id"), "recipe": r.get("recipe"), "updated_at": r.get("updated_at")} for r in runs],
            indent=2,
        )
    )


@cli.command()
@click.argument("job_id")
@click.option("--base", type=click.Path(file_okay=False, dir_okay=True), default=str(DEFAULT_BASE))
def show(job_id: str, base: str) -> None:
    """Show a run summary JSON."""
    store = JobStore(Path(base))
    try:
        state = store.load(job_id)
    except FileNotFoundError:
        raise click.ClickException(f"No run found: {job_id}")
    click.echo(state.model_dump_json(indent=2))


@cli.group()
def ideas() -> None:
    """Batch ideation pipeline."""


@ideas.command("run")
@click.option(
    "--src", required=True, type=click.Path(exists=True, file_okay=False), help="Source directory of .md files"
)
@click.option("--limit", default=5, show_default=True, type=int, help="How many files to process")
@click.option(
    "--work", default=None, type=click.Path(file_okay=False), help="Working directory for incremental outputs"
)
def ideas_run(src: str, limit: int, work: str | None) -> None:
    if not is_sdk_available():
        raise click.ClickException(
            "Claude Code SDK/CLI not available. Install with: 'pip install claude-code-sdk' and 'npm i -g @anthropic-ai/claude-code'."
        )

    def _progress(evt: str, step: str, data: dict | None) -> None:
        if evt == "job" and data:
            click.echo(f"job_id: {data.get('job_id')}  artifacts: {data.get('artifacts_dir')}")
            return
        msg = {"start": f"▶ {step}...", "success": f"✔ {step}", "fail": f"✖ {step} failed"}.get(evt, f"• {step}")
        click.echo(msg)

    result = run_ideas_recipe(src, limit=limit, work_dir=work, progress=_progress)
    click.echo(json.dumps(result, indent=2))


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
