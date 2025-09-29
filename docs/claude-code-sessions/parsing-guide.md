# Claude Code Session Parser API Reference

## Message Class

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class Message:
    """Message representation for Claude Code sessions."""
    # Core fields (required)
    type: str  # 'user', 'assistant', 'system', 'compact_system'
    uuid: str
    timestamp: str
    session_id: str

    # Content fields
    message: Optional[str] = None
    subtype: Optional[str] = None

    # Relationship fields
    parent_uuid: Optional[str] = None
    user_type: Optional[str] = None  # 'human', 'external'

    # Tool fields
    tool_name: Optional[str] = None
    tool_arguments: Optional[Dict[str, Any]] = None
    tool_id: Optional[str] = None

    # Sidechain fields
    is_sidechain: bool = False
    agent_name: Optional[str] = None

    # Error tracking
    is_error: bool = False
    error_message: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Parser tracking
    logical_parent_uuid: Optional[str] = None
    children_uuids: List[str] = field(default_factory=list)
    branch_id: Optional[str] = None
    depth: int = 0

    @classmethod
    def from_json(cls, data: dict) -> 'Message':
        """Create Message from JSON."""
        msg = cls(
            type=data.get('type', 'unknown'),
            uuid=data.get('uuid', ''),
            timestamp=data.get('timestamp', ''),
            session_id=data.get('sessionId', ''),
            message=data.get('message'),
            subtype=data.get('subtype'),
            parent_uuid=data.get('parentUuid'),
            user_type=data.get('userType'),
            tool_name=data.get('toolName'),
            tool_arguments=data.get('toolArguments'),
            tool_id=data.get('toolId'),
            is_sidechain=data.get('isSidechain', False),
            is_error=data.get('isError', False),
            error_message=data.get('errorMessage'),
            metadata=data.get('metadata', {})
        )

        # Extract agent name from Task tool
        if msg.tool_name == 'Task' and msg.tool_arguments:
            msg.agent_name = msg.tool_arguments.get('agentName',
                                msg.tool_arguments.get('agent', 'unknown'))

        return msg

    def get_timestamp_datetime(self) -> Optional[datetime]:
        """Parse timestamp to datetime object."""
        try:
            ts = self.timestamp.replace('Z', '+00:00')
            return datetime.fromisoformat(ts)
        except (ValueError, AttributeError):
            return None
```

## Parser Class

```python
class ClaudeCodeParser:
    """Parser for Claude Code session JSONL files."""

    def __init__(self, jsonl_path: Path, logger: Optional[logging.Logger] = None):
        self.path = Path(jsonl_path)
        self.logger = logger or logging.getLogger(__name__)

        # Core data structures
        self.messages: List[Message] = []
        self.messages_by_uuid: Dict[str, Message] = {}
        self.children_by_parent: Dict[str, List[str]] = {}
        self.orphaned_messages: List[Message] = []

        # Tracking structures
        self.roots: List[Message] = []
        self.sidechains: Dict[str, List[Message]] = {}
        self.compact_operations: List[Dict] = []
        self.parse_errors: List[Dict] = []

        # Statistics
        self.parse_stats = {
            'total_lines': 0,
            'parsed_messages': 0,
            'orphaned_messages': 0,
            'parse_errors': 0,
            'retry_attempts': 0,
            'parse_time': 0.0
        }

    def parse(self) -> 'ClaudeCodeParser':
        """Execute complete parsing pipeline."""
        self.parse_messages()
        self.build_dag()
        self.branches = self.extract_branches()
        self.sidechains = self.extract_sidechains()
        self.handle_compact_operations()
        self._calculate_statistics()
        return self
```

## Core Methods

### parse_messages

```python
def parse_messages(self, max_retries: int = 3, retry_delay: float = 0.5) -> None:
    """
    Parse messages from JSONL file.

    Parameters:
        max_retries: Number of retry attempts for I/O errors
        retry_delay: Initial delay between retries (seconds)

    Handles:
        - Cloud sync I/O errors (OneDrive, Dropbox)
        - Malformed JSON lines
        - Missing required fields
        - Large files via streaming
    """
```

### build_dag

```python
def build_dag(self) -> None:
    """
    Build directed acyclic graph from messages.

    Implementation details:
        - Orphaned messages (missing parent) become roots
        - Detects and breaks cycles
        - Tracks logical parent relationships through compacts
    """
```

### extract_branches

```python
def extract_branches(self) -> Dict[str, List[Message]]:
    """
    Extract all conversation branches.

    Returns:
        Dictionary mapping branch_id to messages in that branch.
        Each branch represents a complete path from root to leaf.
    """
```

### extract_sidechains

```python
def extract_sidechains(self) -> Dict[str, List[Message]]:
    """
    Extract sidechains with agent identification.

    Returns:
        Dictionary mapping sidechain_id to message list.
        IDs include agent name when available.
    """
```

## Utility Functions

### Cycle Detection

```python
def detect_cycles(parser: ClaudeCodeParser) -> List[List[str]]:
    """Detect all cycles in the message graph."""
    cycles = []
    visited = set()
    rec_stack = []

    def dfs(uuid: str) -> bool:
        visited.add(uuid)
        rec_stack.append(uuid)

        for child_uuid in parser.children_by_parent.get(uuid, []):
            if child_uuid not in visited:
                if dfs(child_uuid):
                    return True
            elif child_uuid in rec_stack:
                # Found cycle
                cycle_start = rec_stack.index(child_uuid)
                cycle = rec_stack[cycle_start:] + [child_uuid]
                cycles.append(cycle)
                return True

        rec_stack.pop()
        return False

    for msg in parser.messages:
        if msg.uuid not in visited:
            rec_stack = []
            dfs(msg.uuid)

    return cycles
