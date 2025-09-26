#!/usr/bin/env python3
"""
Aider integration for Amplifier - AI-powered code generation and regeneration.
Implements modular code regeneration following the fractalized thinking philosophy.
"""

import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click

logger = logging.getLogger(__name__)


class AiderRegenerator:
    """
    Manages AI-powered code regeneration using Aider.
    Follows the modular design philosophy where modules can be independently regenerated.
    """

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.aider_venv = self.project_root / ".aider-venv"
        self.aider_bin = self.aider_venv / "bin" / "aider"
        self.specs_dir = self.project_root / "ai_working" / "module_specs"
        self.logs_dir = self.project_root / ".aider-logs"
        self.logs_dir.mkdir(exist_ok=True)

        # Check if Aider is installed
        if not self.aider_bin.exists():
            raise RuntimeError("Aider not installed. Please run: ./scripts/setup-aider.sh")

    def run_aider(
        self,
        files: list[str],
        message: str,
        model: str = "claude-3-5-sonnet-20241022",
        additional_args: list[str] | None = None,
        working_dir: Path | None = None,
    ) -> subprocess.CompletedProcess:
        """Execute Aider with specified parameters."""
        cmd = [str(self.aider_bin)]

        # Core arguments
        cmd.extend(["--model", model])
        cmd.extend(["--message", message])

        # Add files
        for file in files:
            cmd.append(str(file))

        # Additional arguments
        if additional_args:
            cmd.extend(additional_args)

        # Log the command
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"aider_{timestamp}.log"

        logger.info(f"Running Aider: {' '.join(cmd)}")
        logger.info(f"Logging to: {log_file}")

        # Execute
        with open(log_file, "w") as log:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=working_dir or self.project_root)
            log.write(f"Command: {' '.join(cmd)}\n")
            log.write(f"Return code: {result.returncode}\n")
            log.write(f"\n--- STDOUT ---\n{result.stdout}\n")
            log.write(f"\n--- STDERR ---\n{result.stderr}\n")

        return result

    def regenerate_module(
        self, module_path: Path, spec_path: Path | None = None, philosophy: str = "fractalized"
    ) -> bool:
        """
        Regenerate a module following its specification.

        Args:
            module_path: Path to the module to regenerate
            spec_path: Optional path to specification file
            philosophy: Which philosophy to follow (fractalized, modular, zen)
        """
        if not module_path.exists():
            logger.error(f"Module not found: {module_path}")
            return False

        # Build the regeneration instruction
        instruction = self._build_regeneration_instruction(module_path, spec_path, philosophy)

        # Files to include
        files = [str(module_path)]
        if spec_path and spec_path.exists():
            files.append(str(spec_path))

        # Add philosophy files
        philosophy_files = self._get_philosophy_files(philosophy)
        files.extend([str(f) for f in philosophy_files if f.exists()])

        # Run Aider
        result = self.run_aider(files=files, message=instruction, additional_args=["--no-auto-commits", "--yes"])

        if result.returncode == 0:
            logger.info(f"✅ Successfully regenerated {module_path}")
            return True
        logger.error(f"❌ Failed to regenerate {module_path}")
        logger.error(result.stderr)
        return False

    def _build_regeneration_instruction(self, module_path: Path, spec_path: Path | None, philosophy: str) -> str:
        """Build the regeneration instruction based on philosophy."""
        base_instruction = f"Regenerate the module in {module_path.name} following these principles:\n\n"

        if philosophy == "fractalized":
            base_instruction += (
                "1. Apply FRACTALIZED THINKING philosophy:\n"
                "   - Find the smallest thread to start with\n"
                "   - Work patiently from simple to complex\n"
                "   - Recognize patterns that scale fractally\n"
                "   - Build bridges that hold creative tensions\n\n"
            )
        elif philosophy == "modular":
            base_instruction += (
                "1. Apply MODULAR DESIGN philosophy:\n"
                "   - Keep modules self-contained with clear interfaces\n"
                "   - Maintain stable connection points (studs)\n"
                "   - Enable independent regeneration\n"
                "   - Focus on single responsibility\n\n"
            )
        else:  # zen
            base_instruction += (
                "1. Apply ZEN ARCHITECTURE philosophy:\n"
                "   - Embrace ruthless simplicity\n"
                "   - Remove all unnecessary complexity\n"
                "   - Trust in emergence over control\n"
                "   - Keep code minimal and clear\n\n"
            )

        base_instruction += (
            "2. Maintain the same external interface/contracts\n"
            "3. Improve internal implementation quality\n"
            "4. Add NO comments unless they explain WHY not WHAT\n"
            "5. Follow existing code patterns in the codebase\n"
        )

        if spec_path and spec_path.exists():
            base_instruction += f"\n6. Follow the specification in {spec_path.name}\n"

        return base_instruction

    def _get_philosophy_files(self, philosophy: str) -> list[Path]:
        """Get relevant philosophy files to include."""
        ai_context = self.project_root / "ai_context"
        files = []

        if philosophy == "fractalized":
            files.extend(
                [ai_context / "FRACTALIZED_THINKING_PHILOSOPHY.md", ai_context / "FRACTALIZED_THINKING_INTEGRATION.md"]
            )
        elif philosophy == "modular":
            files.append(ai_context / "MODULAR_DESIGN_PHILOSOPHY.md")
        else:  # zen
            files.append(ai_context / "IMPLEMENTATION_PHILOSOPHY.md")

        return files

    def batch_regenerate(self, pattern: str, philosophy: str = "fractalized", dry_run: bool = False) -> dict[str, bool]:
        """
        Regenerate multiple modules matching a pattern.

        Args:
            pattern: Glob pattern to match modules
            philosophy: Philosophy to follow
            dry_run: If True, only show what would be regenerated
        """
        modules = list(self.project_root.glob(pattern))
        results = {}

        if dry_run:
            click.echo(f"🔍 Would regenerate {len(modules)} modules:")
            for module in modules:
                click.echo(f"  • {module.relative_to(self.project_root)}")
            return {}

        click.echo(f"🔄 Regenerating {len(modules)} modules...")

        with click.progressbar(modules) as bar:
            for module in bar:
                # Look for corresponding spec
                spec_name = f"{module.stem}_spec.md"
                spec_path = self.specs_dir / spec_name

                success = self.regenerate_module(
                    module_path=module, spec_path=spec_path if spec_path.exists() else None, philosophy=philosophy
                )
                results[str(module)] = success

        # Summary
        successful = sum(1 for s in results.values() if s)
        failed = len(results) - successful

        click.echo(f"\n📊 Results: {successful} succeeded, {failed} failed")

        if failed > 0:
            click.echo("\n❌ Failed modules:")
            for module, success in results.items():
                if not success:
                    click.echo(f"  • {Path(module).name}")

        return results


