"""Module health monitoring."""

import ast
import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ModuleHealth:
    """Health metrics for a module."""

    module_path: str
    health_score: float
    complexity: int
    loc: int
    type_errors: int = 0
    lint_errors: int = 0


class HealthMonitor:
    """Monitor module health."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self._type_error_cache: dict[str, int] | None = None

    def get_healing_candidates(self, threshold: float = 70) -> list[ModuleHealth]:
        """Get modules that need healing."""
        candidates = []

        type_error_map = self._collect_type_errors(refresh=True)

        # Find all Python files
        for py_file in self.project_root.glob("amplifier/**/*.py"):
            # Skip test files and __pycache__
            if "__pycache__" in py_file.parts or "tests" in py_file.parts:
                continue
            if py_file.name.startswith("test_") or py_file.name.endswith("_test.py"):
                continue

            health = self._analyze_module(py_file, type_error_map=type_error_map)
            if health and health.health_score < threshold:
                candidates.append(health)

        # Sort by health score (worst first)
        return sorted(candidates, key=lambda h: h.health_score)

    def _analyze_module(
        self, module_path: Path, *, type_error_map: dict[str, int] | None = None
    ) -> ModuleHealth | None:
        """Analyze a single module."""
        try:
            with open(module_path, encoding="utf-8") as f:
                source = f.read()
                lines = source.splitlines()

            # Count lines
            loc = len([line for line in lines if line.strip() and not line.strip().startswith("#")])

            # Calculate complexity
            complexity = self._calculate_complexity(source)

            # Count type errors
            type_errors = self._count_type_errors(module_path, type_error_map)

            # Calculate health score
            health_score = self._calculate_health(loc, complexity, type_errors)

            return ModuleHealth(
                module_path=str(module_path),
                health_score=health_score,
                complexity=complexity,
                loc=loc,
                type_errors=type_errors,
            )
        except Exception as e:
            logger.warning(f"Failed to analyze {module_path}: {e}")
            return None

    def _calculate_complexity(self, source: str) -> int:
        """Calculate cyclomatic complexity."""
        try:
            tree = ast.parse(source)
            complexity = 0

            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):  # noqa: UP038
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1

            return complexity
        except Exception as e:
            logger.warning(f"Complexity calculation failed: {e}")
            return 0

    def _collect_type_errors(self, refresh: bool = False) -> dict[str, int]:
        """Collect all type errors via a single pyright invocation."""

        if not refresh and self._type_error_cache is not None:
            return self._type_error_cache

        target_path = self.project_root / "amplifier"
        if not target_path.exists():
            target_path = self.project_root

        try:
            result = subprocess.run(
                ["pyright", str(target_path), "--outputjson"],
                capture_output=True,
                text=True,
                timeout=120,
            )
        except FileNotFoundError:
            logger.debug("Pyright not found; skipping type error analysis")
            self._type_error_cache = {}
            return self._type_error_cache
        except Exception as exc:  # pragma: no cover - defensive logging only
            logger.warning(f"Failed to run pyright: {exc}")
            self._type_error_cache = {}
            return self._type_error_cache

        output_text = result.stdout.strip()
        if not output_text:
            self._type_error_cache = {}
            return self._type_error_cache

        try:
            payload = json.loads(output_text)
        except json.JSONDecodeError:
            logger.warning("Unexpected pyright output; could not parse JSON")
            self._type_error_cache = {}
            return self._type_error_cache

        error_counts: dict[str, int] = {}

        for diag in payload.get("generalDiagnostics", []):
            file_path = diag.get("file")
            severity = str(diag.get("severity", "")).lower()
            if not file_path or severity != "error":
                continue
            resolved = str(Path(file_path).resolve())
            error_counts[resolved] = error_counts.get(resolved, 0) + 1

        for group in payload.get("diagnostics", []):
            file_path = group.get("file")
            if not file_path:
                continue
            resolved = str(Path(file_path).resolve())
            diag_entries = group.get("diagnostics", [])
            errors = sum(1 for diag in diag_entries if str(diag.get("severity", "")).lower() == "error")
            if errors:
                error_counts[resolved] = error_counts.get(resolved, 0) + errors

        self._type_error_cache = error_counts
        return self._type_error_cache

    def _count_type_errors(self, module_path: Path, type_error_map: dict[str, int] | None) -> int:
        """Fetch cached type error count for a module."""

        cache = type_error_map if type_error_map is not None else self._collect_type_errors()
        return cache.get(str(module_path.resolve()), 0)

    def _calculate_health(self, loc: int, complexity: int, type_errors: int) -> float:
        """Calculate health score (0-100)."""
        score = 100.0

        # Deduct for high LOC
        if loc > 200:
            score -= min(30, (loc - 200) / 10)
        elif loc > 100:
            score -= min(15, (loc - 100) / 10)

        # Deduct for complexity
        if complexity > 10:
            score -= min(40, complexity - 10)

        # Deduct for type errors
        score -= min(30, type_errors * 5)

        return max(0, score)
