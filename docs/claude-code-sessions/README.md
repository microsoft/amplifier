# Claude Code Session Logs

## Overview

Claude Code generates session logs in JSONL (JSON Lines) format that record all interactions between users, Claude, and sub-agents. Each log file contains structured message data, tool invocations, and multi-agent communication through the sidechain architecture.

## Documentation

- **[Format Specification](format-specification.md)** - JSONL format, field definitions, and data structures
- **[Message Types](message-types.md)** - Message type definitions and structures
- **[Message Attribution](message-attribution.md)** - Attribution system specification
- **[Sidechain Architecture](sidechain-architecture.md)** - Multi-agent communication mechanism
- **[Parsing Guide](parsing-guide.md)** - Implementation reference
- **[Troubleshooting](troubleshooting.md)** - Error handling and edge cases

## Quick Start

### Finding Session Files

Session logs are stored in:

```
~/.claude/projects/{project-name}/*.jsonl
```

Where `{project-name}` is derived from your working directory path with `/` replaced by `-`.

Example: Working in `/home/user/repos/myproject` creates logs in `~/.claude/projects/-home-user-repos-myproject/`

### Basic Structure

Each line in a JSONL file is a complete JSON object representing one message:

```json
{
  "type": "user",
  "uuid": "msg-123",
  "parentUuid": "msg-122",
  "timestamp": "2025-01-27T10:15:30Z",
  "sessionId": "session-456",
  "message": "Hello Claude"
}
```

Messages form a directed acyclic graph (DAG) through `parentUuid` references, enabling:

- Linear conversation flows
- Branching for edits and "redo from here" operations
- Inline sidechains for sub-agent delegation
- Complex multi-agent orchestration

### Key Concepts

1. **Message DAG**: Messages form a directed acyclic graph through `uuid`/`parentUuid` references. File position determines active branches.

2. **Orphaned Messages**: Messages with non-existent `parentUuid` values become conversation roots. These occur after compact operations or when referencing previous sessions.

3. **Sidechains**: Inline sub-conversations marked with `isSidechain: true` and `userType: "external"`. Agent identification requires correlating Task tool invocations with sidechain messages.

4. **Compact Operations**: Context management operations that create new conversation roots. The `logicalParentUuid` field maintains continuity. Triggered manually via `/compact` or automatically at token thresholds.

5. **Agent Identification**: Sub-agent names appear in the Task tool's `subagent_type` parameter. Match Task invocations with subsequent sidechain messages using session IDs and timestamps.

## Sidechains

Sidechains implement multi-agent communication within session logs:

- Inline within the same session file
- Marked with `isSidechain: true`
- Parent assistant message becomes the "user" in sidechain context
- Support multi-turn sub-agent conversations

See [Sidechain Architecture](sidechain-architecture.md) for specifications.

## Processing Patterns

### Main Conversation Extraction

Filter messages where `isSidechain` is false or undefined.

### Sub-Agent Analysis

1. Locate Task tool invocations with `subagent_type` parameter
2. Match subsequent messages with `isSidechain: true`
3. Correlate using session IDs and timestamps

### Full Context Reconstruction

Build complete message DAG including sidechains and branches.

### Tool Usage Tracking

Examine `subtype` fields for tool invocations.

## Parser Implementation

### Requirements

- Stream parsing for memory efficiency
- DAG construction with cycle detection
- Orphaned message handling as roots
- Respect for `isDeleted` flags
- Separation of `isMeta` messages

### Edge Cases

1. **Orphaned Messages**: Treat as conversation roots
2. **Circular References**: Implement cycle detection
3. **I/O Errors**: Retry with exponential backoff for errno 5
4. **Multiple Compacts**: Handle sequential compact operations
5. **Branch Management**: Use file position for active branch determination

### Performance

- O(1) UUID lookups via dictionaries
- Multi-key indexing (parent, timestamp, session)
- Stream processing for large files
- Message chain caching

## File I/O

Cloud-synced directories require retry logic:

```python
import time
import json

def read_session_with_retry(file_path, max_retries=3):
    """Read session file with retry logic"""
    retry_delay = 0.1

    for attempt in range(max_retries):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return [json.loads(line) for line in lines if line.strip()]
        except OSError as e:
            if e.errno == 5 and attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise
```

## Format Version

Current session format features:

- `isSidechain`: Multi-agent conversation marking
- `userType`: User type identification ("external" for non-human)
- `sessionId`: Message correlation
- `logicalParentUuid`: Compact continuity
- `subagent_type`: Agent identification in Task tool


## References

1. [Format Specification](format-specification.md) - Field definitions
2. [Sidechain Architecture](sidechain-architecture.md) - Multi-agent patterns
3. [Troubleshooting](troubleshooting.md) - Error handling
4. [Parsing Guide](parsing-guide.md) - Implementation reference
5. Session logs location: `~/.claude/projects/`
