# Claude Code Sessions Troubleshooting Guide

This guide addresses common issues encountered when processing Claude Code session logs and provides working solutions.

## Common Issues and Solutions

### 1. Cloud Sync I/O Errors

**Symptom**: `OSError: [Errno 5] Input/output error` when reading files, especially in WSL2 with OneDrive/Dropbox.

**Cause**: Cloud sync services (OneDrive, Dropbox, Google Drive) delay file access while fetching from cloud.

**Solution**: Implement retry logic with exponential backoff and informative warnings.

**Code Example**:
```python
import time
import logging
from pathlib import Path
from typing import Any, Dict

def read_json_with_retry(filepath: Path, max_retries: int = 3) -> Dict[str, Any]:
    """Read JSON file with cloud sync retry logic."""
    retry_delay = 0.5

    for attempt in range(max_retries):
        try:
            return json.loads(filepath.read_text())
        except OSError as e:
            if e.errno == 5 and attempt < max_retries - 1:
                if attempt == 0:
                    logging.warning(
                        f"Cloud sync I/O error on {filepath}. "
                        "Consider enabling 'Always keep on device' for: "
                        f"{filepath.parent}"
                    )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise
```

### 2. Missing Agent Names (All "unknown")

**Symptom**: All sidechain conversations show agent name as "unknown".

**Cause**: Not extracting agent type from Task tool's `subagent_type` parameter.

**Solution**: Track Task tool invocations and correlate with sidechains.

**Code Example**:
```python
def extract_agent_name(message: Dict[str, Any]) -> str:
    """Extract agent name from Task tool invocation."""
    if message.get("type") == "tool_invocation":
        tool = message.get("tool", {})
        if tool.get("name") == "Task":
            # Look for subagent_type in parameters
            params = tool.get("parameters", {})
            return params.get("subagent_type", "unknown")

    # For sidechains, check the parent's tool invocations
    if message.get("isSidechain"):
        parent_uuid = message.get("parentUuid")
        parent_msg = messages_by_uuid.get(parent_uuid, {})
        return extract_agent_name(parent_msg)

    return "unknown"
```

### 3. Empty Conversation Paths

**Symptom**: Extracted conversation paths contain no messages.

**Cause**: Not treating orphaned messages (parentUuid points to non-existent message) as conversation roots.

**Solution**: Check for orphaned messages and treat them as roots.

**Code Example**:
```python
def find_conversation_roots(messages: List[Dict]) -> List[str]:
    """Find all conversation root messages including orphans."""
    message_uuids = {msg["uuid"] for msg in messages}
    roots = []

    for msg in messages:
        parent_uuid = msg.get("parentUuid")

        # Root if no parent or parent doesn't exist (orphan)
        if not parent_uuid or parent_uuid not in message_uuids:
            roots.append(msg["uuid"])
            if parent_uuid and parent_uuid not in message_uuids:
                logging.debug(f"Found orphan: {msg['uuid']} -> {parent_uuid}")

    return roots
```

### 4. Incomplete Sidechain Extraction

**Symptom**: Sub-agent conversations not being extracted.

**Cause**: Not properly checking the `isSidechain` flag.

**Solution**: Filter messages by `isSidechain: true` and group by parent.

**Code Example**:
```python
def extract_sidechains(messages: List[Dict]) -> Dict[str, List[Dict]]:
    """Extract all sidechain conversations grouped by parent."""
    sidechains = {}

    for msg in messages:
        if msg.get("isSidechain", False):
            parent_uuid = msg.get("parentUuid", "unknown")
            if parent_uuid not in sidechains:
                sidechains[parent_uuid] = []
            sidechains[parent_uuid].append(msg)

    # Sort each sidechain by position for correct ordering
    for parent_uuid in sidechains:
        sidechains[parent_uuid].sort(key=lambda m: m.get("filePosition", 0))

    return sidechains
```

### 5. Lost Compact Continuity

**Symptom**: Conversation appears broken at compact boundaries.

**Cause**: Not following `logicalParentUuid` to connect across compacts.

**Solution**: Track both physical and logical parent relationships.

