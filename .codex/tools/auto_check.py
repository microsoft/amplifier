#!/usr/bin/env python3
"""
Auto-check utility for running quality checks on modified files.
Called by amplify-codex.sh after session ends.
Reads file paths from stdin (one per line).
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from amplifier.core.backend import BackendFactory  # noqa: E402


def main():
    """Run auto-quality checks on modified files"""
    try:
        # Read modified files from stdin
        modified_files = []
        for line in sys.stdin:
            line = line.strip()
            if line:
                modified_files.append(line)

        if not modified_files:
            print("No files to check")
            return

        print(f"Running quality checks on {len(modified_files)} files...")

        # Get backend
        backend = BackendFactory.create(backend_type="codex")

        # Run quality checks
        result = backend.run_quality_checks(file_paths=modified_files)

        if result:
            print("\nQuality Check Results:")
            if "passed" in result and result["passed"]:
                print("✅ All checks passed")
            else:
                print("❌ Some checks failed")
                if "output" in result:
                    print(result["output"])
        else:
            print("Quality checks completed (no detailed results)")

    except Exception as e:
        print(f"Auto-check failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
