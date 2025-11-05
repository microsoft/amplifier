#!/usr/bin/env python3
"""
Simple CLI for managing Claude Code memories.
Usage: python memory_cli.py [command] [args]
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import cast

# Add amplifier to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from amplifier.memory import Memory
from amplifier.memory import MemoryCategory
from amplifier.memory import MemoryStore


def main():
    if len(sys.argv) < 2:
        print("Usage: memory_cli.py [add|search|list|clear|stats] [args...]")
        print("\nCommands:")
        print("  add <content> [category]  - Add a new memory")
        print("  search <query>            - Search memories (simple text match)")
        print("  list [n]                  - List n most recent memories (default 10)")
        print("  clear                     - Clear all memories")
        print("  stats                     - Show memory statistics")
        return

    command = sys.argv[1]
    store = MemoryStore()

    if command == "add":
        if len(sys.argv) < 3:
            print("Error: Please provide memory content")
            return

        content = sys.argv[2]
        # Category can be: learning, decision, issue_solved, preference, pattern
        category_str = sys.argv[3] if len(sys.argv) > 3 else "learning"

        # Validate category
        valid_categories = ["learning", "decision", "issue_solved", "preference", "pattern"]
        if category_str not in valid_categories:
            print(f"Warning: Invalid category '{category_str}'. Using 'learning' instead.")
            print(f"Valid categories: {', '.join(valid_categories)}")
            category_str = "learning"

        # Cast to MemoryCategory type for type checking
        category = cast(MemoryCategory, category_str)

        # Create Memory object and add it
        memory = Memory(content=content, category=category, metadata={"source": "CLI", "manual_entry": True})
        stored = store.add_memory(memory)
        print(f"✓ Added memory (ID: {stored.id[:8]}...): {content[:50]}...")

    elif command == "search":
        if len(sys.argv) < 3:
            print("Error: Please provide search query")
            return

        query = " ".join(sys.argv[2:])
        # Simple text search through all memories
        all_memories = store.get_all()
        results = [m for m in all_memories if query.lower() in m.content.lower()]

        if results:
            print(f"Found {len(results)} memories:")
            for i, mem in enumerate(results[:10], 1):  # Limit to 10 results
                print(f"\n{i}. {mem.content}")
                print(f"   Category: {mem.category}")
                print(f"   Added: {mem.timestamp.strftime('%Y-%m-%d %H:%M')}")
                print(f"   Accessed: {mem.accessed_count} times")
        else:
            print("No memories found matching your query")

    elif command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        recent = store.search_recent(limit)

        if recent:
            print(f"Most recent {len(recent)} memories:")
            for i, mem in enumerate(recent, 1):
                print(f"\n{i}. {mem.content}")
                print(f"   Category: {mem.category}")
                print(f"   Added: {mem.timestamp.strftime('%Y-%m-%d %H:%M')}")
                if mem.metadata:
                    print(f"   Metadata: {mem.metadata}")
        else:
            print("No memories found")

    elif command == "clear":
        print("Are you sure you want to clear all memories? (yes/no): ", end="")
        response = input().strip().lower()
        if response == "yes":
            # Clear by reinitializing with empty data
            store._memories = {}
            store._data = {"memories": [], "metadata": {"version": "2.0", "created": datetime.now().isoformat()}}
            store._save_data()
            print("✓ All memories cleared")
        else:
            print("Operation cancelled")

    elif command == "stats":
        all_memories = store.get_all()
        total = len(all_memories)

        if total > 0:
            accessed = sum(1 for m in all_memories if m.accessed_count > 0)
            avg_access = sum(m.accessed_count for m in all_memories) / total

            # Get category statistics
            from collections import Counter

            category_counts = Counter(m.category for m in all_memories)

            print("Memory Statistics:")
            print(f"  Total memories: {total}")
            print(f"  Accessed memories: {accessed} ({accessed * 100 // total}%)")
            print(f"  Average access count: {avg_access:.1f}")

            print("\n  Categories:")
            for category, count in category_counts.most_common():
                print(f"    - {category}: {count} memories")

            # Show metadata stats if available
            metadata_keys = set()
            for mem in all_memories:
                if mem.metadata:
                    metadata_keys.update(mem.metadata.keys())

            if metadata_keys:
                print(f"\n  Metadata keys used: {', '.join(sorted(metadata_keys))}")
        else:
            print("No memories stored yet")

    else:
        print(f"Unknown command: {command}")
        print("Use 'memory_cli.py' without arguments to see usage")


if __name__ == "__main__":
    main()
