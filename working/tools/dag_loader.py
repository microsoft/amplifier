#!/usr/bin/env python3
"""
DAG Loader Module - Load and validate Claude Code session JSONL data.

This module is responsible for loading session files and building the DAG structure.
It handles various message types and ensures data integrity.
"""

import contextlib
import json
import logging
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from subagent_mapper import SubagentMapper

logger = logging.getLogger(__name__)


class SessionType(str, Enum):
    """Type of session."""

    REGULAR = "regular"
    MODERN_SIDECHAIN = "modern_sidechain"
    LEGACY_SUBAGENT = "legacy_subagent"


@dataclass
class Message:
    """Represents a single message in the conversation DAG."""

    uuid: str
    type: str  # user, assistant, system
    parent_uuid: str | None
    content: Any  # Can be string, dict, or list
    timestamp: datetime | None = None
    line_number: int = 0
    is_sidechain: bool = False
    user_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_root(self) -> bool:
        """Check if this message is a root (no parent)."""
        return self.parent_uuid is None

    def is_tool_result(self) -> bool:
        """Check if this message contains tool results."""
        if not isinstance(self.content, dict):
            return False

        items = self.content.get("content", [])
        if not isinstance(items, list):
            return False

        return any(isinstance(item, dict) and item.get("type") == "tool_result" for item in items)

    def is_tool_use(self) -> bool:
        """Check if this message contains tool invocations."""
        if not isinstance(self.content, dict):
            return False

        items = self.content.get("content", [])
        if not isinstance(items, list):
            return False

        return any(isinstance(item, dict) and item.get("type") == "tool_use" for item in items)

    def get_tool_calls(self) -> list[dict[str, Any]]:
        """Extract tool calls from this message."""
        tools = []
        if not isinstance(self.content, dict):
            return tools

        items = self.content.get("content", [])
        if not isinstance(items, list):
            return tools

        for item in items:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                tools.append({"id": item.get("id"), "name": item.get("name"), "input": item.get("input", {})})
        return tools

    def get_tool_results(self) -> list[dict[str, Any]]:
        """Extract tool results from this message."""
        results = []
        if not isinstance(self.content, dict):
            return results

        items = self.content.get("content", [])
        if not isinstance(items, list):
            return results

        for item in items:
            if isinstance(item, dict) and item.get("type") == "tool_result":
                results.append({"tool_use_id": item.get("tool_use_id"), "content": item.get("content")})
        return results


@dataclass
class SessionData:
    """Contains all data from a Claude Code session."""

    messages: dict[str, Message] = field(default_factory=dict)
    parent_child_map: dict[str, list[str]] = field(default_factory=dict)
    root_messages: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    # NEW FIELDS
    session_type: SessionType = SessionType.REGULAR
    subagent_name: str | None = None
    session_id: str | None = None

    def get_message(self, uuid: str) -> Message | None:
        """Get a message by UUID."""
        return self.messages.get(uuid)

    def get_children(self, uuid: str) -> list[str]:
        """Get child UUIDs for a message."""
        return self.parent_child_map.get(uuid, [])

    def get_roots(self) -> list[str]:
        """Get all root message UUIDs."""
        return self.root_messages

    def count_messages(self) -> int:
        """Total number of messages."""
        return len(self.messages)

    def count_branches(self) -> int:
        """Count number of branches (messages with multiple children)."""
        return sum(1 for children in self.parent_child_map.values() if len(children) > 1)

    def has_sidechains(self) -> bool:
        """Check if session contains sidechains."""
        return any(msg.is_sidechain for msg in self.messages.values())


