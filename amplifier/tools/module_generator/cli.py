"""CLI for module generator

Command-line interface for generating modules from specifications.
"""

import asyncio
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path

import click

from .generator import ModuleGenerator
from .parser import SpecificationParser
from .validator import ModuleValidator


@click.group()
def cli():
    """Module generator CLI"""
    pass


@cli.command()
@click.argument("contract", type=click.Path(exists=True))
@click.argument("implementation", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="./amplifier", help="Output directory for generated module")
@click.option("--plan-only", "-p", is_flag=True, help="Only analyze and plan, don't generate")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing module")
@click.option("--yes", "-y", is_flag=True, help="Auto-confirm generation after planning")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--timeout", "-t", default=300, help="Timeout in seconds for SDK operations (default: 300)")
@click.option("--skip-validation", is_flag=True, help="Skip validation after generation")
@click.option("--philosophy-path", type=click.Path(exists=True), help="Path to philosophy document")
@click.option("--debug", "-d", is_flag=True, help="Enable debug logging with full SDK request/response output")
@click.option("--log-dir", default="./logs", help="Directory to store log files (default: ./logs)")
def generate(
    contract,
    implementation,
    output_dir,
    plan_only,
    force,
    yes,
    verbose,
    timeout,
    skip_validation,
    philosophy_path,
    debug,
    log_dir,
):
    """Generate a module from contract and implementation specifications

    CONTRACT: Path to contract markdown specification file
    IMPLEMENTATION: Path to implementation markdown specification file
    """
    # Set up logging
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"module_generator_{timestamp}.log"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # File handler - always captures everything
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Console handler - shows info or debug based on flag
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.WARNING)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Log initial info
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info(f"Module Generator Started at {datetime.now().isoformat()}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Contract: {contract}")
    logger.info(f"Implementation: {implementation}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Debug mode: {debug}")
    logger.info("=" * 80)

    # Tell user where logs are being written
    click.echo(f"\n📝 Logs are being written to: {log_file}")
    if debug:
        click.echo("🔍 Debug mode enabled - full SDK interactions will be logged\n")
    else:
        click.echo("💡 Use --debug flag to see full SDK request/response details\n")

    try:
        # Parse both specifications
        if verbose:
            click.echo(f"Parsing contract: {contract}")
            click.echo(f"Parsing implementation: {implementation}")

        from .parser import parse_contract
        from .parser import parse_implementation

        contract_spec = asyncio.run(parse_contract(Path(contract)))
        impl_spec = asyncio.run(parse_implementation(Path(implementation)))

        if verbose:
            click.echo(f"Module: {contract_spec.module_name}")
            click.echo(f"Purpose: {contract_spec.purpose}")

        # Check if module exists
        output_path = Path(output_dir)
        module_name = contract_spec.module_name.replace("_", "-")
        module_path = output_path / module_name

        if module_path.exists() and not force:
            click.echo(f"Error: Module already exists at {module_path}")
            click.echo("Use --force to overwrite")
            return

        # Determine permission mode
        permission_mode = "plan" if plan_only else "acceptEdits"

        # Convert philosophy path if provided
        philosophy = Path(philosophy_path) if philosophy_path else None

        # Create generator with timeout config
        generator = ModuleGenerator(
            output_dir=output_dir,
            permission_mode=permission_mode,
            timeout_seconds=timeout,
        )

        if verbose:
            click.echo(f"Using timeout: {timeout} seconds")
            if philosophy:
                click.echo(f"Using philosophy document: {philosophy}")

        # Generate module
        click.echo(f"{'Analyzing' if plan_only else 'Generating'} module: {contract_spec.module_name}")
        if not plan_only:
            click.echo(f"Note: Generation may take up to {timeout} seconds for complex modules.")

        # Run async generation
        results = asyncio.run(generator.generate(contract_spec, impl_spec, analyze_only=plan_only))

        # Display results
        if results.get("analysis"):
            click.echo("\n=== Analysis ===")
            analysis = results["analysis"]
            click.echo(f"Feasibility: {analysis.get('feasibility', 'unknown')}")
            click.echo(f"Estimated files: {analysis.get('estimated_files', 'unknown')}")
            click.echo(f"Approach: {analysis.get('implementation_approach', 'Not analyzed')}")

            if analysis.get("key_challenges"):
                click.echo("\nKey Challenges:")
                for challenge in analysis["key_challenges"]:
                    click.echo(f"  - {challenge}")

            if analysis.get("suggested_patterns"):
                click.echo("\nSuggested Patterns:")
                for pattern in analysis["suggested_patterns"]:
                    click.echo(f"  - {pattern}")

        if not plan_only:
            click.echo("\n=== Generation Results ===")
            click.echo(f"Module path: {results['module_path']}")

            if results["files_generated"]:
                click.echo(f"\nGenerated {len(results['files_generated'])} files:")
                for file_path in results["files_generated"]:
                    click.echo(f"  ✓ {file_path}")

            if results["tests_generated"]:
                click.echo(f"\nGenerated {len(results['tests_generated'])} tests:")
                for test_path in results["tests_generated"]:
                    click.echo(f"  ✓ {test_path}")

        if results.get("errors"):
            click.echo("\n=== Errors ===")
            for error in results["errors"]:
                click.echo(f"  ✗ {error}", err=True)

        # Run validation if enabled and generation succeeded
        if not plan_only and not results.get("errors") and not skip_validation:
            click.echo("\n=== Running Validation ===")
            module_path = Path(results["module_path"])
            if module_path.exists():
                validator = ModuleValidator(module_path)
                validation_results = validator.validate_all(skip_tests=False)

                # Show summary
                summary = validation_results.summary
                click.echo(
                    f"  Syntax: {'✓' if summary['syntax']['passed'] else '✗'} ({summary['syntax']['total']} checks)"
                )
                click.echo(
                    f"  Contract: {'✓' if summary['contract']['passed'] else '✗'} ({summary['contract']['total']} checks)"
                )
                click.echo(
                    f"  Tests: {'✓' if summary['tests']['passed'] else '✗'} ({summary['tests']['total']} checks)"
                )

                if not validation_results.all_passed:
                    click.echo("\n⚠️  Some validation checks failed. Review the generated code.")
                    if verbose:
                        # Show detailed failures
                        all_results = (
                            validation_results.syntax_results
                            + validation_results.contract_results
                            + validation_results.test_results
                        )
                        for result in all_results:
                            if not result.passed:
                                click.echo(f"  ✗ {result.message}", err=True)

        # Success message
        if not plan_only and not results.get("errors"):
            click.echo(f"\n✨ Module '{contract_spec.module_name}' generated successfully!")
            click.echo(f"Location: {results['module_path']}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()


@cli.command()
@click.argument("spec_file", type=click.Path(exists=True))
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
def parse(spec_file, output_json):
    """Parse and display a specification file

    SPEC_FILE: Path to markdown specification file
    """
    try:
        parser = SpecificationParser()
        spec = parser.parse_file(spec_file)

        if output_json:
            click.echo(spec.model_dump_json(indent=2))
        else:
            click.echo(f"Module: {spec.name}")
            click.echo(f"Path: {spec.path}")
            click.echo(f"Purpose: {spec.purpose}")
            click.echo(f"\nFiles ({len(spec.files)}):")
            for file_spec in spec.files:
                click.echo(f"  - {file_spec.filename}: {file_spec.purpose}")
                if file_spec.public_interface:
                    click.echo(f"    Exports: {', '.join(file_spec.public_interface)}")

            click.echo(f"\nTests ({len(spec.tests)}):")
            for test_spec in spec.tests:
                click.echo(f"  - {test_spec.filename}: {test_spec.description}")

            if spec.external_deps:
                click.echo("\nExternal Dependencies:")
                for dep in spec.external_deps:
                    click.echo(f"  - {dep}")

            if spec.internal_deps:
                click.echo("\nInternal Dependencies:")
                for dep in spec.internal_deps:
                    click.echo(f"  - {dep}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.argument("module_dir", type=click.Path(exists=True))
@click.option("--skip-tests", is_flag=True, help="Skip test execution")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def validate(module_dir, skip_tests, verbose):
    """Validate a generated module

    MODULE_DIR: Path to generated module directory
    """
    module_path = Path(module_dir)

    click.echo(f"Validating module: {module_path}")

    try:
        validator = ModuleValidator(module_path)
        results = validator.validate_all(skip_tests=skip_tests)

        # Display results
        click.echo("\n=== Syntax Validation ===")
        for result in results.syntax_results:
            status = "✓" if result.passed else "✗"
            if verbose or not result.passed:
                click.echo(f"  {status} {result.message}")

        click.echo("\n=== Contract Validation ===")
        for result in results.contract_results:
            status = "✓" if result.passed else "✗"
            click.echo(f"  {status} {result.message}")

        if not skip_tests and results.test_results:
            click.echo("\n=== Test Validation ===")
            for result in results.test_results:
                status = "✓" if result.passed else "✗"
                click.echo(f"  {status} {result.message}")
                if verbose and not result.passed and "details" in result.__dict__ and "stderr" in result.details:
                    click.echo(f"    Error output:\n{result.details['stderr'][:500]}")

        # Summary
        click.echo("\n=== Summary ===")
        summary = results.summary
        click.echo(
            f"  Syntax: {'✓ PASSED' if summary['syntax']['passed'] else '✗ FAILED'} ({summary['syntax']['total']} checks)"
        )
        click.echo(
            f"  Contract: {'✓ PASSED' if summary['contract']['passed'] else '✗ FAILED'} ({summary['contract']['total']} checks)"
        )
        if not skip_tests and summary["tests"]["total"] > 0:
            click.echo(
                f"  Tests: {'✓ PASSED' if summary['tests']['passed'] else '✗ FAILED'} ({summary['tests']['total']} checks)"
            )

        if results.all_passed:
            click.echo("\n✨ Module validation passed!")
        else:
            click.echo("\n⚠️  Module validation failed")
            return 1  # Exit with error code

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


# Create the main command for use as entry point
generate_command = cli


if __name__ == "__main__":
    cli()
