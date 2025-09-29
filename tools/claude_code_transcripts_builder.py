#!/usr/bin/env python3
"""
Tool: Claude Code Transcripts Builder
Purpose: Parse Claude Code session files and generate organized markdown transcripts

Contract:
  Inputs: Claude Code project directory containing JSONL session files
  Outputs: Organized session directories with transcripts, manifests, and separated sidechains
  Failures: Clear errors for corrupt JSONL, missing files, or invalid DAG structures

Philosophy:
  - Ruthless simplicity: Direct DAG parsing without unnecessary abstractions
  - Fail fast and loud: Clear errors for corrupt data
  - Progress visibility: Show what's being processed
  - Defensive by default: Handle file I/O edge cases with retries

Architecture (Codex-inspired):
  output_dir/
  ├── 2025-01-27-10-15-am__repos~amplifier__abc123/
  │   ├── manifest.json                    # Session metadata
  │   ├── history.jsonl                    # Original session data
  │   ├── transcript.md                    # Main path simplified
  │   ├── transcript_extended.md           # Main path with details
  │   ├── branches/                        # Alternate paths
  │   │   ├── branch_001_transcript.md
  │   │   └── branch_001_extended.md
  │   └── sidechains/                      # Sub-agent conversations
  │       └── sidechain_001_bug-hunter.md
"""

import json
import logging
import re
import shutil
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

import click

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Default timezone
TIMEZONE_DEFAULT = "America/Los_Angeles"


def write_with_retry(content: str, filepath: Path, max_retries: int = 3, initial_delay: float = 0.5) -> None:
    """Write text file with retry logic for cloud sync issues."""
    import time

    retry_delay = initial_delay
    for attempt in range(max_retries):
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
            return
        except OSError as e:
            if e.errno == 5 and attempt < max_retries - 1:
                if attempt == 0:
                    logger.warning(
                        f"File I/O error writing to {filepath} - retrying. This may be due to cloud-synced files."
                    )
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise


# ============================================================================
# DATA MODELS (Simple, clear structures)
# ============================================================================


@dataclass
class Message:
    """A single message in the conversation."""

    uuid: str
    parent_uuid: str | None
    session_id: str
    timestamp: str
    msg_type: str  # 'user' or 'assistant' or 'system'
    content: Any
    line_number: int  # For abandoned branch detection
    logical_parent_uuid: str | None = None  # For compact boundaries

    # Enhanced fields for complete support
    subtype: str | None = None  # tool_use, thinking, response, command, compact_boundary
    is_sidechain: bool = False  # True for sub-agent conversations
    user_type: str | None = None  # 'external' when Claude is the user
    tool_name: str | None = None  # Name of tool being used
    tool_arguments: dict | None = None  # Arguments passed to tool
    tool_result: Any = None  # Result from tool execution
    is_meta: bool = False  # Meta messages (system info, etc)
    is_error: bool = False  # Error messages
    is_deleted: bool = False  # Deleted messages
    compact_metadata: dict[str, Any] | None = None  # Compact operation details
    sidechain_agent: str | None = None  # Name of sub-agent in sidechain


@dataclass
class ConversationPath:
    """A complete conversation path from root to leaf."""

    messages: list[Message]
    session_id: str
    path_id: int
    is_abandoned: bool = False
    fork_point_uuid: str | None = None
    has_compact: bool = False
    sidechain_count: int = 0  # Number of sidechain segments
    sidechain_messages: int = 0  # Total messages in sidechains


# ============================================================================
# SESSION PARSER (Parse JSONL files into message DAG)
# ============================================================================


