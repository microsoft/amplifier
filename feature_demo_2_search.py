#!/usr/bin/env python3
"""
Feature Demo #2: Semantic Search
Shows how Amplifier uses AI to find relevant memories by MEANING, not just keywords
"""
import asyncio
from amplifier.memory import MemoryStore
from amplifier.search import MemorySearcher


async def main():
    print("\n" + "=" * 70)
    print("🔍 FEATURE #2: SEMANTIC SEARCH")
    print("=" * 70)

    print("\n📋 What is Semantic Search?")
    print("   Traditional search finds exact keyword matches.")
    print("   Semantic search understands MEANING using AI embeddings.")
    print()
    print("   Example:")
    print("   • Query: 'database performance issues'")
    print("   • Finds: 'Always use async/await for DB operations'")
    print("   • Why? AI knows they're related, even with different words!")

    # Initialize
    print("\n" + "-" * 70)
    print("🔧 Initializing search system...")
    store = MemoryStore()
    searcher = MemorySearcher()

    all_memories = store.get_all()
    print(f"📊 Searching across {len(all_memories)} memories")
    print(f"🤖 AI Model: {searcher.model_name}")

    # Demonstrate semantic search vs keyword search
    print("\n" + "=" * 70)
    print("🧪 EXPERIMENT: Semantic vs Keyword Search")
    print("=" * 70)

    test_queries = [
        {
            "query": "How should I handle database queries?",
            "explanation": "Looking for DB best practices (no exact keyword match)"
        },
        {
            "query": "coding style preferences",
            "explanation": "Finding style guidelines (synonyms, not exact words)"
        },
        {
            "query": "authentication token problems",
            "explanation": "Security issues with auth (conceptual match)"
        },
        {
            "query": "What technology choices were made?",
            "explanation": "Architectural decisions (high-level concept)"
        },
        {
            "query": "security best practices",
            "explanation": "Safety patterns (domain understanding)"
        }
    ]

    for i, test in enumerate(test_queries, 1):
        print(f"\n{'─' * 70}")
        print(f"Query {i}: '{test['query']}'")
        print(f"Goal: {test['explanation']}")
        print()

        # Perform search
        results = searcher.search(test['query'], all_memories, limit=3)

        if results:
            print(f"✅ Found {len(results)} relevant memories:\n")
            for rank, result in enumerate(results, 1):
                # Color-code by score
                if result.score > 0.5:
                    confidence = "🟢 HIGH"
                elif result.score > 0.3:
                    confidence = "🟡 MED"
                else:
                    confidence = "🔴 LOW"

                print(f"   {rank}. [{confidence}] Score: {result.score:.3f}")
                print(f"      Type: {result.match_type}")
                print(f"      Category: {result.memory.category}")
                print(f"      Memory: {result.memory.content}")
                print()
        else:
            print("   ❌ No matches found")

    # Show the magic: How it works
    print("=" * 70)
    print("🎯 HOW IT WORKS")
    print("=" * 70)
    print()
    print("1. Convert query to AI embedding (vector of numbers)")
    print("   'database performance' → [0.234, -0.891, 0.456, ...]")
    print()
    print("2. Convert each memory to AI embedding")
    print("   'async/await for DB' → [0.223, -0.887, 0.441, ...]")
    print()
    print("3. Calculate similarity (cosine distance)")
    print("   Similar vectors = similar meaning!")
    print()
    print("4. Rank by similarity score (0.0 to 1.0)")
    print("   Higher score = more relevant")
    print()
    print("5. Return top matches")

    # Compare with keyword fallback
    print("\n" + "=" * 70)
    print("🔄 FALLBACK: When AI Isn't Available")
    print("=" * 70)
    print()
    print("Amplifier gracefully degrades to keyword search:")
    print("• Splits query into words")
    print("• Counts matching words in each memory")
    print("• Scores by overlap percentage")
    print()
    print("This ensures the system ALWAYS works, even without AI models!")

    print("\n" + "=" * 70)
    print("✅ Semantic Search Demo Complete!")
    print("=" * 70)

    print("\n💡 Key Takeaways:")
    print("   1. Searches by MEANING, not just keywords")
    print("   2. Finds related concepts even with different words")
    print("   3. Scores indicate confidence (0.0-1.0)")
    print("   4. Works with natural language queries")
    print("   5. Automatic fallback if AI unavailable")

    print("\n🎓 Why This Matters:")
    print("   • No need to remember exact phrasing")
    print("   • Ask questions naturally")
    print("   • Discovers unexpected connections")
    print("   • Gets smarter as you add more memories")

    print("\n🔍 Try it yourself:")
    print("   • Query: make knowledge-query Q='your question'")
    print("   • Add memories and search them")
    print("   • Experiment with different phrasings")
    print()


if __name__ == "__main__":
    asyncio.run(main())
