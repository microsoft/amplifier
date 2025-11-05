# Claude Code DAG Specification

This document specifies the Directed Acyclic Graph (DAG) structure that forms the foundation of Claude Code session files.

## Foundation: DAG as Core Data Structure

Claude Code sessions are fundamentally a DAG where:
- **Nodes** = Messages (user inputs, assistant responses, tool invocations/results)
- **Edges** = Parent-child relationships via `parentUuid → uuid` mapping
- **Roots** = Messages where `parentUuid = null`
- **Temporal Ordering** = Parents always appear before children in the file

## Core Mechanics

### UUID and Parent UUID Relationships

Every message contains:
- `uuid`: Unique identifier for this message
- `parentUuid`: Reference to parent message (or `null` for roots)

```
Message Structure:
{
  "uuid": "msg_abc123",
  "parentUuid": "msg_xyz789",  // or null
  ...
}

Relationship:
child.parentUuid → parent.uuid
```

**Key Properties**:
- UUIDs are globally unique within a session
- Parent references create the DAG structure
- Multiple children can share the same parent (branches)
- Parents always appear before children in file order

### Tool Correlation via ID Matching

Tool invocations and their results are correlated through ID matching:

```
Assistant Message (Tool Invocation):
{
  "type": "assistant",
  "message": {
    "content": [{
      "type": "tool_use",
      "id": "toolu_01abc",  ← Unique invocation ID
      "name": "Read",
      "input": {...}
    }]
  }
}

Tool Result Message:
{
  "type": "tool_result",
  "message": {
    "content": [{
      "type": "tool_result",
      "tool_use_id": "toolu_01abc",  ← Matches invocation ID
      "content": "..."
    }]
  }
}
```

**Correlation Rule**: `tool_use.id === tool_result.tool_use_id`

### Task → Sidechain Linkage Patterns

The Task tool creates sidechain conversations with subagents:

```
Pattern Flow:
1. Assistant invokes Task tool
2. Sidechain starts with first message having:
   - parentUuid = UUID of Task invocation message
   - isSidechain = true
   - userType = "external" (actual initiator)

Assistant Message (Task Invocation):
{
  "uuid": "msg_task_123",
  "type": "assistant",
  "message": {
    "content": [{
      "type": "tool_use",
      "name": "Task",
      "id": "toolu_task_456",
      "input": {
        "subagent_type": "bug-hunter",
        "prompt": "Find bugs in this code"
      }
    }]
  }
}
    ↓
Human Message (Sidechain Start):
{
  "parentUuid": "msg_task_123",  ← Points to Task message
  "type": "human",
  "isSidechain": true,
  "userType": "external",  // Claude acting as user
  "message": {
    "content": "Find bugs in this code"
  }
}
```

**Agent Identification**:
1. Get sidechain's first message
2. Find parent message via `parentUuid`
3. Search parent's tool invocations for Task tool
4. Extract `subagent_type` from Task input

### Branch Mechanics

Branches occur when users regenerate responses:

```
Branch Structure:
Parent Message (uuid: "msg_parent")
├── Child A (line 100) → Abandoned branch
├── Child B (line 150) → Abandoned branch
└── Child C (line 200) → Active branch (last by line number)
```

**Active Branch Rules**:
- Parent with multiple children = branch point
- Active child = child with highest line number in file
- Abandoned branches = all other children
- `is_active` field marks active paths when present

### Compact Operations

Compacts reduce context size by summarizing older messages:

```
Compact Messages:
{
  "type": "compact_prelude",
  "parentUuid": null,  ← New root
  "message": {
    "content": "Preserved message content..."
  }
}

{
  "type": "compact_recap",
  "parentUuid": "msg_compact_prelude",
  "message": {
    "content": "Summary of compacted conversation..."
  }
}
```

## DAG Patterns

### Orphan Handling

Orphans occur when `parentUuid` references a non-existent message:

