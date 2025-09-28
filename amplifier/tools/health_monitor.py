#!/usr/bin/env python3
"""
Module Health Monitor - Track complexity and test metrics for Aider regeneration.

This provides the telemetry foundation for future self-healing capabilities.
"""

import ast
import json
import logging
import subprocess
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ModuleHealth:
    """Health metrics for a Python module."""

    module_path: str
    complexity: int  # Cyclomatic complexity
    function_count: int
    class_count: int
    loc: int  # Lines of code
    test_coverage: float | None = None
    type_errors: int = 0
    lint_issues: int = 0

    @property
    def health_score(self) -> float:
        """Calculate overall health score (0-100)."""
        score = 100.0

        # Penalize complexity
        if self.complexity > 10:
            score -= min((self.complexity - 10) * 2, 30)

        # Penalize large files
        if self.loc > 200:
            score -= min((self.loc - 200) / 10, 20)

        # Penalize type/lint issues
        score -= min(self.type_errors * 5, 20)
        score -= min(self.lint_issues * 2, 10)

        # Boost for test coverage
        if self.test_coverage:
            score = score * 0.7 + (self.test_coverage * 0.3)

        return max(0, min(100, score))

    @property
    def needs_healing(self) -> bool:
        """Determine if module needs regeneration."""
        return self.health_score < 70


class HealthMonitor:
    """Monitor and track module health metrics."""

    def __init__(self, project_root: Path = Path(".")):
        self.project_root = project_root
        self.metrics_file = project_root / ".data" / "module_health.json"
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

    def analyze_module(self, module_path: Path) -> ModuleHealth:
        """Analyze health metrics for a single module."""
        with open(module_path) as f:
            code = f.read()

        # Parse AST for complexity metrics
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            logger.error(f"Syntax error in {module_path}: {e}")
            return ModuleHealth(
                module_path=str(module_path),
                complexity=999,  # Max complexity for broken code
                function_count=0,
                class_count=0,
                loc=len(code.splitlines()),
            )

        # Calculate metrics
        complexity = self._calculate_complexity(tree)
        functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
        classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
        loc = len(code.splitlines())

        # Get type errors from pyright
        type_errors = self._count_type_errors(module_path)

        # Get lint issues from ruff
        lint_issues = self._count_lint_issues(module_path)

        # Get test coverage if available
        coverage = self._get_test_coverage(module_path)

        return ModuleHealth(
            module_path=str(module_path),
            complexity=complexity,
            function_count=functions,
            class_count=classes,
            loc=loc,
            test_coverage=coverage,
            type_errors=type_errors,
            lint_issues=lint_issues,
        )

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of AST."""
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            # Each decision point adds complexity
            if isinstance(node, ast.If | ast.While | ast.For | ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                # Each 'and'/'or' adds a branch
                complexity += len(node.values) - 1
            elif isinstance(node, ast.comprehension):
                complexity += sum(1 for _ in node.ifs) + 1

        return complexity

    def _count_type_errors(self, module_path: Path) -> int:
        """Count pyright type errors."""
        try:
            result = subprocess.run(
                ["pyright", str(module_path), "--outputjson"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return 0

            output = json.loads(result.stdout)
            errors = output.get("generalDiagnostics", [])
            return len([e for e in errors if e.get("severity") == "error"])
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return 0

    def _count_lint_issues(self, module_path: Path) -> int:
        """Count ruff lint issues."""
        try:
            result = subprocess.run(
                ["ruff", "check", str(module_path), "--output-format=json"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return 0

            issues = json.loads(result.stdout)
            return len(issues)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return 0

    def _get_test_coverage(self, module_path: Path) -> float | None:
        """Get test coverage for module if available."""
        # This would integrate with coverage.py data
        # For now, return None as placeholder
        return None

    def scan_directory(self, directory: Path) -> list[ModuleHealth]:
        """Scan all Python files in directory."""
        modules = []
        for py_file in directory.glob("**/*.py"):
            # Skip test files and __pycache__
            if "test_" in py_file.name or "__pycache__" in str(py_file):
                continue

            health = self.analyze_module(py_file)
            modules.append(health)

            if health.needs_healing:
                logger.warning(
                    f"{py_file.name}: Health score {health.health_score:.1f} "
                    f"(complexity: {health.complexity}, loc: {health.loc})"
                )

        return modules

    def save_metrics(self, modules: list[ModuleHealth]):
        """Save metrics to JSON file."""
        data = {
            "modules": [asdict(m) for m in modules],
            "summary": {
                "total_modules": len(modules),
                "healthy": len([m for m in modules if not m.needs_healing]),
                "needs_healing": len([m for m in modules if m.needs_healing]),
                "average_health": sum(m.health_score for m in modules) / len(modules) if modules else 0,
            },
        }

        with open(self.metrics_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved metrics for {len(modules)} modules to {self.metrics_file}")

    def get_healing_candidates(self, threshold: float = 70) -> list[ModuleHealth]:
        """Get modules that need healing based on health score."""
        if not self.metrics_file.exists():
            return []

        with open(self.metrics_file) as f:
            data = json.load(f)

        candidates = []
        for module_data in data["modules"]:
            health = ModuleHealth(**module_data)
            if health.health_score < threshold:
                candidates.append(health)

        return sorted(candidates, key=lambda m: m.health_score)


def main():
    """CLI entry point for health monitoring."""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor module health")
    parser.add_argument("path", nargs="?", default=".", help="Path to scan")
    parser.add_argument("--heal", action="store_true", help="Show healing candidates")
    parser.add_argument("--threshold", type=float, default=70, help="Health threshold")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(levelname)s: %(message)s")

    monitor = HealthMonitor(Path(args.path))

    if args.heal:
        # Show modules that need healing
        candidates = monitor.get_healing_candidates(args.threshold)
        if candidates:
            print(f"\nModules needing healing (threshold: {args.threshold}):\n")
            for module in candidates:
                print(f"  {module.module_path}")
                print(f"    Health: {module.health_score:.1f}")
                print(f"    Issues: complexity={module.complexity}, loc={module.loc}")
        else:
            print("All modules are healthy!")
    else:
        # Scan and save metrics
        print(f"Scanning {args.path}...")
        modules = monitor.scan_directory(Path(args.path))
        monitor.save_metrics(modules)

        # Print summary
        healthy = [m for m in modules if not m.needs_healing]
        needs_healing = [m for m in modules if m.needs_healing]

        print("\nHealth Summary:")
        print(f"  Total modules: {len(modules)}")
        print(f"  Healthy: {len(healthy)}")
        print(f"  Needs healing: {len(needs_healing)}")

        if needs_healing:
            print("\nTop candidates for healing:")
            for module in needs_healing[:5]:
                print(f"  {Path(module.module_path).name}: {module.health_score:.1f}")


if __name__ == "__main__":
    main()
