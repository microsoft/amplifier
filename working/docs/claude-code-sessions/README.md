# Claude Code Sessions Documentation

## Overview

Claude Code generates session logs in JSONL format that capture the complete conversation history, including messages, tool invocations, and results. This documentation provides technical specifications for parsing and working with these session files.

## Session File Location

Session logs are stored in:
```
~/.claude/conversations/{project-name}/*.jsonl
```

Where `{project-name}` is derived from your working directory path with `/` replaced by `_` and `.` replaced by `_`.

Example: Working in `/home/user/repos/my.project` creates logs in `~/.claude/conversations/home_user_repos_my_project/`

## Documentation Structure

### Core Specifications

- **[Message Format](core/MESSAGE-FORMAT.md)** - JSONL structure and field definitions
- **[DAG Specification](core/DAG-SPECIFICATION.md)** - Directed Acyclic Graph structure of conversations
- **[Operations Reference](reference/OPERATIONS-REFERENCE.md)** - Session operations (compact, fork, rewind, clear, sidechains)

### Implementation Guides

- **[Parsing Implementation](implementation/PARSING-IMPLEMENTATION.md)** - Building parsers for session files
- **[Building Systems](implementation/BUILDING-SYSTEMS.md)** - Creating tools that work with sessions

### Resources

- **[Examples](examples/)** - Working code examples and reference implementations
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

## Quick Start for Developers

### Basic Session Structure

Each line in a JSONL session file represents one message:

```python
import json

# Read session file
with open("session.jsonl", "r") as f:
    messages = [json.loads(line) for line in f]

# Each message has these core fields
for msg in messages:
    uuid = msg["uuid"]           # Unique message identifier
    parent = msg["parentUuid"]    # Parent message UUID (creates DAG)
    type = msg["type"]            # Message type (human, assistant, etc.)
    timestamp = msg["timestamp"]  # Unix timestamp in milliseconds
```

### Tool Correlation

Tool invocations and results are correlated via IDs:

```python
# Tool invocation (in assistant message)
tool_use = {
    "type": "tool_use",
    "id": "toolu_01abc123...",  # Unique tool use ID
    "name": "Read",
    "input": {"file_path": "/path/to/file.py"}
}

# Corresponding tool result (separate message)
tool_result = {
    "type": "tool_result",
    "tool_use_id": "toolu_01abc123...",  # References tool_use.id
    "content": "File contents..."
}
```

### DAG Navigation

Messages form a Directed Acyclic Graph through parent-child relationships:

```python
# Build parent-child index
children_by_parent = {}
for msg in messages:
    parent_uuid = msg["parentUuid"]
    if parent_uuid not in children_by_parent:
        children_by_parent[parent_uuid] = []
    children_by_parent[parent_uuid].append(msg)

# Find active conversation path
def get_active_path(messages):
    path = []
    current = find_root_message(messages)

    while current:
        path.append(current)
        children = children_by_parent.get(current["uuid"], [])
        # Active child is typically the last one by file position
        # All branches remain valid in the DAG
        current = children[-1] if children else None

    return path
```

## Key Concepts

### Message Types

- **human**: User messages
- **assistant**: Claude's responses
- **tool_result**: Results from tool executions
- **compact_prelude**: Messages preserved during compaction
- **compact_recap**: Summary of compacted messages

### Operations

- **Compact**: Reduces context size by summarizing older messages
- **Fork**: Creates conversation branches when regenerating responses
- **Clear**: Resets the conversation
- **Sidechain**: Task-spawned sub-conversations with role reversal

### Performance Considerations

- **Small sessions** (<1MB): Load entire file into memory
- **Large sessions** (>100MB): Stream process line-by-line
- **Build indices** for UUID lookups (O(1) access)
- **Cache computed paths** to avoid recalculation

## See Also

- [Claude Code Desktop](https://claude.ai/download) - The Claude Code application