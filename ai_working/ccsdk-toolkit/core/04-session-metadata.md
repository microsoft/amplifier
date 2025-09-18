# Core Improvement: Session Metadata Collection

> **Source Branch**: `generator-from-code-cdx`
> **Created**: 2025-09-18
> **Status**: Phase 1 COMPLETED ✅ (items 1-3) - Phase 2+ specification
> **Context**: Core toolkit improvement specifications from module_generator analysis


## Priority: 🟡 Important (P2)

## Problem Statement

The toolkit doesn't collect critical session metadata like session_id, cost, and duration. The module generator captures this information, enabling cost tracking and session continuity.

## Current Implementation

```python
# ccsdk_toolkit/core/models.py
class SessionResponse(BaseModel):
    content: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)  # Generic, untyped
    error: str | None = Field(default=None)
```

## Proposed Solution

### Enhanced SessionResponse with Typed Metadata

```python
# ccsdk_toolkit/core/models.py
from datetime import datetime

class SessionMetadata(BaseModel):
    """Structured metadata from Claude session."""
    session_id: str | None = None
    total_cost_usd: float = 0.0
    duration_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    turns_used: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now())

class SessionResponse(BaseModel):
    """Enhanced response with structured metadata."""
    content: str = Field(default="")
    metadata: SessionMetadata = Field(default_factory=SessionMetadata)
    error: str | None = Field(default=None)

    @property
    def success(self) -> bool:
        """Check if query was successful."""
        return self.error is None and bool(self.content)

    @property
    def session_id(self) -> str | None:
        """Quick access to session ID."""
        return self.metadata.session_id

    @property
    def cost(self) -> float:
        """Quick access to cost."""
        return self.metadata.total_cost_usd
```

### Collect Metadata During Streaming

```python
# ccsdk_toolkit/core/session.py
async def query(self, prompt: str) -> SessionResponse:
    response_text = ""
    metadata = SessionMetadata()

    async for message in self.client.receive_response():
        # ... handle content ...

        # Collect metadata from ResultMessage
        if hasattr(message, "__class__") and message.__class__.__name__ == "ResultMessage":
            metadata.session_id = getattr(message, "session_id", None)
            metadata.total_cost_usd = getattr(message, "total_cost_usd", 0.0)
            metadata.duration_ms = getattr(message, "duration_ms", 0)
            # Try to get token counts if available
            metadata.input_tokens = getattr(message, "input_tokens", 0)
            metadata.output_tokens = getattr(message, "output_tokens", 0)

    metadata.turns_used = self.options.max_turns  # Track configured turns

    return SessionResponse(
        content=response_text,
        metadata=metadata
    )
```

## Usage Patterns

### Cost Tracking
```python
total_cost = 0.0
files_processed = []

for file in files_to_analyze:
    async with ClaudeSession(options) as session:
        response = await session.query(f"Analyze {file}")

        total_cost += response.cost
        files_processed.append({
            "file": file,
            "cost": response.cost,
            "duration": response.metadata.duration_ms
        })

print(f"Total cost: ${total_cost:.4f}")
print(f"Average per file: ${total_cost/len(files):.4f}")
```

### Session Continuity
```python
# Save session for potential resumption
if response.session_id:
    save_session_state({
        "session_id": response.session_id,
        "last_response": response.content,
        "cost_so_far": response.cost
    })
```

### Performance Monitoring
```python
if response.metadata.duration_ms > 60000:  # Over 1 minute
    logger.warning(
        f"Slow operation: {response.metadata.duration_ms}ms "
        f"for {response.metadata.output_tokens} tokens"
    )
```

## Module Generator Pattern

```python
# sdk/claude.py
async def _collect_messages(client: Any) -> ClaudeRunResult:
    session_id: str | None = None
    total_cost = 0.0
    duration_ms = 0

    async for message in client.receive_response():
        # ... handle content ...
        if ResultMessage and isinstance(message, ResultMessage):
            total_cost = getattr(message, "total_cost_usd", 0.0)
            duration_ms = getattr(message, "duration_ms", 0)
            session_id = getattr(message, "session_id", None)

    return ClaudeRunResult(text, session_id, total_cost, duration_ms)
```

## Testing Requirements

- Verify metadata collection from ResultMessage
- Test cost accumulation across sessions
- Ensure backwards compatibility with existing code
- Test metadata persistence and retrieval

## Migration Impact

- Existing code using generic metadata continues to work
- New typed access methods available
- Examples should demonstrate cost tracking

## Success Criteria

- Every session returns cost information
- Session IDs enable continuity features
- Performance metrics available for monitoring
- Cost awareness built into examples