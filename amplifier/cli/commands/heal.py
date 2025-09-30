"""Heal command for auto-healing unhealthy modules."""

from pathlib import Path

import click

from amplifier.tools.auto_healer import heal_batch


@click.command()
@click.option("--max", default=3, help="Maximum modules to heal")
@click.option("--threshold", default=70.0, help="Health threshold")
@click.option("--check-only", is_flag=True, help="Only check health, do not heal")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--project-root",
    type=click.Path(path_type=Path, exists=True),
    default=None,
    help="Override project root (defaults to current working directory)",
)
def heal(max, threshold, check_only, yes, project_root):
    """Auto-heal unhealthy Python modules."""
    from amplifier.tools.health_monitor import HealthMonitor

    root = project_root or Path.cwd()
    monitor = HealthMonitor(root)

    # Get unhealthy modules
    candidates = monitor.get_healing_candidates(threshold)

    print("📊 Module Health Analysis")
    print("=" * 60)

    if not candidates:
        print(f"\n✅ All modules are healthy (score > {threshold})")
        return

    print(f"\n❗ Found {len(candidates)} unhealthy modules:\n")
    for i, health in enumerate(candidates[:10], 1):
        module_name = Path(health.module_path).name
        print(f"  {i}. {module_name}")
        print(f"     Health: {health.health_score:.1f}/100")
        print(f"     Complexity: {health.complexity}")
        print(f"     Lines: {health.loc}")
        if health.type_errors:
            print(f"     Type Errors: {health.type_errors}")

    if len(candidates) > 10:
        print(f"\n  ... and {len(candidates) - 10} more")

    if check_only:
        print("\n(Check-only mode - no healing performed)")
        return

    # Ask for confirmation unless --yes flag is used
    if not yes:
        try:
            response = input(f"\n🔧 Heal up to {max} modules? (y/n): ")
            if response.lower() != "y":
                print("Cancelled.")
                return
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return

    print("\n🚀 Starting auto-healing...")
    print("-" * 40)

    # Run healing
    results = heal_batch(max, threshold, root)

    # Display results
    print("\n📋 Healing Results")
    print("=" * 60)

    success_count = 0
    for result in results:
        module_name = Path(result.module_path).name
        if result.status == "success":
            improvement = result.health_after - result.health_before
            print(f"✅ {module_name}: +{improvement:.1f} points")
            success_count += 1
        elif result.status == "skipped":
            print(f"⏭️  {module_name}: {result.reason}")
        else:
            print(f"❌ {module_name}: {result.reason}")

    print(f"\n✨ Healed {success_count}/{len(results)} modules successfully!")
