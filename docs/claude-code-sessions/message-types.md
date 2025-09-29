# Message Type Specification

## Message Types

Claude Code sessions contain four primary message types:

| Type | Purpose | Source |
|------|---------|--------|
| `user` | User input messages | Human users or Claude (in sidechains) |
| `assistant` | AI responses and actions | Claude or sub-agents |
| `system` | System-generated messages | Claude Code infrastructure |
| `compact_system` | Conversation management | Compaction operations |

## User Messages (`type: "user"`)

### Field Specification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Always "user" |
| `uuid` | string | Yes | Unique message identifier |
| `timestamp` | string | Yes | ISO 8601 timestamp |
| `sessionId` | string | Yes | Session identifier |
| `message` | string | No | User input text |
| `parentUuid` | string | No | Parent message for threading |
| `isSidechain` | boolean | No | Marks sub-agent conversation |
| `userType` | string | No | "external" when Claude is user |

### Human User Message

```json
{
  "type": "user",
  "uuid": "msg-001",
  "parentUuid": "msg-000",
  "timestamp": "2025-01-27T10:00:00Z",
  "sessionId": "session-123",
  "message": "Please help me write a Python script"
}
```

### Claude as User (Sidechain)

```json
{
  "type": "user",
  "uuid": "msg-002",
  "parentUuid": "msg-001",
  "timestamp": "2025-01-27T10:00:05Z",
  "sessionId": "session-123",
  "message": "Analyze this code for potential improvements",
  "isSidechain": true,
  "userType": "external"
}
```

## Assistant Messages (`type: "assistant"`)

### Field Specification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Always "assistant" |
| `uuid` | string | Yes | Unique message identifier |
| `timestamp` | string | Yes | ISO 8601 timestamp |
| `sessionId` | string | Yes | Session identifier |
| `subtype` | string | No | Categorization of assistant action |
| `message` | string | No | Response text |
| `parentUuid` | string | No | Parent message for threading |
| `toolName` | string | No | Name of invoked tool (for tool_use) |
| `toolArguments` | object | No | Tool invocation parameters |
| `isSidechain` | boolean | No | Marks sub-agent response |

### Subtypes

| Subtype | Purpose | Contains |
|---------|---------|----------|
| `response` | Standard text response | message field with text |
| `tool_use` | Tool invocation | toolName and toolArguments |
| `thinking` | Internal reasoning | message with thinking content |
| `command` | Slash command execution | Command details |
| `error` | Error reporting | Error message and context |

### Response Message

```json
{
  "type": "assistant",
  "uuid": "msg-003",
  "parentUuid": "msg-002",
  "timestamp": "2025-01-27T10:00:10Z",
  "sessionId": "session-123",
  "message": "I'll help you create a Python script.",
  "subtype": "response"
}
```

### Tool Invocation

```json
{
  "type": "assistant",
  "uuid": "msg-004",
  "parentUuid": "msg-003",
  "timestamp": "2025-01-27T10:00:15Z",
  "sessionId": "session-123",
  "subtype": "tool_use",
  "toolName": "Write",
  "toolArguments": {
    "file_path": "/path/to/script.py",
    "content": "#!/usr/bin/env python3\n..."
  }
}
```

### Available Tools

- `Read`, `Write`, `Edit`, `MultiEdit` - File operations
- `Bash`, `BashOutput`, `KillShell` - Command execution
- `Grep`, `Glob` - Search operations
- `WebFetch`, `WebSearch` - Web operations
- `TodoWrite` - Task management
- `SlashCommand` - Command execution
- `Task` - Sub-agent delegation

## System Messages (`type: "system"`)

### Field Specification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Always "system" |
| `uuid` | string | Yes | Unique message identifier |
| `timestamp` | string | Yes | ISO 8601 timestamp |
| `sessionId` | string | Yes | Session identifier |
| `message` | string | No | System message content |
| `parentUuid` | string | No | Parent message for threading |
| `isError` | boolean | No | Marks error messages |
| `isMeta` | boolean | No | Metadata not shown to user |
| `subtype` | string | No | System message categorization |

### Subtypes

| Subtype | Purpose | Characteristics |
|---------|---------|-----------------|
| `tool_result` | Tool execution result | Follows tool_use messages |
| `error` | Error conditions | isError: true |
| `meta` | Metadata/configuration | isMeta: true |
| (none) | General system messages | Status updates, info |

### Tool Result

