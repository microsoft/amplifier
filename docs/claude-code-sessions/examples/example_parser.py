#!/usr/bin/env python3
"""
Simple example parser for Claude Code sessions with auto-discovery.

This demonstrates parsing Claude Code JSONL files from real sessions,
with automatic discovery of projects and sessions.
"""

import argparse
import json
import shutil
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path


class SimpleParser:
    """Minimal parser for Claude Code sessions."""

    def __init__(self):
        self.messages = {}  # uuid -> message dict
        self.parent_child = {}  # parent_uuid -> [child_uuids]
        self.roots = []  # messages with no parent

    def parse_file(self, file_path: Path) -> dict:
        """Parse a JSONL file and build basic DAG structure."""
        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    msg = json.loads(line)
                    if "uuid" not in msg:
                        continue

                    # Store message
                    msg["line_number"] = line_num
                    self.messages[msg["uuid"]] = msg

                    # Track parent-child relationships
                    parent = msg.get("parentUuid")
                    if parent:
                        if parent not in self.parent_child:
                            self.parent_child[parent] = []
                        self.parent_child[parent].append(msg["uuid"])
                    else:
                        self.roots.append(msg["uuid"])

                except json.JSONDecodeError:
                    print(f"Warning: Invalid JSON at line {line_num}")

        return self.messages

    def get_conversation_flow(self) -> list:
        """Get messages in conversation order (simple linear view)."""
        # Sort by line number for simple linear flow
        return sorted(self.messages.values(), key=lambda m: m["line_number"])

    def find_tools(self) -> dict:
        """Extract all tool invocations from messages."""
        tools = {}

        for msg in self.messages.values():
            content = msg.get("message", {})
            if isinstance(content, dict):
                items = content.get("content", [])
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and item.get("type") == "tool_use":
                            tool_id = item.get("id")
                            tools[tool_id] = {
                                "name": item.get("name"),
                                "message_uuid": msg["uuid"],
                                "arguments": item.get("input", {}),
                            }

        return tools

    def print_summary(self):
        """Print basic summary of the session."""
        print("\n📊 Session Summary:")
        print(f"  Total messages: {len(self.messages)}")
        print(f"  Root messages: {len(self.roots)}")
        print(f"  Parent-child relationships: {len(self.parent_child)}")

        # Count message types
        types = {}
        for msg in self.messages.values():
            msg_type = msg.get("type", "unknown")
            types[msg_type] = types.get(msg_type, 0) + 1

        print("\n📝 Message Types:")
        for msg_type, count in types.items():
            print(f"  {msg_type}: {count}")

        # Find tools
        tools = self.find_tools()
        if tools:
            print(f"\n🔧 Tools Used: {len(tools)}")
            tool_names = {}
            for tool in tools.values():
                name = tool["name"]
                tool_names[name] = tool_names.get(name, 0) + 1
            for name, count in tool_names.items():
                print(f"  {name}: {count}")

    def get_summary_text(self) -> str:
        """Get summary as text for saving to file."""
        lines = []
        lines.append("# Session Analysis\n")
        lines.append("## Session Summary")
        lines.append(f"- Total messages: {len(self.messages)}")
        lines.append(f"- Root messages: {len(self.roots)}")
        lines.append(f"- Parent-child relationships: {len(self.parent_child)}")
        lines.append("")

        # Count message types
        types = {}
        for msg in self.messages.values():
            msg_type = msg.get("type", "unknown")
            types[msg_type] = types.get(msg_type, 0) + 1

        lines.append("## Message Types")
        for msg_type, count in types.items():
            lines.append(f"- {msg_type}: {count}")
        lines.append("")

        # Find tools
        tools = self.find_tools()
        if tools:
            lines.append(f"## Tools Used ({len(tools)} total invocations)")
            tool_names = {}
            for tool in tools.values():
                name = tool["name"]
                tool_names[name] = tool_names.get(name, 0) + 1
            for name, count in tool_names.items():
                lines.append(f"- {name}: {count}")
            lines.append("")

        # Add message flow
        flow = self.get_conversation_flow()
        if flow:
            lines.append("## Message Flow (First 10 messages)")
            for msg in flow[:10]:
                msg_type = msg.get("type", "unknown")
                lines.append(f"- [{msg['line_number']:4d}] {msg_type}: {msg['uuid'][:8]}...")
            if len(flow) > 10:
                lines.append(f"- ... and {len(flow) - 10} more messages")
            lines.append("")

        return "\n".join(lines)


