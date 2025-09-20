"""
Remove command module for Amplifier CLI v3.

This module provides the 'amplifier remove' command to remove installed
resources from the project's .claude/ directory.

Contract:
    - Remove specific resources by type and name
    - Support multiple resource removal
    - Confirm before bulk operations
    - Update manifest with removal records
"""

import click
from rich.console import Console
from rich.prompt import Confirm

from amplifier.cli.core.manifest import get_installed_resource
from amplifier.cli.core.manifest import list_installed_resources
from amplifier.cli.core.resources import remove_resource

console = Console()

RESOURCE_TYPES = ["agents", "tools", "commands", "mcp-servers"]


@click.command(name="remove")
@click.argument(
    "resource_type",
    type=click.Choice(RESOURCE_TYPES, case_sensitive=False),
    shell_complete=lambda ctx, param, incomplete: [rt for rt in RESOURCE_TYPES if rt.startswith(incomplete.lower())],
)
@click.argument("names", nargs=-1, required=False)
@click.option("--all", "remove_all", is_flag=True, help="Remove all resources of the specified type")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompts")
def cmd(resource_type: str, names: tuple[str, ...], remove_all: bool, yes: bool) -> None:
    """Remove installed resources.

    Examples:
        amplifier remove agents zen-architect           # Remove specific agent
        amplifier remove agents zen-architect bug-hunter # Remove multiple
        amplifier remove agents --all                    # Remove all agents
        amplifier remove tools test-tool -y              # Skip confirmation
    """
    if not names and not remove_all:
        console.print("[red]Error: Provide resource names or use --all flag[/red]")
        raise click.Abort()

    # Gather resources to remove
    resources_to_remove = []

    if remove_all:
        # Get all installed resources of this type
        installed = list_installed_resources(resource_type)
        if not installed:
            console.print(f"[yellow]No {resource_type} installed to remove.[/yellow]")
            return
        resources_to_remove = [(r.type, r.name) for r in installed]
    else:
        # Check each named resource
        for name in names:
            resource = get_installed_resource(resource_type, name)
            if resource:
                resources_to_remove.append((resource_type, name))
            else:
                console.print(f"[yellow]Warning: {resource_type}/{name} is not installed[/yellow]")

    if not resources_to_remove:
        console.print("[yellow]No resources to remove.[/yellow]")
        return

    # Display what will be removed
    console.print("\n[bold red]Resources to remove:[/bold red]")
    for rtype, name in resources_to_remove:
        console.print(f"  - {rtype}/{name}")

    # Confirm unless --yes flag provided
    if not yes and not Confirm.ask("\n[bold]Continue with removal?[/bold]", default=False):
        console.print("[yellow]Removal cancelled.[/yellow]")
        return

    # Perform removals
    console.print()
    success_count = 0
    fail_count = 0

    for rtype, name in resources_to_remove:
        if remove_resource(rtype, name):
            console.print(f"[green]✓[/green] Removed {name} from .claude/{rtype}/")
            success_count += 1
        else:
            console.print(f"[red]✗[/red] Failed to remove {name}")
            fail_count += 1

    # Summary
    console.print()
    if success_count > 0:
        console.print(f"[green]Successfully removed {success_count} resource(s)[/green]")
    if fail_count > 0:
        console.print(f"[red]Failed to remove {fail_count} resource(s)[/red]")

    if success_count > 0:
        console.print("[dim]Manifest updated[/dim]")
