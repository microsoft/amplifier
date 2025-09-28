"""Analyze and suggest strategies for decoupling tightly connected modules."""

import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CouplingMetrics:
    """Metrics for module coupling."""

    module_path: str
    imports: set[str]
    imported_by: set[str]
    coupling_score: float
    circular_dependencies: list[str]
    interface_suggestions: list[str]


class CouplingAnalyzer:
    """Analyze coupling between modules and suggest decoupling strategies."""

    def __init__(self, project_root: Path = Path(".")):
        self.project_root = project_root
        self.import_graph = defaultdict(set)
        self.reverse_graph = defaultdict(set)

    def analyze_coupling(self, module_path: Path) -> CouplingMetrics:
        """Analyze coupling for a specific module."""

        # Build import graph if not already done
        if not self.import_graph:
            self._build_import_graph()

        module_name = self._path_to_module_name(module_path)
        imports = self.import_graph.get(module_name, set())
        imported_by = self.reverse_graph.get(module_name, set())

        # Calculate coupling score (0-100, higher = more coupled)
        total_connections = len(imports) + len(imported_by)
        coupling_score = min(100, total_connections * 5)  # 20+ connections = 100

        # Detect circular dependencies
        circular_deps = self._find_circular_dependencies(module_name)

        # Generate decoupling suggestions
        suggestions = self._generate_suggestions(module_name, imports, imported_by, circular_deps)

        return CouplingMetrics(
            module_path=str(module_path),
            imports=imports,
            imported_by=imported_by,
            coupling_score=coupling_score,
            circular_dependencies=circular_deps,
            interface_suggestions=suggestions,
        )

    def _build_import_graph(self):
        """Build a graph of module dependencies."""

        for py_file in self.project_root.rglob("*.py"):
            if "test" in str(py_file) or "__pycache__" in str(py_file):
                continue

            module_name = self._path_to_module_name(py_file)

            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imported = alias.name
                            if imported.startswith("amplifier"):
                                self.import_graph[module_name].add(imported)
                                self.reverse_graph[imported].add(module_name)

                    elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("amplifier"):
                        self.import_graph[module_name].add(node.module)
                        self.reverse_graph[node.module].add(module_name)

            except Exception:
                continue

    def _path_to_module_name(self, path: Path) -> str:
        """Convert file path to module name."""
        relative = path.relative_to(self.project_root)
        return str(relative.with_suffix("")).replace("/", ".")

    def _find_circular_dependencies(self, module: str, visited: set = None, path: list = None) -> list[str]:
        """Find circular dependencies starting from module."""
        if visited is None:
            visited = set()
        if path is None:
            path = []

        if module in visited:
            if module in path:
                # Found a cycle
                cycle_start = path.index(module)
                return [" -> ".join(path[cycle_start:] + [module])]
            return []

        visited.add(module)
        path.append(module)

        circular = []
        for imported in self.import_graph.get(module, []):
            result = self._find_circular_dependencies(imported, visited.copy(), path.copy())
            circular.extend(result)

        return circular

    def _generate_suggestions(
        self, module: str, imports: set[str], imported_by: set[str], circular_deps: list[str]
    ) -> list[str]:
        """Generate decoupling suggestions based on analysis."""

        suggestions = []

        # High coupling score suggestions
        if len(imports) > 10:
            suggestions.append(f"Extract interfaces: Module imports {len(imports)} other modules")
            suggestions.append("Consider dependency injection to reduce direct imports")

        if len(imported_by) > 10:
            suggestions.append(f"Split responsibilities: Module is imported by {len(imported_by)} others")
            suggestions.append("Extract commonly used functionality to utility modules")

        # Circular dependency suggestions
        if circular_deps:
            suggestions.append(f"Break circular dependencies: {circular_deps[0]}")
            suggestions.append("Use event-based communication or interfaces")

        # Pattern-based suggestions
        if any("database" in imp or "model" in imp for imp in imports):
            suggestions.append("Separate data access from business logic")

        if any("api" in imp or "client" in imp for imp in imports):
            suggestions.append("Abstract external service calls behind interfaces")

        if len(imports) > 5 and len(imported_by) > 5:
            suggestions.append("This is a 'god module' - break into smaller, focused modules")

        return suggestions


def generate_decoupling_strategy(module_path: Path) -> str:
    """Generate a comprehensive decoupling strategy for a module."""

    analyzer = CouplingAnalyzer(module_path.parent.parent)
    metrics = analyzer.analyze_coupling(module_path)

    strategy = f"""
DECOUPLING STRATEGY for {module_path.name}

COUPLING ANALYSIS:
- Coupling Score: {metrics.coupling_score:.1f}/100
- Direct Dependencies: {len(metrics.imports)}
- Reverse Dependencies: {len(metrics.imported_by)}
- Circular Dependencies: {len(metrics.circular_dependencies)}

STEP-BY-STEP DECOUPLING:

1. IDENTIFY CORE RESPONSIBILITY
   - What is the ONE thing this module should do?
   - Everything else should be extracted

2. BREAK CIRCULAR DEPENDENCIES
"""

    if metrics.circular_dependencies:
        for cycle in metrics.circular_dependencies:
            strategy += f"   - Break cycle: {cycle}\n"
            strategy += "   - Solution: Extract shared interface or use events\n"

    strategy += """
3. REDUCE IMPORT COUNT
   - Current imports: """ + ", ".join(list(metrics.imports)[:5])

    strategy += """
   - Replace with:
     * Dependency injection for services
     * Interfaces for external systems
     * Events for loose coupling

4. REDUCE REVERSE DEPENDENCIES
   - Extract commonly used code to utilities
   - Create clean APIs with minimal surface area
   - Use the Facade pattern to simplify complex interfaces

5. APPLY PATTERNS:
"""

    for suggestion in metrics.interface_suggestions:
        strategy += f"   - {suggestion}\n"

    strategy += """
6. FINAL STRUCTURE:
   - Input: Clean data structures or interfaces
   - Processing: Pure functions with no side effects
   - Output: Simple return values or events
   - Dependencies: Injected, not imported

RESULT: A module that can be tested in complete isolation.
"""

    return strategy
