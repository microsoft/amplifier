"""
Amplifier CLI v3 - Manage Claude Code resources.

This is the main entry point for the CLI. It provides commands to initialize
projects and manage resources in the .claude/ directory.

Contract:
    - Entry point: main() function
    - Commands: init, install, list, remove, update, version
    - All resources go to .claude/, metadata to .amplifier/
"""

import sys

import click
from rich.console import Console
from rich.panel import Panel

from amplifier.cli.commands import completions
from amplifier.cli.commands import config
from amplifier.cli.commands import init
from amplifier.cli.commands import install
from amplifier.cli.commands import list as list_cmd
from amplifier.cli.commands import remove
from amplifier.cli.commands import update
from amplifier.cli.commands import worktree
from amplifier.cli.core.output import OutputManager
from amplifier.cli.core.output import get_output_manager
from amplifier.cli.core.updates import check_updates_on_startup
from amplifier.cli.core.version import get_version


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.option("--quiet", "-q", is_flag=True, help="Minimal output (errors only)")
@click.version_option(version=get_version(), prog_name="amplifier")
@click.pass_context
def cli(ctx: click.Context, debug: bool, quiet: bool) -> None:
    """Amplifier CLI v3 - Manage Claude Code resources.

    Initialize projects and manage agents, tools, commands, and MCP servers
    in the .claude/ directory for use with Claude Code.

    \b
    Examples:
        amplifier init                    # Initialize a new project
        amplifier list                    # Show installed resources
        amplifier install agents           # Install all agents
        amplifier install agents zen-architect  # Install specific agent
        amplifier update                  # Update all resources
        amplifier remove tools test-tool  # Remove specific tool
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    ctx.obj["quiet"] = quiet
    ctx.obj["output"] = get_output_manager(quiet=quiet, debug=debug)

    # Show debug message if enabled
    if debug:
        output = ctx.obj["output"]
        output.debug("Debug mode enabled")


@cli.command()
@click.pass_context
def version(ctx: click.Context) -> None:
    """Show amplifier CLI version and system information."""
    output = ctx.obj.get("output", get_output_manager())

    if ctx.obj.get("quiet"):
        # In quiet mode, just print the version number
        click.echo(get_version())
    else:
        # Create a nice panel with version info
        console = Console()
        version_info = (
            "[bold cyan]Amplifier CLI[/bold cyan]\n\n"
            f"Version: [green]{get_version()}[/green]\n"
            f"Python: [yellow]{sys.version.split()[0]}[/yellow]\n"
            f"Platform: [blue]{sys.platform}[/blue]"
        )

        # Add debug info if debug mode is enabled
        if ctx.obj.get("debug"):
            import platform

            version_info += (
                f"\n\nDebug Information:\n"
                f"Python Path: {sys.executable}\n"
                f"OS: {platform.system()} {platform.release()}\n"
                f"Architecture: {platform.machine()}"
            )

        console.print(
            Panel.fit(
                version_info,
                title="[bold]Version Info[/bold]",
                border_style="cyan",
                padding=(1, 2),
            )
        )

        # Show next steps
        if not ctx.obj.get("debug"):
            output.info("Run 'amplifier --help' to see available commands")


# Register commands
cli.add_command(completions.cmd, name="completions")
cli.add_command(config.cmd, name="config")
cli.add_command(init.cmd, name="init")
cli.add_command(install.cmd, name="install")
cli.add_command(list_cmd.cmd, name="list")
cli.add_command(remove.cmd, name="remove")
cli.add_command(update.cmd, name="update")
cli.add_command(worktree.cmd, name="worktree")


def main() -> None:
    """Main entry point for the CLI."""
    try:
        # Check for updates on startup (non-blocking)
        # This happens before the CLI runs to avoid interfering with command output
        # Only check if not in help mode and not version mode
        if len(sys.argv) > 1 and sys.argv[1] not in ["--help", "-h", "--version", "version"]:
            # Extract flags to determine if in quiet/debug mode
            quiet = "--quiet" in sys.argv or "-q" in sys.argv
            debug = "--debug" in sys.argv
            check_updates_on_startup(quiet=quiet, debug=debug)

        cli()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        console = Console()
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        # Handle unexpected errors
        console = Console()
        console.print(f"\n[red]Error: {e}[/red]")
        console.print("[dim]Run with --debug flag for more details[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
