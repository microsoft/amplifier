# Claude Code Session Logs Documentation

## Overview

Claude Code generates comprehensive session logs that capture every interaction between users, Claude, and specialized sub-agents. These logs are stored as JSONL (JSON Lines) files and contain rich metadata about conversations, tool usage, and AI-to-AI communication patterns through an advanced multi-agent architecture.

This documentation provides the definitive specification for understanding, parsing, and working with Claude Code session logs, based on extensive analysis of production session data including validation against 18 real compact operations and thousands of messages.

## Documentation Structure

### Core Specifications

- **[Format Specification](format-specification.md)** - Complete JSONL format, field definitions, data structures, and validation rules
- **[Message Types](message-types.md)** - All message types, their purposes, structures, and common patterns
- **[Sidechain Architecture](sidechain-architecture.md)** - Complete documentation of the sidechain mechanism for multi-agent communication
- **[Parsing Guide](parsing-guide.md)** - Practical implementation guidance with production-ready code examples
- **[Troubleshooting](troubleshooting.md)** - Common issues, solutions, and edge cases from production

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

### Critical Concepts

1. **Message DAG**: Messages link via `uuid`/`parentUuid` to form conversation trees. File position determines active vs abandoned branches.

2. **Orphaned Messages**: Messages with non-existent `parentUuid` are treated as conversation roots. This is common and expected, not an error condition. These typically occur after compact operations or when referencing messages from previous sessions.

3. **Sidechains**: Inline sub-conversations where Claude delegates tasks to specialized agents. Marked with `isSidechain: true` and `userType: "external"`. The agent name comes from the Task tool's `subagent_type` parameter - track Task invocations to identify which agent is being used.

4. **Compact Operations**: Context management that creates new conversation roots while maintaining logical flow through `logicalParentUuid`. Occurs manually via `/compact` (39% of cases) or automatically (~155k tokens, 61% of cases). Sessions commonly have 8+ compacts.

5. **Agent Identification**: Sub-agent names are found in the Task tool's `subagent_type` parameter, not in sidechain messages. Correlate Task tool invocations with subsequent sidechains using session IDs and timestamps.

## Understanding Sidechains

Sidechains are the architectural foundation of Claude Code's multi-agent system:

- They are **inline** within the same session file (not separate files)
- Marked with `isSidechain: true` on messages
- The parent assistant message becomes the "user" in the sidechain context
- Enable Claude to delegate tasks to specialized sub-agents
- Support multi-turn conversations between Claude and sub-agents

For complete details, see [Sidechain Architecture](sidechain-architecture.md).

## Common Use Cases

### Extracting User-Claude Conversations

Filter messages where `isSidechain` is false or undefined to get the main conversation thread.

### Analyzing Sub-Agent Usage

1. Look for Task tool invocations with `subagent_type` parameter to identify agent names
2. Find subsequent messages with `isSidechain: true` to see the delegation
3. Correlate using session IDs and timestamps

### Reconstructing Full Context

Build the complete message DAG to see all interactions, including sidechains and edits.

### Understanding Tool Usage

Examine `subtype` fields to track tool invocations, file operations, and command execution.

## Implementation Considerations

### Parser Requirements

- **Streaming**: Parse files line by line for memory efficiency
- **DAG Building**: Create `uuid`/`parentUuid` mapping with cycle detection
- **Orphan Handling**: Treat messages with missing parents as new roots
- **Deletion Respect**: Honor `isDeleted` flags when reconstructing
- **Metadata Separation**: Handle `isMeta` messages as metadata, not content

### Critical Edge Cases

1. **Orphaned Messages**: Common after compacts - treat as roots, not errors
2. **Circular References**: Implement defensive cycle detection in DAG building
3. **Cloud Sync I/O Errors**: Implement retry logic with exponential backoff for OSError errno 5
4. **Multiple Compacts**: Sessions can have 8+ compact operations
5. **Branch Management**: File position determines active branch in "redo from here" scenarios

### Performance Optimization

- Use dictionaries for O(1) UUID lookups
- Index messages by multiple keys (parent, timestamp, session)
- Stream process for files > 100MB
- Cache frequently accessed message chains

## File I/O Considerations

When working with session files in cloud-synced directories (OneDrive, Dropbox, iCloud):

```python
import time
import json
from pathlib import Path

def read_session_with_retry(file_path, max_retries=3):
    """Read session file with retry logic for cloud sync issues"""
    retry_delay = 0.1

    for attempt in range(max_retries):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            return [json.loads(line) for line in lines if line.strip()]
        except OSError as e:
            if e.errno == 5 and attempt < max_retries - 1:
                if attempt == 0:
                    print(f"Cloud sync delay detected. Retrying...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise
```

## Version Compatibility

This documentation covers the current Claude Code session format. Key features:

- **Sidechain Support**: `isSidechain` field for multi-agent conversations
- **User Type Distinction**: `userType: "external"` for non-human users
- **Session Grouping**: `sessionId` for message correlation
- **Logical Parent Links**: `logicalParentUuid` for compact continuity
- **Task Tool Integration**: Agent identification via `subagent_type` parameter

## Production Statistics

Based on analysis of production session logs:

- **Compact Frequency**: Manual (39%) via `/compact`, Automatic (61%) at ~155k tokens
- **Compact Count**: Sessions commonly have 8+ compact operations
- **Orphan Rate**: ~15-20% of messages after compacts
- **Sidechain Depth**: Up to 20+ turns in complex delegations
- **Tool Diversity**: 15+ different tool types in active sessions

## Next Steps

1. Review [Format Specification](format-specification.md) for complete field definitions
2. Study [Sidechain Architecture](sidechain-architecture.md) for multi-agent patterns
3. Check [Troubleshooting](troubleshooting.md) for common issues and solutions
4. Use [Parsing Guide](parsing-guide.md) to build production-ready parsers
5. Examine real session logs at `~/.claude/projects/` for practical examples

---

_This documentation represents the definitive specification for Claude Code session logs, validated against thousands of production messages and extensive real-world usage._
