#!/usr/bin/env python3
"""
Amplifier CLI - Unified command-line interface for all Amplifier tools.

This provides a single entry point for all Amplifier functionality, replacing
scattered make targets and individual scripts with a consistent interface.
"""

import shutil
import sys
from pathlib import Path

import click
from click import Context


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version information")
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.pass_context
def cli(ctx: Context, version: bool, debug: bool) -> None:
    """Amplifier - AI-powered knowledge synthesis toolkit.

    A unified CLI for extracting, synthesizing, and managing knowledge from documents.
    """
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug

    if version:
        click.echo("Amplifier v0.2.0")
        sys.exit(0)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.option("--force", is_flag=True, help="Force reprocessing of all items")
@click.option("--since", help="Process only items modified since this date")
@click.option("--concurrency", type=int, default=1, help="Number of parallel workers")
@click.option("--rate-limit", type=int, help="Max requests per minute")
@click.argument("path", type=click.Path(exists=True), required=False)
@click.pass_context
def run(
    ctx: Context, force: bool, since: str | None, concurrency: int, rate_limit: int | None, path: str | None
) -> None:
    """Run the full knowledge extraction and synthesis pipeline."""
    click.echo("Running full pipeline...")

    # Import here to avoid circular dependencies

    # Configure from options
    # TODO: Use config to pass to run_mining and run_synthesis
    # config = {
    #     "force": force,
    #     "since": since,
    #     "concurrency": concurrency,
    #     "rate_limit": rate_limit,
    #     "path": path or ".",
    #     "debug": ctx.obj.get("DEBUG", False),
    # }

    # Run extraction
    click.echo("Step 1: Extracting knowledge...")
    # TODO: Pass config to run_mining

    # Run synthesis
    click.echo("Step 2: Synthesizing insights...")
    # TODO: Pass config to run_synthesis

    click.echo("Pipeline complete!")


@cli.command()
@click.option("--force", is_flag=True, help="Force reprocessing")
@click.option("--concurrency", type=int, default=1, help="Number of parallel workers")
@click.argument("path", type=click.Path(exists=True), required=False)
def extract(force: bool, concurrency: int, path: str | None) -> None:
    """Extract knowledge from documents."""
    click.echo(f"Extracting from {path or 'current directory'}...")

    # TODO: Implement extraction with new options


@cli.command()
@click.option("--force", is_flag=True, help="Force regeneration")
@click.option("--stage", type=click.Choice(["triage", "analysis", "synthesis"]), help="Run specific stage only")
def synthesize(force: bool, stage: str | None) -> None:
    """Synthesize insights from extracted knowledge."""
    click.echo(f"Synthesizing (stage: {stage or 'all'})...")

    # TODO: Implement synthesis with stage selection


@cli.command()
@click.argument("path", type=click.Path(exists=True), required=False)
def triage(path: str | None) -> None:
    """Triage and prioritize content for processing."""
    click.echo("Running triage...")

    # TODO: Implement triage


@cli.command()
def smoke() -> None:
    """Run smoke tests to validate the installation."""
    click.echo("Running smoke tests...")

    from amplifier.smoke_tests.runner import main as run_smoke_tests

    # The smoke test runner handles its own exit codes
    run_smoke_tests()


