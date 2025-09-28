#!/usr/bin/env python3
"""Simple parallel module healer."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from amplifier.tools.auto_healer import AutoHealer
from amplifier.tools.auto_healer import HealingResult
from amplifier.tools.health_monitor import HealthMonitor

logger = logging.getLogger(__name__)


class ParallelHealer:
    """Heal multiple modules in parallel."""

    def __init__(self, project_root: Path = Path("."), max_workers: int = 3):
        self.project_root = project_root
        self.max_workers = max_workers
        self.monitor = HealthMonitor(project_root)
        self.healer = AutoHealer(project_root)

    async def heal_module(self, module_path: Path) -> HealingResult:
        """Heal a single module."""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as pool:
            return await loop.run_in_executor(pool, self.healer.heal_module_safely, module_path)

    async def heal_batch(self, max_modules: int = 10, threshold: float = 70) -> list[HealingResult | BaseException]:
        """Heal multiple modules in parallel."""
        candidates = self.monitor.get_healing_candidates(threshold)
        modules = [Path(h.module_path) for h in candidates[:max_modules]]

        if not modules:
            return []

        tasks = [self.heal_module(m) for m in modules]
        return await asyncio.gather(*tasks, return_exceptions=True)


def main():
    """Run parallel healing."""
    import argparse

    parser = argparse.ArgumentParser(description="Heal modules in parallel")
    parser.add_argument("--max", type=int, default=5, help="Max modules")
    parser.add_argument("--workers", type=int, default=3, help="Max workers")
    parser.add_argument("--threshold", type=float, default=70, help="Health threshold")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    healer = ParallelHealer(max_workers=args.workers)

    print(f"Healing up to {args.max} modules...")
    results = asyncio.run(healer.heal_batch(args.max, args.threshold))

    successful = sum(1 for r in results if isinstance(r, HealingResult) and r.status == "success")
    print(f"\nHealed {successful}/{len(results)} modules successfully")


if __name__ == "__main__":
    main()
