"""Module validation for auto-healing."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def validate_syntax(module_path: Path) -> bool:
    """Check module syntax."""
    try:
        with open(module_path) as f:
            compile(f.read(), str(module_path), "exec")
        return True
    except SyntaxError as e:
        logger.error(f"Syntax error in {module_path}: {e}")
        return False


def validate_tests(module_path: Path, project_root: Path) -> bool:
    """Run module tests if they exist."""
    test_file = project_root / "tests" / f"test_{module_path.stem}.py"
    if not test_file.exists():
        return True

    result = subprocess.run(["python", "-m", "pytest", str(test_file), "-v"], capture_output=True, timeout=30)
    if result.returncode != 0:
        logger.error(f"Tests failed for {module_path}")
        return False
    return True


def validate_imports(module_path: Path, project_root: Path) -> bool:
    """Verify module can be imported."""
    try:
        result = subprocess.run(
            ["python", "-c", f"import amplifier.tools.{module_path.stem}"],
            capture_output=True,
            timeout=5,
            cwd=project_root,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logger.error(f"Import timeout for {module_path}")
        return False


def validate_module(module_path: Path, project_root: Path) -> bool:
    """Run all validation checks."""
    return all(
        [
            validate_syntax(module_path),
            validate_tests(module_path, project_root),
            validate_imports(module_path, project_root),
        ]
    )
