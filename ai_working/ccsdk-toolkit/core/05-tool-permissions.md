# Core Improvement: Tool Permission Control

> **Source Branch**: `generator-from-code-cdx`
> **Created**: 2025-09-18
> **Status**: Phase 1 COMPLETED ✅ (items 1-3) - Phase 2+ specification
> **Context**: Core toolkit improvement specifications from module_generator analysis


## Priority: 🟡 Important (P2)

## Problem Statement

The toolkit doesn't expose control over tool permissions and permission modes, limiting safety options for different phases of work. The module generator demonstrates progressive tool access (read-only for planning, write-enabled for generation).

## Current Implementation

```python
# ccsdk_toolkit/core/session.py
# No tool control exposed
ClaudeSDKClient(
    options=ClaudeCodeOptions(
        system_prompt=self.options.system_prompt,
        max_turns=self.options.max_turns,
        # No tool configuration
    )
)
```

## Proposed Solution

### Add Tool Control to SessionOptions

```python
# ccsdk_toolkit/core/models.py
from typing import Literal

PermissionMode = Literal["default", "acceptEdits", "confirm", "reject"]

class SessionOptions(BaseModel):
    # Existing fields...

    # Tool control
    allowed_tools: list[str] | None = Field(
        default=None,
        description="List of allowed tools (e.g., ['Read', 'Grep', 'Write'])"
    )
    permission_mode: PermissionMode = Field(
        default="default",
        description="How to handle tool permission requests"
    )
```

### Pass Tool Configuration to SDK

```python
# ccsdk_toolkit/core/session.py
async def __aenter__(self):
    from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient

    options_dict = {
        "system_prompt": self.options.system_prompt,
        "max_turns": self.options.max_turns,
    }

    # Add tool configuration if specified
    if self.options.allowed_tools:
        options_dict["allowed_tools"] = self.options.allowed_tools
    if self.options.permission_mode:
        options_dict["permission_mode"] = self.options.permission_mode

    self.client = ClaudeSDKClient(
        options=ClaudeCodeOptions(**options_dict)
    )
```

## Usage Patterns

### Pattern 1: Progressive Tool Access

```python
# Phase 1: Planning (read-only)
planning_options = SessionOptions(
    system_prompt="Plan the implementation...",
    allowed_tools=["Read", "Grep"],  # Read-only
    permission_mode="default",
    max_turns=3
)

async with ClaudeSession(planning_options) as session:
    plan = await session.query("Create implementation plan")

# Phase 2: Implementation (write-enabled)
impl_options = SessionOptions(
    system_prompt="Implement the plan...",
    allowed_tools=["Read", "Write", "Edit", "MultiEdit", "Bash"],
    permission_mode="acceptEdits",  # Auto-approve edits
    max_turns=40
)

async with ClaudeSession(impl_options) as session:
    result = await session.query(f"Implement this plan:\n{plan.content}")
```

### Pattern 2: Safety Levels

```python
class SafetyPresets:
    """Tool permission presets for different safety levels."""

    READONLY = SessionOptions(
        allowed_tools=["Read", "Grep", "Glob"],
        permission_mode="default"
    )

    ANALYSIS = SessionOptions(
        allowed_tools=["Read", "Grep", "Glob", "WebFetch"],
        permission_mode="default"
    )

    EDITING = SessionOptions(
        allowed_tools=["Read", "Write", "Edit", "MultiEdit"],
        permission_mode="confirm"  # Require confirmation
    )

    GENERATION = SessionOptions(
        allowed_tools=["Read", "Write", "Edit", "MultiEdit", "Bash"],
        permission_mode="acceptEdits"  # Auto-approve
    )

    UNRESTRICTED = SessionOptions(
        allowed_tools=None,  # All tools available
        permission_mode="default"
    )
```

### Pattern 3: Context-Aware Permissions

```python
def get_options_for_task(task_type: str) -> SessionOptions:
    """Get appropriate permissions for task type."""
    match task_type:
        case "planning":
            return SafetyPresets.READONLY
        case "analysis":
            return SafetyPresets.ANALYSIS
        case "implementation":
            return SafetyPresets.EDITING
        case "generation":
            return SafetyPresets.GENERATION
        case _:
            return SafetyPresets.READONLY  # Safe default
```

## Module Generator Evidence

```python
# sdk_client.py - Planning phase
allowed_tools=["Read", "Grep"],  # Read-only for planning
permission_mode="default",

# sdk_client.py - Generation phase
allowed_tools=["Read", "Write", "Edit", "MultiEdit", "Bash"],
permission_mode="acceptEdits",  # Auto-approve for generation
```

## Testing Requirements

- Test tool restrictions are enforced
- Verify permission modes work correctly
- Test progression from read-only to write
- Ensure safety defaults are appropriate

## Migration Impact

- Default behavior unchanged (all tools available)
- Opt-in tool restrictions
- Examples should demonstrate safety patterns

## Success Criteria

- Read-only mode prevents accidental modifications
- Progressive access enables safe exploration
- Permission modes provide appropriate control
- Clear patterns for different use cases

## Safety Philosophy

Start with minimal permissions and expand as needed. Read-only exploration should precede modifications. Auto-approval should only be used when the operation's scope is well-understood.