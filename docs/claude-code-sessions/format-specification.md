# Claude Code Session Format Specification

## Overview

Claude Code session logs use JSONL (JSON Lines) format where each line contains a complete JSON object representing a single message or event in the conversation.

## File Structure

### Location

```
~/.claude/projects/{project-name}/*.jsonl
```

- `{project-name}`: Derived from working directory path with `/` replaced by `-`
- Multiple JSONL files per project, one per session
- Files named with timestamp patterns

### JSONL Format

- One JSON object per line
- No commas between lines
- Each line is independently parseable
- Supports streaming/incremental parsing

## Core Message Structure

### Required Fields

Every message contains these core fields:

```json
{
  "type": "user|assistant|system|compact_system",
  "uuid": "unique-message-id",
  "timestamp": "2025-01-27T10:15:30.123Z",
  "sessionId": "session-identifier"
}
```

| Field       | Type   | Description                                    |
| ----------- | ------ | ---------------------------------------------- |
| `type`      | string | Message type (see Message Types documentation) |
| `uuid`      | string | Unique identifier for this message             |
| `timestamp` | string | ISO 8601 timestamp with milliseconds           |
| `sessionId` | string | Groups messages within a session               |

### Common Optional Fields

```json
{
  "parentUuid": "parent-message-id",
  "logicalParentUuid": "original-parent-before-compact",
  "message": "Message content",
  "isSidechain": true,
  "userType": "external",
  "subtype": "tool_use|command|response",
  "toolName": "Read",
  "toolArguments": {"file_path": "/path/to/file"},
  "isMeta": true,
  "isDeleted": true,
  "isAborted": true
}
```

| Field               | Type    | Description                                                              |
| ------------------- | ------- | ------------------------------------------------------------------------ |
| `parentUuid`        | string  | Reference to parent message (creates DAG structure)                      |
| `logicalParentUuid` | string  | Original parent reference preserved across compact boundaries            |
| `message`           | string  | Text content of the message                                              |
| `isSidechain`       | boolean | Marks sidechain messages (sub-agent conversations)                       |
| `userType`          | string  | "external" for non-human users (Claude in sidechains)                    |
| `subtype`           | string  | Specific message subtype for categorization                              |
| `toolName`          | string  | Name of the tool being invoked (for tool_use subtype)                    |
| `toolArguments`     | object  | JSON object containing tool parameters                                   |
| `isMeta`            | boolean | Marks metadata messages                                                  |
| `isDeleted`         | boolean | Soft deletion flag                                                       |
| `isAborted`         | boolean | Marks aborted operations or cancelled messages                           |

## Message Type Structures

### User Message

```json
{
  "type": "user",
  "uuid": "msg-001",
  "parentUuid": "msg-000",
  "timestamp": "2025-01-27T10:00:00Z",
  "sessionId": "session-123",
  "message": "Create a Python script",
  "userType": "human"
}
```

### Assistant Message

```json
{
  "type": "assistant",
  "uuid": "msg-002",
  "parentUuid": "msg-001",
  "timestamp": "2025-01-27T10:00:05Z",
  "sessionId": "session-123",
  "message": "I'll create a Python script for you.",
  "subtype": "response"
}
```

### Sidechain Message

```json
{
  "type": "user",
  "uuid": "msg-003",
  "parentUuid": "msg-002",
  "timestamp": "2025-01-27T10:00:10Z",
  "sessionId": "session-123",
  "message": "Analyze this codebase for potential improvements",
  "isSidechain": true,
  "userType": "external"
}
```

### Tool Use Message

```json
{
  "type": "assistant",
  "uuid": "msg-004",
  "parentUuid": "msg-003",
  "timestamp": "2025-01-27T10:00:15Z",
  "sessionId": "session-123",
  "subtype": "tool_use",
  "toolName": "Read",
  "toolArguments": {
    "file_path": "/path/to/file.py"
  }
}
```

**Common Tool Names**:
- `Read` - File reading operations
- `Edit` - File modification
- `Write` - File creation
- `Bash` - Shell command execution
- `TodoWrite` - Task management
- `Task` - Sub-agent delegation
- `Grep` - Search operations
- `WebSearch` - Web search queries

### System Message

```json
{
  "type": "system",
  "uuid": "msg-005",
  "parentUuid": "msg-004",
  "timestamp": "2025-01-27T10:00:20Z",
  "sessionId": "session-123",
  "message": "File read successfully"
}
```

### Compact System Message

```json
{
  "type": "compact_system",
  "uuid": "msg-006",
  "parentUuid": "msg-005",
  "timestamp": "2025-01-27T10:00:25Z",
  "sessionId": "session-123",
  "message": "conversation_compacted",
  "metadata": {
    "preservedMessages": 10,
    "totalMessages": 100
  }
}
```

