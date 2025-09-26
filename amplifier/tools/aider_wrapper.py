#!/usr/bin/env python3
"""
Wrapper for Aider CLI tool integration with Amplifier.
Calls Aider from its separate virtual environment to avoid dependency conflicts.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class AiderWrapper:
    """Wrapper to execute Aider commands from separate environment."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.aider_venv = self.project_root / ".aider-venv"
        self.aider_path = self.aider_venv / "bin" / "aider"

        if not self.aider_path.exists():
            raise RuntimeError("Aider not found. Please run: ./scripts/setup-aider.sh")

    def run(
        self,
        files: list[str],
        message: str | None = None,
        model: str = "claude-3-5-sonnet-20241022",
        additional_args: list[str] | None = None,
        env_vars: dict[str, str] | None = None,
        working_dir: Path | None = None,
    ) -> subprocess.CompletedProcess:
        """
        Run Aider with specified parameters.

        Args:
            files: List of files to edit
            message: Instruction message for the AI
            model: AI model to use
            additional_args: Additional command line arguments
            env_vars: Additional environment variables
            working_dir: Working directory for command execution
        """
        cmd = [str(self.aider_path)]

        # Add model
        cmd.extend(["--model", model])

        # Add files
        cmd.extend(files)

        # Add message if provided
        if message:
            cmd.extend(["--message", message])

        # Add any additional arguments
        if additional_args:
            cmd.extend(additional_args)

        # Prepare environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # Execute
        logger.info(f"Running Aider: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=working_dir or self.project_root)

        return result

    def regenerate_module(self, module_path: str, spec_path: str | None = None, instruction: str | None = None) -> bool:
        """
        Regenerate a module based on its specification.

        Args:
            module_path: Path to the module to regenerate
            spec_path: Path to the specification file (optional)
            instruction: Custom regeneration instruction (optional)

        Returns:
            True if successful, False otherwise
        """
        files = [module_path]
        if spec_path:
            files.append(spec_path)

        # Build regeneration instruction
        if not instruction:
            instruction = (
                "Regenerate this module following the modular design philosophy. "
                "Maintain the same interface contracts but improve the implementation. "
                "Focus on simplicity, clarity, and the fractalized thinking approach."
            )
            if spec_path:
                instruction += f" Follow the specification in {spec_path}."

        result = self.run(files=files, message=instruction, additional_args=["--no-auto-commits", "--yes"])

        if result.returncode == 0:
            logger.info(f"Successfully regenerated {module_path}")
            return True
        logger.error(f"Failed to regenerate {module_path}: {result.stderr}")
        return False


def main():
    """CLI interface for testing the wrapper."""
    import argparse

    parser = argparse.ArgumentParser(description="Aider wrapper for Amplifier")
    parser.add_argument("files", nargs="+", help="Files to edit")
    parser.add_argument("-m", "--message", help="Instruction message")
    parser.add_argument("--model", default="claude-3-5-sonnet-20241022", help="AI model")
    parser.add_argument("--regenerate", action="store_true", help="Regenerate module mode")

    args = parser.parse_args()

    wrapper = AiderWrapper()

    if args.regenerate:
        # Regenerate mode
        for file in args.files:
            wrapper.regenerate_module(file, instruction=args.message)
    else:
        # Normal mode
        result = wrapper.run(files=args.files, message=args.message, model=args.model)

        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
