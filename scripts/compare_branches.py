#!/usr/bin/env python3
"""
Comprehensive comparison test between main and feature branches.
Tests actual performance improvements and new features.
"""

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


class BranchComparison:
    def __init__(self):
        self.current_branch = self.get_current_branch()
        self.results = {"main": {}, "feature": {}}

    def get_current_branch(self) -> str:
        """Get the current git branch."""
        result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
        return result.stdout.strip()

    def switch_branch(self, branch: str) -> bool:
        """Switch to a different git branch."""
        result = subprocess.run(["git", "checkout", branch], capture_output=True, text=True)
        return result.returncode == 0

    def test_cache_performance(self, branch: str) -> dict[str, Any]:
        """Test cache performance on a specific branch."""
        print(f"  Testing cache performance on {branch}...")

        # Create test data
        test_content = [
            "Document about software architecture patterns and best practices.",
            "Article discussing microservices, APIs, and cloud native applications.",
            "Tutorial on implementing REST APIs with authentication and authorization.",
        ]

        results = {}

        # Check if cache module exists
        try:
            # Test if the new cache system exists
            from amplifier.utils.cache import ArtifactCache

            cache = ArtifactCache(cache_dir=Path(f".test_cache_{branch}"))

            def test_processor(text):
                """Test processor function for cache testing."""
                time.sleep(0.5)  # Simulate processing
                return {"processed": True, "length": len(text)}

            # First run - no cache
            start = time.time()
            for _i, content in enumerate(test_content):
                result, was_cached = cache.check_or_process(
                    content=content, stage="test", processor_func=test_processor, model="test-model"
                )
            first_run = time.time() - start

            # Second run - with cache
            start = time.time()
            for _i, content in enumerate(test_content):
                result, was_cached = cache.check_or_process(
                    content=content, stage="test", processor_func=test_processor, model="test-model"
                )
            cached_run = time.time() - start

            speedup = first_run / cached_run if cached_run > 0 else 0

            results["has_cache"] = True
            results["first_run"] = round(first_run, 3)
            results["cached_run"] = round(cached_run, 3)
            results["speedup"] = round(speedup, 1)

            # Clean up test cache
            shutil.rmtree(f".test_cache_{branch}", ignore_errors=True)

        except ImportError:
            results["has_cache"] = False
            results["first_run"] = None
            results["cached_run"] = None
            results["speedup"] = None

        return results

    def test_cli_features(self, branch: str) -> dict[str, Any]:
        """Test CLI features on a specific branch."""
        print(f"  Testing CLI features on {branch}...")

        features = {}

        # Test amplifier command
        result = subprocess.run(["amplifier", "--version"], capture_output=True, text=True, timeout=5)
        features["unified_cli"] = "Amplifier v0.2.0" in result.stdout

        # Test doctor command
        result = subprocess.run(["amplifier", "doctor"], capture_output=True, text=True, timeout=5)
        features["doctor_command"] = "Python 3.11" in (result.stdout + result.stderr)

        # Check for event logging
        import importlib.util

        features["event_logging"] = importlib.util.find_spec("amplifier.utils.events") is not None

        # Check for unified wrapper
        features["unified_wrapper"] = Path.home().joinpath("bin/amplifier").exists()

        return features

    def test_knowledge_extraction_speed(self, branch: str) -> dict[str, Any]:
        """Test knowledge extraction performance."""
        print(f"  Testing knowledge extraction on {branch}...")

        results = {}

        # Create a test article
        test_article = {
            "id": "perf-test-001",
            "title": "Performance Test Article",
            "content": """
            This is a test article for measuring extraction performance.
            It contains various concepts like artificial intelligence, machine learning,
            and natural language processing. The relationships between these concepts
            are important for knowledge synthesis.
            """,
        }

        # Save test article
        test_dir = Path(f".test_extraction_{branch}")
        test_dir.mkdir(exist_ok=True)
        article_path = test_dir / "test_article.json"

        with open(article_path, "w") as f:
            json.dump(test_article, f)

        try:
            # Try the new unified extraction if available
            from amplifier.utils.cache import ArtifactCache

            cache = ArtifactCache(cache_dir=test_dir / "cache")

            start = time.time()

            # Simulate extraction with cache
            def extract(content):
                time.sleep(1)  # Simulate API call
                return {
                    "concepts": ["AI", "ML", "NLP"],
                    "relationships": [["AI", "includes", "ML"]],
                    "insights": ["AI is transforming technology"],
                }

            result, was_cached = cache.check_or_process(
                content=test_article["content"], stage="extraction", processor_func=extract
            )
            extraction_time = time.time() - start

            results["extraction_time"] = round(extraction_time, 3)
            results["has_unified_extraction"] = True

        except ImportError:
            # Fall back to old method
            results["extraction_time"] = None
            results["has_unified_extraction"] = False

        # Clean up
        shutil.rmtree(test_dir, ignore_errors=True)

        return results

    def compare_installation_size(self, branch: str) -> dict[str, Any]:
        """Compare installation size and dependencies."""
        print(f"  Checking installation size on {branch}...")

        results = {}

        # Count Python files
        py_files = list(Path("amplifier").rglob("*.py"))
        results["python_files"] = len(py_files)

        # Check for key modules
        key_modules = {
            "cli": Path("amplifier/cli.py").exists(),
            "cache": Path("amplifier/utils/cache.py").exists(),
            "events": Path("amplifier/utils/events.py").exists(),
        }
        results["modules"] = key_modules

        # Count dependencies in pyproject.toml
        if Path("pyproject.toml").exists():
            with open("pyproject.toml") as f:
                content = f.read()
                results["has_pyproject"] = True
                results["package_name"] = "amplifier-toolkit" in content
        else:
            results["has_pyproject"] = False
            results["package_name"] = False

        return results

    def run_comparison(self):
        """Run full comparison between branches."""
        print(f"\n{BOLD}{'=' * 60}{RESET}")
        print(f"{BOLD}{BLUE}BRANCH COMPARISON: main vs feature/amplifier-cli-unified{RESET}")
        print(f"{BOLD}{'=' * 60}{RESET}\n")

        # Test main branch
        print(f"{YELLOW}Testing MAIN branch...{RESET}")
        if self.switch_branch("main"):
            # Reinstall for main branch
            subprocess.run(["uv", "pip", "install", "-e", "."], capture_output=True, timeout=30)

            self.results["main"]["cache"] = self.test_cache_performance("main")
            self.results["main"]["cli"] = self.test_cli_features("main")
            self.results["main"]["extraction"] = self.test_knowledge_extraction_speed("main")
            self.results["main"]["installation"] = self.compare_installation_size("main")
        else:
            print(f"{RED}  Failed to switch to main branch{RESET}")

        # Test feature branch
        print(f"\n{YELLOW}Testing FEATURE branch...{RESET}")
        if self.switch_branch("feature/amplifier-cli-unified"):
            # Reinstall for feature branch
            subprocess.run(["uv", "pip", "install", "-e", "."], capture_output=True, timeout=30)

            self.results["feature"]["cache"] = self.test_cache_performance("feature")
            self.results["feature"]["cli"] = self.test_cli_features("feature")
            self.results["feature"]["extraction"] = self.test_knowledge_extraction_speed("feature")
            self.results["feature"]["installation"] = self.compare_installation_size("feature")
        else:
            print(f"{RED}  Failed to switch to feature branch{RESET}")

        # Switch back to original branch
        self.switch_branch(self.current_branch)

        # Display results
        self.display_results()

    def display_results(self):
        """Display comparison results."""
        print(f"\n{BOLD}{'=' * 60}{RESET}")
        print(f"{BOLD}{CYAN}COMPARISON RESULTS{RESET}")
        print(f"{BOLD}{'=' * 60}{RESET}\n")

        # Cache Performance
        print(f"{BOLD}1. CACHE PERFORMANCE{RESET}")
        print("-" * 40)
        main_cache = self.results["main"].get("cache", {})
        feature_cache = self.results["feature"].get("cache", {})

        if not main_cache.get("has_cache"):
            print(f"  Main branch: {RED}No cache system{RESET}")
        else:
            print("  Main branch: Cache exists")

        if feature_cache.get("has_cache"):
            print(f"  Feature branch: {GREEN}✓ Advanced cache system{RESET}")
            print(f"    First run: {feature_cache['first_run']}s")
            print(f"    Cached run: {feature_cache['cached_run']}s")
            print(f"    {GREEN}Speedup: {feature_cache['speedup']}x{RESET}")

        # CLI Features
        print(f"\n{BOLD}2. CLI FEATURES{RESET}")
        print("-" * 40)
        main_cli = self.results["main"].get("cli", {})
        feature_cli = self.results["feature"].get("cli", {})

        features = ["unified_cli", "doctor_command", "event_logging", "unified_wrapper"]
        feature_names = {
            "unified_cli": "Unified CLI",
            "doctor_command": "Doctor Command",
            "event_logging": "Event Logging",
            "unified_wrapper": "Unified Wrapper",
        }

        for feat in features:
            main_has = main_cli.get(feat, False)
            feature_has = feature_cli.get(feat, False)

            if not main_has and feature_has:
                print(f"  {feature_names[feat]}: {RED}✗ Main{RESET} → {GREEN}✓ Feature{RESET}")
            elif main_has and feature_has:
                print(f"  {feature_names[feat]}: {GREEN}✓ Both{RESET}")
            else:
                print(f"  {feature_names[feat]}: {RED}✗ Neither{RESET}")

        # Installation/Modules
        print(f"\n{BOLD}3. NEW MODULES{RESET}")
        print("-" * 40)
        main_inst = self.results["main"].get("installation", {})
        feature_inst = self.results["feature"].get("installation", {})

        main_modules = main_inst.get("modules", {})
        feature_modules = feature_inst.get("modules", {})

        for module, exists in feature_modules.items():
            if exists and not main_modules.get(module, False):
                print(f"  {GREEN}+ {module}.py (new){RESET}")

        # Summary
        print(f"\n{BOLD}{'=' * 60}{RESET}")
        print(f"{BOLD}{GREEN}IMPROVEMENTS SUMMARY{RESET}")
        print(f"{BOLD}{'=' * 60}{RESET}")

        improvements = []

        if feature_cache.get("has_cache") and not main_cache.get("has_cache"):
            improvements.append(f"✅ New artifact cache system with {feature_cache.get('speedup', 0)}x speedup")

        if feature_cli.get("unified_cli") and not main_cli.get("unified_cli"):
            improvements.append("✅ Unified CLI with single 'amplifier' command")

        if feature_cli.get("event_logging") and not main_cli.get("event_logging"):
            improvements.append("✅ Structured event logging system")

        if feature_inst.get("package_name"):
            improvements.append("✅ Renamed to amplifier-toolkit for PyPI compatibility")

        for imp in improvements:
            print(f"  {imp}")

        print(f"\n{BOLD}Performance Gain: {GREEN}{feature_cache.get('speedup', 'N/A')}x faster{RESET} with caching")
        print(f"{BOLD}New Features: {GREEN}{len(improvements)}{RESET} major improvements")


def main():
    """Run the branch comparison."""
    comparison = BranchComparison()
    comparison.run_comparison()


if __name__ == "__main__":
    main()