**Code Example**:
```python
def get_message_parent(msg: Dict, messages_by_uuid: Dict) -> Optional[str]:
    """Get the effective parent, considering logical parents for compacts."""
    # First try logical parent (for compact continuity)
    logical_parent = msg.get("logicalParentUuid")
    if logical_parent and logical_parent in messages_by_uuid:
        return logical_parent

    # Fall back to physical parent
    physical_parent = msg.get("parentUuid")
    if physical_parent and physical_parent in messages_by_uuid:
        return physical_parent

    return None
```

### 6. Memory Issues with Large Files

**Symptom**: Out of memory errors on files > 100MB.

**Cause**: Loading entire file into memory at once.

**Solution**: Stream process line by line.

**Code Example**:
```python
def stream_parse_jsonl(filepath: Path):
    """Stream parse JSONL file line by line."""
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                msg = json.loads(line)
                # Add file position for ordering
                msg['filePosition'] = line_num
                yield msg
            except json.JSONDecodeError as e:
                logging.warning(f"Skipping malformed line {line_num}: {e}")
                continue
```

### 7. Incorrect Branch Detection

**Symptom**: Wrong identification of active vs abandoned branches.

**Cause**: Not using file position to determine the active branch.

**Solution**: The last child by file position is the active branch.

**Code Example**:
```python
def identify_active_branch(parent_uuid: str, messages: List[Dict]) -> Optional[str]:
    """Identify the active branch (last by file position)."""
    children = [
        msg for msg in messages
        if msg.get("parentUuid") == parent_uuid
    ]

    if not children:
        return None

    # Sort by file position and take the last one
    children.sort(key=lambda m: m.get("filePosition", 0))
    return children[-1]["uuid"]
```

### 8. Circular Reference Crashes

**Symptom**: Infinite loop when traversing message DAG.

**Cause**: Malformed parent references creating cycles.

**Solution**: Track visited nodes to detect cycles.

**Code Example**:
```python
def traverse_conversation(root_uuid: str, messages_by_uuid: Dict) -> List[Dict]:
    """Safely traverse conversation with cycle detection."""
    visited = set()
    path = []

    def traverse(uuid: str):
        if uuid in visited:
            logging.warning(f"Cycle detected at {uuid}")
            return

        visited.add(uuid)
        msg = messages_by_uuid.get(uuid)
        if msg:
            path.append(msg)
            # Find active child and continue
            active_child = identify_active_branch(uuid, messages_by_uuid.values())
            if active_child:
                traverse(active_child)

    traverse(root_uuid)
    return path
```

### 9. Missing Project Directory

**Symptom**: Can't find current project's conversation logs.

**Cause**: Directory name transformation rules not applied correctly.

**Solution**: Convert project path to Claude's directory naming convention.

**Code Example**:
```python
def get_project_log_dir(project_path: Path) -> Path:
    """Convert project path to Claude's log directory name."""
    # Replace / with _ and . with _
    dir_name = str(project_path).replace('/', '_').replace('.', '_')

    # Remove leading underscore if present
    if dir_name.startswith('_'):
        dir_name = dir_name[1:]

    base_dir = Path.home() / ".claude" / "conversations"
    return base_dir / dir_name
```

### 10. Tool Result Correlation Failures

**Symptom**: Can't match tool results to their invocations.

**Cause**: Not tracking tool invocation UUIDs.

**Solution**: Map tool UUIDs to their results.

**Code Example**:
```python
def correlate_tool_results(messages: List[Dict]) -> Dict[str, Dict]:
    """Correlate tool invocations with their results."""
    tool_map = {}

    for msg in messages:
        if msg.get("type") == "tool_invocation":
            tool_uuid = msg.get("uuid")
            tool_map[tool_uuid] = {
                "invocation": msg,
                "result": None
            }
        elif msg.get("type") == "tool_result":
            # Match by parentUuid or correlation ID
            parent = msg.get("parentUuid")
            if parent in tool_map:
                tool_map[parent]["result"] = msg

    return tool_map
```

## Performance Optimization Tips

### Index for Fast Lookups
```python
# Build multiple indices for O(1) lookups
messages_by_uuid = {msg["uuid"]: msg for msg in messages}
messages_by_parent = defaultdict(list)
for msg in messages:
    parent = msg.get("parentUuid")
    if parent:
        messages_by_parent[parent].append(msg)
```

### Use Generators for Large Datasets
```python
def process_large_session(filepath: Path):
    """Process large files without loading all into memory."""
    for msg in stream_parse_jsonl(filepath):
        # Process each message immediately
        yield transform_message(msg)
```

