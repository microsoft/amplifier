#!/usr/bin/env python3
"""Interactive session-file graph visualization.

Usage:
    uv run python scripts/recall/session-graph.py DATE_EXPR [options]

Generates an interactive HTML graph showing sessions as nodes connected
to files they touched. Sessions colored by day, files colored by directory.

Examples:
    uv run python scripts/recall/session-graph.py "last 3 days" --no-open
    uv run python scripts/recall/session-graph.py "last week" --min-files 5 -o graph.html
"""

import json
import re
import argparse
import webbrowser
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

try:
    import networkx as nx
    from pyvis.network import Network
except ImportError:
    print("Error: networkx and pyvis required. Run: uv add networkx pyvis")
    raise SystemExit(1)

CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent.parent / "tmp" / "session-graph.html"

# Import date parsing from recall-day
import sys
sys.path.insert(0, str(Path(__file__).parent))
from recall_day import parse_date_expr, get_project_dirs, clean_content, extract_text


# Colors for days (cycling)
DAY_COLORS = [
    "#4CAF50", "#2196F3", "#FF9800", "#9C27B0",
    "#F44336", "#00BCD4", "#FFEB3B", "#795548",
]

# Colors for top-level directories
DIR_COLORS = {
    "src": "#81D4FA",
    "scripts": "#A5D6A7",
    "tests": "#FFCC80",
    "docs": "#CE93D8",
    ".claude": "#EF9A9A",
    "ai_context": "#80DEEA",
}
DEFAULT_DIR_COLOR = "#E0E0E0"


def extract_file_paths_from_session(filepath: Path) -> tuple[list[str], dict]:
    """Extract file paths from tool calls in a session JSONL file.

    Returns (file_paths, session_meta) where session_meta has first_ts, msg_count, first_msg.
    """
    file_paths = set()
    first_ts = None
    last_ts = None
    msg_count = 0
    first_msg = ""

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
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if first_ts is None:
                            first_ts = ts
                        last_ts = ts
                    except (ValueError, AttributeError):
                        pass

                msg_type = entry.get("type")

                # Count user messages
                if msg_type in ("user", "human"):
                    content = entry.get("message", {})
                    if isinstance(content, dict):
                        text = extract_text(content.get("content", ""))
                    else:
                        text = extract_text(content)
                    cleaned = clean_content(text)
                    if cleaned and len(cleaned) > 5:
                        msg_count += 1
                        if not first_msg:
                            first_msg = cleaned[:100].split("\n")[0]

                # Extract file paths from assistant tool_use entries
                if msg_type == "assistant":
                    message = entry.get("message", {})
                    content = message.get("content", []) if isinstance(message, dict) else []
                    if isinstance(content, list):
                        for block in content:
                            if not isinstance(block, dict):
                                continue
                            if block.get("type") != "tool_use":
                                continue
                            name = block.get("name", "")
                            inp = block.get("input", {})
                            if not isinstance(inp, dict):
                                continue

                            # Extract file paths from common tools
                            if name in ("Read", "Write", "Edit", "NotebookEdit"):
                                fp = inp.get("file_path") or inp.get("path", "")
                                if fp:
                                    file_paths.add(normalize_path(fp))
                            elif name in ("Glob", "Grep"):
                                fp = inp.get("path", "")
                                if fp:
                                    file_paths.add(normalize_path(fp))

    except (OSError, UnicodeDecodeError):
        pass

    meta = {
        "first_ts": first_ts,
        "last_ts": last_ts,
        "msg_count": msg_count,
        "first_msg": first_msg,
    }
    return list(file_paths), meta


def normalize_path(fp: str) -> str:
    """Normalize a file path to a relative, readable form."""
    fp = fp.replace("\\", "/")
    # Strip common prefixes
    prefixes = [
        "C:/claude/amplifier/",
        "C:\\claude\\amplifier\\",
        "/c/claude/amplifier/",
    ]
    for prefix in prefixes:
        if fp.startswith(prefix):
            fp = fp[len(prefix):]
            break
    # Also strip home dir paths
    home_prefixes = [
        str(Path.home()).replace("\\", "/") + "/",
    ]
    for prefix in home_prefixes:
        if fp.startswith(prefix):
            fp = "~/" + fp[len(prefix):]
            break
    return fp


