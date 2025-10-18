# Amplifier Memory System - Real Example

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. EXTRACT MEMORIES                          │
│                                                                 │
│  Conversation:                                                  │
│  "I prefer JWT for auth"                                       │
│  "Redis is best for caching"                                   │
│  "Async DB calls improved performance 40%"                     │
│                                                                 │
│                         ↓                                       │
│              🤖 Claude Code SDK (AI)                           │
│                         ↓                                       │
│  Extracted Memories:                                           │
│  • [DECISION] Use JWT for API auth                            │
│  • [PREFERENCE] Redis for caching                             │
│  • [PATTERN] Async DB = 40% faster                            │
└─────────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    2. STORE MEMORIES                            │
│                                                                 │
│  File: .data/memory.json                                       │
│                                                                 │
│  {                                                              │
│    "memories": [                                                │
│      {                                                          │
│        "id": "45683b68-...",                                   │
│        "content": "JWT is preferred for API auth...",          │
│        "category": "decision",                                  │
│        "timestamp": "2025-10-17T16:30:00",                     │
│        "accessed_count": 0,                                     │
│        "metadata": {                                            │
│          "source": "architecture_discussion"                    │
│        }                                                        │
│      },                                                         │
│      ...                                                        │
│    ]                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    3. INDEX MEMORIES                            │
│                                                                 │
│  🧠 Sentence Transformer Model: all-MiniLM-L6-v2              │
│                                                                 │
│  Text: "JWT is preferred for API auth..."                      │
│    ↓                                                            │
│  Embedding: [0.234, -0.567, 0.891, ... 384 dimensions]        │
│                                                                 │
│  Stored in: .data/embeddings.json                              │
│  {                                                              │
│    "45683b68-...": [0.234, -0.567, 0.891, ...]                │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    4. SEARCH MEMORIES                           │
│                                                                 │
│  Query: "caching solutions"                                     │
│    ↓                                                            │
│  Query Embedding: [0.123, -0.456, 0.789, ...]                 │
│    ↓                                                            │
│  Semantic Similarity (Cosine):                                  │
│  • Memory 1: 0.733 ✓ "Redis is preferred caching..."          │
│  • Memory 2: 0.270   "Async/await for DB..."                   │
│  • Memory 3: 0.222   "Async DB calls 40% faster..."            │
│    ↓                                                            │
│  Results: Top 3 most similar memories                          │
└─────────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    5. USE MEMORIES                              │
│                                                                 │
│  New Task: "Design a caching layer for the API"                │
│    ↓                                                            │
│  Search finds:                                                  │
│  ✓ User prefers Redis                                          │
│  ✓ Async calls = 40% performance boost                         │
│  ✓ API-first architecture patterns                             │
│    ↓                                                            │
│  AI Assistant uses these to inform design:                      │
│  "Based on your preferences and past learnings,                 │
│   I'll design a Redis-based caching layer with                  │
│   async operations for optimal performance..."                  │
└─────────────────────────────────────────────────────────────────┘
```

## Real Code Example

### 1. Extract Memories

```python
from amplifier.extraction import MemoryExtractor

extractor = MemoryExtractor()

conversation = """
USER: Should we use JWT or session-based auth?
ASSISTANT: JWT is better for API-first architecture...
"""

# AI extracts what's important
memories = await extractor.extract_memories(
    text=conversation,
    context={"source": "architecture_discussion"}
)

# Result:
# [Memory(
#     content="JWT is preferred for API auth...",
#     category="decision",
#     metadata={...}
# )]
```

### 2. Store Memories

```python
from amplifier.memory import MemoryStore, Memory

store = MemoryStore(data_dir=Path(".data"))

# Add a memory
memory = Memory(
    content="User prefers Redis for caching",
    category="preference",
    metadata={"source": "tech_discussion"}
)

stored = store.add_memory(memory)

# Saved to: .data/memory.json
# {
#   "id": "uuid-here",
#   "content": "User prefers Redis for caching",
#   "category": "preference",
#   "timestamp": "2025-10-17T16:30:00",
#   "accessed_count": 0
# }
```

### 3. Index Memories

```python
from amplifier.search import MemorySearcher

searcher = MemorySearcher(data_dir=Path(".data"))

# Generate embeddings for all memories
for memory in store.get_all():
    # Convert text to 384-dimensional vector
    embedding = searcher.generate_embedding(memory.content)

    # Store for fast similarity search
    searcher.store_embedding(memory.id, embedding)

# Embeddings saved to: .data/embeddings.json
```

### 4. Search Memories

```python
# Search by semantic similarity
query = "authentication methods"
results = searcher.search(query, store.get_all(), limit=3)

# Results ranked by similarity:
# [
#   SearchResult(
#     memory=StoredMemory(content="JWT is preferred..."),
#     score=0.389,  # How similar (0-1)
#     match_type="semantic"
#   ),
#   ...
# ]
```

### 5. Use Memories

```python
# When user asks a new question
new_task = "Design a caching layer"

# Find relevant past knowledge
relevant = searcher.search(new_task, store.get_all(), limit=5)

# AI uses these to inform response:
# "Based on your preferences:
#  • You prefer Redis for caching
#  • Async operations gave 40% performance boost
#  • Your architecture is API-first
#
#  Therefore, I recommend..."
```

## Key Components

### MemoryExtractor (amplifier/extraction/)
- **What**: Uses Claude Code SDK to extract memories from text
- **How**: AI identifies important information worth remembering
- **Categories**: learning, decision, issue_solved, preference, pattern

### MemoryStore (amplifier/memory/)
- **What**: Persists memories to JSON
- **Where**: `.data/memory.json`
- **Features**:
  - UUID for each memory
  - Timestamps
  - Access count tracking
  - Automatic rotation (max 1000)

### MemorySearcher (amplifier/search/)
- **What**: Semantic search using ML embeddings
- **Model**: all-MiniLM-L6-v2 (sentence transformers)
- **How**:
  1. Convert text → 384D vector
  2. Compare vectors with cosine similarity
  3. Rank by relevance
- **Fallback**: Keyword search if ML unavailable

## Storage Format

### memory.json
```json
{
  "memories": [
    {
      "id": "45683b68-...",
      "content": "JWT is preferred for API auth",
      "category": "decision",
      "timestamp": "2025-10-17T16:30:00",
      "accessed_count": 0,
      "metadata": {
        "source": "architecture_discussion",
        "importance": 0.8
      }
    }
  ],
  "metadata": {
    "version": "2.0",
    "count": 16,
    "last_updated": "2025-10-17T16:30:00"
  }
}
```

### embeddings.json
```json
{
  "45683b68-...": [0.234, -0.567, 0.891, ...(384 dimensions)],
  "bec6b1b3-...": [0.123, -0.456, 0.789, ...]
}
```

## Performance Characteristics

### Extraction
- **Speed**: ~10-30 seconds per conversation
- **Requirement**: Claude Code SDK + Claude CLI
- **Quality**: High - AI understands context and importance

### Storage
- **Speed**: < 1ms per memory
- **Format**: JSON (human-readable)
- **Limit**: 1000 memories (auto-rotation)

### Indexing
- **Speed**: ~50ms per memory (first time)
- **Model**: 384-dimensional embeddings
- **Requirement**: sentence-transformers library

### Search
- **Speed**: ~10ms for 100 memories
- **Accuracy**: Semantic similarity beats keywords
- **Fallback**: Keyword search if ML unavailable

## Real-World Benefits

### Session Continuity
```
Session 1: "I prefer Redis for caching"
  ↓ Memory extracted and stored

Session 2 (weeks later): "Design a caching layer"
  ↓ Search finds past preference

AI: "Based on your preference for Redis..."
```

### Learning from Experience
```
Problem: "API is slow"
Solution: "Switched to async DB calls"
Result: "40% performance improvement"
  ↓ Stored as pattern

Later: "Optimize the user service"
  ↓ Memory suggests async pattern

AI: "Based on your 40% improvement with async..."
```

### Team Knowledge Sharing
```
Developer A: "We decided to use JWT"
  ↓ Stored as decision

Developer B (different session): "What auth should I use?"
  ↓ Search finds team decision

AI: "Your team decided on JWT because..."
```

## Try It Yourself

```bash
# Run the demo
python demo_memory_system.py

# Check the stored memories
cat .data/memory.json | jq '.memories[] | .content'

# Check the embeddings
cat .data/embeddings.json | jq 'keys | length'
```

## Architecture Benefits

### 1. Modular ("Bricks & Studs")
- Each component is independent
- Clear interfaces between modules
- Can regenerate any module without breaking others

### 2. Fallback Friendly
- No sentence-transformers? → Keyword search
- No Claude SDK? → Manual memory entry
- No memory file? → Creates new one

### 3. Portable
- Point `.data/` to cloud storage (OneDrive, Dropbox)
- Share knowledge across machines
- Backup happens automatically

### 4. Simple Storage
- Human-readable JSON
- Easy to inspect and debug
- No database required

## What Makes This Different?

### Traditional Approach
```
User: "What did we decide about auth?"
AI: "I don't have context from previous conversations."
```

### Amplifier Approach
```
User: "What did we decide about auth?"
AI: [Searches memories]
    "You decided on JWT for API-first architecture
     because it's stateless and mobile-friendly."
```

### The Magic
1. **Extraction**: AI identifies what's worth remembering
2. **Semantic Search**: Finds relevant info even with different wording
3. **Context Integration**: Past knowledge informs new decisions
4. **Learning Accumulation**: Every session makes the system smarter

## Summary

The Amplifier memory system turns Claude Code into a **learning assistant** that:

✅ **Remembers** your preferences and decisions
✅ **Learns** from past successes and failures
✅ **Searches** semantically (not just keywords)
✅ **Applies** accumulated knowledge to new tasks
✅ **Improves** with every conversation

All with simple JSON files and clean, modular code.
