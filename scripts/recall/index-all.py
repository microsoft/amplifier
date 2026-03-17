#!/usr/bin/env python3
"""Consolidated recall indexer — runs all three indexing tasks in one process."""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent


def run_script(name: str, args: list[str]) -> None:
    """Run a recall script, logging errors to stderr."""
    script = SCRIPTS_DIR / name
    if not script.exists():
        return
    try:
        result = subprocess.run(
            [sys.executable, str(script)] + args,
            capture_output=True,
            timeout=20,
        )
        if result.returncode != 0:
            print(
                f"[index-all] {name} failed (exit {result.returncode})", file=sys.stderr
            )
            if result.stderr:
                # Show last 500 chars — key info is at the end of tracebacks
                stderr_text = result.stderr.decode(errors="replace")[-500:]
                print(f"  {stderr_text}", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print(f"[index-all] {name} timed out after 20s", file=sys.stderr)
    except Exception as e:
        print(f"[index-all] {name} error: {e}", file=sys.stderr)


def main() -> None:
    run_script("extract-sessions.py", ["--days", "3"])
    run_script("extract-docs.py", ["--recent", "3"])
    run_script("generate-doc-registry.py", [])


if __name__ == "__main__":
    main()
