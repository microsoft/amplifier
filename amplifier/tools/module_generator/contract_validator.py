"""
Contract validation to ensure generated modules fulfill their contracts.

This validator:
- Tracks what must be generated based on parsed contracts
- Verifies that generated code fulfills all requirements
- Reports missing or incomplete implementations
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path

from .contract_parser import ContractRequirements
from .contract_parser import EnhancedContractParser


@dataclass
class ValidationResult:
    """Result of contract validation."""

    is_valid: bool
    missing_functions: list[str]
    missing_classes: list[str]
    missing_data_models: list[str]
    missing_errors: list[str]
    missing_config_params: list[str]
    import_errors: list[str]
    test_failures: list[str]
    warnings: list[str]

    def summary(self) -> str:
        """Generate a summary report."""
        lines = []

        if self.is_valid:
            lines.append("✅ Module fulfills contract requirements")
        else:
            lines.append("❌ Module does not fulfill contract requirements")
            lines.append("")

        if self.missing_functions:
            lines.append(f"Missing Functions ({len(self.missing_functions)}):")
            for func in self.missing_functions:
                lines.append(f"  - {func}")

        if self.missing_classes:
            lines.append(f"Missing Classes ({len(self.missing_classes)}):")
            for cls in self.missing_classes:
                lines.append(f"  - {cls}")

        if self.missing_data_models:
            lines.append(f"Missing Data Models ({len(self.missing_data_models)}):")
            for model in self.missing_data_models:
                lines.append(f"  - {model}")

        if self.missing_errors:
            lines.append(f"Missing Error Types ({len(self.missing_errors)}):")
            for error in self.missing_errors:
                lines.append(f"  - {error}")

        if self.missing_config_params:
            lines.append(f"Missing Config Parameters ({len(self.missing_config_params)}):")
            for param in self.missing_config_params:
                lines.append(f"  - {param}")

        if self.import_errors:
            lines.append(f"Import Errors ({len(self.import_errors)}):")
            for error in self.import_errors:
                lines.append(f"  - {error}")

        if self.test_failures:
            lines.append(f"Test Failures ({len(self.test_failures)}):")
            for failure in self.test_failures:
                lines.append(f"  - {failure}")

        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        return "\n".join(lines)


class ContractValidator:
    """Validate that a generated module fulfills its contract."""

    def __init__(self, module_path: Path, requirements: ContractRequirements):
        self.module_path = module_path
        self.requirements = requirements
        self.module_name = requirements.module_name

    @classmethod
    def from_contract_text(cls, module_path: Path, contract_text: str) -> ContractValidator:
        """Create validator from contract text."""
        parser = EnhancedContractParser(contract_text)
        requirements = parser.parse()
        return cls(module_path, requirements)

    def validate(self) -> ValidationResult:
        """Validate the module against its contract."""
        result = ValidationResult(
            is_valid=True,
            missing_functions=[],
            missing_classes=[],
            missing_data_models=[],
            missing_errors=[],
            missing_config_params=[],
            import_errors=[],
            test_failures=[],
            warnings=[],
        )

        # Check module structure exists
        if not self.module_path.exists():
            result.is_valid = False
            result.import_errors.append(f"Module directory does not exist: {self.module_path}")
            return result

        # Validate functions
        self._validate_functions(result)

        # Validate classes
        self._validate_classes(result)

        # Validate data models
        self._validate_data_models(result)

        # Validate error types
        self._validate_errors(result)

        # Validate config parameters
        self._validate_config_params(result)

        # Test imports
        self._test_imports(result)

        # Update overall validity
        result.is_valid = (
            len(result.missing_functions) == 0
            and len(result.missing_classes) == 0
            and len(result.missing_data_models) == 0
            and len(result.missing_errors) == 0
            and len(result.import_errors) == 0
            and len(result.test_failures) == 0
        )

        return result

    def _validate_functions(self, result: ValidationResult) -> None:
        """Check that all required functions exist."""
        # Find all Python files
        python_files = list(self.module_path.glob("*.py"))

        found_functions = set()

        for py_file in python_files:
            if py_file.name.startswith("test_"):
                continue

            try:
                tree = ast.parse(py_file.read_text())

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                        found_functions.add(node.name)
            except Exception as e:
                result.warnings.append(f"Failed to parse {py_file.name}: {e}")

        # Check required functions
        for func in self.requirements.functions:
            if func.name not in found_functions:
                result.missing_functions.append(func.name)

    def _validate_classes(self, result: ValidationResult) -> None:
        """Check that all required classes exist."""
        python_files = list(self.module_path.glob("*.py"))

        found_classes = {}

        for py_file in python_files:
            if py_file.name.startswith("test_"):
                continue

            try:
                tree = ast.parse(py_file.read_text())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Collect methods in this class
                        methods = []
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                                methods.append(item.name)
                        found_classes[node.name] = methods
            except Exception as e:
                result.warnings.append(f"Failed to parse {py_file.name}: {e}")

        # Check required classes
        for cls in self.requirements.classes:
            if cls.name not in found_classes:
                result.missing_classes.append(cls.name)
            else:
                # Check methods
                found_methods = found_classes[cls.name]
                for method in cls.methods:
                    if method.name not in found_methods and method.name != "__init__":
                        result.warnings.append(f"Class {cls.name} missing method: {method.name}")

    def _validate_data_models(self, result: ValidationResult) -> None:
        """Check that all required data models exist with correct fields."""
        models_file = self.module_path / "models.py"

        if not models_file.exists():
            if self.requirements.data_models:
                result.missing_data_models.extend([m.name for m in self.requirements.data_models])
            return

        try:
            tree = ast.parse(models_file.read_text())
            found_models = {}

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Collect fields
                    fields = []
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            fields.append(item.target.id)
                    found_models[node.name] = fields

            # Check required models
            for model in self.requirements.data_models:
                if model.name not in found_models:
                    result.missing_data_models.append(model.name)
                else:
                    # Check fields
                    found_fields = found_models[model.name]
                    for field in model.fields:
                        if field.required and field.name not in found_fields:
                            result.warnings.append(f"Model {model.name} missing required field: {field.name}")

        except Exception as e:
            result.warnings.append(f"Failed to parse models.py: {e}")

    def _validate_errors(self, result: ValidationResult) -> None:
        """Check that all required error types exist."""
        errors_file = self.module_path / "errors.py"

        found_errors = set()

        # Check errors.py if it exists
        if errors_file.exists():
            try:
                tree = ast.parse(errors_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and "Error" in node.name:
                        found_errors.add(node.name)
            except Exception as e:
                result.warnings.append(f"Failed to parse errors.py: {e}")

        # Also check all Python files for error definitions
        for py_file in self.module_path.glob("*.py"):
            if py_file.name == "errors.py" or py_file.name.startswith("test_"):
                continue

            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and "Error" in node.name:
                        found_errors.add(node.name)
            except Exception:
                pass

        # Check required errors
        for error in self.requirements.errors:
            if error.name not in found_errors:
                result.missing_errors.append(error.name)

    def _validate_config_params(self, result: ValidationResult) -> None:
        """Check that config classes have all required parameters."""
        # Look for config classes in models.py or config.py
        for config_file in ["models.py", "config.py", "core.py"]:
            file_path = self.module_path / config_file
            if not file_path.exists():
                continue

            try:
                tree = ast.parse(file_path.read_text())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and "Config" in node.name:
                        # Collect fields
                        found_fields = []
                        for item in node.body:
                            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                                found_fields.append(item.target.id)

                        # Check required config params
                        for param in self.requirements.config_params:
                            if param.name not in found_fields:
                                result.missing_config_params.append(f"{node.name}.{param.name}")

            except Exception as e:
                result.warnings.append(f"Failed to parse {config_file}: {e}")

    def _test_imports(self, result: ValidationResult) -> None:
        """Test that the module can be imported."""
        init_file = self.module_path / "__init__.py"

        if not init_file.exists():
            result.import_errors.append("Missing __init__.py")
            return

        # Add parent directory to path temporarily
        parent_dir = str(self.module_path.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        try:
            # Try to import the module
            spec = importlib.util.spec_from_file_location(self.module_name, init_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Check that __all__ exists
                if not hasattr(module, "__all__"):
                    result.warnings.append("__init__.py missing __all__ export list")
                else:
                    # Check that required functions are exported
                    exports = getattr(module, "__all__", [])
                    for func in self.requirements.functions:
                        if func.name not in exports:
                            result.warnings.append(f"Function {func.name} not exported in __all__")

        except Exception as e:
            result.import_errors.append(f"Failed to import module: {e}")
        finally:
            # Clean up sys.path
            if parent_dir in sys.path:
                sys.path.remove(parent_dir)

    def generate_missing_code_prompt(self, result: ValidationResult) -> str:
        """Generate a prompt to fix missing implementations."""
        if result.is_valid:
            return ""

        prompt = ["The following contract requirements are not fulfilled:"]
        prompt.append("")

        if result.missing_functions:
            prompt.append("MISSING FUNCTIONS:")
            for func_name in result.missing_functions:
                # Find the function in requirements
                func = next((f for f in self.requirements.functions if f.name == func_name), None)
                if func:
                    params = ", ".join([f"{p[0]}: {p[1]}" for p in func.params])
                    ret = f" -> {func.return_type}" if func.return_type else ""
                    async_prefix = "async " if func.is_async else ""
                    prompt.append(f"  {async_prefix}def {func.name}({params}){ret}:")
                    if func.description:
                        prompt.append(f"    # {func.description}")

        if result.missing_classes:
            prompt.append("")
            prompt.append("MISSING CLASSES:")
            for cls_name in result.missing_classes:
                cls = next((c for c in self.requirements.classes if c.name == cls_name), None)
                if cls:
                    prompt.append(f"  class {cls.name}:")
                    for method in cls.methods:
                        params = ", ".join(["self"] + [f"{p[0]}: {p[1]}" for p in method.params])
                        ret = f" -> {method.return_type}" if method.return_type else ""
                        async_prefix = "async " if method.is_async else ""
                        prompt.append(f"    {async_prefix}def {method.name}({params}){ret}: ...")

        if result.missing_data_models:
            prompt.append("")
            prompt.append("MISSING DATA MODELS:")
            for model_name in result.missing_data_models:
                model = next((m for m in self.requirements.data_models if m.name == model_name), None)
                if model:
                    prompt.append("  @dataclass")
                    prompt.append(f"  class {model.name}:")
                    for field in model.fields:
                        default = f" = {field.default}" if field.default else ""
                        prompt.append(f"    {field.name}: {field.type_hint}{default}")

        if result.missing_config_params:
            prompt.append("")
            prompt.append("MISSING CONFIG PARAMETERS:")
            for param in result.missing_config_params:
                prompt.append(f"  - {param}")

        prompt.append("")
        prompt.append("Please implement these missing components to fulfill the contract.")

        return "\n".join(prompt)
