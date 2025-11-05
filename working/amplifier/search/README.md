# Module: Semantic Search

## Purpose
Search memories by semantic similarity with keyword fallback

## Inputs
- **search**: query (str), memories (list[StoredMemory]), limit (int)
- **rerank**: query (str), results (list[SearchResult])

## Outputs
- **search**: list[SearchResult] - scored and sorted results
- **rerank**: list[SearchResult] - reranked by relevance

## Side Effects
- Loads sentence transformer model on first use
- Falls back to keyword search if embedding fails

## Dependencies
- sentence-transformers: Semantic similarity (optional)
- memory.models: StoredMemory model

## Public Interface
```python
from search import MemorySearcher, SearchResult
from memory import MemoryStore

# Initialize
store = MemoryStore()
searcher = MemorySearcher()

# Search memories
memories = store.get_all()
results = searcher.search("dark mode preferences", memories, limit=5)

# Access results
for result in results:
    print(f"{result.score:.2f}: {result.memory.content}")
```