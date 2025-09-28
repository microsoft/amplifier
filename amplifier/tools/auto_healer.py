"""Core auto-healing functionality."""

import logging
import subprocess
import tempfile
import time
from pathlib import Path

from amplifier.tools.git_utils import cleanup_branch
from amplifier.tools.git_utils import commit_and_merge
from amplifier.tools.git_utils import create_healing_branch
from amplifier.tools.healing_models import HealingResult
from amplifier.tools.healing_prompts import select_best_prompt
from amplifier.tools.healing_results import save_results
from amplifier.tools.healing_safety import is_safe_module
from amplifier.tools.healing_validator import validate_module
from amplifier.tools.health_monitor import HealthMonitor

logger = logging.getLogger(__name__)


def heal_batch(max_modules: int, threshold: float, project_root: Path) -> list[HealingResult]:
    """Heal multiple modules that need improvement."""
    candidates = _get_candidates(threshold, project_root)
    if not candidates:
        return []

    results = []
    for health in candidates[:max_modules]:
        result = heal_single_module(Path(health.module_path), health.health_score, project_root)
        results.append(result)
        if result.status == "failed":
            break

    save_results(results, project_root)
    return results


def heal_single_module(module_path: Path, health_score: float, project_root: Path) -> HealingResult:
    """Attempt to heal one module."""
    if not is_safe_module(module_path):
        return HealingResult.skipped(module_path, health_score, "Unsafe module")

    start_time = time.time()
    branch_name = create_healing_branch(module_path.stem)

    try:
        _apply_healing(module_path, health_score, project_root, branch_name)
        return HealingResult.success(
            module_path, health_score, _get_new_score(module_path, project_root), time.time() - start_time
        )
    except Exception as e:
        logger.error(f"Healing failed: {e}")
        return HealingResult.failed(module_path, health_score, str(e), time.time() - start_time)
    finally:
        cleanup_branch(branch_name)


def _get_candidates(threshold: float, project_root: Path) -> list:
    """Get list of modules needing healing."""
    monitor = HealthMonitor(project_root)
    candidates = monitor.get_healing_candidates(threshold)
    safe_candidates = [h for h in candidates if is_safe_module(Path(h.module_path))]

    if not safe_candidates:
        logger.info("No safe modules need healing")

    return safe_candidates


def _apply_healing(module_path: Path, health_score: float, project_root: Path, branch_name: str) -> None:
    """Apply healing to a module."""
    prompt = select_best_prompt(module_path.name, health_score)

    with tempfile.NamedTemporaryFile(suffix=".txt") as f:
        f.write(prompt.encode())
        f.flush()

        if not _run_healing_tool(module_path, f.name):
            raise Exception("Healing failed")

        if not validate_module(module_path, project_root):
            raise Exception("Validation failed")

        new_score = _get_new_score(module_path, project_root)
        if new_score <= health_score:
            raise Exception("No improvement")

        if not commit_and_merge(module_path, branch_name, health_score, new_score):
            raise Exception("Git operations failed")


def _run_healing_tool(module_path: Path, prompt_file: str) -> bool:
    """Run the healing tool on a module."""
    result = subprocess.run(
        [
            ".aider-venv/bin/aider",
            "--model",
            "claude-3-5-sonnet-20241022",
            "--yes",
            "--no-auto-commits",
            "--message-file",
            prompt_file,
            str(module_path),
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    return result.returncode == 0


def _get_new_score(module_path: Path, project_root: Path) -> float:
    """Get updated health score for a module."""
    return HealthMonitor(project_root).analyze_module(module_path).health_score


class AutoHealer:
    """Auto-healer for modules."""

    def __init__(self, project_root: Path = Path(".")):
        self.project_root = project_root
        self.monitor = HealthMonitor(project_root)

    def heal_module_safely(self, module_path: Path) -> HealingResult:
        """Heal a module with safety checks."""
        health = self.monitor.analyze_module(module_path)
        return heal_single_module(module_path, health.health_score, self.project_root)

    def heal_batch_modules(self, max_modules: int = 10, threshold: float = 70) -> list[HealingResult]:
        """Heal multiple modules."""
        return heal_batch(max_modules, threshold, self.project_root)
