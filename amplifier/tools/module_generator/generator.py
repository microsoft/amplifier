"""Module generation pipeline coordinator

Orchestrates the generation of complete modules from specifications.
"""

import json
from pathlib import Path
from typing import Any

from .models import ContractSpec
from .models import ImplementationSpec
from .models import ModuleSpec
from .sdk_client import SDKModuleGenerator
from .writer import ModuleWriter


class ModuleGenerator:
    """Coordinate module generation from specifications"""

    def __init__(self, output_dir: str | Path, permission_mode: str = "plan", timeout_seconds: int = 300):
        """Initialize the module generator

        Args:
            output_dir: Base directory for generated modules
            permission_mode: Either "plan" (dry run) or "acceptEdits" (actual generation)
            timeout_seconds: Timeout for SDK operations (default 300s/5min)
        """
        self.output_dir = Path(output_dir)
        self.permission_mode = permission_mode
        self.timeout_seconds = timeout_seconds

        # Import TimeoutConfig here to avoid linter removing it
        from .sdk_client import TimeoutConfig

        # Create timeout config from seconds
        timeout_config = TimeoutConfig(
            analysis=min(120, timeout_seconds),
            file_generation=timeout_seconds,
            test_generation=timeout_seconds,
            default=min(120, timeout_seconds),
        )

        # Create SDK generator - no backwards compatibility
        self.sdk = SDKModuleGenerator(timeout_config, permission_mode, philosophy_path=None)

        self.writer = ModuleWriter(self.output_dir)

    async def generate(
        self, contract_spec: "ContractSpec", impl_spec: "ImplementationSpec", analyze_only: bool = False
    ) -> dict[str, Any]:
        """Generate a complete module from contract and implementation specifications

        Args:
            contract_spec: Contract specification
            impl_spec: Implementation specification
            analyze_only: Only analyze, don't generate

        Returns:
            Generation results including paths and analysis
        """

        results = {
            "module_name": contract_spec.module_name,
            "module_path": str(self.output_dir / contract_spec.module_name),
            "files_generated": [],
            "tests_generated": [],
            "analysis": None,
            "errors": [],
        }

        try:
            # Set up progress callback for user visibility
            def progress_callback(phase: str, message: str):
                print(f"  [{phase}] {message}")

            if hasattr(self.sdk, "set_progress_callback"):
                self.sdk.set_progress_callback(progress_callback)

            # Combine specs for analysis
            combined_spec = {"contract": contract_spec.model_dump(), "implementation": impl_spec.model_dump()}
            spec_json = json.dumps(combined_spec, indent=2)
            print("Analyzing module specification...")
            analysis = await self.sdk.analyze_spec(spec_json)
            results["analysis"] = analysis

            if analyze_only:
                return results

            # Prepare module context for generation
            module_context = {
                "name": contract_spec.module_name,
                "purpose": contract_spec.purpose,
                "public_interface": contract_spec.public_interface,
                "inputs": contract_spec.inputs,
                "outputs": contract_spec.outputs,
                "side_effects": contract_spec.side_effects,
                "architecture": impl_spec.architecture,
                "algorithms": impl_spec.key_algorithms,
            }

            # Generate core implementation files based on the specifications
            # For now, generate a basic structure - the SDK will fill in the details
            files_to_generate = [
                {"filename": "__init__.py", "purpose": "Module initialization and exports"},
                {"filename": "core.py", "purpose": "Core implementation"},
                {"filename": "models.py", "purpose": "Data models"},
            ]

            for file_spec in files_to_generate:
                try:
                    code = await self._generate_file(file_spec, module_context)
                    file_path = self.writer.write_file(contract_spec.module_name, file_spec["filename"], code)
                    results["files_generated"].append(str(file_path))
                except Exception as e:
                    error = f"Failed to generate {file_spec['filename']}: {e}"
                    results["errors"].append(error)
                    print(f"Error: {error}")

            # Generate test files
            test_files = [
                {"filename": "test_core.py", "description": "Test core functionality"},
            ]

            for test_spec in test_files:
                try:
                    code = await self._generate_test(test_spec, module_context)
                    file_path = self.writer.write_test(contract_spec.module_name, test_spec["filename"], code)
                    results["tests_generated"].append(str(file_path))
                except Exception as e:
                    error = f"Failed to generate {test_spec['filename']}: {e}"
                    results["errors"].append(error)
                    print(f"Error: {error}")

            # Generate __init__.py
            init_code = self._generate_init(contract_spec)
            init_path = self.writer.write_file(contract_spec.module_name, "__init__.py", init_code)
            results["files_generated"].append(str(init_path))

            # Generate README.md
            readme_code = self._generate_readme(contract_spec, impl_spec)
            readme_path = self.writer.write_file(contract_spec.module_name, "README.md", readme_code)
            results["files_generated"].append(str(readme_path))

        except Exception as e:
            results["errors"].append(f"Generation failed: {e}")
            print(f"Error: Generation failed: {e}")

        return results

    async def _generate_file(self, file_spec: dict[str, Any], module_context: dict[str, Any]) -> str:
        """Generate a single file implementation

        Args:
            file_spec: File specification dictionary
            module_context: Module context

        Returns:
            Generated code
        """
        return await self.sdk.generate_file(file_spec, module_context)

    async def _generate_test(self, test_spec: dict[str, Any], module_context: dict[str, Any]) -> str:
        """Generate a test file

        Args:
            test_spec: Test specification dictionary
            module_context: Module context

        Returns:
            Generated test code
        """
        return await self.sdk.generate_test(test_spec, module_context)

    def _generate_init(self, contract_spec: ContractSpec) -> str:
        """Generate __init__.py for the module

        Args:
            contract_spec: Contract specification

        Returns:
            Generated __init__.py content
        """
        # Use public interface from contract spec
        exports = contract_spec.public_interface if contract_spec.public_interface else []

        # Generate imports based on public interface
        imports = []
        for interface in exports:
            # Assume interface is in core.py by default
            imports.append(f"from .core import {interface}")

        init_content = f'''"""{contract_spec.module_name} - {contract_spec.purpose}

This module provides {contract_spec.purpose.lower()}.
"""

{chr(10).join(imports)}

__all__ = {exports}
'''
        return init_content

    def _generate_readme(self, contract_spec: ContractSpec, impl_spec: ImplementationSpec) -> str:
        """Generate README.md for the module

        Args:
            contract_spec: Contract specification
            impl_spec: Implementation specification

        Returns:
            Generated README content
        """
        readme = f"""# {contract_spec.module_name}

{contract_spec.purpose}

## Installation

```bash
pip install -e .
```

## Usage

```python
from {contract_spec.module_name} import ...

# Usage examples
```

## Module Contract

### Inputs
"""

        for key, desc in contract_spec.inputs.items():
            readme += f"- **{key}**: {desc}\n"

        readme += "\n### Outputs\n"
        for key, desc in contract_spec.outputs.items():
            readme += f"- **{key}**: {desc}\n"

        if contract_spec.side_effects:
            readme += "\n### Side Effects\n"
            for effect in contract_spec.side_effects:
                readme += f"- {effect}\n"

        if contract_spec.dependencies:
            readme += "\n## Dependencies\n"
            for dep in contract_spec.dependencies:
                readme += f"- {dep}\n"

        # Add implementation details
        if impl_spec.architecture:
            readme += f"\n## Architecture\n\n{impl_spec.architecture}\n"

        if impl_spec.key_algorithms:
            readme += "\n## Key Algorithms\n\n"
            for algo in impl_spec.key_algorithms:
                readme += f"- {algo}\n"

        if contract_spec.performance_specs:
            readme += "\n## Performance Specifications\n\n"
            for key, spec in contract_spec.performance_specs.items():
                readme += f"- **{key}**: {spec}\n"

        if contract_spec.error_handling:
            readme += "\n## Error Handling\n\n"
            for error, handling in contract_spec.error_handling.items():
                readme += f"- **{error}**: {handling}\n"

        readme += """
## Testing

```bash
pytest tests/
```

## Regeneration

This module can be regenerated from its specification:
```bash
python -m amplifier.tools.module_generator generate contract.md implementation.md
```
"""
        return readme


class PlanAnalyzer:
    """Analyze specifications and provide implementation plans"""

    def __init__(self):
        """Initialize the analyzer"""
        # Import TimeoutConfig for analyzer
        from .sdk_client import TimeoutConfig

        # Create default timeout config for analyzer
        timeout_config = TimeoutConfig()
        self.sdk = SDKModuleGenerator(timeout_config, permission_mode="plan", philosophy_path=None)

    async def analyze(self, spec: ModuleSpec) -> dict[str, Any]:
        """Analyze a specification and return implementation plan

        Args:
            spec: Module specification

        Returns:
            Analysis results
        """
        spec_json = spec.model_dump_json(indent=2)
        return await self.sdk.analyze_spec(spec_json)
