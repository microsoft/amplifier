"""Safety checks for auto-healing."""

from pathlib import Path

SAFE_PATTERNS = ["**/utils/*.py", "**/tools/*.py", "**/helpers/*.py", "**/test_*.py"]
UNSAFE_PATTERNS = ["**/core.py", "**/cli.py", "**/main.py", "**/__init__.py", "**/api/*.py"]


def is_safe_module(module_path: Path) -> bool:
    """Check if module is safe for auto-healing."""
    module_str = str(module_path)

    # Check unsafe patterns first
    if any(Path(module_str).match(pattern) for pattern in UNSAFE_PATTERNS):
        return False

    # Check safe patterns
    if any(Path(module_str).match(pattern) for pattern in SAFE_PATTERNS):
        return True

    # Allow leaf modules
    return bool("test" in module_str or "util" in module_str or "helper" in module_str)