class SessionParser:
    """Parse Claude Code session JSONL files."""

    def __init__(self):
        """Initialize parser."""
        self.all_messages: list[Message] = []  # All messages from all files
        self.message_by_uuid: dict[str, Message] = {}  # Global UUID index
        self.messages_by_session: dict[str, list[Message]] = defaultdict(list)  # Messages per session
        self.task_calls: list[dict] = []  # All Task tool calls with results
        self.sidechain_agent_map: dict[str, str] = {}  # Map session IDs to agent names
        self.session_file_map: dict[str, Path] = {}  # Map session IDs to source files
        self.tool_id_to_name: dict[str, str] = {}  # Maps tool IDs to tool names (across all messages)
        self.tool_id_to_info: dict[str, dict] = {}  # Maps tool IDs to tool info (across all messages)

    def parse_all_files(self, session_files: list[Path]) -> None:
        """Parse all JSONL files into a unified message pool."""
        logger.info(f"Loading {len(session_files)} session files into unified message pool...")

        for session_file in session_files:
            self._parse_single_file(session_file)

        logger.info(f"  Loaded {len(self.all_messages)} total messages")
        logger.info(f"  Found {len(self.task_calls)} Task tool calls")

    def _parse_single_file(self, session_file: Path) -> None:
        """Parse a single JSONL file and add to unified pool."""
        if not session_file.exists():
            logger.warning(f"Session file not found: {session_file}")
            return

        file_line_offset = len(self.all_messages)  # Offset for global line numbers

        with open(session_file, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON at line {line_num} in {session_file.name}: {e}")
                    continue

                # Skip non-message entries but keep meta for completeness
                if "uuid" not in data:
                    continue

                # Extract message content and tool info
                # System messages have content directly, not in a 'message' field
                if data.get("type") == "system":
                    content = data.get("content", "")
                    msg_content = content
                else:
                    msg_content = data.get("message", {})

                tool_name = None
                tool_arguments = None
                tool_result = None
                sidechain_agent = None

                if isinstance(msg_content, dict):
                    # Handle both message formats:
                    # 1. Assistant messages: {"id": "...", "content": [...]}
                    # 2. User messages with tool results: {"role": "user", "content": [...]}
                    content = msg_content.get("content", "")

                    # First pass: collect all tool_use items and build ID mapping
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "tool_use":
                                tool_id = item.get("id")
                                tool_name_item = item.get("name")
                                if tool_id and tool_name_item:
                                    self.tool_id_to_name[tool_id] = tool_name_item
                                    self.tool_id_to_info[tool_id] = {
                                        "name": tool_name_item,
                                        "arguments": item.get("input", {}),
                                    }

                                    # Handle Task tool specifically
                                    if tool_name_item == "Task":
                                        tool_args = item.get("input", {})
                                        task_info_item = {
                                            "timestamp": data.get("timestamp", ""),
                                            "session_id": data.get("sessionId", ""),
                                            "subagent_type": tool_args.get("subagent_type", "unknown"),
                                            "prompt": tool_args.get("prompt", "")[:100]
                                            if tool_args.get("prompt")
                                            else "",
                                            "uuid": data["uuid"],
                                            "source_file": session_file.name,
                                            "spawned_session_id": None,  # Will be filled from result
                                        }
                                        self.tool_id_to_info[tool_id]["task_info"] = task_info_item
                                        self.task_calls.append(task_info_item)

                        # Second pass: process content and correlate tool results
                        for item in content:
                            if isinstance(item, dict):
                                if item.get("type") == "tool_use":
                                    # Set tool_name for this specific tool use
                                    tool_name = item.get("name")
                                    tool_arguments = item.get("input", {})
                                    # Track Task tool invocations and map for sidechain labeling
                                    if tool_name == "Task" and "subagent_type" in tool_arguments:
                                        sidechain_agent = tool_arguments["subagent_type"]
                                elif item.get("type") == "tool_result":
                                    # Correlate tool result to tool name via ID
                                    tool_use_id = item.get("tool_use_id")
                                    if tool_use_id and tool_use_id in self.tool_id_to_name:
                                        # Found the correct tool name via ID correlation
                                        result_tool_name = self.tool_id_to_name[tool_use_id]
                                        tool_result = item.get("content")

                                        # Debug: log structure of tool results
                                        if result_tool_name == "Task" and line_num <= 10:  # Log first few
                                            logger.debug(
                                                f"DEBUG: Task tool_result structure: type={type(tool_result)}, len={len(str(tool_result)) if tool_result else 0}"
                                            )
                                        # If this is a Task result, extract the spawned session ID
                                        if result_tool_name == "Task" and tool_use_id in self.tool_id_to_info:
                                            task_info_for_result = self.tool_id_to_info[tool_use_id].get("task_info")
                                            if task_info_for_result and isinstance(tool_result, str):
                                                # Look for session ID pattern in the result
                                                session_pattern = r"session[_\s]?id[:\s]+([a-f0-9\-]+)"
                                                match = re.search(session_pattern, tool_result, re.IGNORECASE)
                                                if match:
                                                    task_info_for_result["spawned_session_id"] = match.group(1)

                                        # Set the tool_name to the correctly correlated name for the result
                                        # This ensures the Message object gets the right tool_name for results
                                        if not tool_name:  # Only set if we haven't set a tool_name yet
                                            tool_name = result_tool_name
                                    else:
                                        # No ID correlation found, keep tool_result but no tool_name
                                        tool_result = item.get("content")
                elif isinstance(msg_content, str):
                    content = msg_content
                else:
                    content = str(data.get("content", ""))

                # Create message object with enhanced fields
                msg = Message(
                    uuid=data["uuid"],
                    parent_uuid=data.get("parentUuid"),
                    session_id=data.get("sessionId", "unknown"),
                    timestamp=data.get("timestamp", ""),
                    msg_type=data.get("type", "unknown"),
                    content=content,
                    line_number=file_line_offset + line_num,  # Global line number
                    logical_parent_uuid=data.get("logicalParentUuid"),
                    subtype=data.get("subtype"),
                    is_sidechain=data.get("isSidechain", False),
                    user_type=data.get("userType"),
                    tool_name=tool_name,
                    tool_arguments=tool_arguments,
                    tool_result=tool_result,
                    is_meta=data.get("isMeta", False),
                    is_error=data.get("isError", False),
                    is_deleted=data.get("isDeleted", False),
                    compact_metadata=data.get("compactMetadata"),
                    sidechain_agent=sidechain_agent,
                )

                # Add to unified pool
                self.all_messages.append(msg)
                self.message_by_uuid[msg.uuid] = msg
                self.messages_by_session[msg.session_id].append(msg)

                # Track session to file mapping
                if msg.session_id not in self.session_file_map:
                    self.session_file_map[msg.session_id] = session_file


# ============================================================================
# UNIFIED DAG BUILDER (Build global message graph across all sessions)
# ============================================================================


class UnifiedMessageDAG:
    """Build and navigate unified message DAG structure across all sessions."""

    def __init__(self, parser: SessionParser):
        """Initialize DAG from unified message pool."""
        self.messages = parser.all_messages
        self.message_by_uuid = parser.message_by_uuid
        self.messages_by_session = parser.messages_by_session
        self.task_calls = parser.task_calls
        self.sidechain_agent_map = parser.sidechain_agent_map
        self.session_file_map = parser.session_file_map

        self.children_map: dict[str, list[str]] = defaultdict(list)
        self.roots: list[Message] = []
        self.sidechain_roots: list[Message] = []  # Separate tracking for sidechain roots

        # Match sidechains to parent tasks
        self._match_sidechains_to_tasks()

        # Build the unified DAG
        self._build_dag()

    def _match_sidechains_to_tasks(self) -> None:
        """Match sidechain sessions to their parent Task calls using temporal ordering.

        Sidechains appear immediately after Task tool calls in the message flow.
        We track Task calls and match them with subsequent sidechain segments.
        """
        logger.debug("Starting sidechain matching...")

        # First, collect all sidechain segments with their starting line numbers
        sidechain_segments = []

        for session_id, messages in self.messages_by_session.items():
            current_segment = []
            in_sidechain = False
            sidechain_count_in_session = 0
            segment_start_line = None

            for msg in messages:
                # Use the is_sidechain flag from the JSONL data
                if msg.is_sidechain and not in_sidechain:
                    # Start of new sidechain segment
                    in_sidechain = True
                    current_segment = [msg]
                    segment_start_line = msg.line_number
                    sidechain_count_in_session += 1
                elif msg.is_sidechain and in_sidechain:
                    # Continue current sidechain
                    current_segment.append(msg)
                elif not msg.is_sidechain and in_sidechain:
                    # End of sidechain - save the segment
                    if current_segment:
                        sidechain_segments.append(
                            {
                                "messages": current_segment,
                                "session_id": session_id,
                                "start_line": segment_start_line,
                            }
                        )
                    in_sidechain = False
                    current_segment = []
                    segment_start_line = None

            # Handle unclosed sidechain at end
            if current_segment:
                sidechain_segments.append(
                    {
                        "messages": current_segment,
                        "session_id": session_id,
                        "start_line": segment_start_line,
                    }
                )

            if sidechain_count_in_session > 0:
                logger.debug(f"  Session {session_id[:8]}: Found {sidechain_count_in_session} sidechain segments")

        logger.debug(f"Total sidechain segments found: {len(sidechain_segments)}")

        # Build a list of Task calls with their line numbers
        task_calls = []

        for msg in self.messages:
            # Check if this message contains a Task tool_use
            if msg.msg_type == "assistant" and isinstance(msg.content, list):
                for item in msg.content:
                    if isinstance(item, dict) and item.get("type") == "tool_use" and item.get("name") == "Task":
                        tool_arguments = item.get("input", {})
                        task_info = {
                            "uuid": msg.uuid,
                            "subagent_type": tool_arguments.get("subagent_type", "unknown"),
                            "session_id": msg.session_id,
                            "line_number": msg.line_number,
                        }
                        task_calls.append(task_info)
                        logger.debug(
                            f"  Found Task call: subagent_type={task_info['subagent_type']}, line={msg.line_number}"
                        )
                        break

        logger.debug(f"Found {len(task_calls)} Task calls")

        # Match each sidechain segment to the most recent Task call before it
        matched_count = 0
        unmatched_count = 0

        # Sort Task calls by line number for efficient searching
        task_calls_sorted = sorted(task_calls, key=lambda t: t["line_number"])

        for segment_idx, segment in enumerate(sidechain_segments):
            logger.debug(f"Processing sidechain segment {segment_idx + 1}/{len(sidechain_segments)}")
            logger.debug(f"  Session: {segment['session_id'][:8]}, Start line: {segment['start_line']}")

            # Find the most recent Task call before this sidechain
            matched_task = None
            for task in reversed(task_calls_sorted):
                if task["line_number"] < segment["start_line"]:
                    # This task came before the sidechain
                    matched_task = task
                    logger.debug(f"  Matched to Task {task['subagent_type']} at line {task['line_number']}")
                    break

            if matched_task:
                agent_type = matched_task["subagent_type"]
                matched_count += 1

                # Apply agent type to all messages in this segment
                for msg in segment["messages"]:
                    msg.sidechain_agent = agent_type
            else:
                unmatched_count += 1
                logger.warning(f"  No Task call found before sidechain at line {segment['start_line']}")

        logger.info(f"Matched {matched_count}/{len(sidechain_segments)} sidechains to their parent agents")

    def _is_sidechain_start(self, msg: Message) -> bool:
        """Check if a message starts a sidechain conversation."""
        if msg.msg_type != "user":
            return False

        content_str = str(msg.content)[:500] if msg.content else ""

        # Strong indicators of sidechain start
        sidechain_patterns = [
            "You are evaluating",
            "You are analyzing",
            "You are reviewing",
            "You are implementing",
            "You are a specialized",
            "You are an expert",
            "Your task is to",
            "Your role is to",
            "Analyze the following",
            "Review the following",
            "Debug and fix",
            "Create comprehensive",
            "Update the following",
            "Design a comprehensive",
        ]

        return any(pattern in content_str for pattern in sidechain_patterns)

    def _is_sidechain_end(self, msg: Message) -> bool:
        """Check if a message indicates end of sidechain (back to main conversation)."""
        # A user message without sidechain patterns likely means back to main
        if msg.msg_type == "user":
            return not self._is_sidechain_start(msg)
        return False

    def _detect_sidechain_session(self, messages: list[Message]) -> bool:
        """Detect if a session is a sidechain based on patterns."""
        # Check if session has Task calls (parent sessions have them, sidechains don't)
        has_task_calls = any(msg.tool_name == "Task" for msg in messages)
        if has_task_calls:
            return False

        # Check first user message for sidechain patterns
        for msg in messages:
            if msg.msg_type == "user" and msg.content:
                content_str = str(msg.content)[:500]  # Check first 500 chars

                sidechain_patterns = [
                    "You are evaluating",
                    "You are analyzing",
                    "You are reviewing",
                    "You are implementing",
                    "You are a ",
                    "Your task is",
                    "Your role is",
                    "Analyze the following",
                    "Review the following",
                    "Debug and fix",
                ]

                for pattern in sidechain_patterns:
                    if pattern in content_str:
                        return True
                break  # Only check first user message

        return False

    def _build_dag(self) -> None:
        """Build parent-child relationships and find roots across all sessions."""
        # First, build the children map from all messages
        for msg in self.messages:
            if msg.parent_uuid:
                self.children_map[msg.parent_uuid].append(msg.uuid)

        # Find roots: messages without parents OR with non-existent parents in ANY session
        # This is key: a message is only a root if its parent doesn't exist ANYWHERE
        for msg in self.messages:
            is_root = False

            if not msg.parent_uuid:
                # No parent - this is a root
                is_root = True
            elif msg.parent_uuid not in self.message_by_uuid:
                # Parent doesn't exist in the unified pool - treat as orphaned root
                # This handles true conversation starts that reference messages from outside our dataset
                is_root = True

            if is_root:
                if msg.is_sidechain:
                    # Sidechain root - track separately
                    self.sidechain_roots.append(msg)
                else:
                    # Main conversation root
                    self.roots.append(msg)

        # Connect compact boundaries to their logical parents for continuity
        for msg in self.messages:
            if (
                msg.logical_parent_uuid
                and msg.logical_parent_uuid in self.message_by_uuid
                and msg.uuid not in self.children_map[msg.logical_parent_uuid]
            ):
                # Add as child of logical parent for path continuity across compacts
                self.children_map[msg.logical_parent_uuid].append(msg.uuid)

        logger.info(f"  Built unified DAG: {len(self.roots)} main roots, {len(self.sidechain_roots)} sidechain roots")

    def _find_leaves(self) -> list[Message]:
        """Find all leaf nodes (messages with no children) in the main conversation."""
        leaves = []
        for msg in self.messages:
            # Skip sidechain messages when finding main conversation leaves
            if msg.is_sidechain:
                continue

            # A message is a leaf if it has no children OR all its children are sidechains
            if msg.uuid not in self.children_map:
                # No children at all
                leaves.append(msg)
            else:
                # Check if all children are sidechains
                children_uuids = self.children_map[msg.uuid]
                all_sidechain = all(
                    self.message_by_uuid[child_uuid].is_sidechain
                    for child_uuid in children_uuids
                    if child_uuid in self.message_by_uuid
                )
                if all_sidechain:
                    # All children are sidechains, so this is effectively a leaf for the main conversation
                    leaves.append(msg)

        return leaves

    def _trace_backward_to_root(self, leaf: Message) -> list[Message]:
        """Trace backwards from a leaf to the absolute beginning of the conversation.

        This method ensures we capture the COMPLETE history from the very first message,
        not just from an orphaned message that appears to be a root in this session.
        """
        path = []
        current = leaf
        visited = set()  # Prevent cycles

        while current:
            if current.uuid in visited:
                logger.warning(f"Cycle detected at message {current.uuid}, breaking")
                break

            visited.add(current.uuid)
            path.append(current)

            # Try to find parent
            parent_uuid = current.parent_uuid

            # If no parent UUID, check for logical parent (compact boundaries)
            if not parent_uuid and current.logical_parent_uuid:
                parent_uuid = current.logical_parent_uuid
                logger.debug(f"Using logical parent for compact boundary: {parent_uuid}")

            if not parent_uuid:
                # No parent at all - we've reached the absolute beginning
                logger.debug(f"Reached absolute root at {current.uuid}")
                break

            # Try to find the parent message
            parent = self.message_by_uuid.get(parent_uuid)

            if not parent:
                # Parent doesn't exist in this session
                # Try logical parent if we haven't already
                if current.logical_parent_uuid and current.logical_parent_uuid != parent_uuid:
                    parent = self.message_by_uuid.get(current.logical_parent_uuid)
                    if parent:
                        logger.debug(f"Found parent via logical parent: {current.logical_parent_uuid}")

                if not parent:
                    # Parent truly doesn't exist - this is as far back as we can go
                    logger.debug(f"Parent {parent_uuid} not found in session, stopping trace")
                    break

            # Move to parent
            current = parent

        # Reverse to get chronological order (root to leaf)
        return list(reversed(path))

    def extract_all_paths(self) -> list[ConversationPath]:
        """Extract all unique conversation paths using root-forward approach on unified DAG.

        Since we have the complete message graph across all sessions, we can now traverse
        from true roots forward, capturing complete conversation lineages.
        """
        all_paths = []
        path_id = 0

        # Use root-forward traversal since we have the complete graph
        logger.info(f"  Tracing paths from {len(self.roots)} root messages...")

        for root in self.roots:
            # Trace all paths from this root forward
            paths_from_root = self._trace_all_paths_from(root.uuid)

            for path_uuids in paths_from_root:
                path_messages = [self.message_by_uuid[uuid] for uuid in path_uuids]

                # Skip empty paths
                if not path_messages:
                    continue

                # Count path characteristics
                path_id += 1
                has_compact = any(msg.subtype == "compact_boundary" for msg in path_messages)

                # Use the most common session_id in the path
                session_ids = [msg.session_id for msg in path_messages]
                from collections import Counter

                session_id = Counter(session_ids).most_common(1)[0][0] if session_ids else "unknown"

                # Count sidechain segments and messages
                sidechain_count = 0
                sidechain_messages = 0
                in_sidechain = False
                for msg in path_messages:
                    if msg.is_sidechain and not in_sidechain:
                        sidechain_count += 1
                        in_sidechain = True
                    elif not msg.is_sidechain and in_sidechain:
                        in_sidechain = False

                    if msg.is_sidechain:
                        sidechain_messages += 1

                path = ConversationPath(
                    messages=path_messages,
                    session_id=session_id,
                    path_id=path_id,
                    has_compact=has_compact,
                    sidechain_count=sidechain_count,
                    sidechain_messages=sidechain_messages,
                )
                all_paths.append(path)

        # Eliminate subset paths (paths that are entirely contained in other paths)
        all_paths = self._eliminate_subset_paths(all_paths)

        # Mark abandoned branches based on fork points
        self._mark_abandoned_branches(all_paths)

        logger.info(f"  Extracted {len(all_paths)} unique conversation paths")
        return all_paths

    def _trace_all_paths_from(self, root_uuid: str, visited: set[str] | None = None) -> list[list[str]]:
        """Recursively trace all paths from a root to all leaves."""
        if visited is None:
            visited = set()

        # Detect cycles
        if root_uuid in visited:
            logger.warning(f"Cycle detected at {root_uuid[:8]}, breaking")
            return []

        visited = visited | {root_uuid}

        children = self.children_map.get(root_uuid, [])

        if not children:
            # Leaf node - return single path ending here
            return [[root_uuid]]

        # Get all paths from children
        all_paths = []
        for child_uuid in children:
            child_paths = self._trace_all_paths_from(child_uuid, visited)
            for path in child_paths:
                all_paths.append([root_uuid] + path)

        return all_paths

    def _eliminate_subset_paths(self, paths: list[ConversationPath]) -> list[ConversationPath]:
        """Eliminate paths that are subsets of other paths."""
        unique_paths = []

        # Sort by message count (descending) to prefer longer paths
        sorted_paths = sorted(paths, key=lambda p: len(p.messages), reverse=True)

        for candidate in sorted_paths:
            candidate_uuids = {msg.uuid for msg in candidate.messages}

            # Check if this path is a subset of any already selected path
            is_subset = False
            for selected in unique_paths:
                selected_uuids = {msg.uuid for msg in selected.messages}
                if candidate_uuids.issubset(selected_uuids) and candidate_uuids != selected_uuids:
                    is_subset = True
                    break

            if not is_subset:
                unique_paths.append(candidate)

        removed = len(paths) - len(unique_paths)
        if removed > 0:
            logger.info(f"    Removed {removed} subset paths")

        return unique_paths

    def extract_sidechain_paths(self) -> list[tuple[str, list[Message]]]:
        """Extract sidechain conversation paths."""
        sidechains = []

        for root in self.sidechain_roots:
            # Trace the sidechain conversation from its root
            paths = self._trace_paths_from(root.uuid)
            for path_messages in paths:
                # Determine agent name from the messages or session ID map
                agent_name = "unknown"

                # First try to get from sidechain_agent field
                for msg in path_messages:
                    if msg.sidechain_agent:
                        agent_name = msg.sidechain_agent
                        break

                # If still unknown, try session ID mapping
                if agent_name == "unknown" and path_messages:
                    session_id = path_messages[0].session_id
                    if session_id in self.sidechain_agent_map:
                        agent_name = self.sidechain_agent_map[session_id]

                sidechains.append((agent_name, path_messages))

        return sidechains

    def _trace_paths_from(self, node_uuid: str) -> list[list[Message]]:
        """Recursively trace all paths from a node to leaves."""
        node = self.message_by_uuid[node_uuid]
        children_uuids = self.children_map.get(node_uuid, [])

        if not children_uuids:
            # Leaf node - return path ending here
            return [[node]]

        # Get all paths from children
        all_paths = []
        for child_uuid in children_uuids:
            child_paths = self._trace_paths_from(child_uuid)
            for path in child_paths:
                all_paths.append([node] + path)

        return all_paths

    def _mark_abandoned_branches(self, paths: list[ConversationPath]) -> None:
        """Mark paths as abandoned based on fork points."""
        # Group paths by their fork points
        fork_groups: dict[str, list[ConversationPath]] = defaultdict(list)

        for path in paths:
            # Find fork points (messages with multiple children)
            for i, msg in enumerate(path.messages[:-1]):
                children = self.children_map.get(msg.uuid, [])
                if len(children) > 1:
                    # This is a fork point
                    next_msg = path.messages[i + 1]
                    fork_key = f"{msg.uuid}:{next_msg.uuid}"
                    fork_groups[fork_key].append(path)
                    path.fork_point_uuid = msg.uuid
                    break

        # Within each fork group, earlier branches (by line number) are abandoned
        for _fork_key, group_paths in fork_groups.items():
            if len(group_paths) > 1:
                # Sort by line number of first message after fork
                fork_uuid = group_paths[0].fork_point_uuid
                if fork_uuid:
                    fork_idx = next(i for i, msg in enumerate(group_paths[0].messages) if msg.uuid == fork_uuid)
                    sorted_paths = sorted(group_paths, key=lambda p: p.messages[fork_idx + 1].line_number)
                    # Mark all but the last as abandoned
                    for path in sorted_paths[:-1]:
                        path.is_abandoned = True


# ============================================================================
# TRANSCRIPT GENERATOR (Convert paths to markdown)
# ============================================================================


class TranscriptGenerator:
    """Generate organized markdown transcripts from conversation paths."""

    def __init__(self, output_dir: Path, session_file: Path | None = None):
        """Initialize generator with output directory."""
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = session_file

    def generate_session_output(
        self, paths: list[ConversationPath], session_file: Path | None, dag: UnifiedMessageDAG | None = None
    ) -> Path:
        """Generate complete organized output for a session with all paths."""
        if not paths:
            return self.output_dir

        # Create session directory with timestamp__cwd__id naming
        first_msg_timestamp = None
        for path in paths:
            for msg in path.messages:
                if msg.timestamp:
                    first_msg_timestamp = msg.timestamp
                    break
            if first_msg_timestamp:
                break

        # Parse timestamp for directory name with timezone conversion
        if first_msg_timestamp:
            try:
                dt = datetime.fromisoformat(first_msg_timestamp.replace("Z", "+00:00"))
                tz = ZoneInfo(TIMEZONE_DEFAULT)
                local_dt = dt.astimezone(tz)
                timestamp_str = local_dt.strftime("%Y-%m-%d-%I-%M-%p").lower()
            except Exception:
                timestamp_str = "unknown-time"
        else:
            timestamp_str = "unknown-time"

        # Extract project context from session file path
        project_name = session_file.parent.name if session_file else "unknown"
        # Clean project name (replace problematic chars)
        project_name = project_name.replace("/", "~").replace("-", "~")

        session_id = paths[0].session_id[:8] if paths[0].session_id else "unknown"
        session_dir_name = f"{timestamp_str}__{project_name}__{session_id}"
        session_dir = self.output_dir / session_dir_name
        session_dir.mkdir(parents=True, exist_ok=True)

        # Copy original JSONL as history.jsonl
        if session_file and session_file.exists():
            history_file = session_dir / "history.jsonl"
            shutil.copy2(session_file, history_file)
            logger.info("  Copied original session to history.jsonl")

        # Identify main path (longest active path)
        active_paths = [p for p in paths if not p.is_abandoned]
        main_path = max(active_paths, key=lambda p: len(p.messages)) if active_paths else paths[0]

        # Generate main transcripts
        self._generate_main_transcripts(main_path, session_dir)

        # Generate branch transcripts
        branch_paths = [p for p in paths if p != main_path and not p.is_abandoned]
        if branch_paths:
            branches_dir = session_dir / "branches"
            branches_dir.mkdir(exist_ok=True)
            for idx, branch_path in enumerate(branch_paths, 1):
                self._generate_branch_transcripts(branch_path, branches_dir, idx)

        # Extract and generate sidechain transcripts from DAG
        sidechains = []
        if dag:
            sidechains = dag.extract_sidechain_paths()

        if sidechains:
            sidechains_dir = session_dir / "sidechains"
            sidechains_dir.mkdir(exist_ok=True)
            for idx, (agent_name, sidechain_msgs) in enumerate(sidechains, 1):
                self._generate_sidechain_transcript(sidechain_msgs, sidechains_dir, idx, agent_name)

            # Update main path stats
            main_path.sidechain_count = len(sidechains)
            main_path.sidechain_messages = sum(len(msgs) for _, msgs in sidechains)

        # Generate manifest.json
        manifest = self._generate_manifest(paths, session_dir, timestamp_str)
        manifest_file = session_dir / "manifest.json"
        write_with_retry(json.dumps(manifest, indent=2), manifest_file)
        logger.info("  Generated manifest.json")

        return session_dir

    def _generate_main_transcripts(self, path: ConversationPath, session_dir: Path) -> None:
        """Generate both simplified and extended transcripts for main path."""
        # Generate simplified transcript
        simplified_content = self._format_transcript(path, simplified=True, is_main=True)
        write_with_retry(simplified_content, session_dir / "transcript.md")
        logger.info("  Generated transcript.md (simplified)")

        # Generate extended transcript
        extended_content = self._format_transcript(path, simplified=False, is_main=True)
        write_with_retry(extended_content, session_dir / "transcript_extended.md")
        logger.info("  Generated transcript_extended.md (with details)")

    def _generate_branch_transcripts(self, path: ConversationPath, branches_dir: Path, idx: int) -> None:
        """Generate transcripts for a branch."""
        # Generate simplified branch transcript
        simplified_content = self._format_transcript(path, simplified=True, is_main=False, branch_id=idx)
        write_with_retry(simplified_content, branches_dir / f"branch_{idx:03d}_transcript.md")

        # Generate extended branch transcript
        extended_content = self._format_transcript(path, simplified=False, is_main=False, branch_id=idx)
        write_with_retry(extended_content, branches_dir / f"branch_{idx:03d}_extended.md")
        logger.info(f"  Generated branch {idx:03d} transcripts")

    def _extract_sidechains(self, path: ConversationPath) -> list[tuple[str, list[Message]]]:
        """Extract sidechain conversations from path."""
        sidechains = []
        current_sidechain = []
        current_agent = None

        for msg in path.messages:
            if msg.is_sidechain:
                if not current_agent and msg.sidechain_agent:
                    current_agent = msg.sidechain_agent
                current_sidechain.append(msg)
            elif current_sidechain:
                # End of sidechain
                sidechains.append((current_agent or "unknown", current_sidechain))
                current_sidechain = []
                current_agent = None

        # Handle final sidechain if exists
        if current_sidechain:
            sidechains.append((current_agent or "unknown", current_sidechain))

        return sidechains

    def _generate_sidechain_transcript(
        self, messages: list[Message], sidechains_dir: Path, idx: int, agent_name: str
    ) -> None:
        """Generate transcript for a sidechain conversation."""
        lines = []
        lines.append(f"# Sidechain {idx:03d}: {agent_name}\n")
        lines.append(f"Agent: {agent_name}")
        lines.append(f"Messages: {len(messages)}")
        lines.append("---\n")

        for msg in messages:
            # Format sidechain message
            if msg.msg_type == "user":
                lines.append("## 🤖→ CLAUDE (as user)")
            else:
                lines.append(f"## 🧠 {agent_name.upper()}")

            # Add timestamp in codex format
            if msg.timestamp:
                try:
                    dt = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00"))
                    tz = ZoneInfo(TIMEZONE_DEFAULT)
                    local_dt = dt.astimezone(tz)
                    lines.append(f"*{local_dt.strftime('%Y-%m-%d %I:%M %p %Z')}*\n")
                except Exception:
                    pass

            # Add content (simplified)
            content = self._format_content(msg, simplified=True)
            lines.append(content)
            lines.append("\n---\n")

        filename = f"sidechain_{idx:03d}_{agent_name.lower().replace(' ', '_')}.md"
        write_with_retry("\n".join(lines), sidechains_dir / filename)
        logger.info(f"  Generated sidechain {idx:03d} ({agent_name})")

    def _generate_manifest(self, paths: list[ConversationPath], session_dir: Path, timestamp_str: str) -> dict:
        """Generate manifest with session metadata."""
        # Count statistics
        total_messages = sum(len(p.messages) for p in paths)
        active_branches = len([p for p in paths if not p.is_abandoned])
        abandoned_branches = len([p for p in paths if p.is_abandoned])

        # Collect sidechain stats
        total_sidechains = sum(p.sidechain_count for p in paths)
        total_sidechain_msgs = sum(p.sidechain_messages for p in paths)

        # List generated files
        files = []
        if (session_dir / "transcript.md").exists():
            files.append("transcript.md")
        if (session_dir / "transcript_extended.md").exists():
            files.append("transcript_extended.md")
        if (session_dir / "history.jsonl").exists():
            files.append("history.jsonl")

        branches_dir = session_dir / "branches"
        if branches_dir.exists():
            files.extend([f"branches/{f.name}" for f in branches_dir.glob("*.md")])

        sidechains_dir = session_dir / "sidechains"
        if sidechains_dir.exists():
            files.extend([f"sidechains/{f.name}" for f in sidechains_dir.glob("*.md")])

        manifest = {
            "session_id": paths[0].session_id if paths else "unknown",
            "timestamp": timestamp_str,
            "project": session_dir.parent.name,
            "statistics": {
                "total_messages": total_messages,
                "branches": {"active": active_branches, "abandoned": abandoned_branches, "total": len(paths)},
                "sidechains": {"count": total_sidechains, "messages": total_sidechain_msgs},
            },
            "files": sorted(files),
            "generated_at": datetime.now().isoformat(),
        }

        return manifest

    def _format_transcript(
        self, path: ConversationPath, simplified: bool = False, is_main: bool = True, branch_id: int | None = None
    ) -> str:
        """Format a conversation path as markdown."""
        lines = []

        # Header
        if is_main:
            lines.append("# Claude Code Session Transcript\n")
            if simplified:
                lines.append("*Simplified view - tool details hidden*\n")
            else:
                lines.append("*Extended view - includes full tool payloads*\n")
        else:
            lines.append(f"# Branch {branch_id:03d} Transcript\n")

        lines.append(f"Session ID: {path.session_id}")
        lines.append(f"Status: {'ABANDONED' if path.is_abandoned else 'ACTIVE'}")

        if path.fork_point_uuid:
            lines.append(f"Fork Point: {path.fork_point_uuid}")

        if path.has_compact:
            lines.append("**Contains Compact Operation(s)**")

        if path.sidechain_count > 0 and not simplified:
            lines.append(f"**Sidechains**: {path.sidechain_count} conversations ({path.sidechain_messages} messages)")

        lines.append(f"Total Messages: {len(path.messages)}")
        lines.append(f"Generated: {datetime.now().isoformat()}\n")
        lines.append("---\n")

        # Add messages (skip sidechains in simplified main transcript)
        for msg in path.messages:
            # Skip deleted messages, meta messages, and sidechains in simplified view
            if msg.is_deleted or msg.is_meta:
                continue
            if simplified and msg.is_sidechain:
                # Add a marker for sidechain in simplified view
                if msg.sidechain_agent and not any(
                    "→ Sidechain:" in line and msg.sidechain_agent in line for line in lines[-5:]
                ):
                    lines.append(f"\n→ *Sidechain: Conversation with {msg.sidechain_agent} (see sidechains folder)*\n")
                continue

            # Handle compact boundaries with enhanced formatting
            if msg.subtype == "compact_boundary":
                lines.append("\n")
                lines.append("═" * 50)
                lines.append("📦 CONVERSATION COMPACTED")
                if msg.compact_metadata:
                    lines.append(f"- Trigger: {msg.compact_metadata.get('trigger', 'unknown')}")
                    lines.append(f"- Pre-compact tokens: {msg.compact_metadata.get('preTokens', 'unknown')}")
                    preserved = msg.compact_metadata.get("preservedMessageCount", "unknown")
                    lines.append(f"- Preserved messages: {preserved}")
                lines.append(f"- Logical parent: {msg.logical_parent_uuid}")
                lines.append("═" * 50)
                lines.append("")
                continue

            # Format message with codex-style headers
            role_label = self._get_codex_role_label(msg)

            # Add timestamp in codex format
            if msg.timestamp:
                try:
                    dt = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00"))
                    tz = ZoneInfo(TIMEZONE_DEFAULT)
                    local_dt = dt.astimezone(tz)
                    time_str = local_dt.strftime("%Y-%m-%d %I:%M %p %Z")
                except Exception:
                    time_str = msg.timestamp
            else:
                time_str = "unknown time"

            # Format header in codex style
            # Always use role_label which handles tool results correctly
            if msg.tool_name and msg.tool_result is None:
                # Special case for tool calls (not results)
                lines.append(f"\n- **Tool Call** · {time_str}")
            else:
                # Use role_label for everything else (includes tool results with names)
                lines.append(f"\n- **{role_label}** · {time_str}")

            # Format content with indentation (codex style)
            content_str = self._format_content(msg, simplified)
            # Indent content lines
            indented_lines = []
            for line in content_str.split("\n"):
                if line:  # Only indent non-empty lines
                    indented_lines.append(f"  {line}")
                else:
                    indented_lines.append("")  # Keep empty lines
            lines.append("\n".join(indented_lines))
            lines.append("")  # Empty line after content

        return "\n".join(lines)

    def _get_role_info(self, msg: Message) -> tuple[str, str]:
        """Get role emoji and label for a message."""
        if msg.is_sidechain:
            if msg.msg_type == "user":
                return "🤖→👤", "CLAUDE (as user)"
            return "🧠", msg.sidechain_agent.upper() if msg.sidechain_agent else "SUB-AGENT"
        if msg.msg_type == "user":
            return "👤", "USER"
        if msg.msg_type == "system":
            return "⚙️", "SYSTEM"
        return "🤖", "ASSISTANT"

    def _get_codex_role_label(self, msg: Message) -> str:
        """Get codex-style role label for a message with correct attribution."""
        # System-generated messages
        if msg.subtype == "compact_boundary" or msg.compact_metadata:
            return "System [Compact]"

        if msg.is_meta:
            return "System [Metadata]"

        if msg.is_error:
            return "System [Error]"

        if msg.tool_result is not None:
            tool_name = msg.tool_name or "unknown"
            return f"Tool Result [{tool_name}]"

        # Sidechain messages
        if msg.is_sidechain:
            if msg.msg_type == "user":
                return "Claude [as user]"
            agent_name = msg.sidechain_agent if msg.sidechain_agent else "sub-agent"
            return f"Agent [{agent_name}]"

        # Regular messages
        if msg.msg_type == "user":
            # Verify this is actually from a human user
            if msg.user_type == "external":
                return "User [external]"
            return "User"

        if msg.msg_type == "assistant":
            return "Assistant"

        if msg.msg_type == "system":
            return "System"

        return "Assistant"

    def _format_content(self, msg: Message, simplified: bool = False) -> str:
        """Format message content based on type and simplification level."""
        lines = []
        content = msg.content

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get("type")

                    if item_type == "text":
                        text = item.get("text", "")
                        lines.append(text)

                    elif item_type == "tool_use":
                        tool_name = item.get("name", "unknown")
                        tool_input = item.get("input", {})

                        if simplified:
                            # Simplified tool display with user-friendly formatting
                            if tool_name == "Write":
                                if "file_path" in tool_input:
                                    lines.append(f"\n📝 **Writing file**: `{tool_input['file_path']}`")
                                else:
                                    lines.append("\n📝 **Tool: Write**")
                            elif tool_name == "Edit" or tool_name == "MultiEdit":
                                if "file_path" in tool_input:
                                    lines.append(f"\n✏️ **Editing file**: `{tool_input['file_path']}`")
                                else:
                                    lines.append(f"\n✏️ **Tool: {tool_name}**")
                            elif tool_name == "Read":
                                if "file_path" in tool_input:
                                    fp = tool_input["file_path"]
                                    limit = tool_input.get("limit")
                                    offset = tool_input.get("offset")
                                    if limit or offset:
                                        range_str = []
                                        if offset:
                                            range_str.append(f"from line {offset}")
                                        if limit:
                                            range_str.append(f"{limit} lines")
                                        lines.append(f"\n📖 **Reading**: `{fp}` ({', '.join(range_str)})")
                                    else:
                                        lines.append(f"\n📖 **Reading file**: `{fp}`")
                                else:
                                    lines.append("\n📖 **Tool: Read**")
                            elif tool_name == "Bash":
                                lines.append("\n💻 **Running command**")
                                if "command" in tool_input:
                                    cmd = tool_input["command"]
                                    desc = tool_input.get("description", "")
                                    if desc:
                                        lines.append(f"  {desc}")
                                    if len(cmd) > 80 or "\n" in cmd:
                                        if len(cmd) > 100:
                                            cmd = cmd[:100] + "..."
                                        lines.append(f"```bash\n{cmd}\n```")
                                    else:
                                        lines.append(f"  `$ {cmd}`")
                            elif tool_name == "Task":
                                agent = tool_input.get("subagent_type", tool_input.get("agent", "unknown"))
                                desc = tool_input.get("description", "")
                                if desc:
                                    lines.append(f"\n🤖 **Delegating to {agent}**: {desc}")
                                else:
                                    lines.append(f"\n🤖 **Calling agent**: {agent}")
                            elif tool_name == "Grep":
                                pattern = tool_input.get("pattern", "")
                                path = tool_input.get("path", ".")
                                lines.append(f"\n🔍 **Searching for**: `{pattern}` in `{path}`")
                            elif tool_name == "TodoWrite":
                                todos = tool_input.get("todos", [])
                                lines.append(f"\n📋 **Updating todo list** ({len(todos)} items)")
                            elif tool_name == "WebFetch" or tool_name == "WebSearch":
                                if tool_name == "WebFetch":
                                    url = tool_input.get("url", "")
                                    lines.append(f"\n🌐 **Fetching**: {url}")
                                else:
                                    query = tool_input.get("query", "")
                                    lines.append(f"\n🔎 **Web search**: {query}")
                            else:
                                # Generic tool with emoji
                                lines.append(f"\n🔧 **Tool: {tool_name}**")
                        else:
                            # Full tool display
                            lines.append(f"\n### 🔧 TOOL: {tool_name}")
                            lines.append("```json")
                            lines.append(json.dumps(tool_input, indent=2))
                            lines.append("```")

                    elif item_type == "tool_result":
                        result = item.get("content", "")
                        if simplified and isinstance(result, str) and len(result) > 100:
                            lines.append(f"```\n{result[:100]}...\n[Truncated {len(result)} chars]\n```")
                        elif isinstance(result, str) and len(result) > 500 and not simplified:
                            lines.append(f"```\n{result[:500]}...\n[Output truncated - {len(result)} chars total]\n```")
                        else:
                            lines.append(f"```\n{result}\n```")

                    elif item_type == "thinking":
                        # Extract thinking content from 'thinking' field, not 'text'
                        thinking_content = item.get("thinking", "")
                        if thinking_content:  # Only add if there's content
                            # Show full thinking content in both modes (user requested this)
                            lines.append("\n💭 **Thinking:**")
                            for think_line in thinking_content.split("\n"):
                                lines.append("> " + think_line)

                    else:
                        lines.append(str(item))
                else:
                    lines.append(str(item))
        else:
            # Simple text content - clean ANSI codes for system messages
            content_str = str(content)
            # Remove ANSI escape sequences
            content_str = re.sub(r"\x1b\[[0-9;]*m", "", content_str)
            lines.append(content_str)

        return "\n".join(lines)


# ============================================================================
# DEDUPLICATOR (Remove duplicate conversation paths across sessions)
# ============================================================================


class PathDeduplicator:
    """Deduplicate conversation paths across multiple sessions."""

    def deduplicate(self, all_paths: list[ConversationPath]) -> list[ConversationPath]:
        """Remove paths that are subsets of other paths."""
        unique_paths = []

        # Sort by message count (descending) to prefer longer paths
        sorted_paths = sorted(all_paths, key=lambda p: len(p.messages), reverse=True)

        for candidate in sorted_paths:
            candidate_uuids = {msg.uuid for msg in candidate.messages}

            # Check if this path is a subset of any already selected path
            is_subset = False
            for selected in unique_paths:
                selected_uuids = {msg.uuid for msg in selected.messages}
                if candidate_uuids.issubset(selected_uuids):
                    is_subset = True
                    break

            if not is_subset:
                unique_paths.append(candidate)

        removed = len(all_paths) - len(unique_paths)
        if removed > 0:
            logger.info(f"  Removed {removed} duplicate paths")

        return unique_paths


# ============================================================================
# MAIN ORCHESTRATOR (CLI and coordination)
# ============================================================================


@click.command()
@click.argument(
    "project_dir",
    type=click.Path(exists=True, path_type=Path),
    required=False,
)
@click.option(
    "--project-name",
    help="Project name to search for in ~/.claude/projects/",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=Path("claude_transcripts"),
    help="Output directory for transcripts",
)
@click.option(
    "--include-abandoned",
    is_flag=True,
    default=True,
    help="Include abandoned conversation branches",
)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def main(
    project_dir: Path | None,
    project_name: str | None,
    output: Path,
    include_abandoned: bool,
    verbose: bool,
):
    """Claude Code Transcripts Builder - Extract all conversation paths from session files.

    This tool parses Claude Code session JSONL files and generates markdown transcripts
    for each conversation path, including branches created by "redo" operations and
    compact boundaries.

    Usage:
        # Process a specific project directory
        claude_code_transcripts_builder ~/.claude/projects/my-project

        # Search for project by name
        claude_code_transcripts_builder --project-name my-project

        # Process current directory's Claude project
        claude_code_transcripts_builder
    """
    if verbose:
        logger.setLevel("DEBUG")

    # Determine project directory
    if project_dir:
        session_dir = project_dir
    elif project_name:
        # Search for project in default location
        claude_dir = Path.home() / ".claude" / "projects"
        matching = list(claude_dir.glob(f"*{project_name}*"))
        if not matching:
            logger.error(f"No project found matching: {project_name}")
            sys.exit(1)
        if len(matching) > 1:
            logger.error(f"Multiple projects found matching '{project_name}':")
            for p in matching:
                logger.error(f"  - {p.name}")
            sys.exit(1)
        session_dir = matching[0]
    else:
        # Try to find project for current directory
        # Claude Code converts paths like /home/user/project to -home-user-project
        # and also converts dots to hyphens
        cwd_path = Path.cwd().resolve()
        claude_project_name = str(cwd_path).replace("/", "-").replace(".", "-")

        claude_dir = Path.home() / ".claude" / "projects"
        session_dir = claude_dir / claude_project_name

        if not session_dir.exists():
            # Fallback: try partial match with just the directory name
            cwd_name = Path.cwd().name
            matching = list(claude_dir.glob(f"*{cwd_name}*"))
            if not matching:
                logger.error("No Claude project found for current directory")
                logger.error(f"  Looked for: {claude_project_name}")
                logger.error(f"  Also tried partial match: *{cwd_name}*")
                logger.error("Use --project-name or provide explicit path")
                sys.exit(1)
            session_dir = matching[0]

    logger.info(f"Processing project: {session_dir.name}")

    # Find all JSONL session files
    session_files = sorted(session_dir.glob("*.jsonl"))
    if not session_files:
        logger.error(f"No JSONL files found in: {session_dir}")
        sys.exit(1)

    logger.info(f"Found {len(session_files)} session files")

    # Build unified message pool from ALL session files
    parser = SessionParser()
    parser.parse_all_files(session_files)

    if not parser.all_messages:
        logger.error("No messages found in any session files")
        sys.exit(1)

    # Build unified DAG across all sessions
    logger.info("Building unified message graph across all sessions...")
    unified_dag = UnifiedMessageDAG(parser)

    # Extract all unique conversation paths from the unified graph
    all_paths = unified_dag.extract_all_paths()

    if not all_paths:
        logger.error("No conversation paths found")
        sys.exit(1)

    # No need for separate deduplication since UnifiedMessageDAG already handles it
    unique_paths = all_paths

    # Filter abandoned if requested
    if not include_abandoned:
        unique_paths = [p for p in unique_paths if not p.is_abandoned]
        logger.info(f"Filtered to {len(unique_paths)} active paths")

    # Group paths by session for output organization
    paths_by_session = defaultdict(list)

    for path in unique_paths:
        session_id = path.session_id
        paths_by_session[session_id].append(path)

    # Use the session file map from the parser
    session_file_map = parser.session_file_map

    # Generate organized output for each session
    logger.info(f"Generating organized output for {len(paths_by_session)} sessions...")
    generator = TranscriptGenerator(output)

    generated_dirs = []
    for session_id, session_paths in paths_by_session.items():
        session_file = session_file_map.get(session_id)
        # Use the unified DAG for all sessions
        if session_file:
            session_dir = generator.generate_session_output(session_paths, session_file, unified_dag)
            generated_dirs.append(session_dir)
        else:
            # If we couldn't find the session file, create a fallback
            logger.warning(f"Could not find session file for session {session_id}, using first available")
            session_dir = generator.generate_session_output(
                session_paths, session_files[0] if session_files else None, unified_dag
            )
            generated_dirs.append(session_dir)

    logger.info(f"✅ Successfully generated transcripts for {len(paths_by_session)} sessions")
    logger.info(f"📁 Output directory: {output.absolute()}")

    # Summary statistics
    compact_paths = sum(1 for p in unique_paths if p.has_compact)
    abandoned_paths = sum(1 for p in unique_paths if p.is_abandoned)
    sidechain_paths = sum(1 for p in unique_paths if p.sidechain_count > 0)
    total_sidechains = sum(p.sidechain_count for p in unique_paths)
    total_sidechain_msgs = sum(p.sidechain_messages for p in unique_paths)

    logger.info("\nSummary:")
    logger.info(f"  - Total paths: {len(unique_paths)}")
    logger.info(f"  - Active paths: {len(unique_paths) - abandoned_paths}")
    logger.info(f"  - Abandoned paths: {abandoned_paths}")
    logger.info(f"  - Paths with compacts: {compact_paths}")
    logger.info(f"  - Paths with sidechains: {sidechain_paths}")
    logger.info(f"  - Total sidechains: {total_sidechains}")
    logger.info(f"  - Total sidechain messages: {total_sidechain_msgs}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
