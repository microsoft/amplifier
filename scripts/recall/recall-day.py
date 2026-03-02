#!/usr/bin/env python3
"""Temporal recall — scan Claude Code sessions by date.

Usage:
    uv run python scripts/recall/recall-day.py list DATE_EXPR [--min-msgs N] [--all-projects]
    uv run python scripts/recall/recall-day.py expand SESSION_ID

Date expressions:
    yesterday, today, YYYY-MM-DD, last monday..last sunday,
    this week, last week, N days ago, last N days

Examples:
    uv run python scripts/recall/recall-day.py list yesterday
    uv run python scripts/recall/recall-day.py list "last 3 days"
    uv run python scripts/recall/recall-day.py list "last week" --min-msgs 5
    uv run python scripts/recall/recall-day.py expand a26c7fc9-733b-4872-8657-41cd0b27040a
"""

import io
import sys
import json
import re
import argparse
from datetime import datetime, timezone, timedelta, date
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"

# Reuse strip patterns from extract-sessions
STRIP_PATTERNS = [
    re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL),
    re.compile(r"<local-command-caveat>.*?</local-command-caveat>", re.DOTALL),
    re.compile(r"<local-command-stdout>.*?</local-command-stdout>", re.DOTALL),
    re.compile(
        r"<command-name>.*?</command-name>\s*<command-message>.*?</command-message>\s*(?:<command-args>.*?</command-args>)?",
        re.DOTALL,
    ),
    re.compile(r"<command-message>.*?</command-message>", re.DOTALL),
    re.compile(r"<command-name>.*?</command-name>", re.DOTALL),
    re.compile(r"<command-args>.*?</command-args>", re.DOTALL),
    re.compile(r"<task-notification>.*?</task-notification>", re.DOTALL),
    re.compile(r"<teammate-message[^>]*>.*?</teammate-message>", re.DOTALL),
]


def clean_content(text: str) -> str:
    """Strip system tags."""
    if not isinstance(text, str):
        return ""
    for pat in STRIP_PATTERNS:
        text = pat.sub("", text)
    return text.strip()


