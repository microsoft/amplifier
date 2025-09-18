# Core Improvement: Flexible Max Turns

> **Source Branch**: `generator-from-code-cdx`
> **Created**: 2025-09-18
> **Status**: Phase 1 COMPLETED ✅ (items 1-3) - Phase 2+ specification
> **Context**: Core toolkit improvement specifications from module_generator analysis


## Priority: 🔴 Critical (P1)

## Problem Statement

The toolkit defaults to 1 turn with a maximum of 100, which is insufficient for complex operations. The module generator uses up to 40 turns for generation tasks, proving that real work requires extensive conversation.

## Current Implementation

```python
# ccsdk_toolkit/core/models.py
max_turns: int = Field(default=1, gt=0, le=100)  # Limited to 100
```

## Proposed Solution

### Remove Upper Limit and Provide Presets

```python
# ccsdk_toolkit/core/models.py
class SessionOptions(BaseModel):
    max_turns: int = Field(default=1, gt=0)  # No upper limit

# ccsdk_toolkit/core/presets.py
class SessionPresets:
    """Common session configurations for different use cases."""

    # Quick operations
    QUICK_QUERY = SessionOptions(
        max_turns=1,
        timeout_seconds=60
    )

    # Analysis tasks
    ANALYSIS = SessionOptions(
        max_turns=5,
        timeout_seconds=300
    )

    # Planning operations
    PLANNING = SessionOptions(
        max_turns=3,
        timeout_seconds=None,
        stream_output=True
    )

    # Complex generation
    GENERATION = SessionOptions(
        max_turns=40,
        timeout_seconds=None,
        stream_output=True
    )

    # Open-ended exploration
    EXPLORATION = SessionOptions(
        max_turns=100,
        timeout_seconds=None,
        stream_output=True
    )
```

## Usage Examples

### Basic Usage
```python
# Use preset for generation
from amplifier.ccsdk_toolkit import SessionPresets

async with ClaudeSession(SessionPresets.GENERATION) as session:
    response = await session.query("Generate module...")
```

### Custom Configuration
```python
# Override preset values
options = SessionPresets.GENERATION
options.max_turns = 50  # Even more turns for complex task
options.system_prompt = "Custom prompt..."
```

### Progressive Complexity
```python
# Start simple, increase as needed
async def attempt_task(prompt: str):
    for turns in [5, 20, 40, 80]:
        options = SessionOptions(max_turns=turns, stream_output=True)
        async with ClaudeSession(options) as session:
            response = await session.query(prompt)
            if response.metadata.get("completed"):
                return response
    # Needs even more turns
    return await unlimited_session(prompt)
```

## Module Generator Evidence

```python
# Different operations use different turn counts
max_turns=40  # Generation (sdk_client.py:143)
max_turns=3   # Planning (sdk_client.py:98)
max_turns=5   # Decomposition (decomposer/specs.py:55)
max_turns=4   # Plan service (planner/service.py:22)
```

## Implementation Details

1. Remove `le=100` constraint from Field
2. Create presets module with common configurations
3. Document when to use which preset
4. Update examples to use appropriate turn counts

## Testing Requirements

- Test operations with 50+ turns
- Verify memory usage with high turn counts
- Test preset configurations work correctly
- Ensure backwards compatibility

## Migration Impact

- Existing code continues to work
- Presets provide easy migration path
- Documentation needed for turn count guidance

## Success Criteria

- Support 40+ turn generation operations
- Complex tasks complete without turn limits
- Presets make configuration simple
- Users understand turn requirements

## Philosophy Note

Turns should represent logical conversation boundaries, not arbitrary limits. Let the task complexity determine the turn count, not artificial constraints. Trust that productive work may require extensive dialogue.