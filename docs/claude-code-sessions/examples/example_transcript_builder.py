#!/usr/bin/env python3
"""
Example transcript builder for Claude Code sessions with auto-discovery.

This demonstrates how to project a DAG structure into a linear transcript
from real Claude Code sessions.
"""

import argparse
import json
import shutil
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path


class TranscriptBuilder:
    """Builds readable transcripts from Claude Code sessions."""

    def __init__(self):
        self.messages = []
        self.tool_map = {}  # tool_id -> invocation details

    def load_session(self, file_path: Path):
        """Load and process a session file."""
        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    msg = json.loads(line)
                    if "uuid" in msg:
                        msg["line_number"] = line_num
                        self.messages.append(msg)
                        self._extract_tools(msg)
                except json.JSONDecodeError:
                    pass  # Skip invalid lines

        # Sort by line number to get chronological order
        self.messages.sort(key=lambda m: m["line_number"])

    def _extract_tools(self, msg: dict):
        """Extract tool invocations and results from a message."""
        content = msg.get("message", {})
        if isinstance(content, dict):
            items = content.get("content", [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        if item.get("type") == "tool_use":
                            # Store tool invocation
                            self.tool_map[item.get("id")] = {
                                "name": item.get("name"),
                                "input": item.get("input", {}),
                                "message_uuid": msg["uuid"],
                            }
                        elif item.get("type") == "tool_result":
                            # Link result to invocation
                            tool_id = item.get("tool_use_id")
                            if tool_id in self.tool_map:
                                self.tool_map[tool_id]["result"] = item.get("content")

    def get_attribution(self, msg: dict) -> str:
        """Determine who sent this message based on context.

        Attribution rules:
        - Main conversation: user = Human, assistant = Claude
        - Sidechains: user = Claude (initiator), assistant = Sub-agent
        - Tool results: Always System
        """
        msg_type = msg.get("type", "unknown")
        is_sidechain = msg.get("isSidechain", False)
        user_type = msg.get("userType")

        # Check if this is a tool result
        if msg_type == "user" and "message" in msg:
            msg_content = msg.get("message", {})
            if isinstance(msg_content, dict) and "content" in msg_content:
                content = msg_content.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_result":
                            return "System"

        # Handle attribution based on context
        if msg_type == "user":
            if is_sidechain and user_type == "external":
                return "Claude"
            if user_type == "external" or user_type is None:
                return "User"
            return "System"
        if msg_type == "assistant":
            if is_sidechain:
                return "Sub-agent"
            return "Claude"
        if msg_type == "system":
            return "System"
        return msg_type.capitalize()

    def format_message(self, msg: dict) -> str:
        """Format a single message for display."""
        is_sidechain = msg.get("isSidechain", False)
        attribution = self.get_attribution(msg)

        # Build header with proper attribution
        header = f"[{msg['line_number']:4d}] {attribution}"
        if is_sidechain:
            header += " (SIDECHAIN)"

        # Extract content
        content = self._extract_content(msg)

        return f"{header}\n{content}\n"

    def _extract_content(self, msg: dict) -> str:
        """Extract displayable content from a message."""
        content = msg.get("message", msg.get("content", ""))

        if isinstance(content, str):
            # Simple string content
            return self._truncate(content, 200)

        if isinstance(content, dict):
            # Complex content with parts
            parts = []

            # Check for text content
            if "content" in content:
                items = content["content"]
                if isinstance(items, list):
                    for item in items:
                        part = self._format_content_item(item)
                        if part:
                            parts.append(part)
                elif isinstance(items, str):
                    parts.append(self._truncate(items, 200))

            return "\n".join(parts) if parts else "[No content]"

        return "[Unknown content type]"

    def _format_content_item(self, item: dict) -> str:
        """Format a single content item."""
        if not isinstance(item, dict):
            return ""

        item_type = item.get("type")

        if item_type == "text":
            text = item.get("text", "")
            return self._truncate(text, 200)

        if item_type == "tool_use":
            name = item.get("name", "unknown")
            tool_id = item.get("id", "")[:8]
            return f"  🔧 Tool: {name} [{tool_id}...]"

        if item_type == "tool_result":
            tool_id = item.get("tool_use_id", "")[:8]
            content = item.get("content", "")
            if isinstance(content, str):
                result = self._truncate(content, 100)
            else:
                result = "[Complex result]"
            return f"  ✅ Result [{tool_id}...]: {result}"

        return ""

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text to maximum length."""
        if len(text) <= max_len:
            return text
        return text[:max_len] + "..."

    def build_transcript(self, include_system: bool = False) -> str:
        """Build a complete transcript from loaded messages.

        Args:
            include_system: Whether to include system messages (tool results, etc.)
        """
        lines = []
        lines.append("=" * 60)
        lines.append("CLAUDE CODE SESSION TRANSCRIPT")
        lines.append("=" * 60)
        lines.append("")

        for msg in self.messages:
            # Skip system messages if not included
            attribution = self.get_attribution(msg)
            if not include_system and attribution == "System":
                continue

            lines.append(self.format_message(msg))

        # Add summary
        lines.append("=" * 60)
        lines.append("SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Total messages: {len(self.messages)}")
        lines.append(f"Tool invocations: {len(self.tool_map)}")

        # Count sidechains
        sidechain_count = sum(1 for m in self.messages if m.get("isSidechain"))
        if sidechain_count:
            lines.append(f"Sidechain messages: {sidechain_count}")

        return "\n".join(lines)

    def save_transcript(self, output_path: Path, include_system: bool = False):
        """Save transcript to a file."""
        transcript = self.build_transcript(include_system)
        output_path.write_text(transcript, encoding="utf-8")
        print(f"✅ Transcript saved to: {output_path}")


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
        description="Build transcripts from Claude Code session files",
        epilog="Examples:\n"
        "  %(prog)s                     # Build transcript for most recent session\n"
        "  %(prog)s --list              # List all projects and sessions\n"
        "  %(prog)s --project amplifier  # Use most recent from project\n"
        "  %(prog)s session.jsonl output.md  # Specific input/output files\n"
        "  %(prog)s --include-system    # Include system messages in transcript\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("input_file", nargs="?", help="Path to session file (optional)")

    parser.add_argument("output_file", nargs="?", help="Output transcript file (optional)")

    parser.add_argument("--project", "-p", help="Project name or directory (fuzzy match supported)")

    parser.add_argument("--list", "-l", action="store_true", help="List available projects and sessions")

    parser.add_argument("--session", "-s", help="Session UUID or filename within project")

    parser.add_argument(
        "--include-system",
        action="store_true",
        help="Include system messages (tool results) in transcript",
    )

    parser.add_argument(
        "--preview-lines",
        type=int,
        default=30,
        help="Number of preview lines to show (default: 30)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("./output"),
        help="Output directory for transcript and session files (default: ./output)",
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

            if sessions:
                print(f"     Sessions: {len(sessions)}")
                # Show most recent 2 sessions
                for session_file, mtime in sessions[:2]:
                    dt = datetime.fromtimestamp(mtime, tz=UTC)
                    size_kb = session_file.stat().st_size / 1024
                    print(f"       - {session_file.name} ({dt.strftime('%Y-%m-%d %H:%M')}, {size_kb:.1f}KB)")
                if len(sessions) > 2:
                    print(f"       ... and {len(sessions) - 2} more")
            print()
        return

    # Determine input file
    input_file = None

    if args.input_file:
        # Explicit file provided
        input_file = Path(args.input_file)
        if not input_file.exists():
            print(f"Error: File not found: {input_file}")
            sys.exit(1)

    elif args.project:
        # Find project by name
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
            sys.exit(1)

        # Find session within project
        if args.session:
            for sf in matched_project.glob("*.jsonl"):
                if args.session in sf.name:
                    input_file = sf
                    break
            if not input_file:
                print(f"Error: No session matching '{args.session}' in project")
                sys.exit(1)
        else:
            sessions = list_sessions(matched_project)
            if not sessions:
                print("Error: No sessions found in project")
                sys.exit(1)
            input_file = sessions[0][0]

    else:
        # Default: use context-aware session selection
        input_file = find_default_session(projects_dir)
        if not input_file:
            print("Error: No sessions found in any project")
            sys.exit(1)

    # Build transcript
    print(f"📄 Reading: {input_file}")
    project_dir_name = input_file.parent.name  # e.g., "-home-user-repos-amplifier"
    project_name = project_dir_name[1:].replace("-", "/") if project_dir_name.startswith("-") else project_dir_name
    print(f"📂 Project: {project_name}")

    file_size = input_file.stat().st_size
    print(f"📏 Size: {file_size:,} bytes")

    builder = TranscriptBuilder()
    builder.load_session(input_file)

    # Determine output location
    if args.output_file:
        # Legacy: explicit output file provided
        output_file = Path(args.output_file)
        builder.save_transcript(output_file, include_system=args.include_system)
    else:
        # New structure: save to organized directory
        session_id = input_file.stem  # UUID part before .jsonl
        output_dir = args.output / project_dir_name / session_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save transcript as .md
        output_file = output_dir / "transcript.md"
        builder.save_transcript(output_file, include_system=args.include_system)

        # Copy source JSONL
        session_copy = output_dir / "session.jsonl"
        shutil.copy2(input_file, session_copy)
        print(f"✅ Session copied to: {session_copy}")

    # Show preview
    print(f"\n📄 Preview (first {args.preview_lines} lines):")
    print("-" * 40)
    transcript = builder.build_transcript(args.include_system)
    preview_lines = transcript.split("\n")[: args.preview_lines]
    for line in preview_lines:
        print(line)
    print("-" * 40)
    line_count = len(transcript.split("\n"))
    print(f"... [{line_count} total lines]")


if __name__ == "__main__":
    main()
