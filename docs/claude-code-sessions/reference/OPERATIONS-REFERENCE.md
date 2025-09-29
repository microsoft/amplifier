# Claude Code Operations Reference

This document describes the operations that occur within Claude Code sessions and how they affect the DAG structure.

## Core Operations

### Compact Operation

Reduces conversation size by summarizing older messages when approaching context limits.

**Trigger**:
- Automatic when cumulative tokens approach ~155k-162k
- No user control over timing

**Process**:
1. Older messages are summarized into compact messages
2. Recent messages (~10-20k tokens) are preserved
3. New root is created at compact boundary

**Message Types**:
- `compact_prelude`: Preserved important messages
- `compact_recap`: Summary of compacted conversation

**Effects on DAG**:
- Creates new epoch (breaks parent chain)
- Compact messages have `parentUuid: null`
- Subsequent messages use compact as new root

### Fork Operation

Creates conversation branches when regenerating or editing responses.

**Triggers**:
- User edits a previous message
- User clicks "retry" on a response
- User regenerates an assistant response

**Branch Structure**:
```
Parent Message
├── Original Response (inactive branch - preserved in DAG)
└── New Response (active branch - highest line number)
```

**Branch Behavior**:
- All branches permanently preserved in DAG
- Active branch determined by file position (last child)
- Inactive branches remain fully accessible via UI history
- No programmatic way to reactivate inactive branches
- Each branch operation is irreversible

### Rewind/Branch Operation

Creates a new branch from an earlier message in the conversation. Note: The UI may call this "rewind" but it's actually a branching operation.

**Trigger**:
- User invokes rewind/regenerate to return to a previous message
- User edits a previous message
- User regenerates an assistant response

**Effects**:
- Creates new branch (new child) at the target message
- Original conversation path remains intact as inactive branch
- New session ID often created for the branch
- All messages preserved in DAG structure
- File duplication preserves complete shared history

**DAG Structure After Branch Operation**:
```
Target Message (branch point)
├── Original Path (now inactive, line numbers lower)
│   └── ... (complete conversation preserved)
└── New Branch (active, highest line numbers)
    └── ... (new conversation continues)
```

**File Duplication Pattern**:
- New JSONL file created for branch
- Shared history duplicated in new file
- Branch-specific messages appended
- Same UUIDs appear across multiple files

### Clear Operation

Resets the conversation to a clean state.

**Effects**:
- Creates new root message
- Previous conversation remains in file but disconnected
- New messages start fresh DAG

### Sidechain Operation

Creates sub-conversations when delegating to agents via Task tool.

**Trigger**:
- Assistant invokes Task tool with subagent

**Structure**:
```
Main Conversation
└── Task Invocation
    └── Sidechain Start (isSidechain: true)
        └── Agent Conversation
```

**Characteristics**:
- Role reversal (human type = Claude delegating)
- `userType: "external"` marks actual initiator
- Can nest (agents invoking other agents)
- Returns to main conversation via tool result

## Tool Operations

### Tool Invocation

Assistant calls a tool to perform an action.

**Message Structure**:
```json
{
  "type": "assistant",
  "message": {
    "content": [{
      "type": "tool_use",
      "id": "toolu_unique_id",
      "name": "ToolName",
      "input": {...}
    }]
  }
}
```

### Tool Result

System returns the result of a tool execution.

**Message Structure**:
```json
{
  "type": "tool_result",
  "message": {
    "content": [{
      "type": "tool_result",
      "tool_use_id": "toolu_unique_id",
      "content": "Result data",
      "is_error": false
    }]
  }
}
```

**Correlation**: `tool_use.id` must match `tool_result.tool_use_id`

### Batch Tool Operations

Multiple tools invoked in single assistant message.

**Pattern**:
```json
{
  "content": [
    {"type": "tool_use", "id": "toolu_001", ...},
    {"type": "tool_use", "id": "toolu_002", ...},
    {"type": "tool_use", "id": "toolu_003", ...}
  ]
}
```

**Results**: Each tool gets separate result with matching `tool_use_id`

## Message Flow Patterns

### Standard Request-Response

```
1. Human: Request
2. Assistant: Response
3. Human: Follow-up
4. Assistant: Response
```

### Tool-Assisted Response

```
1. Human: Request
2. Assistant: Text + Tool invocation
3. Tool Result: Data
4. Assistant: Final response using data
```

### Delegated Task Flow

```
1. Assistant: Task invocation
2. Sidechain Human: Delegated prompt
3. Sidechain Assistant: Agent response
4. Tool Result: Agent's output
5. Assistant: Integration of results
```

### Nested Delegation

```
Main → Agent A → Agent B → Agent C
         ↓         ↓         ↓
      Results   Results   Results
```

## Operation Constraints

### Compact Constraints

- Cannot control when compaction occurs
- Cannot recover compacted messages
- Preserved message count varies
- Summary quality depends on conversation content

### Branch/Fork Constraints

- Cannot merge branches back together
- Active branch strictly determined by line number
- No mechanism to reactivate inactive branches
- No branch naming or management features
- Every regeneration creates permanent fork
- Experimental workflows affected by irreversible branching

### Sidechain Constraints

- Agent name must be extracted from Task tool
- Nested depth has no built-in limit
- Role reversal must be handled correctly
- Agent messages interleave with main conversation

## Performance Considerations

### Large Sessions

- Compact operations become more likely
- DAG traversal becomes slower
- Branch navigation complexity increases
- Memory usage grows linearly

### Optimization Strategies

1. **Index Building**: Create UUID lookups on load
2. **Path Caching**: Cache active path calculations
3. **Streaming**: Process messages incrementally
4. **Pruning**: Filter inactive branches when not needed for specific views
5. **DAG Deduplication**: When a complete DAG flow is fully contained within another, discard the smaller subset duplicate

## Error Recovery

### Orphaned Messages

**Cause**: Parent UUID references non-existent message
**Recovery**: Treat as alternative root

### Missing Tool Results

**Cause**: Tool execution failed or result not recorded
**Recovery**: Continue processing, note missing result

### Broken Sidechains

**Cause**: Task tool or sidechain messages missing
**Recovery**: Mark agent as "unknown", continue processing

### Corrupt Compaction

**Cause**: Incomplete compact operation
**Recovery**: Treat last valid message as conversation end