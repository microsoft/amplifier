# Module Contract: IdeaSynthesizer

## Purpose

Given a set of summary files produced upstream, synthesize **net-new** cross-document ideas with clear provenance tracking. Each idea must cite which summaries inspired it, and all outputs must be atomic, machine-readable artifacts suitable for downstream processing.

## Module Identity

- **Name**: idea_synthesizer
- **Package**: amplifier.idea_synthesizer
- **Version**: 1.0.0

## Public Interface

### Primary Function

```python
async def synthesize_ideas(
    summaries: List[SummaryRecord],
    params: SynthesisParams
) -> List[IdeaRecord]:
    """
    Synthesize net-new ideas from multiple document summaries.
    
    Args:
        summaries: List of summary records from upstream processing
        params: Configuration parameters for synthesis
    
    Returns:
        List of synthesized ideas with full provenance
    
    Raises:
        InsufficientInputsError: If fewer than min_sources_per_idea summaries
        AIUnavailableError: If AI service times out or is unavailable
    """
```

### Data Models

#### Input: SummaryRecord
```python
class SummaryRecord:
    digest: str           # SHA256 of source content
    path: str            # Original file path
    title: str           # Document title
    summary: str         # Concise summary (≤400 words)
    key_points: List[str]  # Extracted key points
    created_at: datetime   # Timestamp
```

#### Input: SynthesisParams
```python
class SynthesisParams:
    max_ideas: int = 10                # Maximum ideas to generate
    min_sources_per_idea: int = 2      # Minimum citations per idea
    novelty_threshold: float = 0.6     # 0-1 novelty score threshold
    seed: Optional[int] = None          # For deterministic ordering
    output_dir: Path                   # Where to write outputs
```

#### Output: IdeaRecord
```python
class IdeaRecord:
    id: str                         # Stable: sha1(normalized_title + sorted(digests))
    title: str                      # ≤100 characters
    summary: str                    # 1-3 paragraph description
    rationale: str                  # Why this is net-new
    sources: List[SourceRef]        # Which summaries inspired this
    novelty_score: float            # 0-1 AI-estimated novelty
    impact_score: float             # 0-1 estimated impact
    effort_score: float             # 0-1 estimated effort
    risk_notes: Optional[str]       # Any identified risks
    priority: Literal["high", "medium", "low"]
    tags: List[str]                 # Categorization tags
    created_at: datetime            # ISO-8601 timestamp
```

#### SourceRef
```python
class SourceRef:
    digest: str          # Summary digest that inspired this idea
    path: Optional[str]  # Original document path if known
    relevance: str       # How this source contributed
```

## Side Effects

### File Outputs

1. **Individual idea files**: `{output_dir}/ideas/{idea_id}.json`
2. **Index file**: `{output_dir}/ideas/_index.jsonl` (append-only)
3. **Provenance map**: `{output_dir}/ideas/_provenance.json`
4. **Human-readable briefs**: `{output_dir}/ideas/{idea_id}.md`

### Logging

- Progress logs: `{output_dir}/logs/synthesis_{timestamp}.jsonl`
- Metrics: `{output_dir}/logs/synthesis_{timestamp}.metrics.json`

## Invariants

1. **Net-new requirement**: Ideas must synthesize across sources, not restate single summaries
2. **Provenance completeness**: Every idea must cite ≥ min_sources_per_idea
3. **ID stability**: Same inputs + seed must produce same IDs
4. **Atomic writes**: No partial files; use temp + rename pattern
5. **Idempotency**: Re-running with same inputs produces no duplicates

## Error Handling

| Error | Condition | Response |
|-------|-----------|----------|
| `InsufficientInputsError` | < min_sources summaries | Return empty list + status file |
| `AIUnavailableError` | Timeout/API failure | Retry with backoff, then partial results |
| `OutputWriteError` | Can't write to output_dir | Write to `_failed/` subdirectory |
| `ParseError` | Malformed AI response | Log, skip item, continue |

## Performance Specifications

- Target latency: ≤120s per synthesis batch
- Batch size: Process summaries in groups of ≤10
- Memory usage: O(n) where n = number of summaries
- Concurrency: Support parallel synthesis operations

## Dependencies

- Claude Code SDK for AI synthesis
- Python 3.11+ with asyncio
- hashlib for digest generation
- pathlib for file operations

## Configuration

```python
# Default configuration (can be overridden)
DEFAULT_CONFIG = {
    "max_ideas": 10,
    "min_sources_per_idea": 2,
    "novelty_threshold": 0.6,
    "batch_size": 10,
    "timeout_seconds": 120,
    "retry_attempts": 2,
    "retry_backoff_base": 1.5
}
```

## Usage Example

```python
from amplifier.idea_synthesizer import synthesize_ideas, SynthesisParams
from amplifier.summary_store import load_summaries

# Load summaries from upstream
summaries = await load_summaries("data/summaries")

# Configure synthesis
params = SynthesisParams(
    max_ideas=15,
    min_sources_per_idea=3,
    novelty_threshold=0.7,
    output_dir=Path("data/ideas")
)

# Generate ideas
ideas = await synthesize_ideas(summaries, params)
print(f"Generated {len(ideas)} net-new ideas")
```

## Testing Requirements

- Unit tests for ID generation and deduplication
- Integration tests with mock AI responses
- Idempotency tests with fixed seeds
- Error handling tests for each error type
- Performance tests with 100+ summaries

## Versioning

This contract follows semantic versioning:
- Breaking changes to interface → major version bump
- New optional parameters → minor version bump  
- Bug fixes → patch version bump