class DAGLoader:
    """Loads Claude Code session JSONL files and builds DAG structure."""

    def __init__(self, subagent_mapper: SubagentMapper | None = None):
        """Initialize DAGLoader with optional subagent mapper."""
        self.session_data = SessionData()
        self.error_count = 0
        self.warning_count = 0
        self.subagent_mapper = subagent_mapper

    def load_file(self, file_path: Path) -> SessionData:
        """Load a JSONL session file and build DAG structure.

        Args:
            file_path: Path to the JSONL file

        Returns:
            SessionData containing the loaded DAG

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty or invalid
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Session file not found: {file_path}")

        if file_path.stat().st_size == 0:
            raise ValueError(f"Session file is empty: {file_path}")

        logger.info(f"Loading session from {file_path}")
        logger.info(f"File size: {file_path.stat().st_size:,} bytes")

        # Reset state
        self.session_data = SessionData()
        self.error_count = 0
        self.warning_count = 0

        # Set session_id from filename (stem)
        self.session_data.session_id = file_path.stem

        # Store file metadata
        self.session_data.metadata["file_path"] = str(file_path)
        self.session_data.metadata["file_size"] = file_path.stat().st_size
        self.session_data.metadata["modified_time"] = datetime.fromtimestamp(file_path.stat().st_mtime, tz=UTC)

        # First pass: identify compact artifacts to filter
        compact_boundary_uuids = set()
        compact_summary_uuids = set()

        with open(file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)

                    # Mark compact boundaries (system messages with subtype)
                    if (
                        data.get("type") == "system"
                        and data.get("subtype") == "compact_boundary"
                        and (uuid := data.get("uuid"))
                    ):
                        compact_boundary_uuids.add(uuid)

                    # Mark compact summaries (messages with isCompactSummary flag)
                    if data.get("isCompactSummary") and (uuid := data.get("uuid")):
                        compact_summary_uuids.add(uuid)

                except json.JSONDecodeError:
                    continue

        # Second pass: load messages, filtering compact artifacts
        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                self._process_line(line, line_num, compact_boundary_uuids, compact_summary_uuids)

        # Build parent-child relationships
        self._build_relationships()

        # NEW: Classify session type
        self._classify_session()

        # Log summary
        logger.info(f"Loaded {self.session_data.count_messages()} messages")
        if compact_boundary_uuids or compact_summary_uuids:
            logger.info(
                f"Filtered {len(compact_boundary_uuids)} compact boundaries and {len(compact_summary_uuids)} compact summaries"
            )
        if self.session_data.count_branches() > 0:
            logger.info(f"Found {self.session_data.count_branches()} branches")
        if self.session_data.has_sidechains():
            logger.info("Session contains sidechains")
        if self.error_count > 0:
            logger.warning(f"Encountered {self.error_count} errors during loading")

        return self.session_data

    def _process_line(
        self,
        line: str,
        line_num: int,
        compact_boundary_uuids: set | None = None,
        compact_summary_uuids: set | None = None,
    ):
        """Process a single line from the JSONL file."""
        line = line.strip()
        if not line:
            return

        try:
            data = json.loads(line)

            # Skip if no UUID
            if "uuid" not in data:
                self.warning_count += 1
                logger.debug(f"Line {line_num}: Message without UUID, skipping")
                return

            # Skip compact artifacts if filtering is enabled
            if compact_boundary_uuids is not None or compact_summary_uuids is not None:
                uuid = data["uuid"]
                if (compact_boundary_uuids and uuid in compact_boundary_uuids) or (
                    compact_summary_uuids and uuid in compact_summary_uuids
                ):
                    logger.debug(f"Filtering compact artifact: {uuid}")
                    return

            # Create message object
            msg = self._create_message(data, line_num)

            # Store the message
            self.session_data.messages[msg.uuid] = msg

        except json.JSONDecodeError as e:
            self.error_count += 1
            logger.warning(f"Line {line_num}: Invalid JSON - {e}")
        except Exception as e:
            self.error_count += 1
            logger.warning(f"Line {line_num}: Error processing message - {e}")

    def _create_message(self, data: dict, line_num: int) -> Message:
        """Create a Message object from raw data."""
        # Extract content - can be in different places
        content = data.get("message") or data.get("content") or ""

        # Parse timestamp if available
        timestamp = None
        if "timestamp" in data:
            with contextlib.suppress(ValueError, TypeError):
                timestamp = datetime.fromisoformat(data["timestamp"])

        # Create message
        msg = Message(
            uuid=data["uuid"],
            type=data.get("type", "unknown"),
            parent_uuid=data.get("parentUuid"),
            content=content,
            timestamp=timestamp,
            line_number=line_num,
            is_sidechain=data.get("isSidechain", False),
            user_type=data.get("userType"),
        )

        # Store any extra metadata
        skip_fields = {"uuid", "type", "parentUuid", "message", "content", "timestamp", "isSidechain", "userType"}
        for key, value in data.items():
            if key not in skip_fields:
                msg.metadata[key] = value

        return msg

    def _build_relationships(self):
        """Build parent-child relationships and identify roots."""
        for uuid, msg in self.session_data.messages.items():
            if msg.parent_uuid:
                # Add to parent's children
                if msg.parent_uuid not in self.session_data.parent_child_map:
                    self.session_data.parent_child_map[msg.parent_uuid] = []
                self.session_data.parent_child_map[msg.parent_uuid].append(uuid)
            else:
                # It's a root message
                self.session_data.root_messages.append(uuid)

        # Sort children by line number for consistent ordering
        for parent_uuid in self.session_data.parent_child_map:
            children = self.session_data.parent_child_map[parent_uuid]
            children.sort(key=lambda c: self.session_data.messages[c].line_number)

    def _classify_session(self):
        """Classify session type and detect subagent name."""
        # Check for modern sidechain (any message has isSidechain: true)
        has_sidechain = any(msg.is_sidechain for msg in self.session_data.messages.values())

        if has_sidechain:
            self.session_data.session_type = SessionType.MODERN_SIDECHAIN
            self.session_data.subagent_name = self._extract_subagent_from_task()
            logger.info(f"Detected modern sidechain session (agent: {self.session_data.subagent_name})")
            return

        # Check for legacy subagent session using mapper
        if self.subagent_mapper and self.session_data.session_id:
            subagent_info = self.subagent_mapper.get_subagent_info(self.session_data.session_id)
            if subagent_info:
                self.session_data.session_type = SessionType.LEGACY_SUBAGENT
                self.session_data.subagent_name = subagent_info.subagent_type
                logger.info(f"Detected legacy subagent session (agent: {self.session_data.subagent_name})")
                return

        self.session_data.session_type = SessionType.REGULAR

    def _extract_subagent_from_task(self) -> str | None:
        """Extract subagent name from Task tool invocation."""
        # Look through all messages for Task tool
        for msg in self.session_data.messages.values():
            if msg.is_tool_use():
                tools = msg.get_tool_calls()
                for tool in tools:
                    if tool.get("name") == "Task":
                        input_data = tool.get("input", {})
                        subagent = input_data.get("subagent_type")
                        if subagent:
                            return subagent
        return "Unknown Agent"

    def load_session_chain(self, session_paths: list[Path]) -> SessionData:
        """Load a chain of sessions linked by compact operations.

        Sessions are merged into a single DAG, filtering out compact boundary
        and summary messages to provide a clean conversation history.

        Args:
            session_paths: List of session files ordered oldest to newest

        Returns:
            SessionData with merged conversation from all sessions
        """
        if not session_paths:
            raise ValueError("No session paths provided")

        logger.info(f"Loading session chain of {len(session_paths)} sessions")

        # Reset state
        self.session_data = SessionData()
        self.error_count = 0
        self.warning_count = 0

        # Set session_id from the first session file (primary session)
        if session_paths:
            self.session_data.session_id = session_paths[0].stem

        # Track compact artifacts to filter them out
        compact_boundary_uuids = set()
        compact_summary_uuids = set()

        # First pass: identify compact artifacts across all files
        for session_path in session_paths:
            if not session_path.exists():
                logger.warning(f"Session file not found: {session_path}")
                continue

            with open(session_path, encoding="utf-8") as f:
                for _line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # Mark compact boundaries (system messages with subtype)
                        if (
                            data.get("type") == "system"
                            and data.get("subtype") == "compact_boundary"
                            and (uuid := data.get("uuid"))
                        ):
                            compact_boundary_uuids.add(uuid)

                        # Mark compact summaries (messages with isCompactSummary flag)
                        if data.get("isCompactSummary") and (uuid := data.get("uuid")):
                            compact_summary_uuids.add(uuid)

                    except json.JSONDecodeError:
                        continue
                    except Exception:
                        continue

        # Second pass: load messages, filtering compact artifacts
        for session_index, session_path in enumerate(session_paths):
            if not session_path.exists():
                continue

            logger.info(f"  Loading session {session_index + 1}/{len(session_paths)}: {session_path.name}")

            with open(session_path, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        uuid = data.get("uuid")

                        # Skip if no UUID
                        if not uuid:
                            continue

                        # Skip compact artifacts
                        if uuid in compact_boundary_uuids or uuid in compact_summary_uuids:
                            logger.debug(f"Filtering compact artifact: {uuid}")
                            continue

                        # Skip if we already have this message (deduplicate across files)
                        if uuid in self.session_data.messages:
                            logger.debug(f"Skipping duplicate message: {uuid}")
                            continue

                        # Create and store message
                        msg = self._create_message(data, line_num)
                        self.session_data.messages[msg.uuid] = msg

                    except json.JSONDecodeError as e:
                        self.error_count += 1
                        logger.warning(f"{session_path.name}:{line_num}: Invalid JSON - {e}")
                    except Exception as e:
                        self.error_count += 1
                        logger.warning(f"{session_path.name}:{line_num}: Error - {e}")

        # Build relationships for the merged DAG
        self._build_relationships()

        # NEW: Classify session type
        self._classify_session()

        # Store metadata about the chain
        self.session_data.metadata["chain_length"] = len(session_paths)
        self.session_data.metadata["chain_sessions"] = [p.stem for p in session_paths]
        self.session_data.metadata["file_path"] = str(session_paths[-1])  # Most recent
        self.session_data.metadata["total_files_size"] = sum(p.stat().st_size for p in session_paths if p.exists())

        # Log summary
        logger.info(f"Loaded {self.session_data.count_messages()} messages from chain")
        logger.info(
            f"Filtered {len(compact_boundary_uuids)} compact boundaries and {len(compact_summary_uuids)} compact summaries"
        )
        if self.session_data.count_branches() > 0:
            logger.info(f"Found {self.session_data.count_branches()} branches in merged DAG")
        if self.session_data.has_sidechains():
            logger.info("Merged session contains sidechains")
        if self.error_count > 0:
            logger.warning(f"Encountered {self.error_count} errors during loading")

        return self.session_data
