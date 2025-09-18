# Core Improvement: Remove Timeout Constraints

> **Source Branch**: `generator-from-code-cdx`
> **Created**: 2025-09-18
> **Status**: Phase 1 COMPLETED ✅ (items 1-3) - Phase 2+ specification
> **Context**: Core toolkit improvement specifications from module_generator analysis


## Priority: 🔴 Critical (P1)

## Problem Statement

The toolkit currently enforces a 120-second default timeout with a maximum of 600 seconds (10 minutes), which kills productive sessions mid-operation. The module generator proves that operations can and should run to natural completion, sometimes taking 10+ minutes for complex generation tasks.

## Current Implementation

```python
# ccsdk_toolkit/core/models.py
timeout_seconds: int = Field(default=120, gt=0, le=600)  # Hard max of 10 minutes

# ccsdk_toolkit/core/session.py
async with asyncio.timeout(self.options.timeout_seconds):
    # Kills operation after timeout!
```

## Proposed Solution

### Option A: No Default Timeout (Recommended)

```python
# ccsdk_toolkit/core/models.py
class SessionOptions(BaseModel):
    timeout_seconds: int | None = Field(default=None)  # No timeout by default
    max_turns: int = Field(default=1, gt=0)  # No upper limit

# ccsdk_toolkit/core/session.py
async def query(self, prompt: str) -> SessionResponse:
    if self.options.timeout_seconds:
        # Only apply timeout if explicitly requested
        async with asyncio.timeout(self.options.timeout_seconds):
            return await self._execute_query(prompt)
    else:
        # Run to natural completion
        return await self._execute_query(prompt)
```

### Option B: Smart Timeout Based on Turns

```python
class SessionOptions(BaseModel):
    timeout_seconds: int | None = Field(default=None)
    timeout_per_turn: int = Field(default=180)  # 3 min per turn
    max_turns: int = Field(default=1)

    @property
    def effective_timeout(self) -> int | None:
        if self.timeout_seconds is not None:
            return self.timeout_seconds
        # Auto-calculate based on expected turns
        return self.timeout_per_turn * self.max_turns if self.timeout_per_turn else None
```

## Implementation Details

1. Remove the `le=600` constraint immediately
2. Change default from 120 to None
3. Make timeout application conditional
4. Update error messages to be clearer about timeout vs other failures

## Example Usage

```python
# Long-running generation
options = SessionOptions(
    system_prompt="Generate module...",
    max_turns=40,
    timeout_seconds=None  # Run to completion
)

# Quick query with timeout
options = SessionOptions(
    system_prompt="Quick answer...",
    max_turns=1,
    timeout_seconds=30  # Fast fail for quick operations
)
```

## Testing Requirements

- Test operations that run for 15+ minutes
- Verify no timeout applied when None
- Ensure timeout still works when explicitly set
- Test interruption/cancellation still works

## Migration Impact

- Existing code with explicit timeout continues to work
- Default behavior changes from timeout to no-timeout
- May need to add timeouts to some existing examples

## Success Criteria

- Module generation (40 turns, 15+ minutes) completes successfully
- Complex analysis can run for hours if making progress
- Users can still set timeouts when appropriate
- No hanging operations without visibility

## Notes from Module Generator

The generator never uses timeouts on SDK operations:
```python
# No timeout wrapper at all!
async with ClaudeSDKClient(options=options) as client:
    await client.query(prompt)
    # Runs to natural completion
```

This has proven reliable in production use.