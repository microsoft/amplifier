"""
AI-Driven Smoke Test Runner

Simple test runner that uses AI for all evaluation.
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

import yaml

from .ai_evaluator import AIEvaluator
from .config import config

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


class AITestRunner:
    """Run tests with AI evaluation."""

    def __init__(self, test_file: Path):
        """Initialize with test file."""
        self.test_file = test_file
        self.evaluator = AIEvaluator()
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def load_tests(self) -> list:
        """Load test definitions from YAML."""
        with open(self.test_file) as f:
            data = yaml.safe_load(f)
        return data.get("tests", [])

    def run_command(self, command: str, timeout: int = 30) -> tuple[int, str]:
        """Run a command and return exit code and output."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=config.get_test_env(),
            )
            output = result.stdout + "\n" + result.stderr
            return result.returncode, output
        except subprocess.TimeoutExpired:
            return -1, f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, str(e)

    async def run_test(self, test: dict) -> bool:
        """Run a single test."""
        name = test.get("name", "Unnamed")
        command = test.get("command", "")
        success_criteria = test.get("success_criteria", "Command runs without errors")
        timeout = test.get("timeout", 30)

        print(f"\n{BOLD}Test:{RESET} {name}")
        print(f"  Command: {command[:80]}{'...' if len(command) > 80 else ''}")
        print(f"  Criteria: {success_criteria}")

        # Run command
        start_time = time.time()
        exit_code, output = self.run_command(command, timeout)
        duration = time.time() - start_time

        print(f"  Duration: {duration:.1f}s | Exit: {exit_code}")

        # Evaluate with AI (async)
        print(f"  {BOLD}AI Evaluation:{RESET}", end=" ")
        passed, reasoning = await self.evaluator.evaluate(command, output, success_criteria, timeout=config.ai_timeout)

        if passed:
            print(f"{GREEN}✓ PASS{RESET}")
            print(f"    {reasoning}")
            self.passed += 1
        else:
            print(f"{RED}✗ FAIL{RESET}")
            print(f"    {reasoning}")
            self.failed += 1

            # Show some output on failure
            lines = output.strip().split("\n")[:5]
            if lines:
                print(f"  {BOLD}Output snippet:{RESET}")
                for line in lines:
                    if line.strip():
                        print(f"    │ {line[:100]}")

        return passed

    async def run_all(self) -> int:
        """Run all tests and return exit code."""
        print(f"\n{BOLD}=== AI-Driven Smoke Tests ==={RESET}")

        # Setup test environment
        print("Setting up test environment...")
        config.setup_test_environment()

        # Load tests
        tests = self.load_tests()
        print(f"Loaded {len(tests)} tests")

        # Note: We don't check AI availability here since it's handled in the evaluator

        # Run tests
        start_time = time.time()
        for test in tests:
            await self.run_test(test)

        # Cleanup
        print("\nCleaning up test environment...")
        config.cleanup_test_environment()

        # Summary
        duration = time.time() - start_time
        total = self.passed + self.failed + self.skipped

        print(f"\n{BOLD}=== Summary ==={RESET}")
        print(f"  Total: {total} tests in {duration:.1f}s")
        print(f"  {GREEN}Passed: {self.passed}{RESET}")
        if self.failed > 0:
            print(f"  {RED}Failed: {self.failed}{RESET}")
        if self.skipped > 0:
            print(f"  {YELLOW}Skipped: {self.skipped}{RESET}")

        if self.failed == 0:
            print(f"\n{GREEN}{BOLD}✓ All tests passed!{RESET}")
            return 0
        print(f"\n{RED}{BOLD}✗ {self.failed} test(s) failed{RESET}")
        return 1


async def async_main():
    """Async main entry point."""
    test_file = Path(__file__).parent / "tests.yaml"
    if not test_file.exists():
        print(f"{RED}Error: {test_file} not found{RESET}")
        sys.exit(1)

    runner = AITestRunner(test_file)
    exit_code = await runner.run_all()
    sys.exit(exit_code)


def main():
    """Main entry point."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