```python
def is_orphan(message, all_messages):
    if message.parentUuid is None:
        return False  # Root, not orphan
    parent_exists = any(m.uuid == message.parentUuid for m in all_messages)
    return not parent_exists
```

**Treatment**: Orphans become alternative roots in the DAG

### Tool Result Delays

Results may be delayed when sidechains execute between invocation and result:

```
Message Flow:
1. Assistant: Tool invocation (id: "toolu_123")
2. Assistant: Task invocation → spawns sidechain
3. Human: Sidechain start
4. Assistant: Sidechain response
5. Tool Result: (tool_use_id: "toolu_123")  ← Delayed result
```

### Nested Sidechains

Agents can invoke other agents creating nested sidechains:

```
Main Conversation
└── Sidechain 1 (agent: zen-architect)
    └── Sidechain 2 (agent: bug-hunter)  ← Nested
```

**Depth Calculation**:
```python
def get_sidechain_depth(message):
    depth = 0
    current = message
    while current and current.get("isSidechain"):
        depth += 1
        current = get_parent(current)
    return depth
```

### Role Reversal in Sidechains

Sidechains reverse the user/assistant roles:

| Message Type | Main Conversation | Sidechain |
|-------------|-------------------|-----------|
| human | Human user | Claude delegating |
| assistant | Claude response | Agent response |

**Key Indicator**: `userType = "external"` identifies the actual initiator

## Implementation Requirements

A compliant implementation must:

1. **Parse DAG Structure**
   - Build parent-child relationships
   - Handle orphaned nodes
   - Detect and track branches

2. **Correlate Tools**
   - Match invocations to results by ID
   - Handle delayed results across sidechains
   - Support batch tool invocations

3. **Process Sidechains**
   - Identify sidechain boundaries
   - Determine agent names from Task invocations
   - Track nesting depth
   - Handle role reversals

4. **Handle Compacts**
   - Detect compact messages
   - Preserve conversation continuity

5. **Determine Active Paths**
   - Identify branch points
   - Calculate active branches by line number or `is_active` field

## Edge Cases

1. **Broken Parent References**: Parent UUID doesn't exist in file
2. **Missing Agent Names**: Task tool may be absent or too far back
3. **Deeply Nested Sidechains**: No built-in depth limit
4. **Multiple Compact Operations**: Sessions may have several compacts
5. **Interleaved Tool Results**: Results may not follow invocation order

## Reference Implementation Patterns

### Building the DAG

```python
def build_dag(messages):
    dag = {}
    roots = []
    orphans = []

    # Build parent-child mappings
    for msg in messages:
        if msg.parentUuid is None:
            roots.append(msg)
        elif msg.parentUuid not in {m.uuid for m in messages}:
            orphans.append(msg)
        else:
            if msg.parentUuid not in dag:
                dag[msg.parentUuid] = []
            dag[msg.parentUuid].append(msg)

    return dag, roots, orphans
```

### Finding Tool Results

```python
def find_tool_result(invocation_id, messages):
    for msg in messages:
        if msg.type != "tool_result":
            continue
        for content in msg.message.get("content", []):
            if content.get("type") == "tool_result":
                if content.get("tool_use_id") == invocation_id:
                    return msg, content
    return None, None
```

### Determining Active Branch

```python
def get_active_child(parent_uuid, children):
    if not children:
        return None
    # Check is_active field first
    for child in children:
        if child.get("is_active"):
            return child
    # Fall back to last by file position
    return max(children, key=lambda c: c.line_number)
```

### Extracting Agent Name

```python
def get_sidechain_agent(first_sidechain_msg, messages):
    if not first_sidechain_msg.parentUuid:
        return "unknown"

    # Find parent message
    parent = next((m for m in messages if m.uuid == first_sidechain_msg.parentUuid), None)
    if not parent:
        return "unknown"

    # Look for Task tool in parent
    for content in parent.message.get("content", []):
        if content.get("type") == "tool_use" and content.get("name") == "Task":
            return content.get("input", {}).get("subagent_type", "unknown")

    return "unknown"
```