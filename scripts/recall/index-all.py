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


def ensure_retros_table() -> None:
    """Create retros table in recall-index.sqlite if it doesn't exist."""
    import sqlite3

    db_path = Path.home() / ".claude" / "recall-index.sqlite"
    if not db_path.exists():
        return  # DB created by extract-sessions.py on first run
    conn = sqlite3.connect(str(db_path))
    conn.execute("""CREATE TABLE IF NOT EXISTS retros (
        id              INTEGER PRIMARY KEY,
        session_id      TEXT NOT NULL,
        timestamp       TEXT NOT NULL,
        smoothness      TEXT NOT NULL,
        total_agents    INTEGER,
        successful_agents INTEGER,
        total_retries   INTEGER,
        loops_detected  INTEGER,
        friction_points TEXT,
        learnings       TEXT,
        open_items      TEXT,
        UNIQUE(session_id)
    )""")
    conn.commit()
    conn.close()


def main() -> None:
    ensure_retros_table()
    run_script("extract-sessions.py", ["--days", "3"])
    run_script("extract-docs.py", ["--recent", "3"])
    run_script("generate-doc-registry.py", [])


if __name__ == "__main__":
    main()
