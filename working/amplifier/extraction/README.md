# Module: Memory Extraction

## Purpose
Extract memories from conversations using AI with pattern fallback

## Inputs
- **extract_memories**: text (str) - conversation text to analyze
- **context**: Optional[dict] - additional context for extraction

## Outputs
- **extract_memories**: list[Memory] - extracted memories with categories

## Side Effects
- Makes API calls to Claude Code SDK (with 120s timeout)
- Falls back to pattern matching if SDK unavailable

## Dependencies
- claude_code_sdk: AI extraction (optional)
- re: Pattern matching fallback
- memory.models: Memory data model

## Configuration

The memory extraction system supports configuration via environment variables or `.env` file:

- `MEMORY_EXTRACTION_MODEL`: Model for extraction (default: `claude-3-5-haiku-20241022`)
- `MEMORY_EXTRACTION_TIMEOUT`: Timeout in seconds (default: `120`)
- `MEMORY_EXTRACTION_MAX_MESSAGES`: Max messages to process (default: `20`)
- `MEMORY_EXTRACTION_MAX_CONTENT_LENGTH`: Max characters per message (default: `500`)
- `MEMORY_EXTRACTION_MAX_MEMORIES`: Max memories to extract (default: `10`)

## Public Interface
```python
from extraction import MemoryExtractor, get_config
from memory import Memory

# Get configuration
config = get_config()
print(f"Using model: {config.memory_extraction_model}")

# Initialize extractor (uses config automatically)
extractor = MemoryExtractor()

# Extract memories from text
text = "The user prefers dark mode and wants notifications disabled."
memories = await extractor.extract_memories(text)

# With context
memories = await extractor.extract_memories(
    text,
    context={"source": "settings_conversation"}
)
```