@cli.command()
def doctor() -> None:
    """Check and diagnose the Amplifier environment."""
    click.echo("Running environment diagnostics...")
    click.echo()

    import shutil
    import subprocess
    from pathlib import Path

    checks = []

    # Check Python version
    py_version = sys.version_info
    if py_version >= (3, 11):
        checks.append(("Python 3.11+", True, f"{py_version.major}.{py_version.minor}.{py_version.micro}"))
    else:
        checks.append(
            ("Python 3.11+", False, f"{py_version.major}.{py_version.minor}.{py_version.micro} (upgrade required)")
        )

    # Check Claude CLI
    claude_path = shutil.which("claude")
    if claude_path:
        checks.append(("Claude CLI", True, claude_path))
    else:
        checks.append(("Claude CLI", False, "Not found (install with: npm install -g @anthropic-ai/claude-code)"))

    # Check Node/npm
    npm_path = shutil.which("npm")
    if npm_path:
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=2)
            checks.append(("npm", True, f"v{result.stdout.strip()}"))
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            checks.append(("npm", False, "Found but couldn't get version"))
    else:
        checks.append(("npm", False, "Not found"))

    # Check environment variables
    import os

    amplifier_home = os.environ.get("AMPLIFIER_HOME")
    if amplifier_home:
        checks.append(("AMPLIFIER_HOME", True, amplifier_home))
    else:
        checks.append(("AMPLIFIER_HOME", False, "Not set (using default)"))

    # Check data directory
    data_dir = Path(".data")
    if data_dir.exists() and data_dir.is_dir():
        checks.append(("Data directory", True, str(data_dir.absolute())))
    else:
        checks.append(("Data directory", False, "Not found (will be created on first run)"))

    # Check config file
    config_file = Path("amplifier.config.json")
    if config_file.exists():
        checks.append(("Config file", True, str(config_file.absolute())))
    else:
        checks.append(("Config file", False, "Using defaults"))

    # Display results
    all_good = True
    for name, status, details in checks:
        if status:
            icon = click.style("✓", fg="green")
            status_text = click.style("OK", fg="green")
        else:
            icon = click.style("✗", fg="red")
            status_text = click.style("FAIL", fg="red")
            all_good = False

        click.echo(f"{icon} {name:20} [{status_text}] {details}")

    click.echo()
    if all_good:
        click.echo(click.style("Environment is healthy!", fg="green"))
    else:
        click.echo(click.style("Some issues found. Please fix the items marked with ✗", fg="yellow"))
        sys.exit(1)


@cli.group()
def events() -> None:
    """Manage and view event logs."""
    pass


@events.command("tail")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option("--lines", "-n", type=int, default=10, help="Number of lines to show")
def events_tail(follow: bool, lines: int) -> None:
    """Tail the event log."""
    click.echo(f"Tailing last {lines} events...")

    # TODO: Implement event tailing
    event_file = Path(".data/events/events.jsonl")
    if not event_file.exists():
        click.echo("No events found")
        return

    import json

    with open(event_file) as f:
        all_lines = f.readlines()
        for line in all_lines[-lines:]:
            event = json.loads(line)
            click.echo(f"[{event.get('timestamp')}] {event.get('stage')} - {event.get('status')}")

    if follow:
        click.echo("Following events... (Ctrl+C to stop)")
        # TODO: Implement follow mode


@events.command("summary")
@click.option("--stage", help="Filter by stage")
def events_summary(stage: str | None) -> None:
    """Show summary statistics for events."""
    click.echo("Event summary:")

    # TODO: Implement event summary
    event_file = Path(".data/events/events.jsonl")
    if not event_file.exists():
        click.echo("No events found")
        return

    import json
    from collections import Counter

    stages = Counter()
    statuses = Counter()

    with open(event_file) as f:
        for line in f:
            event = json.loads(line)
            if not stage or event.get("stage") == stage:
                stages[event.get("stage")] += 1
                statuses[event.get("status")] += 1

    click.echo("\nBy Stage:")
    for s, count in stages.most_common():
        click.echo(f"  {s}: {count}")

    click.echo("\nBy Status:")
    for s, count in statuses.most_common():
        click.echo(f"  {s}: {count}")


@cli.command()
def graph() -> None:
    """Visualize the knowledge graph."""
    click.echo("Generating knowledge graph visualization...")

    # TODO: Implement graph visualization


@cli.command("self-update")
def self_update() -> None:
    """Update Amplifier to the latest version."""
    click.echo("Checking for updates...")

    import subprocess

    try:
        # Try to update via pip/uv
        result = subprocess.run(
            ["uv", "pip", "install", "--upgrade", "amplifier-toolkit"], capture_output=True, text=True
        )
        if result.returncode == 0:
            click.echo(click.style("✓ Updated successfully!", fg="green"))
        else:
            click.echo("No updates available")
    except FileNotFoundError:
        click.echo("Update mechanism not available. Please update manually.")


@cli.command("install-global")
def install_global() -> None:
    """Install Amplifier globally for use across all projects."""
    click.echo("Installing Amplifier globally...")

    import subprocess

    # Detect installation method
    if shutil.which("pipx"):
        click.echo("Installing with pipx...")
        subprocess.run(["pipx", "install", "amplifier-toolkit"])
    elif shutil.which("brew"):
        click.echo("Installing with Homebrew...")
        # TODO: Set up Homebrew tap
        click.echo("Homebrew installation coming soon. Use pipx for now.")
    else:
        click.echo("Installing with pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "amplifier-toolkit"])

    click.echo(click.style("✓ Installation complete!", fg="green"))
    click.echo("You can now use 'amplifier' command from anywhere.")


if __name__ == "__main__":
    cli()
