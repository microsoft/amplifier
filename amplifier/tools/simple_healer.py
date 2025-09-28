#!/usr/bin/env python3
"""
Simple Healer - Orchestrate Aider regeneration based on health metrics.

A pragmatic implementation that works with current tools.
"""

import json
import logging
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

from amplifier.tools.health_monitor import HealthMonitor
from amplifier.tools.health_monitor import ModuleHealth

load_dotenv()

logger = logging.getLogger(__name__)


class SimpleHealer:
    """Orchestrate healing of unhealthy modules."""

    def __init__(self, project_root: Path = Path("."), dry_run: bool = False):
        self.project_root = project_root
        self.dry_run = dry_run
        self.monitor = HealthMonitor(project_root)
        self.healing_log = project_root / ".data" / "healing_log.json"
        self.healing_log.parent.mkdir(parents=True, exist_ok=True)

    def heal_module(self, module_path: Path, health: ModuleHealth) -> bool:
        """Attempt to heal a single module using Aider."""
        logger.info(f"Healing {module_path} (health: {health.health_score:.1f})")

        if self.dry_run:
            logger.info("[DRY RUN] Would regenerate module")
            return True

        # Build healing prompt based on issues
        prompt = self._build_healing_prompt(health)

        # Check if Aider regenerator exists
        regenerator_script = self.project_root / "amplifier" / "tools" / "aider_regenerator.py"
        if not regenerator_script.exists():
            logger.error("Aider regenerator not found. Run setup-aider.sh first.")
            return False

        # Run Aider regeneration
        cmd = [
            sys.executable,
            str(regenerator_script),
            str(module_path),
            "--philosophy",
            "zen",  # Use zen philosophy for simplicity
            "--verbose",
        ]

        logger.info(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                logger.info("Healing successful")
                self._log_healing(module_path, health, "success", prompt)
                return True
            logger.error(f"Healing failed: {result.stderr}")
            self._log_healing(module_path, health, "failed", prompt)
            return False

        except subprocess.TimeoutExpired:
            logger.error("Healing timed out")
            self._log_healing(module_path, health, "timeout", prompt)
            return False
        except Exception as e:
            logger.error(f"Healing error: {e}")
            self._log_healing(module_path, health, "error", prompt)
            return False

    def _build_healing_prompt(self, health: ModuleHealth) -> str:
        """Build a specific healing prompt based on issues."""
        issues = []

        if health.complexity > 15:
            issues.append(f"Reduce complexity from {health.complexity} to under 10")

        if health.loc > 200:
            issues.append(f"Split large file ({health.loc} lines) into smaller modules")

        if health.type_errors > 0:
            issues.append(f"Fix {health.type_errors} type errors")

        if health.lint_issues > 0:
            issues.append(f"Fix {health.lint_issues} lint issues")

        prompt = "Simplify this module following zen philosophy:\n"
        for issue in issues:
            prompt += f"- {issue}\n"

        return prompt

    def _log_healing(self, module_path: Path, health: ModuleHealth, status: str, prompt: str):
        """Log healing attempt for analysis."""
        log_entry = {
            "module": str(module_path),
            "health_before": health.health_score,
            "status": status,
            "prompt": prompt,
            "timestamp": subprocess.check_output(["date", "-Iseconds"]).decode().strip(),
        }

        # Append to log file
        logs = []
        if self.healing_log.exists():
            with open(self.healing_log) as f:
                logs = json.load(f)

        logs.append(log_entry)

        with open(self.healing_log, "w") as f:
            json.dump(logs, f, indent=2)

    def validate_healing(self, module_path: Path) -> bool:
        """Validate a healed module passes basic checks."""
        logger.info(f"Validating {module_path}")

        # Run make check
        result = subprocess.run(["make", "check"], capture_output=True, cwd=self.project_root)

        if result.returncode != 0:
            logger.error("Validation failed: make check failed")
            return False

        # Check if health improved
        new_health = self.monitor.analyze_module(module_path)
        logger.info(f"New health score: {new_health.health_score:.1f}")

        return new_health.health_score > 70

    def heal_batch(self, max_modules: int = 3, threshold: float = 70) -> dict:
        """Heal a batch of unhealthy modules."""
        # Get candidates
        candidates = self.monitor.get_healing_candidates(threshold)

        if not candidates:
            logger.info("No modules need healing")
            return {"healed": 0, "failed": 0}

        # Limit batch size
        batch = candidates[:max_modules]

        results = {"healed": 0, "failed": 0}

        for health in batch:
            module_path = Path(health.module_path)

            if self.heal_module(module_path, health):
                if self.validate_healing(module_path):
                    results["healed"] += 1
                    logger.info(f"✅ Successfully healed {module_path.name}")
                else:
                    results["failed"] += 1
                    logger.warning(f"⚠️ Healing validation failed for {module_path.name}")
            else:
                results["failed"] += 1
                logger.error(f"❌ Failed to heal {module_path.name}")

        return results


def main():
    """CLI entry point for simple healing."""
    import argparse

    parser = argparse.ArgumentParser(description="Heal unhealthy modules")
    parser.add_argument("--scan", action="store_true", help="Scan for unhealthy modules")
    parser.add_argument("--heal", action="store_true", help="Heal unhealthy modules")
    parser.add_argument("--max", type=int, default=3, help="Max modules to heal")
    parser.add_argument("--threshold", type=float, default=70, help="Health threshold")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    healer = SimpleHealer(dry_run=args.dry_run)

    if args.scan:
        # Just scan and report
        monitor = HealthMonitor()
        modules = monitor.scan_directory(Path("."))
        monitor.save_metrics(modules)

        unhealthy = [m for m in modules if m.needs_healing]
        if unhealthy:
            print(f"\nFound {len(unhealthy)} modules needing healing:")
            for m in unhealthy[:10]:
                print(f"  {Path(m.module_path).name}: {m.health_score:.1f}")
        else:
            print("All modules are healthy!")

    elif args.heal:
        # Heal modules
        print(f"Healing up to {args.max} modules (threshold: {args.threshold})")
        if args.dry_run:
            print("[DRY RUN MODE]")

        results = healer.heal_batch(args.max, args.threshold)

        print("\nHealing Results:")
        print(f"  ✅ Healed: {results['healed']}")
        print(f"  ❌ Failed: {results['failed']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
