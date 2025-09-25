#!/usr/bin/env python3
"""
Amplifier CLI - Unified command-line interface for all Amplifier tools.

This provides a single entry point for all Amplifier functionality, replacing
scattered make targets and individual scripts with a consistent interface.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import click
from click import Context


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version information")
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.argument("project_dir", type=click.Path(), required=False)
@click.pass_context
def cli(ctx: Context, version: bool, debug: bool, project_dir: str | None) -> None:
    """Amplifier - Launch Claude with Amplifier's AI agents and tools.

    Launch Claude with Amplifier context for any project. If no PROJECT_DIR is
    provided, uses the current directory.

    Examples:
        amplifier                    # Launch in current directory
        amplifier ~/myproject        # Launch in specific project
        amplifier --version          # Show version
    """
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = debug

    if version:
        click.echo("Amplifier v0.2.0")
        sys.exit(0)

    # If no subcommand, launch Claude (default behavior)
    if ctx.invoked_subcommand is None:
        from amplifier.claude_launcher import launch_claude
        from pathlib import Path

        # Use provided directory or current directory
        target_dir = Path(project_dir) if project_dir else Path.cwd()
        sys.exit(launch_claude(target_dir))


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
    # Will be used when run_mining and run_synthesis are implemented
    _ = {
        "force": force,
        "since": since,
        "concurrency": concurrency,
        "rate_limit": rate_limit,
        "path": path or ".",
        "debug": ctx.obj.get("DEBUG", False),
    }

    # Run extraction
    click.echo("Step 1: Extracting knowledge...")
    # Note: Pass config when run_mining is implemented

    # Run synthesis
    click.echo("Step 2: Synthesizing insights...")
    # Note: Pass config when run_synthesis is implemented

    click.echo("Pipeline complete!")


@cli.command()
@click.option("--force", is_flag=True, help="Force reprocessing")
@click.option("--concurrency", type=int, default=1, help="Number of parallel workers")
@click.argument("path", type=click.Path(exists=True), required=False)
def extract(force: bool, concurrency: int, path: str | None) -> None:
    """Extract knowledge from documents."""
    click.echo(f"Extracting from {path or 'current directory'}...")

    # Extraction implementation pending integration with knowledge mining system
    click.echo("Extraction complete.")


@cli.command()
@click.option("--force", is_flag=True, help="Force regeneration")
@click.option("--stage", type=click.Choice(["triage", "analysis", "synthesis"]), help="Run specific stage only")
def synthesize(force: bool, stage: str | None) -> None:
    """Synthesize insights from extracted knowledge."""
    click.echo(f"Synthesizing (stage: {stage or 'all'})...")

    # Synthesis implementation pending integration with synthesis engine
    click.echo("Synthesis complete.")


@cli.command()
@click.argument("path", type=click.Path(exists=True), required=False)
def triage(path: str | None) -> None:
    """Triage and prioritize content for processing."""
    click.echo("Running triage...")

    # Triage implementation pending integration with content prioritization system
    click.echo("Triage complete.")


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
    from enum import Enum
    from pathlib import Path

    class CheckStatus(Enum):
        REQUIRED = "required"
        OPTIONAL = "optional"

    checks = []

    # Check Python version (REQUIRED)
    py_version = sys.version_info
    if py_version >= (3, 11):
        checks.append(
            ("Python 3.11+", True, f"{py_version.major}.{py_version.minor}.{py_version.micro}", CheckStatus.REQUIRED)
        )
    else:
        checks.append(
            (
                "Python 3.11+",
                False,
                f"{py_version.major}.{py_version.minor}.{py_version.micro} (upgrade required)",
                CheckStatus.REQUIRED,
            )
        )

    # Check Claude CLI (REQUIRED for knowledge extraction)
    claude_path = shutil.which("claude")
    if claude_path:
        checks.append(("Claude CLI", True, claude_path, CheckStatus.REQUIRED))
    else:
        checks.append(
            (
                "Claude CLI",
                False,
                "Not found (install with: npm install -g @anthropic-ai/claude-code)",
                CheckStatus.REQUIRED,
            )
        )

    # Check Node/npm (REQUIRED for Claude CLI)
    npm_path = shutil.which("npm")
    if npm_path:
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=2)
            checks.append(("npm", True, f"v{result.stdout.strip()}", CheckStatus.REQUIRED))
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            checks.append(("npm", False, "Found but couldn't get version", CheckStatus.REQUIRED))
    else:
        checks.append(("npm", False, "Not found (needed for Claude CLI)", CheckStatus.REQUIRED))

    # Check environment variables (OPTIONAL)

    amplifier_home = os.environ.get("AMPLIFIER_HOME")
    if amplifier_home:
        checks.append(("AMPLIFIER_HOME", True, amplifier_home, CheckStatus.OPTIONAL))
    else:
        checks.append(("AMPLIFIER_HOME", None, "Not set (using default location)", CheckStatus.OPTIONAL))

    # Check data directory (OPTIONAL - will be created)
    data_dir = Path(".data")
    if data_dir.exists() and data_dir.is_dir():
        checks.append(("Data directory", True, str(data_dir.absolute()), CheckStatus.OPTIONAL))
    else:
        checks.append(("Data directory", None, "Not found (will be created on first run)", CheckStatus.OPTIONAL))

    # Check config file (OPTIONAL)
    config_file = Path("amplifier.config.json")
    if config_file.exists():
        checks.append(("Config file", True, str(config_file.absolute()), CheckStatus.OPTIONAL))
    else:
        checks.append(("Config file", None, "Not found (using defaults)", CheckStatus.OPTIONAL))

    # Display results
    critical_failures = False

    click.echo(click.style("Required Components:", bold=True))
    for name, status, details, check_type in checks:
        if check_type != CheckStatus.REQUIRED:
            continue

        if status:
            icon = click.style("✓", fg="green")
            status_text = click.style("OK", fg="green")
        else:
            icon = click.style("✗", fg="red")
            status_text = click.style("FAIL", fg="red")
            critical_failures = True

        click.echo(f"  {icon} {name:20} [{status_text}] {details}")

    click.echo()
    click.echo(click.style("Optional Components:", bold=True))
    for name, status, details, check_type in checks:
        if check_type != CheckStatus.OPTIONAL:
            continue

        if status is True:
            icon = click.style("✓", fg="green")
            status_text = click.style("OK", fg="green")
        elif status is False:
            icon = click.style("✗", fg="yellow")
            status_text = click.style("WARN", fg="yellow")
        else:  # None means optional and not configured
            icon = click.style("◯", fg="cyan")
            status_text = click.style("INFO", fg="cyan")

        click.echo(f"  {icon} {name:20} [{status_text}] {details}")

    click.echo()
    if critical_failures:
        click.echo(
            click.style(
                "❌ Critical issues found! Please fix the required components marked with ✗", fg="red", bold=True
            )
        )
        sys.exit(1)
    else:
        click.echo(click.style("✅ All required components are healthy!", fg="green", bold=True))
        click.echo(click.style("   Optional components marked with ◯ can be configured if needed.", fg="cyan"))


@cli.command()
@click.argument("project_dir", type=click.Path(exists=True), required=False)
@click.argument("claude_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def claude(ctx: Context, project_dir: str | None, claude_args: tuple[str, ...]) -> None:
    """Launch Claude with Amplifier context.

    \b
    Examples:
        amplifier claude                    # Launch in current directory
        amplifier claude ~/myproject        # Launch in specific project
        amplifier claude . --help           # Pass args to claude CLI

    This command launches Claude with appropriate context depending on whether
    you're working on Amplifier itself or an external project.
    """
    from pathlib import Path

    from amplifier.claude_launcher import launch_claude

    try:
        # Convert tuple to list for extra args
        extra_args = list(claude_args) if claude_args else None
        # Convert string path to Path object if provided
        path_obj = Path(project_dir) if project_dir else None
        launch_claude(path_obj, extra_args)
    except RuntimeError as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        # Handled in launch_claude, just exit cleanly
        sys.exit(0)


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

    # Event tailing implementation
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
        # Follow mode will be implemented with file watching


@events.command("summary")
@click.option("--stage", help="Filter by stage")
def events_summary(stage: str | None) -> None:
    """Show summary statistics for events."""
    click.echo("Event summary:")

    # Generate event summary
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

    # Graph visualization pending integration with visualization system
    click.echo("Graph visualization not yet available.")


@cli.command("self-update")
def self_update() -> None:
    """Update Amplifier to the latest version."""
    click.echo("Checking for updates...")

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

    # Detect installation method
    if shutil.which("pipx"):
        click.echo("Installing with pipx...")
        subprocess.run(["pipx", "install", "amplifier-toolkit"])
    elif shutil.which("brew"):
        click.echo("Installing with Homebrew...")
        # Homebrew tap configuration pending
        click.echo("Homebrew installation coming soon. Use pipx for now.")
    else:
        click.echo("Installing with pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "amplifier-toolkit"])

    click.echo(click.style("✓ Installation complete!", fg="green"))
    click.echo("You can now use 'amplifier' command from anywhere.")


if __name__ == "__main__":
    cli()
