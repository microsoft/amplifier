#!/usr/bin/env python3
"""Check for stubs and placeholders in Python code."""

import re
import sys
from pathlib import Path

# Try to import tomllib (Python 3.11+) or tomli (fallback)
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("Warning: Cannot read pyproject.toml (install tomli for Python <3.11)", file=sys.stderr)
        tomllib = None


def read_pyproject_exclusions():
    """Read exclude patterns from pyproject.toml."""
    default_excludes = {".venv", "__pycache__", ".git", "node_modules", ".tox", "templates"}

    if not tomllib or not Path("pyproject.toml").exists():
        return default_excludes

    try:
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)

        # Get pyright exclusions
        pyright_excludes = config.get("tool", {}).get("pyright", {}).get("exclude", [])

        # Convert patterns to directory names for simple matching
        # Handle patterns like "**/__pycache__", ".venv/**"
        excludes = set()
        for pattern in pyright_excludes:
            # Strip glob patterns to get directory name
            pattern = pattern.strip("/").strip("*")
            if pattern:
                excludes.add(pattern)

        # Always include some critical exclusions
        excludes.update(default_excludes)
        return excludes

    except Exception as e:
        print(f"Warning: Could not read pyproject.toml: {e}", file=sys.stderr)
        return default_excludes


def is_legitimate_pattern(filepath, line_num, line):
    """Check if a pattern is a legitimate use rather than a stub."""
    # Quick heuristics for legitimate patterns

    # Mock functions in test files are legitimate
    if ("def mock_" in line or "def fake_" in line or "def dummy_" in line) and (
        "test" in str(filepath) or "conftest" in str(filepath)
    ):
        return True

    # Click CLI group pattern: @click.group() followed by pass
    if "pass" in line:
        # Try to read a few lines before to check for @click.group()
        try:
            with open(filepath, encoding="utf-8") as f:
                lines = f.readlines()
                if line_num > 1:
                    # Check previous lines for click decorators
                    for i in range(max(0, line_num - 5), line_num):
                        if "@click.group" in lines[i] or "@cli.group" in lines[i]:
                            return True
                        # Also check for click.command
                        if "@click.command" in lines[i] or "@cli.command" in lines[i]:
                            return True
        except Exception:
            pass

    # Empty __init__.py files are legitimate
    if filepath.name == "__init__.py" and "pass" in line:
        return True

    # Abstract methods with NotImplementedError are legitimate
    if "NotImplementedError" in line:
        try:
            with open(filepath, encoding="utf-8") as f:
                lines = f.readlines()
                if line_num > 1:
                    # Check for @abstractmethod decorator
                    for i in range(max(0, line_num - 3), line_num):
                        if "@abstractmethod" in lines[i] or "@abc.abstractmethod" in lines[i]:
                            return True
        except Exception:
            pass

    # Protocol definitions may have empty methods with pass or ...
    if "pass" in line or line.strip() == "...":
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
                # Simple check for Protocol usage
                if "Protocol" in content and (
                    "from typing import Protocol" in content or "from typing_extensions import Protocol" in content
                ):
                    # Could be a protocol definition
                    return True
        except Exception:
            pass

    # Intentional exception silencing patterns
    if re.search(r"except.*:\s*pass", line):
        # This could be legitimate graceful degradation
        # Without more context, we'll allow it with a note
        return True

    # Check if pass is inside an except block (multi-line)
    if "pass" in line and line.strip() == "pass":
        try:
            with open(filepath, encoding="utf-8") as f:
                lines = f.readlines()
                # Look backwards for except statement
                for i in range(max(0, line_num - 5), line_num):
                    if "except" in lines[i] and ":" in lines[i]:
                        # Check if we're still in the except block (proper indentation)
                        except_indent = len(lines[i]) - len(lines[i].lstrip())
                        pass_indent = len(line) - len(line.lstrip())
                        if pass_indent > except_indent:
                            return True
        except Exception:
            pass

    return False


# Patterns that indicate stubs/placeholders
STUB_PATTERNS = [
    (r"raise\s+NotImplementedError", "NotImplementedError"),
    (r"#\s*TODO[:\s]", "TODO comment"),
    (r"#\s*FIXME[:\s]", "FIXME comment"),
    (r"^\s*pass\s*$", "Empty pass statement"),
    (r"^\s*\.\.\.\s*$", "Ellipsis placeholder"),
    (r'return\s+["\']not\s+implemented', "Not implemented return"),
    (r"def\s+mock_", "Mock function"),
    (r"def\s+fake_", "Fake function"),
    (r"def\s+dummy_", "Dummy function"),
    (r"#.*coming\s+soon", "Coming soon comment"),
]


def check_file(filepath):
    """Check a single file for stubs."""
    violations = []

    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, 1):
        for pattern, desc in STUB_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE) and not is_legitimate_pattern(filepath, line_num, line):
                violations.append((filepath, line_num, desc, line.strip()))

    return violations


def main():
    """Check all Python files for stubs."""
    # Read exclusions from pyproject.toml
    exclude_dirs = read_pyproject_exclusions()

    print(f"Using exclusions: {sorted(exclude_dirs)}")

    # Find all Python files
    root = Path(".")
    py_files = []

    for file in root.rglob("*.py"):
        # Skip excluded directories
        if any(excluded in str(file) for excluded in exclude_dirs):
            continue
        # Skip test files that test stub detection
        if "test_stub" in file.name:
            continue
        py_files.append(file)

    # Check each file
    all_violations = []
    for file in py_files:
        # Skip the stub checker itself
        if "check_stubs.py" in file.name:
            continue
        violations = check_file(file)
        all_violations.extend(violations)

    # Report results
    if all_violations:
        print("✗ STUB VIOLATIONS FOUND:", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        for filepath, line_num, desc, content in all_violations:
            print(f"\n{filepath}:{line_num}", file=sys.stderr)
            print(f"  Type: {desc}", file=sys.stderr)
            print(f"  Line: {content[:100]}", file=sys.stderr)
        print(f"\nTotal violations: {len(all_violations)}", file=sys.stderr)
        sys.exit(1)
    else:
        print("✓ No stubs or placeholders found")
        sys.exit(0)


if __name__ == "__main__":
    main()
