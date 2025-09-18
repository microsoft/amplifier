"""Module output verification system.

This module ensures that generated modules are complete and correct before
declaring success. It tracks planned vs actual file generation and validates
the module structure.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

from .import_mappings import validate_imports_in_code


@dataclass
class FileGenerationPlan:
    """Tracks planned file generation and verification status."""

    module_name: str
    module_path: Path
    required_files: list[str] = field(default_factory=list)
    optional_files: list[str] = field(default_factory=list)
    generated_files: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "module_name": self.module_name,
            "module_path": str(self.module_path),
            "required_files": self.required_files,
            "optional_files": self.optional_files,
            "generated_files": self.generated_files,
            "missing_files": self.missing_files,
            "validation_errors": self.validation_errors,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FileGenerationPlan:
        """Create from dictionary."""
        return cls(
            module_name=data["module_name"],
            module_path=Path(data["module_path"]),
            required_files=data.get("required_files", []),
            optional_files=data.get("optional_files", []),
            generated_files=data.get("generated_files", []),
            missing_files=data.get("missing_files", []),
            validation_errors=data.get("validation_errors", []),
        )


class ModuleVerifier:
    """Verifies that generated modules are complete and correct."""

    def __init__(self, module_path: Path, module_name: str):
        self.module_path = module_path
        self.module_name = module_name
        self.plan = FileGenerationPlan(module_name=module_name, module_path=module_path)

    def set_required_files(self, files: list[str]) -> None:
        """Set the list of required files for this module."""
        self.plan.required_files = files

    def set_optional_files(self, files: list[str]) -> None:
        """Set the list of optional files for this module."""
        self.plan.optional_files = files

    def verify_structure(self) -> tuple[bool, list[str]]:
        """Verify the module structure is complete.

        Returns:
            Tuple of (is_complete, list_of_issues)
        """
        issues = []

        # Check if module directory exists
        if not self.module_path.exists():
            issues.append(f"Module directory does not exist: {self.module_path}")
            return False, issues

        # Check for __init__.py
        init_file = self.module_path / "__init__.py"
        if not init_file.exists():
            issues.append("Missing __init__.py")
        else:
            self.plan.generated_files.append("__init__.py")

        # Check for implementation files (at least one must exist)
        impl_files = ["core.py", "synthesizer.py", "engine.py", "processor.py", "main.py"]
        has_impl = False
        for impl_file in impl_files:
            if (self.module_path / impl_file).exists():
                has_impl = True
                self.plan.generated_files.append(impl_file)
                break

        if not has_impl:
            issues.append(f"Missing implementation file (expected one of: {', '.join(impl_files)})")

        # Check required files
        for req_file in self.plan.required_files:
            file_path = self.module_path / req_file
            if not file_path.exists():
                # Check if it's a pattern match
                if "*" in req_file:
                    # Handle glob patterns
                    matches = list(self.module_path.glob(req_file))
                    if not matches:
                        issues.append(f"Missing required file/pattern: {req_file}")
                        self.plan.missing_files.append(req_file)
                    else:
                        for match in matches:
                            self.plan.generated_files.append(str(match.relative_to(self.module_path)))
                else:
                    issues.append(f"Missing required file: {req_file}")
                    self.plan.missing_files.append(req_file)
            else:
                self.plan.generated_files.append(req_file)

        # Check for tests directory
        tests_dir = self.module_path / "tests"
        if tests_dir.exists():
            test_init = tests_dir / "__init__.py"
            if test_init.exists():
                self.plan.generated_files.append("tests/__init__.py")

            # Find test files
            test_files = list(tests_dir.glob("test_*.py"))
            for test_file in test_files:
                self.plan.generated_files.append(f"tests/{test_file.name}")

            if not test_files:
                issues.append("Tests directory exists but has no test files")
        else:
            issues.append("Missing tests directory")

        return len(issues) == 0, issues

    def verify_imports(self) -> tuple[bool, list[str]]:
        """Verify that all imports in the module are correct.

        Returns:
            Tuple of (all_imports_valid, list_of_import_issues)
        """
        import_issues = []

        # Check all Python files
        for py_file in self.module_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                code = py_file.read_text()
                warnings = validate_imports_in_code(code)
                if warnings:
                    for warning in warnings:
                        import_issues.append(f"{py_file.relative_to(self.module_path)}: {warning}")
            except Exception as e:
                import_issues.append(f"Error reading {py_file}: {e}")

        return len(import_issues) == 0, import_issues

    def verify_syntax(self) -> tuple[bool, list[str]]:
        """Verify that all Python files have valid syntax.

        Returns:
            Tuple of (all_syntax_valid, list_of_syntax_errors)
        """
        syntax_errors = []

        for py_file in self.module_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                code = py_file.read_text()
                ast.parse(code)
            except SyntaxError as e:
                rel_path = py_file.relative_to(self.module_path)
                syntax_errors.append(f"{rel_path}:{e.lineno}: {e.msg}")
            except Exception as e:
                syntax_errors.append(f"Error parsing {py_file}: {e}")

        return len(syntax_errors) == 0, syntax_errors

    def verify_dependencies(self) -> tuple[bool, list[str]]:
        """Verify that imported local modules exist.

        Returns:
            Tuple of (all_deps_exist, list_of_missing_deps)
        """
        missing_deps = []

        for py_file in self.module_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                code = py_file.read_text()
                # Check for relative imports
                for line in code.split("\n"):
                    line = line.strip()
                    if line.startswith("from ."):
                        # Extract module name
                        parts = line.split()
                        if len(parts) >= 2:
                            import_path = parts[1]
                            # Handle parent imports (from ..utils.file_io)
                            if import_path.startswith(".."):
                                # This is importing from parent module, skip verification
                                # as it's outside this module's scope
                                continue
                            # Remove leading dot for local imports (from .models)
                            module = import_path.lstrip(".")
                            if module and module != "":
                                # Check if module file exists
                                module_file = self.module_path / f"{module}.py"
                                if (
                                    not module_file.exists()
                                    and module not in ["utils", "models", "errors"]
                                    and module not in ["config", "constants", "types"]
                                ):
                                    missing_deps.append(
                                        f"{py_file.relative_to(self.module_path)} imports "
                                        f"'.{module}' but {module}.py doesn't exist"
                                    )
            except Exception as e:
                missing_deps.append(f"Error checking deps in {py_file}: {e}")

        return len(missing_deps) == 0, missing_deps

    def verify_all(self) -> tuple[bool, str]:
        """Run all verification checks.

        Returns:
            Tuple of (is_valid, formatted_report)
        """
        report_lines = [f"Module Verification Report: {self.module_name}"]
        report_lines.append("=" * 60)

        all_valid = True

        # Structure verification
        structure_ok, structure_issues = self.verify_structure()
        if not structure_ok:
            all_valid = False
            report_lines.append("\n❌ Structure Issues:")
            for issue in structure_issues:
                report_lines.append(f"  - {issue}")
        else:
            report_lines.append("\n✅ Structure: Complete")

        # Syntax verification
        syntax_ok, syntax_errors = self.verify_syntax()
        if not syntax_ok:
            all_valid = False
            report_lines.append("\n❌ Syntax Errors:")
            for error in syntax_errors:
                report_lines.append(f"  - {error}")
        else:
            report_lines.append("✅ Syntax: Valid")

        # Import verification
        imports_ok, import_issues = self.verify_imports()
        if not imports_ok:
            all_valid = False
            report_lines.append("\n❌ Import Issues:")
            for issue in import_issues:
                report_lines.append(f"  - {issue}")
        else:
            report_lines.append("✅ Imports: Correct")

        # Dependency verification
        deps_ok, missing_deps = self.verify_dependencies()
        if not deps_ok:
            all_valid = False
            report_lines.append("\n❌ Missing Dependencies:")
            for dep in missing_deps:
                report_lines.append(f"  - {dep}")
        else:
            report_lines.append("✅ Dependencies: Resolved")

        # Summary
        report_lines.append("\n" + "=" * 60)
        if all_valid:
            report_lines.append("✅ MODULE VERIFICATION PASSED")
            report_lines.append(f"   Generated {len(self.plan.generated_files)} files successfully")
        else:
            report_lines.append("❌ MODULE VERIFICATION FAILED")
            report_lines.append(f"   {len(self.plan.missing_files)} files missing")
            report_lines.append(f"   {len(self.plan.validation_errors)} validation errors")

        # Save plan for debugging
        plan_file = self.module_path / ".generation_plan.json"
        with open(plan_file, "w") as f:
            json.dump(self.plan.to_dict(), f, indent=2)

        return all_valid, "\n".join(report_lines)


def extract_planned_files_from_prompt(prompt: str) -> tuple[list[str], list[str]]:
    """Extract the list of files that should be generated from the prompt.

    Args:
        prompt: The generation prompt

    Returns:
        Tuple of (required_files, optional_files)
    """
    required_files = []
    optional_files = []

    # Look for checklist items in the prompt
    lines = prompt.split("\n")
    for line in lines:
        # Match patterns like "[ ] 1. {module_dir_rel}/__init__.py"
        if "[ ]" in line and ("/" in line or ".py" in line):
            # Extract file path
            parts = line.split("/")
            if len(parts) > 1:
                # Get the file name part
                file_part = parts[-1].strip()
                if ".py" in file_part:
                    file_name = file_part.split()[0].strip()
                    if "(" in file_name:
                        file_name = file_name.split("(")[0].strip()

                    # Determine if required or optional
                    if "if" in line.lower() or "optional" in line.lower():
                        optional_files.append(file_name)
                    else:
                        required_files.append(file_name)

    # Always require these core files
    if "__init__.py" not in required_files:
        required_files.append("__init__.py")

    # At least one implementation file is required
    if not any(f in required_files for f in ["core.py", "synthesizer.py", "engine.py"]):
        required_files.append("core.py")  # Default expectation

    return required_files, optional_files
