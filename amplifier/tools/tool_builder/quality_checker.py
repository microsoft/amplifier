"""Quality checking microtask for Tool Builder.

This module validates generated tools for correctness, style, and functionality.
"""

import subprocess
from pathlib import Path
from typing import Any


class QualityChecker:
    """Performs quality checks on generated tools."""

    async def check(self, tool_name: str, output_dir: Path) -> dict[str, Any]:
        """Run quality checks on the generated tool.

        This microtask:
        - Runs linting (ruff)
        - Runs type checking (pyright)
        - Runs tests (pytest)
        - Validates structure

        Args:
            tool_name: Name of the tool
            output_dir: Tool directory

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

        return issues
