#!/usr/bin/env python3
"""
Simple example parser for Claude Code sessions.

This demonstrates the minimal approach to parsing Claude Code JSONL files
and building a basic DAG structure.
"""

import json
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


def main():
    """Example usage."""
    import sys

    if len(sys.argv) != 2:
        print("Usage: python example_parser.py <session.jsonl>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    # Parse and analyze
    parser = SimpleParser()
    parser.parse_file(file_path)
    parser.print_summary()

    # Show first few messages
    flow = parser.get_conversation_flow()
    print("\n💬 First 3 messages:")
    for msg in flow[:3]:
        msg_type = msg.get("type", "unknown")
        print(f"  [{msg['line_number']:3d}] {msg_type}: {msg['uuid'][:8]}...")


if __name__ == "__main__":
    main()
