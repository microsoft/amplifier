#!/usr/bin/env python3
"""
Visualize Memory Data Examples

Shows the actual data transformations at each stage
"""

import json


def show_extraction_example():
    """Show what AI extraction produces"""
    print("\n" + "=" * 70)
    print("STAGE 1: EXTRACTION - AI Output")
    print("=" * 70)

    extraction_output = {
        "memories": [
            {
                "type": "decision",
                "content": "JWT is preferred over session-based auth for API-first architecture",
                "importance": 0.9,
                "tags": ["authentication", "jwt", "api", "architecture"],
            },
            {
                "type": "preference",
                "content": "Redis is the preferred caching solution",
                "importance": 0.8,
                "tags": ["caching", "redis", "database"],
            },
            {
                "type": "pattern",
                "content": "Async/await database calls improved performance by 40%",
                "importance": 0.95,
                "tags": ["performance", "async", "database", "optimization"],
            },
        ],
        "key_learnings": [
            "Async operations significantly improve database performance"
        ],
        "decisions_made": ["JWT for authentication", "Redis for caching"],
        "issues_solved": [],
    }

    print("\n📤 Raw AI Extraction Result:")
    print(json.dumps(extraction_output, indent=2))

    return extraction_output


def show_storage_example(extraction):
    """Show how memories are stored with metadata"""
    print("\n" + "=" * 70)
    print("STAGE 2: STORAGE - Enriched with Metadata")
    print("=" * 70)

    stored_memories = [
        {
            "id": "45683b68-f001-4d8f-a9e2-d232f7f5a37f",
            "content": extraction["memories"][0]["content"],
            "category": extraction["memories"][0]["type"],
            "timestamp": "2025-10-17T16:26:32.455817",
            "accessed_count": 0,
            "metadata": {
                "authentication_method": "JWT",
                "importance": extraction["memories"][0]["importance"],
                "tags": extraction["memories"][0]["tags"],
                "source": "architecture_discussion",
                "rationale": [
                    "Microservices support",
                    "Mobile app friendly",
                    "No server-side storage",
                ],
            },
        },
        {
            "id": "bec6b1b3-e4f2-4a2b-8f9d-3e5678abcdef",
            "content": extraction["memories"][1]["content"],
            "category": extraction["memories"][1]["type"],
            "timestamp": "2025-10-17T16:26:32.456234",
            "accessed_count": 0,
            "metadata": {
                "technology": "Redis",
                "use_case": "Caching",
                "importance": extraction["memories"][1]["importance"],
                "tags": extraction["memories"][1]["tags"],
                "source": "architecture_discussion",
            },
        },
        {
            "id": "12471e2b-a3c4-4d5e-6f7g-8h9012ijklmn",
            "content": extraction["memories"][2]["content"],
            "category": extraction["memories"][2]["type"],
            "timestamp": "2025-10-17T16:26:32.456567",
            "accessed_count": 0,
            "metadata": {
                "performance_improvement": 40,
                "technique": "Async database calls",
                "importance": extraction["memories"][2]["importance"],
                "tags": extraction["memories"][2]["tags"],
                "source": "architecture_discussion",
            },
        },
    ]

    print("\n💾 Stored in .data/memory.json:")
    print(json.dumps({"memories": stored_memories}, indent=2))

    return stored_memories


def show_embedding_example():
    """Show how text becomes vectors"""
    print("\n" + "=" * 70)
    print("STAGE 3: INDEXING - Text → Vector Embeddings")
    print("=" * 70)

    print("\n🧠 Text-to-Vector Transformation:\n")

    examples = [
        {
            "text": "JWT is preferred over session-based auth",
            "embedding_preview": [
                0.063,
                -0.035,
                0.002,
                0.049,
                0.011,
                -0.031,
                0.042,
                0.028,
            ],
            "full_dimensions": 384,
        },
        {
            "text": "Redis is the preferred caching solution",
            "embedding_preview": [
                0.045,
                -0.021,
                0.067,
                -0.012,
                0.033,
                0.018,
                -0.042,
                0.056,
            ],
            "full_dimensions": 384,
        },
    ]

    for i, ex in enumerate(examples, 1):
        print(f"Example {i}:")
        print(f"  Text: '{ex['text']}'")
        print(f"  Vector: [{', '.join(map(str, ex['embedding_preview']))}, ...")
        print(
            f"           ... {ex['full_dimensions'] - len(ex['embedding_preview'])} more numbers]"
        )
        print()

    embeddings_storage = {
        "45683b68-f001-4d8f-a9e2-d232f7f5a37f": [
            0.063,
            -0.035,
            0.002,
            "... 381 more values ...",
        ],
        "bec6b1b3-e4f2-4a2b-8f9d-3e5678abcdef": [
            0.045,
            -0.021,
            0.067,
            "... 381 more values ...",
        ],
    }

    print("💾 Stored in .data/embeddings.json:")
    print(json.dumps(embeddings_storage, indent=2))


def show_search_example():
    """Show how search works with similarities"""
    print("\n" + "=" * 70)
    print("STAGE 4: SEARCH - Finding Similar Memories")
    print("=" * 70)

    print("\n🔍 Query: 'caching solutions'\n")

    print("Step 1: Convert query to vector")
    print("  Query vector: [0.047, -0.023, 0.071, ... 384 dimensions]\n")

    print("Step 2: Compare with all memory vectors (cosine similarity)")

    comparisons = [
        {
            "memory": "Redis is the preferred caching solution",
            "category": "preference",
            "similarity": 0.733,
            "match": "✓ HIGH MATCH",
        },
        {
            "memory": "Async/await database calls improved performance by 40%",
            "category": "pattern",
            "similarity": 0.270,
            "match": "○ Medium match",
        },
        {
            "memory": "JWT is preferred over session-based auth",
            "category": "decision",
            "similarity": 0.102,
            "match": "○ Low match",
        },
    ]

    for comp in comparisons:
        print(f"  Memory: '{comp['memory'][:50]}...'")
        print(f"    Category: {comp['category']}")
        print(f"    Similarity: {comp['similarity']:.3f} {comp['match']}")
        print()

    print("Step 3: Return top results sorted by similarity")
    print("  Result 1: Redis caching (0.733)")
    print("  Result 2: Async DB calls (0.270)")
    print("  Result 3: JWT auth (0.102)")


