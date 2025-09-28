# Claude Code Message Types

## Overview

Claude Code sessions contain various message types that represent different aspects of the conversation flow, tool usage, and system operations. This document provides comprehensive technical documentation of all message types, their structures, and relationships.

## Primary Message Types

Claude Code uses four primary message types to represent all interactions in a session:

| Type | Purpose | Source |
|------|---------|--------|
| `user` | User input messages | Human users or Claude (in sidechains) |
| `assistant` | AI responses and actions | Claude or sub-agents |
| `system` | System-generated messages | Claude Code infrastructure |
| `compact_system` | Conversation management | Compaction operations |

### 1. User Messages (`type: "user"`)

Represents input from either a human user or Claude acting as a user in sidechains.

#### Core Fields

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

#### Standard User Message (Human)

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

**Characteristics:**
- No `isSidechain` or `userType` fields
- Contains direct human input
- May include commands (e.g., `/compact`)

#### Sidechain User Message (Claude as User)

When Claude delegates to sub-agents, it acts as the user in those conversations:

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

**Key Identifiers:**
- `userType: "external"` - Non-human user (Claude in this context)
- `isSidechain: true` - Part of sub-agent conversation
- Message content typically contains delegated tasks

### 2. Assistant Messages (`type: "assistant"`)

Represents responses from Claude or sub-agents, including text responses, tool invocations, and reasoning.

#### Core Fields

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

#### Message Subtypes

| Subtype | Purpose | Contains |
|---------|---------|----------|
| `response` | Standard text response | message field with text |
| `tool_use` | Tool invocation | toolName and toolArguments |
| `thinking` | Internal reasoning | message with thinking content |
| `command` | Slash command execution | Command details |
| `error` | Error reporting | Error message and context |

#### Standard Response

```json
{
  "type": "assistant",
  "uuid": "msg-003",
  "parentUuid": "msg-002",
  "timestamp": "2025-01-27T10:00:10Z",
  "sessionId": "session-123",
  "message": "I'll help you create a Python script. Let me start by understanding your requirements.",
  "subtype": "response"
}
```

#### Tool Use Message

Tool invocations are the primary way Claude performs actions:

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

**Common Tool Names:**
- `Read`, `Write`, `Edit`, `MultiEdit` - File operations
- `Bash`, `BashOutput`, `KillShell` - Command execution
- `Grep`, `Glob` - Search operations
- `WebFetch`, `WebSearch` - Web operations
- `TodoWrite` - Task management
- `SlashCommand` - Command execution

#### Thinking Message

Internal reasoning that may be hidden from UI display:

```json
{
  "type": "assistant",
  "uuid": "msg-005",
  "parentUuid": "msg-004",
  "timestamp": "2025-01-27T10:00:20Z",
  "sessionId": "session-123",
  "subtype": "thinking",
  "message": "The user needs a script that processes data files. I should create a modular design..."
}
```

### 3. System Messages (`type: "system"`)

System-generated messages including tool results, errors, metadata, and infrastructure communications.

#### Core Fields

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

#### Message Subtypes

| Subtype | Purpose | Characteristics |
|---------|---------|-----------------|
| `tool_result` | Tool execution result | Follows tool_use messages |
| `error` | Error conditions | isError: true |
| `meta` | Metadata/configuration | isMeta: true |
| (none) | General system messages | Status updates, info |

#### Tool Result

Most common system message, reporting tool execution outcomes:

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

**Patterns:**
- Always follows a tool_use message
- Contains execution outcome (success/failure)
- May include output data or error details

#### Error Message

System errors during operations:

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

**Common Error Types:**
- File I/O errors (permissions, not found)
- Tool execution failures
- Network/API errors
- Validation failures

#### System Reminder

Infrastructure metadata and context management:

```json
{
  "type": "system",
  "uuid": "msg-008",
  "parentUuid": "msg-007",
  "timestamp": "2025-01-27T10:00:35Z",
  "sessionId": "session-123",
  "message": "<system-reminder>Context limit approaching</system-reminder>",
  "isMeta": true,
  "subtype": "meta"
}
```

**Characteristics:**
- Often wrapped in `<system-reminder>` tags
- May contain context instructions
- Not displayed to end users (isMeta: true)

### 4. Compact System Messages (`type: "compact_system"`)

Specialized messages that mark conversation compaction operations to manage context window limits.

#### Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Always "compact_system" |
| `uuid` | string | Yes | Unique message identifier |
| `timestamp` | string | Yes | ISO 8601 timestamp |
| `sessionId` | string | Yes | Session identifier |
| `message` | string | Yes | Operation type |
| `parentUuid` | string | No | Parent message for threading |
| `metadata` | object | No | Operation details/statistics |

#### Operation Types

| Message Value | Operation | Purpose |
|---------------|-----------|---------|
| `conversation_compacting` | Start compaction | Marks beginning of compaction |
| `conversation_compacted` | Compaction complete | Contains compression statistics |
| `conversation_restored` | Restoration complete | Full context restored |
| `conversation_restoring` | Start restoration | Beginning context restoration |

#### Compaction Start

Marks the beginning of a compaction operation:

```json
{
  "type": "compact_system",
  "uuid": "msg-009",
  "parentUuid": "msg-008",
  "timestamp": "2025-01-27T10:00:40Z",
  "sessionId": "session-123",
  "message": "conversation_compacting"
}
```

#### Compaction Complete

Indicates successful compaction with statistics:

```json
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

**Metadata Fields:**
- `preservedMessages` - Count of messages kept in context
- `totalMessages` - Original message count
- `compressionRatio` - Preserved/total ratio

#### Restoration

Marks successful restoration of full conversation context:

```json
{
  "type": "compact_system",
  "uuid": "msg-011",
  "parentUuid": "msg-010",
  "timestamp": "2025-01-27T10:00:50Z",
  "sessionId": "session-123",
  "message": "conversation_restored"
}
```

**Compaction Workflow:**
1. User invokes `/compact` command
2. System emits `conversation_compacting`
3. Context reduced to essential messages
4. System emits `conversation_compacted` with stats
5. Later: User requests restoration
6. System emits `conversation_restoring`
7. Full context restored
8. System emits `conversation_restored`

## Tool Invocation and Result Patterns

Tool operations follow a consistent request-response pattern with assistant messages for invocation and system messages for results.

### Pattern Structure

```
assistant (tool_use) → system (tool_result)
```

Multiple tools can be invoked in parallel:
```
assistant (tool_use 1)
assistant (tool_use 2)
assistant (tool_use 3)
  → system (result 1)
  → system (result 2)
  → system (result 3)
```

### File Operations

#### Read Tool

**Invocation:**
```json
{
  "type": "assistant",
  "subtype": "tool_use",
  "toolName": "Read",
  "toolArguments": {
    "file_path": "/home/user/project/main.py",
    "limit": 100,
    "offset": 0
  }
}
```

**Result:**
```json
{
  "type": "system",
  "subtype": "tool_result",
  "message": "1→def main():\n2→    print('Hello')\n..."
}
```

#### Write Tool

**Invocation:**
```json
{
  "type": "assistant",
  "subtype": "tool_use",
  "toolName": "Write",
  "toolArguments": {
    "file_path": "/home/user/project/new_file.py",
    "content": "# Python code here"
  }
}
```

**Result:**
```json
{
  "type": "system",
  "subtype": "tool_result",
  "message": "File written successfully: /home/user/project/new_file.py"
}
```

#### Edit Tool

**Invocation:**
```json
{
  "type": "assistant",
  "subtype": "tool_use",
  "toolName": "Edit",
  "toolArguments": {
    "file_path": "/home/user/project/main.py",
    "old_string": "def old_function():",
    "new_string": "def new_function():",
    "replace_all": false
  }
}
```

**Result:**
```json
{
  "type": "system",
  "subtype": "tool_result",
  "message": "File edited successfully. Changes:\n-def old_function():\n+def new_function():"
}
```

### Command Execution

#### Bash Command

**Invocation:**
```json
{
  "type": "assistant",
  "subtype": "tool_use",
  "toolName": "Bash",
  "toolArguments": {
    "command": "python script.py",
    "description": "Run the Python script",
    "timeout": 30000,
    "run_in_background": false
  }
}
```

**Result:**
```json
{
  "type": "system",
  "subtype": "tool_result",
  "message": "Script executed successfully\nOutput: Processing complete\n\nExit code: 0"
}
```

### Search Operations

#### Grep Search

**Invocation:**
```json
{
  "type": "assistant",
  "subtype": "tool_use",
  "toolName": "Grep",
  "toolArguments": {
    "pattern": "TODO|FIXME",
    "path": "/home/user/project",
    "output_mode": "files_with_matches",
    "-i": true
  }
}
```

**Result:**
```json
{
  "type": "system",
  "subtype": "tool_result",
  "message": "/home/user/project/main.py\n/home/user/project/utils.py"
}
```

#### Glob Pattern

**Invocation:**
```json
{
  "type": "assistant",
  "subtype": "tool_use",
  "toolName": "Glob",
  "toolArguments": {
    "pattern": "**/*.py",
    "path": "/home/user/project"
  }
}
```

**Result:**
```json
{
  "type": "system",
  "subtype": "tool_result",
  "message": "main.py\nutils.py\ntests/test_main.py"
}
```

### Task Management

#### TodoWrite

**Invocation:**
```json
{
  "type": "assistant",
  "subtype": "tool_use",
  "toolName": "TodoWrite",
  "toolArguments": {
    "todos": [
      {
        "content": "Analyze requirements",
        "status": "completed",
        "activeForm": "Analyzing requirements"
      },
      {
        "content": "Implement solution",
        "status": "in_progress",
        "activeForm": "Implementing solution"
      }
    ]
  }
}
```

**Result:**
```json
{
  "type": "system",
  "subtype": "tool_result",
  "message": "✓ Analyzing requirements\n⚡ Implementing solution"
}
```

## Special Message Flags and States

### Sidechain Messages

Sidechains represent sub-agent conversations where Claude delegates work. In these contexts:

- Claude becomes the "user" asking questions
- Sub-agents provide "assistant" responses
- All messages have `isSidechain: true`

**Semantic Changes in Sidechains:**
| Role | Main Conversation | Sidechain |
|------|------------------|-----------|
| User | Human | Claude (external) |
| Assistant | Claude | Sub-agent |

**Example Sidechain Flow:**
```json
// Main conversation
{ "type": "user", "message": "Analyze this code" }
{ "type": "assistant", "message": "I'll delegate this to a specialist" }

