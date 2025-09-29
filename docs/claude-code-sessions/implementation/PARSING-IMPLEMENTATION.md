# Claude Code Session Parsing Implementation

This guide provides implementation patterns for parsing Claude Code session files.

## Core Data Structures

### Message Class

```python
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class Message:
    """Represents a single message in the session."""

    # Core fields (always present)
    uuid: str
    parent_uuid: Optional[str]
    session_id: str
    timestamp: int  # Unix timestamp in milliseconds
    type: str  # human, assistant, tool_result, etc.
    version: str

    # Message content
    content: Any  # Can be string or structured dict
    raw_data: dict  # Original JSON for reference

    # Position tracking
    line_number: int  # Position in file (for branch determination)

    # Relationships
    children_uuids: list[str] = field(default_factory=list)

    # Special flags
    is_sidechain: bool = False
    is_active: bool = True
    user_type: Optional[str] = None

    # Tool tracking
    tool_invocations: list = field(default_factory=list)
    tool_results: list = field(default_factory=list)
```

### DAG Structure

```python
class SessionDAG:
    """Manages the DAG structure of a session."""

    def __init__(self):
        self.messages: dict[str, Message] = {}
        self.roots: list[str] = []
        self.children_by_parent: dict[str, list[str]] = {}
        self.tool_results_by_id: dict[str, Any] = {}
```

## Parsing Implementation

### Basic Parser

```python
import json
from pathlib import Path

def parse_session_file(file_path: Path) -> SessionDAG:
    """Parse a Claude Code session JSONL file."""
    dag = SessionDAG()

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue

            # Parse JSON
            data = json.loads(line)

            # Create message
            msg = Message(
                uuid=data['uuid'],
                parent_uuid=data.get('parentUuid'),
                session_id=data['sessionId'],
                timestamp=data['timestamp'],
                type=data['type'],
                version=data.get('version', 'unknown'),
                content=data.get('message', {}),
                raw_data=data,
                line_number=line_num,
                is_sidechain=data.get('isSidechain', False),
                is_active=data.get('is_active', True),
                user_type=data.get('userType')
            )

            # Add to DAG
            dag.messages[msg.uuid] = msg

            # Track roots
            if msg.parent_uuid is None:
                dag.roots.append(msg.uuid)
            else:
                # Track parent-child relationships
                if msg.parent_uuid not in dag.children_by_parent:
                    dag.children_by_parent[msg.parent_uuid] = []
                dag.children_by_parent[msg.parent_uuid].append(msg.uuid)

                # Update parent's children list if parent exists
                if msg.parent_uuid in dag.messages:
                    dag.messages[msg.parent_uuid].children_uuids.append(msg.uuid)

    # Process tool correlations
    correlate_tools(dag)

    # Mark orphans
    mark_orphans(dag)

    return dag
```

### Tool Correlation

```python
def correlate_tools(dag: SessionDAG):
    """Correlate tool invocations with their results."""

    # Extract all tool invocations
    invocations = {}
    for msg in dag.messages.values():
        if msg.type == 'assistant':
            content = msg.content.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if item.get('type') == 'tool_use':
                        tool_id = item.get('id')
                        invocations[tool_id] = {
                            'message_uuid': msg.uuid,
                            'tool_name': item.get('name'),
                            'input': item.get('input', {})
                        }
                        msg.tool_invocations.append(item)

    # Match with results
    for msg in dag.messages.values():
        if msg.type == 'tool_result':
            content = msg.content.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if item.get('type') == 'tool_result':
                        tool_use_id = item.get('tool_use_id')
                        if tool_use_id in invocations:
                            # Link result to invocation
                            dag.tool_results_by_id[tool_use_id] = {
                                'result': item.get('content'),
                                'is_error': item.get('is_error', False),
                                'message_uuid': msg.uuid
                            }
                            msg.tool_results.append(item)
```

### Branch Detection

```python
def determine_active_branches(dag: SessionDAG):
    """Determine which branches are active."""

    for parent_uuid, children_uuids in dag.children_by_parent.items():
        if len(children_uuids) > 1:
            # Multiple children = branch point
            # Sort by line number to find the active child
            children = [dag.messages[uuid] for uuid in children_uuids]
            children.sort(key=lambda m: m.line_number)

            # Mark all but the last as inactive
            for child in children[:-1]:
                mark_branch_inactive(dag, child.uuid)

def mark_branch_inactive(dag: SessionDAG, start_uuid: str):
    """Recursively mark a branch as inactive."""
    if start_uuid not in dag.messages:
        return

    msg = dag.messages[start_uuid]
    msg.is_active = False

    # Recursively mark children
    for child_uuid in msg.children_uuids:
        mark_branch_inactive(dag, child_uuid)
```

### Sidechain Processing

