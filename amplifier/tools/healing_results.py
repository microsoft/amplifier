"""Handle healing results storage and reporting."""

import json
import logging
from pathlib import Path

from amplifier.tools.healing_models import HealingResult

logger = logging.getLogger(__name__)


def save_results(results: list[HealingResult], project_root: Path) -> None:
    """Save healing results and log summary."""
    results_file = project_root / ".data" / "healing_results.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)

    all_results = []
    if results_file.exists():
        with open(results_file) as f:
            all_results = json.load(f)

    all_results.extend([r.dict() for r in results])
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)

    _log_summary(results)


def _log_summary(results: list[HealingResult]) -> None:
    """Log healing results summary."""
    successful = [r for r in results if r.status == "success"]
    if not successful:
        return

    avg_improvement = sum(r.health_after - r.health_before for r in successful) / len(successful)
    logger.info(
        f"\nHealing Summary:\n"
        f"  Successful: {len(successful)}\n"
        f"  Failed: {len(results) - len(successful)}\n"
        f"  Average improvement: {avg_improvement:.1f} points"
    )
