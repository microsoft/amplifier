"""CLI entry point for the Module Generator.

Provides commands for generating, validating, and resuming module generation
from contract and implementation specifications.
"""

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn
from rich.table import Table

from module_generator.core.file_io import read_yaml
from module_generator.core.state import GenerationState
from module_generator.orchestrator import ModuleOrchestrator
from module_generator.validators.spec_validator import validate_files

console = Console()


def print_header(text: str) -> None:
    """Print a formatted header."""
    console.print(f"\n[bold blue]{'=' * 60}[/bold blue]")
    console.print(f"[bold cyan]{text}[/bold cyan]")
    console.print(f"[bold blue]{'=' * 60}[/bold blue]\n")


def print_success(text: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {text}")


def print_error(text: str) -> None:
    """Print an error message."""
    console.print(f"[red]✗[/red] {text}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]⚠[/yellow] {text}")


def print_info(text: str) -> None:
    """Print an info message."""
    console.print(f"[blue]ℹ[/blue] {text}")


async def validate_specs(contract_path: Path, spec_path: Path) -> bool:
    """Validate contract and implementation specifications.

    Args:
        contract_path: Path to contract specification
        spec_path: Path to implementation specification

    Returns:
        True if validation passes, False otherwise
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Validate both files together
        task = progress.add_task("Validating contract and specification...", total=None)
        try:
            validation_result = validate_files(contract_path, spec_path)
            progress.update(task, completed=True)

            if validation_result.is_valid:
                print_success(f"Validation passed ({len(validation_result.warnings)} warnings)")
            else:
                print_error("Validation failed")
                for error in validation_result.errors:
                    console.print(f"  [red]• {error}[/red]")

            # Show warnings if any
            for warning in validation_result.warnings:
                print_warning(f"  {warning}")

            # Show token count
            print_info(f"Total token count: {validation_result.token_count:,}")
            if validation_result.token_count > 15000:
                print_error("Token count exceeds 15,000 limit!")
            elif validation_result.token_count > 12000:
                print_warning("Token count is approaching 15,000 limit")

            return validation_result.is_valid

        except Exception as e:
            progress.update(task, completed=True)
            print_error(f"Failed to validate files: {e}")
            return False


def show_generation_summary(contract: dict, spec: dict, output_dir: Path, resume: bool) -> None:
    """Display a summary of what will be generated.

    Args:
        contract: Contract specification
        spec: Implementation specification
        output_dir: Output directory path
        resume: Whether resuming from checkpoint
    """
    table = Table(title="Generation Summary", show_header=True)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    # Extract module info from nested structure
    module_info = contract.get("module", {})
    module_name = module_info.get("name", "unknown")
    module_version = module_info.get("version", "unknown")

    # Count components
    num_functions = len(contract.get("public_interface", {}).get("functions", []))
    num_models = len(contract.get("public_interface", {}).get("models", []))
    num_tests = len(spec.get("test_specifications", []))

    table.add_row("Module Name", module_name)
    table.add_row("Module Version", module_version)
    table.add_row("Output Directory", str(output_dir))
    table.add_row("Mode", "Resume from checkpoint" if resume else "Fresh generation")
    table.add_row("", "")  # Separator
    table.add_row("Public Functions", str(num_functions))
    table.add_row("Data Models", str(num_models))
    table.add_row("Test Specifications", str(num_tests))

    console.print(table)


async def run_generation(
    contract_path: Path, spec_path: Path, output_dir: Path, resume: bool, timeout: int = 300
) -> None:
    """Run the module generation process.

    Args:
        contract_path: Path to contract specification
        spec_path: Path to implementation specification
        output_dir: Output directory for generated module
        resume: Whether to resume from checkpoint
    """
    # Load specifications
    try:
        contract = read_yaml(contract_path)
        spec = read_yaml(spec_path)  # noqa: F841 - Will be used when orchestrator is implemented
    except Exception as e:
        print_error(f"Failed to load specifications: {e}")
        sys.exit(1)

    # Extract module name from nested structure
    module_info = contract.get("module", {})
    module_name = module_info.get("name", "unknown")
    checkpoint_path = output_dir / f".generation_checkpoint_{module_name}.json"

    # Initialize or load state
    if resume and checkpoint_path.exists():
        print_info(f"Resuming from checkpoint: {checkpoint_path}")
        try:
            state = GenerationState.load_or_create(module_name)
            print_success(f"Loaded checkpoint from phase: {state.current_phase}")
        except Exception as e:
            print_error(f"Failed to load checkpoint: {e}")
            print_info("Starting fresh generation instead")
            state = GenerationState(module_name=module_name)
            state.add_artifact("output_path", str(output_dir))
    else:
        if resume:
            print_info("No checkpoint found, starting fresh generation")
        state = GenerationState(module_name=module_name)
        state.add_artifact("output_path", str(output_dir))

    # Call orchestrator to generate the module
    orchestrator = ModuleOrchestrator(state, timeout=timeout)
    try:
        await orchestrator.generate_module(contract_path, spec_path, output_dir)
        print_success(f"Module '{module_name}' generated successfully!")
        print_info(f"Output directory: {output_dir}")
    except Exception as e:
        print_error(f"Generation failed: {e}")
        print_info(f"Checkpoint saved at: {checkpoint_path}")
        print_info("You can resume with: module-generator resume")
        sys.exit(1)


@click.group()
def cli():
    """Module Generator - AI-powered module generation from specifications."""
    pass


@cli.command()
@click.option(
    "--contract",
    "-c",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to contract specification YAML file",
)
@click.option(
    "--spec",
    "-s",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to implementation specification YAML file",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("./generated"),
    help="Output directory for generated module (default: ./generated)",
)
@click.option("--resume/--fresh", default=True, help="Resume from checkpoint if available (default: resume)")
@click.option("--skip-validation", is_flag=True, help="Skip specification validation (not recommended)")
@click.option(
    "--timeout",
    "-t",
    type=click.IntRange(30, 600),
    default=300,
    help="Timeout in seconds for Claude SDK operations (default: 300, range: 30-600)",
)
def generate(contract: Path, spec: Path, output: Path, resume: bool, skip_validation: bool, timeout: int):
    """Generate a module from contract and implementation specifications.

    This command validates the specifications and generates a complete
    module including code, tests, and documentation.
    """
    print_header("Module Generator")

    # Validate specifications unless skipped
    if not skip_validation:
        print_info("Validating specifications...")
        if not asyncio.run(validate_specs(contract, spec)):
            print_error("Validation failed. Fix errors and try again.")
            print_info("Use --skip-validation to bypass (not recommended)")
            sys.exit(1)
        print_success("All validations passed!\n")
    else:
        print_warning("Skipping validation - generation may fail with invalid specs\n")

    # Load specs to show summary
    try:
        contract_data = read_yaml(contract)
        spec_data = read_yaml(spec)
        show_generation_summary(contract_data, spec_data, output, resume)
    except Exception as e:
        print_error(f"Failed to load specifications: {e}")
        sys.exit(1)

    # Confirm generation
    if not click.confirm("\nProceed with generation?", default=True):
        print_info("Generation cancelled")
        sys.exit(0)

    print_header("Starting Generation")

    # Run generation
    asyncio.run(run_generation(contract, spec, output, resume, timeout))


@cli.command()
@click.option(
    "--contract",
    "-c",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to contract specification YAML file",
)
@click.option(
    "--spec",
    "-s",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to implementation specification YAML file",
)
def validate(contract: Path, spec: Path):
    """Validate specifications without generating code.

    This command checks that both contract and implementation
    specifications are valid and compatible.
    """
    print_header("Specification Validator")

    if asyncio.run(validate_specs(contract, spec)):
        print_success("\nAll specifications are valid!")

        # Load and display summary
        try:
            contract_data = read_yaml(contract)
            spec_data = read_yaml(spec)

            console.print("\n[bold]Module Summary:[/bold]")
            module_info = contract_data.get("module", {})
            console.print(f"  Name: {module_info.get('name', 'unknown')}")
            console.print(f"  Version: {module_info.get('version', 'unknown')}")
            console.print(f"  Functions: {len(contract_data.get('public_interface', {}).get('functions', []))}")
            console.print(f"  Models: {len(contract_data.get('public_interface', {}).get('models', []))}")
            console.print(f"  Tests: {len(spec_data.get('test_specifications', []))}")
        except Exception:
            pass  # Ignore summary errors
    else:
        print_error("\nValidation failed. Please fix the errors above.")
        sys.exit(1)


@cli.command()
@click.option(
    "--checkpoint",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to checkpoint file (auto-detected if not specified)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output directory (extracted from checkpoint if not specified)",
)
def resume(checkpoint: Path | None, output: Path | None):
    """Resume generation from a checkpoint.

    This is a convenience command that automatically finds and loads
    the most recent checkpoint to continue generation.
    """
    print_header("Resume Generation")

    # Find checkpoint file
    if checkpoint:
        checkpoint_path = checkpoint
    else:
        # Look for checkpoint files in current directory and ./generated
        search_dirs = [Path("."), Path("./generated")]
        checkpoint_files = []

        for search_dir in search_dirs:
            if search_dir.exists():
                checkpoint_files.extend(search_dir.glob(".generation_checkpoint_*.json"))

        if not checkpoint_files:
            print_error("No checkpoint files found")
            print_info("Specify checkpoint with --checkpoint or run from directory with checkpoints")
            sys.exit(1)

        # Use most recent checkpoint
        checkpoint_path = max(checkpoint_files, key=lambda p: p.stat().st_mtime)
        print_info(f"Found checkpoint: {checkpoint_path}")

    # Load checkpoint to get state
    try:
        state = GenerationState.load_or_create(checkpoint_path.stem.replace(".generation_checkpoint_", ""))
        print_success(f"Loaded checkpoint for module: {state.module_name}")
        print_info(f"Current phase: {state.current_phase}")
        completed_phases = state.completed_phases
        print_info(f"Progress: {len(completed_phases)} phases completed")

        if output:
            state.add_artifact("output_dir", str(output))
            print_info(f"Output directory updated to: {output}")

        output_dir = Path(state.get_artifact("output_dir") or output or ".")

    except Exception as e:
        print_error(f"Failed to load checkpoint: {e}")
        sys.exit(1)

    # Find original specification files
    # This is a simplified version - in practice, we'd store paths in checkpoint
    print_warning("Original specification files must be provided manually")
    print_info("In future versions, these will be stored in the checkpoint")

    contract_path = click.prompt("Contract specification path", type=click.Path(exists=True, path_type=Path))
    spec_path = click.prompt("Implementation specification path", type=click.Path(exists=True, path_type=Path))

    # Confirm resumption
    if not click.confirm("\nResume generation from checkpoint?", default=True):
        print_info("Resume cancelled")
        sys.exit(0)

    print_header("Resuming Generation")

    # Run generation with resume=True
    asyncio.run(run_generation(Path(contract_path), Path(spec_path), output_dir, resume=True, timeout=300))


@cli.command()
def version():
    """Display version information."""
    console.print("[bold]Module Generator[/bold] version 0.1.0")
    console.print("AI-powered module generation from specifications")
    console.print("\nFor more information: https://github.com/your-org/module-generator")


if __name__ == "__main__":
    cli()
