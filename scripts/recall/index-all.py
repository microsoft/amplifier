#!/usr/bin/env python3
"""Consolidated recall indexer — runs all three indexing tasks in one process."""
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent


def run_script(name: str, args: list[str]) -> None:
    """Run a recall script, suppressing errors."""
    script = SCRIPTS_DIR / name
    if script.exists():
        try:
            subprocess.run(
                [sys.executable, str(script)] + args,
                capture_output=True,
                timeout=20,
            )
        except (subprocess.TimeoutExpired, Exception):
            pass


def main() -> None:
    run_script("extract-sessions.py", ["--days", "3"])
    run_script("extract-docs.py", ["--recent", "3"])
    run_script("generate-doc-registry.py", [])


if __name__ == "__main__":
    main()