```json
{
  "type": "system",
  "uuid": "msg-006",
  "parentUuid": "msg-005",
  "timestamp": "2025-01-27T10:00:25Z",
  "sessionId": "session-123",
  "subtype": "tool_result",
  "message": "File created successfully at: /path/to/script.py"
}
```

### Error Message

```json
{
  "type": "system",
  "uuid": "msg-007",
  "parentUuid": "msg-006",
  "timestamp": "2025-01-27T10:00:30Z",
  "sessionId": "session-123",
  "message": "Error: Permission denied writing to /protected/path",
  "isError": true,
  "subtype": "error"
}
```

## Compact System Messages (`type: "compact_system"`)

### Field Specification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Always "compact_system" |
| `uuid` | string | Yes | Unique message identifier |
| `timestamp` | string | Yes | ISO 8601 timestamp |
| `sessionId` | string | Yes | Session identifier |
| `message` | string | Yes | Operation type |
| `parentUuid` | string | No | Parent message for threading |
| `metadata` | object | No | Operation details/statistics |

### Operation Types

| Message Value | Operation | Purpose |
|---------------|-----------|---------|
| `conversation_compacting` | Start compaction | Marks beginning of compaction |
| `conversation_compacted` | Compaction complete | Contains compression statistics |
| `conversation_restored` | Restoration complete | Full context restored |
| `conversation_restoring` | Start restoration | Beginning context restoration |

### Compaction Messages

```json
// Start
{
  "type": "compact_system",
  "uuid": "msg-009",
  "parentUuid": "msg-008",
  "timestamp": "2025-01-27T10:00:40Z",
  "sessionId": "session-123",
  "message": "conversation_compacting"
}

// Complete
{
  "type": "compact_system",
  "uuid": "msg-010",
  "parentUuid": "msg-009",
  "timestamp": "2025-01-27T10:00:45Z",
  "sessionId": "session-123",
  "message": "conversation_compacted",
  "metadata": {
    "preservedMessages": 15,
    "totalMessages": 150,
    "compressionRatio": 0.1
  }
}
```

## Tool Invocation Patterns

### Request-Response Pattern

```
assistant (tool_use) → system (tool_result)
```

### Parallel Tool Execution

```
assistant (tool_use 1)
assistant (tool_use 2)
assistant (tool_use 3)
  → system (result 1)
  → system (result 2)
  → system (result 3)
```

## Message State Flags

### Sidechain Context

When `isSidechain: true`:

| Role | Main Conversation | Sidechain |
|------|------------------|-----------|
| User | Human | Claude (external) |
| Assistant | Claude | Sub-agent |

### Special Flags

| Flag | Type | Purpose |
|------|------|---------|
| `isSidechain` | boolean | Message is part of sub-agent conversation |
| `isDeleted` | boolean | Message marked for soft deletion |
| `isAborted` | boolean | Operation was cancelled |
| `isMeta` | boolean | Infrastructure metadata |
| `isError` | boolean | Message contains error information |

## Message Flow Patterns

### Linear Conversation

```
user → assistant → user → assistant
```

### Tool Usage

```
user → assistant (response) → assistant (tool_use) → system (result) → assistant (response)
```

### Sidechain Delegation

```
user → assistant → user[sidechain] → assistant[sidechain] → assistant
```

### Error Recovery

```
user
  └── assistant (attempt 1)
      └── assistant (tool_use)
          └── system (error)
              └── assistant (alternative approach)
                  └── assistant (tool_use: different tool)
                      └── system (success)
```

### Compaction Flow

```
user (/compact command)
  └── compact_system (conversation_compacting)
      └── compact_system (conversation_compacted)
          └── assistant (acknowledgment)
```

## Message Chain Branching

When users edit messages, new branches form:

```
Original:
user(1) → assistant(2) → user(3) → assistant(4)

After editing message 3:
user(1) → assistant(2) → user(3) → assistant(4)
                      ↘
                       user(3') → assistant(4')
```

## Validation Requirements

### Field Requirements

| Message Type | Required Fields | Conditional Fields |
|--------------|-----------------|-------------------|
| user | type, uuid, timestamp, sessionId | message (unless command) |
| assistant | type, uuid, timestamp, sessionId | toolName/Args (if tool_use) |
| system | type, uuid, timestamp, sessionId | message |
| compact_system | type, uuid, timestamp, sessionId, message | metadata (for compacted) |

### Integrity Rules

1. UUID must be globally unique within session
2. Timestamps must be ISO 8601 format
3. parentUuid must reference existing message or be null
4. Message structure must match declared type
5. Tool invocations must include toolName and toolArguments
6. Sidechain messages must have consistent isSidechain flag