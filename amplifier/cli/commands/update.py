"""
Update command for Amplifier CLI v3.

This command checks for updates to installed resources and applies them.
It compares installed SHA hashes with the latest from GitHub.

Contract:
    - update [--check] → Check/apply updates for all resources
    - update --check → Check for updates without installing
    - update [type] → Update only specific resource type
"""

import asyncio

import click
from rich.console import Console
from rich.table import Table

from amplifier.cli.core.github import GitHubClient
from amplifier.cli.core.manifest import list_installed_resources
from amplifier.cli.core.manifest import needs_update
from amplifier.cli.core.manifest import update_resource_sha
from amplifier.cli.core.paths import get_resource_target_dir
from amplifier.cli.core.resources import get_resource_extension

console = Console()


async def check_for_updates(resource_type: str | None = None) -> list[dict]:
    """Check for available updates.

    Args:
        resource_type: Optional filter by type

    Returns:
        List of resources with updates available
    """
    updates = []
    github = GitHubClient()

    # Get latest release or use main
    ref = await github.get_latest_release() or "main"

    # Get all installed resources
    installed = list_installed_resources(resource_type)

    for resource in installed:
        # Check GitHub for latest SHA
        metadata = await github.fetch_resource_metadata(resource.type, resource.name, ref)

        if metadata:
            github_sha = metadata["sha"]
            if needs_update(resource.type, resource.name, github_sha):
                updates.append(
                    {
                        "type": resource.type,
                        "name": resource.name,
                        "current_sha": resource.sha or "unknown",
                        "new_sha": github_sha,
                        "ref": ref,
                    }
                )

    return updates


async def apply_update(update_info: dict) -> bool:
    """Apply a single resource update.

    Args:
        update_info: Dictionary with update details

    Returns:
        True if update succeeded
    """
    github = GitHubClient()

    # Fetch the new content
    content, sha, sha256 = await github.fetch_resource(update_info["type"], update_info["name"], update_info["ref"])

    if content is None or sha is None:
        console.print(f"[red]Failed to fetch {update_info['type']}/{update_info['name']} from GitHub[/red]")
        return False

    # Write the updated content
    target_dir = get_resource_target_dir(update_info["type"])
    extension = get_resource_extension(update_info["type"])
    target_file = target_dir / f"{update_info['name']}{extension}"

    try:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)

        # Update manifest with new SHA
        update_resource_sha(update_info["type"], update_info["name"], sha, update_info["ref"])

        console.print(f"[green]✓[/green] Updated {update_info['type']}/{update_info['name']}")
        return True

    except Exception as e:
        console.print(f"[red]Error updating {update_info['type']}/{update_info['name']}: {e}[/red]")
        return False


async def async_update(check_only: bool, resource_type: str | None) -> None:
    """Async implementation of update command.

    Args:
        check_only: If True, only check for updates without applying
        resource_type: Optional filter by resource type
    """
    # Check for updates
    console.print("Checking for updates...")
    updates = await check_for_updates(resource_type)

    if not updates:
        console.print("[green]All resources are up to date![/green]")
        return

    # Display available updates
    table = Table(title="Available Updates")
    table.add_column("Type", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Current SHA", style="dim")
    table.add_column("New SHA", style="dim")

    for update in updates:
        table.add_row(
            update["type"],
            update["name"],
            update["current_sha"][:8] if update["current_sha"] != "unknown" else "unknown",
            update["new_sha"][:8],
        )

    console.print(table)

    if check_only:
        console.print(f"\n[yellow]{len(updates)} update(s) available[/yellow]")
        console.print("Run [cyan]amplifier update[/cyan] to apply updates")
        return

    # Apply updates
    console.print(f"\nApplying {len(updates)} update(s)...")

    success_count = 0
    for update in updates:
        if await apply_update(update):
            success_count += 1

    console.print(f"\n[green]Successfully updated {success_count}/{len(updates)} resource(s)[/green]")


@click.command()
@click.option("--check", is_flag=True, help="Check for updates without installing")
@click.argument("resource_type", required=False)
def cmd(check: bool, resource_type: str | None) -> None:
    """Check for and apply updates to installed resources.

    Check for updates to all resources or a specific type. By default,
    applies updates. Use --check to only check without updating.

    Examples:

        amplifier update              # Update all resources
        amplifier update --check      # Check for updates only
        amplifier update agents       # Update only agents
    """
    # Validate resource type if provided
    valid_types = ["agents", "tools", "commands", "mcp-servers"]
    if resource_type and resource_type not in valid_types:
        console.print(f"[red]Invalid resource type: {resource_type}[/red]")
        console.print(f"Valid types: {', '.join(valid_types)}")
        return

    # Run async update
    asyncio.run(async_update(check, resource_type))
