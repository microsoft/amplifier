#!/usr/bin/env python3
"""Index project documentation into FTS5 for BM25 search.

Usage:
    uv run python scripts/recall/extract-docs.py [--full] [--recent N]

Scans all project directories for .md files and indexes them into
a SQLite FTS5 database for fast keyword search.

Incremental by default — only re-indexes files whose mtime changed.
Use --full to force complete re-index.
"""

import io
import re
import sys
import sqlite3
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

DOCS_DB = Path.home() / ".claude" / "docs-index.sqlite"
WORKSPACE_ROOT = Path("C:/claude")


def discover_project_roots(workspace: Path) -> dict[str, Path]:
    """Auto-discover git repos under the workspace directory."""
    roots = {}
    if not workspace.exists():
        return roots
    for child in sorted(workspace.iterdir()):
        if child.is_dir() and (child / ".git").exists():
            roots[child.name] = child
    return roots


# Auto-discover all git repos under C:\claude\
PROJECT_ROOTS = discover_project_roots(WORKSPACE_ROOT)

# Directories to skip
SKIP_DIRS = {
    "node_modules", ".venv", ".git", "vendor", "__pycache__",
    ".tox", ".mypy_cache", ".ruff_cache", "dist", "build",
    ".claude-worktrees", "worktrees",
}

# Files to skip
SKIP_FILES = {"llms-full.txt", "uv.lock", "package-lock.json"}

# Category detection from relative path
CATEGORY_PATTERNS = [
    (re.compile(r"^docs/plans/"), "plan"),
    (re.compile(r"^docs/specs/"), "spec"),
    (re.compile(r"^docs/api/"), "api"),
    (re.compile(r"^docs/testing/"), "testing"),
    (re.compile(r"^docs/reviews/"), "review"),
    (re.compile(r"^docs/reports/"), "report"),
    (re.compile(r"^\.claude/agents/"), "agent"),
    (re.compile(r"^\.claude/commands/"), "command"),
    (re.compile(r"^\.claude/context/"), "context"),
    (re.compile(r"^ai_context/"), "philosophy"),
    (re.compile(r"^context/"), "context"),
    (re.compile(r"^scripts/"), "script"),
    (re.compile(r"^(CLAUDE|AGENTS|COWORK|DISCOVERIES)\.md$"), "config"),
    (re.compile(r"^README\.md$"), "readme"),
    (re.compile(r"^(CHANGELOG|NEWS|CONTRIBUTING|SECURITY|SUPPORT)\.md$"), "meta"),
]


def detect_category(rel_path: str) -> str:
    """Auto-detect document category from its relative path."""
    rel_path = rel_path.replace("\\", "/")
    for pattern, category in CATEGORY_PATTERNS:
        if pattern.search(rel_path):
            return category
    return "guide"


def extract_title(content: str, filename: str) -> str:
    """Extract title from first # heading or use filename."""
    for line in content.split("\n")[:20]:
        line = line.strip()
        if line.startswith("# ") and not line.startswith("# ---"):
            return line[2:].strip()[:200]
    # Fallback to filename without extension
    return Path(filename).stem.replace("-", " ").replace("_", " ").title()[:200]


def should_skip_dir(dirname: str) -> bool:
    """Check if a directory should be skipped."""
    return dirname in SKIP_DIRS or dirname.startswith(".")


def collect_md_files(project: str, root: Path, recent_days: int | None = None) -> list[dict]:
    """Collect all .md files from a project directory."""
    if not root.exists():
        return []

    cutoff = None
    if recent_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=recent_days)

    results = []
    for md_file in root.rglob("*.md"):
        # Skip excluded directories
        parts = md_file.relative_to(root).parts
        if any(should_skip_dir(p) for p in parts[:-1]):
            continue

        # Skip excluded files
        if md_file.name in SKIP_FILES:
            continue

        # Check mtime for recent-only mode
        try:
            mtime = md_file.stat().st_mtime
            if cutoff:
                mtime_dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
                if mtime_dt < cutoff:
                    continue
        except OSError:
            continue

        rel_path = str(md_file.relative_to(root)).replace("\\", "/")

        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Skip very small files (< 20 chars) and very large files (> 500KB)
        if len(content) < 20 or len(content) > 512_000:
            continue

        title = extract_title(content, md_file.name)
        category = detect_category(rel_path)

        results.append({
            "project": project,
            "path": rel_path,
            "abs_path": str(md_file),
            "title": title,
            "category": category,
            "content": content,
            "mtime": mtime,
        })

    return results


