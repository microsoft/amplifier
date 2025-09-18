"""
Test Generator Agent

Creates pytest tests from acceptance criteria and requirements.
Generates runnable test cases that match the codebase testing style.
"""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..agent import execute_task
from .requirements import Requirement


@dataclass
class GeneratedTest:
    """Represents a generated test"""

    test_name: str
    test_path: str
    requirement_id: Optional[str] = None
    module_path: Optional[str] = None
    generated_at: str = ""
    status: str = "pending"  # pending, generated, failed
    error: Optional[str] = None


class TestGeneratorAgent:
    """Agent specialized in generating pytest tests from requirements"""

    def __init__(self, session_dir: Optional[Path] = None):
        """Initialize the test generator.

        Args:
            session_dir: Optional directory to track test generation status
        """
        self.agent_type = "test_generator"
        self.session_dir = session_dir or Path("ai_working/test_generation")
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.status_file = self.session_dir / "test_status.json"
        self.generated_tests = self._load_status()

    def _load_status(self) -> Dict[str, GeneratedTest]:
        """Load test generation status from file"""
        if self.status_file.exists():
            try:
                with open(self.status_file, "r") as f:
                    data = json.load(f)
                    return {k: GeneratedTest(**v) for k, v in data.items()}
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    def _save_status(self):
        """Save test generation status to file"""
        data = {k: asdict(v) for k, v in self.generated_tests.items()}
        with open(self.status_file, "w") as f:
            json.dump(data, f, indent=2)

    async def generate_tests_for_requirement(
        self, requirement: Requirement, test_path: Optional[str] = None
    ) -> GeneratedTest:
        """Generate pytest tests for a single requirement.

        Args:
            requirement: The requirement to generate tests for
            test_path: Optional path where to save the test file

        Returns:
            GeneratedTest object with status
        """
        # Determine test path
        if not test_path:
            test_path = f"tests/test_{requirement.id}.py"

        # Check if already generated
        test_key = f"{requirement.id}_{test_path}"
        if test_key in self.generated_tests:
            existing = self.generated_tests[test_key]
            if existing.status == "generated":
                return existing

        prompt = """
Generate comprehensive pytest tests for this requirement.

REQUIREMENT ID: {req_id}
DESCRIPTION: {description}
USER STORY: {user_story}
ACCEPTANCE CRITERIA:
{criteria}

Generate a complete pytest test file that:
1. Tests each acceptance criterion
2. Includes both positive and negative test cases
3. Uses proper pytest patterns and fixtures
4. Has clear test names and docstrings
5. Includes necessary imports

Return ONLY the complete Python test code, no markdown formatting.
Start with imports and go straight into the test functions.
"""

        context = {
            "req_id": requirement.id,
            "description": requirement.description,
            "user_story": requirement.user_story or "N/A",
            "criteria": "\n".join(f"- {c}" for c in (requirement.acceptance_criteria or [])),
        }

        try:
            # Generate test code
            test_code = await execute_task(prompt, context, timeout=300)  # Increased to 5 minutes for test generation

            # Clean up any markdown formatting if present
            test_code = test_code.strip()
            if test_code.startswith("```python"):
                test_code = test_code[9:]
            elif test_code.startswith("```"):
                test_code = test_code[3:]
            if test_code.endswith("```"):
                test_code = test_code[:-3]
            test_code = test_code.strip()

            # Ensure test code has proper structure
            if not test_code.startswith("import") and not test_code.startswith("from"):
                # Add basic imports if missing
                test_code = "import pytest\n\n" + test_code

            # Save test file
            test_file = Path(test_path)
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text(test_code)

            # Update status
            generated_test = GeneratedTest(
                test_name=f"test_{requirement.id}",
                test_path=str(test_file),
                requirement_id=requirement.id,
                generated_at=datetime.now().isoformat(),
                status="generated",
            )

            self.generated_tests[test_key] = generated_test
            self._save_status()

            return generated_test

        except Exception as e:
            # Record failure
            generated_test = GeneratedTest(
                test_name=f"test_{requirement.id}",
                test_path=test_path,
                requirement_id=requirement.id,
                generated_at=datetime.now().isoformat(),
                status="failed",
                error=str(e),
            )

            self.generated_tests[test_key] = generated_test
            self._save_status()

            return generated_test

    async def generate_tests_for_module(self, module_path: str, test_path: Optional[str] = None) -> GeneratedTest:
        """Generate tests for a code module.

        Args:
            module_path: Path to the module to test
            test_path: Optional path where to save the test file

        Returns:
            GeneratedTest object with status
        """
        # Read module code
        module_file = Path(module_path)
        if not module_file.exists():
            return GeneratedTest(
                test_name=f"test_{module_file.stem}",
                test_path=test_path or "",
                module_path=module_path,
                status="failed",
                error=f"Module not found: {module_path}",
            )

        module_code = module_file.read_text()

        # Determine test path
        if not test_path:
            test_path = f"tests/test_{module_file.stem}.py"

        # Check if already generated
        test_key = f"{module_path}_{test_path}"
        if test_key in self.generated_tests:
            existing = self.generated_tests[test_key]
            if existing.status == "generated":
                return existing

        prompt = """
Generate comprehensive pytest tests for this Python module.

MODULE PATH: {module_path}
MODULE CODE:
{module_code}

Generate a complete pytest test file that:
1. Tests all public functions and classes
2. Includes edge cases and error conditions
3. Uses proper pytest patterns and fixtures
4. Has clear test names and docstrings
5. Mocks external dependencies appropriately
6. Achieves good code coverage

Return ONLY the complete Python test code, no markdown formatting.
"""

        context = {
            "module_path": module_path,
            "module_code": module_code[:5000],  # Limit code length
        }

        try:
            # Generate test code
            test_code = await execute_task(prompt, context, timeout=300)  # Increased to 5 minutes for test generation

            # Clean up formatting
            test_code = test_code.strip()
            if test_code.startswith("```python"):
                test_code = test_code[9:]
            elif test_code.startswith("```"):
                test_code = test_code[3:]
            if test_code.endswith("```"):
                test_code = test_code[:-3]
            test_code = test_code.strip()

            # Save test file
            test_file = Path(test_path)
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text(test_code)

            # Update status
            generated_test = GeneratedTest(
                test_name=f"test_{module_file.stem}",
                test_path=str(test_file),
                module_path=module_path,
                generated_at=datetime.now().isoformat(),
                status="generated",
            )

            self.generated_tests[test_key] = generated_test
            self._save_status()

            return generated_test

        except Exception as e:
            # Record failure
            generated_test = GeneratedTest(
                test_name=f"test_{module_file.stem}",
                test_path=test_path,
                module_path=module_path,
                generated_at=datetime.now().isoformat(),
                status="failed",
                error=str(e),
            )

            self.generated_tests[test_key] = generated_test
            self._save_status()

            return generated_test

    async def generate_test_suite(
        self, requirements: List[Requirement], base_test_path: str = "tests"
    ) -> Dict[str, GeneratedTest]:
        """Generate a full test suite for multiple requirements.

        Args:
            requirements: List of requirements to generate tests for
            base_test_path: Base directory for test files

        Returns:
            Dictionary mapping requirement IDs to GeneratedTest objects
        """
        results = {}

        for req in requirements:
            # Generate test path based on requirement ID
            test_path = os.path.join(base_test_path, f"test_{req.id}.py")

            # Generate tests for this requirement
            result = await self.generate_tests_for_requirement(req, test_path)

            results[req.id] = result

            # Save after each generation for resilience
            self._save_status()

        return results

    def get_test_status(self) -> Dict[str, Any]:
        """Return current status of all generated tests.

        Returns:
            Dictionary with test generation statistics and details
        """
        total = len(self.generated_tests)
        generated = sum(1 for t in self.generated_tests.values() if t.status == "generated")
        failed = sum(1 for t in self.generated_tests.values() if t.status == "failed")
        pending = sum(1 for t in self.generated_tests.values() if t.status == "pending")

        # Group by requirement
        by_requirement = {}
        for test in self.generated_tests.values():
            if test.requirement_id:
                if test.requirement_id not in by_requirement:
                    by_requirement[test.requirement_id] = []
                by_requirement[test.requirement_id].append(
                    {
                        "test_name": test.test_name,
                        "test_path": test.test_path,
                        "status": test.status,
                        "error": test.error,
                    }
                )

        # Group by module
        by_module = {}
        for test in self.generated_tests.values():
            if test.module_path:
                if test.module_path not in by_module:
                    by_module[test.module_path] = []
                by_module[test.module_path].append(
                    {
                        "test_name": test.test_name,
                        "test_path": test.test_path,
                        "status": test.status,
                        "error": test.error,
                    }
                )

        return {
            "summary": {
                "total": total,
                "generated": generated,
                "failed": failed,
                "pending": pending,
                "success_rate": f"{(generated / total * 100):.1f}%" if total > 0 else "N/A",
            },
            "by_requirement": by_requirement,
            "by_module": by_module,
            "failed_tests": [
                {"test_name": t.test_name, "test_path": t.test_path, "error": t.error}
                for t in self.generated_tests.values()
                if t.status == "failed"
            ],
        }

    async def retry_failed(self) -> Dict[str, GeneratedTest]:
        """Retry generation for all failed tests.

        Returns:
            Dictionary of retried tests
        """
        failed_tests = [(key, test) for key, test in self.generated_tests.items() if test.status == "failed"]

        results = {}
        for key, test in failed_tests:
            if test.requirement_id:
                # Create a minimal requirement object
                req = Requirement(
                    id=test.requirement_id,
                    description=f"Retry for {test.requirement_id}",
                )
                result = await self.generate_tests_for_requirement(req, test.test_path)
            elif test.module_path:
                result = await self.generate_tests_for_module(test.module_path, test.test_path)
            else:
                continue

            results[key] = result

        return results
