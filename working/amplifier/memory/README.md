# Memory Storage Module

A persistent memory system for storing and retrieving contextual information from Claude Code sessions.

## Purpose

The memory module provides JSON-based persistence for memories extracted from conversations, enabling Claude to maintain context across sessions and learn from past interactions.

## Architecture

```
amplifier/memory/
├── __init__.py      # Public exports
├── core.py          # Core memory storage logic
├── models.py        # Data models (Memory, StoredMemory)
└── README.md        # This file
```

## Public Interface

### Models

```python
from amplifier.memory import Memory, StoredMemory

# Input model for creating memories
memory = Memory(
    content="User prefers Python 3.11 for all projects",
    category="preferences",
    tags=["python", "dependencies"],
    metadata={"source": "conversation", "confidence": 0.9}
)

# Stored memory includes id and timestamp
stored_memory = StoredMemory(
    id="abc-123",
    content="...",
    category="...",
    timestamp="2024-01-15T10:30:00",
    # ... other fields
)
```

### Storage Operations

```python
from amplifier.memory import MemoryStore

# Initialize store (uses .data/memory.json by default)
store = MemoryStore()

# Add a memory
stored = store.add_memory(memory)

# Get recent memories
recent = store.search_recent(limit=10)

# Get specific memory by ID
memory = store.get_by_id("abc-123")

# Search by tags
tagged = store.search_by_tags(["python", "dependencies"])

# Get statistics
stats = store.get_stats()  # Returns counts by category
```

## Storage Format

Memories are stored in JSON format at `.data/memory.json`:

```json
{
  "memories": [
    {
      "id": "uuid-here",
      "content": "Important information",
      "category": "technical",
      "tags": ["tag1", "tag2"],
      "timestamp": "2024-01-15T10:30:00",
      "metadata": {
        "source": "conversation",
        "confidence": 0.9
      }
    }
  ]
}
```

## Design Principles

1. **Simple Storage**: JSON files for reliability and debuggability
2. **Automatic Deduplication**: Prevents duplicate memories based on content
3. **Tag-Based Organization**: Flexible categorization system
4. **Metadata Support**: Extensible metadata for tracking source and confidence

## Integration

### With Hook Scripts

The memory module is used by Claude Code hooks:

```python
# In hook_stop.py
from amplifier.memory import MemoryStore

store = MemoryStore()
memory = Memory(
    content=extracted_insight,
    category="learning",
    tags=identified_tags
)
store.add_memory(memory)
```

### With Search Module

The search module uses memory storage for retrieval:

```python
from amplifier.memory import MemoryStore
from amplifier.search import MemorySearcher

store = MemoryStore()
searcher = MemorySearcher(store)
results = await searcher.search("python dependencies")
```

## Configuration

Default configuration can be overridden:

```python
store = MemoryStore(
    storage_path=".custom/memories.json",
    max_memories=10000,  # Limit total memories
    dedupe_threshold=0.95  # Similarity threshold for deduplication
)
```

## Testing

Run module tests:

```bash
# Run memory module tests
pytest amplifier/memory/tests/ -v

# Run specific test
pytest amplifier/memory/tests/test_core.py::test_add_memory -v
```

## Dependencies

- **pydantic**: Data validation and models
- **uuid**: Generate unique identifiers
- **datetime**: Timestamp management
- **json**: Storage serialization
- **pathlib**: File system operations

## Error Handling

The module handles errors gracefully:

- Missing storage file: Creates new file automatically
- Corrupted JSON: Backs up and creates fresh storage
- Duplicate memories: Silently deduplicated
- Invalid data: Validated by Pydantic models

## Performance Considerations

- Memories are loaded into memory on initialization
- Writes are atomic (write to temp, then rename)
- Suitable for up to ~10,000 memories
- For larger datasets, consider database migration

## Future Enhancements

Planned improvements:

- SQLite backend option for larger datasets
- Memory expiration/archival
- Advanced deduplication strategies
- Memory importance scoring
- Compression for old memories

## See Also

- [Search Module](../search/README.md) - Semantic memory search
- [Validation Module](../validation/README.md) - Claim verification
- [Memory CLI](../../.claude/tools/memory_cli.py) - Command-line interface