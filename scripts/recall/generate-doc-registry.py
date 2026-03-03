#!/usr/bin/env python3
"""Generate a lightweight doc registry for session-start context loading.

Usage:
    uv run python scripts/recall/generate-doc-registry.py [--db PATH] [--output PATH]

Reads the FTS5 doc index and produces a compact markdown file listing
every indexed doc with project, category, path, and title.
This file is loaded at session start so Claude knows where all docs are
without spending tokens on search.
"""

import io
import sys
import sqlite3
import argparse
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DOCS_DB = Path.home() / ".claude" / "docs-index.sqlite"
REGISTRY_PATH = Path.home() / ".claude" / "docs-registry.md"


def generate_registry(db_path: Path, output_path: Path) -> None:
    """Generate the doc registry markdown file."""
    if not db_path.exists():
        print(f"Error: Doc index not found at {db_path}")
        print("Run: uv run python scripts/recall/extract-docs.py --full")
        return

    conn = sqlite3.connect(str(db_path))

    # Get all docs grouped by project
    rows = conn.execute(
        """SELECT project, rel_path, title, category
           FROM indexed_docs
           ORDER BY project, category, rel_path"""
    ).fetchall()

    total = len(rows)

    # Get project counts
    project_counts = conn.execute(
        "SELECT project, COUNT(*) FROM indexed_docs GROUP BY project ORDER BY project"
    ).fetchall()
    conn.close()

    lines = [
        "# Doc Registry",
        f"<!-- Auto-generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC — {total} docs -->",
        f"<!-- Search: /docs QUERY | Browse: /docs list PROJECT | Recent: /docs recent N -->",
        "",
    ]

    current_project = None
    for proj, path, title, category in rows:
        if proj != current_project:
            current_project = proj
            count = next((c for p, c in project_counts if p == proj), 0)
            lines.append(f"## {proj} ({count})")
            lines.append("")

        # Compact format: category | path | title
        safe_title = title[:60].replace("|", "-")
        lines.append(f"  {category:<12} {path:<58} {safe_title}")

    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Registry generated: {output_path} ({total} docs, {len(lines)} lines)")


def main():
    parser = argparse.ArgumentParser(description="Generate doc registry")
    parser.add_argument("--db", type=str, default=None, help=f"Database path (default: {DOCS_DB})")
    parser.add_argument("--output", type=str, default=None, help=f"Output path (default: {REGISTRY_PATH})")
    args = parser.parse_args()

    db_path = Path(args.db) if args.db else DOCS_DB
    output_path = Path(args.output) if args.output else REGISTRY_PATH
    generate_registry(db_path, output_path)


if __name__ == "__main__":
    main()
