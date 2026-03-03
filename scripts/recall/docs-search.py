#!/usr/bin/env python3
"""BM25 search across indexed project documentation.

Usage:
    uv run python scripts/recall/docs-search.py QUERY [-n N] [--project P] [--category C]
    uv run python scripts/recall/docs-search.py --list [PROJECT] [--category C]
    uv run python scripts/recall/docs-search.py --recent N [--project P]
    uv run python scripts/recall/docs-search.py --stats

Searches the FTS5 index built by extract-docs.py.

Examples:
    uv run python scripts/recall/docs-search.py "exchange deployment"
    uv run python scripts/recall/docs-search.py "mailbox provider" --project fusecp-enterprise
    uv run python scripts/recall/docs-search.py "cluster awareness" --category spec
    uv run python scripts/recall/docs-search.py --list amplifier --category config
    uv run python scripts/recall/docs-search.py --recent 7
    uv run python scripts/recall/docs-search.py --stats
"""

import io
import sys
import sqlite3
import argparse
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

DOCS_DB = Path.home() / ".claude" / "docs-index.sqlite"


def search_docs(query: str, limit: int, db_path: Path,
                project: str | None = None, category: str | None = None) -> list[dict]:
    """Search FTS5 index with BM25 ranking."""
    if not db_path.exists():
        print(f"Error: Doc index not found at {db_path}")
        print("Run: uv run python scripts/recall/extract-docs.py --full")
        return []

    conn = sqlite3.connect(str(db_path))

    # Build FTS5 query — quote each word to prevent operator interpretation
    words = query.strip().split()
    quoted_words = [f'"{w.replace(chr(34), "")}"' for w in words if w.replace('"', "")]
    fts_query = " OR ".join(quoted_words)

    # Build SQL with optional filters
    sql = """SELECT project, path, title, category,
                    snippet(docs, 4, '>>>', '<<<', '...', 40),
                    rank
             FROM docs
             WHERE docs MATCH ?"""
    params: list = [fts_query]

    if project:
        sql += " AND project = ?"
        params.append(project)
    if category:
        sql += " AND category = ?"
        params.append(category)

    sql += " ORDER BY rank LIMIT ?"
    params.append(limit)

    try:
        rows = conn.execute(sql, params).fetchall()
    except Exception as e:
        print(f"Search error: {e}")
        return []
    finally:
        conn.close()

    results = []
    for row in rows:
        results.append({
            "project": row[0],
            "path": row[1],
            "title": row[2],
            "category": row[3],
            "snippet": row[4],
            "score": row[5],
        })
    return results


def list_docs(db_path: Path, project: str | None = None,
              category: str | None = None) -> list[dict]:
    """List docs from the index, optionally filtered."""
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))

    sql = "SELECT project, rel_path, title, category FROM indexed_docs WHERE 1=1"
    params: list = []

    if project:
        sql += " AND project = ?"
        params.append(project)
    if category:
        sql += " AND category = ?"
        params.append(category)

    sql += " ORDER BY project, category, rel_path"

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return [{"project": r[0], "path": r[1], "title": r[2], "category": r[3]} for r in rows]


def recent_docs(db_path: Path, days: int, project: str | None = None) -> list[dict]:
    """List recently modified docs."""
    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    import time
    cutoff = time.time() - (days * 86400)

    sql = """SELECT project, rel_path, title, category, mtime
             FROM indexed_docs WHERE mtime > ?"""
    params: list = [cutoff]

    if project:
        sql += " AND project = ?"
        params.append(project)

    sql += " ORDER BY mtime DESC"

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    from datetime import datetime, timezone
    return [{
        "project": r[0], "path": r[1], "title": r[2], "category": r[3],
        "modified": datetime.fromtimestamp(r[4], tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
    } for r in rows]


def show_stats(db_path: Path) -> None:
    """Show index statistics."""
    if not db_path.exists():
        print(f"No index at {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    total = conn.execute("SELECT COUNT(*) FROM indexed_docs").fetchone()[0]
    by_project = conn.execute(
        "SELECT project, COUNT(*) FROM indexed_docs GROUP BY project ORDER BY COUNT(*) DESC"
    ).fetchall()
    by_category = conn.execute(
        "SELECT category, COUNT(*) FROM indexed_docs GROUP BY category ORDER BY COUNT(*) DESC"
    ).fetchall()
    conn.close()

    print(f"\n## Doc Index Stats ({total} total)\n")
    print("By project:")
    for proj, cnt in by_project:
        print(f"  {proj:<35} {cnt:>4}")
    print("\nBy category:")
    for cat, cnt in by_category:
        print(f"  {cat:<35} {cnt:>4}")


def main():
    parser = argparse.ArgumentParser(description="Search project documentation")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("-n", "--limit", type=int, default=10, help="Max results (default: 10)")
    parser.add_argument("--project", type=str, default=None, help="Filter by project")
    parser.add_argument("--category", type=str, default=None, help="Filter by category")
    parser.add_argument("--list", nargs="?", const="__all__", default=None,
                        help="List docs (optionally for a project)")
    parser.add_argument("--recent", type=int, default=None, help="Show docs modified in last N days")
    parser.add_argument("--stats", action="store_true", help="Show index statistics")
    parser.add_argument("--db", type=str, default=None, help=f"Database path (default: {DOCS_DB})")
    args = parser.parse_args()

    db_path = Path(args.db) if args.db else DOCS_DB

    if args.stats:
        show_stats(db_path)
        return

    if args.recent is not None:
        results = recent_docs(db_path, args.recent, project=args.project)
        if results:
            print(f"\n## Docs modified in last {args.recent} days ({len(results)} found)\n")
            for r in results:
                print(f"  [{r['modified']}] {r['project']}/{r['path']}")
                print(f"    {r['title']} ({r['category']})")
                print()
        else:
            print(f"No docs modified in last {args.recent} days")
        return

    if args.list is not None:
        project = args.list if args.list != "__all__" else args.project
        results = list_docs(db_path, project=project, category=args.category)
        if results:
            current_project = None
            for r in results:
                if r["project"] != current_project:
                    current_project = r["project"]
                    print(f"\n## {current_project}\n")
                print(f"  {r['category']:<12} {r['path']:<55} {r['title'][:50]}")
        else:
            print("No docs found matching filters")
        return

    if not args.query:
        parser.print_help()
        return

    results = search_docs(args.query, args.limit, db_path,
                          project=args.project, category=args.category)
    if results:
        print(f"\n## Search: \"{args.query}\" ({len(results)} results)\n")
        for r in results:
            print(f"  [{r['project']}] {r['title']} ({r['category']})")
            print(f"    Path: {r['path']}")
            print(f"    ...{r['snippet']}...")
            print(f"    Score: {r['score']:.4f}")
            print()
    else:
        print(f"No results for '{args.query}'")


if __name__ == "__main__":
    main()
