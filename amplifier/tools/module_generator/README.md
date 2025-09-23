# idea_synthesizer

A modular component for synthesizing net-new cross-document ideas from document summaries with clear provenance tracking.

## Purpose

The `idea_synthesizer` module processes a collection of document summaries to generate novel, cross-document ideas that emerge from the synthesis of multiple sources. Each generated idea includes clear provenance tracking, novelty scoring, and is persisted as an atomic, machine-readable artifact.

Key features:
- **Cross-document synthesis**: Generates ideas that span multiple documents, not just restating single sources
- **Provenance tracking**: Every idea traces back to the summaries that inspired it
- **Atomic persistence**: Ideas are saved as individual JSON files with no partial writes
- **Idempotent operation**: Re-running with the same inputs produces no duplicate artifacts
- **Parallel processing**: Uses Claude Code SDK subagents for efficient parallel synthesis

## Installation

```bash
# Install dependencies
pip install pydantic click

# For development
pip install pytest pytest-asyncio
```

## Quick Start

### Python API

```python
from idea_synthesizer import synthesize_ideas, SynthesisConfig
from pathlib import Path

# Basic usage
results = await synthesize_ideas(
    summaries_dir=Path("path/to/summaries"),
    limit=10,  # Process only first 10 summaries
    run_id="synthesis-001"
)

print(f"Generated {results['total_ideas']} ideas")
for idea in results['ideas']:
    print(f"- {idea.title} (novelty: {idea.novelty_score:.2f})")
```

### Command Line

```bash
# Synthesize ideas from summaries directory
python -m idea_synthesizer \
    --summaries-dir ./summaries \
    --output-dir ./ideas \
    --limit 20 \
    --run-id batch-001

# With filters
python -m idea_synthesizer \
    --summaries-dir ./summaries \
    --include "*.summary.md" \
    --exclude "*draft*"
```

## API Documentation

### Main Function

#### `synthesize_ideas()`

Synthesize net-new ideas from document summaries.

**Parameters:**
- `summaries_dir` (Path, required): Directory containing `*.summary.md` files
- `limit` (int, optional): Maximum number of summaries to process
- `filters` (dict, optional): Include/exclude patterns for filenames
- `run_id` (str, optional): Unique identifier for this run
- `output_dir` (Path, optional): Where to write ideas (default: "ideas")

**Returns:**
Dictionary containing:
- `total_ideas`: Number of ideas generated
- `ideas`: List of IdeaRecord objects
- `metrics`: SynthesisMetrics object
- `output_dir`: Path where ideas were written

**Raises:**
- `NoSummariesError`: If no summaries found
- `ParseError`: If summary parsing fails
- `WriteError`: If file writing fails

### Data Models

#### `IdeaRecord`

Represents a synthesized idea with full metadata.

```python
from idea_synthesizer import IdeaRecord, ProvenanceItem

idea = IdeaRecord(
    id="ai-healthcare-diagnostics-a1b2c3d4",
    title="AI-Powered Healthcare Diagnostics",
    summary="A comprehensive approach to using ML for early disease detection...",
    rationale="This synthesizes insights from papers on computer vision and medical data...",
    novelty_score=0.85,
    impact_score=0.92,
    effort_score=0.65,
    tags=["healthcare", "ai", "diagnostics"],
    provenance=[
        ProvenanceItem(
            summary_path="summaries/paper1.summary.md",
            summary_hash="sha256_hash_here"
        )
    ],
    created_at="2024-01-15T10:30:00Z",
    source_manifest_hash="manifest_hash_123"
)
```

#### `SynthesisConfig`

Configuration for synthesis runs.

```python
from idea_synthesizer import SynthesisConfig

config = SynthesisConfig(
    summaries_dir="./summaries",
    limit=50,
    run_id="batch-2024-01",
    max_summaries_per_partition=10,
    min_novelty_threshold=0.4,
    dedup_similarity_threshold=0.85
)
```

## Output Structure

The module creates the following file structure:

```
ideas/
├── ai-healthcare-abc123.idea.json     # Individual idea files
├── ml-optimization-def456.idea.json
├── _index.jsonl                        # Append-only index
└── _provenance.json                    # Optional provenance map

logs/idea_synthesizer/
├── batch-001.jsonl                     # Progress logs
└── batch-001.metrics.json              # Run metrics
```

### Idea File Format

Each idea is saved as a JSON file:

```json
{
  "id": "ai-healthcare-abc123",
  "title": "AI-Powered Healthcare Diagnostics",
  "summary": "A comprehensive approach to using machine learning...",
  "rationale": "This idea synthesizes insights from multiple papers...",
  "novelty_score": 0.85,
  "impact_score": 0.92,
  "effort_score": 0.65,
  "tags": ["healthcare", "ai"],
  "provenance": [
    {
      "summary_path": "summaries/paper1.summary.md",
      "summary_hash": "a1b2c3d4..."
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "source_manifest_hash": "xyz789..."
}
```