### Cache Frequently Accessed Paths
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_conversation_path(root_uuid: str) -> List[str]:
    """Cache conversation paths to avoid recomputation."""
    return traverse_conversation(root_uuid, messages_by_uuid)
```

### Batch File Operations
```python
def save_results_batch(results: List[Dict], output_dir: Path):
    """Batch write operations for better performance."""
    # Collect all data first
    all_data = []
    for result in results:
        all_data.append(json.dumps(result))

    # Single write operation
    output_file = output_dir / "results.jsonl"
    output_file.write_text("\n".join(all_data))
```

## Validation Checklist

Before considering your transcript builder complete, verify:

- [ ] **Handles orphaned messages**: Messages with non-existent parents become roots
- [ ] **Extracts agent names**: Correctly identifies agents from Task tool parameters
- [ ] **Processes compacts correctly**: Follows logicalParentUuid for continuity
- [ ] **Handles cloud sync errors**: Implements retry logic for I/O errors
- [ ] **Identifies sidechains**: Extracts all isSidechain=true conversations
- [ ] **Determines active branches**: Uses file position to identify active path
- [ ] **Avoids circular references**: Detects and breaks cycles in message graph
- [ ] **Manages memory efficiently**: Streams large files instead of loading all
- [ ] **Correlates tools correctly**: Matches invocations with results
- [ ] **Finds project logs**: Correctly transforms project paths to log directories

## Testing Patterns

### Essential Test Scenarios

1. **Multi-Compact Sessions**
   ```python
   # Test with sessions having 8+ compacts
   test_file = "conversation_2025_01_27_with_8_compacts.jsonl"
   assert count_compacts(test_file) >= 8
   ```

2. **Orphaned Messages**
   ```python
   # Create test data with orphan
   messages = [
       {"uuid": "msg1", "parentUuid": "non_existent"},
       {"uuid": "msg2", "parentUuid": "msg1"}
   ]
   roots = find_conversation_roots(messages)
   assert "msg1" in roots  # Orphan should be root
   ```

3. **Sidechain Extraction**
   ```python
   # Test sidechain grouping
   messages = [
       {"uuid": "main1", "isSidechain": False},
       {"uuid": "side1", "parentUuid": "main1", "isSidechain": True},
       {"uuid": "side2", "parentUuid": "main1", "isSidechain": True}
   ]
   sidechains = extract_sidechains(messages)
   assert len(sidechains["main1"]) == 2
   ```

4. **Cloud Sync Simulation**
   ```python
   # Simulate cloud sync delay
   import errno

   def simulate_cloud_sync_read():
       if random.random() < 0.3:  # 30% chance of sync delay
           e = OSError()
           e.errno = errno.EIO  # errno 5
           raise e
       return actual_read()
   ```

5. **Large File Handling**
   ```python
   # Test with 100MB+ file
   large_file = create_test_file(size_mb=100)
   message_count = 0
   for msg in stream_parse_jsonl(large_file):
       message_count += 1
   assert message_count > 0
   ```

## Quick Fixes Reference

| Issue | Quick Fix |
|-------|-----------|
| OSError errno 5 | Add retry with 0.5s exponential backoff |
| Unknown agents | Check Task tool's subagent_type param |
| Empty paths | Include orphaned messages as roots |
| Missing sidechains | Filter by isSidechain=true |
| Broken at compact | Use logicalParentUuid |
| OOM on large files | Use streaming parser |
| Wrong branch | Sort children by filePosition |
| Infinite loop | Add visited set for cycle detection |
| Can't find logs | Transform project path correctly |
| No tool results | Map by tool UUID |

## Debug Logging

Enable detailed logging to diagnose issues:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transcript_builder.log'),
        logging.StreamHandler()
    ]
)

# Add debug points
logger.debug(f"Processing message: {msg['uuid']}")
logger.debug(f"Found {len(roots)} conversation roots")
logger.debug(f"Extracted {len(sidechains)} sidechains")
```

## Recovery Strategies

When encountering corrupt or incomplete data:

1. **Skip malformed messages**: Log and continue
2. **Use partial results**: Better than nothing
3. **Save progress frequently**: Write after each conversation
4. **Provide recovery mode**: Allow resuming from checkpoint
5. **Report issues clearly**: Show what succeeded and what failed

Remember: The goal is to extract as much useful information as possible, even from imperfect data.