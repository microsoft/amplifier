"""
Feedback Loop System

Processes test results and iteratively refines implementations to fix failing tests.
Integrates with code and test generation agents to create a self-improving cycle.
"""

import json
import re
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .agent import execute_task
from .agents.code_generator import CodeGeneratorAgent
from .agents.test_generator import TestGeneratorAgent
from .storage import append_jsonl


@dataclass
class TestResult:
    """Result from running a test"""

    test_file: str
    passed: int
    failed: int
    errors: int
    skipped: int
    duration: float
    failures: List[Dict[str, str]]  # List of {test_name, error_message, traceback}
    timestamp: str = ""
    raw_output: str = ""


@dataclass
class CodeFix:
    """A fix for failing code"""

    file_path: str
    original_code: str
    fixed_code: str
    test_file: str
    failure_reason: str
    fix_description: str
    timestamp: str = ""


@dataclass
class IterationResult:
    """Result of one feedback iteration"""

    iteration: int
    test_result: TestResult
    fixes_applied: List[CodeFix]
    success: bool
    timestamp: str = ""


class FeedbackLoop:
    """Manages the test-fix-retest feedback loop"""

    def __init__(self, session_id: Optional[str] = None):
        """Initialize the feedback loop.

        Args:
            session_id: Optional session ID for tracking iterations
        """
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = Path(".sessions") / f"feedback_{self.session_id}"
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.iteration_log = self.session_dir / "iterations.jsonl"
        self.fixes_log = self.session_dir / "fixes.jsonl"

        # Initialize agents
        self.code_generator = CodeGeneratorAgent(session_id=self.session_id)
        self.test_generator = TestGeneratorAgent(session_dir=self.session_dir)

        self.iterations: List[IterationResult] = []

    async def run_tests(self, test_path: str) -> TestResult:
        """Execute pytest tests and capture results.

        Args:
            test_path: Path to test file or directory

        Returns:
            TestResult with test execution details
        """
        test_file = Path(test_path)
        if not test_file.exists():
            return TestResult(
                test_file=test_path,
                passed=0,
                failed=0,
                errors=1,
                skipped=0,
                duration=0.0,
                failures=[
                    {
                        "test_name": "file_not_found",
                        "error_message": f"Test file not found: {test_path}",
                        "traceback": "",
                    }
                ],
                timestamp=datetime.now().isoformat(),
                raw_output=f"Test file not found: {test_path}",
            )

        # Run pytest with verbose output and JSON report
        cmd = ["python", "-m", "pytest", str(test_file), "-v", "--tb=short", "--no-header", "--no-summary", "-q"]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )  # Increased to 2 minutes for test execution

            # Parse the output
            output = result.stdout + result.stderr

            # Extract test statistics
            passed = len(re.findall(r"PASSED", output))
            failed = len(re.findall(r"FAILED", output))
            errors = len(re.findall(r"ERROR", output))
            skipped = len(re.findall(r"SKIPPED", output))

            # Parse failures
            failures = self._parse_pytest_failures(output)

            # Try to extract duration
            duration_match = re.search(r"in ([\d.]+)s", output)
            duration = float(duration_match.group(1)) if duration_match else 0.0

            return TestResult(
                test_file=test_path,
                passed=passed,
                failed=failed,
                errors=errors,
                skipped=skipped,
                duration=duration,
                failures=failures,
                timestamp=datetime.now().isoformat(),
                raw_output=output[:5000],  # Limit output size
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                test_file=test_path,
                passed=0,
                failed=0,
                errors=1,
                skipped=0,
                duration=60.0,
                failures=[
                    {
                        "test_name": "timeout",
                        "error_message": "Test execution timed out after 120 seconds",
                        "traceback": "",
                    }
                ],
                timestamp=datetime.now().isoformat(),
                raw_output="Test execution timed out",
            )
        except Exception as e:
            return TestResult(
                test_file=test_path,
                passed=0,
                failed=0,
                errors=1,
                skipped=0,
                duration=0.0,
                failures=[{"test_name": "execution_error", "error_message": str(e), "traceback": ""}],
                timestamp=datetime.now().isoformat(),
                raw_output=str(e),
            )

    def _parse_pytest_failures(self, output: str) -> List[Dict[str, str]]:
        """Parse pytest output to extract failure details.

        Args:
            output: Raw pytest output

        Returns:
            List of failure dictionaries
        """
        failures = []

        # Split by FAILED markers
        failed_sections = re.split(r"FAILED ", output)

        for section in failed_sections[1:]:  # Skip first element (before first FAILED)
            lines = section.split("\n")
            if not lines:
                continue

            # First line contains test name
            test_name = lines[0].split(" - ")[0].strip()

            # Look for assertion or error message
            error_message = ""
            traceback_lines = []

            for i, line in enumerate(lines[1:], 1):
                if "AssertionError" in line or "Error" in line:
                    error_message = line.strip()
                    # Collect next few lines as traceback
                    traceback_lines = lines[i + 1 : i + 10]
                    break

            failures.append(
                {
                    "test_name": test_name,
                    "error_message": error_message or "Test failed",
                    "traceback": "\n".join(traceback_lines)[:1000],  # Limit traceback size
                }
            )

        return failures

    async def analyze_failures(self, test_result: TestResult) -> List[Dict[str, Any]]:
        """Analyze test failures to understand root causes.

        Args:
            test_result: Result from test execution

        Returns:
            List of failure analyses
        """
        if not test_result.failures:
            return []

        analyses = []

        for failure in test_result.failures:
            prompt = """
Analyze this test failure and identify the root cause.

TEST NAME: {test_name}
ERROR MESSAGE: {error_message}
TRACEBACK: {traceback}

Provide a concise analysis that includes:
1. The root cause of the failure
2. What needs to be fixed in the code
3. Whether it's a code bug, test issue, or missing implementation

Return your analysis as a JSON object with these fields:
- root_cause: Brief description of why it failed
- fix_type: One of "code_bug", "test_issue", "missing_implementation", "import_error"
- fix_location: Where the fix should be applied (file/function)
- fix_suggestion: Specific suggestion for fixing it
"""

            context = {
                "test_name": failure["test_name"],
                "error_message": failure["error_message"],
                "traceback": failure["traceback"],
            }

            try:
                response = await execute_task(
                    prompt, context, timeout=180
                )  # Increased to 3 minutes for failure analysis

                # Try to parse as JSON
                try:
                    analysis = json.loads(response)
                except json.JSONDecodeError:
                    # Fallback to basic analysis
                    analysis = {
                        "root_cause": failure["error_message"],
                        "fix_type": "code_bug",
                        "fix_location": "unknown",
                        "fix_suggestion": "Review the error and fix the code",
                    }

                analysis["test_name"] = failure["test_name"]
                analyses.append(analysis)

            except Exception as e:
                # Basic fallback analysis
                analyses.append(
                    {
                        "test_name": failure["test_name"],
                        "root_cause": failure["error_message"],
                        "fix_type": "unknown",
                        "fix_location": "unknown",
                        "fix_suggestion": f"Manual review needed: {str(e)}",
                    }
                )

        return analyses

    async def generate_fixes(self, failures: List[Dict[str, Any]], code_path: str) -> List[CodeFix]:
        """Generate code fixes for identified failures.

        Args:
            failures: List of failure analyses
            code_path: Path to the code file to fix

        Returns:
            List of CodeFix objects
        """
        fixes = []

        # Read the current code
        code_file = Path(code_path)
        if not code_file.exists():
            return fixes

        original_code = code_file.read_text()

        for failure in failures:
            # Skip test issues - focus on code bugs
            if failure.get("fix_type") == "test_issue":
                continue

            prompt = """
Fix this code based on the test failure analysis.

ORIGINAL CODE:
{original_code}

FAILURE ANALYSIS:
- Root Cause: {root_cause}
- Fix Type: {fix_type}
- Fix Location: {fix_location}
- Fix Suggestion: {fix_suggestion}
- Test Name: {test_name}

Generate the complete fixed code that addresses this issue.
Make minimal changes - only fix what's necessary.
Preserve all existing functionality.

Return ONLY the complete fixed Python code, no explanations.
"""

            context = {
                "original_code": original_code,
                "root_cause": failure.get("root_cause", ""),
                "fix_type": failure.get("fix_type", ""),
                "fix_location": failure.get("fix_location", ""),
                "fix_suggestion": failure.get("fix_suggestion", ""),
                "test_name": failure.get("test_name", ""),
            }

            try:
                fixed_code = await execute_task(prompt, context, timeout=300)  # Increased to 5 minutes for code fixing

                # Clean up the code
                fixed_code = self._clean_code(fixed_code)

                # Create fix object
                fix = CodeFix(
                    file_path=code_path,
                    original_code=original_code,
                    fixed_code=fixed_code,
                    test_file="",  # Will be set by caller
                    failure_reason=failure.get("root_cause", ""),
                    fix_description=failure.get("fix_suggestion", ""),
                    timestamp=datetime.now().isoformat(),
                )

                fixes.append(fix)

                # Update original_code for next iteration (cumulative fixes)
                original_code = fixed_code

            except Exception as e:
                print(f"Failed to generate fix for {failure.get('test_name')}: {e}")
                continue

        return fixes

    def _clean_code(self, code: str) -> str:
        """Clean generated code by removing markdown formatting."""
        code = code.strip()

        # Remove markdown code blocks
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]

        if code.endswith("```"):
            code = code[:-3]

        return code.strip() + "\n"

    def apply_refinement(self, fixes: List[CodeFix]) -> int:
        """Apply generated fixes to code files.

        Args:
            fixes: List of fixes to apply

        Returns:
            Number of fixes successfully applied
        """
        applied = 0

        for fix in fixes:
            try:
                # Back up original file
                code_file = Path(fix.file_path)
                backup_file = self.session_dir / f"{code_file.name}.backup.{applied}"
                backup_file.write_text(fix.original_code)

                # Apply the fix
                code_file.write_text(fix.fixed_code)

                # Log the fix
                append_jsonl(asdict(fix), self.fixes_log)

                applied += 1

            except Exception as e:
                print(f"Failed to apply fix to {fix.file_path}: {e}")
                continue

        return applied

    async def iterate_until_pass(
        self, test_path: str, code_path: str, max_iterations: int = 3
    ) -> Tuple[bool, List[IterationResult]]:
        """Run the full feedback loop until tests pass or max iterations reached.

        Args:
            test_path: Path to test file
            code_path: Path to code file to fix
            max_iterations: Maximum number of fix iterations

        Returns:
            Tuple of (success, iteration_results)
        """
        iterations = []

        for iteration in range(1, max_iterations + 1):
            print(f"\n=== Iteration {iteration}/{max_iterations} ===")

            # Run tests
            print("Running tests...")
            if iteration == 1:
                print("   ⏳ Initial test run may take a couple of minutes...")
            test_result = await self.run_tests(test_path)

            print(f"Results: {test_result.passed} passed, {test_result.failed} failed, {test_result.errors} errors")

            # Check if all tests pass
            if test_result.failed == 0 and test_result.errors == 0:
                # Success!
                iteration_result = IterationResult(
                    iteration=iteration,
                    test_result=test_result,
                    fixes_applied=[],
                    success=True,
                    timestamp=datetime.now().isoformat(),
                )
                iterations.append(iteration_result)
                append_jsonl(asdict(iteration_result), self.iteration_log)

                print("✅ All tests passing!")
                return True, iterations

            # Analyze failures
            print("Analyzing failures...")
            failure_analyses = await self.analyze_failures(test_result)

            if not failure_analyses:
                print("No failures to analyze")
                break

            # Generate fixes
            print(f"Generating fixes for {len(failure_analyses)} failures...")
            print("   ⏳ This may take a few minutes for complex fixes...")
            fixes = await self.generate_fixes(failure_analyses, code_path)

            if not fixes:
                print("No fixes generated")
                break

            # Apply fixes
            print(f"Applying {len(fixes)} fixes...")
            applied = self.apply_refinement(fixes)

            # Record iteration
            iteration_result = IterationResult(
                iteration=iteration,
                test_result=test_result,
                fixes_applied=fixes,
                success=False,
                timestamp=datetime.now().isoformat(),
            )
            iterations.append(iteration_result)
            append_jsonl(asdict(iteration_result), self.iteration_log)

            print(f"Applied {applied} fixes")

            if applied == 0:
                print("No fixes could be applied")
                break

        # Max iterations reached without success
        print(f"❌ Max iterations ({max_iterations}) reached. Tests still failing.")
        return False, iterations

    async def batch_feedback_loop(
        self, test_code_pairs: List[Tuple[str, str]], max_iterations: int = 3
    ) -> Dict[str, Dict[str, Any]]:
        """Run feedback loop for multiple test-code pairs.

        Args:
            test_code_pairs: List of (test_path, code_path) tuples
            max_iterations: Max iterations per pair

        Returns:
            Dictionary with results for each pair
        """
        results = {}

        for test_path, code_path in test_code_pairs:
            print(f"\n{'=' * 60}")
            print(f"Processing: {code_path}")
            print(f"Test: {test_path}")
            print("=" * 60)

            success, iterations = await self.iterate_until_pass(test_path, code_path, max_iterations)

            results[code_path] = {
                "success": success,
                "iterations": len(iterations),
                "final_test_result": iterations[-1].test_result if iterations else None,
                "total_fixes": sum(len(it.fixes_applied) for it in iterations),
            }

        return results

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of the feedback loop session.

        Returns:
            Dictionary with session statistics
        """
        # Load all iterations
        iterations = []
        if self.iteration_log.exists():
            with open(self.iteration_log, "r") as f:
                for line in f:
                    if line.strip():
                        iterations.append(json.loads(line))

        # Load all fixes
        fixes = []
        if self.fixes_log.exists():
            with open(self.fixes_log, "r") as f:
                for line in f:
                    if line.strip():
                        fixes.append(json.loads(line))

        # Calculate statistics
        total_iterations = len(iterations)
        successful_iterations = sum(1 for it in iterations if it.get("success"))
        total_fixes = len(fixes)

        # Group by file
        fixes_by_file = {}
        for fix in fixes:
            file_path = fix.get("file_path", "unknown")
            if file_path not in fixes_by_file:
                fixes_by_file[file_path] = 0
            fixes_by_file[file_path] += 1

        return {
            "session_id": self.session_id,
            "total_iterations": total_iterations,
            "successful_iterations": successful_iterations,
            "total_fixes_applied": total_fixes,
            "fixes_by_file": fixes_by_file,
            "success_rate": f"{(successful_iterations / total_iterations * 100):.1f}%"
            if total_iterations > 0
            else "N/A",
        }
