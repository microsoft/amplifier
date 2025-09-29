#!/usr/bin/env python3
"""
Example transcript builder for Claude Code sessions.

This demonstrates how to project a DAG structure into a linear transcript
that can be displayed or analyzed.
"""

import json
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

    def build_transcript(self) -> str:
        """Build a complete transcript from loaded messages."""
        lines = []
        lines.append("=" * 60)
        lines.append("CLAUDE CODE SESSION TRANSCRIPT")
        lines.append("=" * 60)
        lines.append("")

        for msg in self.messages:
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

    def save_transcript(self, output_path: Path):
        """Save transcript to a text file."""
        transcript = self.build_transcript()
        output_path.write_text(transcript, encoding="utf-8")
        print(f"✅ Transcript saved to: {output_path}")


def main():
    """Example usage."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python example_transcript_builder.py <session.jsonl> [output.txt]")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    # Determine output file
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
    else:
        output_file = input_file.with_suffix(".transcript.txt")

    # Build transcript
    builder = TranscriptBuilder()
    builder.load_session(input_file)
    builder.save_transcript(output_file)

    # Show preview
    print("\n📄 Preview (first 30 lines):")
    print("-" * 40)
    transcript = builder.build_transcript()
    preview_lines = transcript.split("\n")[:30]
    for line in preview_lines:
        print(line)
    print("-" * 40)
    line_count = len(transcript.split("\n"))
    print(f"... [{line_count} total lines]")


if __name__ == "__main__":
    main()
