#!/usr/bin/env python3
"""
Diagnostic tool to inspect compact operations in Claude Code session files.

This tool helps understand:
- Where compact boundaries occur
- What compact-related messages exist
- The structure around continuation messages
- References between compact operations and previous sessions
"""

import json
import sys
from pathlib import Path


def inspect_compact_operations(session_file: Path) -> None:
    """Inspect compact operations in a session file."""
    print(f"\n{'=' * 80}")
    print(f"Inspecting: {session_file.name}")
    print(f"{'=' * 80}\n")

    messages = []
    with open(session_file, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                data["_line_number"] = line_num
                messages.append(data)
            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_num}: {e}")
                continue

    print(f"Total messages: {len(messages)}\n")

    # Find compact-related messages
    compact_boundaries = []
    compact_summaries = []
    system_compact_messages = []
    continuation_messages = []

    for msg in messages:
        # Check for compact boundary
        if msg.get("type") == "system" and msg.get("subtype") == "compact_boundary":
            compact_boundaries.append(msg)

        # Check for compact summary flag
        if msg.get("isCompactSummary"):
            compact_summaries.append(msg)

        # Check for any system message mentioning compact
        if msg.get("type") == "system":
            content = str(msg.get("message", {}))
            if "compact" in content.lower():
                system_compact_messages.append(msg)

        # Check for continuation messages
        if msg.get("type") == "user":
            content = msg.get("message", {})
            if isinstance(content, dict):
                content_str = str(content.get("content", ""))
            else:
                content_str = str(content)

            if "session is being continued" in content_str.lower() or "continuing from" in content_str.lower():
                continuation_messages.append(msg)

    # Report findings
    print(f"Compact Boundaries: {len(compact_boundaries)}")
    print(f"Compact Summaries: {len(compact_summaries)}")
    print(f"System Compact Messages: {len(system_compact_messages)}")
    print(f"Continuation Messages: {len(continuation_messages)}\n")

    # Show compact boundaries
    if compact_boundaries:
        print("\n" + "=" * 80)
        print("COMPACT BOUNDARIES")
        print("=" * 80)
        for cb in compact_boundaries:
            print(f"\nLine {cb['_line_number']}:")
            print(f"  UUID: {cb.get('uuid')}")
            print(f"  Parent UUID: {cb.get('parentUuid')}")
            print(f"  Session ID: {cb.get('sessionId')}")
            print(f"  Type: {cb.get('type')}")
            print(f"  Subtype: {cb.get('subtype')}")

    # Show compact summaries
    if compact_summaries:
        print("\n" + "=" * 80)
        print("COMPACT SUMMARIES")
        print("=" * 80)
        for cs in compact_summaries:
            print(f"\nLine {cs['_line_number']}:")
            print(f"  UUID: {cs.get('uuid')}")
            print(f"  Parent UUID: {cs.get('parentUuid')}")
            print(f"  Session ID: {cs.get('sessionId')}")
            print(f"  Type: {cs.get('type')}")
            print(f"  isCompactSummary: {cs.get('isCompactSummary')}")

    # Show system compact messages
    if system_compact_messages:
        print("\n" + "=" * 80)
        print("SYSTEM COMPACT MESSAGES")
        print("=" * 80)
        for scm in system_compact_messages:
            print(f"\nLine {scm['_line_number']}:")
            print(f"  UUID: {scm.get('uuid')}")
            print(f"  Parent UUID: {scm.get('parentUuid')}")
            print(f"  Type: {scm.get('type')}")
            print(f"  Subtype: {scm.get('subtype')}")
            msg_content = scm.get("message", {})
            if isinstance(msg_content, dict):
                content_str = str(msg_content.get("content", ""))[:200]
            else:
                content_str = str(msg_content)[:200]
            print(f"  Content preview: {content_str}...")

    # Show continuation messages
    if continuation_messages:
        print("\n" + "=" * 80)
        print("CONTINUATION MESSAGES")
        print("=" * 80)
        for cm in continuation_messages:
            print(f"\nLine {cm['_line_number']}:")
            print(f"  UUID: {cm.get('uuid')}")
            print(f"  Parent UUID: {cm.get('parentUuid')}")
            print(f"  Session ID: {cm.get('sessionId')}")
            print(f"  Type: {cm.get('type')}")
            msg_content = cm.get("message", {})
            if isinstance(msg_content, dict):
                content = msg_content.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_result":
                            tool_content = item.get("content", "")
                            print(f"  Tool result content preview: {tool_content[:300]}...")
                        elif isinstance(item, dict) and item.get("type") == "text":
                            text = item.get("text", "")
                            print(f"  Text content: {text[:300]}...")
                elif isinstance(content, str):
                    print(f"  Content: {content[:300]}...")
            else:
                print(f"  Content: {str(msg_content)[:300]}...")

    # Check first 10 messages
    print("\n" + "=" * 80)
    print("FIRST 10 MESSAGES")
    print("=" * 80)
    for i, msg in enumerate(messages[:10], 1):
        print(f"\n{i}. Line {msg['_line_number']}:")
        print(f"  UUID: {msg.get('uuid')}")
        print(f"  Parent UUID: {msg.get('parentUuid')}")
        print(f"  Type: {msg.get('type')}")
        print(f"  Session ID: {msg.get('sessionId')}")
        if msg.get("isCompactSummary"):
            print("  isCompactSummary: True")
        if msg.get("subtype"):
            print(f"  Subtype: {msg.get('subtype')}")

    # Check roots (messages with parentUuid = null)
    roots = [m for m in messages if m.get("parentUuid") is None]
    print("\n" + "=" * 80)
    print(f"ROOT MESSAGES (parentUuid = null): {len(roots)}")
    print("=" * 80)
    for root in roots[:10]:  # Show first 10 roots
        print(f"\nLine {root['_line_number']}:")
        print(f"  UUID: {root.get('uuid')}")
        print(f"  Type: {root.get('type')}")
        print(f"  Session ID: {root.get('sessionId')}")
        if root.get("subtype"):
            print(f"  Subtype: {root.get('subtype')}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python inspect_compact.py <session_file>")
        print("\nExample:")
        print("  python inspect_compact.py ~/.claude/projects/my-project/session-id.jsonl")
        sys.exit(1)

    session_file = Path(sys.argv[1]).expanduser()
    if not session_file.exists():
        print(f"Error: File not found: {session_file}")
        sys.exit(1)

    inspect_compact_operations(session_file)


if __name__ == "__main__":
    main()
