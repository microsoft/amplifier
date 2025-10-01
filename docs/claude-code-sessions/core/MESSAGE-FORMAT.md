# Claude Code Message Format Specification

This document provides the technical specification for the JSONL message format used in Claude Code session files.

## File Format

### JSONL Structure

Claude Code sessions use JSONL (JSON Lines) format:
- One JSON object per line
- No commas between lines
- Each line independently parseable
- Supports streaming/incremental parsing
- UTF-8 encoding

### File Location

```
~/.claude/conversations/{project-name}/*.jsonl
```

Where:
- `{project-name}`: Working directory path with `/` replaced by `_`
- Multiple JSONL files per project (one per session)
- Files named with timestamp patterns

## Core Message Structure

### Base Message Schema

Every message contains these fields:

```json
{
  "uuid": "msg_abc123def456",
  "parentUuid": "msg_parent789",
  "sessionId": "session_xyz",
  "type": "human" | "assistant" | "tool_result",
  "timestamp": 1738160130123,
  "version": "1.0.128",
  "message": { /* content object */ }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `uuid` | string | Yes | Unique identifier for this message |
| `parentUuid` | string\|null | Yes | Reference to parent message UUID or null for roots |
| `sessionId` | string | Yes | Groups messages within a session |
| `type` | string | Yes | Message type (see Message Types section) |
| `timestamp` | number | Yes | Unix timestamp in milliseconds |
| `version` | string | Yes* | Claude Code app version |
| `message` | object | Yes | Message content object |

*Note: `version` field may be absent in special messages

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `isSidechain` | boolean | Marks sidechain/subagent messages |
| `userType` | string | "external" for actual initiators |
| `isMeta` | boolean | System metadata messages |
| `isError` | boolean | Error messages |
| `isDeleted` | boolean | Soft deletion flag |
| `isAborted` | boolean | Cancelled/aborted operations |
| `compactMetadata` | object | Compact operation metadata |
| `subtype` | string | Message subtype for categorization |
| `is_active` | boolean | Marks active branch in fork |

## Message Types

### Human Message

User input messages:

```json
{
  "uuid": "msg_user_001",
  "parentUuid": "msg_assistant_000",
  "sessionId": "session_123",
  "type": "human",
  "timestamp": 1738160130123,
  "version": "1.0.128",
  "message": {
    "type": "message",
    "content": "Create a Python script to parse JSON files"
  }
}
```

### Assistant Message

Claude responses with tool invocations:

```json
{
  "uuid": "msg_assistant_002",
  "parentUuid": "msg_user_001",
  "sessionId": "session_123",
  "type": "assistant",
  "timestamp": 1738160135456,
  "version": "1.0.128",
  "message": {
    "type": "message",
    "content": [
      {
        "type": "text",
        "text": "I'll create a Python script to parse JSON files."
      },
      {
        "type": "tool_use",
        "id": "toolu_01abc123",
        "name": "Write",
        "input": {
          "file_path": "/parse_json.py",
          "content": "import json\n\ndef parse_json(file_path):\n    ..."
        }
      }
    ]
  }
}
```

### Tool Result Message

System-generated tool execution results:

```json
{
  "uuid": "msg_result_003",
  "parentUuid": "msg_assistant_002",
  "sessionId": "session_123",
  "type": "tool_result",
  "timestamp": 1738160136789,
  "version": "1.0.128",
  "message": {
    "type": "message",
    "content": [
      {
        "type": "tool_result",
        "tool_use_id": "toolu_01abc123",
        "content": "File created successfully",
        "is_error": false
      }
    ]
  }
}
```

## Message Content Structures

### Text Content

Simple text message:

```json
{
  "message": {
    "type": "message",
    "content": "This is a text message"
  }
}
```

### Mixed Content Array

Messages with multiple content types:

```json
{
  "message": {
    "type": "message",
    "content": [
      {
        "type": "text",
        "text": "Here's the analysis:"
      },
      {
        "type": "tool_use",
        "id": "toolu_xyz789",
        "name": "Read",
        "input": {
          "file_path": "/config.json"
        }
      }
    ]
  }
}
```

### Tool Invocation

Within assistant messages:

```json
{
  "type": "tool_use",
  "id": "toolu_unique_id",
  "name": "ToolName",
  "input": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

### Tool Result

Within tool_result messages:

```json
{
  "type": "tool_result",
  "tool_use_id": "toolu_unique_id",
  "content": "Tool execution result",
  "is_error": false
}
```

### Image Content

Binary data encoded as base64:

```json
{
  "type": "image",
  "source": {
    "type": "base64",
    "media_type": "image/png",
    "data": "iVBORw0KGgoAAAANSUhEUgA..."
  }
}
```

## Special Message Patterns

### Sidechain Messages

Messages in subagent conversations:

```json
{
  "uuid": "msg_sidechain_001",
  "parentUuid": "msg_task_invocation",
  "sessionId": "session_123",
  "type": "human",
  "timestamp": 1738160140000,
  "version": "1.0.128",
  "isSidechain": true,
  "userType": "external",
  "message": {
    "type": "message",
    "content": "Analyze this codebase for potential improvements"
  }
}
```

**Key Indicators**:
- `isSidechain: true` - Marks sidechain conversation
- `userType: "external"` - Actual initiator (Claude in sidechains)
- Role reversal: In sidechains, human type = Claude delegating, assistant = agent responding

### Compact Messages

Messages preserved during compaction:

```json
{
  "uuid": "msg_compact_001",
  "parentUuid": null,
  "sessionId": "session_123",
  "type": "compact_prelude",
  "timestamp": 1738160150000,
  "version": "1.0.128",
  "message": {
    "type": "message",
    "content": "Previous message content..."
  }
}
```

```json
{
  "uuid": "msg_recap_001",
  "parentUuid": "msg_compact_001",
  "sessionId": "session_123",
  "type": "compact_recap",
  "timestamp": 1738160151000,
  "version": "1.0.128",
  "message": {
    "type": "message",
    "content": "Summary of compacted conversation..."
  }
}
```

## Tool Specifications

### Common Tools

| Tool Name | Purpose | Common Parameters |
|-----------|---------|-------------------|
| `Read` | Read file contents | `file_path`, `limit`, `offset` |
| `Write` | Create/overwrite file | `file_path`, `content` |
| `Edit` | Modify file | `file_path`, `old_string`, `new_string` |
| `MultiEdit` | Multiple edits | `file_path`, `edits[]` |
| `Bash` | Execute commands | `command`, `timeout` |
| `TodoWrite` | Task management | `todos[]` |
| `Task` | Delegate to subagent | `subagent_type`, `prompt` |
| `Grep` | Search files | `pattern`, `path` |
| `WebSearch` | Web search | `query` |
| `WebFetch` | Fetch URL content | `url`, `prompt` |

## Tool Correlation

Tool invocations and results are correlated through IDs:

1. Assistant invokes tool with unique ID:
   ```json
   {"type": "tool_use", "id": "toolu_01xyz", "name": "Read", ...}
   ```

2. System returns result referencing that ID:
   ```json
   {"type": "tool_result", "tool_use_id": "toolu_01xyz", "content": "..."}
   ```

This ID-based correlation is the definitive method for matching invocations with results.

## Message Flow Examples

### Standard Development Flow

```
1. Human: "Fix the bug in auth.py"
2. Assistant: "I'll examine the file" + tool_use(Read, auth.py)
3. Tool Result: File contents
4. Assistant: "Found the issue" + tool_use(Edit, auth.py)
5. Tool Result: "File updated successfully"
```

### Task Delegation Flow

```
1. Assistant: "Delegating to specialist" + tool_use(Task, bug-hunter)
2. Sidechain Human (Claude): "Find bugs in auth module"
3. Sidechain Assistant (Agent): "Analyzing..." + tool_use(Read, auth.py)
4. Sidechain Tool Result: File contents
5. Sidechain Assistant: "Found 3 issues..."
6. Main Tool Result: Agent's findings
```

## Validation Rules

1. **Required Fields**: Every message must have core fields (uuid, parentUuid, sessionId, type, timestamp, message)

2. **UUID Uniqueness**: UUIDs must be unique within a session

3. **Parent References**: Messages reference parents to form DAG structure

4. **Tool Correlation**: Tool results must have `tool_use_id` matching a previous `tool_use.id`

5. **Sidechain Markers**: Sidechain messages must have `isSidechain: true`

6. **Content Structure**: `message.content` can be string or array of content objects

7. **Binary Encoding**: Images must be base64 encoded with proper media type

## Compatibility Notes

- Parsers must handle unknown fields gracefully
- New fields may be added in future versions
- Existing field semantics will be preserved
- Version field indicates Claude Code app version, not format version