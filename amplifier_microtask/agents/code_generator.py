"""
Code Generation Agent

Specialized agent for generating Python code from implementation specifications.
Generates code file-by-file with immediate saving and resumption capability.
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..agent import execute_task
from ..orchestrator import Task as OrchestratorTask
from ..storage import append_jsonl


@dataclass
class GenerationStatus:
    """Status of code generation for a module"""

    module_name: str
    file_path: str
    generated: bool
    timestamp: Optional[str] = None
    error: Optional[str] = None
    lines_generated: int = 0


@dataclass
class ModuleSpec:
    """Specification for a code module"""

    name: str
    purpose: str
    imports: List[str]
    classes: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    constants: Optional[Dict[str, Any]] = None


class CodeGeneratorAgent:
    """Agent specialized in generating Python code from specifications"""

    def __init__(self, session_id: Optional[str] = None):
        self.agent_type = "code_generator"
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.generation_log = Path(".sessions") / f"codegen_{self.session_id}.jsonl"
        self.generation_log.parent.mkdir(exist_ok=True)

        # Load existing generation status if resuming
        self.status: Dict[str, GenerationStatus] = self._load_status()

    def _load_status(self) -> Dict[str, GenerationStatus]:
        """Load existing generation status from log"""
        status = {}
        if self.generation_log.exists():
            try:
                with open(self.generation_log, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            entry = json.loads(line)
                            status[entry["module_name"]] = GenerationStatus(**entry)
            except (json.JSONDecodeError, IOError):
                pass  # Return empty status if file is corrupted
        return status

    def _save_status(self, status: GenerationStatus) -> None:
        """Save generation status to log"""
        self.status[status.module_name] = status
        append_jsonl(asdict(status), self.generation_log)

    async def generate_module(self, task: OrchestratorTask, output_path: Path) -> GenerationStatus:
        """
        Generate a single Python module from task specifications.

        Args:
            task: Task containing module specifications
            output_path: Where to save the generated module

        Returns:
            GenerationStatus indicating success or failure
        """
        module_name = task.id.replace("impl_", "")

        # Check if already generated
        if module_name in self.status and self.status[module_name].generated:
            return self.status[module_name]

        # Extract specifications from task context
        spec = self._extract_spec_from_task(task)

        prompt = """
Generate a complete Python module based on these specifications:

MODULE NAME: {module_name}
PURPOSE: {purpose}

REQUIRED IMPORTS:
{imports}

CLASSES TO IMPLEMENT:
{classes}

FUNCTIONS TO IMPLEMENT:
{functions}

CONSTANTS:
{constants}

Generate production-ready Python code that:
1. Includes all necessary imports
2. Has proper docstrings for all classes and functions
3. Uses type hints throughout
4. Follows Python best practices
5. Is simple and maintainable

