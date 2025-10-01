#!/usr/bin/env python3
"""
Reference parser for Claude Code session files.

Handles:
- Tool invocation and result correlation
- Sidechain (Task) conversations
- Compact operations and logical parents
- Branch detection
- Orphan handling
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ToolInvocation:
    """Represents a tool invocation with full context."""

    tool_id: str
    tool_name: str
    message_uuid: str
    timestamp: str
    arguments: dict[str, Any] = field(default_factory=dict)
    result: Any | None = None
    result_message_uuid: str | None = None
    is_task: bool = False
    subagent_type: str | None = None


@dataclass
class Message:
    """Complete message representation with all relationships."""

    # Core identifiers
    uuid: str
    parent_uuid: str | None
    session_id: str
    timestamp: str
    type: str  # user, assistant, system, etc.

    # Message content
    content: Any
    raw_data: dict[str, Any]

    # Position tracking
    line_number: int

    # Relationship fields
    logical_parent_uuid: str | None = None
    children_uuids: list[str] = field(default_factory=list)

    # Special flags
    is_sidechain: bool = False
    is_orphan: bool = False
    is_root: bool = False

    # Tool-related fields
    tool_invocations: list[ToolInvocation] = field(default_factory=list)
    tool_results: list[tuple[str, Any]] = field(default_factory=list)  # (tool_id, result)

    # Sidechain fields
    sidechain_agent: str | None = None

    # Compact operation fields
    compact_metadata: dict[str, Any] | None = None


class ClaudeCodeParser:
    """Parser for Claude Code session files that builds a complete DAG."""

    def __init__(self):
        """Initialize the parser."""
        # Message storage
        self.messages: dict[str, Message] = {}
        self.messages_by_line: dict[int, Message] = {}

        # Relationship mappings
        self.children_by_parent: dict[str, list[str]] = defaultdict(list)

        # Root tracking
        self.roots: set[str] = set()
        self.orphans: set[str] = set()

        # Tool tracking indexed by tool_id
        self.tool_invocations: dict[str, ToolInvocation] = {}

        # Statistics
        self.stats = {
            "total_messages": 0,
            "total_tools": 0,
            "total_sidechains": 0,
            "total_orphans": 0,
        }

    def parse_file(self, file_path: Path) -> dict[str, Message]:
        """Parse a JSONL session file and return messages indexed by UUID."""
        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    msg_data = json.loads(line)
                    if "uuid" in msg_data:  # Valid message
                        self._add_message(msg_data, line_num)
                except json.JSONDecodeError as e:
                    logger.warning(f"Line {line_num}: Invalid JSON - {e}")

        # Build relationships after all messages are loaded
        self._build_relationships()

        return self.messages

    def _add_message(self, msg_data: dict[str, Any], line_number: int) -> Message:
        """Add a message to the parser."""
        # Create Message object
        msg = Message(
            uuid=msg_data["uuid"],
            parent_uuid=msg_data.get("parentUuid"),
            session_id=msg_data.get("sessionId", "unknown"),
            timestamp=msg_data.get("timestamp", ""),
            type=msg_data.get("type", "unknown"),
            content=msg_data.get("message", msg_data.get("content", "")),
            raw_data=msg_data,
            line_number=line_number,
            logical_parent_uuid=msg_data.get("logicalParentUuid"),
            is_sidechain=msg_data.get("isSidechain", False),
            compact_metadata=msg_data.get("compactMetadata"),
        )

        # Extract tool information
        self._extract_tool_info(msg)

        # Store message
        self.messages[msg.uuid] = msg
        self.messages_by_line[line_number] = msg

        # Track parent-child relationships
        if msg.parent_uuid:
            self.children_by_parent[msg.parent_uuid].append(msg.uuid)
        else:
            msg.is_root = True
            self.roots.add(msg.uuid)

        # Update statistics
        self.stats["total_messages"] += 1
        if msg.is_sidechain:
            self.stats["total_sidechains"] += 1

        return msg

    def _extract_tool_info(self, msg: Message):
        """Extract tool invocations and results from message content."""
        if not isinstance(msg.content, dict):
            return

        content = msg.content.get("content", [])
        if not isinstance(content, list):
            return

        for item in content:
            if not isinstance(item, dict):
                continue

            item_type = item.get("type")

            # Handle tool invocations
            if item_type == "tool_use":
                tool_id = item.get("id")
                tool_name = item.get("name")
                tool_input = item.get("input", {})

                # Only process if we have valid tool_id and tool_name
                if tool_id and tool_name:
                    invocation = ToolInvocation(
                        tool_id=tool_id,
                        tool_name=tool_name,
                        message_uuid=msg.uuid,
                        timestamp=msg.timestamp,
                        arguments=tool_input,
                        is_task=(tool_name == "Task"),
                        subagent_type=tool_input.get("subagent_type") if tool_name == "Task" else None,
                    )

                    msg.tool_invocations.append(invocation)
                    # Index by tool_id for result correlation
                    self.tool_invocations[tool_id] = invocation
                    self.stats["total_tools"] += 1

            # Handle tool results
            elif item_type == "tool_result":
                # Use tool_use_id to match with invocation
                tool_id = item.get("tool_use_id")
                result_content = item.get("content")

                if tool_id:
                    msg.tool_results.append((tool_id, result_content))

                    # Link result to invocation
                    if tool_id in self.tool_invocations:
                        invocation = self.tool_invocations[tool_id]
                        invocation.result = result_content
                        invocation.result_message_uuid = msg.uuid

    def _build_relationships(self):
        """Build complex relationships after loading all messages."""
        # Identify orphans
        for msg in self.messages.values():
            if msg.parent_uuid and msg.parent_uuid not in self.messages:
                msg.is_orphan = True
                self.orphans.add(msg.uuid)
                self.stats["total_orphans"] += 1

        # Identify sidechain agents
        self._identify_sidechain_agents()

        # Update children lists
        for msg in self.messages.values():
            if msg.parent_uuid and msg.parent_uuid in self.messages:
                parent = self.messages[msg.parent_uuid]
                parent.children_uuids.append(msg.uuid)

    def _identify_sidechain_agents(self):
        """Identify which agent is handling each sidechain segment.

        Pattern: Look for Task invocations before sidechain messages.
        """
        # Sort messages by line number for sequential processing
        sorted_messages = sorted(self.messages.values(), key=lambda m: m.line_number)

        for i, msg in enumerate(sorted_messages):
            if not msg.is_sidechain or msg.sidechain_agent:
                continue

            # Look backward for a Task invocation
            for j in range(i - 1, max(0, i - 10), -1):
                prev_msg = sorted_messages[j]
                for invocation in prev_msg.tool_invocations:
                    if invocation.is_task and invocation.subagent_type:
                        msg.sidechain_agent = invocation.subagent_type
                        break
                if msg.sidechain_agent:
                    break

    def get_linear_transcript(self) -> list[Message]:
        """Get messages in linear order, following active branches.

        This follows the primary conversation path, including sidechains.
        Note: All branches remain valid in the DAG; this shows the current active path.
        """
        # Simple approach: sort by line number
        # More sophisticated: follow parent-child chains from roots
        return sorted(self.messages.values(), key=lambda m: m.line_number)

    def get_statistics(self) -> dict[str, Any]:
        """Get parser statistics."""
        return self.stats.copy()


def main():
    """Example usage of the reference parser."""
    import sys

    if len(sys.argv) != 2:
        print("Usage: python reference_parser.py <session.jsonl>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    # Parse the file
    parser = ClaudeCodeParser()
    _ = parser.parse_file(file_path)

    # Print statistics
    stats = parser.get_statistics()
    print("\n📊 Session Statistics:")
    print(f"  Total messages: {stats['total_messages']}")
    print(f"  Tool invocations: {stats['total_tools']}")
    print(f"  Sidechain messages: {stats['total_sidechains']}")
    print(f"  Orphan messages: {stats['total_orphans']}")

    # Show first few messages
    print("\n📝 First 5 messages:")
    transcript = parser.get_linear_transcript()
    for msg in transcript[:5]:
        prefix = "🤖" if msg.type == "assistant" else "👤"
        tools = f" [Tools: {len(msg.tool_invocations)}]" if msg.tool_invocations else ""
        sidechain = " [SIDECHAIN]" if msg.is_sidechain else ""
        print(f"  {prefix} {msg.type}{tools}{sidechain}")

        # Show tool names if present
        for inv in msg.tool_invocations:
            print(f"      → {inv.tool_name}")


if __name__ == "__main__":
    main()