def show_usage_example():
    """Show how AI uses memories in responses"""
    print("\n" + "=" * 70)
    print("STAGE 5: USAGE - AI Applies Memories")
    print("=" * 70)

    print("\n📋 User Request:")
    print('  "Design a caching layer for the API"\n')

    print("🔍 Search finds relevant memories:")
    memories_found = [
        {
            "content": "Redis is the preferred caching solution",
            "category": "preference",
            "score": 0.615,
        },
        {
            "content": "Async/await database calls improved performance by 40%",
            "category": "pattern",
            "score": 0.315,
        },
        {
            "content": "JWT is preferred for API-first architecture",
            "category": "decision",
            "score": 0.292,
        },
    ]

    for i, mem in enumerate(memories_found, 1):
        print(f"  {i}. [{mem['category'].upper()}] (score: {mem['score']:.3f})")
        print(f"     {mem['content']}")

    print("\n🤖 AI Response (informed by memories):")
    print(
        """
  Based on your preferences and past learnings, here's the recommended approach:

  🎯 Technology Stack:
    • Redis for distributed caching (your preferred solution)
    • Async cache operations (40% performance boost pattern)

  📐 Architecture:
    • Stateless cache keys (aligns with JWT/API-first architecture)
    • Distributed caching for microservices scalability

  ⚡ Implementation:
    • Use async/await for cache operations
    • Implement cache-aside pattern
    • Set appropriate TTL based on data volatility

  This design incorporates your team's preferences and proven patterns.
"""
    )


def show_full_lifecycle():
    """Show complete data transformation"""
    print("\n" + "=" * 70)
    print("COMPLETE DATA LIFECYCLE")
    print("=" * 70)

    print(
        """
Raw Conversation
    ↓
┌──────────────────────────────────────────────────────────────────┐
│ "I prefer JWT for auth"                                          │
│ "Redis is best for caching"                                      │
│ "Async DB calls improved performance 40%"                        │
└──────────────────────────────────────────────────────────────────┘
    ↓ AI Extraction
┌──────────────────────────────────────────────────────────────────┐
│ {                                                                │
│   "memories": [                                                  │
│     {                                                            │
│       "type": "decision",                                        │
│       "content": "JWT is preferred...",                          │
│       "importance": 0.9                                          │
│     }                                                            │
│   ]                                                              │
│ }                                                                │
└──────────────────────────────────────────────────────────────────┘
    ↓ Add Metadata
┌──────────────────────────────────────────────────────────────────┐
│ {                                                                │
│   "id": "45683b68-...",                                          │
│   "content": "JWT is preferred...",                              │
│   "category": "decision",                                        │
│   "timestamp": "2025-10-17T16:26:32",                            │
│   "accessed_count": 0,                                           │
│   "metadata": {                                                  │
│     "source": "architecture_discussion",                         │
│     "rationale": ["Microservices", "Mobile apps"]                │
│   }                                                              │
│ }                                                                │
└──────────────────────────────────────────────────────────────────┘
    ↓ Generate Embeddings
┌──────────────────────────────────────────────────────────────────┐
│ "JWT is preferred..." → [0.063, -0.035, 0.002, ... 384 dims]    │
│                                                                  │
│ Stored in embeddings.json:                                       │
│ {                                                                │
│   "45683b68-...": [0.063, -0.035, ...]                          │
│ }                                                                │
└──────────────────────────────────────────────────────────────────┘
    ↓ Search Query
┌──────────────────────────────────────────────────────────────────┐
│ Query: "authentication methods"                                  │
│ Query vector: [0.234, -0.456, ...]                              │
│                                                                  │
│ Cosine similarity with stored vectors:                           │
│   Memory 1 (JWT): 0.389 ✓                                       │
│   Memory 2 (Redis): 0.102                                       │
│                                                                  │
│ Result: JWT memory (highest similarity)                          │
└──────────────────────────────────────────────────────────────────┘
    ↓ AI Uses Memory
┌──────────────────────────────────────────────────────────────────┐
│ AI Response:                                                     │
│ "Based on your architecture decisions, JWT is preferred         │
│  for authentication because it supports microservices and        │
│  mobile applications..."                                         │
└──────────────────────────────────────────────────────────────────┘
"""
    )


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("MEMORY SYSTEM DATA VISUALIZATION")
    print("=" * 70)
    print("\nShowing real data transformations at each stage...")

    extraction = show_extraction_example()
    show_storage_example(extraction)
    show_embedding_example()
    show_search_example()
    show_usage_example()
    show_full_lifecycle()

    print("\n" + "=" * 70)
    print("✨ COMPLETE")
    print("=" * 70)
    print("\n💡 Key Takeaways:")
    print("  1. Text → Structured data (AI extraction)")
    print("  2. Structured data → Enriched storage (metadata)")
    print("  3. Text → Vector embeddings (ML)")
    print("  4. Vector similarity → Relevant results (search)")
    print("  5. Relevant results → Informed responses (usage)")
    print()


if __name__ == "__main__":
    main()
