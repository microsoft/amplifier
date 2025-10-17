#!/usr/bin/env python3
"""
Quick demo of Amplifier's memory system
"""

import asyncio
from amplifier.memory import MemoryStore, Memory
from amplifier.search import MemorySearcher


async def main():
    print("🚀 Amplifier Memory System Demo\n")
    print("=" * 60)

    # Initialize modules
    print("\n1️⃣  Initializing memory system...")
    store = MemoryStore()
    searcher = MemorySearcher()

    # Add some example memories
    print("\n2️⃣  Adding example memories...")

    memories = [
        Memory(
            content="User prefers dark mode for coding environments",
            category="preference",
            metadata={"source": "user-settings"},
        ),
        Memory(
            content="Claude Code API has rate limit of 100 requests per minute",
            category="learning",
            metadata={"source": "api-docs"},
        ),
        Memory(
            content="Successfully resolved async/await pattern for database connections",
            category="issue_solved",
            metadata={"source": "debugging-session"},
        ),
        Memory(
            content="Team decided to use TypeScript for all frontend components",
            category="decision",
            metadata={"source": "team-meeting"},
        ),
    ]

    for memory in memories:
        _stored = store.add_memory(memory)
        print(f"   ✅ Added: {memory.content[:50]}...")

    # Show statistics
    print("\n3️⃣  Memory Statistics:")
    all_memories = store.get_all()
    print(f"   📊 Total memories: {len(all_memories)}")

    categories = {}
    for mem in all_memories:
        categories[mem.category] = categories.get(mem.category, 0) + 1

    for category, count in categories.items():
        print(f"   📁 {category}: {count}")

    # Search memories
    print("\n4️⃣  Testing semantic search...")
    queries = [
        "API limits and rate throttling",
        "user interface preferences",
        "database connection patterns",
    ]

    for query in queries:
        print(f"\n   🔍 Query: '{query}'")
        results = searcher.search(query, all_memories, limit=2)

        if results:
            for i, result in enumerate(results, 1):
                print(
                    f"      {i}. [{result.score:.2f}] {result.memory.content[:60]}..."
                )
        else:
            print("      No results found")

    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")
    print("\n💡 Next steps:")
    print('   • Explore: make knowledge-query Q="your question"')
    print("   • Extract knowledge: make knowledge-update")
    print("   • See all commands: make help")
    print()


if __name__ == "__main__":
    asyncio.run(main())