```

### Cloud Sync Retry

```python
def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 0.5,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    logger: logging.Logger = None
) -> Any:
    """
    Retry function with exponential backoff for cloud sync issues.

    Parameters:
        func: Function to execute
        max_retries: Maximum retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        backoff_factor: Multiplier for each retry delay
        logger: Optional logger for warnings

    Returns:
        Function result

    Raises:
        Exception: After max_retries attempts
    """
```

## Transcript Generator

```python
class TranscriptGenerator:
    """Generate output formats from parsed sessions."""

    def __init__(self, parser: ClaudeCodeParser):
        self.parser = parser
        self.output_dir = Path('output')

    def generate_simple_transcript(self, branch_id: str = None) -> str:
        """Generate human-readable transcript."""

    def generate_extended_transcript(self) -> Dict:
        """Generate detailed transcript with metadata."""

    def save_outputs(self) -> Path:
        """Save all outputs to directory."""
```

## Orphan Handling Strategies

```python
def handle_orphaned_messages(parser: ClaudeCodeParser) -> None:
    """
    Handle orphaned messages.

    Strategies:
        - make_root: Treat as roots (default)
        - find_temporal_parent: Find parent by timestamp proximity
        - group_orphans: Group under synthetic parent
    """
```

## Malformed JSON Recovery

```python
def parse_malformed_line(line: str, line_num: int, logger: logging.Logger) -> Optional[Dict]:
    """
    Attempt to recover from malformed JSON.

    Recovery strategies:
        1. Fix common quote issues
        2. Fix truncated JSON by adding closing braces
        3. Extract JSON from mixed content
        4. Fix unicode issues
        5. Use regex to extract valid JSON
    """
```

## Performance Optimization

```python
class OptimizedClaudeCodeParser(ClaudeCodeParser):
    """Optimized parser for 100MB+ files."""

    def parse_messages_streaming(self) -> None:
        """
        Stream parse with minimal memory footprint.

        Optimizations:
            - Process in chunks to reduce memory
            - Use generators where possible
            - Build indexes incrementally
        """

    def get_message_lazy(self, uuid: str) -> Optional[Message]:
        """Lazy load message from disk if not in memory."""
```

## Usage Examples

### Basic Usage

```python
from pathlib import Path
from claude_code_parser import ClaudeCodeParser

# Parse session
parser = ClaudeCodeParser(Path("session.jsonl"))
parser.parse()

# Access results
print(f"Messages: {len(parser.messages)}")
print(f"Branches: {len(parser.branches)}")
print(f"Sidechains: {len(parser.sidechains)}")
```

### Generate Transcript

```python
from claude_code_parser import ClaudeCodeParser, TranscriptGenerator

parser = ClaudeCodeParser(Path("session.jsonl"))
parser.parse()

generator = TranscriptGenerator(parser)
generator.save_outputs()
```

### Extract Specific Branch

```python
parser = ClaudeCodeParser(Path("session.jsonl"))
parser.parse()

branches = parser.branches
for branch_id, messages in branches.items():
    print(f"Branch {branch_id}: {len(messages)} messages")
```

## Error Handling

### Required Field Validation

```python
def _validate_message(self, data: dict, line_num: int) -> bool:
    """Validate message has required fields."""
    required = ['type', 'uuid', 'timestamp', 'sessionId']
    missing = [f for f in required if f not in data]

    if missing:
        self.parse_errors.append({
            'line': line_num,
            'error': f"Missing required fields: {missing}",
            'data': data
        })
        return False

    valid_types = ['user', 'assistant', 'system', 'compact_system']
    if data['type'] not in valid_types:
        return False

    return True
```

### Error Recovery

When encountering malformed messages:

1. Log error with message UUID
2. Attempt to extract usable fields
3. Mark as corrupted but retain in chain
4. Continue processing subsequent messages
5. Report summary of issues at end

## DAG Rules

### Parent Resolution

1. Messages with valid `parentUuid` linking to existing message maintain that relationship
2. Messages with `parentUuid` referencing non-existent message become roots
3. Logical parent tracked separately for reconstruction through compacts
4. Cycles detected and broken by removing back edge

### Branch Construction

1. Each branch represents a complete path from root to leaf
2. Messages can belong to multiple branches if they have multiple children
3. Branch IDs assigned sequentially as `branch_0000`, `branch_0001`, etc.

## Sidechain Rules

### Agent Identification

1. Task tool invocation contains `subagent_type` or `agent` field
2. First sidechain message after Task contains exact prompt text
3. All consecutive `isSidechain: true` messages belong to same sidechain
4. Agent name propagated to all messages in sidechain

### Sidechain Boundaries

1. Sidechain starts when `isSidechain: true` first appears
2. Sidechain ends when `isSidechain` absent or false
3. Incomplete sidechains marked with `incomplete: True`

## Compact Operation Tracking

```python
def handle_compact_operations(self) -> None:
    """
    Track compact operations and logical parent relationships.

    Handles:
        - Multiple compacts in long sessions
        - Preserving logical flow across compacts
        - Metadata extraction from compact messages
    """
```

## Statistics Calculation

```python
self.stats = {
    'total_messages': len(self.messages),
    'user_messages': count by type,
    'assistant_messages': count by type,
    'system_messages': count by type,
    'tool_invocations': count by subtype,
    'sidechain_messages': count by flag,
    'orphaned_messages': len(self.orphaned_messages),
    'branches': len(self.branches),
    'sidechains': len(self.sidechains),
    'compact_operations': len(self.compact_operations),
    'unique_tools': unique tool names,
    'parse_errors': len(self.parse_errors),
    'duration_seconds': max(timestamps) - min(timestamps)
}
```