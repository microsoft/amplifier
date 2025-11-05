# Claude Code Sessions Troubleshooting

This guide helps resolve common issues when parsing and working with Claude Code session files.

## Common Issues

### Tool Results Not Matching Invocations

**Problem**: Tool results appear missing or don't correlate with invocations.

**Solution**: Use correct field for correlation:
```python
# Correct - use tool_use_id to match id
if result["tool_use_id"] == invocation["id"]:
    # Match found

# Wrong - these fields don't exist or don't match
if result["id"] == invocation["id"]:  # result has no "id"
if result["invocation_id"] == invocation["id"]:  # field doesn't exist
```

### Missing Parent References

**Problem**: Messages reference parent UUIDs that don't exist in the file.

**Solution**: Treat orphaned messages as alternative roots:
```python
if parent_uuid not in all_messages:
    # This is an orphan - treat as root
    roots.append(message)
```

### Branch Navigation Issues

**Problem**: Can't determine which branch is active.

**Solution**: Active branch is determined by file position:
```python
# Active child = last child by line number
children.sort(key=lambda m: m.line_number)
active_child = children[-1]
```

### Sidechain Agent Not Found

**Problem**: Can't identify which agent is handling a sidechain.

**Solution**: Look for Task tool in parent message:
```python
# Find parent of first sidechain message
parent = messages[first_sidechain_msg.parent_uuid]
# Look for Task tool invocation
for tool in parent.tool_invocations:
    if tool["name"] == "Task":
        agent = tool["input"]["subagent_type"]
```

### Content Format Variations

**Problem**: Message content can be string, dict, or list.

**Solution**: Check type before processing:
```python
content = message.get("content")
if isinstance(content, str):
    # Direct string content
    text = content
elif isinstance(content, dict):
    # Structured content
    text = extract_from_dict(content)
elif isinstance(content, list):
    # Array of content items
    text = extract_from_list(content)
```

## Performance Issues

### Large File Processing

**Problem**: Loading large session files (>100MB) causes memory issues.

**Solution**: Use streaming processing:
```python
# Stream process line by line
with open(session_file, 'r') as f:
    for line_num, line in enumerate(f, 1):
        if line.strip():
            msg = json.loads(line)
            process_message(msg)
```

### Slow DAG Traversal

**Problem**: Navigating the DAG is slow for large sessions.

**Solution**: Build indices for O(1) lookups:
```python
# Build UUID index
uuid_index = {msg["uuid"]: msg for msg in messages}

# Build children index
children_index = {}
for msg in messages:
    parent = msg.get("parentUuid")
    if parent:
        if parent not in children_index:
            children_index[parent] = []
        children_index[parent].append(msg["uuid"])
```

### Memory Usage

**Problem**: Storing entire DAG in memory is expensive.

**Solution**: Process incrementally and free unused data:
```python
# Process in chunks
def process_in_chunks(file_path, chunk_size=1000):
    chunk = []
    with open(file_path, 'r') as f:
        for line in f:
            chunk.append(json.loads(line))
            if len(chunk) >= chunk_size:
                process_chunk(chunk)
                chunk = []
    if chunk:
        process_chunk(chunk)
```

## Edge Cases

### Empty or Malformed Lines

**Problem**: Some lines in JSONL file are empty or invalid.

**Solution**: Skip invalid lines gracefully:
```python
for line in file:
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        print(f"Skipping invalid line: {line[:50]}...")
        continue
```

### Messages Without Version Field

**Problem**: Some messages lack the version field.

**Solution**: Handle missing fields with defaults:
```python
version = message.get("version", "unknown")
```

### Circular Parent References

**Problem**: Messages might have circular parent references (shouldn't happen but defensive coding).

**Solution**: Track visited nodes:
```python
def trace_parents(msg_uuid, visited=None):
    if visited is None:
        visited = set()

    if msg_uuid in visited:
        # Circular reference detected
        return []

    visited.add(msg_uuid)
    # Continue tracing...
```

## Data Integrity

### Timestamp Validation

**Problem**: Timestamps might be in different formats.

**Solution**: Handle both millisecond and second timestamps:
```python
timestamp = msg.get("timestamp")
if timestamp > 10**12:
    # Milliseconds
    dt = datetime.fromtimestamp(timestamp / 1000)
else:
    # Seconds
    dt = datetime.fromtimestamp(timestamp)
```

### UUID Uniqueness

**Problem**: UUIDs should be unique but might have duplicates.

**Solution**: Handle duplicates by keeping last occurrence:
```python
messages_by_uuid = {}
for msg in messages:
    uuid = msg["uuid"]
    if uuid in messages_by_uuid:
        print(f"Warning: Duplicate UUID {uuid}")
    messages_by_uuid[uuid] = msg  # Keep last
```

## Debugging Tips

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

def parse_message(msg):
    logging.debug(f"Processing message: {msg['uuid']}")
    # Processing logic...
```

### Validate DAG Structure

```python
def validate_dag(messages):
    """Check DAG integrity."""
    issues = []

    # Check all parent references exist
    all_uuids = {m["uuid"] for m in messages}
    for msg in messages:
        if parent := msg.get("parentUuid"):
            if parent not in all_uuids:
                issues.append(f"Orphan: {msg['uuid']} references missing {parent}")

    # Check for circular references
    # Check for duplicate UUIDs
    # etc.

    return issues
```

### Export Debug Information

```python
def export_debug_info(dag, output_file):
    """Export DAG structure for debugging."""
    debug_info = {
        "total_messages": len(dag.messages),
        "roots": dag.roots,
        "orphans": [m for m in dag.messages if m.is_orphan],
        "branches": find_all_branches(dag),
        "sidechains": find_all_sidechains(dag)
    }

    with open(output_file, 'w') as f:
        json.dump(debug_info, f, indent=2)
```

## Getting Help

If you encounter issues not covered here:

1. Check the example implementations in `/examples`
2. Review the DAG specification in `/core/DAG-SPECIFICATION.md`
3. Validate your session file format against `/core/MESSAGE-FORMAT.md`
4. Test with a minimal session file to isolate the issue