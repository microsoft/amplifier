# Decision Record: Artifact Cache Design

**Date**: 2025-01-14  
**Status**: Implemented  
**Author**: Architecture Team

## Context

Amplifier reprocesses the same content repeatedly across runs, leading to:
- Unnecessary API costs (10-100x higher than needed)
- Slow iteration cycles
- Inability to resume after interruption
- No way to force refresh when needed

## Decision

Implement content-addressable artifact cache with:
1. Deterministic fingerprinting based on content + parameters
2. Local filesystem storage in `.data/artifacts/`
3. Per-stage caching with separate namespaces
4. Incremental processing with resume support

## Rationale

- **Content-addressable**: Automatic cache invalidation when inputs change
- **Fingerprinting scope**: Include model, params, and content for correctness
- **Local storage**: Simple, no external dependencies, portable
- **Fixed filenames**: Enables resume by overwriting, not accumulating

## Implementation

### Fingerprint Components
```python
fingerprint = hash(
    content_hash +    # SHA256 of input text
    stage +           # "extraction", "synthesis", etc.
    model +           # Model version if applicable
    params            # Processing parameters
)[:16]  # Truncate for readability
```

### Cache Structure
```
.data/artifacts/
├── extraction/
│   ├── a1b2c3d4e5f6.json
│   └── b2c3d4e5f6g7.json
├── synthesis/
│   └── c3d4e5f6g7h8.json
└── triage/
    └── d4e5f6g7h8i9.json
```

### API Design
```python
cache = ArtifactCache()

# Main entry point
result, was_cached = cache.check_or_process(
    content="...",
    stage="extraction",
    processor_func=extract_knowledge,
    model="gpt-4",
    params={"temperature": 0.7},
    force=False  # Override cache
)

# Incremental processor for batch operations
processor = IncrementalProcessor(
    output_file=Path("results.json"),
    cache=cache
)
```

## Alternatives Considered

1. **Redis/Memcached**: Rejected - unnecessary complexity for single-machine use
2. **SQLite**: Rejected - overkill for key-value storage
3. **No truncation of hash**: Rejected - full SHA256 too long for filenames
4. **In-memory only**: Rejected - loses benefit across runs
5. **Cloud storage**: Rejected - latency, complexity, and privacy concerns

## Consequences

### Positive
- 10-100x cost reduction on repeated runs
- Near-instant results for unchanged content
- Interruption/resume without data loss
- Predictable storage patterns
- Easy to debug and inspect

### Negative
- Disk space usage (mitigated by `.gitignore`)
- Cache invalidation complexity if parameters change
- No cache sharing between machines (acceptable tradeoff)

## Invalidation Rules

Cache is automatically invalidated when:
- Content changes (different hash)
- Model version changes
- Processing parameters change
- Stage implementation changes (manual cache clear needed)

Manual invalidation:
- `--force` flag on any command
- Delete `.data/artifacts/` directory
- `cache.clear_stage("extraction")`

## Review Triggers

- Cache size becomes problematic (>1GB)
- Need for distributed caching
- Performance issues with filesystem operations
- Need for more sophisticated invalidation