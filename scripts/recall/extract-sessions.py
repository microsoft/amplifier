#!/usr/bin/env python3
"""Extract user messages from Claude Code session logs into searchable markdown.

Usage:
    uv run python scripts/recall/extract-sessions.py [--days 21] [--source DIR] [--output DIR]

Extracts YOUR messages from Claude Code JSONL session logs.
Strips system tags, slash commands, and agent noise.
Creates one markdown file per session with timestamp headers.
Also indexes all extracted content into a SQLite FTS5 database for BM25 search.

Output files: YYYY-MM-DD-HHMM-{session_id_short}.md
Each file has frontmatter (date, session_id, title, type, messages count)
and each user message as its own ## section with timestamp.
"""

import json
import sys
import sqlite3
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Import shared functions from the canonical module
sys.path.insert(0, str(Path(__file__).parent))
from recall_day import clean_content, extract_text, CLAUDE_PROJECTS

DEFAULT_OUTPUT = Path.home() / ".claude" / "recall-sessions"
FTS_DB = Path.home() / ".claude" / "recall-index.sqlite"


def scan_session(filepath: Path, cutoff: datetime) -> dict | None:
    """Scan a JSONL session file and extract user messages after cutoff."""
    messages = []
    first_ts = None
    session_title = None

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Get timestamp
                ts_str = entry.get("timestamp")
                if not ts_str:
                    continue
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    continue

                if first_ts is None:
                    first_ts = ts

                if ts < cutoff:
                    continue

                # Extract user messages only
                msg_type = entry.get("type")
                if msg_type in ("user", "human"):
                    content = entry.get("message", {})
                    if isinstance(content, dict):
                        text = extract_text(content.get("content", ""))
                    else:
                        text = extract_text(content)

                    cleaned = clean_content(text)
                    if cleaned and len(cleaned) > 10:
                        messages.append(
                            {
                                "timestamp": ts,
                                "text": cleaned,
                            }
                        )
                        if session_title is None:
                            # First substantial message becomes session title
                            session_title = cleaned[:100].split("\n")[0]

    except (OSError, UnicodeDecodeError):
        return None

    if not messages or first_ts is None:
        return None

    return {
        "session_id": filepath.stem,
        "first_ts": first_ts,
        "title": session_title or "Untitled session",
        "messages": messages,
        "msg_count": len(messages),
    }


def write_session_md(session: dict, output_dir: Path) -> Path:
    """Write a session to a markdown file with frontmatter."""
    ts = session["first_ts"]
    short_id = session["session_id"][:8]
    filename = f"{ts.strftime('%Y-%m-%d-%H%M')}-{short_id}.md"
    filepath = output_dir / filename

    lines = [
        "---",
        f"date: {ts.strftime('%Y-%m-%d')}",
        f"session_id: {session['session_id']}",
        'title: "{}"'.format(session["title"][:200].replace('"', "'")),
        f"messages: {session['msg_count']}",
        "type: claude-session",
        "---",
        "",
        f"# {session['title'][:200]}",
        "",
    ]

    for msg in session["messages"]:
        lines.append(f"## {msg['timestamp'].strftime('%H:%M:%S')}")
        lines.append("")
        lines.append(msg["text"])
        lines.append("")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return filepath


def init_fts_db(db_path: Path) -> sqlite3.Connection:
    """Initialize SQLite FTS5 database for BM25 search."""
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """CREATE VIRTUAL TABLE IF NOT EXISTS sessions USING fts5(
            session_id,
            date,
            title,
            content,
            filepath,
            tokenize='porter unicode61'
        )"""
    )
    # Metadata table for tracking indexed sessions
    conn.execute(
        """CREATE TABLE IF NOT EXISTS indexed_sessions (
            session_id TEXT PRIMARY KEY,
            filepath TEXT,
            indexed_at TEXT
        )"""
    )
    conn.commit()
    return conn


def index_session(conn: sqlite3.Connection, session: dict, md_path: Path) -> None:
    """Index a session into the FTS5 database."""
    sid = session["session_id"]

    # Check if already indexed
    row = conn.execute(
        "SELECT 1 FROM indexed_sessions WHERE session_id = ?", (sid,)
    ).fetchone()
    if row:
        return

    # Combine all messages into searchable content
    content = "\n\n".join(msg["text"] for msg in session["messages"])

    conn.execute(
        "INSERT INTO sessions(session_id, date, title, content, filepath) VALUES (?, ?, ?, ?, ?)",
        (
            sid,
            session["first_ts"].strftime("%Y-%m-%d"),
            session["title"][:200],
            content,
            str(md_path),
        ),
    )
    conn.execute(
        "INSERT INTO indexed_sessions(session_id, filepath, indexed_at) VALUES (?, ?, ?)",
        (sid, str(md_path), datetime.now(timezone.utc).isoformat()),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Extract Claude Code sessions to markdown + FTS5 index"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=21,
        help="Extract sessions from last N days (default: 21)",
    )
    parser.add_argument(
        "--source", type=str, default=None, help="Source project dir (default: all)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=f"Output dir (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help=f"FTS5 database path (default: {FTS_DB})",
    )
    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else DEFAULT_OUTPUT
    output_dir.mkdir(parents=True, exist_ok=True)

    db_path = Path(args.db) if args.db else FTS_DB
    conn = init_fts_db(db_path)

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)

    # Collect source directories
    if args.source:
        source_dirs = [Path(args.source)]
    else:
        source_dirs = [
            d for d in CLAUDE_PROJECTS.iterdir() if d.is_dir()
        ]

    # Track existing output files to avoid re-processing
    existing = {f.stem for f in output_dir.glob("*.md")}

    total_extracted = 0
    total_skipped = 0
    total_indexed = 0

    for proj_dir in source_dirs:
        jsonl_files = list(proj_dir.glob("*.jsonl"))
        for filepath in jsonl_files:
            # Quick mtime check to skip old files
            try:
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc)
                if mtime < cutoff - timedelta(days=1):
                    continue
            except OSError:
                continue

            session = scan_session(filepath, cutoff)
            if session is None:
                continue

            # Check if already extracted (by matching date-time-shortid pattern)
            short_id = session["session_id"][:8]
            ts = session["first_ts"]
            expected_stem = f"{ts.strftime('%Y-%m-%d-%H%M')}-{short_id}"

            if expected_stem in existing:
                total_skipped += 1
                # Still index if not in FTS yet
                md_path = output_dir / f"{expected_stem}.md"
                index_session(conn, session, md_path)
                continue

            out_path = write_session_md(session, output_dir)
            index_session(conn, session, out_path)
            total_extracted += 1
            total_indexed += 1
            print(f"  Extracted: {out_path.name} ({session['msg_count']} messages)")

    conn.commit()
    conn.close()

    # Count total indexed
    conn2 = sqlite3.connect(str(db_path))
    total_in_db = conn2.execute("SELECT COUNT(*) FROM indexed_sessions").fetchone()[0]
    conn2.close()

    print(f"\nDone: {total_extracted} new sessions extracted, {total_skipped} already existed")
    print(f"FTS5 index: {total_in_db} total sessions indexed at {db_path}")
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()
