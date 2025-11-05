#!/usr/bin/env python3
"""
Transcript Formatter Module - Convert DAG branches to markdown transcripts.

This module formats conversation data into readable markdown transcripts
with proper attribution and formatting.
"""

import json
import logging
from pathlib import Path
from typing import Any

from dag_loader import Message
from dag_loader import SessionData
from dag_navigator import Branch
from dag_navigator import ConversationTree

logger = logging.getLogger(__name__)


class TranscriptFormatter:
    """Format conversation data into markdown transcripts."""

    def __init__(self, session_data: SessionData, tree: ConversationTree):
        self.session_data = session_data
        self.tree = tree
        self.tool_map: dict[str, dict[str, Any]] = {}
        self._build_tool_map()

    def _build_tool_map(self):
        """Build a map of tool invocations for quick lookup."""
        for msg in self.session_data.messages.values():
            # Extract tool invocations
            for tool in msg.get_tool_calls():
                self.tool_map[tool["id"]] = {"name": tool["name"], "input": tool["input"], "message_uuid": msg.uuid}

            # Link results to invocations
            for result in msg.get_tool_results():
                tool_id = result["tool_use_id"]
                if tool_id in self.tool_map:
                    self.tool_map[tool_id]["result"] = result["content"]

    def get_attribution(self, msg: Message) -> str:
        """Get attribution label for a message."""
        # Tool results are always System
        if msg.is_tool_result():
            return "System"

        # Check if this is a legacy subagent session (entire session is subagent conversation)
        if hasattr(self.session_data, "session_type") and self.session_data.session_type == "legacy_subagent":
            if msg.type == "user":
                return "Claude (delegating)"
            if msg.type == "assistant":
                agent_name = self.session_data.subagent_name or "Unknown Agent"
                return f"Subagent ({agent_name})"

        # Check if this specific message is part of a modern sidechain
        if msg.is_sidechain:
            if msg.type == "user":
                return "Claude (delegating)"
            if msg.type == "assistant":
                # Try to get agent name from session data if available
                agent_name = getattr(self.session_data, "subagent_name", None) or "Unknown Agent"
                return f"Subagent ({agent_name})"

        # Regular session attribution
        if msg.type == "user":
            if msg.user_type == "external" or msg.user_type is None:
                return "User"
            return "System"

        if msg.type == "assistant":
            return "Agent"

        return "System"

    def format_simple_transcript(self, include_system: bool = False) -> str:
        """Format a simple linear transcript.

        Args:
            include_system: Whether to include system messages

        Returns:
            Formatted markdown transcript
        """
        lines = []

        # Add header
        lines.extend(self._format_header())
        lines.append("")

        # Add metadata
        lines.extend(self._format_metadata())
        lines.append("")

        # Add conversation
        lines.append("## Conversation")
        lines.append("")

        # Get linear flow
        from dag_navigator import DAGNavigator

        navigator = DAGNavigator(self.session_data)
        navigator.tree = self.tree
        flow = navigator.get_linear_flow()

        for msg_uuid in flow:
            msg = self.session_data.get_message(msg_uuid)
            if not msg:
                continue

            # Skip system messages if not included
            attribution = self.get_attribution(msg)
            if not include_system and attribution == "System":
                continue

            # Format the message
            lines.extend(self._format_message(msg))
            lines.append("")

        return "\n".join(lines)

    def format_extended_transcript(self, include_system: bool = True) -> str:
        """Format an extended transcript with full details.

        Args:
            include_system: Whether to include system messages

        Returns:
            Formatted markdown transcript with full content
        """
        lines = []

        # Add header
        lines.extend(self._format_header())
        lines.append("")

        # Add metadata
        lines.extend(self._format_metadata())
        lines.append("")

        # Add branch summary if multiple branches
        if self.tree.count_branches() > 1:
            lines.append("## Branch Structure")
            lines.append("")
            lines.extend(self._format_branch_summary())
            lines.append("")

        # Add main conversation
        lines.append("## Main Conversation")
        lines.append("")

        if self.tree.main_branch:
            lines.extend(self._format_branch(self.tree.main_branch, include_system))
        else:
            # Fallback to linear flow
            from dag_navigator import DAGNavigator

            navigator = DAGNavigator(self.session_data)
            navigator.tree = self.tree
            flow = navigator.get_linear_flow()

            for msg_uuid in flow:
                msg = self.session_data.get_message(msg_uuid)
                if not msg:
                    continue

                attribution = self.get_attribution(msg)
                if not include_system and attribution == "System":
                    continue

                lines.extend(self._format_message_extended(msg))
                lines.append("")

        # Add sidechains
        sidechains = [b for b in self.tree.branches.values() if b.is_sidechain]
        if sidechains:
            lines.append("## Sidechains")
            lines.append("")

            for sidechain in sidechains:
                lines.append(f"### Sidechain: {sidechain.branch_id}")
                lines.append("")
                lines.extend(self._format_branch(sidechain, include_system))
                lines.append("")

        return "\n".join(lines)

    def _format_header(self) -> list[str]:
        """Format the transcript header."""
        return ["# Claude Code Session Transcript"]

    def _format_metadata(self) -> list[str]:
        """Format session metadata."""
        lines = ["## Metadata"]

        # File info
        if "file_path" in self.session_data.metadata:
            file_path = Path(self.session_data.metadata["file_path"])
            lines.append(f"- **Session ID**: {file_path.stem}")

            # Extract project name from path
            project_dir = file_path.parent.name
            if project_dir.startswith("-"):
                project_name = project_dir[1:].replace("-", "/")
                lines.append(f"- **Project**: {project_name}")

        # Timestamps
        if "modified_time" in self.session_data.metadata:
            dt = self.session_data.metadata["modified_time"]
            lines.append(f"- **Modified**: {dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")

        # Add session type if not regular
        if hasattr(self.session_data, "session_type") and self.session_data.session_type != "regular":
            # Get the string value of the enum
            session_type_str = str(self.session_data.session_type).split(".")[-1].replace("_", " ").title()
            lines.append(f"- **Session Type**: {session_type_str}")
            if self.session_data.subagent_name:
                lines.append(f"- **Subagent**: {self.session_data.subagent_name}")

        # Statistics
        lines.append(f"- **Total messages**: {self.session_data.count_messages()}")
        lines.append(f"- **Branches**: {self.tree.count_branches()}")

        if self.tree.count_sidechains() > 0:
            lines.append(f"- **Sidechains**: {self.tree.count_sidechains()}")

        return lines

    def _format_branch_summary(self) -> list[str]:
        """Format a summary of branch structure."""
        lines = []

        for branch in self.tree.branches.values():
            indent = "  " if branch.is_sidechain else ""
            branch_type = "Sidechain" if branch.is_sidechain else "Branch"
            lines.append(f"{indent}- **{branch_type}** `{branch.branch_id}`: {branch.count_messages()} messages")

            if branch.child_branches:
                lines.append(f"{indent}  - Children: {', '.join(branch.child_branches)}")

        return lines

    def _format_branch(self, branch: Branch, include_system: bool) -> list[str]:
        """Format all messages in a branch."""
        lines = []

        for msg_uuid in branch.messages:
            msg = self.session_data.get_message(msg_uuid)
            if not msg:
                continue

            attribution = self.get_attribution(msg)
            if not include_system and attribution == "System":
                continue

            lines.extend(self._format_message_extended(msg))
            lines.append("")

        return lines

    def _format_message(self, msg: Message) -> list[str]:
        """Format a single message in simple format."""
        lines = []
        attribution = self.get_attribution(msg)

        # Format timestamp if available
        timestamp = ""
        if msg.timestamp:
            timestamp = f" · {msg.timestamp.strftime('%H:%M:%S')}"

        # Message header
        lines.append(f"- **{attribution}**{timestamp}")

        # Extract and format content
        content = self._extract_simple_content(msg)
        if content:
            # Indent content
            for line in content.split("\n"):
                lines.append(f"  {line}")

        return lines

    def _format_message_extended(self, msg: Message) -> list[str]:
        """Format a single message with extended details."""
        lines = []
        attribution = self.get_attribution(msg)

        # Format timestamp if available
        timestamp = ""
        if msg.timestamp:
            timestamp = f" · {msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

        # Message header with line number
        header = f"### [{msg.line_number:04d}] {attribution}{timestamp}"
        if msg.is_sidechain:
            header += " (SIDECHAIN)"
        lines.append(header)
        lines.append("")

        # Extract and format full content
        content = self._extract_full_content(msg)
        if content:
            lines.append(content)

        return lines

    def _extract_simple_content(self, msg: Message) -> str:
        """Extract simplified content from a message."""
        content = msg.content

        if isinstance(content, str):
            # Simple string content
            return self._truncate(content, 500)

        if isinstance(content, dict):
            # Complex content with parts
            parts = []

            if "content" in content:
                items = content["content"]
                if isinstance(items, list):
                    for item in items:
                        part = self._format_content_item_simple(item)
                        if part:
                            parts.append(part)
                elif isinstance(items, str):
                    parts.append(self._truncate(items, 500))

            return "\n".join(parts) if parts else ""

        return ""

    def _extract_full_content(self, msg: Message) -> str:
        """Extract full content from a message."""
        content = msg.content

        if isinstance(content, str):
            # Simple string content
            return content

        if isinstance(content, dict):
            # Complex content with parts
            parts = []

            if "content" in content:
                items = content["content"]
                if isinstance(items, list):
                    for item in items:
                        part = self._format_content_item_full(item)
                        if part:
                            parts.append(part)
                elif isinstance(items, str):
                    parts.append(items)

            return "\n\n".join(parts) if parts else ""

        return ""

    def _format_content_item_simple(self, item: dict) -> str:
        """Format a content item in simple format."""
        if not isinstance(item, dict):
            return ""

        item_type = item.get("type")

        if item_type == "text":
            text = item.get("text", "")
            return self._truncate(text, 500)

        if item_type == "tool_use":
            name = item.get("name", "unknown")
            input_data = item.get("input", {})

            # Special handling for Task tool (subagent invocations)
            if name == "Task" and "subagent_type" in input_data:
                subagent = input_data.get("subagent_type", "unknown")
                task = input_data.get("prompt", input_data.get("task", ""))
                task_preview = self._truncate(task, 100)
                return f"**[Task: {subagent}]** {task_preview}"

            # Format other tools with input args
            args_summary = self._format_tool_args_summary(input_data)
            return f"**Tool Call**: `{name}` ({args_summary})"

        if item_type == "tool_result":
            content = item.get("content", "")
            if isinstance(content, str):
                result = self._truncate(content, 200)
            else:
                result = "[Complex result]"
            return f"**Tool Result**: {result}"

        return ""

    def _format_content_item_full(self, item: dict) -> str:
        """Format a content item with full details."""
        if not isinstance(item, dict):
            return ""

        item_type = item.get("type")

        if item_type == "text":
            return item.get("text", "")

        if item_type == "tool_use":
            name = item.get("name", "unknown")
            input_data = item.get("input", {})

            # Check if it's a Task tool (sub-agent)
            if name == "Task" and "subagent_type" in input_data:
                subagent = input_data.get("subagent_type", "unknown")
                task = input_data.get("prompt", input_data.get("task", "No task description"))
                return f"**Sub-agent Task**\n- Agent: `{subagent}`\n- Task: {task}"

            # Format as code block for complex inputs
            if input_data:
                formatted_input = json.dumps(input_data, indent=2)
                return f"**Tool Call**: `{name}`\n```json\n{formatted_input}\n```"
            return f"**Tool Call**: `{name}`"

        if item_type == "tool_result":
            content = item.get("content", "")
            if isinstance(content, str):
                # Check if it's JSON
                try:
                    parsed = json.loads(content)
                    formatted = json.dumps(parsed, indent=2)
                    return f"**Tool Result**:\n```json\n{formatted}\n```"
                except (json.JSONDecodeError, TypeError, ValueError):
                    # Not JSON, return as text
                    if len(content) > 1000:
                        return f"**Tool Result** (truncated):\n```\n{content[:1000]}...\n```"
                    return f"**Tool Result**:\n```\n{content}\n```"
            else:
                return "**Tool Result**: [Complex object]"

        return ""

    def _format_tool_args_summary(self, input_data: dict) -> str:
        """Format a summary of tool arguments."""
        if not input_data:
            return "no args"

        # Special handling for common tools
        if "command" in input_data:
            cmd = input_data["command"]
            if len(cmd) > 50:
                cmd = cmd[:50] + "..."
            return f'command: "{cmd}"'

        if "file_path" in input_data:
            return f"file: {Path(input_data['file_path']).name}"

        if "pattern" in input_data:
            return f'pattern: "{input_data["pattern"]}"'

        # Generic summary
        keys = list(input_data.keys())[:3]
        return f"{len(input_data)} args: {', '.join(keys)}"

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text to maximum length."""
        if len(text) <= max_len:
            return text
        return text[:max_len] + "..."

    def export_sidechains(self, output_dir: Path):
        """Export sidechains to separate files.

        Args:
            output_dir: Directory to write sidechain files
        """
        sidechains = [b for b in self.tree.branches.values() if b.is_sidechain]

        if not sidechains:
            logger.info("No sidechains to export")
            return

        # Create sidechains directory
        sidechains_dir = output_dir / "sidechains"
        sidechains_dir.mkdir(parents=True, exist_ok=True)

        for sidechain in sidechains:
            # Create directory for this sidechain
            sidechain_dir = sidechains_dir / sidechain.branch_id
            sidechain_dir.mkdir(parents=True, exist_ok=True)

            # Format sidechain transcript
            lines = [f"# Sidechain: {sidechain.branch_id}", ""]
            lines.extend(self._format_branch(sidechain, include_system=True))

            # Write transcript
            transcript_file = sidechain_dir / "transcript.md"
            transcript_file.write_text("\n".join(lines), encoding="utf-8")

            logger.info(f"Exported sidechain to {transcript_file}")
