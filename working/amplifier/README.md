# Amplifier Memory System

A modular memory system built following the "bricks and studs" philosophy. Each module is self-contained, regeneratable, and connects through clean interfaces.

## Architecture

The system consists of four independent modules that work together:

### 1. Memory Storage (`memory/`)

**Purpose**: Persist and retrieve memories with JSON storage
**Contract**: Add, search, and retrieve memories
**Key Features**:

- Simple JSON file storage in `.data/memory.json`
- Pydantic models for data validation
- Access count tracking

### 2. Memory Extraction (`extraction/`)

**Purpose**: Extract memories from conversations using AI
**Contract**: Text → List of categorized memories
**Key Features**:

- Claude Code SDK integration for AI extraction
- Categories: learning, decision, issue_solved, preference, pattern

### 3. Semantic Search (`search/`)

**Purpose**: Search memories by semantic similarity
**Contract**: Query + Memories → Scored results
**Key Features**:

- Sentence transformer embeddings (all-MiniLM-L6-v2)
- Fallback keyword search
- Relevance scoring

### 4. Claim Validation (`validation/`)

**Purpose**: Validate claims against stored memories
**Contract**: Claims + Memories → Validation results
**Key Features**:

- Contradiction detection
- Support verification
- Confidence scoring

## Installation

```bash
# Install optional dependencies for full functionality
uv add sentence-transformers  # For semantic search
npm install -g @anthropic-ai/claude-code  # For AI extraction
```

## Usage Example

```python
import asyncio
from memory import MemoryStore, Memory
from extraction import MemoryExtractor
from search import MemorySearcher
from validation import ClaimValidator

async def main():
    # Initialize modules
    store = MemoryStore()
    extractor = MemoryExtractor()
    searcher = MemorySearcher()
    validator = ClaimValidator()

    # Store a memory
    memory = Memory(
        content="User prefers dark mode",
        category="preference",
        metadata={"source": "settings"}
    )
    stored = store.add_memory(memory)

    # Extract memories from conversation
    text = "I learned the API limit is 100/min"
    memories = await extractor.extract_memories(text)

    # Search memories
    all_memories = store.get_all()
    results = searcher.search("API limits", all_memories)

    # Validate claims
    claim = "User prefers light mode"
    validation = validator.validate_text(claim, all_memories)
    if validation.has_contradictions:
        print("Contradiction detected!")

asyncio.run(main())
```

## Module Design Principles

Each module follows these principles:

1. **Self-Contained**: All code, tests, and data within module directory
2. **Clear Contract**: Public API defined in README and `__init__.py`
3. **Regeneratable**: Can be rebuilt from specification without breaking others
4. **Simple Implementation**: Ruthlessly simple, no unnecessary abstractions
5. **Fallback Strategy**: Graceful degradation when dependencies unavailable

## Testing

Run the test script to verify all modules:

```bash
python test_memory_system.py
```

## Data Storage

Memories are stored in `.data/memory.json` with this structure:

```json
{
  "uuid": {
    "id": "uuid",
    "content": "memory text",
    "category": "preference",
    "timestamp": "2024-01-01T00:00:00",
    "metadata": {},
    "accessed_count": 0
  }
}
```

## Future Enhancements

Each module can be independently enhanced without breaking others:

- **Memory**: Add database backend, compression, archiving
- **Extraction**: Improve AI prompts, add more categories
- **Search**: Better embedding models, hybrid search
- **Validation**: Sophisticated contradiction detection, explanation generation
