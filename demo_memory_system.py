#!/usr/bin/env python3
"""
Real Working Example: Amplifier Memory System

This script demonstrates the complete memory lifecycle:
1. EXTRACT - AI extracts memories from conversation
2. STORE - Memories saved to .data/memory.json
3. INDEX - Semantic embeddings created for search
4. SEARCH - Find memories using semantic similarity
5. USE - Apply memories to new tasks
"""

import asyncio
import sys
from pathlib import Path

# Add amplifier to path
sys.path.insert(0, str(Path(__file__).parent))

from amplifier.extraction import MemoryExtractor
from amplifier.memory import Memory, MemoryStore
from amplifier.search import MemorySearcher


async def demo_extraction():
    """Step 1: Extract memories from a conversation"""
    print("\n" + "=" * 70)
    print("STEP 1: EXTRACT MEMORIES FROM CONVERSATION")
    print("=" * 70)

    # Simulate a conversation about a project decision
    conversation = """
USER: I'm working on the authentication system. Should we use JWT or session-based auth?

ASSISTANT: For your API-first architecture, JWT makes more sense because:
- Stateless authentication works better for microservices
- Mobile apps can store tokens easily
- No server-side session storage needed

USER: Good point. I'll go with JWT. Also, I prefer using Redis for caching.

ASSISTANT: Redis is an excellent choice. I'll remember that you prefer Redis for caching.

USER: We found that using async/await for database calls improved performance by 40%.

ASSISTANT: That's a significant improvement! I'll note that async database calls gave you a 40% performance boost.
"""

    print(f"\nConversation text ({len(conversation)} chars):")
    print("-" * 70)
    print(conversation[:200] + "..." if len(conversation) > 200 else conversation)

    print("\n🤖 Calling Claude Code SDK to extract memories...")
    print("   (This uses AI to identify what's worth remembering)")

    try:
        extractor = MemoryExtractor()

        # Extract memories using AI
        memories = await extractor.extract_memories(
            text=conversation, context={"source": "architecture_discussion"}
        )

        print(f"\n✅ Extracted {len(memories)} memories:\n")
        for i, memory in enumerate(memories, 1):
            print(f"{i}. [{memory.category.upper()}]")
            print(f"   {memory.content}")
            print()

        return memories

    except RuntimeError as e:
        print(f"\n⚠️  Extraction requires Claude Code SDK: {e}")
        print("\n💡 Installing: npm install -g @anthropic-ai/claude-code")
        print("   Then: pip install claude-code-sdk\n")

        # Return mock memories for demo
        print("📝 Using mock memories for demo...\n")
        return [
            Memory(
                content="User prefers JWT for authentication in API-first architectures",
                category="preference",
                metadata={"source": "architecture_discussion"},
            ),
            Memory(
                content="User prefers Redis for caching",
                category="preference",
                metadata={"source": "architecture_discussion"},
            ),
            Memory(
                content="Async database calls improved performance by 40%",
                category="learning",
                metadata={"source": "architecture_discussion"},
            ),
        ]


def demo_storage(memories: list[Memory]):
    """Step 2: Store memories in JSON file"""
    print("\n" + "=" * 70)
    print("STEP 2: STORE MEMORIES")
    print("=" * 70)

    # Initialize storage
    store = MemoryStore(data_dir=Path(".data"))

    print(f"\n📂 Storage location: {store.data_file}")
    print(f"📊 Current count: {len(store.get_all())} memories")

    # Store each memory
    print("\n💾 Storing new memories...")
    stored_memories = []
    for memory in memories:
        stored = store.add_memory(memory)
        stored_memories.append(stored)
        print(f"   ✓ Stored: {stored.id[:8]}... - {stored.content[:50]}...")

    print(f"\n✅ Total memories now: {len(store.get_all())}")

    return store, stored_memories


def demo_indexing(store: MemoryStore):
    """Step 3: Create semantic embeddings for search"""
    print("\n" + "=" * 70)
    print("STEP 3: INDEX MEMORIES (Create Semantic Embeddings)")
    print("=" * 70)

    try:
        # Initialize searcher (loads embedding model)
        searcher = MemorySearcher(data_dir=Path(".data"))

        if searcher.model is None:
            print("\n⚠️  Semantic search requires sentence-transformers")
            print("💡 Install: pip install sentence-transformers")
            print("   (Will use keyword search as fallback)")
            return searcher

        print(f"\n🧠 Loaded embedding model: {searcher.model_name}")

        # Generate embeddings for all memories
        memories = store.get_all()
        print(f"📊 Generating embeddings for {len(memories)} memories...")

        indexed = 0
        for memory in memories:
            embedding = searcher.generate_embedding(memory.content)
            if embedding:
                searcher.store_embedding(memory.id, embedding)
                indexed += 1

        print(f"✅ Indexed {indexed} memories with semantic embeddings")

        return searcher

    except ImportError:
        print("\n⚠️  sentence-transformers not installed")
        print("💡 Install: pip install sentence-transformers")
        print("   (Will use keyword search as fallback)")
        return MemorySearcher(data_dir=Path(".data"))