## Data Relationships

### Message DAG Structure

Messages form a Directed Acyclic Graph (DAG) through `parentUuid` references:

```
msg-001 (user: "Hello")
  └── msg-002 (assistant: "Hi there")
      ├── msg-003 (user: "Write code" - edited)
      │   └── msg-004 (assistant: "Here's the code")
      └── msg-005 (user: "Explain this" - original)
          └── msg-006 (assistant: "Let me explain")
```

### Sidechain Relationships

Sidechains create inline sub-conversations:

```
msg-001 (user: "Analyze my project")
  └── msg-002 (assistant: "I'll analyze using a specialist")
      └── msg-003 (user: "Analyze codebase" - sidechain start, userType: external)
          └── msg-004 (assistant: "Analyzing..." - sub-agent response)
              └── msg-005 (user: "Focus on performance" - Claude continues)
                  └── msg-006 (assistant: "Performance analysis..." - sub-agent)
                      └── msg-007 (assistant: "Based on analysis..." - main thread resumes)
```

## Special Patterns

### Orphaned Messages

Messages with non-existent `parentUuid` values are common and expected:

```json
{
  "type": "user",
  "uuid": "msg-100",
  "parentUuid": "msg-from-previous-session",  // Does not exist in current file
  "timestamp": "2025-01-27T10:00:00Z",
  "sessionId": "session-123",
  "message": "Continue from before"
}
```

**Production Statistics**:
- 15-20% of messages in compacted sessions are orphaned
- Sessions average 8+ compact operations
- Orphans cluster at compact boundaries
- Most orphans maintain `logicalParentUuid` for continuity tracking

**Important**: Orphaned messages should be treated as conversation roots, not errors. They commonly occur:
- After compact operations (preserved messages lose their parent references)
- When referencing messages from previous sessions
- During session restoration after crashes
- At the beginning of resumed conversations

### Logical Parent UUID Pattern

The `logicalParentUuid` field maintains conversation continuity across compact boundaries:

```json
[
  // Before compact
  {
    "uuid": "msg-001",
    "parentUuid": "msg-000",
    "message": "Original conversation"
  },

  // Compact operation occurs
  {
    "type": "compact_system",
    "message": "conversation_compacted"
  },

  // After compact - parentUuid orphaned but logical parent preserved
  {
    "uuid": "msg-002",
    "parentUuid": "msg-001",  // May not exist after compact
    "logicalParentUuid": "msg-000",  // Original parent preserved
    "message": "Continued conversation"
  }
]
```

### Multi-Turn Sidechains

Sidechains often contain multiple exchanges:

```json
[
  {
    "type": "user",
    "isSidechain": true,
    "userType": "external",
    "message": "Initial task"
  },
  { "type": "assistant", "isSidechain": true, "message": "Working on it" },
  {
    "type": "user",
    "isSidechain": true,
    "userType": "external",
    "message": "Additional instruction"
  },
  {
    "type": "assistant",
    "isSidechain": true,
    "message": "Understood, continuing"
  },
  {
    "type": "user",
    "isSidechain": true,
    "userType": "external",
    "message": "One more thing"
  },
  { "type": "assistant", "isSidechain": true, "message": "Final response" }
]
```

### Task Delegation Pattern

The task prompt in parent assistant message matches first sidechain message:

```json
[
  {
    "type": "assistant",
    "uuid": "parent-001",
    "message": "I'll delegate to analyzer: 'Review this code for bugs'"
  },
  {
    "type": "user",
    "parentUuid": "parent-001",
    "isSidechain": true,
    "message": "Review this code for bugs"
  }
]
```

### Compact Mode Boundaries

Compact operations create special boundaries:

```json
[
  { "type": "compact_system", "message": "conversation_compacting" },
  { "type": "compact_system", "message": "conversation_compacted" },
  { "type": "compact_system", "message": "conversation_restored" }
]
```

**Compact Operation Flow**:
1. `conversation_compacting` - Marks the start of compact operation
2. Messages become orphaned as their parents are removed
3. `conversation_compacted` - Marks successful completion
4. Preserved messages may include `logicalParentUuid` for continuity
5. `conversation_restored` - Marks return to normal mode

### Aborted Operations

Messages can be marked as aborted when operations are cancelled:

```json
{
  "type": "assistant",
  "uuid": "msg-100",
  "parentUuid": "msg-099",
  "timestamp": "2025-01-27T10:00:00Z",
  "sessionId": "session-123",
  "subtype": "tool_use",
  "toolName": "Bash",
  "isAborted": true,
  "message": "Operation cancelled by user"
}
```

### Deleted Messages

Soft deletion preserves message structure while marking content as removed:

