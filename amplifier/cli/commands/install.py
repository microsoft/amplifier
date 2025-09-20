"""
Install command for Amplifier CLI v3.

Fetches resources from the microsoft/amplifier GitHub repository.

Contract:
    - Install specific resources: amplifier install agents zen-architect
    - Install all of a type: amplifier install agents
    - Install all resource types: amplifier install all
    - Resources ALWAYS go to .claude/ subdirectories
    - Updates manifest after installation with SHA tracking
    - Supports --source flag for branch/tag selection
"""

import asyncio

import click

from amplifier.cli.core import fetch_from_github
from amplifier.cli.core import get_resource_extension
from amplifier.cli.core import get_resource_target_dir
from amplifier.cli.core import install_resource
from amplifier.cli.core import is_resource_installed
from amplifier.cli.core import list_github_resources
from amplifier.cli.core.github import GitHubClient


async def _install_single_type(
    resource_type: str,
    names: tuple[str, ...],
    force: bool,
    dry_run: bool,
    ref: str,
) -> tuple[int, int, int]:
    """Install resources of a single type.

    Returns:
        Tuple of (installed_count, skipped_count, failed_count)
    """
    # Get available resources from GitHub
    available_names = await list_github_resources(resource_type, ref)

    if not available_names:
        click.echo(f"  No {resource_type} available from GitHub.")
        return 0, 0, 0

    # Determine what to install
    if names:
        # Install specific resources
        to_install = list(names)
        # Validate names
        invalid = [n for n in to_install if n not in available_names]
        if invalid:
            click.echo(f"  Error: Unknown {resource_type}: {', '.join(invalid)}")
            click.echo(f"  Available: {', '.join(available_names)}")
            return 0, 0, len(invalid)
    else:
        # Install all available resources of this type
        to_install = available_names
        if dry_run:
            click.echo(f"  Would install all available {resource_type}...")
        else:
            click.echo(f"  Installing all available {resource_type}...")

    # Install each resource
    installed_count = 0
    skipped_count = 0
    failed_count = 0

    for name in to_install:
        # Check if already installed
        if is_resource_installed(resource_type, name) and not force:
            if dry_run:
                click.echo(f"    → {name}: Would skip (already installed, use --force to reinstall)")
            else:
                click.echo(f"    → {name}: Already installed (use --force to reinstall)")
            skipped_count += 1
            continue

        if dry_run:
            # Just show what would happen
            target_dir = get_resource_target_dir(resource_type)
            click.echo(f"    → {name}: Would fetch from GitHub and install to {target_dir}")
            installed_count += 1
        else:
            # Fetch from GitHub
            content, sha = await fetch_from_github(resource_type, name, ref)

            if content is None:
                click.echo(f"    ✗ {name}: Failed to fetch from GitHub")
                failed_count += 1
                continue

            # Install the resource
            success = install_resource(
                resource_type=resource_type,
                name=name,
                content=content,
                sha=sha,
                ref=ref,
                source="github",
            )

            if success:
                target_dir = get_resource_target_dir(resource_type)
                # If name has extension, use it; otherwise show with the resource type's default extension
                display_name = name if "." in name else f"{name}{get_resource_extension(resource_type)}"
                click.echo(f"    ✓ {name}: Installed to {target_dir}/{display_name}")
                installed_count += 1
            else:
                click.echo(f"    ✗ {name}: Installation failed")
                failed_count += 1

    return installed_count, skipped_count, failed_count


