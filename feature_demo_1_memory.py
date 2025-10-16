#!/usr/bin/env python3
"""
Feature Demo #1: Memory System
Shows how Amplifier stores and retrieves memories across sessions
"""
import asyncio
from datetime import datetime
from amplifier.memory import MemoryStore, Memory


async def main():
    print("\n" + "=" * 70)
    print("🧠 FEATURE #1: MEMORY SYSTEM")
    print("=" * 70)

    print("\n📋 What is the Memory System?")
    print("   Amplifier remembers important information across sessions:")
    print("   • Preferences - Your coding style, tool choices")
    print("   • Learnings - API limits, framework quirks, gotchas")
    print("   • Decisions - Why you chose approach X over Y")
    print("   • Solutions - How you fixed tricky bugs")
    print("   • Patterns - Recurring themes in your work")

    # Initialize
    print("\n" + "-" * 70)
    print("🔧 Initializing memory store...")
    store = MemoryStore()

    # Show existing memories
    existing = store.get_all()
    print(f"📊 Current database: {len(existing)} memories")

    # Add new memories with different categories
    print("\n" + "-" * 70)
    print("➕ Adding new memories (watch how different types are stored)...\n")

    new_memories = [
        {
            "content": "Always use async/await for database operations - learned from performance issues",
            "category": "learning",
            "metadata": {"source": "debugging", "importance": "high"}
        },
        {
            "content": "User prefers 2-space indentation for JavaScript, 4-space for Python",
            "category": "preference",
            "metadata": {"source": "code-review"}
        },
        {
            "content": "Decided to use PostgreSQL over MongoDB for better transaction support",
            "category": "decision",
            "metadata": {"source": "architecture-meeting", "date": "2025-10-15"}
        },
        {
            "content": "Fixed JWT token expiration bug by adding timezone awareness to datetime comparisons",
            "category": "issue_solved",
            "metadata": {"source": "bug-fix", "severity": "critical"}
        },
        {
            "content": "Pattern: Always validate user input on both client and server side",
            "category": "pattern",
            "metadata": {"source": "security-review"}
        }
    ]

    for mem_data in new_memories:
        memory = Memory(**mem_data)
        stored = store.add_memory(memory)
        print(f"   ✅ [{memory.category:12}] {memory.content[:60]}...")
        print(f"      ID: {stored.id}")
        print(f"      Metadata: {stored.metadata}")
        print()

    # Show statistics
    print("-" * 70)
    print("📈 Memory Statistics by Category:\n")

    all_memories = store.get_all()
    categories = {}
    for mem in all_memories:
        categories[mem.category] = categories.get(mem.category, 0) + 1

    for category, count in sorted(categories.items()):
        print(f"   📁 {category:15} : {count:3} memories")

    # Demonstrate retrieval
    print("\n" + "-" * 70)
    print("🔍 Retrieving specific memories...\n")

    # Get memories by category
    preferences = [m for m in all_memories if m.category == "preference"]
    print(f"   Preferences ({len(preferences)}):")
    for pref in preferences[-2:]:  # Show last 2
        print(f"      • {pref.content}")

    learnings = [m for m in all_memories if m.category == "learning"]
    print(f"\n   Learnings ({len(learnings)}):")
    for learn in learnings[-2:]:  # Show last 2
        print(f"      • {learn.content}")

    # Show access counting
    print("\n" + "-" * 70)
    print("📊 Access Tracking (memories track how often they're used):\n")

    sample_memories = all_memories[-3:]  # Get last 3
    for mem in sample_memories:
        print(f"   Memory: {mem.content[:50]}...")
        print(f"   Accessed: {mem.accessed_count} times")
        print(f"   Last access: {mem.timestamp}")
        print()

    # Demonstrate persistence
    print("-" * 70)
    print("💾 Persistence:\n")
    print(f"   Storage location: {store.data_file}")
    print(f"   Format: JSON (human-readable)")
    print(f"   Auto-saves: After every operation")
    print(f"   Cross-session: YES - memories survive restarts")

    print("\n" + "=" * 70)
    print("✅ Memory System Demo Complete!")
    print("=" * 70)

    print("\n💡 Key Takeaways:")
    print("   1. Memories persist across sessions (saved to .data/memory.json)")
    print("   2. Different categories help organize knowledge")
    print("   3. Metadata adds context to each memory")
    print("   4. Access tracking shows which memories are most useful")
    print("   5. Human-readable JSON for easy inspection/editing")

    print("\n🔍 Try this yourself:")
    print("   • View stored memories: cat .data/memory.json | jq")
    print("   • Add your own: Edit demo_amplifier.py")
    print("   • Query memories: Next feature demo! ⬇️")
    print()


if __name__ == "__main__":
    asyncio.run(main())