```json
{
  "type": "user",
  "uuid": "msg-200",
  "parentUuid": "msg-199",
  "timestamp": "2025-01-27T10:00:00Z",
  "sessionId": "session-123",
  "isDeleted": true,
  "message": "[Content removed]"
}
```

## Field Value Specifications

### Timestamps

- ISO 8601 format: `YYYY-MM-DDTHH:mm:ss.sssZ`
- Always UTC timezone
- Millisecond precision

### UUIDs

- Unique string identifiers
- Format varies (may be standard UUID or custom format)
- Must be unique within session

### Message Types

- `user`: Human or AI user input
- `assistant`: Claude or sub-agent response
- `system`: System messages and tool results
- `compact_system`: Compaction-related messages

### Subtypes

- `tool_use`: Tool invocation
- `command`: Command execution
- `response`: Standard response
- `thinking`: Internal reasoning
- Various tool-specific subtypes

### User Types

- `human`: Default human user
- `external`: Non-human user (Claude in sidechains)
- May be undefined for standard messages

## Validation Rules

1. Every message must have `type`, `uuid`, `timestamp`, `sessionId`
2. `parentUuid` may reference non-existent messages (orphans are valid)
3. `logicalParentUuid` preserves original parent across compacts
4. `isSidechain` only appears on sidechain messages
5. `userType: "external"` implies sidechain context (Claude as user)
6. Timestamps must be chronologically ordered within chains
7. Tool use messages must have `toolName` when `subtype: "tool_use"`
8. `toolArguments` must be valid JSON object when present
9. Orphaned messages (15-20% typical) should be treated as roots
10. Multiple compact operations per session are normal (8+ average)

## Production-Validated Patterns

### Typical Session Characteristics

Based on production data analysis:

- **Message volume**: Sessions range from hundreds to thousands of messages
- **Compact frequency**: Average 8+ compacts per long session
- **Orphan rate**: 15-20% of messages post-compact
- **Sidechain depth**: Often 3-6 exchanges per delegation
- **Tool usage**: Heavy use of Read, Edit, Bash, Task tools
- **Parent chain depth**: Can exceed 100+ messages in active sessions

### Message Flow Examples

#### Standard Development Flow
```json
[
  {"type": "user", "message": "Fix the bug in auth.py"},
  {"type": "assistant", "message": "I'll examine the file", "subtype": "response"},
  {"type": "assistant", "subtype": "tool_use", "toolName": "Read", "toolArguments": {"file_path": "/auth.py"}},
  {"type": "system", "message": "[File contents]"},
  {"type": "assistant", "message": "Found the issue", "subtype": "response"},
  {"type": "assistant", "subtype": "tool_use", "toolName": "Edit", "toolArguments": {"file_path": "/auth.py", "old_string": "bug", "new_string": "fix"}},
  {"type": "system", "message": "File edited successfully"}
]
```

#### Complex Sidechain with Multiple Tools
```json
[
  {"type": "assistant", "uuid": "main-001", "message": "Delegating to analyzer"},
  {"type": "user", "parentUuid": "main-001", "isSidechain": true, "userType": "external", "message": "Analyze the codebase"},
  {"type": "assistant", "isSidechain": true, "subtype": "tool_use", "toolName": "Grep", "toolArguments": {"pattern": "TODO"}},
  {"type": "system", "isSidechain": true, "message": "[Search results]"},
  {"type": "assistant", "isSidechain": true, "subtype": "tool_use", "toolName": "Read", "toolArguments": {"file_path": "/main.py"}},
  {"type": "system", "isSidechain": true, "message": "[File contents]"},
  {"type": "assistant", "isSidechain": true, "message": "Analysis complete: 5 TODOs found"},
  {"type": "assistant", "parentUuid": "main-001", "message": "Based on analysis, there are 5 TODOs to address"}
]
```

#### Compact Boundary Transition
```json
[
  // Pre-compact
  {"uuid": "old-001", "parentUuid": "old-000", "type": "user", "message": "Start of conversation"},
  {"uuid": "old-002", "parentUuid": "old-001", "type": "assistant", "message": "Working on it"},

  // Compact operation
  {"type": "compact_system", "message": "conversation_compacting"},
  {"type": "compact_system", "message": "conversation_compacted", "metadata": {"preservedMessages": 10, "totalMessages": 500}},

  // Post-compact (orphaned but with logical parent)
  {"uuid": "new-001", "parentUuid": "old-002", "logicalParentUuid": "old-001", "type": "user", "message": "Continue the work"},
  {"uuid": "new-002", "parentUuid": "new-001", "type": "assistant", "message": "Resuming from before"}
]
```

## Future Compatibility

- New fields may be added
- Existing field semantics preserved
- Parsers should handle unknown fields gracefully
- The `logicalParentUuid` pattern enables future DAG reconstruction