def extract_text(content) -> str:
    """Extract text from message content (string or list of content blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return ""


def parse_date_expr(expr: str) -> tuple[date, date]:
    """Parse a natural language date expression into (start_date, end_date) inclusive."""
    expr = expr.strip().lower()
    today = date.today()

    if expr == "today":
        return today, today

    if expr == "yesterday":
        d = today - timedelta(days=1)
        return d, d

    # YYYY-MM-DD
    try:
        d = date.fromisoformat(expr)
        return d, d
    except ValueError:
        pass

    # "N days ago"
    m = re.match(r"(\d+)\s+days?\s+ago", expr)
    if m:
        d = today - timedelta(days=int(m.group(1)))
        return d, d

    # "last N days"
    m = re.match(r"last\s+(\d+)\s+days?", expr)
    if m:
        start = today - timedelta(days=int(m.group(1)))
        return start, today

    # "this week" (Mon-today)
    if expr == "this week":
        start = today - timedelta(days=today.weekday())
        return start, today

    # "last week" (Mon-Sun of previous week)
    if expr == "last week":
        start = today - timedelta(days=today.weekday() + 7)
        end = start + timedelta(days=6)
        return start, end

    # "last monday" .. "last sunday"
    day_names = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }
    m = re.match(r"last\s+(\w+)", expr)
    if m and m.group(1) in day_names:
        target = day_names[m.group(1)]
        days_back = (today.weekday() - target) % 7
        if days_back == 0:
            days_back = 7
        d = today - timedelta(days=days_back)
        return d, d

    # Fallback: try as date
    raise ValueError(f"Cannot parse date expression: '{expr}'")


def get_project_dirs(all_projects: bool) -> list[Path]:
    """Get project directories to scan."""
    if all_projects:
        return [d for d in CLAUDE_PROJECTS.iterdir() if d.is_dir()]

    # Try to detect current project from CWD
    # Default to amplifier project
    amplifier = CLAUDE_PROJECTS / "C--claude-amplifier"
    if amplifier.exists():
        return [amplifier]
    return [d for d in CLAUDE_PROJECTS.iterdir() if d.is_dir()]


def scan_sessions_for_dates(
    start: date, end: date, min_msgs: int, all_projects: bool
) -> list[dict]:
    """Scan JSONL files and return sessions within date range."""
    sessions = []
    start_dt = datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time()).replace(
        tzinfo=timezone.utc
    )

    for proj_dir in get_project_dirs(all_projects):
        for filepath in proj_dir.glob("*.jsonl"):
            # Quick mtime check
            try:
                mtime = datetime.fromtimestamp(
                    filepath.stat().st_mtime, tz=timezone.utc
                )
                if mtime < start_dt - timedelta(days=1):
                    continue
            except OSError:
                continue

            first_ts = None
            last_ts = None
            user_msgs = []
            assistant_count = 0

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

                        ts_str = entry.get("timestamp")
                        if not ts_str:
                            continue
                        try:
                            ts = datetime.fromisoformat(
                                ts_str.replace("Z", "+00:00")
                            )
                        except (ValueError, AttributeError):
                            continue

                        if first_ts is None:
                            first_ts = ts
                        last_ts = ts

                        msg_type = entry.get("type")
                        if msg_type in ("user", "human"):
                            content = entry.get("message", {})
                            if isinstance(content, dict):
                                text = extract_text(content.get("content", ""))
                            else:
                                text = extract_text(content)
                            cleaned = clean_content(text)
                            if cleaned and len(cleaned) > 5:
                                user_msgs.append({"timestamp": ts, "text": cleaned})
                        elif msg_type == "assistant":
                            assistant_count += 1

            except (OSError, UnicodeDecodeError):
                continue

            if first_ts is None or not user_msgs:
                continue

            # Check if session falls within date range
            if first_ts >= end_dt or (last_ts and last_ts < start_dt):
                continue

            if len(user_msgs) < min_msgs:
                continue

            first_msg = user_msgs[0]["text"][:120].split("\n")[0]

            # Filter out agent warmup sessions and context summaries
            if first_msg.startswith("Warmup") or first_msg.startswith("Context: This summary"):
                continue

            sessions.append(
                {
                    "session_id": filepath.stem,
                    "first_ts": first_ts,
                    "last_ts": last_ts,
                    "msg_count": len(user_msgs),
                    "assistant_count": assistant_count,
                    "first_msg": first_msg,
                    "messages": user_msgs,
                    "project": proj_dir.name,
                }
            )

    sessions.sort(key=lambda s: s["first_ts"])
    return sessions


def expand_session(session_id: str, all_projects: bool) -> dict | None:
    """Read full conversation flow for a specific session."""
    for proj_dir in get_project_dirs(all_projects):
        filepath = proj_dir / f"{session_id}.jsonl"
        if not filepath.exists():
            # Try partial match
            matches = list(proj_dir.glob(f"{session_id}*.jsonl"))
            if not matches:
                continue
            filepath = matches[0]

        entries = []
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

                    ts_str = entry.get("timestamp")
                    if not ts_str:
                        continue
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        continue

                    msg_type = entry.get("type")
                    if msg_type in ("user", "human"):
                        content = entry.get("message", {})
                        if isinstance(content, dict):
                            text = extract_text(content.get("content", ""))
                        else:
                            text = extract_text(content)
                        cleaned = clean_content(text)
                        if cleaned and len(cleaned) > 5:
                            entries.append(
                                {"type": "user", "timestamp": ts, "text": cleaned}
                            )

                    elif msg_type == "assistant":
                        content = entry.get("message", {})
                        if isinstance(content, dict):
                            text = extract_text(content.get("content", ""))
                        else:
                            text = extract_text(content)
                        # Just first line for assistant
                        first_line = (text or "")[:200].split("\n")[0]
                        if first_line:
                            entries.append(
                                {
                                    "type": "assistant",
                                    "timestamp": ts,
                                    "text": first_line,
                                }
                            )

        except (OSError, UnicodeDecodeError):
            continue

        if entries:
            return {
                "session_id": filepath.stem,
                "entries": entries,
                "project": proj_dir.name,
            }

    return None


def cmd_list(args):
    """List sessions for a date range."""
    try:
        start, end = parse_date_expr(args.date_expr)
    except ValueError as e:
        print(f"Error: {e}")
        return

    sessions = scan_sessions_for_dates(start, end, args.min_msgs, args.all_projects)

    if not sessions:
        print(f"No sessions found for '{args.date_expr}' (min {args.min_msgs} messages)")
        return

    # Print header
    date_range = f"{start}" if start == end else f"{start} to {end}"
    print(f"\nSessions for {date_range} ({len(sessions)} found):\n")
    print(f"{'Time':<18} {'Msgs':>5} {'First Message':<70} {'Session ID'}")
    print("-" * 120)

    for s in sessions:
        ts = s["first_ts"].strftime("%Y-%m-%d %H:%M")
        msg = s["first_msg"][:68]
        sid = s["session_id"][:12]
        print(f"{ts:<18} {s['msg_count']:>5} {msg:<70} {sid}")


def cmd_expand(args):
    """Expand a single session to show conversation flow."""
    result = expand_session(args.session_id, args.all_projects)
    if result is None:
        print(f"Session not found: {args.session_id}")
        return

    print(f"\n## Session: {result['session_id'][:12]}... ({result['project']})\n")

    for entry in result["entries"]:
        ts = entry["timestamp"].strftime("%H:%M:%S")
        role = "YOU" if entry["type"] == "user" else "CLAUDE"
        text = entry["text"]
        if entry["type"] == "user":
            print(f"**[{ts}] {role}:** {text}\n")
        else:
            print(f"  [{ts}] {role}: {text}\n")


def main():
    parser = argparse.ArgumentParser(description="Temporal recall for Claude Code sessions")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list command
    list_parser = subparsers.add_parser("list", help="List sessions for a date range")
    list_parser.add_argument("date_expr", help="Date expression (yesterday, last 3 days, etc.)")
    list_parser.add_argument("--min-msgs", type=int, default=3, help="Minimum messages (default: 3)")
    list_parser.add_argument("--all-projects", action="store_true", help="Scan all projects")

    # expand command
    expand_parser = subparsers.add_parser("expand", help="Show conversation flow for a session")
    expand_parser.add_argument("session_id", help="Session ID (full or prefix)")
    expand_parser.add_argument("--all-projects", action="store_true", help="Scan all projects")

    args = parser.parse_args()
    if args.command == "list":
        cmd_list(args)
    elif args.command == "expand":
        cmd_expand(args)


if __name__ == "__main__":
    main()
