#!/usr/bin/env python3
"""CLI command for auto-healing Python modules."""

import logging
from pathlib import Path

import click

from amplifier.tools.auto_healer import heal_batch
from amplifier.tools.health_monitor import HealthMonitor


@click.command()
@click.option("--max", default=3, help="Maximum modules to heal")
@click.option("--threshold", default=70, help="Health score threshold")
@click.option("--check-only", is_flag=True, help="Only check health, don't heal")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def heal(max: int, threshold: float, check_only: bool, yes: bool, verbose: bool):
    """Auto-heal unhealthy Python modules using AI.

    This command analyzes module health (complexity, LOC, type errors)
    and uses Aider to refactor modules that fall below the threshold.
    """
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    project_root = Path(".")
    monitor = HealthMonitor(project_root)

    # Show current health status
    click.echo("\n📊 Module Health Analysis")
    click.echo("=" * 60)

    candidates = monitor.get_healing_candidates(threshold)

    if not candidates:
        click.echo(f"✅ All modules are healthy (score > {threshold})")
        return

    # Display unhealthy modules
    click.echo(f"\n❗ Found {len(candidates)} unhealthy modules:\n")
    for i, health in enumerate(candidates[:max], 1):
        module_name = Path(health.module_path).name
        click.echo(f"  {i}. {module_name}")
        click.echo(f"     Health: {health.health_score:.1f}/100")
        click.echo(f"     Complexity: {health.complexity}")
        click.echo(f"     Lines: {health.loc}")
        if health.type_errors:
            click.echo(f"     Type Errors: {health.type_errors}")

    if check_only:
        click.echo("\n(Check-only mode - no healing performed)")
        return

    # Confirm before healing (unless --yes flag is used)
    if not yes and not click.confirm(f"\n🔧 Heal up to {max} modules?"):
        click.echo("Cancelled.")
        return

    click.echo("\n🚀 Starting auto-healing...")
    click.echo("-" * 40)

    # Perform healing
    results = heal_batch(max, threshold, project_root)

    # Show results
    click.echo("\n📋 Healing Results")
    click.echo("=" * 60)

    for result in results:
        module_name = Path(result.module_path).name
        if result.status == "success":
            improvement = result.health_after - result.health_before
            click.echo(f"✅ {module_name}: +{improvement:.1f} points")
        elif result.status == "failed":
            click.echo(f"❌ {module_name}: {result.error}")
        elif result.status == "skipped":
            click.echo(f"⏭️  {module_name}: {result.error}")

    successful = sum(1 for r in results if r.status == "success")
    click.echo(f"\n✨ Healed {successful}/{len(results)} modules successfully!")


if __name__ == "__main__":
    heal()
