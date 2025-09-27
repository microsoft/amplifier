#!/usr/bin/env python3
"""
Claude Code Transcripts Builder

Extracts and generates human-readable transcripts from Claude Code session logs.
Handles DAG structure, compact boundaries, and generates organized markdown output.
"""

import argparse
import contextlib
import json
import logging
import sys
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a single message in the conversation."""

    uuid: str
    parent_uuid: str | None
    logical_parent_uuid: str | None
    content: str
    type: str  # 'human' or 'assistant'
    timestamp: datetime | None = None
    line_number: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def effective_parent(self) -> str | None:
        """Returns logical parent if present, otherwise regular parent."""
        return self.logical_parent_uuid or self.parent_uuid


@dataclass
class ConversationPath:
    """Represents a path through the conversation DAG."""

    messages: list[Message]
    is_active: bool = True
    branch_point: Message | None = None
    path_id: str = "main"

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def human_messages(self) -> int:
        return sum(1 for m in self.messages if m.type == "human")

    @property
    def assistant_messages(self) -> int:
        return sum(1 for m in self.messages if m.type == "assistant")


@dataclass
class SessionData:
    """Container for all session data."""

    messages: dict[str, Message]
    root_messages: list[Message]
    paths: list[ConversationPath]
    metadata: dict = field(default_factory=dict)
    project_name: str = ""
    session_id: str = ""


class ClaudeTranscriptBuilder:
    """Main class for building transcripts from Claude Code sessions."""

    def __init__(self, claude_dir: Path, output_dir: Path):
        self.claude_dir = claude_dir
        self.output_dir = output_dir
        self.sessions_processed = 0
        self.sessions_failed = 0

    def process_all(
        self, project_filter: str | None = None, include_abandoned: bool = False, timezone_str: str = "UTC"
    ) -> None:
        """Process all Claude Code sessions."""
        logger.info(f"Scanning Claude directory: {self.claude_dir}")

        # Find all session files
        session_files = self._find_session_files(project_filter)

        if not session_files:
            logger.warning("No session files found")
            return

        logger.info(f"Found {len(session_files)} session files to process")

        # Process each session
        for session_file in session_files:
            try:
                self._process_session(session_file, include_abandoned, timezone_str)
                self.sessions_processed += 1
            except Exception as e:
                logger.error(f"Failed to process {session_file}: {e}")
                self.sessions_failed += 1

        # Generate global index
        self._generate_global_index()

        logger.info(f"Processing complete: {self.sessions_processed} succeeded, {self.sessions_failed} failed")

    def _find_session_files(self, project_filter: str | None) -> list[Path]:
        """Find all .jsonl session files in Claude projects directory."""
        session_files = []

        for project_dir in self.claude_dir.iterdir():
            if not project_dir.is_dir():
                continue

            # Apply project filter if specified
            if project_filter and project_filter not in project_dir.name:
                continue

            # Look for JSONL session files (UUID format)
            for session_file in project_dir.glob("*.jsonl"):
                session_files.append(session_file)

        return sorted(session_files)

    def _process_session(self, session_file: Path, include_abandoned: bool, timezone_str: str) -> None:
        """Process a single session file."""
        logger.info(f"Processing: {session_file}")

        # Parse session data
        session_data = self._parse_session_file(session_file)

        if not session_data.messages:
            logger.warning(f"No messages found in {session_file}")
            return

        # Extract conversation paths
        paths = self._extract_paths(session_data)
        session_data.paths = paths

        logger.info(f"  Found {len(paths)} conversation paths")

        # Generate transcripts
        self._generate_transcripts(session_data, include_abandoned, timezone_str)

    def _parse_session_file(self, session_file: Path) -> SessionData:
        """Parse a .jsonl session file and extract messages."""
        session_data = SessionData(messages={}, root_messages=[], paths=[])

        # Extract project and session info from path
        parts = session_file.parts
        for i, part in enumerate(parts):
            if part == "projects" and i + 1 < len(parts):
                session_data.project_name = parts[i + 1]

        # Session ID is the filename without extension
        session_data.session_id = session_file.stem

        # Read JSONL file line by line
        with open(session_file, encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    message = self._parse_message(data, line_num)
                    if message:
                        session_data.messages[message.uuid] = message
                        if not message.parent_uuid:
                            session_data.root_messages.append(message)
                except json.JSONDecodeError:
                    logger.debug(f"Skipping non-JSON line {line_num}")
                except Exception as e:
                    logger.warning(f"Error parsing line {line_num}: {e}")

        logger.info(f"  Parsed {len(session_data.messages)} messages")
        return session_data

    def _parse_message(self, data: dict, line_number: int) -> Message | None:
        """Parse a message from JSON data."""
        # Skip non-message entries (e.g., summary entries or meta)
        msg_type = data.get("type")
        if msg_type not in ["user", "assistant"]:
            return None

        # Extract required fields
        uuid = data.get("uuid", "")
        if not uuid:
            return None

        # Extract content from message field
        content = ""
        if "message" in data:
            msg = data["message"]
            if isinstance(msg, dict):
                msg_content = msg.get("content", "")
                if isinstance(msg_content, str):
                    content = msg_content
                elif isinstance(msg_content, list):
                    # Handle array content (tool use, etc.)
                    parts = []
                    for item in msg_content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                parts.append(item.get("text", ""))
                            elif item.get("type") == "tool_use":
                                parts.append(f"[Tool: {item.get('name', 'unknown')}]")
                        elif isinstance(item, str):
                            parts.append(item)
                    content = "\n".join(parts)

        # Map Claude Code types to our internal types
        internal_type = "human" if msg_type == "user" else "assistant"

        message = Message(
            uuid=uuid,
            parent_uuid=data.get("parentUuid"),
            logical_parent_uuid=data.get("logicalParentUuid"),
            content=content,
            type=internal_type,
            line_number=line_number,
            metadata=data,
        )

        # Parse timestamp if available
        if "timestamp" in data:
            with contextlib.suppress(ValueError, TypeError):
                timestamp_str = data["timestamp"]
                if isinstance(timestamp_str, str):
                    message.timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

        return message

    def _extract_paths(self, session_data: SessionData) -> list[ConversationPath]:
        """Extract all conversation paths from the DAG structure."""
        paths = []

        # Build children mapping for traversal
        children_map = self._build_children_map(session_data.messages)

        # Find the latest line number to determine active path
        max_line = max((m.line_number for m in session_data.messages.values()), default=0)

        # Process each root message
        for root in session_data.root_messages:
            root_paths = self._extract_paths_from_root(root, session_data.messages, children_map, max_line)
            paths.extend(root_paths)

        # Sort paths: active first, then by message count
        paths.sort(key=lambda p: (not p.is_active, -p.message_count))

        # Assign path IDs
        active_count = sum(1 for p in paths if p.is_active)
        if active_count == 1:
            for p in paths:
                if p.is_active:
                    p.path_id = "main"
                    break

        branch_num = 1
        for p in paths:
            if p.path_id == "main":
                continue
            p.path_id = f"branch{branch_num}"
            branch_num += 1

        return paths

    def _build_children_map(self, messages: dict[str, Message]) -> dict[str, list[str]]:
        """Build a mapping of parent UUID to child UUIDs."""
        children_map = {}

        for uuid, message in messages.items():
            parent = message.effective_parent
            if parent:
                if parent not in children_map:
                    children_map[parent] = []
                children_map[parent].append(uuid)

        return children_map

    def _extract_paths_from_root(
        self, root: Message, messages: dict[str, Message], children_map: dict[str, list[str]], max_line: int
    ) -> list[ConversationPath]:
        """Extract all paths starting from a root message."""
        paths = []

        def traverse(current_uuid: str, path_so_far: list[Message], branch_point: Message | None = None):
            current = messages.get(current_uuid)
            if not current:
                return

            new_path = path_so_far + [current]

            # Get children
            children = children_map.get(current_uuid, [])

            if not children:
                # Leaf node - create a path
                is_active = current.line_number == max_line
                path = ConversationPath(messages=new_path, is_active=is_active, branch_point=branch_point)
                paths.append(path)
            elif len(children) == 1:
                # Single child - continue path
                traverse(children[0], new_path, branch_point)
            else:
                # Multiple children - branching point
                for child_uuid in children:
                    traverse(child_uuid, new_path, current)

        traverse(root.uuid, [])
        return paths

    def _generate_transcripts(self, session_data: SessionData, include_abandoned: bool, timezone_str: str) -> None:
        """Generate transcript files for all paths."""
        # Create output directory structure
        output_path = self.output_dir / session_data.project_name / session_data.session_id
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate transcript for each path
        for path in session_data.paths:
            if not include_abandoned and not path.is_active:
                continue

            self._generate_transcript_file(path, session_data, output_path, timezone_str)

        # Generate metadata file
        self._generate_metadata_file(session_data, output_path)

        # Generate project index
        self._generate_project_index(session_data.project_name)

    def _generate_transcript_file(
        self, path: ConversationPath, session_data: SessionData, output_path: Path, timezone_str: str
    ) -> None:
        """Generate a transcript markdown file for a conversation path."""
        # Determine filename
        if path.is_active:
            filename = f"transcript_{path.path_id}.md"
        else:
            filename = f"transcript_{path.path_id}_abandoned.md"

        filepath = output_path / filename

        # Build transcript content
        lines = []

        # Header
        lines.append("# Claude Code Session Transcript")
        lines.append("")
        lines.append(f"**Project**: {session_data.project_name}")
        lines.append(f"**Session**: {session_data.session_id}")
        lines.append(f"**Path**: {path.path_id} ({'Active' if path.is_active else 'Abandoned'})")
        lines.append(
            f"**Messages**: {path.message_count} ({path.human_messages} human, {path.assistant_messages} assistant)"
        )

        if path.branch_point:
            lines.append(f"**Branched from**: Message at line {path.branch_point.line_number}")

        lines.append("")
        lines.append("---")
        lines.append("")

        # Messages
        prev_message = None
        for i, message in enumerate(path.messages):
            # Check for compact boundary
            if prev_message and message.logical_parent_uuid and message.logical_parent_uuid != prev_message.uuid:
                lines.append("")
                lines.append("---")
                lines.append("*[Compact boundary - conversation compacted here]*")
                lines.append("---")
                lines.append("")

            # Format timestamp
            timestamp_str = ""
            if message.timestamp:
                try:
                    # Convert to specified timezone if needed
                    if timezone_str != "UTC":
                        # For now, just use UTC
                        timestamp_str = message.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
                    else:
                        timestamp_str = message.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
                except (ValueError, AttributeError):
                    timestamp_str = ""

            # Message header
            if message.type == "human":
                lines.append(f"## Human Message {i + 1}")
            else:
                lines.append(f"## Assistant Response {i + 1}")

            if timestamp_str:
                lines.append(f"*{timestamp_str}*")

            lines.append("")

            # Message content
            lines.append(message.content)
            lines.append("")

            prev_message = message

        # Write file
        filepath.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"  Generated: {filepath.name}")

    def _generate_metadata_file(self, session_data: SessionData, output_path: Path) -> None:
        """Generate a metadata JSON file for the session."""
        metadata = {
            "project_name": session_data.project_name,
            "session_id": session_data.session_id,
            "total_messages": len(session_data.messages),
            "total_paths": len(session_data.paths),
            "active_paths": sum(1 for p in session_data.paths if p.is_active),
            "abandoned_paths": sum(1 for p in session_data.paths if not p.is_active),
            "root_messages": len(session_data.root_messages),
            "paths": [],
        }

        for path in session_data.paths:
            path_info = {
                "id": path.path_id,
                "is_active": path.is_active,
                "message_count": path.message_count,
                "human_messages": path.human_messages,
                "assistant_messages": path.assistant_messages,
            }
            metadata["paths"].append(path_info)

        filepath = output_path / "metadata.json"
        filepath.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    def _generate_project_index(self, project_name: str) -> None:
        """Generate an index file for a project."""
        project_path = self.output_dir / project_name
        if not project_path.exists():
            return

        lines = [f"# Claude Code Sessions - {project_name}", "", "## Sessions", ""]

        # List all sessions
        for session_dir in sorted(project_path.iterdir()):
            if not session_dir.is_dir():
                continue

            # Load metadata if available
            metadata_file = session_dir / "metadata.json"
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
                lines.append(f"### [{session_dir.name}]({session_dir.name}/)")
                lines.append(f"- Total messages: {metadata['total_messages']}")
                lines.append(f"- Paths: {metadata['active_paths']} active, {metadata['abandoned_paths']} abandoned")

                # List transcripts
                lines.append("- Transcripts:")
                for path in metadata["paths"]:
                    status = "active" if path["is_active"] else "abandoned"
                    filename = (
                        f"transcript_{path['id']}.md" if path["is_active"] else f"transcript_{path['id']}_abandoned.md"
                    )
                    lines.append(f"  - [{path['id']} ({status})]({session_dir.name}/{filename})")
            else:
                lines.append(f"### [{session_dir.name}]({session_dir.name}/)")

            lines.append("")

        filepath = project_path / "index.md"
        filepath.write_text("\n".join(lines), encoding="utf-8")

    def _generate_global_index(self) -> None:
        """Generate a global index file for all projects."""
        lines = ["# Claude Code Transcripts", "", "## Projects", ""]

        # List all projects
        for project_dir in sorted(self.output_dir.iterdir()):
            if not project_dir.is_dir():
                continue

            lines.append(f"- [{project_dir.name}]({project_dir.name}/index.md)")

            # Count sessions
            session_count = sum(1 for d in project_dir.iterdir() if d.is_dir())
            if session_count > 0:
                lines.append(f"  - {session_count} sessions")

        lines.append("")
        lines.append("---")
        lines.append(f"*Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}*")

        filepath = self.output_dir / "global_index.md"
        filepath.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Generated global index: {filepath}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Extract and generate transcripts from Claude Code session logs")

    parser.add_argument(
        "--claude-dir",
        type=Path,
        default=Path.home() / ".claude" / "projects",
        help="Claude projects directory (default: ~/.claude/projects)",
    )

    parser.add_argument(
        "--output", type=Path, default=Path("claude_transcripts"), help="Output directory (default: claude_transcripts)"
    )

    parser.add_argument("--project", help="Filter to specific project name")

    parser.add_argument("--include-abandoned", action="store_true", help="Include abandoned conversation branches")

    parser.add_argument("--timezone", default="UTC", help="Timezone for timestamp formatting (default: UTC)")

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate Claude directory
    if not args.claude_dir.exists():
        logger.error(f"Claude directory not found: {args.claude_dir}")
        sys.exit(1)

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Run the builder
    builder = ClaudeTranscriptBuilder(args.claude_dir, args.output)
    builder.process_all(
        project_filter=args.project, include_abandoned=args.include_abandoned, timezone_str=args.timezone
    )

    logger.info(f"Transcripts generated in: {args.output}")


if __name__ == "__main__":
    main()
