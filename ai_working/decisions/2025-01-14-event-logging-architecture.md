# Decision Record: Event Logging Architecture

**Date**: 2025-01-14  
**Status**: Implemented  
**Author**: Architecture Team

## Context

Amplifier pipeline operations were opaque with no visibility into:
- What's currently processing
- How long operations take
- Which items failed and why
- API costs being incurred
- Cache hit rates

## Decision

Implement structured JSONL event logging with:
1. Consistent event schema across all stages
2. Local file-based storage
3. Real-time tailing capability
4. Cost and latency tracking
5. Standard status enum (started, completed, failed, cached, skipped)

## Rationale

- **JSONL format**: Human-readable, streamable, grep-able, standard
- **File-based**: Simple, no dependencies, works everywhere
- **Structured schema**: Enables querying and analysis
- **Real-time tailing**: Immediate feedback during long runs

## Implementation

### Event Schema
```python
@dataclass
class Event:
    stage: str              # "extraction", "synthesis", etc.
    status: str             # EventStatus enum
    item_id: Optional[str]  # Item being processed
    fingerprint: Optional[str]  # Cache fingerprint
    message: Optional[str]  # Human-readable message
    cost: Optional[float]   # API cost in dollars
    latency: Optional[float]  # Operation time in seconds
    error: Optional[str]    # Error message if failed
    metadata: Optional[dict]  # Additional context
    timestamp: str          # ISO format UTC timestamp
```

### Storage Format
```
.data/events/events.jsonl

{"stage": "extraction", "status": "started", "item_id": "article_1", "timestamp": "2025-01-14T10:00:00Z"}
{"stage": "extraction", "status": "completed", "item_id": "article_1", "latency": 2.3, "cost": 0.0012, "timestamp": "2025-01-14T10:00:02Z"}
```

### API Design
```python
# Global logger
logger = get_event_logger()

# Track operations with timing
op_id = logger.start_operation("extraction", item_id="article_1")
# ... do work ...
logger.complete_operation(op_id, cost=0.0012)

# Direct logging
log_event("extraction", "cached", item_id="article_2")

# CLI integration
amplifier events tail --follow
amplifier events summary --stage extraction
```

## Alternatives Considered

1. **Structured logging (Python logging)**: Rejected - heavyweight for our needs
2. **SQLite database**: Rejected - overkill, harder to tail
3. **CSV format**: Rejected - poor support for nested data
4. **Binary format**: Rejected - not human-readable
5. **External service (DataDog, etc)**: Rejected - complexity, cost, privacy

## Consequences

### Positive
- Full observability into pipeline operations
- Easy debugging of failures
- Cost tracking and optimization
- Performance profiling data
- Simple integration with existing tools (grep, jq, etc.)

### Negative
- Disk usage for high-volume operations
- No built-in rotation (manual cleanup needed)
- No aggregation across machines
- Basic analysis capabilities (could add more)

## Event Patterns

### Standard Flow
```
started → completed (success)
started → failed (error)
started → skipped (conditional skip)
cached (retrieved from cache, no started event)
```

### Best Practices
1. Always use start/complete pairs for timed operations
2. Include item_id for debuggability
3. Add cost immediately when known
4. Use consistent stage names (EventStage enum)
5. Include error details in metadata for debugging

## Review Triggers

- Event volume becomes unwieldy (>100MB/day)
- Need for structured queries beyond grep/jq
- Multi-machine aggregation requirements
- Real-time alerting needs