# Message Attribution

## Overview

Message attribution determines the source of each message in Claude Code session logs.

## Message Categories

### User Messages

1. **Direct input** - Human user text
2. **Commands** - Slash commands (`/compact`, `/help`)
3. **Edits** - "Redo from here" operations

### Assistant Messages

1. **Claude responses** - Primary assistant replies
2. **Sub-agent responses** - Sidechain agent replies
3. **Tool invocations** - Tool calls by Claude

### System Messages

1. **Compact operations**
   - Type: `"user"` with `subtype: "compact_boundary"`
   - Contains `compactMetadata` field
   - Attribution: System

2. **Tool results**
   - Tool execution outputs
   - Attribution: System or Tool Result

3. **Meta messages**
   - Field: `isMeta: true`
   - Session metadata
   - Attribution: System

4. **Error messages**
   - Field: `isError: true`
   - Error reports
   - Attribution: System

## Attribution Rules

### Compact Operations

**Detection**:
```python
if msg.subtype == "compact_boundary" or msg.compact_metadata:
    actual_type = "system"
```

**Attribution**: "System [Compact]"

### Tool Results

**Detection**:
```python
if msg.tool_result is not None:
    actual_type = "system"
```

**Attribution**: "Tool Result"

### Meta Messages

**Detection**:
```python
if msg.is_meta:
    actual_type = "system"
```

**Attribution**: "System [Metadata]" or filter

## Attribution Function

```python
def get_attribution(msg: Message) -> str:
    """Determine message attribution."""

    # System messages
    if msg.subtype == "compact_boundary" or msg.compact_metadata:
        return "System [Compact]"

    if msg.is_meta:
        return "System [Metadata]"

    if msg.is_error:
        return "System [Error]"

    if msg.tool_result is not None:
        return f"Tool Result [{msg.tool_name}]"

    # Sidechain messages
    if msg.is_sidechain:
        if msg.msg_type == "user":
            return "Claude [as user]"
        agent = msg.sidechain_agent or "sub-agent"
        return f"Agent [{agent}]"

    # Standard messages
    if msg.msg_type == "user":
        if not msg.user_type or msg.user_type == "human":
            return "User"
        return f"User [{msg.user_type}]"

    if msg.msg_type == "assistant":
        return "Assistant"

    if msg.msg_type == "system":
        return "System"

    return f"Unknown [{msg.msg_type}]"
```

## Display Format

### Compact Operations

```
- **System [Compact]** · 2025-01-27 10:00 AM PST
  📦 CONVERSATION COMPACTED
  - Trigger: automatic (token limit)
  - Pre-compact tokens: 155,000
```

### Tool Results

```
- **Tool Result [Read]** · 2025-01-27 10:01 AM PST
  [tool result content]
```

### Meta Messages

```
- **System [Metadata]** · 2025-01-27 10:02 AM PST
  [metadata content]
```

## Validation

- Compact operations display as "System" not "User"
- Tool results distinguished from assistant messages
- Meta messages filtered or marked
- Error messages show as system-generated
- Sidechain messages maintain correct attribution
- User messages verified as human-generated