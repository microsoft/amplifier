# Knowledge Synthesis Module

Simple, direct knowledge extraction from text using Claude Code SDK.

## Overview

This module provides a streamlined approach to extracting structured knowledge from text documents and content files. It extracts concepts, relationships, insights, and patterns in a single pass through Claude.

## Key Features

- **Single-pass extraction**: One Claude call extracts everything
- **JSON Lines storage**: Simple, incremental, queryable format
- **Incremental processing**: Tracks what's been processed, skips duplicates
- **Direct integration**: Works with content from configured directories

## Architecture

```
text → KnowledgeSynthesizer → JSON extraction → KnowledgeStore → .jsonl file
```

## Usage

### Command Line

```bash
# Extract knowledge from all content files
python -m amplifier.knowledge_synthesis.cli sync

# Process only next 5 files
python -m amplifier.knowledge_synthesis.cli sync --max-files 5

# Search extracted knowledge
python -m amplifier.knowledge_synthesis.cli search "AI agents"

# Show statistics
python -m amplifier.knowledge_synthesis.cli stats

# View recent pipeline events (last 50)
python -m amplifier.knowledge_synthesis.cli events --n 50

# Follow events live (Ctrl+C to stop)
python -m amplifier.knowledge_synthesis.cli events --follow

# Export all knowledge
python -m amplifier.knowledge_synthesis.cli export --format json
```

### Python API

```python
from amplifier.knowledge_synthesis import KnowledgeSynthesizer, KnowledgeStore

# Extract knowledge
synthesizer = KnowledgeSynthesizer()
extraction = await synthesizer.extract(text, title="Document Title")

# Store results
store = KnowledgeStore()
store.save(extraction)

# Check if already processed
if not store.is_processed("document-id"):
    # Process document...
```

## Extraction Format

Each extraction returns:

```json
{
  "source_id": "unique-document-id",
  "title": "Document Title",
  "concepts": [
    {
      "name": "AI Agents",
      "description": "Autonomous software entities...",
      "importance": 0.9
    }
  ],
  "relationships": [
    {
      "subject": "AI Agents",
      "predicate": "enable",
      "object": "automation",
      "confidence": 0.95
    }
  ],
  "insights": ["AI agents can reduce manual work by 80%"],
  "patterns": [
    {
      "name": "Agent Orchestration",
      "description": "Pattern of coordinating multiple agents..."
    }
  ]
}
```

## Storage

Extractions are saved in two formats for resilience and compatibility:

1. **Individual files** (`.data/extractions/{id}.json`):

   - One file per article for resilience
   - Nested format with metadata
   - Used for selective retry and recovery
   - Enables incremental progress tracking

2. **Consolidated JSONL** (`.data/knowledge/extractions.jsonl`):
   - Single append-only file with flat format
   - Used by downstream tools (stats, graph, synthesis)
   - Each line is a complete extraction
   - Optimized for batch processing

The system automatically writes to both locations during extraction for resilience and compatibility.

Benefits of JSON Lines:

- Append-only (fast writes)
- Line-by-line processing (memory efficient)
- Direct text search with grep
- Easy to parse incrementally

### Events

Pipeline events are appended to `.data/knowledge/events.jsonl` as newline-delimited JSON. These provide visibility into sync, extraction progress, successes, skips, and failures.

Examples of event types:

- `sync_started`, `sync_finished`
- `document_skipped` (e.g., already processed, read error)
- `extraction_started`, `extraction_succeeded`, `extraction_failed`

## Dependencies

- `claude-code-sdk`: For Claude integration (requires Claude Code environment)
- `click`: For CLI
- Standard library only for core functionality

## Design Philosophy

Following the project's ruthless simplicity principle:

- No complex graph databases
- No unnecessary chunking (Claude handles 100K+ tokens)
- No over-engineered abstractions
- Direct, obvious code paths
- One way to do things

## Notes

- Works best within Claude Code environment where SDK is available
- Outside Claude Code, extraction returns empty results
- Uses 120-second timeout for Claude operations
- Automatically strips markdown formatting from responses
