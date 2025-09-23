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
@click.option("--session-file", type=click.Path(), help="Session persistence file for resume capability")
@click.option("--resume", is_flag=True, help="Resume from previous session if available")
@click.option("--use-v2", is_flag=True, default=True, help="Use new CCSDK toolkit-based generator (default)")
@click.option("--use-v1", is_flag=True, help="Use legacy generator (deprecated)")
def main(
    contract_file: str,
    impl_spec_file: str,
    plan_only: bool,
    force: bool,
    yes: bool,
    output_dir: str,
    session_file: str | None,
    resume: bool,
    use_v2: bool,
    use_v1: bool,
) -> None:
    """Generate code modules from contract and implementation specifications.

    Args:
        CONTRACT_FILE: Path to the contract specification markdown file
        IMPL_SPEC_FILE: Path to the implementation specification markdown file
    """
    # Determine which generator to use
    if use_v1:
        use_new_generator = False
    else:
        use_new_generator = True  # Default to v2

    try:
        # Run the async generator
        asyncio.run(
            generate_module(
                contract_file,
                impl_spec_file,
                plan_only,
                force,
                output_dir,
                yes,
                session_file,
                resume,
                use_new_generator,
            )
        )
    except KeyboardInterrupt:
        click.echo("\nGeneration cancelled by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


async def generate_module(
    contract_file: str,
    impl_spec_file: str,
    plan_only: bool,
    force: bool,
    output_dir: str,
    yes: bool = False,
    session_file: str | None = None,
    resume: bool = False,
    use_new_generator: bool = True,
) -> None:
    """Generate a module from specifications."""

    # Choose generator based on flag
    if use_new_generator:
        from .generator_v2 import ModuleGeneratorV2

        # Initialize new generator with session support
        session_path = Path(session_file) if session_file else None
        generator_v2 = ModuleGeneratorV2(output_dir=Path(output_dir), session_file=session_path)
        generator = generator_v2  # type: ignore
    else:
        from .generator import ModuleGenerator

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

    # Check if using new generator with session support
    if use_new_generator:
        # Use session-based generation (we know generator is ModuleGeneratorV2)
        from .generator_v2 import ModuleGeneratorV2

        assert isinstance(generator, ModuleGeneratorV2)  # Type hint for pyright

        if plan_only:
            # Just generate and show the plan
            plan = await generator.generate_plan(contract_content, impl_content)
            if not plan:
                click.echo("Error: Failed to generate plan", err=True)
                sys.exit(1)

            click.echo("\n" + "=" * 60)
            click.echo("IMPLEMENTATION PLAN")
            click.echo("=" * 60)
            click.echo(plan)
            click.echo("=" * 60 + "\n")
            return

        # Generate with session
        success = await generator.generate_with_session(module_name, contract_content, impl_content, force, resume)
    else:
        # Use legacy generator
        from .generator import ModuleGenerator

        assert isinstance(generator, ModuleGenerator)  # Type hint for pyright

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
        module_path = Path(output_dir) / module_name
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
