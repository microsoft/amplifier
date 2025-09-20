#!/usr/bin/env python3
"""
Command-line interface for module generator.

Simple, focused CLI for generating code modules from specifications.
"""

import asyncio
import sys
from pathlib import Path

import click


@click.command()
@click.argument("contract_file", type=click.Path(exists=True))
@click.argument("impl_spec_file", type=click.Path(exists=True))
@click.option("--plan-only", is_flag=True, help="Show the generation plan without executing")
@click.option("--force", is_flag=True, help="Overwrite existing module if it exists")
@click.option("--yes", "-y", is_flag=True, help="Automatically confirm generation (non-interactive mode)")
@click.option("--output-dir", type=click.Path(), default="amplifier", help="Base output directory")
def main(contract_file: str, impl_spec_file: str, plan_only: bool, force: bool, yes: bool, output_dir: str) -> None:
    """Generate code modules from contract and implementation specifications.

    Args:
        CONTRACT_FILE: Path to the contract specification markdown file
        IMPL_SPEC_FILE: Path to the implementation specification markdown file
    """
    try:
        # Run the async generator
        asyncio.run(generate_module(contract_file, impl_spec_file, plan_only, force, output_dir, yes))
    except KeyboardInterrupt:
        click.echo("\nGeneration cancelled by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


async def generate_module(
    contract_file: str, impl_spec_file: str, plan_only: bool, force: bool, output_dir: str, yes: bool = False
) -> None:
    """Generate a module from specifications."""
    from .generator import ModuleGenerator

    # Initialize generator
    generator = ModuleGenerator(output_dir=Path(output_dir))

    # Read specification files
    contract_path = Path(contract_file)
    impl_path = Path(impl_spec_file)

    click.echo(f"Reading contract from: {contract_path}")
    click.echo(f"Reading implementation spec from: {impl_path}")

    contract_content = contract_path.read_text()
    impl_content = impl_path.read_text()

    # Extract module name from contract
    module_name = generator.extract_module_name(contract_content)
    if not module_name:
        click.echo("Error: Could not extract module name from contract", err=True)
        sys.exit(1)

    click.echo(f"\nModule name: {module_name}")

    # Check if module already exists
    module_path = Path(output_dir) / module_name
    if module_path.exists() and not force:
        click.echo(f"Error: Module {module_path} already exists. Use --force to overwrite.", err=True)
        sys.exit(1)

    # Generate plan
    click.echo("\nGenerating implementation plan...")
    plan = await generator.generate_plan(contract_content, impl_content)

    if not plan:
        click.echo("Error: Failed to generate plan", err=True)
        sys.exit(1)

    click.echo("\n" + "=" * 60)
    click.echo("IMPLEMENTATION PLAN")
    click.echo("=" * 60)
    click.echo(plan)
    click.echo("=" * 60 + "\n")

    if plan_only:
        click.echo("Plan-only mode: Exiting without generating code")
        return

    # Confirm generation (skip if --yes flag is used)
    if not yes and not click.confirm("Proceed with code generation?"):
        click.echo("Generation cancelled")
        return

    # Generate the module
    click.echo(f"\nGenerating module in {module_path}...")
    success = await generator.generate_module(module_name, contract_content, impl_content, plan, force)

    if success:
        click.echo(f"\n✓ Module successfully generated at: {module_path}")
        click.echo("\nNext steps:")
        click.echo(f"  1. Review the generated code in {module_path}/")
        click.echo(f"  2. Run tests: cd {module_path} && pytest")
        click.echo("  3. Check types: make check")
    else:
        click.echo("\n✗ Module generation failed", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
