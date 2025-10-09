#!/usr/bin/env python3
"""
Aider Regenerator - AI-powered module regeneration tool.

This tool provides AI-powered code regeneration capabilities using Aider,
enabling automated module regeneration based on specifications.
"""

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class AiderRegenerator:
    """AI-powered module regeneration using Aider."""

    def __init__(self, venv_path: Path = Path(".aider-venv")):
        """Initialize the Aider regenerator.

        Args:
            venv_path: Path to the Aider virtual environment
        """
        self.venv_path = venv_path
        self.aider_cmd = self.venv_path / "bin" / "aider"

        if not self.aider_cmd.exists():
            raise RuntimeError(f"Aider not found at {self.aider_cmd}. Please run scripts/setup-aider.sh first.")

    def regenerate_module(
        self,
        module_path: Path,
        spec_path: Path | None = None,
        philosophy: str = "fractalized",
        auto_commit: bool = False,
        model: str = "claude-3-5-sonnet-20241022",
    ) -> bool:
        """Regenerate a module using AI based on its specification.

        Args:
            module_path: Path to the module to regenerate
            spec_path: Optional path to specification file
            philosophy: Philosophy to follow (fractalized, modular, zen)
            auto_commit: Whether to auto-commit changes
            model: AI model to use

        Returns:
            True if regeneration succeeded
        """
        if not module_path.exists():
            logger.error(f"Module not found: {module_path}")
            return False

        # Build the prompt based on philosophy
        prompt = self._build_prompt(module_path, spec_path, philosophy)

        # Prepare Aider command
        cmd = [
            str(self.aider_cmd),
            "--model",
            model,
            "--yes-always",  # Auto-approve changes
            "--no-auto-commits" if not auto_commit else "--auto-commits",
            str(module_path),
        ]

        if spec_path and spec_path.exists():
            cmd.append(str(spec_path))

        # Add the prompt via stdin
        logger.info(f"Regenerating {module_path.name} with {philosophy} philosophy...")

        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                text=True,
                capture_output=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                logger.info(f"Successfully regenerated {module_path.name}")
                return True
            logger.error(f"Aider failed: {result.stderr}")
            return False

        except subprocess.TimeoutExpired:
            logger.error("Aider timed out after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"Error running Aider: {e}")
            return False

    def _build_prompt(self, module_path: Path, spec_path: Path | None, philosophy: str) -> str:
        """Build the regeneration prompt based on philosophy.

        Args:
            module_path: Path to the module
            spec_path: Optional specification file
            philosophy: Philosophy to follow

        Returns:
            The prompt string for Aider
        """
        prompts = {
            "fractalized": (
                "Regenerate this module following the Fractalized Thinking philosophy:\n"
                "1. Start with the smallest, simplest working piece\n"
                "2. Patiently untangle complexity thread by thread\n"
                "3. Build bridges between simple components\n"
                "4. Let patterns emerge naturally\n\n"
            ),
            "modular": (
                "Regenerate this module following the Modular philosophy:\n"
                "1. Create self-contained bricks with clear studs (interfaces)\n"
                "2. Each brick has one clear responsibility\n"
                "3. Contracts are stable, implementations can change\n"
                "4. Prefer regeneration over patching\n\n"
            ),
            "zen": (
                "Regenerate this module following the Zen philosophy:\n"
                "1. Ruthless simplicity - remove everything unnecessary\n"
                "2. Direct solutions without unnecessary abstractions\n"
                "3. Trust in emergence from simple components\n"
                "4. Handle only what's needed now\n\n"
            ),
        }

        base_prompt = prompts.get(philosophy, prompts["fractalized"])

        if spec_path and spec_path.exists():
            spec_content = spec_path.read_text()
            base_prompt += f"Follow this specification:\n{spec_content}\n\n"

        base_prompt += f"Regenerate the module at {module_path} to be cleaner, simpler, and more maintainable."

        return base_prompt

    def batch_regenerate(
        self,
        modules: list[Path],
        philosophy: str = "fractalized",
        auto_commit: bool = False,
        model: str = "claude-3-5-sonnet-20241022",
    ) -> dict[str, bool]:
        """Regenerate multiple modules in sequence.

        Args:
            modules: List of module paths to regenerate
            philosophy: Philosophy to follow
            auto_commit: Whether to auto-commit changes
            model: AI model to use

        Returns:
            Dictionary mapping module paths to success status
        """
        results = {}

        for module in modules:
            logger.info(f"Processing {module}...")
            success = self.regenerate_module(
                module,
                philosophy=philosophy,
                auto_commit=auto_commit,
                model=model,
            )
            results[str(module)] = success

            if not success:
                logger.warning(f"Failed to regenerate {module}, continuing...")

        # Summary
        successful = sum(1 for s in results.values() if s)
        logger.info(f"Regenerated {successful}/{len(modules)} modules successfully")

        return results


def main():
    """CLI entry point for direct usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Regenerate modules using AI")
    parser.add_argument("modules", nargs="+", help="Module files to regenerate")
    parser.add_argument(
        "--philosophy",
        choices=["fractalized", "modular", "zen"],
        default="fractalized",
        help="Philosophy to follow",
    )
    parser.add_argument(
        "--spec",
        help="Path to specification file",
    )
    parser.add_argument(
        "--auto-commit",
        action="store_true",
        help="Auto-commit changes",
    )
    parser.add_argument(
        "--model",
        default="claude-3-5-sonnet-20241022",
        help="AI model to use",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Initialize regenerator
    try:
        regenerator = AiderRegenerator()
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)

    # Process modules
    modules = [Path(m) for m in args.modules]

    if len(modules) == 1 and args.spec:
        # Single module with spec
        success = regenerator.regenerate_module(
            modules[0],
            spec_path=Path(args.spec) if args.spec else None,
            philosophy=args.philosophy,
            auto_commit=args.auto_commit,
            model=args.model,
        )
        sys.exit(0 if success else 1)
    else:
        # Batch regeneration
        results = regenerator.batch_regenerate(
            modules,
            philosophy=args.philosophy,
            auto_commit=args.auto_commit,
            model=args.model,
        )

        # Exit with error if any failed
        sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()