Return ONLY the Python code, no explanations or markdown formatting.
"""

        context = {
            "module_name": module_name,
            "purpose": spec.get("purpose", ""),
            "imports": json.dumps(spec.get("imports", []), indent=2),
            "classes": json.dumps(spec.get("classes", []), indent=2),
            "functions": json.dumps(spec.get("functions", []), indent=2),
            "constants": json.dumps(spec.get("constants", {}), indent=2),
        }

        try:
            # Generate the code with 120 second timeout
            code = await execute_task(prompt, context, timeout=300)  # Increased to 5 minutes for code generation

            # Clean up the code if needed
            code = self._clean_generated_code(code)

            # Save immediately
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(code)

            # Track status
            status = GenerationStatus(
                module_name=module_name,
                file_path=str(output_path),
                generated=True,
                timestamp=datetime.now().isoformat(),
                lines_generated=len(code.splitlines()),
            )
            self._save_status(status)

            return status

        except Exception as e:
            # Save failure status
            status = GenerationStatus(
                module_name=module_name,
                file_path=str(output_path),
                generated=False,
                timestamp=datetime.now().isoformat(),
                error=str(e),
            )
            self._save_status(status)

            return status

    def _extract_spec_from_task(self, task: OrchestratorTask) -> Dict[str, Any]:
        """Extract module specifications from task"""
        # The task should have specifications in its context or as part of the prompt
        # This is a simplified extraction - adapt based on actual task structure
        spec = {}

        # Try to extract from task context keys
        if hasattr(task, "context_keys"):
            spec["context_keys"] = task.context_keys

        # Parse prompt for specifications if structured
        if hasattr(task, "prompt"):
            # Simple extraction - enhance as needed
            lines = task.prompt.split("\n")
            for line in lines:
                if "PURPOSE:" in line:
                    spec["purpose"] = line.split("PURPOSE:")[1].strip()
                elif "MODULE:" in line:
                    spec["module"] = line.split("MODULE:")[1].strip()

        # Default structure if not found
        if not spec:
            spec = {
                "purpose": "Generated module",
                "imports": ["from typing import Any, Dict, List, Optional"],
                "classes": [],
                "functions": [],
                "constants": {},
            }

        return spec

    def _clean_generated_code(self, code: str) -> str:
        """Clean up generated code"""
        # Remove markdown code blocks if present
        code = code.strip()
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]

        if code.endswith("```"):
            code = code[:-3]

        return code.strip() + "\n"  # Ensure newline at end

    async def generate_from_tasks(self, tasks: List[OrchestratorTask], base_path: Path) -> Dict[str, GenerationStatus]:
        """
        Generate code for multiple tasks.

        Args:
            tasks: List of tasks with implementation specifications
            base_path: Base directory for generated code

        Returns:
            Dictionary mapping module names to generation status
        """
        results = {}

        for task in tasks:
            # Determine output path
            module_name = task.id.replace("impl_", "")
            output_path = base_path / f"{module_name}.py"

            # Generate the module
            status = await self.generate_module(task, output_path)
            results[module_name] = status

            # Continue even if one fails (graceful degradation)
            if not status.generated:
                print(f"Warning: Failed to generate {module_name}: {status.error}")

        return results

    def get_generation_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current generation status for all modules.

        Returns:
            Dictionary with module status information
        """
        return {
            name: {
                "generated": status.generated,
                "file_path": status.file_path,
                "timestamp": status.timestamp,
                "lines_generated": status.lines_generated,
                "error": status.error,
            }
            for name, status in self.status.items()
        }

    async def generate_implementation(self, spec: Dict[str, Any], output_path: Path) -> GenerationStatus:
        """
        Generate implementation from a detailed specification.

        Args:
            spec: Complete module specification
            output_path: Where to save the generated code

        Returns:
            GenerationStatus for the generation
        """
        module_name = output_path.stem

        # Check if already generated
        if module_name in self.status and self.status[module_name].generated:
            return self.status[module_name]

        prompt = """
Generate a complete Python implementation based on this specification:

{specification}

Requirements:
1. Implement ALL specified functions and classes
2. Include comprehensive docstrings
3. Use proper type hints
4. Follow Python best practices
5. Make the code production-ready
6. Keep it simple and maintainable

Return ONLY the Python code, no explanations.
"""

        context = {"specification": json.dumps(spec, indent=2)}

        try:
            # Generate with 120 second timeout
            code = await execute_task(prompt, context, timeout=300)  # Increased to 5 minutes for code generation

            # Clean and save
            code = self._clean_generated_code(code)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(code)

            # Track status
            status = GenerationStatus(
                module_name=module_name,
                file_path=str(output_path),
                generated=True,
                timestamp=datetime.now().isoformat(),
                lines_generated=len(code.splitlines()),
            )
            self._save_status(status)

            return status

        except Exception as e:
            status = GenerationStatus(
                module_name=module_name,
                file_path=str(output_path),
                generated=False,
                timestamp=datetime.now().isoformat(),
                error=str(e),
            )
            self._save_status(status)

            return status

    async def generate_test_file(self, module_path: Path, test_path: Path) -> GenerationStatus:
        """
        Generate tests for an existing module.

        Args:
            module_path: Path to the module to test
            test_path: Where to save the test file

        Returns:
            GenerationStatus for the test generation
        """
        if not module_path.exists():
            return GenerationStatus(
                module_name=f"test_{module_path.stem}",
                file_path=str(test_path),
                generated=False,
                error=f"Module {module_path} does not exist",
            )

        # Read the module code
        module_code = module_path.read_text()

        prompt = """
Generate comprehensive pytest tests for this Python module:

MODULE CODE:
{code}

Generate tests that:
1. Test all public functions and methods
2. Include edge cases and error conditions
3. Use proper pytest fixtures where appropriate
4. Have clear test names and docstrings
5. Achieve good code coverage

Return ONLY the Python test code.
"""

        context = {"code": module_code}

        try:
            test_code = await execute_task(prompt, context, timeout=300)  # Increased to 5 minutes for code generation

            # Clean and save
            test_code = self._clean_generated_code(test_code)
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(test_code)

            status = GenerationStatus(
                module_name=f"test_{module_path.stem}",
                file_path=str(test_path),
                generated=True,
                timestamp=datetime.now().isoformat(),
                lines_generated=len(test_code.splitlines()),
            )
            self._save_status(status)

            return status

        except Exception as e:
            status = GenerationStatus(
                module_name=f"test_{module_path.stem}",
                file_path=str(test_path),
                generated=False,
                timestamp=datetime.now().isoformat(),
                error=str(e),
            )
            self._save_status(status)

            return status
