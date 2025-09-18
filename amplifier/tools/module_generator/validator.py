"""Module validation framework

Validates generated modules for syntax, contract compliance, and test execution.
"""

import ast
import subprocess
import sys
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any


@dataclass
class ValidationResult:
    """Result of a single validation check"""

    check_name: str
    passed: bool
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResults:
    """Container for all validation results"""

    syntax_results: list[ValidationResult] = field(default_factory=list)
    contract_results: list[ValidationResult] = field(default_factory=list)
    test_results: list[ValidationResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        """Check if all validations passed"""
        all_results = self.syntax_results + self.contract_results + self.test_results
        return all(r.passed for r in all_results)

    @property
    def summary(self) -> dict[str, Any]:
        """Get summary of validation results"""
        return {
            "syntax": {"passed": all(r.passed for r in self.syntax_results), "total": len(self.syntax_results)},
            "contract": {"passed": all(r.passed for r in self.contract_results), "total": len(self.contract_results)},
            "tests": {"passed": all(r.passed for r in self.test_results), "total": len(self.test_results)},
            "overall_passed": self.all_passed,
        }


class ModuleValidator:
    """Validate generated modules"""

    def __init__(self, module_path: Path):
        """Initialize validator

        Args:
            module_path: Path to the module directory
        """
        self.module_path = Path(module_path)
        if not self.module_path.exists():
            raise ValueError(f"Module path does not exist: {module_path}")

    def validate_all(self, skip_tests: bool = False) -> ValidationResults:
        """Run all validation checks

        Args:
            skip_tests: Skip test execution validation

        Returns:
            Combined validation results
        """
        results = ValidationResults()

        # Validate syntax
        results.syntax_results = self.validate_syntax()

        # Validate contract
        results.contract_results = self.validate_contract()

        # Validate tests (if not skipped)
        if not skip_tests:
            results.test_results = self.validate_tests()

        return results

    def validate_syntax(self) -> list[ValidationResult]:
        """Validate Python syntax for all .py files

        Returns:
            List of validation results
        """
        results = []
        py_files = list(self.module_path.rglob("*.py"))

        if not py_files:
            results.append(ValidationResult("python_files_exist", False, "No Python files found"))
            return results

        for py_file in py_files:
            relative_path = py_file.relative_to(self.module_path)
            try:
                with open(py_file, encoding="utf-8") as f:
                    code = f.read()

                # Try to compile the code
                compile(code, str(py_file), "exec")

                # Try to parse as AST for more detailed checks
                ast.parse(code)

                results.append(
                    ValidationResult(f"syntax_{relative_path}", True, f"{relative_path}: Valid Python syntax")
                )

            except SyntaxError as e:
                results.append(
                    ValidationResult(
                        f"syntax_{relative_path}",
                        False,
                        f"{relative_path}: Syntax error at line {e.lineno}: {e.msg}",
                        {"error": str(e), "line": e.lineno},
                    )
                )
            except Exception as e:
                results.append(
                    ValidationResult(
                        f"syntax_{relative_path}",
                        False,
                        f"{relative_path}: Validation error: {str(e)}",
                        {"error": str(e)},
                    )
                )

        return results

    def validate_contract(self) -> list[ValidationResult]:
        """Validate module contract compliance

        Returns:
            List of validation results
        """
        results = []

        # Check for required files
        init_file = self.module_path / "__init__.py"
        if init_file.exists():
            results.append(ValidationResult("init_exists", True, "__init__.py exists"))

            # Check if __init__.py has __all__ export
            try:
                with open(init_file, encoding="utf-8") as f:
                    init_content = f.read()

                tree = ast.parse(init_content)
                has_all = False
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == "__all__":
                                has_all = True
                                break

                if has_all:
                    results.append(ValidationResult("exports_defined", True, "__all__ exports defined"))
                else:
                    results.append(
                        ValidationResult("exports_defined", False, "__all__ exports not defined in __init__.py")
                    )

            except Exception as e:
                results.append(ValidationResult("init_parseable", False, f"Cannot parse __init__.py: {str(e)}"))
        else:
            results.append(ValidationResult("init_exists", False, "__init__.py missing"))

        # Check for README
        readme_file = self.module_path / "README.md"
        if readme_file.exists():
            results.append(ValidationResult("readme_exists", True, "README.md exists"))

            # Check README has minimum content
            with open(readme_file, encoding="utf-8") as f:
                readme_content = f.read()

            min_sections = ["Installation", "Usage", "Module Contract"]
            for section in min_sections:
                if section in readme_content:
                    results.append(ValidationResult(f"readme_{section.lower()}", True, f"README has {section} section"))
                else:
                    results.append(
                        ValidationResult(f"readme_{section.lower()}", False, f"README missing {section} section")
                    )
        else:
            results.append(ValidationResult("readme_exists", False, "README.md missing"))

        # Check for tests directory
        tests_dir = self.module_path / "tests"
        if tests_dir.exists():
            results.append(ValidationResult("tests_dir_exists", True, "tests/ directory exists"))

            # Check for test files
            test_files = list(tests_dir.glob("test_*.py"))
            if test_files:
                results.append(ValidationResult("test_files_exist", True, f"Found {len(test_files)} test file(s)"))
            else:
                results.append(ValidationResult("test_files_exist", False, "No test files found"))
        else:
            results.append(ValidationResult("tests_dir_exists", False, "tests/ directory missing"))

        return results

    def validate_tests(self) -> list[ValidationResult]:
        """Run pytest on generated tests

        Returns:
            List of validation results
        """
        results = []

        tests_dir = self.module_path / "tests"
        if not tests_dir.exists():
            results.append(ValidationResult("tests_executable", False, "No tests directory found"))
            return results

        # Check if pytest is available
        try:
            subprocess.run([sys.executable, "-m", "pytest", "--version"], capture_output=True, check=True, timeout=5)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            results.append(ValidationResult("pytest_available", False, "pytest not available or not responding"))
            return results

        # Run pytest
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(tests_dir), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.module_path.parent,  # Run from parent to ensure imports work
            )

            if result.returncode == 0:
                results.append(
                    ValidationResult(
                        "tests_pass", True, "All tests passed", {"stdout": result.stdout, "stderr": result.stderr}
                    )
                )
            else:
                # Parse pytest output for more details
                lines = result.stdout.split("\n")
                failed_tests = [line for line in lines if "FAILED" in line]
                error_msg = f"Tests failed (exit code {result.returncode})"
                if failed_tests:
                    error_msg += f"\nFailed tests: {len(failed_tests)}"

                results.append(
                    ValidationResult(
                        "tests_pass",
                        False,
                        error_msg,
                        {"stdout": result.stdout, "stderr": result.stderr, "failed_tests": failed_tests},
                    )
                )

        except subprocess.TimeoutExpired:
            results.append(ValidationResult("tests_timeout", False, "Tests timed out after 30 seconds"))
        except Exception as e:
            results.append(ValidationResult("tests_error", False, f"Error running tests: {str(e)}"))

        return results


