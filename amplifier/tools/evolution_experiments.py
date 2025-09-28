#!/usr/bin/env python3
"""
Evolution Experiments - Phase 3: Generate multiple variants and let them compete.

Creates parallel implementations using different philosophies and selects the best.
"""

import json
import logging
import shutil
import subprocess
import time
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from amplifier.tools.health_monitor import HealthMonitor

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class Variant:
    """A code variant with its performance metrics."""

    variant_id: str
    philosophy: str
    module_path: str
    health_score: float
    complexity: int
    loc: int
    benchmark_time: float | None = None
    test_passed: bool = False
    fitness_score: float = 0.0


class EvolutionExperiments:
    """Generate and test multiple code variants to find the best implementation."""

    PHILOSOPHIES = {
        "zen": {
            "prompt": "Rewrite with ruthless simplicity - remove all unnecessary complexity",
            "weight": {"simplicity": 0.5, "performance": 0.2, "readability": 0.3},
        },
        "functional": {
            "prompt": "Rewrite in functional style - pure functions, immutability, no side effects",
            "weight": {"simplicity": 0.3, "performance": 0.3, "readability": 0.4},
        },
        "modular": {
            "prompt": "Rewrite with modular design - clear interfaces, single responsibility",
            "weight": {"simplicity": 0.3, "performance": 0.2, "readability": 0.5},
        },
        "performance": {
            "prompt": "Optimize for performance - faster algorithms, caching, minimal overhead",
            "weight": {"simplicity": 0.2, "performance": 0.6, "readability": 0.2},
        },
    }

    def __init__(self, project_root: Path = Path("."), dry_run: bool = False):
        self.project_root = project_root
        self.dry_run = dry_run
        self.monitor = HealthMonitor(project_root)
        self.experiments_dir = project_root / ".data" / "evolution_experiments"
        self.experiments_dir.mkdir(parents=True, exist_ok=True)

    def generate_variant(self, module_path: Path, philosophy: str) -> Variant | None:
        """Generate a variant using a specific philosophy."""
        variant_id = f"{module_path.stem}_{philosophy}_{int(time.time())}"
        variant_dir = self.experiments_dir / variant_id
        variant_dir.mkdir(exist_ok=True)

        variant_path = variant_dir / module_path.name

        if self.dry_run:
            # In dry-run, create a mock variant
            logger.info(f"[DRY RUN] Would generate {philosophy} variant for {module_path.name}")

            # Copy original for simulation
            shutil.copy(module_path, variant_path)

            # Simulate improvements based on philosophy
            health = self.monitor.analyze_module(variant_path)

            # Mock improvements - calculate what the new metrics would be
            if philosophy == "zen":
                mock_complexity = max(5, health.complexity - 20)
                mock_loc = int(health.loc * 0.6)
                mock_health = min(100, 100 - (mock_complexity / 2) - (mock_loc / 10))
            elif philosophy == "functional":
                mock_complexity = max(8, health.complexity - 15)
                mock_loc = int(health.loc * 0.8)
                mock_health = min(100, 100 - (mock_complexity / 2) - (mock_loc / 10))
            elif philosophy == "modular":
                mock_complexity = max(10, health.complexity - 10)
                mock_loc = int(health.loc * 0.9)
                mock_health = min(100, 100 - (mock_complexity / 2) - (mock_loc / 10))
            elif philosophy == "performance":
                # Performance optimizations might increase complexity
                mock_complexity = health.complexity + 5
                mock_loc = health.loc
                mock_health = min(100, 100 - (mock_complexity / 2) - (mock_loc / 10))

            return Variant(
                variant_id=variant_id,
                philosophy=philosophy,
                module_path=str(variant_path),
                health_score=mock_health,
                complexity=mock_complexity,
                loc=mock_loc,
                test_passed=True,
            )

        # Real generation would use Aider here
        logger.info(f"Generating {philosophy} variant for {module_path.name}")

        # Copy original as starting point
        shutil.copy(module_path, variant_path)

        # Generate with Aider (requires API key)
        prompt = self.PHILOSOPHIES[philosophy]["prompt"]
        prompt += f"\n\nRewrite the module at {variant_path} following this philosophy."

        # This would call Aider in production
        # For now, just analyze the original
        health = self.monitor.analyze_module(variant_path)

        return Variant(
            variant_id=variant_id,
            philosophy=philosophy,
            module_path=str(variant_path),
            health_score=health.health_score,
            complexity=health.complexity,
            loc=health.loc,
        )

    def benchmark_variant(self, variant: Variant) -> float:
        """Benchmark a variant's performance."""
        if self.dry_run:
            # Simulate benchmark times based on philosophy
            base_time = 1.0
            if variant.philosophy == "performance":
                variant.benchmark_time = base_time * 0.5  # 50% faster
            elif variant.philosophy == "zen":
                variant.benchmark_time = base_time * 0.7  # 30% faster
            elif variant.philosophy == "functional":
                variant.benchmark_time = base_time * 0.8  # 20% faster
            else:
                variant.benchmark_time = base_time * 0.9  # 10% faster

            return variant.benchmark_time

        # Real benchmarking would run performance tests
        logger.info(f"Benchmarking {variant.variant_id}")

        # Simple timing test
        start = time.time()
        try:
            # Import and run the module
            result = subprocess.run(
                ["python", "-c", f"import {Path(variant.module_path).stem}"],
                capture_output=True,
                timeout=5,
                cwd=Path(variant.module_path).parent,
            )
            variant.test_passed = result.returncode == 0
        except subprocess.TimeoutExpired:
            variant.test_passed = False

        variant.benchmark_time = time.time() - start
        return variant.benchmark_time

    def calculate_fitness(self, variant: Variant) -> float:
        """Calculate overall fitness score for a variant."""
        weights = self.PHILOSOPHIES[variant.philosophy]["weight"]

        # Normalize scores to 0-1 range
        health_normalized = variant.health_score / 100
        complexity_normalized = 1 - min(variant.complexity / 50, 1)  # Lower is better
        performance_normalized = 1 / (variant.benchmark_time + 0.01) if variant.benchmark_time else 0.5

        # Weighted fitness
        fitness = (
            weights["simplicity"] * complexity_normalized
            + weights["performance"] * performance_normalized
            + weights["readability"] * health_normalized
        )

        # Bonus for passing tests
        if variant.test_passed:
            fitness *= 1.2

        variant.fitness_score = fitness
        return fitness

    def tournament_selection(self, variants: list[Variant]) -> Variant:
        """Select the best variant through tournament selection."""
        # Calculate fitness for all variants
        for variant in variants:
            self.calculate_fitness(variant)

        # Sort by fitness
        sorted_variants = sorted(variants, key=lambda v: v.fitness_score, reverse=True)

        logger.info("\n=== Tournament Results ===")
        for i, v in enumerate(sorted_variants, 1):
            logger.info(
                f"{i}. {v.philosophy}: Fitness={v.fitness_score:.3f}, "
                f"Health={v.health_score:.1f}, Complexity={v.complexity}"
            )

        winner = sorted_variants[0]
        logger.info(f"\n🏆 Winner: {winner.philosophy} variant with fitness {winner.fitness_score:.3f}")

        return winner

    def evolve_module(self, module_path: Path, philosophies: list[str] | None = None) -> dict:
        """Evolve a module by generating and testing multiple variants."""
        if philosophies is None:
            philosophies = list(self.PHILOSOPHIES.keys())

        logger.info(f"Evolving {module_path.name} with {len(philosophies)} philosophies")

        # Generate variants
        variants = []
        for philosophy in philosophies:
            variant = self.generate_variant(module_path, philosophy)
            if variant:
                # Benchmark each variant
                self.benchmark_variant(variant)
                variants.append(variant)

        if not variants:
            logger.error("No variants generated")
            return {"winner": None, "variants": []}

        # Tournament selection
        winner = self.tournament_selection(variants)

        # Save results
        results = {
            "module": str(module_path),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "winner": asdict(winner),
            "variants": [asdict(v) for v in variants],
        }

        results_file = self.experiments_dir / f"evolution_{module_path.stem}.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to {results_file}")

        # Apply winner if not dry-run
        if not self.dry_run and winner.test_passed:
            self.apply_winner(module_path, winner)

        return results

    def apply_winner(self, original_path: Path, winner: Variant):
        """Apply the winning variant to the original module."""
        logger.info(f"Applying {winner.philosophy} variant to {original_path.name}")

        # Backup original
        backup_path = original_path.with_suffix(".backup")
        shutil.copy(original_path, backup_path)

        # Apply winner
        shutil.copy(winner.module_path, original_path)

        logger.info(f"✅ Applied winning variant (backup at {backup_path})")


def main():
    """CLI for evolution experiments."""
    import argparse

    parser = argparse.ArgumentParser(description="Evolve modules through competition")
    parser.add_argument("module", help="Module to evolve")
    parser.add_argument("--philosophies", nargs="+", help="Philosophies to test")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    evolver = EvolutionExperiments(dry_run=args.dry_run)

    module_path = Path(args.module)
    if not module_path.exists():
        logger.error(f"Module not found: {module_path}")
        return

    philosophies = args.philosophies or ["zen", "functional", "modular", "performance"]

    print(f"🧬 Evolving {module_path.name} with {len(philosophies)} philosophies...")
    if args.dry_run:
        print("[DRY RUN MODE]")

    results = evolver.evolve_module(module_path, philosophies)

    if results.get("winner"):
        winner = results["winner"]
        print(f"\n🏆 Winner: {winner['philosophy']}")
        print(f"   Fitness: {winner['fitness_score']:.3f}")
        print(f"   Health: {winner['health_score']:.1f}")
        print(f"   Complexity: {winner['complexity']}")
        print(f"   LOC: {winner['loc']}")

    print("\n✨ Evolution complete!")


if __name__ == "__main__":
    main()
