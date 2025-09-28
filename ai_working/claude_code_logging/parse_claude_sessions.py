#!/usr/bin/env python3
"""
Claude Code Session Parser and Transcript Generator

This tool parses Claude Code session logs and generates complete transcripts
for each unique conversation path, handling both cross-session forks and
internal DAG branches within sessions.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

# Increase recursion limit for deep conversation paths
sys.setrecursionlimit(10000)


class ClaudeSessionParser:
    def __init__(self, project_dir: str):
        """Initialize parser with project directory."""
        self.project_dir = Path(project_dir)

        # Helper to replace home path with ~
        def format_path_for_display(path):
            path_str = str(path)
            home_str = str(Path.home())
            if path_str.startswith(home_str):
                return path_str.replace(home_str, "~", 1)
            return path_str

        # Check if this is a direct path to session files
        if self.project_dir.exists() and self.project_dir.is_dir():
            # Check if it's already a Claude projects directory
            if "projects" in self.project_dir.parts and ".claude" in self.project_dir.parts:
                # Direct path to Claude session directory
                self.claude_dir = self.project_dir
                self.display_claude_dir = format_path_for_display(self.project_dir)
            else:
                # Regular project directory - convert to Claude naming convention
                # Get the absolute resolved path
                resolved_path = self.project_dir.resolve()
                # Convert to Claude project naming (replace / with -)
                claude_project_name = str(resolved_path).replace("/", "-")
                self.claude_dir = Path.home() / ".claude" / "projects" / claude_project_name
                self.display_claude_dir = f"~/.claude/projects/{claude_project_name}"
        else:
            # Convert the full path to the Claude naming convention
            self.claude_dir = Path.home() / ".claude" / "projects" / str(self.project_dir).replace("/", "-")
            self.display_claude_dir = f"~/.claude/projects/{str(self.project_dir).replace('/', '-')}"

        self.sessions: dict[str, dict] = {}
        self.all_paths: list[dict] = []
        self.subagent_sessions: set[str] = set()  # Track which sessions are subagents

    def discover_sessions(self) -> list[Path]:
        """Find all session JSONL files in the Claude directory."""
        if not self.claude_dir.exists():
            print(f"Claude directory not found: {self.display_claude_dir}")
            return []

        jsonl_files = list(self.claude_dir.glob("*.jsonl"))
        print(f"Found {len(jsonl_files)} session files in {self.display_claude_dir}")
        return jsonl_files

    def parse_jsonl_file(self, filepath: Path) -> list[dict]:
        """Parse a JSONL file and return list of message objects."""
        messages = []
        with open(filepath, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    msg["_line_number"] = line_num  # Track line number for branch detection
                    messages.append(msg)
                except json.JSONDecodeError as e:
                    print(f"Error parsing line {line_num} in {filepath}: {e}")
        return messages

    def extract_session_id(self, filepath: Path) -> str:
        """Extract session UUID from filename."""
        return filepath.stem

    def build_message_dag(self, messages: list[dict]) -> tuple[dict, dict, list]:
        """Build a DAG structure from messages."""
        children_map = defaultdict(list)
        message_by_uuid = {}
        roots = []

        for msg in messages:
            if msg.get("type") == "summary":
                continue

            uuid = msg.get("uuid")
            parent_uuid = msg.get("parentUuid")

            message_by_uuid[uuid] = msg

            if parent_uuid:
                children_map[parent_uuid].append(uuid)
            else:
                roots.append(uuid)

        return children_map, message_by_uuid, roots

    def detect_compact_boundaries(self, messages: list[dict]) -> list[dict]:
        """Find compact boundary messages in a session."""
        boundaries = []
        for msg in messages:
            if msg.get("subtype") == "compact_boundary":
                boundaries.append(msg)
        return boundaries

    def trace_all_paths(self, root_uuid: str, children_map: dict, message_by_uuid: dict) -> list[list[str]]:
        """Recursively trace all paths from a root to all leaves."""

        def trace_from(node, visited=None):
            if visited is None:
                visited = set()

            # Detect cycles
            if node in visited:
                print(f"Warning: Cycle detected at node {node[:8]}...")
                return []

            visited = visited | {node}

            children = children_map.get(node, [])

            if not children:
                # Leaf node - return single path ending here
                return [[node]]

            # Get all paths from children
            all_paths = []
            for child in children:
                child_paths = trace_from(child, visited)
                for path in child_paths:
                    all_paths.append([node] + path)

            return all_paths

        return trace_from(root_uuid)

    def detect_abandoned_branches(self, paths: list[list[str]], message_by_uuid: dict) -> dict[int, bool]:
        """Detect which paths are abandoned based on fork points and file position."""
        path_status = {}

        # Find fork points (where paths diverge)
        for i, path1 in enumerate(paths):
            path_status[i] = False  # Default to not abandoned

            # Check if this path shares a fork point with another path
            for j, path2 in enumerate(paths):
                if i == j:
                    continue

                # Find common ancestor and divergence point
                min_len = min(len(path1), len(path2))
                divergence_idx = None

                for k in range(min_len):
                    if path1[k] != path2[k]:
                        divergence_idx = k
                        break

                if divergence_idx is not None and divergence_idx > 0:
                    # These paths diverge at index divergence_idx
                    # The earlier branch (by line number) is abandoned
                    msg1 = message_by_uuid[path1[divergence_idx]]
                    msg2 = message_by_uuid[path2[divergence_idx]]

                    line1 = msg1.get("_line_number", 0)
                    line2 = msg2.get("_line_number", 0)

                    if line1 < line2:
                        path_status[i] = True  # Path i is abandoned
                    elif line2 < line1:
                        path_status[j] = True  # Path j is abandoned

        return path_status

    def extract_session_paths(self, session_id: str, messages: list[dict]) -> list[dict]:
        """Extract all conversation paths from a session."""
        # Check if summary-only
        if all(msg.get("type") == "summary" for msg in messages):
            return []

        # Check for compact boundaries
        boundaries = self.detect_compact_boundaries(messages)

        if boundaries:
            # Handle compacted session specially
            return self.extract_compact_session_paths(session_id, messages, boundaries)

        # Build DAG for non-compact session
        children_map, message_by_uuid, roots = self.build_message_dag(messages)

        if not roots:
            return []

        # Extract all paths
        all_paths = []
        for root in roots:
            paths = self.trace_all_paths(root, children_map, message_by_uuid)
            all_paths.extend(paths)

        # Detect abandoned branches
        path_status = self.detect_abandoned_branches(all_paths, message_by_uuid)

        # Build path information
        path_info_list = []
        for i, path in enumerate(all_paths):
            path_messages = [message_by_uuid[uuid] for uuid in path]

            # Find fork point if abandoned
            fork_point = None
            if path_status.get(i, False):
                # Find where this path diverged
                for j, other_path in enumerate(all_paths):
                    if i != j and not path_status.get(j, False):
                        # Find divergence point
                        for k in range(min(len(path), len(other_path))):
                            if path[k] != other_path[k]:
                                if k > 0:
                                    fork_point = path[k - 1]
                                break
                        if fork_point:
                            break

            path_info = {
                "session_id": session_id,
                "path_index": i + 1,
                "total_paths": len(all_paths),
                "is_abandoned": path_status.get(i, False),
                "fork_point": fork_point,
                "message_uuids": path,
                "messages": path_messages,
            }
            path_info_list.append(path_info)

        return path_info_list

    def extract_compact_session_paths(
        self, session_id: str, messages: list[dict], boundaries: list[dict]
    ) -> list[dict]:
        """Extract complete conversation paths from a compacted session, combining pre and post-compact segments."""
        # Build a complete DAG with all messages including boundaries
        children_map, message_by_uuid, roots = self.build_message_dag(messages)

        # Create artificial connections from boundaries to their logical parents
        # BUT avoid cycles - only connect if boundary isn't already reachable
        for boundary in boundaries:
            boundary_uuid = boundary.get("uuid")
            logical_parent_uuid = boundary.get("logicalParentUuid")

            if (
                logical_parent_uuid
                and logical_parent_uuid in message_by_uuid
                and boundary_uuid not in children_map.get(logical_parent_uuid, [])
            ):
                # Add the boundary as a child of its logical parent (avoid cycles)
                children_map[logical_parent_uuid].append(boundary_uuid)

        # Extract all complete paths from roots to leaves
        all_paths = []
        for root in roots:
            paths = self.trace_all_paths(root, children_map, message_by_uuid)
            all_paths.extend(paths)

        # Detect abandoned branches using line number comparison
        path_status = self.detect_abandoned_branches(all_paths, message_by_uuid)

        # Build path information with full conversations
        path_info_list = []
        for i, path in enumerate(all_paths):
            path_messages = [message_by_uuid[uuid] for uuid in path]

            # Check if this path includes any compact boundaries
            has_compact = any(msg.get("subtype") == "compact_boundary" for msg in path_messages)

            # Find fork point if abandoned
            fork_point = None
            if path_status.get(i, False):
                for j, other_path in enumerate(all_paths):
                    if i != j and not path_status.get(j, False):
                        for k in range(min(len(path), len(other_path))):
                            if path[k] != other_path[k]:
                                if k > 0:
                                    fork_point = path[k - 1]
                                break
                        if fork_point:
                            break

            path_info = {
                "session_id": session_id,
                "path_index": i + 1,
                "total_paths": len(all_paths),
                "is_abandoned": path_status.get(i, False),
                "fork_point": fork_point,
                "message_uuids": path,
                "messages": path_messages,
                "has_compact": has_compact,
            }
            path_info_list.append(path_info)

        return path_info_list

    def extract_task_calls(self, messages: list[dict]) -> list[dict]:
        """Extract all Task tool calls from messages.

        Returns:
            list: List of task call details with timestamp, session_id, subagent_type, description
        """
        task_calls = []

        for msg in messages:
            if msg.get("type") != "assistant":
                continue

            message_data = msg.get("message", {})
            content = message_data.get("content", [])

            if not isinstance(content, list):
                continue

            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use" and item.get("name") == "Task":
                    tool_input = item.get("input", {})
                    task_info = {
                        "timestamp": msg.get("timestamp", ""),
                        "session_id": msg.get("sessionId", ""),
                        "subagent_type": tool_input.get("subagent_type", "unknown"),
                        "prompt": tool_input.get("prompt", ""),
                        "uuid": msg.get("uuid", ""),
                    }
                    task_calls.append(task_info)

        return task_calls

    def find_parent_task(
        self, session_start_time: str, all_task_calls: list[dict], time_window: tuple[int, int] = (30, 180)
    ) -> dict | None:
        """Find the parent Task call that likely spawned this subagent session.

        Args:
            session_start_time: ISO timestamp of session start
            all_task_calls: List of all task calls from all sessions
            time_window: (min_seconds, max_seconds) before session start to look for parent

        Returns:
            dict: Parent task info or None if not found
        """
        from datetime import datetime
        from datetime import timedelta

        try:
            session_dt = datetime.fromisoformat(session_start_time.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

        min_seconds, max_seconds = time_window
        min_time = session_dt - timedelta(seconds=max_seconds)
        max_time = session_dt - timedelta(seconds=min_seconds)

        # Find task calls within time window
        candidates = []
        for task in all_task_calls:
            try:
                task_dt = datetime.fromisoformat(task["timestamp"].replace("Z", "+00:00"))
                if min_time <= task_dt <= max_time:
                    time_diff = (session_dt - task_dt).total_seconds()
                    candidates.append((time_diff, task))
            except (ValueError, AttributeError):
                continue

        if not candidates:
            return None

        # Return closest match
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    def detect_subagent_session(self, messages: list[dict]) -> bool:
        """Detect if this session is a subagent session (no Task calls).

        Returns:
            bool: True if likely a subagent session
        """
        if not messages:
            return False

        # Sessions with Task calls are parent sessions, not subagents
        task_calls = self.extract_task_calls(messages)
        if task_calls:
            return False

        # Check first user message for common subagent patterns
        for msg in messages:
            if msg.get("type") == "user" and msg.get("message"):
                content = msg["message"].get("content", "")
                if isinstance(content, list) and content:
                    content = content[0].get("text", "") if isinstance(content[0], dict) else str(content[0])
                content_str = str(content)

                # Simple subagent patterns
                subagent_patterns = [
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

                for pattern in subagent_patterns:
                    if pattern in content_str[:500]:  # Check first 500 chars
                        return True
                break  # Only check first user message

        return False

    def build_session_graph(self):
        """Build a graph of all sessions and extract all paths."""
        session_files = self.discover_sessions()

        # First pass: Parse all sessions and collect Task calls
        all_task_calls = []
        temp_sessions = {}  # Temporary storage

        for filepath in session_files:
            session_id = self.extract_session_id(filepath)
            messages = self.parse_jsonl_file(filepath)

            if not messages:
                print(f"Warning: Empty session file {filepath}")
                continue

            # Extract Task calls from this session
            task_calls = self.extract_task_calls(messages)
            all_task_calls.extend(task_calls)

            # Store for second pass
            temp_sessions[session_id] = {"filepath": filepath, "messages": messages, "has_task_calls": bool(task_calls)}

        # Second pass: Match subagents to parent Tasks and build final sessions
        for session_id, session_data in temp_sessions.items():
            messages = session_data["messages"]

            # Detect if this is a subagent session
            is_subagent = self.detect_subagent_session(messages)
            agent_type = "unknown"

            if is_subagent:
                self.subagent_sessions.add(session_id)

                # Find parent Task to determine agent type
                if messages:
                    first_msg_time = messages[0].get("timestamp", "")
                    parent_task = self.find_parent_task(first_msg_time, all_task_calls)

                    if parent_task:
                        agent_type = parent_task.get("subagent_type", "unknown")
                        # Clean up agent type (remove quotes, lowercase, replace spaces)
                        agent_type = agent_type.strip('"').lower().replace(" ", "-").replace("_", "-")
                        if not agent_type:
                            agent_type = "unknown"

            # Extract all paths from this session
            session_paths = self.extract_session_paths(session_id, messages)

            self.sessions[session_id] = {
                "filepath": session_data["filepath"],
                "messages": messages,
                "paths": session_paths,
                "is_subagent": is_subagent,
                "agent_type": agent_type if is_subagent else "",
                "has_task_calls": session_data["has_task_calls"],
            }

            # Add paths to global list
            self.all_paths.extend(session_paths)

            # Format session type for display
            if is_subagent:
                session_type = f"[SUBAGENT-{agent_type.upper()[:10]:<10}]"
            else:
                session_type = "[MAIN           ]"
            print(f"Session {session_id[:8]}... {session_type}: {len(messages)} messages, {len(session_paths)} path(s)")

    def eliminate_subset_paths(self) -> list[dict]:
        """Eliminate paths that are subsets of other paths."""
        unique_paths = []

        for i, path1 in enumerate(self.all_paths):
            is_subset = False
            path1_uuids = set(path1["message_uuids"])

            for j, path2 in enumerate(self.all_paths):
                if i == j:
                    continue

                path2_uuids = set(path2["message_uuids"])

                if path1_uuids.issubset(path2_uuids) and path1_uuids != path2_uuids:
                    is_subset = True
                    break

            if not is_subset:
                unique_paths.append(path1)

        return unique_paths

    def format_message(self, msg: dict, prev_msg: dict | None = None) -> str:
        """Format a single message for the transcript."""
        output = []

        # Add timestamp and session info
        timestamp = msg.get("timestamp", "N/A")
        session_id = msg.get("sessionId", "unknown")
        msg_type = msg.get("type", "unknown")

        output.append(f"\n{'=' * 80}")
        output.append(f"Timestamp: {timestamp}")
        output.append(f"Session: {session_id}")
        output.append(f"Type: {msg_type}")

        # Handle compact boundary
        if msg.get("subtype") == "compact_boundary":
            output.append("\n[COMPACT BOUNDARY]")
            compact_meta = msg.get("compactMetadata", {})
            output.append(f"Trigger: {compact_meta.get('trigger', 'N/A')}")
            output.append(f"Pre-Tokens: {compact_meta.get('preTokens', 'N/A')}")
            if msg.get("logicalParentUuid"):
                output.append(f"Logical Parent: {msg['logicalParentUuid'][:12]}...")
            output.append(f"Content: {msg.get('content', 'Conversation compacted')}")
            return "\n".join(output)

        # Handle meta messages
        if msg.get("isMeta"):
            output.append("[META MESSAGE]")

        # Check if this is a compact summary (follows a compact boundary)
        is_compact_summary = (
            prev_msg and prev_msg.get("subtype") == "compact_boundary" and msg.get("parentUuid") == prev_msg.get("uuid")
        )

        # Extract and format content
        message_data = msg.get("message", {})
        role = message_data.get("role", msg_type)

        # Handle content which can be string or array
        content = message_data.get("content", "")
        if isinstance(content, list):
            # Handle structured content
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get("type", "")
                    if item_type == "text":
                        text_parts.append(str(item.get("text", "")))
                    elif item_type == "tool_use":
                        tool_name = item.get("name", "unknown")
                        tool_input = item.get("input", {})
                        text_parts.append(f"[Tool Use: {tool_name}]")
                        # Include key tool inputs for context
                        if isinstance(tool_input, dict) and tool_input:
                            for key, value in list(tool_input.items())[:3]:  # First 3 params
                                # Convert non-string values to string representation
                                if not isinstance(value, str):
                                    value = str(value)
                                if len(value) > 100:
                                    value = value[:100] + "..."
                                text_parts.append(f"  {key}: {value}")
                    elif item_type == "tool_result":
                        tool_content = item.get("content", "")
                        is_error = item.get("is_error", False)

                        # Always show tool result, even if empty
                        if is_error:
                            text_parts.append("[Tool Result - Error]")
                        else:
                            text_parts.append("[Tool Result]")

                        if tool_content:
                            # Convert to string and truncate long tool results
                            tool_content_str = str(tool_content)
                            if len(tool_content_str) > 500:
                                tool_content_str = tool_content_str[:500] + "..."
                            text_parts.append(tool_content_str)
                        else:
                            text_parts.append("(Empty result - tool executed successfully)")
                    elif item_type == "thinking":
                        # Handle thinking content (internal reasoning)
                        thinking_content = item.get("thinking", "")
                        if thinking_content:
                            text_parts.append("[Internal Thinking]")
                            # Don't truncate thinking - show full content
                            text_parts.append(str(thinking_content))
                    else:
                        # Unknown content type - include if it has text
                        if "text" in item:
                            text_parts.append(str(item.get("text", "")))
                        elif "content" in item:
                            text_parts.append(str(item.get("content", "")))
                elif isinstance(item, str):
                    text_parts.append(item)
            content = "\n".join(text_parts) if text_parts else ""

        # Check if this is a tool-related message (based on parsed content, not raw)
        is_tool_use = False
        is_tool_result = False

        # Check the parsed text content for tool markers
        if isinstance(content, str):
            if "[Tool Use:" in content:
                is_tool_use = True
            elif "[Tool Result" in content:
                is_tool_result = True

        # Format the role label
        if is_compact_summary:
            output.append("\n[COMPACT SUMMARY - System Generated]:")
        elif is_tool_result and msg_type == "user":
            # Tool results come back as "user" messages but aren't from the user
            output.append("\n[SYSTEM - Tool Execution]:")
        elif is_tool_use and msg_type == "assistant":
            # Assistant's tool use
            output.append("\n[ASSISTANT - Tool Call]:")
        else:
            output.append(f"\n[{role.upper()}]:")

        output.append(content if content else "[No content]")

        # Add model info for assistant messages
        if msg_type == "assistant" and "model" in message_data:
            model = message_data.get("model", "unknown")
            output.append(f"\nModel: {model}")

            # Add usage stats if available
            usage = message_data.get("usage", {})
            if usage:
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                output.append(f"Tokens: {input_tokens} in / {output_tokens} out")

        return "\n".join(output)

    def format_user_friendly_message(self, msg: dict, prev_msg: dict | None = None) -> str | None:
        """Format a message for user-friendly transcript."""
        msg_type = msg.get("type", "unknown")

        # Skip meta messages and system messages
        if msg.get("isMeta") or msg.get("subtype") == "compact_boundary":
            return None

        timestamp = msg.get("timestamp", "N/A")
        # Convert timestamp to readable format
        from datetime import datetime

        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            formatted_time = dt.strftime("%Y-%m-%d %I:%M %p UTC")
        except (ValueError, AttributeError):
            formatted_time = timestamp

        message_data = msg.get("message", {})
        content = message_data.get("content", "")

        # Check if this is a compact summary
        is_compact_summary = (
            prev_msg and prev_msg.get("subtype") == "compact_boundary" and msg.get("parentUuid") == prev_msg.get("uuid")
        )

        output_lines = []

        # Parse content
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get("type", "")
                    if item_type == "text":
                        text = item.get("text", "").strip()
                        if text:
                            if is_compact_summary:
                                output_lines.append(f"- **Compact Summary** · {formatted_time}")
                                # Show first part of summary
                                first_part = text.split("\n")[0][:200]
                                output_lines.append(f"  {first_part}...")
                            elif msg_type == "user":
                                output_lines.append(f"- **User** · {formatted_time}")
                                output_lines.append(f"  {text}")
                            else:
                                output_lines.append(f"- **Assistant** · {formatted_time}")
                                output_lines.append(f"  {text}")
                    elif item_type == "thinking":
                        thinking = item.get("thinking", "")
                        if thinking:
                            # Summarize thinking in one line
                            summary = thinking.split("\n")[0][:100]
                            output_lines.append(f"- **Assistant [thinking]** · {formatted_time}")
                            output_lines.append(f"  {summary}...")
                    elif item_type == "tool_use":
                        tool_name = item.get("name", "unknown")
                        tool_input = item.get("input", {})
                        output_lines.append(f"- **Tool Call** · {formatted_time}")
                        # Format tool call compactly
                        params = []
                        for key, val in list(tool_input.items())[:3]:
                            if isinstance(val, str) and len(val) > 50:
                                val = val[:50] + "..."
                            params.append(f"{key}={val}")
                        output_lines.append(f"  `{tool_name}` ({', '.join(params)})")
                    elif item_type == "tool_result":
                        content_text = item.get("content", "")
                        output_lines.append(f"- **Tool Result** · {formatted_time}")
                        if content_text:
                            summary = content_text[:100] + "..." if len(content_text) > 100 else content_text
                            output_lines.append(f"  `{tool_name if 'tool_name' in locals() else 'tool'}` {summary}")
                        else:
                            output_lines.append("  (Empty result)")
                elif isinstance(item, str):
                    if item.strip():
                        if msg_type == "user":
                            output_lines.append(f"- **User** · {formatted_time}")
                        else:
                            output_lines.append(f"- **Assistant** · {formatted_time}")
                        output_lines.append(f"  {item}")
        elif isinstance(content, str) and content.strip():
            if is_compact_summary:
                output_lines.append(f"- **Compact Summary** · {formatted_time}")
                # Show first part of summary
                first_part = content.split("\n")[0][:200]
                output_lines.append(f"  {first_part}...")
            elif msg_type == "user":
                output_lines.append(f"- **User** · {formatted_time}")
                output_lines.append(f"  {content}")
            else:
                output_lines.append(f"- **Assistant** · {formatted_time}")
                output_lines.append(f"  {content}")

        return "\n\n".join(output_lines) if output_lines else None

    def generate_transcript_directory(self, path_info: dict, output_dir: Path) -> Path:
        """Generate a directory with both transcript versions."""
        session_id = path_info["session_id"]
        messages = path_info["messages"]
        session_data = self.sessions.get(session_id, {})
        is_subagent = session_data.get("is_subagent", False)
        agent_type = session_data.get("agent_type", "unknown")

        # Get first message timestamp for directory name
        first_msg = messages[0] if messages else None
        if first_msg:
            timestamp = first_msg.get("timestamp", "")
            from datetime import datetime

            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d-%I-%M-%p").lower()
            except (ValueError, AttributeError):
                date_str = "unknown-date"
        else:
            date_str = "unknown-date"

        # Get CWD for path component
        cwd = first_msg.get("cwd", "") if first_msg else ""
        if cwd:
            # Convert path to format with ~ separators
            if cwd.startswith(str(Path.home())):
                path_part = cwd.replace(str(Path.home()) + "/", "").replace("/", "~")
            else:
                path_part = cwd.replace("/", "~")
        else:
            path_part = "unknown-path"

        # Create directory name using new format: SUBAGENT_{agent_type}_{timestamp}_{session_id}
        if is_subagent:
            dir_name = f"SUBAGENT_{agent_type}_{date_str}__{session_id[:8]}"
        else:
            dir_name = f"{date_str}__{path_part}__{session_id[:8]}"
        transcript_dir = output_dir / dir_name
        transcript_dir.mkdir(exist_ok=True, parents=True)

        # Generate user-friendly transcript
        user_friendly_lines = []
        user_friendly_lines.append("# Session Transcript\n")
        user_friendly_lines.append("## Metadata")
        user_friendly_lines.append(f"- Session ID: {session_id}")
        if is_subagent:
            user_friendly_lines.append(f"- **Type: SUBAGENT SESSION** ({agent_type})")
        if first_msg:
            user_friendly_lines.append(f"- Start: {date_str.replace('-', ' ').replace('~', ':').upper()}")
            user_friendly_lines.append(f"- CWD: {cwd}")
        user_friendly_lines.append("")
        user_friendly_lines.append("## Conversation")

        prev_msg = None
        for msg in messages:
            formatted = self.format_user_friendly_message(msg, prev_msg)
            if formatted:
                user_friendly_lines.append(formatted)
            prev_msg = msg

        # Write user-friendly version
        with open(transcript_dir / "transcript.md", "w", encoding="utf-8") as f:
            f.write("\n".join(user_friendly_lines))

        # Generate extended transcript (existing format with improvements)
        extended_lines = []
        extended_lines.append("# CLAUDE CODE SESSION TRANSCRIPT - EXTENDED\n")
        extended_lines.append(f"Session ID: {session_id}")
        if is_subagent:
            extended_lines.append(f"**Session Type: SUBAGENT ({agent_type})**")
        extended_lines.append(f"Total Messages: {len(messages)}")

        if path_info.get("has_compact", False):
            extended_lines.append("**Contains Compact Operation(s)**")

        extended_lines.append("\n" + "=" * 80 + "\n")

        prev_msg = None
        for msg in messages:
            # Use existing format_message but remove excessive blank lines
            formatted = self.format_message(msg, prev_msg)
            # Clean up multiple blank lines
            formatted = "\n".join(line for line in formatted.split("\n") if line.strip() or not prev_msg)
            extended_lines.append(formatted)
            prev_msg = msg

        # Write extended version
        with open(transcript_dir / "transcript_extended.md", "w", encoding="utf-8") as f:
            f.write("\n".join(extended_lines))

        # Copy the original session JSONL file to the transcript directory
        import shutil

        session_data = self.sessions.get(session_id, {})
        if session_data and "filepath" in session_data:
            source_file = session_data["filepath"]
            dest_file = transcript_dir / "session.jsonl"
            shutil.copy2(source_file, dest_file)

        return transcript_dir

    def generate_all_transcripts(self, output_dir: Path | None = None) -> list[Path]:
        """Generate transcripts for all unique conversation paths."""
        if output_dir is None:
            output_dir = Path.cwd() / "claude_transcripts"

        output_dir.mkdir(exist_ok=True)

        # Build the session graph and extract all paths
        self.build_session_graph()

        # Eliminate subset paths
        unique_paths = self.eliminate_subset_paths()

        print(f"\nTotal paths found: {len(self.all_paths)}")
        print(f"Unique paths after deduplication: {len(unique_paths)}")
        print(f"\nGenerating transcripts for {len(unique_paths)} unique conversation path(s)...")

        generated_dirs = []
        for path_info in unique_paths:
            session_id = path_info["session_id"]
            path_idx = path_info["path_index"]
            status = "abandoned" if path_info["is_abandoned"] else "active"
            print(f"Generating transcript directory for session {session_id[:8]}... path {path_idx} ({status})...")
            transcript_dir = self.generate_transcript_directory(path_info, output_dir)
            # Store the directory name in path_info for the summary
            path_info["directory_name"] = transcript_dir.name
            generated_dirs.append(transcript_dir)
            print(f"  -> Created directory: {transcript_dir.name}")

        # Generate summary file
        summary_file = output_dir / "session_summary.md"
        self.generate_summary(summary_file, unique_paths)
        generated_dirs.append(summary_file)

        return generated_dirs

    def extract_summaries(self) -> dict[str, list[dict]]:
        """Extract summary information from summary-only files."""
        summaries_by_target = defaultdict(list)

        for session_id, data in self.sessions.items():
            # Check if this is a summary-only file
            if all(msg.get("type") == "summary" for msg in data["messages"]):
                for msg in data["messages"]:
                    if msg.get("type") == "summary":
                        summary_text = msg.get("summary", "")
                        leaf_uuid = msg.get("leafUuid", "")

                        # Find which session contains this UUID
                        for target_id, target_data in self.sessions.items():
                            for target_msg in target_data["messages"]:
                                if target_msg.get("uuid") == leaf_uuid:
                                    summaries_by_target[target_id].append(
                                        {
                                            "text": summary_text,
                                            "leaf_uuid": leaf_uuid,
                                            "source_file": session_id,
                                        }
                                    )
                                    break

        return summaries_by_target

    def generate_summary(self, output_file: Path, unique_paths: list[dict]):
        """Generate a summary of all sessions and paths."""

        # Helper to format paths for display
        def format_path(path):
            path_str = str(path)
            home_str = str(Path.home())
            if path_str.startswith(home_str):
                return path_str.replace(home_str, "~", 1)
            return path_str

        lines = []
        lines.append("# Claude Code Session Analysis Summary")
        lines.append(f"\nProject Directory: {format_path(self.project_dir)}")
        lines.append(f"Claude Directory: {self.display_claude_dir}")
        lines.append(f"Total Session Files: {len(self.sessions)}")
        lines.append(f"- Main Sessions: {len(self.sessions) - len(self.subagent_sessions)}")
        lines.append(f"- Subagent Sessions: {len(self.subagent_sessions)}")
        lines.append(f"Total Unique Conversation Paths: {len(unique_paths)}")

        # Extract summaries
        summaries_by_target = self.extract_summaries()

        lines.append("\n## Session Details\n")

        for session_id, data in self.sessions.items():
            paths = data.get("paths", [])
            is_subagent = data.get("is_subagent", False)
            if is_subagent:
                agent_type = data.get("agent_type", "unknown")
                session_type = f"SUBAGENT-{agent_type}"
            else:
                session_type = "MAIN"
            lines.append(f"### Session: {session_id[:8]}... [{session_type}]")
            lines.append(f"- File messages: {len(data['messages'])}")
            lines.append(f"- Conversation paths: {len(paths)}")

            # Add branch summaries if available
            if session_id in summaries_by_target:
                lines.append("- Branch Summaries:")
                for summary in summaries_by_target[session_id]:
                    lines.append(f'  - "{summary["text"]}"')

            if len(paths) > 1:
                lines.append("- Branches:")
                for path in paths:
                    status = "ABANDONED" if path["is_abandoned"] else "ACTIVE"
                    lines.append(f"  - Path {path['path_index']}: {len(path['messages'])} messages [{status}]")

        lines.append("\n## Generated Transcripts\n")
        for path_info in unique_paths:
            session_id = path_info["session_id"]
            status = "ABANDONED" if path_info["is_abandoned"] else "ACTIVE"

            # Get directory name from the path_info if available
            dir_name = path_info.get("directory_name", f"{session_id[:8]}...")

            # List both transcript files in the directory
            lines.append(f"- {dir_name}/")
            lines.append(f"  - transcript.md [{status}] - User-friendly format")
            lines.append(f"  - transcript_extended.md [{status}] - Full extended format")
            lines.append("  - session.jsonl - Source session data")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(
        description="Parse Claude Code sessions and generate transcripts for all conversation paths"
    )
    parser.add_argument("project_dir", help="Project directory (cwd) to analyze")
    parser.add_argument("--output", "-o", help="Output directory for transcripts", default=None)

    args = parser.parse_args()

    # Convert to Path and resolve
    project_dir = Path(args.project_dir).resolve()

    if not project_dir.exists():
        print(f"Error: Project directory does not exist: {project_dir}")
        sys.exit(1)

    output_dir = Path(args.output) if args.output else project_dir / "claude_transcripts"

    print(f"Analyzing Claude Code sessions for: {project_dir}")

    # Create parser and generate transcripts
    parser = ClaudeSessionParser(str(project_dir))
    generated_files = parser.generate_all_transcripts(output_dir)

    print(f"\n{'=' * 80}")
    print(f"Successfully generated {len(generated_files)} files:")
    for f in generated_files:
        display_path = str(f).replace(str(Path.home()), "~")
        print(f"  - {display_path}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
