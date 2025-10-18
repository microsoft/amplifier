#!/usr/bin/env python3
"""
Visualize REAL Memory Data from Actual Storage

Shows the actual memories extracted from real Claude Code sessions
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from amplifier.memory import MemoryStore
from amplifier.search import MemorySearcher


def show_real_stored_memories():
    """Show actual memories from .data/memory.json"""
    print("\n" + "=" * 70)
    print("REAL MEMORIES FROM ACTUAL STORAGE (.data/memory.json)")
    print("=" * 70)

    memory_file = Path(".data/memory.json")
    if not memory_file.exists():
        print("\n❌ No memory file found at .data/memory.json")
        return

    with open(memory_file) as f:
        data = json.load(f)

    memories = data.get("memories", [])
    metadata = data.get("metadata", {})

    print(f"\n📊 Total memories stored: {metadata.get('count', len(memories))}")
    print(f"📅 Created: {metadata.get('created', 'unknown')}")
    print(f"📅 Last updated: {metadata.get('last_updated', 'unknown')}")

    # Filter to show only memories from real_conversation
    real_conversation_memories = [
        m
        for m in memories
        if m.get("metadata", {}).get("source") == "real_conversation"
    ]

    print(f"\n✨ Memories from REAL conversations: {len(real_conversation_memories)}")
    print(
        f"📝 Other memories (demos/examples): {len(memories) - len(real_conversation_memories)}"
    )

    print("\n" + "=" * 70)
    print("REAL CONVERSATION MEMORIES (Extracted from Claude Code Sessions)")
    print("=" * 70)

    for i, mem in enumerate(real_conversation_memories, 1):
        print(f"\n{i}. [{mem['category'].upper()}] (ID: {mem['id'][:8]}...)")
        print(f"   Content: {mem['content']}")
        print(f"   Importance: {mem['metadata'].get('importance', 'N/A')}")
        print(f"   Tags: {', '.join(mem['metadata'].get('tags', []))}")
        print(f"   Extracted: {mem['metadata'].get('extracted_at', 'unknown')}")
        print(f"   Stored: {mem['timestamp']}")


def show_real_memory_search():
    """Search through real memories"""
    print("\n" + "=" * 70)
    print("SEARCH REAL MEMORIES")
    print("=" * 70)

    store = MemoryStore(data_dir=Path(".data"))
    searcher = MemorySearcher(data_dir=Path(".data"))

    all_memories = store.get_all()

    # Filter to real conversation memories only
    real_memories = [
        m for m in all_memories if m.metadata.get("source") == "real_conversation"
    ]

    print(f"\n🔍 Searching {len(real_memories)} real conversation memories...")

    queries = [
        "modular design",
        "AI development",
        "simplicity philosophy",
    ]

    for query in queries:
        print(f"\n🔍 Query: '{query}'")
        print("-" * 70)

        # Search only real conversation memories
        results = searcher.search(query, real_memories, limit=3)

        if not results:
            print("   No results found")
            continue

        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result.score:.3f} ({result.match_type})")
            print(f"   Category: {result.memory.category}")
            print(f"   Content: {result.memory.content[:100]}...")
            print("   ✨ From REAL Claude Code session!")
            print(
                f"   Extracted: {result.memory.metadata.get('extracted_at', 'unknown')}"
            )


def show_memory_statistics():
    """Show statistics about real memories"""
    print("\n" + "=" * 70)
    print("REAL MEMORY STATISTICS")
    print("=" * 70)

    memory_file = Path(".data/memory.json")
    with open(memory_file) as f:
        data = json.load(f)

    memories = data.get("memories", [])

    # Separate real vs demo memories
    real_memories = [
        m
        for m in memories
        if m.get("metadata", {}).get("source") == "real_conversation"
    ]
    demo_memories = [
        m
        for m in memories
        if m.get("metadata", {}).get("source") != "real_conversation"
    ]

    print("\n📊 Memory Breakdown:")
    print(f"   Total: {len(memories)}")
    print(f"   ✅ Real (from sessions): {len(real_memories)}")
    print(f"   📝 Demo/Example: {len(demo_memories)}")

    # Category breakdown for real memories
    categories = {}
    for mem in real_memories:
        cat = mem.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    print("\n📁 Real Memory Categories:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   {cat}: {count}")

    # Importance distribution
    importances = [
        m.get("metadata", {}).get("importance", 0)
        for m in real_memories
        if "importance" in m.get("metadata", {})
    ]

    if importances:
        avg_importance = sum(importances) / len(importances)
        print(f"\n⭐ Average Importance: {avg_importance:.2f}")
        print(f"   Highest: {max(importances):.2f}")
        print(f"   Lowest: {min(importances):.2f}")

    # Most common tags
    all_tags = []
    for mem in real_memories:
        all_tags.extend(mem.get("metadata", {}).get("tags", []))

    if all_tags:
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        print("\n🏷️  Most Common Tags:")
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]:
            print(f"   {tag}: {count}")


def main():
    """Run complete visualization of REAL memory data"""
    print("\n" + "=" * 70)
    print("REAL MEMORY DATA VISUALIZATION")
    print("=" * 70)
    print("\nShowing ACTUAL memories from Claude Code sessions")
    print("(NOT demo/dummy data)")

    # Show stored memories
    show_real_stored_memories()

    # Show statistics
    show_memory_statistics()

    # Show search
    show_real_memory_search()

    print("\n" + "=" * 70)
    print("✨ COMPLETE - ALL DATA IS REAL")
    print("=" * 70)
    print("\nAll memories shown above were extracted from:")
    print("  ~/.claude/projects/-Users-max-Documents-GitHub-amplifier/")
    print("  (Your actual Claude Code session files)")
    print("\nLook for 'source: real_conversation' in the metadata!")


if __name__ == "__main__":
    main()
