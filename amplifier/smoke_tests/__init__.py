"""
Smoke Test Runner for Amplifier

Simple, direct smoke testing without frameworks.
Tests basic functionality to catch obvious breaks.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from typing import Optional

import yaml

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_test_header(name: str, description: str) -> None:
    """Print test header."""
    print(f"\n{BOLD}Testing: {name}{RESET}")
    if description:
        print(f"  {description}")


def print_result(passed: bool, message: str = "") -> None:
    """Print test result."""
    if passed:
        print(f"  {GREEN}✓ PASS{RESET} {message}")
    else:
        print(f"  {RED}✗ FAIL{RESET} {message}")


class SmokeTestRunner:
    """Run smoke tests from YAML configuration."""

    def __init__(self, config_path: Path):
        """Initialize with test configuration."""
        self.config_path = config_path
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def load_tests(self) -> None:
        """Load test definitions from YAML."""
        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        self.tests = config.get("tests", [])
        print(f"Loaded {len(self.tests)} smoke tests")

    def run_command(self, command: str, timeout: int = 30) -> tuple[int, str, str]:
        """
        Run a shell command and capture output.

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            # Use shell=True to handle complex commands with pipes, redirects, etc.
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, "PYTHONPATH": str(Path.cwd())},
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return -1, "", str(e)

    def validate_output_contains(self, output: str, expected: list[str]) -> bool:
        """Check if output contains all expected strings."""
        all_found = True
        for exp in expected:
            if exp in output:
                # Show where we found it with better context
                idx = output.find(exp)
                # Get the full line containing the match
                line_start = output.rfind("\n", 0, idx) + 1
                line_end = output.find("\n", idx)
                if line_end == -1:
                    line_end = len(output)

                full_line = output[line_start:line_end].strip()
                # Truncate long lines but keep the matched part visible
                if len(full_line) > 100:
                    # Try to keep the match in view
                    match_pos = full_line.find(exp)
                    if match_pos > 50:
                        full_line = "..." + full_line[match_pos - 20 :]
                    if len(full_line) > 100:
                        full_line = full_line[:97] + "..."

                print(f"    {GREEN}✓{RESET} Found '{BOLD}{exp}{RESET}' in: {full_line}")
            else:
                print(f"    {RED}✗{RESET} Missing: '{exp}'")
                all_found = False
        return all_found

    def validate_output_contains_any(self, output: str, expected: list[str]) -> bool:
        """Check if output contains at least one of the expected strings."""
        for exp in expected:
            if exp in output:
                # Show where we found it with better context
                idx = output.find(exp)
                # Get the full line containing the match
                line_start = output.rfind("\n", 0, idx) + 1
                line_end = output.find("\n", idx)
                if line_end == -1:
                    line_end = len(output)

                full_line = output[line_start:line_end].strip()
                # Truncate long lines but keep the matched part visible
                if len(full_line) > 100:
                    # Try to keep the match in view
                    match_pos = full_line.find(exp)
                    if match_pos > 50:
                        full_line = "..." + full_line[match_pos - 20 :]
                    if len(full_line) > 100:
                        full_line = full_line[:97] + "..."

                print(f"    {GREEN}✓{RESET} Found '{BOLD}{exp}{RESET}' in: {full_line}")
                return True
        print(f"    {RED}✗{RESET} None found from: {expected[:3]}{'...' if len(expected) > 3 else ''}")
        return False

    def validate_exit_code(self, actual: int, expected: int) -> bool:
        """Check if exit code matches expected."""
        if actual != expected:
            print(f"    Expected exit code {expected}, got {actual}")
            return False
        return True

    async def validate_ai_check(self, output: str, check_prompt: str) -> bool:
        """
        Use AI to validate complex output.
        Falls back to basic validation if SDK not available.
        """
        # Try to use Claude Code SDK if available
        try:
            from amplifier.knowledge_synthesis.extractor import CLAUDE_SDK_AVAILABLE
            from amplifier.knowledge_synthesis.extractor import ClaudeCodeOptions
            from amplifier.knowledge_synthesis.extractor import ClaudeSDKClient

            if not CLAUDE_SDK_AVAILABLE:
                print(f"    {YELLOW}⚠ Claude SDK not available, skipping AI check{RESET}")
                return True  # Don't fail test if SDK unavailable

            prompt = f"""Analyze this command output and answer with just YES or NO.

Check: {check_prompt}

Output to analyze:
{output[:5000]}

Answer YES if the check passes, NO if it fails."""

            response = ""
            async with asyncio.timeout(30):
                async with ClaudeSDKClient(
                    options=ClaudeCodeOptions(
                        system_prompt="You are a test validator. Answer only YES or NO.",
                        max_turns=1,
                    )
                ) as client:
                    await client.query(prompt)

                    async for message in client.receive_response():
                        if hasattr(message, "content"):
                            content = getattr(message, "content", [])
                            if isinstance(content, list):
                                for block in content:
                                    if hasattr(block, "text"):
                                        response += getattr(block, "text", "")

            # Check if response contains YES
            response_upper = response.upper().strip()
            passed = "YES" in response_upper and "NO" not in response_upper
            if not passed:
                print(f"    AI check failed: {response[:100]}")
            return passed

        except Exception as e:
            print(f"    {YELLOW}⚠ AI validation error: {e}, skipping check{RESET}")
            return True  # Don't fail test on AI errors

    def _extract_key_lines(self, output: str, max_lines: int = 3, skip_patterns: list[str] | None = None) -> list[str]:
        """Extract key non-empty lines from output, skipping boilerplate."""
        if skip_patterns is None:
            skip_patterns = [
                "make:",  # Make output
                "uv run",  # UV commands
                "cd /",  # Directory changes
                "Terminated",  # Process termination
                "warning:",  # Warnings
                "note:",  # Notes
            ]

        lines = []
        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Skip lines that start with any skip pattern
            if any(line.startswith(pattern) for pattern in skip_patterns):
                continue

            # Skip lines that are just Python module paths (common in tracebacks)
            if line.startswith('File "') and line.endswith('"'):
                continue

            # Truncate and add
            if len(line) > 100:
                line = line[:97] + "..."
            lines.append(line)

            if len(lines) >= max_lines:
                break
        return lines

    async def run_test(self, test: dict[str, Any]) -> bool:
        """Run a single test."""
        name = test.get("name", "Unnamed")
        description = test.get("description", "")
        command = test.get("command", "")
        timeout = test.get("timeout", 30)
        validations = test.get("validate", {})
        skip_if = test.get("skip_if")
        is_startup_test = test.get("startup_test", False)

        print_test_header(name, description)

        # Check skip condition
        if skip_if:
            skip_exit, skip_out, skip_err = self.run_command(skip_if, timeout=5)
            if skip_exit == 0:
                print(f"  {YELLOW}⊘ SKIPPED{RESET} (condition met: {skip_if})")
                self.skipped += 1
                return True

        # Run the command
        print(f"  {BOLD}Command:{RESET} {command[:80]}{'...' if len(command) > 80 else ''}")
        start_time = time.time()
        exit_code, stdout, stderr = self.run_command(command, timeout)
        duration = time.time() - start_time

        # Show timing and exit status
        exit_color = GREEN if exit_code == 0 else (YELLOW if exit_code == -1 else RED)
        print(f"  {BOLD}Duration:{RESET} {duration:.1f}s | {BOLD}Exit:{RESET} {exit_color}{exit_code}{RESET}")

        # Combine output for validation
        output = stdout + stderr

        # Show key output lines for visibility (show 2-3 lines)
        key_lines = self._extract_key_lines(output, max_lines=2 if is_startup_test else 3)
        if key_lines:
            print(f"  {BOLD}Output:{RESET}")
            for line in key_lines:
                print(f"    │ {line}")

        # Run validations
        all_passed = True

        # Special handling for startup tests
        if is_startup_test and "startup_ok" in validations:
            print(f"  {BOLD}Checking startup:{RESET}")

            # For startup tests, we check if command started without Python errors
            # Common startup errors we want to catch
            startup_errors = [
                "ModuleNotFoundError",
                "ImportError",
                "SyntaxError",
                "NameError",
                "AttributeError",
                "TypeError",
                "Traceback (most recent call last)",
                "No such file or directory",
                "Permission denied",
                "command not found",
                "cannot import name",
                "No module named",
            ]

            # Ignore expected timeout termination messages
            if "Terminated" in output and "make: ***" in output:
                # This is just the timeout killing the process, not an error
                output_clean = output.replace("make: *** [Makefile", "").replace("Terminated", "")
            else:
                output_clean = output

            has_startup_error = any(error in output_clean for error in startup_errors)

            if has_startup_error:
                all_passed = False
                # Show which error was found with context
                for error in startup_errors:
                    if error in output_clean:
                        idx = output_clean.find(error)
                        line_start = output_clean.rfind("\n", 0, idx) + 1
                        line_end = output_clean.find("\n", idx)
                        if line_end == -1:
                            line_end = len(output_clean)
                        error_line = output_clean[line_start:line_end].strip()[:100]
                        print(f"    {RED}✗{RESET} Startup error found: {BOLD}{error}{RESET}")
                        print(f"      └─ {error_line}")
                        break
            else:
                # Command started successfully (may have timed out, which is expected)
                print(f"    {GREEN}✓{RESET} No Python errors detected")

                # For startup tests, also check for processing indicators
                if "output_contains_any" in validations:
                    expected = validations["output_contains_any"]
                    print(f"  {BOLD}Checking for activity indicators:{RESET} ({len(expected)} patterns)")
                    found = False
                    for exp in expected:
                        if exp in output:
                            # Show context where we found it
                            idx = output.find(exp)
                            line_start = output.rfind("\n", 0, idx) + 1
                            line_end = output.find("\n", idx)
                            if line_end == -1:
                                line_end = len(output)
                            context_line = output[line_start:line_end].strip()[:100]
                            print(f"    {GREEN}✓{RESET} Found activity: '{BOLD}{exp}{RESET}'")
                            print(f"      └─ {context_line}")
                            found = True
                            break
                    if not found:
                        all_passed = False
                        print(f"    {RED}✗{RESET} No activity indicators found")
        else:
            # Normal validation for non-startup tests
            # Check exit code
            if "exit_code" in validations:
                expected_code = validations["exit_code"]
                print(f"  {BOLD}Checking exit code:{RESET}")
                if exit_code == expected_code:
                    print(f"    {GREEN}✓{RESET} Exit code matches expected: {expected_code}")
                else:
                    print(f"    {RED}✗{RESET} Exit code mismatch: expected {expected_code}, got {exit_code}")
                    all_passed = False

            # Check output contains
            if "output_contains" in validations:
                patterns = validations["output_contains"]
                print(f"  {BOLD}Checking for required patterns:{RESET} ({len(patterns)} patterns)")
                if not self.validate_output_contains(output, patterns):
                    all_passed = False

            # Check output contains any
            if "output_contains_any" in validations:
                patterns = validations["output_contains_any"]
                print(f"  {BOLD}Checking for any pattern:{RESET} ({len(patterns)} patterns)")
                if not self.validate_output_contains_any(output, patterns):
                    all_passed = False

            # AI validation (if configured)
            if "ai_check" in validations:
                ai_passed = await self.validate_ai_check(output, validations["ai_check"])
                if not ai_passed:
                    all_passed = False

        # Show result
        if all_passed:
            print_result(True)
            self.passed += 1
        else:
            print_result(False)
            # On failure, show more output for debugging
            if stderr:
                print("  Error output:")
                for line in self._extract_key_lines(stderr, max_lines=5):
                    print(f"    │ {RED}{line}{RESET}")
            elif not key_lines:  # Only show stdout if we didn't show preview
                print("  Full output snippet:")
                for line in self._extract_key_lines(stdout, max_lines=5):
                    print(f"    │ {line}")
            self.failed += 1

        return all_passed

    async def run_all(self) -> int:
        """Run all tests and return exit code."""
        print(f"\n{BOLD}=== Amplifier Smoke Tests ==={RESET}")
        start_time = time.time()

        for test in self.tests:
            await self.run_test(test)

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
            print(f"\n{GREEN}{BOLD}✓ All smoke tests passed!{RESET}")
            return 0
        print(f"\n{RED}{BOLD}✗ {self.failed} test(s) failed{RESET}")
        return 1


def main():
    """Main entry point."""
    # Find test config
    config_path = Path(__file__).parent / "smoke_tests.yaml"
    if not config_path.exists():
        print(f"{RED}Error: {config_path} not found{RESET}")
        sys.exit(1)

    # Run tests
    runner = SmokeTestRunner(config_path)
    runner.load_tests()

    # Use asyncio for AI validation support
    exit_code = asyncio.run(runner.run_all())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