## Advanced Usage

### Custom Configuration

```python
from idea_synthesizer import synthesize_ideas

# Advanced configuration
results = await synthesize_ideas(
    summaries_dir=Path("./summaries"),
    limit=100,
    filters={
        "include": ["*.summary.md"],
        "exclude": ["*draft*", "*temp*"]
    },
    run_id="custom-run",
    max_summaries_per_partition=5,  # Smaller partitions
    min_novelty_threshold=0.5,       # Higher novelty requirement
    dedup_similarity_threshold=0.9,  # Stricter deduplication
    max_retries=3                    # More retries on failure
)
```

### Resume from Interruption

The module supports resuming from partial completion:

```python
# If synthesis was interrupted, it will resume from where it left off
results = await synthesize_ideas(
    summaries_dir=Path("./summaries"),
    run_id="batch-001"  # Same run_id as interrupted run
)
```

### Programmatic Filtering

```python
# Complex filtering logic
results = await synthesize_ideas(
    summaries_dir=Path("./summaries"),
    filters={
        "include": ["research/*.summary.md", "papers/*.summary.md"],
        "exclude": ["*archived*", "*old*"]
    }
)
```

## Testing

### Run Tests

```bash
# Run all tests
pytest test_idea_synthesizer.py -v

# Run specific test categories
pytest test_idea_synthesizer.py::TestIdeaRecord -v
pytest test_idea_synthesizer.py::TestErrorHandling -v

# Run with coverage
pytest test_idea_synthesizer.py --cov=idea_synthesizer
```

### Test Categories

The test suite covers:
- **Data model validation**: Ensures IdeaRecord and other models work correctly
- **Core functionality**: Tests loading, partitioning, and synthesis
- **Error handling**: Validates proper error handling and recovery
- **Idempotency**: Ensures re-runs don't create duplicates
- **Resume capability**: Tests interruption and resume scenarios
- **Metrics and logging**: Validates observability features

## Error Handling

The module handles three main error types:

```python
from idea_synthesizer import NoSummariesError, ParseError, WriteError

try:
    results = await synthesize_ideas(summaries_dir=Path("./empty"))
except NoSummariesError:
    print("No summaries found in directory")
except ParseError as e:
    print(f"Failed to parse summary: {e}")
except WriteError as e:
    print(f"Failed to write output: {e}")
```

## Module Contract

### Inputs
- `summaries_dir`: Directory containing `*.summary.md` files
- `limit`: Maximum summaries to process (optional)
- `filters`: Include/exclude patterns (optional)
- `run_id`: Execution identifier (optional)

### Outputs
- Individual idea files: `ideas/<idea-id>.idea.json`
- Index file: `ideas/_index.jsonl` (append-only)
- Provenance map: `ideas/_provenance.json` (optional)

### Observable Side-effects
- Progress logs: `logs/idea_synthesizer/<run-id>.jsonl`
- Metrics: `logs/idea_synthesizer/<run-id>.metrics.json`

### Invariants
- **Net-new synthesis**: Ideas must synthesize across documents
- **Provenance tracking**: Every idea traces to source summaries
- **Atomic writes**: No partial files on failure
- **Idempotency**: Same inputs produce same outputs
- **Determinism**: With fixed seeds, results are reproducible

## Development

### Project Structure

```
idea_synthesizer/
├── __init__.py           # Public API
├── synthesizer.py        # Core synthesis logic
├── models.py             # Data models (Pydantic)
├── partitioner.py        # Summary partitioning
├── deduplicator.py       # Deduplication logic
├── subagent_manager.py   # Claude Code SDK integration
├── utils.py              # Utilities
├── cli.py                # CLI interface
├── config.py             # Configuration
├── test_idea_synthesizer.py  # Tests
└── README.md             # This file
```

### Contributing

1. Ensure tests pass: `pytest test_idea_synthesizer.py`
2. Follow the modular design philosophy (see MODULAR_DESIGN_PHILOSOPHY.md)
3. Maintain contract compatibility when making changes
4. Update tests for new functionality
5. Document any new configuration options

## Dependencies

- **pydantic**: Data validation and models
- **click**: CLI interface
- **claude-code-sdk**: AI synthesis (via subagents)
- **pathlib**: File system operations
- **hashlib**: Content hashing
- **json**: Data serialization

## License

See LICENSE file in the repository root.

## Support

For issues or questions, please refer to the project's issue tracker.