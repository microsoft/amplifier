"""Auto-healing functionality for Python modules."""

import logging
import time
from dataclasses import dataclass
from pathlib import Path

from amplifier.tools.claude_healer import run_claude_healing
from amplifier.tools.git_utils import cleanup_branch
from amplifier.tools.git_utils import commit_and_merge
from amplifier.tools.git_utils import create_healing_branch
from amplifier.tools.health_monitor import HealthMonitor

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "healing" / "prompts"
DEFAULT_PROMPT_PATH = PROMPTS_DIR / "simplify.md"

logger = logging.getLogger(__name__)


@dataclass
class HealingResult:
    """Result of healing attempt."""

    module_path: str
    status: str  # success, failed, skipped
    health_before: float
    health_after: float = 0
    reason: str = ""
    duration: float = 0

    @classmethod
    def success(cls, path: Path, before: float, after: float, duration: float):
        """Create success result."""
        return cls(str(path), "success", before, after, "", duration)

    @classmethod
    def failed(cls, path: Path, before: float, reason: str, duration: float):
        """Create failure result."""
        return cls(str(path), "failed", before, 0, reason, duration)

    @classmethod
    def skipped(cls, path: Path, before: float, reason: str):
        """Create skipped result."""
        return cls(str(path), "skipped", before, 0, reason, 0)


def heal_batch(max_modules: int, threshold: float, project_root: Path) -> list[HealingResult]:
    """Heal multiple modules in batch."""
    monitor = HealthMonitor(project_root)
    candidates = monitor.get_healing_candidates(threshold)

    if not candidates:
        logger.info("No modules need healing")
        return []

    results = []
    for health in candidates[:max_modules]:
        module_path = Path(health.module_path)
        logger.info(f"Healing {module_path.name} (health: {health.health_score:.1f})")

        result = heal_single_module(module_path, health.health_score, project_root)
        results.append(result)

        if result.status == "success":
            logger.info(
                f"Successfully healed {module_path.name}: +{result.health_after - result.health_before:.1f} points"
            )
        else:
            logger.warning(f"Failed to heal {module_path.name}: {result.reason}")

    return results


def heal_single_module(module_path: Path, health_before: float, project_root: Path) -> HealingResult:
    """Heal a single module."""
    start_time = time.time()

    # Skip if not safe to heal
    is_safe, reason = is_safe_module(module_path)
    if not is_safe:
        return HealingResult.skipped(module_path, health_before, reason)

    try:
        # Create a branch for healing
        branch_name = create_healing_branch(module_path.stem)

        # Run Claude healing
        prompt_path = DEFAULT_PROMPT_PATH
        if not prompt_path.exists():
            cleanup_branch(branch_name)
            return HealingResult.failed(
                module_path,
                health_before,
                f"Healing prompt not found at {prompt_path}",
                time.time() - start_time,
            )

        success = run_claude_healing(module_path, prompt_path)

        if not success:
            cleanup_branch(branch_name)
            return HealingResult.failed(module_path, health_before, "Healing failed", time.time() - start_time)

        # Validate the healed module
        if not validate_module(module_path):
            cleanup_branch(branch_name)
            return HealingResult.failed(module_path, health_before, "Validation failed", time.time() - start_time)

        # Check new health score
        monitor = HealthMonitor(project_root)
        new_health = monitor._analyze_module(module_path)
        if not new_health:
            cleanup_branch(branch_name)
            return HealingResult.failed(
                module_path, health_before, "Could not analyze healed module", time.time() - start_time
            )

        # Commit and merge if improved
        if new_health.health_score > health_before:
            if commit_and_merge(module_path, branch_name, health_before, new_health.health_score):
                return HealingResult.success(
                    module_path, health_before, new_health.health_score, time.time() - start_time
                )
            return HealingResult.failed(module_path, health_before, "Merge failed", time.time() - start_time)
        cleanup_branch(branch_name)
        return HealingResult.failed(module_path, health_before, "No improvement", time.time() - start_time)

    except Exception as e:
        logger.error(f"Healing failed: {e}")
        return HealingResult.failed(module_path, health_before, str(e), time.time() - start_time)


def is_safe_module(module_path: Path) -> tuple[bool, str]:
    """Check if module is safe to heal.

    Returns:
        Tuple of (is_safe, reason) where reason explains why if not safe
    """
    # Don't heal critical files
    unsafe_patterns = ["__init__", "setup", "config", "settings", "test_"]
    name = module_path.stem.lower()

    for pattern in unsafe_patterns:
        if pattern in name:
            return False, f"Critical file pattern '{pattern}' in filename"

    # Don't heal files that are too large (may timeout)
    max_lines = 400
    try:
        with open(module_path, encoding="utf-8") as f:
            line_count = sum(1 for _ in f)

        if line_count > max_lines:
            return False, f"File too large ({line_count} lines, limit: {max_lines})"
    except Exception as e:
        logger.warning(f"Could not check file size for {module_path}: {e}")
        # Allow healing if we can't check size

    return True, ""


def validate_module(module_path: Path) -> bool:
    """Validate a healed module."""
    try:
        # Check syntax
        with open(module_path) as f:
            code = f.read()

        compile(code, str(module_path), "exec")

        # Check imports work
        import ast

        tree = ast.parse(code)
        for node in ast.walk(tree):  # noqa: SIM110
            # Basic check that relative imports are reasonable
            if isinstance(node, ast.ImportFrom) and node.level > 5:
                return False

        return True
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False