// Sidechain starts - Claude becomes user
{
  "type": "user",
  "message": "Please analyze this Python code for improvements",
  "isSidechain": true,
  "userType": "external"
}
{
  "type": "assistant",
  "message": "I've identified three optimization opportunities...",
  "isSidechain": true
}

// Back to main conversation
{ "type": "assistant", "message": "Based on the analysis..." }
```

### Deleted Messages

Messages marked for soft deletion but retained in logs:

```json
{
  "type": "user",
  "uuid": "msg-del-001",
  "timestamp": "2025-01-27T10:00:00Z",
  "sessionId": "session-123",
  "isDeleted": true,
  "message": "[Message deleted by user]"
}
```

**Characteristics:**
- `isDeleted: true` flag
- Original content may be replaced with placeholder
- Still maintains position in message chain

### Aborted Operations

Messages from cancelled or interrupted operations:

```json
{
  "type": "assistant",
  "uuid": "msg-abort-001",
  "timestamp": "2025-01-27T10:00:00Z",
  "sessionId": "session-123",
  "isAborted": true,
  "message": "Operation cancelled by user",
  "subtype": "tool_use",
  "toolName": "Bash",
  "toolArguments": {
    "command": "long_running_script.py"
  }
}
```

### Meta Messages

Infrastructure metadata not part of conversation flow:

```json
{
  "type": "system",
  "uuid": "msg-meta-001",
  "timestamp": "2025-01-27T10:00:00Z",
  "sessionId": "session-123",
  "isMeta": true,
  "message": "Session metadata: context_length=8192, model=claude-3"
}
```

**Common Meta Message Types:**
- Session configuration
- Context window status
- Model information
- System reminders
- Performance metrics

## Message Flow Patterns

### Linear Conversation

Basic user-assistant interaction:

```
user → assistant → user → assistant
```

### Tool Usage Pattern

Standard tool invocation and result:

```
user → assistant (response) → assistant (tool_use) → system (result) → assistant (response)
```

### Parallel Tool Pattern

Multiple tools invoked simultaneously:

```
user
  └── assistant (planning)
      ├── assistant (tool_use: Read file1)
      ├── assistant (tool_use: Read file2)
      └── assistant (tool_use: Read file3)
          ├── system (result: file1 contents)
          ├── system (result: file2 contents)
          └── system (result: file3 contents)
              └── assistant (synthesis)
```

### Sidechain Pattern

Delegation to sub-agents:

```
user → assistant → user[sidechain] → assistant[sidechain] → assistant
```

### Error Recovery Pattern

Handling tool failures:

```
user
  └── assistant (attempt 1)
      └── assistant (tool_use)
          └── system (error)
              └── assistant (alternative approach)
                  └── assistant (tool_use: different tool)
                      └── system (success)