def find_claude_projects_dir():
    """Find the Claude Code projects directory."""
    claude_dir = Path.home() / ".claude" / "projects"
    if not claude_dir.exists():
        return None
    return claude_dir


def list_projects(projects_dir: Path):
    """List all available projects."""
    projects = []
    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir() and project_dir.name.startswith("-"):
            # Extract readable project name
            project_name = project_dir.name[1:].replace("-", "/")
            projects.append((project_dir.name, project_name))
    return sorted(projects, key=lambda x: x[1])


def list_sessions(project_dir: Path):
    """List all sessions in a project with their modification times."""
    sessions = []
    for session_file in project_dir.glob("*.jsonl"):
        mtime = session_file.stat().st_mtime
        sessions.append((session_file, mtime))
    return sorted(sessions, key=lambda x: x[1], reverse=True)


def find_default_session(projects_dir: Path):
    """Find the default session using context-aware selection.

    First tries to find a session from the current working directory's project.
    Falls back to the most recent session across all projects if no match.
    """
    import os

    # Get current working directory
    cwd = os.getcwd()

    # Convert CWD to Claude Code project directory format
    # Replace / with - and add leading -
    # Also replace dots with - as Claude Code does
    cwd_encoded = cwd.replace("/", "-").replace(".", "-")
    if not cwd_encoded.startswith("-"):
        cwd_encoded = "-" + cwd_encoded

    # Try to find the best matching project
    best_match = None
    best_match_score = 0

    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir() and project_dir.name.startswith("-") and cwd_encoded.startswith(project_dir.name):
            # Check if the encoded CWD starts with this project directory name
            # This handles both exact matches and parent directories
            # Score based on the length of the match (longer = more specific)
            score = len(project_dir.name)
            if score > best_match_score:
                best_match = project_dir
                best_match_score = score

    # If we found a matching project, use its most recent session
    if best_match:
        sessions = list_sessions(best_match)
        if sessions:
            session_file = sessions[0][0]  # Most recent session
            # Try to reconstruct the path for display (may not be perfect due to ambiguity)
            display_path = best_match.name[1:].replace("-", "/")
            if not display_path.startswith("/"):
                display_path = "/" + display_path
            print(f"📍 Using session from current project directory: {display_path}")
            return session_file

    # Fallback: find most recent session across all projects
    most_recent = None
    most_recent_time = 0

    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir():
            for session_file in project_dir.glob("*.jsonl"):
                mtime = session_file.stat().st_mtime
                if mtime > most_recent_time:
                    most_recent = session_file
                    most_recent_time = mtime

    return most_recent


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Parse Claude Code session files",
        epilog="Examples:\n"
        "  %(prog)s                    # Parse most recent session\n"
        "  %(prog)s --list             # List all projects and sessions\n"
        "  %(prog)s --project amplifier # Parse most recent from project\n"
        "  %(prog)s session.jsonl      # Parse specific file\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("session_file", nargs="?", help="Path to specific session file (optional)")

    parser.add_argument("--project", "-p", help="Project name or directory (fuzzy match supported)")

    parser.add_argument("--list", "-l", action="store_true", help="List available projects and sessions")

    parser.add_argument("--session", "-s", help="Session UUID or filename within project")

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("./output"),
        help="Output directory for analysis results (default: ./output)",
    )

    args = parser.parse_args()

    # Find Claude projects directory
    projects_dir = find_claude_projects_dir()
    if not projects_dir:
        print("Error: Claude Code projects directory not found at ~/.claude/projects")
        sys.exit(1)

    # Handle --list flag
    if args.list:
        print("📁 Available Claude Code Projects:\n")
        projects = list_projects(projects_dir)

        if not projects:
            print("No projects found")
            return

        for dir_name, readable_name in projects:
            project_path = projects_dir / dir_name
            sessions = list_sessions(project_path)
            print(f"  📂 {readable_name}")
            print(f"     Directory: {dir_name}")

            if sessions:
                print(f"     Sessions: {len(sessions)}")
                # Show most recent 3 sessions
                for session_file, mtime in sessions[:3]:
                    dt = datetime.fromtimestamp(mtime, tz=UTC)
                    print(f"       - {session_file.name} ({dt.strftime('%Y-%m-%d %H:%M')})")
                if len(sessions) > 3:
                    print(f"       ... and {len(sessions) - 3} more")
            else:
                print("     No sessions")
            print()
        return

    # Determine which session file to parse
    session_file = None

    if args.session_file:
        # Explicit file provided
        session_file = Path(args.session_file)
        if not session_file.exists():
            print(f"Error: File not found: {session_file}")
            sys.exit(1)

    elif args.project:
        # Find project by name (fuzzy match)
        project_query = args.project.lower()
        matched_project = None

        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir():
                project_name = project_dir.name.lower()
                if project_query in project_name:
                    matched_project = project_dir
                    break

        if not matched_project:
            print(f"Error: No project found matching '{args.project}'")
            print("\nAvailable projects:")
            for _, readable in list_projects(projects_dir)[:10]:
                print(f"  - {readable}")
            sys.exit(1)

        # Find session within project
        if args.session:
            # Specific session requested
            for sf in matched_project.glob("*.jsonl"):
                if args.session in sf.name:
                    session_file = sf
                    break

            if not session_file:
                print(f"Error: No session matching '{args.session}' in project")
                sessions = list_sessions(matched_project)
                if sessions:
                    print("\nAvailable sessions:")
                    for sf, _ in sessions[:5]:
                        print(f"  - {sf.name}")
                sys.exit(1)
        else:
            # Use most recent session from project
            sessions = list_sessions(matched_project)
            if not sessions:
                print(f"Error: No sessions found in project {matched_project.name}")
                sys.exit(1)
            session_file = sessions[0][0]

    else:
        # Default: use context-aware session selection
        session_file = find_default_session(projects_dir)
        if not session_file:
            print("Error: No sessions found in any project")
            sys.exit(1)

    # Parse and analyze the session
    print(f"📄 Parsing: {session_file}")
    project_dir_name = session_file.parent.name  # e.g., "-home-user-repos-amplifier"
    project_name = project_dir_name[1:].replace("-", "/") if project_dir_name.startswith("-") else project_dir_name
    print(f"📂 Project: {project_name}")

    file_size = session_file.stat().st_size
    print(f"📏 Size: {file_size:,} bytes")

    mtime = session_file.stat().st_mtime
    dt = datetime.fromtimestamp(mtime, tz=UTC)
    print(f"🕐 Modified: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

    # Parse and analyze
    parser = SimpleParser()
    parser.parse_file(session_file)
    parser.print_summary()

    # Show first few messages
    flow = parser.get_conversation_flow()
    if flow:
        print("\n💬 First 5 messages:")
        for msg in flow[:5]:
            msg_type = msg.get("type", "unknown")
            print(f"  [{msg['line_number']:4d}] {msg_type}: {msg['uuid'][:8]}...")

        if len(flow) > 5:
            print(f"  ... and {len(flow) - 5} more messages")

    # Save analysis to output directory
    session_id = session_file.stem  # UUID part before .jsonl
    output_dir = args.output / project_dir_name / session_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save analysis
    analysis_file = output_dir / "analysis.md"
    analysis_content = "# Claude Code Session Analysis\n\n"
    analysis_content += f"**File:** {session_file}\n"
    analysis_content += f"**Project:** {project_name}\n"
    analysis_content += f"**Size:** {file_size:,} bytes\n"
    analysis_content += f"**Modified:** {dt.strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
    analysis_content += parser.get_summary_text()

    analysis_file.write_text(analysis_content, encoding="utf-8")

    # Copy source JSONL
    session_copy = output_dir / "session.jsonl"
    shutil.copy2(session_file, session_copy)

    print(f"\n✅ Analysis saved to: {analysis_file}")
    print(f"✅ Session copied to: {session_copy}")


if __name__ == "__main__":
    main()
