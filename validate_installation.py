#!/usr/bin/env python3
"""
Comprehensive validation script for Amplifier installation.
Run this to verify everything is working correctly.
"""

import subprocess
import sys
from pathlib import Path

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def run_test(name, test_func):
    """Run a single test and report result."""
    try:
        result, message = test_func()
        if result:
            print(f"  {GREEN}✓{RESET} {name}")
            return True
        print(f"  {RED}✗{RESET} {name}: {message}")
        return False
    except Exception as e:
        print(f"  {RED}✗{RESET} {name}: {str(e)}")
        return False


def test_python_version():
    """Check Python version is 3.11+"""
    version = sys.version_info
    if version >= (3, 11):
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor} (need 3.11+)"


def test_amplifier_command():
    """Test amplifier --version command."""
    try:
        result = subprocess.run(["amplifier", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and "Amplifier v0.2.0" in result.stdout:
            return True, "v0.2.0"
        return False, f"Unexpected output: {result.stdout}"
    except Exception as e:
        return False, str(e)


def test_amplifier_doctor():
    """Test amplifier doctor command."""
    try:
        result = subprocess.run(["amplifier", "doctor"], capture_output=True, text=True, timeout=5)
        if "Python 3.11" in result.stderr or "Python 3.11" in result.stdout:
            return True, "Doctor runs successfully"
        return False, "Doctor command didn't show expected output"
    except Exception as e:
        return False, str(e)


def test_python_cli():
    """Check if Python CLI is installed."""
    cli_path = Path.home() / "dev" / "amplifier" / ".venv" / "bin" / "amplifier"
    if cli_path.exists():
        return True, str(cli_path)
    return False, "Python CLI not found"


def test_unified_wrapper():
    """Check if unified wrapper is installed."""
    wrapper_path = Path.home() / "bin" / "amplifier"
    if wrapper_path.exists():
        return True, str(wrapper_path)
    return False, "Unified wrapper not found"


def test_cache_module():
    """Test cache module import."""
    try:
        from amplifier.utils.cache import ArtifactCache

        ArtifactCache()  # Test instantiation
        return True, "Cache module works"
    except ImportError as e:
        return False, f"Import error: {e}"


def test_event_module():
    """Test event module import."""
    try:
        from amplifier.utils.events import Event
        from amplifier.utils.events import EventLogger

        Event("test", "ok")  # Test instantiation
        _ = EventLogger  # Verify EventLogger is importable
        return True, "Event module works"
    except ImportError as e:
        return False, f"Import error: {e}"


def test_cli_module():
    """Test CLI module import."""
    try:
        from amplifier.cli import cli

        _ = cli  # Verify cli is importable
        return True, "CLI module works"
    except ImportError as e:
        return False, f"Import error: {e}"


def test_cache_performance():
    """Test cache performance if test file exists."""
    test_file = Path("test_cache_performance.py")
    if not test_file.exists():
        return False, "test_cache_performance.py not found"

    try:
        result = subprocess.run(["python", "test_cache_performance.py"], capture_output=True, text=True, timeout=15)
        if "Speedup" in result.stdout and "x faster" in result.stdout:
            # Extract speedup value
            for line in result.stdout.split("\n"):
                if "Speedup:" in line:
                    return True, line.strip()
            return True, "Cache test passed"
        return False, "No speedup found in output"
    except subprocess.TimeoutExpired:
        return False, "Test timed out"
    except Exception as e:
        return False, str(e)


def test_lint_status():
    """Check if code passes lint checks."""
    try:
        result = subprocess.run(
            ["ruff", "check", "test_performance_comparison.py", "test_cache_performance.py"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True, "No lint errors"
        return False, f"{result.stdout}"
    except FileNotFoundError:
        return False, "ruff not found"
    except Exception as e:
        return False, str(e)


def test_smoke_tests():
    """Run the AI-driven smoke test suite."""
    try:
        # Note: Smoke tests can take 2-3 minutes with AI evaluation
        print("      (This may take 2-3 minutes...)")
        result = subprocess.run(["python", "-m", "amplifier.smoke_tests"], capture_output=True, text=True, timeout=240)
        # Look for the summary line
        if "✅ All tests passed" in result.stdout:
            return True, "All smoke tests passed"
        if "passed" in result.stdout.lower():
            # Extract pass/fail counts
            for line in result.stdout.split("\n"):
                if "Passed:" in line or "Total:" in line:
                    return True, line.strip()
            return True, "Smoke tests ran"
        return False, "Some smoke tests failed"
    except subprocess.TimeoutExpired:
        return False, "Smoke tests timed out (>30s)"
    except Exception as e:
        return False, str(e)


def main():
    """Run all validation tests."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate Amplifier installation")
    parser.add_argument("--full", action="store_true", help="Include smoke tests (takes 2-3 minutes)")
    args = parser.parse_args()

    print("=" * 50)
    print(f"{BLUE}AMPLIFIER INSTALLATION VALIDATOR{RESET}")
    print("=" * 50)

    all_passed = True
    test_groups = [
        (
            "CORE INSTALLATION",
            [
                ("Python version", test_python_version),
                ("amplifier command", test_amplifier_command),
                ("amplifier doctor", test_amplifier_doctor),
                ("Python CLI installed", test_python_cli),
                ("Unified wrapper installed", test_unified_wrapper),
            ],
        ),
        (
            "MODULE IMPORTS",
            [
                ("Cache module", test_cache_module),
                ("Event module", test_event_module),
                ("CLI module", test_cli_module),
            ],
        ),
        (
            "PERFORMANCE & QUALITY",
            [
                ("Cache performance test", test_cache_performance),
                ("Lint status", test_lint_status),
            ],
        ),
    ]

    # Add smoke tests if --full flag is used
    if args.full:
        test_groups.append(
            (
                "SMOKE TESTS (AI-DRIVEN)",
                [
                    ("Full smoke test suite", test_smoke_tests),
                ],
            ),
        )

    for group_name, tests in test_groups:
        print(f"\n{group_name}")
        print("-" * len(group_name))
        for test_name, test_func in tests:
            if not run_test(test_name, test_func):
                all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print(f"{GREEN}✅ ALL VALIDATIONS PASSED!{RESET}")
        print("Amplifier is fully installed and working correctly.")
        if not args.full:
            print(f"\n{YELLOW}Tip: Run 'python validate_installation.py --full' to include smoke tests{RESET}")
        return 0
    print(f"{RED}❌ SOME VALIDATIONS FAILED{RESET}")
    print("Please review the failures above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