```

### Compact Operation Pattern

Context window management:

```
user (/compact command)
  └── compact_system (conversation_compacting)
      └── compact_system (conversation_compacted)
          └── assistant (acknowledgment)
              └── user (continue work)
                  └── assistant (working with compacted context)
```

## Message State Transitions

### Tool Operation States

```
Planning → Invocation → Execution → Result → Integration
```

1. **Planning**: Assistant message explaining approach
2. **Invocation**: tool_use subtype with arguments
3. **Execution**: System processing (may be async)
4. **Result**: System message with outcome
5. **Integration**: Assistant incorporates result

### Conversation States

```
Active → Compacting → Compacted → Restoring → Restored
```

### Message Chain Branching

When users edit messages, new branches form:

```
Original Chain:
user(1) → assistant(2) → user(3) → assistant(4)

After editing message 3:
user(1) → assistant(2) → user(3) → assistant(4)
                      ↘
                       user(3') → assistant(4')
```

## Message Categorization

### By Purpose

| Category | Types | Subtypes | Purpose |
|----------|-------|----------|---------|
| Input | user | - | Human or Claude input |
| Processing | assistant | tool_use, thinking | Work execution |
| Output | assistant | response | Results to user |
| Infrastructure | system | tool_result, error, meta | System state |
| Management | compact_system | - | Context control |

### By Visibility

| Visibility | Message Types | Display |
|------------|---------------|---------|
| User-facing | user, assistant (response) | Always shown |
| Operational | assistant (tool_use), system (tool_result) | May be collapsed |
| Hidden | assistant (thinking), system (meta) | Not shown to user |
| Administrative | compact_system | Status only |

## Common Message Patterns

### Request-Process-Respond

```json
[
  { "type": "user", "message": "Create a Python function" },
  { "type": "assistant", "message": "I'll create that function for you" },
  { "type": "assistant", "subtype": "tool_use", "toolName": "Write" },
  { "type": "system", "message": "File created successfully" },
  { "type": "assistant", "message": "I've created the function in main.py" }
]
```

### Multi-Step Operation

```json
[
  { "type": "user", "message": "Refactor this module" },
  { "type": "assistant", "subtype": "tool_use", "toolName": "Read" },
  { "type": "system", "message": "[file contents]" },
  { "type": "assistant", "subtype": "thinking", "message": "Analyzing structure" },
  { "type": "assistant", "subtype": "tool_use", "toolName": "MultiEdit" },
  { "type": "system", "message": "Edits applied successfully" },
  { "type": "assistant", "subtype": "tool_use", "toolName": "Bash",
    "toolArguments": { "command": "python -m pytest" }},
  { "type": "system", "message": "All tests passed" }
]
```

## Validation and Processing Guidelines

### Message Integrity

1. **UUID Uniqueness**: Every message must have a globally unique identifier
2. **Timestamp Ordering**: Messages should be chronologically ordered
3. **Parent Validity**: parentUuid must reference existing message
4. **Type Consistency**: Message structure must match declared type

### Required Field Validation

| Message Type | Required Fields | Conditional Fields |
|--------------|-----------------|-------------------|
| user | type, uuid, timestamp, sessionId | message (unless command) |
| assistant | type, uuid, timestamp, sessionId | toolName/Args (if tool_use) |
| system | type, uuid, timestamp, sessionId | message |
| compact_system | type, uuid, timestamp, sessionId, message | metadata (for compacted) |

### Processing Recommendations

1. **Parse type first** to determine structure
2. **Check for special flags** (isSidechain, isMeta, isDeleted)
3. **Validate required fields** before processing
4. **Handle subtypes** for specialized behavior
5. **Preserve unknown fields** for forward compatibility
6. **Track parent chains** for conversation threading
7. **Group related messages** (tool invocation + result)

### Error Handling

When encountering malformed messages:

1. Log the error with message UUID
2. Attempt to extract usable fields
3. Mark as corrupted but retain in chain
4. Continue processing subsequent messages
5. Report summary of issues at end

## Summary

Claude Code sessions use a structured message type system with four primary types (user, assistant, system, compact_system) and various subtypes for categorization. Special flags like `isSidechain`, `isMeta`, and `isDeleted` modify message semantics. Understanding these types, their relationships, and common patterns is essential for correctly parsing and interpreting Claude Code session logs.
