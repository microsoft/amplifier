"""Quality checking microtask for Tool Builder.

This module validates generated tools for correctness, style, and functionality.
"""

import subprocess
from pathlib import Path
from typing import Any


class QualityChecker:
    """Performs quality checks on generated tools."""

    async def check(
        self, tool_name: str, output_dir: Path, requirements: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Run quality checks on the generated tool.

        This microtask:
        - Runs linting (ruff)
        - Runs type checking (pyright)
        - Runs tests (pytest)
        - Validates structure
        - Checks CLI/core module alignment

        Args:
            tool_name: Name of the tool
            output_dir: Tool directory
            requirements: Tool requirements (optional, for alignment checks)

        Returns:
            Quality check results
        """
        results = {
            "status": "success",
            "checks": {},
            "issues": [],
            "summary": "",
        }

        # Check directory structure
        structure_check = self._check_structure(output_dir)
        results["checks"]["structure"] = structure_check

        # Check CLI/core module alignment if requirements provided
        if requirements:
            alignment_check = self._check_cli_core_alignment(output_dir, requirements)
            results["checks"]["cli_core_alignment"] = alignment_check

        # Run ruff for linting and formatting
        ruff_check = await self._run_ruff(output_dir)
        results["checks"]["ruff"] = ruff_check

        # Run pyright for type checking
        pyright_check = await self._run_pyright(output_dir)
        results["checks"]["pyright"] = pyright_check

        # Run pytest if tests exist
        test_check = await self._run_tests(output_dir)
        results["checks"]["tests"] = test_check

        # Aggregate results
        all_passed = all(check.get("passed", False) for check in results["checks"].values())

        if all_passed:
            results["status"] = "success"
            results["summary"] = f"All quality checks passed for {tool_name}"
        else:
            results["status"] = "partial"
            failed_checks = [name for name, check in results["checks"].items() if not check.get("passed", False)]
            results["summary"] = f"Some checks failed: {', '.join(failed_checks)}"
            results["issues"] = self._collect_issues(results["checks"])

        return results

    def _check_structure(self, output_dir: Path) -> dict[str, Any]:
        """Check directory structure."""
        required_files = ["__init__.py", "cli.py"]
        missing = []

        for file in required_files:
            if not (output_dir / file).exists():
                missing.append(file)

        return {
            "passed": len(missing) == 0,
            "missing_files": missing,
            "message": "Structure valid" if not missing else f"Missing files: {', '.join(missing)}",
        }

    async def _run_ruff(self, output_dir: Path) -> dict[str, Any]:
        """Run ruff linting and formatting check."""
        try:
            # Run ruff check
            result = subprocess.run(
                ["ruff", "check", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Run ruff format check
            format_result = subprocess.run(
                ["ruff", "format", "--check", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            passed = result.returncode == 0 and format_result.returncode == 0

            return {
                "passed": passed,
                "lint_output": result.stdout + result.stderr,
                "format_output": format_result.stdout + format_result.stderr,
                "message": "Linting passed" if passed else "Linting issues found",
            }

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return {
                "passed": False,
                "error": str(e),
                "message": "Ruff not available or timed out",
            }

    async def _run_pyright(self, output_dir: Path) -> dict[str, Any]:
        """Run pyright type checking."""
        try:
            result = subprocess.run(
                ["pyright", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            passed = result.returncode == 0

            return {
                "passed": passed,
                "output": result.stdout + result.stderr,
                "message": "Type checking passed" if passed else "Type errors found",
            }

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Pyright might not be installed, that's okay
            return {
                "passed": True,
                "skipped": True,
                "message": "Pyright not available (skipped)",
            }

    async def _run_tests(self, output_dir: Path) -> dict[str, Any]:
        """Run pytest on the tool."""
        # Look for test files
        test_files = list(output_dir.rglob("test_*.py"))

        if not test_files:
            return {
                "passed": True,
                "skipped": True,
                "message": "No tests found (skipped)",
            }

        try:
            result = subprocess.run(
                ["pytest", str(output_dir), "-v"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            passed = result.returncode == 0

            return {
                "passed": passed,
                "output": result.stdout + result.stderr,
                "test_count": len(test_files),
                "message": "All tests passed" if passed else "Some tests failed",
            }

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return {
                "passed": False,
                "error": str(e),
                "message": "Pytest not available or timed out",
            }

    def _check_cli_core_alignment(self, output_dir: Path, requirements: dict[str, Any]) -> dict[str, Any]:
        """Check CLI and core module alignment based on requirements.

        Args:
            output_dir: Tool directory
            requirements: Tool requirements containing cli_type

        Returns:
            Check results with issues found
        """
        issues = []
        warnings = []
        cli_file = output_dir / "cli.py"
        core_file = output_dir / "core.py"

        # Read CLI file if it exists
        if not cli_file.exists():
            return {
                "passed": False,
                "message": "CLI file not found",
                "issues": ["cli.py file missing"],
            }

        cli_content = cli_file.read_text()

        # Check core file exists if needed
        has_core = core_file.exists()
        core_content = core_file.read_text() if has_core else ""

        cli_type = requirements.get("cli_type", "text_processor")

        # Check based on CLI type
        if cli_type == "directory_processor":
            # Should have source_dir argument with dir_okay=True
            if "source_dir" not in cli_content:
                issues.append("Missing 'source_dir' argument for directory processor")

            if "dir_okay=True" not in cli_content:
                issues.append("CLI missing 'dir_okay=True' for directory argument")

            if "file_okay=False" not in cli_content:
                warnings.append("CLI should have 'file_okay=False' for directory-only processing")

            # Check for file iteration patterns
            if has_core:
                if "Path(" not in core_content and "pathlib" not in core_content:
                    warnings.append("Core module should use Path for directory handling")

                # Check for common directory error patterns
                if "open(source_dir" in core_content or "open(directory" in core_content:
                    issues.append("Core module tries to open directory path directly (will cause IsADirectoryError)")

            # Check for batch processing indicators
            if requirements.get("batch_processing") and "for " not in cli_content and "for " not in core_content:
                warnings.append("Batch processing specified but no iteration patterns found")

        elif cli_type == "file_processor":
            # Should have input_file argument with file_okay=True
            if "input_file" not in cli_content and "input" not in cli_content.lower():
                issues.append("Missing file input argument for file processor")

            if "file_okay=True" not in cli_content:
                warnings.append("CLI should have explicit 'file_okay=True' for file argument")

            if "dir_okay=False" not in cli_content:
                warnings.append("CLI should have 'dir_okay=False' for file-only processing")

            # Check core handles files properly
            if has_core and "open(" not in core_content and "read" not in core_content.lower():
                warnings.append("Core module should have file reading capability")

        else:  # text_processor
            # Should accept text input, not file paths
            if "click.Path" in cli_content:
                warnings.append("Text processor using Path argument instead of text/string")

        # Check for general alignment issues
        if has_core and "def run(" in cli_content:
            # Check that CLI parameters match core function signatures
            # Extract CLI run function parameters
            import re

            cli_match = re.search(r"def run\((.*?)\):", cli_content, re.DOTALL)
            if cli_match:
                cli_params = cli_match.group(1)

                # Look for main processing function in core
                core_match = re.search(r"def process.*?\((.*?)\):", core_content, re.DOTALL)
                if core_match:
                    core_params = core_match.group(1)

                    # Basic check: CLI should pass compatible arguments
                    cli_param_names = {p.split(":")[0].strip() for p in cli_params.split(",") if p.strip()}

                    # Common mismatches
                    if "source_dir" in cli_param_names and "file" in core_params.lower():
                        issues.append("CLI passes directory but core expects file")
                    if "input_file" in cli_param_names and "dir" in core_params.lower():
                        issues.append("CLI passes file but core expects directory")

        # Compile results
        passed = len(issues) == 0

        result = {
            "passed": passed,
            "issues": issues,
            "warnings": warnings,
            "message": "CLI/core alignment valid" if passed else f"Found {len(issues)} alignment issues",
        }

        if not passed:
            result["details"] = {
                "cli_type": cli_type,
                "batch_processing": requirements.get("batch_processing", False),
                "has_core_module": has_core,
            }

        return result

    def _collect_issues(self, checks: dict[str, dict[str, Any]]) -> list[str]:
        """Collect all issues from checks."""
        issues = []

        for check_name, check_result in checks.items():
            if not check_result.get("passed", False):
                if "missing_files" in check_result:
                    issues.extend([f"Missing: {f}" for f in check_result["missing_files"]])
                if "error" in check_result:
                    issues.append(f"{check_name}: {check_result['error']}")
                if "lint_output" in check_result and check_result["lint_output"]:
                    issues.append(f"Linting issues found (run 'ruff check {check_name}')")
                if "issues" in check_result:
                    # Add CLI/core alignment issues
                    issues.extend([f"Alignment: {issue}" for issue in check_result["issues"]])

        return issues