async def async_install(
    resource_type: str,
    names: tuple[str, ...],
    force: bool,
    dry_run: bool,
    source: str,
    release: str | None,
) -> None:
    """Async implementation of install command.

    Args:
        resource_type: Type of resource to install (or 'all' for all types)
        names: Specific resource names or empty for all
        force: Force reinstall even if already installed
        dry_run: Preview without making changes
        source: Branch or 'release' for latest release
        release: Specific release tag to use
    """
    github = GitHubClient()

    # Determine the ref to use
    if release:
        ref = release
    elif source == "release":
        ref = await github.get_latest_release()
        if not ref:
            click.echo("Warning: No releases found, using main branch")
            ref = "main"
    else:
        ref = source

    # Handle "all" resource type
    if resource_type == "all":
        if names:
            click.echo("Error: Cannot specify resource names when using 'all'")
            return

        click.echo(f"Installing ALL resources from GitHub (ref: {ref})...")
        click.echo("")

        # Install all resource types
        all_types = ["agents", "tools", "commands", "mcp-servers"]
        total_installed = 0
        total_skipped = 0
        total_failed = 0

        for rtype in all_types:
            click.echo(f"Processing {rtype}:")
            installed, skipped, failed = await _install_single_type(rtype, (), force, dry_run, ref)
            total_installed += installed
            total_skipped += skipped
            total_failed += failed

            if installed > 0 or skipped > 0 or failed > 0:
                click.echo(f"  Summary: {installed} installed, {skipped} skipped, {failed} failed")
            click.echo("")

        # Overall summary
        click.echo("=" * 50)
        if dry_run:
            if total_installed > 0:
                click.echo(click.style(f"Would install {total_installed} resources total", fg="yellow"))
            if total_skipped > 0:
                click.echo(f"Would skip {total_skipped} (already installed)")
            if total_failed > 0:
                click.echo(click.style(f"✗ {total_failed} resources not found", fg="red"))
            click.echo("\n[DRY RUN] No changes made. Remove --dry-run to install.")
        else:
            if total_installed > 0:
                click.echo(click.style(f"✓ Installed {total_installed} resources total", fg="green"))
            if total_skipped > 0:
                click.echo(f"Skipped {total_skipped} (already installed)")
            if total_failed > 0:
                click.echo(click.style(f"✗ Failed to install {total_failed} resources", fg="red"))
        return

    # Handle single resource type installation
    click.echo(f"Fetching {resource_type} from GitHub (ref: {ref})...")

    installed_count, skipped_count, failed_count = await _install_single_type(resource_type, names, force, dry_run, ref)

    # Summary
    click.echo("")
    if dry_run:
        if installed_count > 0:
            click.echo(click.style(f"Would install {installed_count} {resource_type}", fg="yellow"))
        if skipped_count > 0:
            click.echo(f"  Would skip {skipped_count} (already installed)")
        if failed_count > 0:
            click.echo(click.style(f"✗ {failed_count} {resource_type} not found", fg="red"))
        click.echo("\n[DRY RUN] No changes made. Remove --dry-run to install.")
    else:
        if installed_count > 0:
            click.echo(click.style(f"✓ Installed {installed_count} {resource_type}", fg="green"))
        if skipped_count > 0:
            click.echo(f"  Skipped {skipped_count} (already installed)")
        if failed_count > 0:
            click.echo(click.style(f"✗ Failed to install {failed_count} {resource_type}", fg="red"))


@click.command()
@click.argument("resource_type", type=click.Choice(["agents", "tools", "commands", "mcp-servers", "all"]))
@click.argument("names", nargs=-1)
@click.option("--force", is_flag=True, help="Force reinstall even if already installed")
@click.option("--dry-run", is_flag=True, help="Preview what would be installed without making changes")
@click.option("--source", default="main", help="Git ref to install from (branch/tag, default: main)")
@click.option("--release", help="Install from specific release tag")
def cmd(
    resource_type: str,
    names: tuple[str, ...],
    force: bool,
    dry_run: bool,
    source: str,
    release: str | None,
) -> None:
    """Install resources from GitHub to the .claude/ directory.

    RESOURCE_TYPE: Type of resource (agents, tools, commands, mcp-servers, all)
    NAMES: Optional specific resource names. If omitted, installs all available.
           Cannot be used with 'all' resource type.

    Examples:

        amplifier install agents zen-architect
        amplifier install agents --source main
        amplifier install all                      # Install all resource types
        amplifier install all --force              # Reinstall everything
        amplifier install agents --release v1.0.0
        amplifier install agents --source release  # Latest release
    """
    # Run async installation
    asyncio.run(
        async_install(
            resource_type=resource_type,
            names=names,
            force=force,
            dry_run=dry_run,
            source=source if source != "release" else "release",
            release=release,
        )
    )
