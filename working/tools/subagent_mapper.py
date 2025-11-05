#!/usr/bin/env python3
"""
SubagentMapper: Map Task invocations to resulting subagent sessions

Purpose: Connect parent sessions to their spawned subagent sessions by matching
         Task tool invocations with the first user message in subagent sessions.

Contract:
    Inputs: List of session file paths (JSONL format)
    Outputs: Dict mapping session_id -> SubagentInfo
    Errors: ValueError for invalid formats, FileNotFoundError for missing files
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SubagentInfo:
    """Information about a subagent session"""

    parent_session_id: str
    subagent_type: str
    task_prompt: str


class SubagentMapper:
    """Map Task invocations to resulting subagent sessions"""

    def __init__(self, session_paths: list[Path]):
        """Initialize with all session file paths"""
        self.session_paths = session_paths
        self._mapping: dict[str, SubagentInfo] = {}
        self._task_index: dict[
            str, list[tuple[str, str, str]]
        ] = {}  # prompt_hash -> [(session_id, subagent_type, prompt)]

    def build_mapping(self) -> dict[str, SubagentInfo]:
        """Build complete mapping of subagent sessions"""
        # Build task index from all sessions
        self._build_task_index()

        # Match sessions to tasks
        self._match_sessions_to_tasks()

        return self._mapping

    def is_subagent_session(self, session_id: str) -> bool:
        """Check if a session is a subagent session"""
        if not self._mapping:
            self.build_mapping()
        return session_id in self._mapping

    def get_subagent_info(self, session_id: str) -> SubagentInfo | None:
        """Get subagent info for a session if it exists"""
        if not self._mapping:
            self.build_mapping()
        return self._mapping.get(session_id)

    def get_subagent_sessions(self, parent_session_id: str) -> list[tuple[str, SubagentInfo]]:
        """Get all subagent sessions spawned from a parent.

        Returns list of (session_id, SubagentInfo) tuples.
        Includes both v1.x separate files and v2.x synthetic sidechain IDs.
        """
        if not self._mapping:
            self.build_mapping()

        result = []
        for session_id, info in self._mapping.items():
            if info.parent_session_id == parent_session_id:
                result.append((session_id, info))

        return result

    def _build_task_index(self):
        """Extract all Task invocations from sessions"""
        for session_path in self.session_paths:
            if not session_path.exists():
                logger.warning(f"Session file not found: {session_path}")
                continue

            session_id = session_path.stem

            try:
                with open(session_path, encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue

                        try:
                            message = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        # Look for assistant messages with tool use
                        # Handle both direct message format and nested message format
                        if "message" in message and isinstance(message["message"], dict):
                            msg = message["message"]
                            if msg.get("role") == "assistant" and "content" in msg:
                                self._extract_task_invocations(session_id, msg["content"])
                        elif message.get("role") == "assistant" and "content" in message:
                            self._extract_task_invocations(session_id, message["content"])

            except Exception as e:
                logger.error(f"Error processing {session_path}: {e}")

    def _extract_task_invocations(self, session_id: str, content):
        """Extract Task tool invocations from assistant message content"""
        if not isinstance(content, list):
            return

        for block in content:
            if not isinstance(block, dict):
                continue

            # Check for tool_use block with Task tool
            if block.get("type") == "tool_use" and block.get("name") == "Task":
                input_data = block.get("input", {})
                subagent_type = input_data.get("subagent_type", "")
                prompt = input_data.get("prompt", "")

                if prompt:
                    # Normalize and hash the prompt
                    normalized = self._normalize_prompt(prompt)
                    prompt_hash = self._hash_prompt(normalized)

                    # Add to index
                    if prompt_hash not in self._task_index:
                        self._task_index[prompt_hash] = []
                    self._task_index[prompt_hash].append((session_id, subagent_type, prompt))

    def _match_sessions_to_tasks(self):
        """Match sessions to tasks based on first user message"""
        for session_path in self.session_paths:
            if not session_path.exists():
                continue

            session_id = session_path.stem

            # Handle v2.x sidechains within the same file
            self._process_sidechains(session_path)

            # Also check for v1.x separate files (first user message matching)
            first_user_msg = self._get_first_user_message(session_path, exclude_sidechains=True)
            if not first_user_msg:
                continue

            # Normalize and hash
            normalized = self._normalize_prompt(first_user_msg)
            prompt_hash = self._hash_prompt(normalized)

            # Look for matching Task invocation
            if prompt_hash in self._task_index:
                # Use the first match (could be multiple if same prompt used multiple times)
                parent_session_id, subagent_type, task_prompt = self._task_index[prompt_hash][0]

                # Don't map a session to itself (v1.x style)
                if parent_session_id != session_id:
                    self._mapping[session_id] = SubagentInfo(
                        parent_session_id=parent_session_id, subagent_type=subagent_type, task_prompt=task_prompt
                    )

    def _process_sidechains(self, session_path: Path):
        """Process v2.x sidechains within a session file"""
        session_id = session_path.stem

        try:
            with open(session_path, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        message = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Look for sidechain user messages
                    if message.get("isSidechain") is True:
                        # Check if message has nested structure
                        content = None
                        if "message" in message and isinstance(message["message"], dict):
                            msg = message["message"]
                            if msg.get("role") == "user":
                                content = msg.get("content", "")

                        if content:
                            if isinstance(content, list):
                                # Extract text from content blocks
                                text_parts = []
                                for block in content:
                                    if isinstance(block, dict) and block.get("type") == "text":
                                        text_parts.append(block.get("text", ""))
                                content = " ".join(text_parts)

                            # Match against task index
                            normalized = self._normalize_prompt(content)
                            prompt_hash = self._hash_prompt(normalized)

                            if prompt_hash in self._task_index:
                                # Find the task that matches and is from this same session
                                for task_session_id, subagent_type, task_prompt in self._task_index[prompt_hash]:
                                    if task_session_id == session_id:
                                        # Create a synthetic session ID for the sidechain
                                        sidechain_id = f"{session_id}_sidechain_{message.get('uuid', 'unknown')[:8]}"
                                        self._mapping[sidechain_id] = SubagentInfo(
                                            parent_session_id=session_id,
                                            subagent_type=subagent_type,
                                            task_prompt=task_prompt,
                                        )
                                        break

        except Exception as e:
            logger.error(f"Error processing sidechains in {session_path}: {e}")

    def _get_first_user_message(self, session_path: Path, exclude_sidechains: bool = False) -> str | None:
        """Get the content of the first user message in a session"""
        try:
            with open(session_path, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        message = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Skip sidechains if requested
                    if exclude_sidechains and message.get("isSidechain") is True:
                        continue

                    # Handle both direct and nested message formats
                    role = None
                    content = None

                    if "message" in message and isinstance(message["message"], dict):
                        msg = message["message"]
                        role = msg.get("role")
                        content = msg.get("content", "")
                    else:
                        role = message.get("role")
                        content = message.get("content", "")

                    if role == "user" and content:
                        # Handle both string and list content
                        if isinstance(content, list):
                            # Extract text from content blocks
                            text_parts = []
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    text_parts.append(block.get("text", ""))
                            return " ".join(text_parts)
                        return content

        except Exception as e:
            logger.error(f"Error reading first user message from {session_path}: {e}")

        return None

    def _is_sidechain(self, session_path: Path) -> bool:
        """Check if session has v2.x sidechain flag"""
        try:
            with open(session_path, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        message = json.loads(line)
                        if message.get("isSidechain") is True:
                            return True
                    except json.JSONDecodeError:
                        continue

                    # Only check first few messages for efficiency
                    break

        except Exception:
            pass

        return False

    def _normalize_prompt(self, text: str) -> str:
        """Normalize text for matching (strip and collapse whitespace)"""
        if not text:
            return ""
        # Strip leading/trailing whitespace and collapse internal whitespace
        return " ".join(text.split())

    def _hash_prompt(self, normalized_text: str) -> str:
        """Generate SHA256 hash of normalized text for efficient lookup"""
        return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


def main():
    """Simple CLI for testing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python subagent_mapper.py <session_dir>")
        sys.exit(1)

    session_dir = Path(sys.argv[1])
    if not session_dir.exists():
        print(f"Directory not found: {session_dir}")
        sys.exit(1)

    # Find all JSONL files
    session_files = list(session_dir.glob("*.jsonl"))
    print(f"Found {len(session_files)} session files")

    # Build mapping
    mapper = SubagentMapper(session_files)
    mapping = mapper.build_mapping()

    # Display results
    print(f"\nFound {len(mapping)} subagent sessions:")
    for session_id, info in mapping.items():
        print(f"\n  Session: {session_id}")
        print(f"    Parent: {info.parent_session_id}")
        print(f"    Type: {info.subagent_type}")
        print(
            f"    Prompt: {info.task_prompt[:100]}..."
            if len(info.task_prompt) > 100
            else f"    Prompt: {info.task_prompt}"
        )


if __name__ == "__main__":
    main()
