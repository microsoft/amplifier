# Core Improvement: Real-time Progress Streaming

> **Source Branch**: `generator-from-code-cdx`
> **Created**: 2025-09-18
> **Status**: Phase 1 COMPLETED ✅ (items 1-3) - Phase 2+ specification
> **Context**: Core toolkit improvement specifications from module_generator analysis


## Priority: 🔴 Critical (P1)

## Problem Statement

The toolkit silently collects all output and returns it at the end, leaving users in the dark about what's happening during long operations. The module generator streams output in real-time, maintaining user confidence and providing progress visibility.

## Current Implementation

```python
# ccsdk_toolkit/core/session.py
# Silently collects everything
response_text = ""
async for message in self.client.receive_response():
    # ... collect text ...
    response_text += getattr(block, "text", "")
# Return all at once
return SessionResponse(content=response_text)
```

## Proposed Solution

### Add Streaming Support to SessionOptions

```python
# ccsdk_toolkit/core/models.py
class SessionOptions(BaseModel):
    stream_output: bool = Field(default=False)
    progress_callback: Callable[[str], None] | None = Field(default=None)
```

### Implement Streaming in Session

```python
# ccsdk_toolkit/core/session.py
async def query(self, prompt: str, stream: bool | None = None) -> SessionResponse:
    """Query with optional streaming output."""
    response_text = ""
    metadata = {}

    async for message in self.client.receive_response():
        if hasattr(message, "content"):
            content = getattr(message, "content", [])
            if isinstance(content, list):
                for block in content:
                    if hasattr(block, "text"):
                        text = getattr(block, "text", "")
                        if text:
                            response_text += text

                            # Stream output if enabled
                            should_stream = stream if stream is not None else self.options.stream_output
                            if should_stream:
                                print(text, end="", flush=True)

                            # Call progress callback if provided
                            if self.options.progress_callback:
                                self.options.progress_callback(text)

        # Collect metadata from ResultMessage
        if hasattr(message, "session_id"):
            metadata["session_id"] = getattr(message, "session_id", None)
            metadata["total_cost_usd"] = getattr(message, "total_cost_usd", 0.0)
            metadata["duration_ms"] = getattr(message, "duration_ms", 0)

    if stream or self.options.stream_output:
        print()  # Final newline after streaming

    return SessionResponse(content=response_text, metadata=metadata)
```

## Implementation Patterns

### Pattern 1: Simple Streaming
```python
options = SessionOptions(stream_output=True)
async with ClaudeSession(options) as session:
    # Will print output as it arrives
    response = await session.query("Generate something...")
```

### Pattern 2: Custom Progress Handler
```python
def progress_handler(text: str):
    # Custom progress display
    console.print(f"[dim]{text}[/dim]", end="")

options = SessionOptions(progress_callback=progress_handler)
```

### Pattern 3: Rich Progress Display
```python
from rich.progress import Progress

with Progress() as progress:
    task = progress.add_task("Generating...", total=None)

    def update_progress(text: str):
        progress.console.print(text, end="")
        progress.advance(task)

    options = SessionOptions(progress_callback=update_progress)
```

## Testing Requirements

- Verify streaming output appears in real-time
- Test progress callback is called with chunks
- Ensure non-streaming mode still works
- Test that streaming can be toggled per-query

## Migration Impact

- Default behavior unchanged (no streaming)
- Opt-in via `stream_output=True`
- Examples should demonstrate streaming for long operations

## Success Criteria

- Users see real-time output during generation
- Progress is visible for operations taking minutes
- Confidence maintained during long operations
- Custom progress displays possible

## Module Generator Pattern

```python
# sdk/claude.py and sdk_client.py
async for message in client.receive_response():
    if TextBlock and isinstance(block, TextBlock):
        text = getattr(block, "text", "")
        if text:
            print(text, end="", flush=True)  # Real-time visibility!
            collected.append(text)
```

This simple pattern has proven essential for user confidence.