def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize FTS5 database for doc search."""
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(
            project,
            path,
            title,
            category,
            content,
            tokenize='porter unicode61'
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS indexed_docs (
            full_path TEXT PRIMARY KEY,
            project TEXT,
            rel_path TEXT,
            title TEXT,
            category TEXT,
            mtime REAL,
            indexed_at TEXT
        )"""
    )
    conn.commit()
    return conn


def index_doc(conn: sqlite3.Connection, doc: dict, force: bool = False) -> bool:
    """Index a single document. Returns True if indexed (new or updated)."""
    full_path = doc["abs_path"]

    # Check if already indexed with same mtime
    if not force:
        row = conn.execute(
            "SELECT mtime FROM indexed_docs WHERE full_path = ?", (full_path,)
        ).fetchone()
        if row and abs(row[0] - doc["mtime"]) < 1.0:
            return False

    # Remove old entry if exists
    old = conn.execute(
        "SELECT rowid FROM indexed_docs WHERE full_path = ?", (full_path,)
    ).fetchone()
    if old:
        # Delete from FTS5 — need to find matching row
        conn.execute(
            "DELETE FROM docs WHERE project = ? AND path = ?",
            (doc["project"], doc["path"]),
        )
        conn.execute("DELETE FROM indexed_docs WHERE full_path = ?", (full_path,))

    # Insert into FTS5
    conn.execute(
        "INSERT INTO docs(project, path, title, category, content) VALUES (?, ?, ?, ?, ?)",
        (doc["project"], doc["path"], doc["title"], doc["category"], doc["content"]),
    )

    # Insert into tracking table
    conn.execute(
        """INSERT INTO indexed_docs(full_path, project, rel_path, title, category, mtime, indexed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            full_path,
            doc["project"],
            doc["path"],
            doc["title"],
            doc["category"],
            doc["mtime"],
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    return True


def main():
    parser = argparse.ArgumentParser(description="Index project docs into FTS5")
    parser.add_argument(
        "--full", action="store_true", help="Force full re-index of all docs"
    )
    parser.add_argument(
        "--recent", type=int, default=None,
        help="Only index docs modified in last N days (default: all)",
    )
    parser.add_argument(
        "--db", type=str, default=None,
        help=f"Database path (default: {DOCS_DB})",
    )
    args = parser.parse_args()

    db_path = Path(args.db) if args.db else DOCS_DB
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if args.full and db_path.exists():
        db_path.unlink()
        print("Cleared existing index for full rebuild.")

    conn = init_db(db_path)

    total_new = 0
    total_updated = 0
    total_skipped = 0

    for project, root in sorted(PROJECT_ROOTS.items()):
        if not root.exists():
            continue

        docs = collect_md_files(project, root, recent_days=args.recent)
        project_indexed = 0

        for doc in docs:
            if index_doc(conn, doc, force=args.full):
                project_indexed += 1
                total_new += 1
            else:
                total_skipped += 1

        if project_indexed > 0:
            print(f"  {project}: {project_indexed} docs indexed")

    conn.commit()

    # Report totals
    total_in_db = conn.execute("SELECT COUNT(*) FROM indexed_docs").fetchone()[0]
    projects_in_db = conn.execute(
        "SELECT project, COUNT(*) FROM indexed_docs GROUP BY project ORDER BY project"
    ).fetchall()
    conn.close()

    print(f"\nDone: {total_new} new/updated, {total_skipped} unchanged")
    print(f"Total in index: {total_in_db} docs")
    for proj, cnt in projects_in_db:
        print(f"  {proj}: {cnt}")
    print(f"Database: {db_path}")


if __name__ == "__main__":
    main()
