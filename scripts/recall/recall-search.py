#!/usr/bin/env python3
"""BM25 topic search across indexed Claude Code sessions.

Usage:
    uv run python scripts/recall/recall-search.py QUERY [-n N] [-c COLLECTION]

Searches the FTS5 index built by extract-sessions.py.
Returns results ranked by BM25 relevance.

Examples:
    uv run python scripts/recall/recall-search.py "FuseCP exchange mailbox"
    uv run python scripts/recall/recall-search.py "authentication bug" -n 10
"""

import io
import sys
import sqlite3
import argparse
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

FTS_DB = Path.home() / ".claude" / "recall-index.sqlite"


def _find_memory_dir() -> Path:
    """Find amplifier memory directory (platform-agnostic)."""
    base = Path.home() / ".claude" / "projects"
    for name in ("-opt-amplifier", "C--claude-amplifier"):
        candidate = base / name / "memory"
        if candidate.is_dir():
            return candidate
    return base / "-opt-amplifier" / "memory"


MEMORY_DIR = _find_memory_dir()


def search_fts(query: str, limit: int, db_path: Path) -> list[dict]:
    """Search FTS5 index with BM25 ranking."""
    if not db_path.exists():
        print(f"Error: FTS5 index not found at {db_path}")
        print("Run: uv run python scripts/recall/extract-sessions.py")
        return []

    conn = sqlite3.connect(str(db_path))

    # FTS5 query — tokenize words for BM25 matching
    # Quote each word to prevent FTS5 operator interpretation (e.g. -V as NOT)
    # Strip embedded quotes to prevent malformed FTS5 syntax
    words = query.strip().split()
    quoted_words = [f'"{w.replace(chr(34), "")}"' for w in words if w.replace('"', "")]
    fts_query = " OR ".join(quoted_words)

    try:
        rows = conn.execute(
            """SELECT session_id, date, title, snippet(sessions, 3, '>>>', '<<<', '...', 40),
                      rank, filepath
               FROM sessions
               WHERE sessions MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (fts_query, limit),
        ).fetchall()
    except Exception as e:
        print(f"Search error: {e}")
        return []
    finally:
        conn.close()

    results = []
    for row in rows:
        results.append(
            {
                "session_id": row[0][:12],
                "date": row[1],
                "title": row[2][:100],
                "snippet": row[3],
                "score": row[4],
                "filepath": row[5],
            }
        )
    return results


def search_memory_files(query: str, limit: int) -> list[dict]:
    """Simple keyword search in auto-memory markdown files."""
    if not MEMORY_DIR.exists():
        return []

    results = []
    words = query.lower().split()

    for md_file in MEMORY_DIR.glob("*.md"):
        try:
            raw = md_file.read_text(encoding="utf-8", errors="replace")
            content = raw.lower()
            # Count word matches
            matches = sum(1 for w in words if w in content)
            if matches > 0:
                # Get first matching line as snippet
                snippet = ""
                for line in raw.split("\n"):
                    if any(w in line.lower() for w in words):
                        snippet = line.strip()[:120]
                        break
                results.append(
                    {
                        "file": md_file.name,
                        "matches": matches,
                        "snippet": snippet,
                        "filepath": str(md_file),
                    }
                )
        except OSError:
            continue

    results.sort(key=lambda r: -r["matches"])
    return results[:limit]


def main():
    parser = argparse.ArgumentParser(
        description="BM25 search across Claude Code sessions"
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "-n", "--limit", type=int, default=5, help="Max results (default: 5)"
    )
    parser.add_argument(
        "-c",
        "--collection",
        choices=["sessions", "memory", "all"],
        default="all",
        help="Collection to search (default: all)",
    )
    parser.add_argument(
        "--db", type=str, default=None, help=f"FTS5 database path (default: {FTS_DB})"
    )
    args = parser.parse_args()

    db_path = Path(args.db) if args.db else FTS_DB

    session_results = []
    mem_results = []

    if args.collection in ("sessions", "all"):
        session_results = search_fts(args.query, args.limit, db_path)
        if session_results:
            print(f"\n## Sessions ({len(session_results)} results)\n")
            for r in session_results:
                print(f"  [{r['date']}] {r['title']}")
                print(f"    ...{r['snippet']}...")
                print(f"    Session: {r['session_id']} | Score: {r['score']:.4f}")
                print()
        else:
            print(f"No session results for '{args.query}'")

    if args.collection in ("memory", "all"):
        mem_results = search_memory_files(args.query, args.limit)
        if mem_results:
            print(f"\n## Memory ({len(mem_results)} results)\n")
            for r in mem_results:
                print(f"  [{r['file']}] ({r['matches']} keyword matches)")
                print(f"    {r['snippet']}")
                print()
        else:
            print(f"No memory results for '{args.query}'")


if __name__ == "__main__":
    main()