```python
def process_sidechains(dag: SessionDAG):
    """Identify and process sidechain conversations."""

    for msg in dag.messages.values():
        if msg.is_sidechain and not msg.sidechain_agent:
            # Find the agent from parent's Task invocation
            agent = find_sidechain_agent(dag, msg)
            msg.sidechain_agent = agent

            # Calculate depth
            msg.sidechain_depth = calculate_sidechain_depth(dag, msg)

def find_sidechain_agent(dag: SessionDAG, sidechain_msg: Message) -> str:
    """Extract agent name from Task invocation."""

    if not sidechain_msg.parent_uuid:
        return "unknown"

    parent = dag.messages.get(sidechain_msg.parent_uuid)
    if not parent:
        return "unknown"

    # Look for Task tool in parent's invocations
    for invocation in parent.tool_invocations:
        if invocation.get('name') == 'Task':
            input_data = invocation.get('input', {})
            return input_data.get('subagent_type', 'unknown')

    return "unknown"

def calculate_sidechain_depth(dag: SessionDAG, msg: Message) -> int:
    """Calculate nesting depth of sidechains."""
    depth = 0
    current = msg

    while current and current.is_sidechain:
        depth += 1
        if current.parent_uuid:
            current = dag.messages.get(current.parent_uuid)
        else:
            break

    return depth
```

### Orphan Handling

```python
def mark_orphans(dag: SessionDAG):
    """Identify messages with non-existent parents."""

    for msg in dag.messages.values():
        if msg.parent_uuid and msg.parent_uuid not in dag.messages:
            # Parent doesn't exist - this is an orphan
            msg.is_orphan = True
            # Treat as alternative root
            dag.roots.append(msg.uuid)
```

## Path Traversal

### Active Path

```python
def get_active_path(dag: SessionDAG, start_uuid: str = None) -> list[Message]:
    """Get the active conversation path."""
    path = []

    # Start from root or specified message
    if start_uuid:
        current = dag.messages.get(start_uuid)
    else:
        # Find first root
        if dag.roots:
            current = dag.messages.get(dag.roots[0])
        else:
            return path

    while current:
        path.append(current)

        # Find active child
        active_child = None
        for child_uuid in current.children_uuids:
            child = dag.messages[child_uuid]
            if child.is_active:
                active_child = child
                break

        current = active_child

    return path
```

### Sidechain Extraction

```python
def get_sidechain_messages(dag: SessionDAG, task_msg: Message) -> list[Message]:
    """Extract all messages in a sidechain."""
    sidechain = []

    # Find sidechain start (first child with is_sidechain=true)
    sidechain_start = None
    for child_uuid in task_msg.children_uuids:
        child = dag.messages[child_uuid]
        if child.is_sidechain:
            sidechain_start = child
            break

    if not sidechain_start:
        return sidechain

    # Collect all sidechain messages
    to_process = [sidechain_start]
    processed = set()

    while to_process:
        current = to_process.pop(0)
        if current.uuid in processed:
            continue

        processed.add(current.uuid)
        sidechain.append(current)

        # Add children that are part of sidechain
        for child_uuid in current.children_uuids:
            child = dag.messages.get(child_uuid)
            if child and child.is_sidechain:
                to_process.append(child)

    return sidechain
```

## Performance Optimizations

### Streaming Parser

```python
def parse_session_streaming(file_path: Path):
    """Stream parse for large files."""

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue

            data = json.loads(line)
            yield line_num, data
```

### Index Building

```python
def build_indices(dag: SessionDAG):
    """Build indices for fast lookups."""

    # UUID to line number index
    dag.uuid_to_line = {
        msg.uuid: msg.line_number
        for msg in dag.messages.values()
    }

    # Session to message index
    dag.messages_by_session = {}
    for msg in dag.messages.values():
        if msg.session_id not in dag.messages_by_session:
            dag.messages_by_session[msg.session_id] = []
        dag.messages_by_session[msg.session_id].append(msg.uuid)
```

## Error Handling

### Robust Parsing

```python
def parse_message_safe(line: str, line_num: int) -> Optional[Message]:
    """Parse a message with error handling."""
    try:
        data = json.loads(line)

        # Validate required fields
        required = ['uuid', 'sessionId', 'type', 'timestamp']
        for field in required:
            if field not in data:
                print(f"Line {line_num}: Missing required field '{field}'")
                return None

        return create_message(data, line_num)

    except json.JSONDecodeError as e:
        print(f"Line {line_num}: Invalid JSON - {e}")
        return None
    except Exception as e:
        print(f"Line {line_num}: Unexpected error - {e}")
        return None
```

## Usage Example

```python
# Parse session
session_file = Path("~/.claude/conversations/project/session.jsonl")
dag = parse_session_file(session_file)

# Process relationships
determine_active_branches(dag)
process_sidechains(dag)

# Get active conversation
active_path = get_active_path(dag)

# Find tool results
for tool_id, result in dag.tool_results_by_id.items():
    print(f"Tool {tool_id}: {result['result'][:100]}...")

# Extract sidechain
for msg in dag.messages.values():
    if msg.tool_invocations:
        for inv in msg.tool_invocations:
            if inv.get('name') == 'Task':
                sidechain = get_sidechain_messages(dag, msg)
                print(f"Sidechain with {len(sidechain)} messages")
```