@click.group()
def cli():
    """Aider integration for AI-powered code generation and regeneration."""
    pass


@cli.command()
@click.argument("module_path", type=click.Path(exists=True))
@click.option("--spec", type=click.Path(exists=True), help="Path to specification file")
@click.option(
    "--philosophy",
    type=click.Choice(["fractalized", "modular", "zen"]),
    default="fractalized",
    help="Philosophy to follow",
)
def regenerate(module_path: str, spec: str | None, philosophy: str):
    """Regenerate a single module using AI."""
    regenerator = AiderRegenerator()

    module = Path(module_path)
    spec_path = Path(spec) if spec else None

    click.echo(f"🔄 Regenerating {module.name} using {philosophy} philosophy...")

    success = regenerator.regenerate_module(module_path=module, spec_path=spec_path, philosophy=philosophy)

    if success:
        click.echo("✅ Regeneration successful!")
    else:
        click.echo("❌ Regeneration failed. Check logs for details.")
        sys.exit(1)


@cli.command()
@click.argument("pattern")
@click.option(
    "--philosophy",
    type=click.Choice(["fractalized", "modular", "zen"]),
    default="fractalized",
    help="Philosophy to follow",
)
@click.option("--dry-run", is_flag=True, help="Show what would be regenerated")
def batch(pattern: str, philosophy: str, dry_run: bool):
    """Regenerate multiple modules matching a pattern."""
    regenerator = AiderRegenerator()

    results = regenerator.batch_regenerate(pattern=pattern, philosophy=philosophy, dry_run=dry_run)

    if not dry_run and results:
        failed_count = sum(1 for s in results.values() if not s)
        if failed_count > 0:
            sys.exit(1)


@cli.command()
@click.argument("files", nargs=-1, required=True, type=click.Path())
@click.option("--message", "-m", required=True, help="Instruction for AI")
@click.option("--model", default="claude-3-5-sonnet-20241022", help="AI model to use")
@click.option("--commit", is_flag=True, help="Auto-commit changes")
def edit(files: tuple, message: str, model: str, commit: bool):
    """Direct Aider interface for general code editing."""
    regenerator = AiderRegenerator()

    additional_args = []
    if not commit:
        additional_args.append("--no-auto-commits")
    additional_args.append("--yes")

    click.echo(f"🤖 Running Aider on {len(files)} file(s)...")

    result = regenerator.run_aider(files=list(files), message=message, model=model, additional_args=additional_args)

    if result.returncode == 0:
        click.echo("✅ Edit completed successfully!")
    else:
        click.echo("❌ Edit failed.")
        sys.exit(1)


@cli.command()
def setup():
    """Set up Aider environment if not already configured."""
    setup_script = Path(__file__).parent.parent.parent / "scripts" / "setup-aider.sh"

    if not setup_script.exists():
        click.echo("❌ Setup script not found!")
        sys.exit(1)

    click.echo("🔧 Running Aider setup...")
    result = subprocess.run([str(setup_script)], capture_output=True, text=True)

    if result.returncode == 0:
        click.echo("✅ Aider setup complete!")
    else:
        click.echo("❌ Setup failed:")
        click.echo(result.stderr)
        sys.exit(1)


@cli.command()
@click.option("--verbose", is_flag=True, help="Show detailed status")
def status(verbose: bool):
    """Check Aider installation status."""
    regenerator = AiderRegenerator()

    click.echo("📊 Aider Status:")
    click.echo(f"  • Project root: {regenerator.project_root}")
    click.echo(f"  • Aider venv: {'✅ Exists' if regenerator.aider_venv.exists() else '❌ Missing'}")
    click.echo(f"  • Aider binary: {'✅ Installed' if regenerator.aider_bin.exists() else '❌ Not installed'}")

    if verbose and regenerator.aider_bin.exists():
        # Check Aider version
        result = subprocess.run([str(regenerator.aider_bin), "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            click.echo(f"  • Version: {result.stdout.strip()}")

    # Check for logs
    if regenerator.logs_dir.exists():
        logs = list(regenerator.logs_dir.glob("*.log"))
        click.echo(f"  • Logs: {len(logs)} file(s)")
        if verbose and logs:
            click.echo("    Recent logs:")
            for log in sorted(logs)[-5:]:
                click.echo(f"      - {log.name}")


if __name__ == "__main__":
    cli()
