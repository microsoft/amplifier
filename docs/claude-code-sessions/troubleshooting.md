# Error Handling Reference

## Error Conditions and Handling

### OSError Errno 5 - Cloud Sync Delays

**Condition**: File I/O operations on cloud-synced directories (OneDrive, Dropbox, Google Drive) in WSL2 environments.

**Behavior**: Operations fail with `OSError: [Errno 5] Input/output error` when accessing files not locally cached.

**Required Handling**: Exponential backoff retry with 0.5s initial delay, doubling on each retry, maximum 3 attempts.

**Implementation**:
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

### Undefined Agent Names in Sidechains

**Condition**: Sidechain messages without corresponding Task tool invocations.

**Data Source**: Agent names are stored in Task tool's `subagent_type` parameter, not in message fields.

**Required Processing**: Extract `subagent_type` from Task tool invocations and correlate with subsequent sidechains.

**Implementation**:
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

### Orphaned Message Handling

**Condition**: Messages with `parentUuid` referencing non-existent messages.

**Occurrence Rate**: 15-20% of messages after compact operations.

**Required Behavior**: Orphaned messages must be treated as DAG roots for traversal.

**Implementation**:
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

### Sidechain Message Identification

**Condition**: Messages with `isSidechain: true` flag.

**Structure**: Sidechains group sequentially by `parentUuid` reference.

**Required Processing**: Filter by `isSidechain` flag and maintain grouping by parent UUID.

**Implementation**:
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

### Compact Operation Continuity

**Condition**: Messages following compact operations with `logicalParentUuid` field.

**Structure**: `logicalParentUuid` maintains conversation flow across compact boundaries.

**Required Processing**: Prioritize `logicalParentUuid` over `parentUuid` when present.

**Implementation**:
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

### Large File Processing

**Condition**: Session files exceeding 100MB.

**Memory Constraint**: Full file loading causes out-of-memory errors.

**Required Approach**: Line-by-line streaming with immediate processing.

**Implementation**:
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

### Branch Active Path Determination

**Condition**: Multiple children for a single parent message.

**Determination Rule**: Last child by file position represents the active branch.

**Required Processing**: Sort children by file position and select the last entry.

**Implementation**:
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

### Circular Reference Detection

**Condition**: Malformed parent references creating cycles in DAG.

**Detection Method**: Visited node tracking during traversal.

**Required Behavior**: Terminate traversal upon cycle detection and log warning.

**Implementation**:
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

### Project Log Directory Resolution

**Condition**: Project paths require transformation to log directory names.

**Transformation Rules**: Replace `/` with `_`, replace `.` with `_`, remove leading underscore.

**Base Path**: `~/.claude/conversations/`

**Implementation**:
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

### Tool Invocation-Result Correlation

**Condition**: Tool results require matching to their invocations.

**Correlation Method**: Match tool result's `parentUuid` to invocation's `uuid`.

**Required Structure**: Map tool invocations by UUID for O(1) result matching.

**Implementation**:
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

## Performance Requirements

### Index Construction
```python
# Build multiple indices for O(1) lookups
messages_by_uuid = {msg["uuid"]: msg for msg in messages}
messages_by_parent = defaultdict(list)
for msg in messages:
    parent = msg.get("parentUuid")
    if parent:
        messages_by_parent[parent].append(msg)
```

### Memory-Efficient Processing
```python
def process_large_session(filepath: Path):
    """Process large files without loading all into memory."""
    for msg in stream_parse_jsonl(filepath):
        # Process each message immediately
        yield transform_message(msg)
```

### Path Caching
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_conversation_path(root_uuid: str) -> List[str]:
    """Cache conversation paths to avoid recomputation."""
    return traverse_conversation(root_uuid, messages_by_uuid)
```

### Batch I/O Operations
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

## Required Implementation Behaviors

- Orphaned messages (non-existent `parentUuid`) become DAG roots
- Agent names extracted from Task tool `subagent_type` parameter
- Compact continuity maintained via `logicalParentUuid` field
- Cloud sync I/O errors handled with exponential backoff retry
- Sidechain messages identified by `isSidechain: true` flag
- Active branches determined by last child in file position order
- Circular references detected using visited node tracking
- Large files processed via line-by-line streaming
- Tool results correlated via `parentUuid` to invocation UUID mapping
- Project paths transformed to log directories using underscore replacement

## Test Requirements

### Multi-Compact Sessions
   ```python
   # Test with sessions having 8+ compacts
   test_file = "conversation_2025_01_27_with_8_compacts.jsonl"
   assert count_compacts(test_file) >= 8
   ```

### Orphaned Message Handling
   ```python
   # Create test data with orphan
   messages = [
       {"uuid": "msg1", "parentUuid": "non_existent"},
       {"uuid": "msg2", "parentUuid": "msg1"}
   ]
   roots = find_conversation_roots(messages)
   assert "msg1" in roots  # Orphan should be root
   ```

### Sidechain Grouping
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

### Cloud Sync Error Simulation
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

### Large File Streaming
   ```python
   # Test with 100MB+ file
   large_file = create_test_file(size_mb=100)
   message_count = 0
   for msg in stream_parse_jsonl(large_file):
       message_count += 1
   assert message_count > 0
   ```

## Error Code Reference

| Error | Resolution |
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

## Failure Recovery Behaviors

- **Malformed JSON lines**: Skip line, log error with line number, continue processing
- **Partial results**: Save successfully processed data before failure point
- **Progress persistence**: Write results after each complete conversation path
- **Checkpoint recovery**: Resume from last successfully written position
- **Error reporting**: Include line numbers, error types, and affected message UUIDs