def validate_module(module_path: Path, skip_tests: bool = False, verbose: bool = False) -> bool:
    """Convenience function to validate a module

    Args:
        module_path: Path to module directory
        skip_tests: Skip test execution
        verbose: Show detailed output

    Returns:
        True if all validations passed
    """
    validator = ModuleValidator(module_path)
    results = validator.validate_all(skip_tests=skip_tests)

    if verbose:
        print(f"Validating module: {module_path}")
        print("\n=== Syntax Validation ===")
        for result in results.syntax_results:
            status = "✓" if result.passed else "✗"
            print(f"  {status} {result.message}")

        print("\n=== Contract Validation ===")
        for result in results.contract_results:
            status = "✓" if result.passed else "✗"
            print(f"  {status} {result.message}")

        if results.test_results:
            print("\n=== Test Validation ===")
            for result in results.test_results:
                status = "✓" if result.passed else "✗"
                print(f"  {status} {result.message}")

        print("\n=== Summary ===")
        summary = results.summary
        print(f"  Syntax: {summary['syntax']['passed']} ({summary['syntax']['total']} checks)")
        print(f"  Contract: {summary['contract']['passed']} ({summary['contract']['total']} checks)")
        if summary["tests"]["total"] > 0:
            print(f"  Tests: {summary['tests']['passed']} ({summary['tests']['total']} checks)")
        print(f"  Overall: {'✓ PASSED' if summary['overall_passed'] else '✗ FAILED'}")

    return results.all_passed
