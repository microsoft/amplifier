"""
Mutation Testing System - Introduce bugs to verify contracts catch them.
This proves that behavioral contracts actually work and aren't just theater.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Any


def quick_mutation_test():
    """Quick demonstration of mutation testing concept."""

    print("Quick Mutation Test Demonstration")
    print("=" * 50)
    print()
    print("Mutation testing temporarily introduces bugs to verify")
    print("that behavioral contracts actually catch issues.")
    print()
    print("Example mutations that could be tested:")
    print("  • Disable input validation")
    print("  • Return incorrect values")
    print("  • Skip critical operations")
    print("  • Corrupt data structures")
    print()
    print("When a mutation is introduced:")
    print("  1. Apply the mutation to the code")
    print("  2. Run behavioral contracts")
    print("  3. Verify contracts detect the issue")
    print("  4. Restore original code")
    print()
    print("If contracts pass with mutations, they're not effective!")
    print()
    print("Full mutation testing can be implemented for specific projects")
    print("by creating project-specific mutations and testing them.")


class Mutation:
    """Represents a single code mutation."""

    def __init__(self, name: str, file_path: str, original: str, mutated: str):
        self.name = name
        self.file_path = file_path
        self.original = original
        self.mutated = mutated

    def apply(self, base_dir: Path):
        """Apply this mutation to the code."""
        file_path = base_dir / self.file_path
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text()

        if self.original not in content:
            raise ValueError(f"Original code not found in {self.file_path}")

        mutated_content = content.replace(self.original, self.mutated)
        file_path.write_text(mutated_content)

    def revert(self, base_dir: Path):
        """Revert this mutation."""
        file_path = base_dir / self.file_path
        if not file_path.exists():
            return

        content = file_path.read_text()

        if self.mutated in content:
            original_content = content.replace(self.mutated, self.original)
            file_path.write_text(original_content)


class MutationTester:
    """Tests whether contracts catch deliberate bugs."""

    def __init__(self, source_dir: Path, mutations: list[Mutation]):
        self.source_dir = source_dir
        self.mutations = mutations
        self.results = []

    def run_mutation_test(self, mutation: Mutation, test_function) -> dict[str, Any]:
        """Run a test function with a specific mutation applied."""

        # Create a temporary copy of the source
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_source = Path(tmpdir) / "mutated_code"
            shutil.copytree(self.source_dir, temp_source)

            try:
                # Apply mutation
                mutation.apply(temp_source)

                # Run the test function
                # The test function should return True if the mutation was caught
                caught = test_function(temp_source)

                return {
                    "mutation": mutation.name,
                    "caught": caught,
                }

            finally:
                # Cleanup happens automatically with temp directory
                pass

    def test_all_mutations(self, test_function) -> dict[str, Any]:
        """Test all mutations and report which ones were caught."""

        print("=" * 60)
        print("MUTATION TESTING")
        print("=" * 60)
        print("\nIntroducing deliberate bugs to verify contracts work...")
        print(f"Testing {len(self.mutations)} mutations\n")

        for mutation in self.mutations:
            print(f"Testing mutation: {mutation.name}")
            result = self.run_mutation_test(mutation, test_function)
            self.results.append(result)

            if result["caught"]:
                print("  ✅ Mutation caught by contracts!")
            else:
                print("  ❌ Mutation NOT caught - contracts may be ineffective")

        return self._generate_report()

    def _generate_report(self) -> dict[str, Any]:
        """Generate comprehensive mutation testing report."""

        caught_count = sum(1 for r in self.results if r.get("caught", False))
        not_caught = [r for r in self.results if not r.get("caught", False)]

        report = {
            "total_mutations": len(self.mutations),
            "caught": caught_count,
            "missed": len(not_caught),
            "effectiveness": (caught_count / len(self.mutations) * 100) if self.mutations else 0,
            "missed_mutations": not_caught,
            "all_results": self.results,
        }

        print("\n" + "=" * 60)
        print("MUTATION TESTING REPORT")
        print("=" * 60)

        print(f"\nMutations tested: {report['total_mutations']}")
        print(f"Caught by contracts: {report['caught']}")
        print(f"Missed: {report['missed']}")
        print(f"Effectiveness: {report['effectiveness']:.1f}%")

        if not_caught:
            print("\nMutations NOT caught:")
            for missed in not_caught:
                print(f"  • {missed['mutation']}")

        return report


if __name__ == "__main__":
    quick_mutation_test()
