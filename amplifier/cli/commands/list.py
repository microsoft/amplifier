"""
List command module for Amplifier CLI v3.

This module provides the 'amplifier list' command to display installed and
available resources from the project's .claude/ directory.

Contract:
    - List all installed resources
    - Filter by resource type
    - Show available but not installed resources
    - Display in user-friendly format
"""

from datetime import datetime
from typing import Any

import click
from rich import box

from amplifier.cli.core.decorators import handle_errors
from amplifier.cli.core.decorators import log_command
from amplifier.cli.core.decorators import requires_init
from amplifier.cli.core.manifest import list_installed_resources
from amplifier.cli.core.output import get_output_manager
from amplifier.cli.core.resources import list_available_github_resources

RESOURCE_TYPES = ["agents", "tools", "commands", "mcp-servers"]


@click.command(name="list")
@click.argument("resource_type", required=False, type=click.Choice(RESOURCE_TYPES + ["all"], case_sensitive=False))
@click.option("--installed", is_flag=True, help="Show only installed resources")
@click.option("--available", is_flag=True, help="Show only resources not yet installed")
@handle_errors()
@requires_init
@log_command("list")
@click.pass_context
def cmd(ctx: click.Context, resource_type: str | None, installed: bool, available: bool) -> None:
    """List resources (both installed and available).

    Examples:
        amplifier list                    # List both installed and available resources
        amplifier list --installed        # Show only installed resources
        amplifier list --available        # Show only resources not yet installed
        amplifier list agents             # List all agents (installed and available)
        amplifier list agents --installed # List installed agents only
    """
    output = ctx.obj.get("output", get_output_manager())

    # Default to showing BOTH if no flags specified
    if not installed and not available:
        installed = True
        available = True

    # Handle resource type filter
    types_to_check = RESOURCE_TYPES
    if resource_type and resource_type != "all":
        types_to_check = [resource_type]

    # Gather data
    installed_data = {}
    available_data = {}
    all_available_resources = {}

    with output.spinner("Gathering resource information..."):
        # Get installed resources
        for rtype in types_to_check:
            resources = list_installed_resources(rtype)
            if resources:
                installed_data[rtype] = resources

        # Get available resources from GitHub
        import asyncio

        try:
            all_available_resources = asyncio.run(list_available_github_resources())
        except Exception:
            # Fallback to empty if GitHub fails
            all_available_resources = {}

        # Build set of installed resource names (without extensions for comparison)
        installed_all = list_installed_resources()
        installed_names = set()
        for r in installed_all:
            # Store both with and without extension for comparison
            installed_names.add((r.type, r.name))
            # Also strip extension if present for comparison
            name_without_ext = r.name.rsplit(".", 1)[0] if "." in r.name else r.name
            installed_names.add((r.type, name_without_ext))

        # Filter available resources to find not installed
        for rtype in types_to_check:
            if rtype in all_available_resources:
                not_installed = []
                for name in all_available_resources[rtype]:
                    # Check both full name and name without extension
                    name_without_ext = name.rsplit(".", 1)[0] if "." in name else name
                    if (rtype, name) not in installed_names and (rtype, name_without_ext) not in installed_names:
                        not_installed.append(name)
                if not_installed:
                    available_data[rtype] = not_installed

    # Display results
    show_installed = installed and installed_data
    show_available = available and available_data

    if show_installed:
        display_installed_resources(installed_data, output)

    if show_available:
        if show_installed:
            output.console.print()  # Add space between sections
        display_available_resources(available_data, output)

    # Handle empty results with helpful messages
    if not show_installed and not show_available:
        if installed and not installed_data:
            output.warning("No resources installed yet")
            output.info("💡 Run 'amplifier install agents' to get started")
        elif available and not available_data:
            # Check if we failed to fetch from GitHub
            if not all_available_resources:
                output.warning("Could not fetch available resources from GitHub")
                output.info("💡 Check your internet connection or set GITHUB_TOKEN for better rate limits")
            else:
                total_installed = len(installed_all) if "installed_all" in locals() else 0
                if total_installed > 0:
                    output.info(f"All available resources are already installed ({total_installed} resources)")
                else:
                    output.info("No available resources found in the GitHub repository")
        elif not installed_data and not available_data:
            output.warning("No resources found")
            if not all_available_resources:
                output.info("💡 Could not fetch from GitHub. Check your connection or set GITHUB_TOKEN")
            else:
                output.info("💡 Try 'amplifier list' without flags to see all resources")


def display_installed_resources(resources_by_type: dict[str, list[Any]], output) -> None:
    """Display installed resources in a formatted table.

    Args:
        resources_by_type: Dictionary of resource type to list of Resource objects
        output: OutputManager instance
    """
    # Create a table for installed resources
    table = output.create_table("Installed Resources")
    table.box = box.ROUNDED
    table.add_column("Type", style="cyan", min_width=12)
    table.add_column("Name", style="white", min_width=25)
    table.add_column("Status", style="green", justify="center")
    table.add_column("Installed", style="dim", min_width=20)
    table.add_column("Source", style="yellow")

    row_count = 0
    for resource_type in RESOURCE_TYPES:
        if resource_type not in resources_by_type:
            continue

        resources = resources_by_type[resource_type]
        # Add a separator row if not the first type
        if row_count > 0:
            table.add_section()

        for resource in resources:
            # Format timestamp
            if hasattr(resource, "installed_at"):
                if isinstance(resource.installed_at, str):
                    # Parse ISO format string
                    dt = datetime.fromisoformat(resource.installed_at)
                    timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    timestamp = resource.installed_at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp = "unknown"

            # Add row with better formatting
            table.add_row(
                resource_type,
                resource.name,
                "✓ Installed",
                timestamp,
                resource.source or "local",
            )
            row_count += 1

    output.console.print(table)

    # Summary
    total = sum(len(resources) for resources in resources_by_type.values())
    output.console.print(f"\n[dim]Total: {total} resource{'s' if total != 1 else ''} installed[/dim]")


def display_available_resources(resources_by_type: dict[str, list[str]], output) -> None:
    """Display available (not installed) resources.

    Args:
        resources_by_type: Dictionary of resource type to list of resource names
        output: OutputManager instance
    """
    # Create a table for available resources
    table = output.create_table("Available Resources (Not Installed)")
    table.box = box.SIMPLE_HEAVY
    table.add_column("Type", style="cyan", min_width=12)
    table.add_column("Name", style="white", min_width=25)
    table.add_column("Status", justify="center")
    table.add_column("Install Command", style="dim")

    row_count = 0
    for resource_type in RESOURCE_TYPES:
        if resource_type not in resources_by_type:
            continue

        names = resources_by_type[resource_type]
        # Add a separator row if not the first type
        if row_count > 0:
            table.add_section()

        for name in names:
            action = f"amplifier install {resource_type} {name}"
            table.add_row(
                resource_type,
                name,
                "[dim]Not installed[/dim]",
                action,
            )
            row_count += 1

    output.console.print(table)

    # Summary and help
    total = sum(len(names) for names in resources_by_type.values())
    output.console.print(f"\n[dim]Total: {total} resource{'s' if total != 1 else ''} available to install[/dim]")

    # Show helpful tips
    if total > 0:
        output.console.print()
        output.info("💡 To install a specific resource, run the command shown in the table")
        output.info(
            f"💡 To install all {list(resources_by_type.keys())[0]}, run: amplifier install {list(resources_by_type.keys())[0]}"
        )