def get_dir_color(filepath: str) -> str:
    """Get color based on top-level directory."""
    parts = filepath.split("/")
    if len(parts) > 1:
        return DIR_COLORS.get(parts[0], DEFAULT_DIR_COLOR)
    return DEFAULT_DIR_COLOR


def build_graph(
    date_expr: str, min_files: int, min_msgs: int, all_projects: bool
) -> tuple[nx.Graph, dict]:
    """Build a bipartite graph of sessions and files."""
    from datetime import date as date_type

    start, end = parse_date_expr(date_expr)
    start_dt = datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time()).replace(
        tzinfo=timezone.utc
    )

    G = nx.Graph()
    stats = {"sessions": 0, "files": 0, "edges": 0, "date_range": f"{start} to {end}"}

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

            file_paths, meta = extract_file_paths_from_session(filepath)

            if meta["first_ts"] is None:
                continue
            if meta["first_ts"] >= end_dt or (
                meta["last_ts"] and meta["last_ts"] < start_dt
            ):
                continue
            if meta["msg_count"] < min_msgs:
                continue
            if len(file_paths) < min_files:
                continue

            # Add session node
            sid = filepath.stem[:8]
            session_date = meta["first_ts"].date()
            day_idx = (session_date - start).days % len(DAY_COLORS)
            label = f"{sid}\n{meta['first_msg'][:40]}"

            G.add_node(
                f"s:{sid}",
                label=label,
                title=f"Session {filepath.stem}\n{meta['first_ts'].strftime('%Y-%m-%d %H:%M')}\n{meta['msg_count']} messages\n{meta['first_msg'][:100]}",
                color=DAY_COLORS[day_idx],
                shape="dot",
                size=max(10, min(30, meta["msg_count"])),
                group="session",
            )
            stats["sessions"] += 1

            # Add file nodes and edges
            for fp in file_paths:
                file_node = f"f:{fp}"
                if file_node not in G:
                    G.add_node(
                        file_node,
                        label=fp.split("/")[-1],
                        title=fp,
                        color=get_dir_color(fp),
                        shape="triangle",
                        size=8,
                        group="file",
                    )
                    stats["files"] += 1

                G.add_edge(f"s:{sid}", file_node)
                stats["edges"] += 1

    return G, stats


def render_graph(G: nx.Graph, output: Path) -> None:
    """Render graph to interactive HTML."""
    net = Network(height="800px", width="100%", bgcolor="#1a1a2e", font_color="white")
    net.from_nx(G)
    net.set_options(
        """{
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 100,
                "springConstant": 0.08
            },
            "solver": "forceAtlas2Based",
            "stabilization": {"iterations": 150}
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 200
        }
    }"""
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(output))


def main():
    parser = argparse.ArgumentParser(description="Session-file graph visualization")
    parser.add_argument("date_expr", help="Date expression (yesterday, last 3 days, etc.)")
    parser.add_argument("--min-files", type=int, default=2, help="Min files touched (default: 2)")
    parser.add_argument("--min-msgs", type=int, default=3, help="Min messages (default: 3)")
    parser.add_argument("--all-projects", action="store_true", help="Scan all projects")
    parser.add_argument("-o", "--output", type=str, default=None, help=f"Output path (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--no-open", action="store_true", help="Don't open in browser")
    args = parser.parse_args()

    output = Path(args.output) if args.output else DEFAULT_OUTPUT

    try:
        G, stats = build_graph(args.date_expr, args.min_files, args.min_msgs, args.all_projects)
    except ValueError as e:
        print(f"Error: {e}")
        return

    if stats["sessions"] == 0:
        print(f"No sessions found for '{args.date_expr}' with min {args.min_files} files and {args.min_msgs} messages")
        return

    render_graph(G, output)

    print(f"\nGraph generated: {output}")
    print(f"  Date range: {stats['date_range']}")
    print(f"  Sessions: {stats['sessions']}")
    print(f"  Files: {stats['files']}")
    print(f"  Edges: {stats['edges']}")

    if not args.no_open:
        webbrowser.open(str(output))


if __name__ == "__main__":
    main()
