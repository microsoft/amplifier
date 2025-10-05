#!/usr/bin/env python3
"""
Amplifier Multi-Module Development Installer

A self-contained module for installing all Amplifier modules in the correct dependency order.
Auto-discovers amplifier-* directories and resolves dependencies automatically.

Contract:
    Purpose: Install all Amplifier modules in dependency order
    Input: Command-line flags for installation options
    Output: Installed modules with progress reporting
    Side Effects: Runs uv install commands for each module
"""

import argparse
import json
import os
import subprocess
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class AmplifierInstaller:
    """Orchestrates the installation of all Amplifier modules."""

    # Core modules that must be installed first (in order)
    REQUIRED_MODULES = ["amplifier-core", "amplifier"]

    def __init__(
        self,
        base_dir: Path,
        no_editable: bool = False,
        parallel: bool = False,
        verbose: bool = False,
        check_only: bool = False
    ):
        """Initialize the installer with configuration options.

        Args:
            base_dir: Base directory containing amplifier-* modules
            no_editable: If True, install without -e flag
            parallel: If True, install independent modules in parallel
            verbose: If True, show detailed output
            check_only: If True, only show what would be installed
        """
        self.base_dir = base_dir
        self.no_editable = no_editable
        self.parallel = parallel
        self.verbose = verbose
        self.check_only = check_only
        self.modules: Dict[str, Path] = {}
        self.dependencies: Dict[str, Set[str]] = {}

    def discover_modules(self) -> Dict[str, Path]:
        """Auto-discover all amplifier-* directories with pyproject.toml.

        Returns:
            Dictionary mapping module names to their paths
        """
        modules = {}

        # First, add required modules if they exist
        for module_name in self.REQUIRED_MODULES:
            module_path = self.base_dir / module_name
            if module_path.exists() and (module_path / "pyproject.toml").exists():
                modules[module_name] = module_path
                if self.verbose:
                    print(f"Found required module: {module_name}")
            else:
                print(f"Warning: Required module {module_name} not found at {module_path}")

        # Then discover all amplifier-* directories
        for path in self.base_dir.glob("amplifier-*"):
            if path.is_dir() and (path / "pyproject.toml").exists():
                module_name = path.name
                if module_name not in modules:  # Don't duplicate required modules
                    modules[module_name] = path
                    if self.verbose:
                        print(f"Discovered module: {module_name}")

        self.modules = modules
        return modules

    def parse_dependencies(self, module_path: Path) -> Set[str]:
        """Parse dependencies from a module's pyproject.toml.

        Args:
            module_path: Path to the module directory

        Returns:
            Set of amplifier-* dependencies
        """
        pyproject_path = module_path / "pyproject.toml"
        dependencies = set()

        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)

            # Check project.dependencies
            if "project" in data and "dependencies" in data["project"]:
                for dep in data["project"]["dependencies"]:
                    # Extract package name from dependency spec
                    dep_name = dep.split("[")[0].split(">=")[0].split("==")[0].split("<")[0].strip()
                    # Only track amplifier-* dependencies
                    if dep_name.startswith("amplifier"):
                        # Normalize amplifier to amplifier (core package)
                        if dep_name == "amplifier":
                            dependencies.add("amplifier")
                        else:
                            dependencies.add(dep_name)

            # Check tool.uv.sources for local dependencies
            if "tool" in data and "uv" in data["tool"] and "sources" in data["tool"]["uv"]:
                for dep_name, source in data["tool"]["uv"]["sources"].items():
                    if isinstance(source, dict) and "path" in source:
                        # This is a local dependency
                        if dep_name.startswith("amplifier"):
                            dependencies.add(dep_name)

        except Exception as e:
            print(f"Warning: Failed to parse dependencies for {module_path}: {e}")

        return dependencies

    def build_dependency_graph(self) -> Dict[str, Set[str]]:
        """Build a dependency graph for all modules.

        Returns:
            Dictionary mapping each module to its dependencies
        """
        graph = {}

        for module_name, module_path in self.modules.items():
            deps = self.parse_dependencies(module_path)
            # Only include dependencies that are in our module set
            graph[module_name] = deps & set(self.modules.keys())

            if self.verbose and graph[module_name]:
                print(f"{module_name} depends on: {', '.join(graph[module_name])}")

        self.dependencies = graph
        return graph

    def topological_sort(self) -> List[str]:
        """Perform topological sort on the dependency graph.

        Returns:
            List of module names in installation order
        """
        # Create a copy of the graph
        graph = {k: v.copy() for k, v in self.dependencies.items()}

        # Start with required modules in order
        result = []
        for module in self.REQUIRED_MODULES:
            if module in self.modules:
                result.append(module)
                # Remove this module from all dependency lists
                for deps in graph.values():
                    deps.discard(module)

        # Continue with standard topological sort for remaining modules
        while graph:
            # Find modules with no dependencies
            ready = [m for m, deps in graph.items() if not deps and m not in result]

            if not ready:
                # Cycle detected - install remaining modules in alphabetical order
                print("Warning: Dependency cycle detected. Installing remaining modules alphabetically.")
                remaining = [m for m in graph.keys() if m not in result]
                result.extend(sorted(remaining))
                break

            # Add ready modules to result
            for module in sorted(ready):  # Sort for deterministic order
                result.append(module)
                del graph[module]
                # Remove this module from all dependency lists
                for deps in graph.values():
                    deps.discard(module)

        return result

    def install_module(self, module_name: str) -> bool:
        """Install a single module using uv.

        Args:
            module_name: Name of the module to install

        Returns:
            True if installation succeeded, False otherwise
        """
        module_path = self.modules[module_name]

        if self.check_only:
            print(f"Would install: {module_name} from {module_path}")
            return True

        # Build the uv command
        cmd = ["uv", "pip", "install"]
        if not self.no_editable:
            cmd.append("-e")
        cmd.append(str(module_path))

        print(f"Installing {module_name}...")

        try:
            result = subprocess.run(
                cmd,
                capture_output=not self.verbose,
                text=True,
                check=True
            )

            if self.verbose and not self.verbose:
                print(result.stdout)

            print(f"✓ Successfully installed {module_name}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {module_name}: {e}")
            if not self.verbose and e.stderr:
                print(f"  Error: {e.stderr}")
            return False

    def install_parallel(self, modules: List[str]) -> Dict[str, bool]:
        """Install modules in parallel.

        Args:
            modules: List of module names to install

        Returns:
            Dictionary mapping module names to success status
        """
        results = {}

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_module = {
                executor.submit(self.install_module, module): module
                for module in modules
            }

            for future in as_completed(future_to_module):
                module = future_to_module[future]
                try:
                    results[module] = future.result()
                except Exception as e:
                    print(f"✗ Unexpected error installing {module}: {e}")
                    results[module] = False

        return results

    def run(self) -> int:
        """Run the complete installation process.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print("Amplifier Multi-Module Installer")
        print("=" * 40)

        # Step 1: Discover modules
        print("\n1. Discovering modules...")
        modules = self.discover_modules()
        if not modules:
            print("No modules found!")
            return 1
        print(f"Found {len(modules)} modules")

        # Step 2: Build dependency graph
        print("\n2. Analyzing dependencies...")
        self.build_dependency_graph()

        # Step 3: Determine installation order
        print("\n3. Computing installation order...")
        install_order = self.topological_sort()

        print("\nInstallation order:")
        for i, module in enumerate(install_order, 1):
            deps = self.dependencies.get(module, set())
            if deps:
                print(f"  {i}. {module} (depends on: {', '.join(deps)})")
            else:
                print(f"  {i}. {module}")

        if self.check_only:
            print("\n(Check-only mode - no actual installation performed)")
            return 0

        # Step 4: Install modules
        print(f"\n4. Installing {len(install_order)} modules...")

        failed = []

        if self.parallel:
            # Group modules by dependency level for parallel installation
            levels = []
            installed = set()
            remaining = install_order.copy()

            while remaining:
                # Find modules whose dependencies are all installed
                level = []
                for module in remaining:
                    deps = self.dependencies.get(module, set())
                    if deps.issubset(installed):
                        level.append(module)

                if not level:
                    # This shouldn't happen after topological sort
                    print("Error: Unable to determine next installation level")
                    return 1

                levels.append(level)
                installed.update(level)
                remaining = [m for m in remaining if m not in installed]

            # Install each level in parallel
            for level_num, level_modules in enumerate(levels, 1):
                if len(level_modules) > 1:
                    print(f"\nInstalling level {level_num} in parallel: {', '.join(level_modules)}")
                    results = self.install_parallel(level_modules)
                    failed.extend([m for m, success in results.items() if not success])
                else:
                    # Single module, install normally
                    module = level_modules[0]
                    if not self.install_module(module):
                        failed.append(module)
        else:
            # Sequential installation
            for module in install_order:
                if not self.install_module(module):
                    failed.append(module)
                    # For required modules, fail immediately
                    if module in self.REQUIRED_MODULES:
                        print(f"\nError: Required module {module} failed to install")
                        return 1

        # Summary
        print("\n" + "=" * 40)
        print("Installation Summary:")
        print(f"  Total modules: {len(install_order)}")
        print(f"  Successful: {len(install_order) - len(failed)}")
        print(f"  Failed: {len(failed)}")

        if failed:
            print(f"\nFailed modules: {', '.join(failed)}")
            return 1
        else:
            print("\n✓ All modules installed successfully!")
            return 0


def check_and_create_virtual_environment():
    """Check virtual environment, create if needed, provide activation help."""

    # Check if in venv
    in_venv = (sys.real_prefix if hasattr(sys, 'real_prefix') else
               sys.base_prefix != sys.prefix or
               os.environ.get('VIRTUAL_ENV'))

    if in_venv:
        return  # All good, continue

    # Not in venv - check if .venv exists
    venv_path = Path.cwd() / ".venv"

    if not venv_path.exists():
        print("No virtual environment found. Creating one now...")
        try:
            subprocess.run(["uv", "venv", ".venv"], check=True)
            print("Virtual environment created successfully!")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Failed to create venv. Please ensure 'uv' is installed:")
            print("   pip install uv")
            sys.exit(1)

    # Show activation instructions based on OS
    print("\nNext step: Activate the virtual environment")
    print("-" * 40)

    if sys.platform == "win32":
        print("Run this command:")
        print("  .venv\\Scripts\\activate")
    else:
        print("Run this command:")
        print("  source .venv/bin/activate")

    print("\nThen run the installer again:")
    print("  python install_all.py")

    sys.exit(0)  # Clean exit


def check_conflicting_installations():
    """Check for conflicting amplifier installations that might cause issues."""
    # Check if amplifier is installed in user's .local/bin
    home = Path.home()
    local_bin = home / ".local" / "bin" / "amplifier"

    if local_bin.exists():
        print("⚠️  WARNING: Found existing amplifier installation in ~/.local/bin")
        print(f"  Path: {local_bin}")
        print("\nThis may conflict with the development installation.")
        print("You can check which amplifier will be used with: which amplifier")
        print("To remove the old installation: pip uninstall amplifier")
        print()

    # Check if amplifier is already in PATH (but not from current venv)
    try:
        result = subprocess.run(
            ["which", "amplifier"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            amplifier_path = result.stdout.strip()
            venv_path = os.environ.get('VIRTUAL_ENV')
            if venv_path and not amplifier_path.startswith(venv_path):
                print(f"⚠️  WARNING: amplifier found in PATH at: {amplifier_path}")
                print("This installation will take precedence over the development version.")
                print("Consider removing it with: pip uninstall amplifier")
                print()
    except (subprocess.CalledProcessError, FileNotFoundError):
        # 'which' command not available or amplifier not found
        pass


def main():
    """Main entry point for the installer."""
    parser = argparse.ArgumentParser(
        description="Install all Amplifier modules in dependency order"
    )
    parser.add_argument(
        "--no-editable",
        action="store_true",
        help="Install without -e flag (non-editable)"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Install independent modules in parallel"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only show what would be installed without actually installing"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path(__file__).parent,
        help="Base directory containing amplifier modules (default: script directory)"
    )
    parser.add_argument(
        "--skip-venv-check",
        action="store_true",
        help="Skip virtual environment check (not recommended)"
    )

    args = parser.parse_args()

    # Check virtual environment unless explicitly skipped
    if not args.skip_venv_check:
        check_and_create_virtual_environment()

    # Check for conflicting installations
    check_conflicting_installations()

    installer = AmplifierInstaller(
        base_dir=args.base_dir,
        no_editable=args.no_editable,
        parallel=args.parallel,
        verbose=args.verbose,
        check_only=args.check_only
    )

    return installer.run()


if __name__ == "__main__":
    sys.exit(main())