def demo_search(store: MemoryStore, searcher: MemorySearcher):
    """Step 4: Search memories using semantic similarity"""
    print("\n" + "=" * 70)
    print("STEP 4: SEARCH MEMORIES")
    print("=" * 70)

    queries = [
        "authentication methods",
        "caching solutions",
        "performance improvements",
    ]

    memories = store.get_all()

    for query in queries:
        print(f"\n🔍 Query: '{query}'")
        print("-" * 70)

        results = searcher.search(query, memories, limit=3)

        if not results:
            print("   No results found")
            continue

        for i, result in enumerate(results, 1):
            print(f"\n{i}. Score: {result.score:.3f} ({result.match_type})")
            print(f"   Category: {result.memory.category}")
            print(f"   Content: {result.memory.content}")
            if result.memory.metadata:
                print(f"   Metadata: {result.memory.metadata}")


def demo_usage(store: MemoryStore, searcher: MemorySearcher):
    """Step 5: Use memories to inform new tasks"""
    print("\n" + "=" * 70)
    print("STEP 5: USE MEMORIES IN NEW TASKS")
    print("=" * 70)

    # Simulate a new task
    new_task = "Design a caching layer for the API"

    print(f"\n📋 New Task: '{new_task}'")
    print("-" * 70)

    # Search for relevant memories
    memories = store.get_all()
    results = searcher.search(new_task, memories, limit=5)

    if not results:
        print("\n⚠️  No relevant memories found")
        return

    print(f"\n🧠 Found {len(results)} relevant memories:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. [{result.memory.category.upper()}] (score: {result.score:.3f})")
        print(f"   {result.memory.content}")

    print("\n💡 Using these memories to inform the design:")
    print("-" * 70)
    print("Based on past learnings:")
    print("• User prefers Redis for caching")
    print("• Async calls improved performance by 40%")
    print("• API-first architecture suggests distributed caching")
    print("\n✨ Recommended approach:")
    print("   → Use Redis for distributed caching")
    print("   → Implement async cache operations")
    print("   → Design stateless cache keys for microservices")


def demo_storage_format():
    """Bonus: Show the actual JSON storage format"""
    print("\n" + "=" * 70)
    print("BONUS: STORAGE FORMAT")
    print("=" * 70)

    memory_file = Path(".data/memory.json")

    if not memory_file.exists():
        print(f"\n⚠️  No memory file found at {memory_file}")
        return

    print(f"\n📄 File: {memory_file}")
    print("-" * 70)

    import json

    with open(memory_file) as f:
        data = json.load(f)

    # Show structure
    print("\nStructure:")
    print(f"  memories: {len(data.get('memories', []))} items")
    print(f"  metadata: {list(data.get('metadata', {}).keys())}")

    # Show one example memory
    if data.get("memories"):
        print("\nExample memory:")
        example = data["memories"][0]
        print(json.dumps(example, indent=2))


async def main():
    """Run the complete demo"""
    print("\n" + "=" * 70)
    print("AMPLIFIER MEMORY SYSTEM - COMPLETE DEMO")
    print("=" * 70)
    print("\nThis demo shows the complete lifecycle:")
    print("  1. Extract memories from conversation (AI)")
    print("  2. Store memories in JSON (.data/memory.json)")
    print("  3. Index with semantic embeddings (ML)")
    print("  4. Search using semantic similarity")
    print("  5. Use memories to inform new tasks")

    try:
        # Run the complete workflow
        memories = await demo_extraction()
        store, _ = demo_storage(memories)
        searcher = demo_indexing(store)
        demo_search(store, searcher)
        demo_usage(store, searcher)
        demo_storage_format()

        print("\n" + "=" * 70)
        print("✨ DEMO COMPLETE")
        print("=" * 70)
        print(f"\n💾 Memories stored: {store.data_file}")
        print(f"📊 Total memories: {len(store.get_all())}")
        print("\n💡 Try it yourself:")
        print("   python demo_memory_system.py")

    except KeyboardInterrupt:
        print("\n\n⏸️  Demo interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
