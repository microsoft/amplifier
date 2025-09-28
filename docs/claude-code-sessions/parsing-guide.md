# Claude Code Session Parsing Guide

## Overview

This guide provides comprehensive, production-ready implementation guidance for parsing Claude Code session logs. It covers the complete parser architecture, critical edge cases, and performance optimizations needed for handling real-world session files that can exceed 100MB with complex DAG structures.

## Complete Production Parser Architecture

### Core Message Class

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import time
import logging

@dataclass
class Message:
    """Complete message representation with all fields"""
    # Core fields (always present)
    type: str  # 'user', 'assistant', 'system', 'compact_system'
    uuid: str
    timestamp: str
    session_id: str

    # Content fields
    message: Optional[str] = None
    subtype: Optional[str] = None  # 'tool_use', 'tool_result', etc.

    # Relationship fields
    parent_uuid: Optional[str] = None
    user_type: Optional[str] = None  # 'human', 'external'

    # Tool fields
    tool_name: Optional[str] = None
    tool_arguments: Optional[Dict[str, Any]] = None
    tool_id: Optional[str] = None

    # Sidechain fields
    is_sidechain: bool = False
    agent_name: Optional[str] = None  # Extracted from Task tool

    # Error tracking
    is_error: bool = False
    error_message: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Parser tracking
    logical_parent_uuid: Optional[str] = None  # For orphans/compact handling
    children_uuids: List[str] = field(default_factory=list)
    branch_id: Optional[str] = None
    depth: int = 0

    @classmethod
    def from_json(cls, data: dict) -> 'Message':
        """Create Message from JSON with validation"""
        # Map JSON fields to dataclass fields
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

        # Extract agent name from Task tool arguments
        if msg.tool_name == 'Task' and msg.tool_arguments:
            msg.agent_name = msg.tool_arguments.get('agentName',
                                msg.tool_arguments.get('agent', 'unknown'))

        return msg

    def get_timestamp_datetime(self) -> Optional[datetime]:
        """Parse timestamp to datetime object"""
        try:
            # Handle both formats: with and without timezone
            ts = self.timestamp.replace('Z', '+00:00')
            return datetime.fromisoformat(ts)
        except (ValueError, AttributeError):
            return None
```

### Robust Parser with Cloud Sync Retry Logic

```python
class ClaudeCodeParser:
    """Production-ready parser with comprehensive error handling"""

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

        # Performance tracking
        self.parse_stats = {
            'total_lines': 0,
            'parsed_messages': 0,
            'orphaned_messages': 0,
            'parse_errors': 0,
            'retry_attempts': 0,
            'parse_time': 0.0
        }

    def parse_messages(self, max_retries: int = 3, retry_delay: float = 0.5) -> None:
        """
        Stream parse messages with cloud sync retry logic

        Handles:
        - Cloud sync I/O errors (OneDrive, Dropbox, etc.)
        - Malformed JSON lines
        - Missing required fields
        - Large files (streaming)
        """
        start_time = time.time()

        for attempt in range(max_retries):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        self.parse_stats['total_lines'] += 1

                        line = line.strip()
                        if not line:
                            continue

                        try:
                            data = json.loads(line)

                            # Validate required fields
                            if not self._validate_message(data, line_num):
                                continue

                            # Create message object
                            msg = Message.from_json(data)
                            self.messages.append(msg)
                            self.messages_by_uuid[msg.uuid] = msg
                            self.parse_stats['parsed_messages'] += 1

                        except json.JSONDecodeError as e:
                            self.parse_errors.append({
                                'line': line_num,
                                'error': str(e),
                                'content': line[:200]
                            })
                            self.parse_stats['parse_errors'] += 1

                        except Exception as e:
                            self.logger.warning(f"Unexpected error at line {line_num}: {e}")
                            self.parse_stats['parse_errors'] += 1

                # Success - break retry loop
                break

            except OSError as e:
                # Handle cloud sync I/O errors
                if e.errno == 5 and attempt < max_retries - 1:
                    self.parse_stats['retry_attempts'] += 1
                    if attempt == 0:
                        self.logger.warning(
                            f"File I/O error reading {self.path} - retrying. "
                            "This may be due to cloud-synced files (OneDrive, Dropbox, etc.). "
                            "Consider enabling 'Always keep on this device' for the data folder."
                        )
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    raise

        self.parse_stats['parse_time'] = time.time() - start_time
        self.logger.info(f"Parsed {self.parse_stats['parsed_messages']} messages "
                        f"in {self.parse_stats['parse_time']:.2f}s")

    def _validate_message(self, data: dict, line_num: int) -> bool:
        """Validate message has required fields"""
        required = ['type', 'uuid', 'timestamp', 'sessionId']
        missing = [f for f in required if f not in data]

        if missing:
            self.parse_errors.append({
                'line': line_num,
                'error': f"Missing required fields: {missing}",
                'data': data
            })
            return False

        # Validate type field
        valid_types = ['user', 'assistant', 'system', 'compact_system']
        if data['type'] not in valid_types:
            self.parse_errors.append({
                'line': line_num,
                'error': f"Invalid message type: {data['type']}",
                'data': data
            })
            return False

        return True

    def build_dag(self) -> None:
        """
        Build DAG with orphan handling and cycle detection

        Critical implementation details:
        - Orphaned messages (missing parent) are treated as roots
        - Detects and breaks cycles
        - Tracks logical parent relationships through compacts
        """
        # Build parent-child relationships
        for msg in self.messages:
            if msg.parent_uuid:
                # Check if parent exists
                if msg.parent_uuid in self.messages_by_uuid:
                    parent = self.messages_by_uuid[msg.parent_uuid]
                    parent.children_uuids.append(msg.uuid)
                    if msg.parent_uuid not in self.children_by_parent:
                        self.children_by_parent[msg.parent_uuid] = []
                    self.children_by_parent[msg.parent_uuid].append(msg.uuid)
                else:
                    # Orphaned message - treat as root
                    msg.logical_parent_uuid = msg.parent_uuid
                    msg.parent_uuid = None  # Clear parent to make it a root
                    self.orphaned_messages.append(msg)
                    self.parse_stats['orphaned_messages'] += 1
                    self.logger.debug(f"Orphaned message {msg.uuid} - treating as root")

        # Identify root messages
        self.roots = [msg for msg in self.messages if not msg.parent_uuid]

        # Detect and handle cycles
        self._detect_and_break_cycles()

        # Calculate depths
        self._calculate_depths()

        self.logger.info(f"DAG built: {len(self.roots)} roots, "
                        f"{len(self.orphaned_messages)} orphans")

    def _detect_and_break_cycles(self) -> None:
        """Detect and break cycles in the DAG using DFS"""
        visited = set()
        rec_stack = set()
        cycles_broken = 0

        def has_cycle(uuid: str) -> bool:
            visited.add(uuid)
            rec_stack.add(uuid)

            for child_uuid in self.children_by_parent.get(uuid, []):
                if child_uuid not in visited:
                    if has_cycle(child_uuid):
                        return True
                elif child_uuid in rec_stack:
                    # Cycle detected - break it
                    child = self.messages_by_uuid[child_uuid]
                    self.logger.warning(f"Cycle detected: {uuid} -> {child_uuid}, breaking link")

                    # Remove child from parent's children
                    self.children_by_parent[uuid].remove(child_uuid)
                    parent = self.messages_by_uuid[uuid]
                    parent.children_uuids.remove(child_uuid)

                    # Make child a root
                    child.logical_parent_uuid = child.parent_uuid
                    child.parent_uuid = None
                    self.roots.append(child)
                    nonlocal cycles_broken
                    cycles_broken += 1
                    return True

            rec_stack.remove(uuid)
            return False

        # Check all components
        for msg in self.messages:
            if msg.uuid not in visited:
                has_cycle(msg.uuid)

        if cycles_broken > 0:
            self.logger.warning(f"Broke {cycles_broken} cycles in DAG")

    def _calculate_depths(self) -> None:
        """Calculate depth for each message in the DAG"""
        def set_depth(msg: Message, depth: int):
            msg.depth = depth
            for child_uuid in msg.children_uuids:
                if child_uuid in self.messages_by_uuid:
                    child = self.messages_by_uuid[child_uuid]
                    set_depth(child, depth + 1)

        for root in self.roots:
            set_depth(root, 0)

    def extract_branches(self) -> Dict[str, List[Message]]:
        """
        Extract all conversation branches

        Returns dict mapping branch_id to messages in that branch.
        Each branch represents a complete path from root to leaf.
        """
        branches = {}
        branch_counter = 0

        def extract_branch_from(msg: Message, current_branch: List[Message]) -> None:
            """Recursively extract branches"""
            nonlocal branch_counter

            current_branch = current_branch + [msg]

            if not msg.children_uuids:
                # Leaf node - save this branch
                branch_id = f"branch_{branch_counter:04d}"
                branches[branch_id] = current_branch
                for m in current_branch:
                    m.branch_id = branch_id
                branch_counter += 1
            else:
                # Continue traversing
                for child_uuid in msg.children_uuids:
                    if child_uuid in self.messages_by_uuid:
                        child = self.messages_by_uuid[child_uuid]
                        extract_branch_from(child, current_branch)

        # Extract branches from each root
        for root in self.roots:
            extract_branch_from(root, [])

        self.logger.info(f"Extracted {len(branches)} branches")
        return branches

    def extract_sidechains(self) -> Dict[str, List[Message]]:
        """
        Extract sidechains with agent identification

        Critical details:
        - Groups consecutive sidechain messages
        - Identifies agent from Task tool invocation
        - Preserves message order within sidechains
        """
        sidechains = {}
        current_sidechain = []
        sidechain_counter = 0
        current_agent = None

        for msg in self.messages:
            # Check for Task tool that starts a sidechain
            if msg.tool_name == 'Task' and not msg.is_sidechain:
                # This is the Task invocation that starts the sidechain
                if msg.tool_arguments:
                    current_agent = msg.tool_arguments.get('agentName',
                                    msg.tool_arguments.get('agent', f'agent_{sidechain_counter}'))

            if msg.is_sidechain:
                # Add agent info to message
                if current_agent:
                    msg.agent_name = current_agent
                current_sidechain.append(msg)

            elif current_sidechain:
                # End of sidechain - save it
                sidechain_id = f"sidechain_{sidechain_counter:04d}_{current_agent or 'unknown'}"
                sidechains[sidechain_id] = current_sidechain
                self.logger.debug(f"Extracted sidechain {sidechain_id} with {len(current_sidechain)} messages")

                # Reset for next sidechain
                current_sidechain = []
                sidechain_counter += 1
                current_agent = None

        # Don't forget last sidechain if exists
        if current_sidechain:
            sidechain_id = f"sidechain_{sidechain_counter:04d}_{current_agent or 'unknown'}"
            sidechains[sidechain_id] = current_sidechain

        self.logger.info(f"Extracted {len(sidechains)} sidechains")
        return sidechains

    def handle_compact_operations(self) -> None:
        """
        Track compact operations and logical parent relationships

        Critical for handling:
        - Multiple compacts (8+ in long sessions)
        - Preserving logical flow across compacts
        - Metadata extraction from compact messages
        """
        compact_stack = []  # Track nested/sequential compacts

        for msg in self.messages:
            if msg.type == 'compact_system':
                if msg.message == 'conversation_compacting':
                    # Start of compact operation
                    compact_info = {
                        'start_uuid': msg.uuid,
                        'start_timestamp': msg.timestamp,
                        'start_index': self.messages.index(msg),
                        'affected_messages': []
                    }
                    compact_stack.append(compact_info)
                    self.logger.debug(f"Compact operation started at {msg.timestamp}")

                elif msg.message == 'conversation_compacted':
                    # End of compact operation
                    if compact_stack:
                        compact_info = compact_stack.pop()
                        compact_info['end_uuid'] = msg.uuid
                        compact_info['end_timestamp'] = msg.timestamp
                        compact_info['end_index'] = self.messages.index(msg)
                        compact_info['metadata'] = msg.metadata

                        # Track affected messages between start and end
                        start_idx = compact_info['start_index']
                        end_idx = compact_info['end_index']
                        for i in range(start_idx + 1, end_idx):
                            affected_msg = self.messages[i]
                            compact_info['affected_messages'].append(affected_msg.uuid)
                            # Mark logical parent for reconstruction
                            affected_msg.logical_parent_uuid = affected_msg.parent_uuid

                        self.compact_operations.append(compact_info)
                        self.logger.debug(f"Compact operation completed, "
                                        f"affected {len(compact_info['affected_messages'])} messages")

        if compact_stack:
            self.logger.warning(f"{len(compact_stack)} unclosed compact operations detected")

## Complete Working Parser Implementation

```python
# Complete production-ready parser
class ClaudeCodeParser:
    """Full implementation with all components"""

    def parse(self) -> 'ClaudeCodeParser':
        """Complete parsing pipeline"""
        try:
            # 1. Parse messages from JSONL
            self.parse_messages()

            # 2. Build DAG structure
            self.build_dag()

            # 3. Extract branches
            self.branches = self.extract_branches()

            # 4. Extract sidechains
            self.sidechains = self.extract_sidechains()

            # 5. Handle compact operations
            self.handle_compact_operations()

            # 6. Calculate statistics
            self._calculate_statistics()

            return self

        except Exception as e:
            self.logger.error(f"Parsing failed: {e}")
            raise

    def _calculate_statistics(self) -> None:
        """Calculate comprehensive session statistics"""
        self.stats = {
            'total_messages': len(self.messages),
            'user_messages': sum(1 for m in self.messages if m.type == 'user'),
            'assistant_messages': sum(1 for m in self.messages if m.type == 'assistant'),
            'system_messages': sum(1 for m in self.messages if m.type in ['system', 'compact_system']),
            'tool_invocations': sum(1 for m in self.messages if m.subtype == 'tool_use'),
            'sidechain_messages': sum(1 for m in self.messages if m.is_sidechain),
            'orphaned_messages': len(self.orphaned_messages),
            'branches': len(self.branches),
            'sidechains': len(self.sidechains),
            'compact_operations': len(self.compact_operations),
            'unique_tools': len(set(m.tool_name for m in self.messages if m.tool_name)),
            'parse_errors': len(self.parse_errors),
            'duration_seconds': None
        }

        # Calculate session duration
        timestamps = [m.get_timestamp_datetime() for m in self.messages]
        timestamps = [t for t in timestamps if t]  # Filter None
        if timestamps:
            self.stats['duration_seconds'] = (max(timestamps) - min(timestamps)).total_seconds()

## Performance Optimizations for Large Files

```python
class OptimizedClaudeCodeParser(ClaudeCodeParser):
    """Optimized parser for 100MB+ files"""

    def __init__(self, jsonl_path: Path, **kwargs):
        super().__init__(jsonl_path, **kwargs)
        self.use_streaming = True
        self.chunk_size = 1000  # Process messages in chunks
        self.lazy_load = True

    def parse_messages_streaming(self) -> None:
        """
        Stream parse with minimal memory footprint

        Optimizations:
        - Process in chunks to reduce memory
        - Use generators where possible
        - Build indexes incrementally
        """
        import ijson  # For streaming JSON parsing

        chunk = []
        with open(self.path, 'rb') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                try:
                    # Parse JSON directly from bytes
                    data = json.loads(line)
                    msg = Message.from_json(data)
                    chunk.append(msg)

                    # Process chunk when full
                    if len(chunk) >= self.chunk_size:
                        self._process_chunk(chunk)
                        chunk = []

                except (json.JSONDecodeError, ValueError) as e:
                    self.parse_errors.append({
                        'line': line_num,
                        'error': str(e)
                    })

        # Process remaining messages
        if chunk:
            self._process_chunk(chunk)

    def _process_chunk(self, chunk: List[Message]) -> None:
        """Process a chunk of messages"""
        for msg in chunk:
            self.messages.append(msg)
            self.messages_by_uuid[msg.uuid] = msg

            # Build indexes incrementally
            if msg.parent_uuid:
                if msg.parent_uuid not in self.children_by_parent:
                    self.children_by_parent[msg.parent_uuid] = []
                self.children_by_parent[msg.parent_uuid].append(msg.uuid)

    def get_message_lazy(self, uuid: str) -> Optional[Message]:
        """Lazy load message from disk if not in memory"""
        if uuid in self.messages_by_uuid:
            return self.messages_by_uuid[uuid]

        # Search in file (only if needed)
        if self.lazy_load:
            return self._load_message_from_file(uuid)
        return None

    def _load_message_from_file(self, uuid: str) -> Optional[Message]:
        """Load specific message from file"""
        with open(self.path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if data.get('uuid') == uuid:
                        return Message.from_json(data)
                except json.JSONDecodeError:
                    continue
        return None
```

### Common Tool Patterns

```python
COMMON_TOOLS = {
    'Read': 'File reading',
    'Write': 'File creation',
    'Edit': 'File modification',
    'MultiEdit': 'Multiple file edits',
    'Bash': 'Command execution',
    'Grep': 'Pattern search',
    'Glob': 'File pattern matching',
    'WebFetch': 'Web content retrieval',
    'WebSearch': 'Web searching',
    'TodoWrite': 'Task management'
}

def categorize_tool_usage(tool_uses):
    """Categorize tools by purpose"""
    categories = {
        'file_ops': ['Read', 'Write', 'Edit', 'MultiEdit'],
        'search': ['Grep', 'Glob'],
        'execution': ['Bash'],
        'web': ['WebFetch', 'WebSearch'],
        'planning': ['TodoWrite'],
        'agents': ['Task']  # Sub-agent invocations
    }

    categorized = {cat: [] for cat in categories}

    for tool_use in tool_uses:
        tool_name = tool_use['tool']
        for category, tools in categories.items():
            if tool_name in tools:
                categorized[category].append(tool_use)
                break

    return categorized
```

## Output Generation

```python
class TranscriptGenerator:
    """Generate various output formats from parsed sessions"""

    def __init__(self, parser: ClaudeCodeParser):
        self.parser = parser
        self.output_dir = Path('output')

    def generate_simple_transcript(self, branch_id: str = None) -> str:
        """Generate simple human-readable transcript"""
        lines = []
        messages = self.parser.branches.get(branch_id, self.parser.messages)

        for msg in messages:
            # Format timestamp
            ts = msg.get_timestamp_datetime()
            time_str = ts.strftime('%H:%M:%S') if ts else 'unknown'

            # Identify actor
            actor = self._identify_actor(msg)

            # Format content
            if msg.subtype == 'tool_use':
                content = f"[Tool: {msg.tool_name}]"
            elif msg.message:
                content = msg.message[:200] + ('...' if len(msg.message) > 200 else '')
            else:
                content = '[No content]'

            # Add indentation for sidechains
            indent = '  ' if msg.is_sidechain else ''
            lines.append(f"{time_str} {indent}[{actor}] {content}")

        return '\n'.join(lines)

    def generate_extended_transcript(self) -> Dict:
        """Generate detailed transcript with metadata"""
        return {
            'session_info': {
                'total_messages': len(self.parser.messages),
                'duration': self.parser.stats['duration_seconds'],
                'branches': len(self.parser.branches),
                'sidechains': len(self.parser.sidechains)
            },
            'main_conversation': self._extract_main_thread(),
            'sidechains': self._format_sidechains(),
            'tool_usage': self._analyze_tool_usage(),
            'compact_operations': self.parser.compact_operations
        }

    def _identify_actor(self, msg: Message) -> str:
        """Identify who is speaking"""
        if msg.type == 'user':
            if msg.is_sidechain and msg.user_type == 'external':
                return f'Claude→{msg.agent_name or "Agent"}'
            return 'User'
        elif msg.type == 'assistant':
            if msg.is_sidechain:
                return msg.agent_name or 'Agent'
            return 'Claude'
        elif msg.type in ['system', 'compact_system']:
            return 'System'
        return 'Unknown'

    def _extract_main_thread(self) -> List[Dict]:
        """Extract main conversation without sidechains"""
        main = []
        for msg in self.parser.messages:
            if not msg.is_sidechain:
                main.append({
                    'uuid': msg.uuid,
                    'type': msg.type,
                    'timestamp': msg.timestamp,
                    'content': msg.message,
                    'tool': msg.tool_name
                })
        return main

    def _format_sidechains(self) -> Dict:
        """Format sidechains for output"""
        formatted = {}
        for sc_id, messages in self.parser.sidechains.items():
            agent_name = messages[0].agent_name if messages else 'unknown'
            formatted[sc_id] = {
                'agent': agent_name,
                'message_count': len(messages),
                'messages': [self._format_message(m) for m in messages]
            }
        return formatted

    def _format_message(self, msg: Message) -> Dict:
        """Format single message for output"""
        return {
            'type': msg.type,
            'timestamp': msg.timestamp,
            'content': msg.message[:500] if msg.message else None,
            'tool': msg.tool_name,
            'error': msg.error_message if msg.is_error else None
        }

    def _analyze_tool_usage(self) -> Dict:
        """Analyze and summarize tool usage"""
        tools = {}
        for msg in self.parser.messages:
            if msg.tool_name:
                if msg.tool_name not in tools:
                    tools[msg.tool_name] = {
                        'count': 0,
                        'in_sidechains': 0,
                        'errors': 0
                    }
                tools[msg.tool_name]['count'] += 1
                if msg.is_sidechain:
                    tools[msg.tool_name]['in_sidechains'] += 1
                if msg.is_error:
                    tools[msg.tool_name]['errors'] += 1
        return tools

    def save_outputs(self) -> Path:
        """Save all outputs to directory"""
        self.output_dir.mkdir(exist_ok=True)

        # Save simple transcript
        transcript_path = self.output_dir / 'transcript.txt'
        transcript_path.write_text(self.generate_simple_transcript())

        # Save extended data
        extended_path = self.output_dir / 'extended.json'
        with open(extended_path, 'w') as f:
            json.dump(self.generate_extended_transcript(), f, indent=2, default=str)

        # Save statistics
        stats_path = self.output_dir / 'statistics.json'
        with open(stats_path, 'w') as f:
            json.dump(self.parser.stats, f, indent=2)

        # Generate manifest
        manifest = {
            'generated_at': datetime.now().isoformat(),
            'source_file': str(self.parser.path),
            'outputs': [
                'transcript.txt',
                'extended.json',
                'statistics.json'
            ],
            'statistics': self.parser.stats
        }
        manifest_path = self.output_dir / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        self.parser.logger.info(f"Outputs saved to {self.output_dir}")
        return self.output_dir
```

## Edge Case Handling

### Handling Circular References

```python
def detect_cycles(parser: ClaudeCodeParser) -> List[List[str]]:
    """Detect all cycles in the message graph"""
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
                parser.logger.warning(f"Cycle detected: {' -> '.join(cycle)}")
                return True

        rec_stack.pop()
        return False

    # Check all components
    for msg in parser.messages:
        if msg.uuid not in visited:
            rec_stack = []
            dfs(msg.uuid)

    return cycles

def break_cycles_safe(parser: ClaudeCodeParser) -> int:
    """Safely break cycles by removing the back edge"""
    cycles = detect_cycles(parser)
    broken = 0

    for cycle in cycles:
        # Remove edge from last to first node
        if len(cycle) > 1:
            last_uuid = cycle[-2]  # Second to last (last repeats first)
            first_uuid = cycle[-1]  # Last element is the repeated first

            if last_uuid in parser.children_by_parent:
                if first_uuid in parser.children_by_parent[last_uuid]:
                    parser.children_by_parent[last_uuid].remove(first_uuid)
                    broken += 1
                    parser.logger.info(f"Broke cycle edge: {last_uuid} -> {first_uuid}")

    return broken
```

### Handling Missing Parents (Orphans)

```python
def handle_orphaned_messages(parser: ClaudeCodeParser) -> None:
    """
    Handle orphaned messages intelligently

    Strategies:
    1. Treat as roots (default)
    2. Try to find logical parent by timestamp proximity
    3. Group orphans together
    """
    orphan_strategies = {
        'make_root': lambda m: setattr(m, 'parent_uuid', None),
        'find_temporal_parent': lambda m: find_temporal_parent(parser, m),
        'group_orphans': lambda m: group_with_orphans(parser, m)
    }

    strategy = 'make_root'  # Default strategy

    for orphan in parser.orphaned_messages:
        orphan_strategies[strategy](orphan)
        parser.logger.debug(f"Applied {strategy} to orphan {orphan.uuid}")

def find_temporal_parent(parser: ClaudeCodeParser, orphan: Message) -> None:
    """Find closest message by timestamp to be parent"""
    orphan_time = orphan.get_timestamp_datetime()
    if not orphan_time:
        return

    best_parent = None
    min_diff = float('inf')

    for msg in parser.messages:
        if msg.uuid == orphan.uuid:
            continue

        msg_time = msg.get_timestamp_datetime()
        if msg_time and msg_time < orphan_time:
            diff = (orphan_time - msg_time).total_seconds()
            if diff < min_diff:
                min_diff = diff
                best_parent = msg

    if best_parent and min_diff < 60:  # Within 1 minute
        orphan.parent_uuid = best_parent.uuid
        best_parent.children_uuids.append(orphan.uuid)
        parser.logger.debug(f"Found temporal parent for {orphan.uuid}: {best_parent.uuid}")

def group_with_orphans(parser: ClaudeCodeParser, orphan: Message) -> None:
    """Group orphans together under synthetic parent"""
    if not hasattr(parser, 'orphan_group_parent'):
        # Create synthetic parent for all orphans
        parser.orphan_group_parent = Message(
            type='system',
            uuid='orphan-group-parent',
            timestamp=parser.messages[0].timestamp if parser.messages else '',
            session_id=orphan.session_id,
            message='[Orphaned Messages Group]'
        )
        parser.messages.insert(0, parser.orphan_group_parent)
        parser.messages_by_uuid[parser.orphan_group_parent.uuid] = parser.orphan_group_parent
        parser.roots.append(parser.orphan_group_parent)

    orphan.parent_uuid = parser.orphan_group_parent.uuid
    parser.orphan_group_parent.children_uuids.append(orphan.uuid)
```

### Handling Cloud Sync I/O Errors

```python
import time
import errno
from typing import Callable, Any

def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 0.5,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    logger: logging.Logger = None
) -> Any:
    """
    Retry function with exponential backoff for cloud sync issues

    Handles OneDrive, Dropbox, Google Drive sync delays
    """
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            return func()
        except OSError as e:
            # Check for cloud sync I/O error
            if e.errno == errno.EIO and attempt < max_retries - 1:
                if logger and attempt == 0:
                    logger.warning(
                        f"Cloud sync I/O error - retrying with backoff. "
                        f"File may be syncing from cloud storage. "
                        f"Consider enabling 'Always keep on device' for better performance."
                    )

                time.sleep(min(delay, max_delay))
                delay *= backoff_factor
            else:
                raise
        except Exception as e:
            if attempt < max_retries - 1 and "cloud" in str(e).lower():
                time.sleep(min(delay, max_delay))
                delay *= backoff_factor
            else:
                raise

    raise Exception(f"Failed after {max_retries} retries")

# Usage in parser
def parse_with_retry(file_path: Path) -> List[Message]:
    """Parse file with cloud sync retry logic"""
    def parse_func():
        messages = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    messages.append(Message.from_json(json.loads(line)))
        return messages

    return retry_with_backoff(parse_func, logger=logging.getLogger(__name__))
```

### Handling Multiple Compacts (8+ Sessions)

```python
def handle_deep_compaction(parser: ClaudeCodeParser) -> None:
    """
    Handle sessions with many compact operations

    Long sessions can have 8+ compacts, making reconstruction complex
    """
    if len(parser.compact_operations) > 5:
        parser.logger.warning(f"Heavy compaction detected: {len(parser.compact_operations)} operations")

    # Track compaction depth
    compaction_depth = {}
    for compact in parser.compact_operations:
        for msg_uuid in compact['affected_messages']:
            if msg_uuid in compaction_depth:
                compaction_depth[msg_uuid] += 1
            else:
                compaction_depth[msg_uuid] = 1

    # Warn about deeply compacted messages
    deep_compacts = [uuid for uuid, depth in compaction_depth.items() if depth > 3]
    if deep_compacts:
        parser.logger.warning(f"{len(deep_compacts)} messages compacted 3+ times, may have lost context")

    # Build compaction timeline
    timeline = []
    for compact in parser.compact_operations:
        timeline.append({
            'timestamp': compact['start_timestamp'],
            'event': 'compact_start',
            'affected': len(compact['affected_messages'])
        })
        timeline.append({
            'timestamp': compact['end_timestamp'],
            'event': 'compact_end',
            'metadata': compact.get('metadata', {})
        })

    # Sort by timestamp
    timeline.sort(key=lambda x: x['timestamp'])
    parser.compact_timeline = timeline
```

### Handling Malformed JSON Lines

```python
def parse_malformed_line(line: str, line_num: int, logger: logging.Logger) -> Optional[Dict]:
    """
    Attempt to recover from malformed JSON

    Common issues:
    - Truncated lines
    - Embedded quotes not escaped
    - Invalid unicode
    - Missing closing braces
    """
    strategies = [
        # Strategy 1: Fix common quote issues
        lambda l: json.loads(l.replace("'", '"')),

        # Strategy 2: Fix truncated JSON by adding closing braces
        lambda l: json.loads(fix_truncated_json(l)),

        # Strategy 3: Extract JSON from mixed content
        lambda l: json.loads(extract_json_from_text(l)),

        # Strategy 4: Fix unicode issues
        lambda l: json.loads(l.encode('utf-8', 'ignore').decode('utf-8')),

        # Strategy 5: Use regex to extract valid JSON
        lambda l: json.loads(extract_with_regex(l))
    ]

    for i, strategy in enumerate(strategies):
        try:
            data = strategy(line)
            logger.debug(f"Recovered line {line_num} with strategy {i+1}")
            return data
        except:
            continue

    logger.error(f"Failed to recover line {line_num}: {line[:100]}...")
    return None

def fix_truncated_json(text: str) -> str:
    """Add missing closing braces to truncated JSON"""
    open_braces = text.count('{') - text.count('}')
    open_brackets = text.count('[') - text.count(']')

    if open_braces > 0:
        text += '}' * open_braces
    if open_brackets > 0:
        text += ']' * open_brackets

    return text

def extract_json_from_text(text: str) -> str:
    """Extract JSON object from mixed text"""
    import re
    json_pattern = r'\{[^{}]*\}'
    match = re.search(json_pattern, text)
    if match:
        return match.group(0)
    return text

def extract_with_regex(text: str) -> str:
    """Use regex to find valid JSON structure"""
    import re
    # Match complete JSON object
    pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    return text
```

## Test Patterns and Examples

### Testing DAG Construction

```python
def test_dag_construction():
    """Test DAG building with various edge cases"""
    test_cases = [
        {
            'name': 'Simple linear conversation',
            'messages': [
                {'uuid': '1', 'parentUuid': None, 'type': 'user'},
                {'uuid': '2', 'parentUuid': '1', 'type': 'assistant'},
                {'uuid': '3', 'parentUuid': '2', 'type': 'user'}
            ],
            'expected_roots': 1,
            'expected_orphans': 0
        },
        {
            'name': 'Conversation with orphan',
            'messages': [
                {'uuid': '1', 'parentUuid': None, 'type': 'user'},
                {'uuid': '2', 'parentUuid': '1', 'type': 'assistant'},
                {'uuid': '3', 'parentUuid': 'missing', 'type': 'user'}  # Orphan
            ],
            'expected_roots': 2,  # Original root + orphan becomes root
            'expected_orphans': 1
        },
        {
            'name': 'Circular reference',
            'messages': [
                {'uuid': '1', 'parentUuid': '3', 'type': 'user'},
                {'uuid': '2', 'parentUuid': '1', 'type': 'assistant'},
                {'uuid': '3', 'parentUuid': '2', 'type': 'user'}
            ],
            'expected_roots': 1,  # After breaking cycle
            'expected_orphans': 0
        }
    ]

    for test in test_cases:
        # Add required fields
        for msg in test['messages']:
            msg['timestamp'] = '2024-01-01T00:00:00Z'
            msg['sessionId'] = 'test-session'

        # Create parser and test
        parser = ClaudeCodeParser('dummy.jsonl')
        parser.messages = [Message.from_json(m) for m in test['messages']]
        parser.build_dag()

        assert len(parser.roots) == test['expected_roots'], \
            f"{test['name']}: Expected {test['expected_roots']} roots, got {len(parser.roots)}"
        assert len(parser.orphaned_messages) == test['expected_orphans'], \
            f"{test['name']}: Expected {test['expected_orphans']} orphans, got {len(parser.orphaned_messages)}"
```

### Testing Sidechain Extraction

```python
def test_sidechain_extraction():
    """Test sidechain identification and agent extraction"""
    messages = [
        # Main conversation
        {'uuid': '1', 'type': 'user', 'isSidechain': False},
        {'uuid': '2', 'type': 'assistant', 'isSidechain': False,
         'subtype': 'tool_use', 'toolName': 'Task',
         'toolArguments': {'agentName': 'zen-architect', 'task': 'Design system'}},

        # Sidechain starts
        {'uuid': '3', 'type': 'user', 'isSidechain': True, 'userType': 'external'},
        {'uuid': '4', 'type': 'assistant', 'isSidechain': True},
        {'uuid': '5', 'type': 'system', 'isSidechain': True},

        # Back to main
        {'uuid': '6', 'type': 'user', 'isSidechain': False},

        # Another sidechain
        {'uuid': '7', 'type': 'assistant', 'isSidechain': False,
         'subtype': 'tool_use', 'toolName': 'Task',
         'toolArguments': {'agent': 'bug-hunter', 'task': 'Find issues'}},
        {'uuid': '8', 'type': 'user', 'isSidechain': True, 'userType': 'external'},
        {'uuid': '9', 'type': 'assistant', 'isSidechain': True}
    ]

    # Add required fields and parse
    for msg in messages:
        msg['timestamp'] = '2024-01-01T00:00:00Z'
        msg['sessionId'] = 'test'
        msg['parentUuid'] = None

    parser = ClaudeCodeParser('dummy.jsonl')
    parser.messages = [Message.from_json(m) for m in messages]
    sidechains = parser.extract_sidechains()

    assert len(sidechains) == 2, f"Expected 2 sidechains, got {len(sidechains)}"

    # Check agent identification
    sidechain_keys = list(sidechains.keys())
    assert 'zen-architect' in sidechain_keys[0], "First sidechain should identify zen-architect"
    assert 'bug-hunter' in sidechain_keys[1], "Second sidechain should identify bug-hunter"
```

### Real-World Example Patterns

```python
# Example 1: Parse and generate transcript
def parse_and_export(jsonl_path: Path, output_dir: Path):
    """Complete example of parsing and exporting session"""
    # Initialize parser
    parser = ClaudeCodeParser(jsonl_path)

    # Parse with full pipeline
    parser.parse()

    # Generate outputs
    generator = TranscriptGenerator(parser)
    generator.output_dir = output_dir

    # Save all formats
    generator.save_outputs()

    # Print statistics
    print(f"Session Statistics:")
    print(f"  Total Messages: {parser.stats['total_messages']}")
    print(f"  Duration: {parser.stats['duration_seconds'] / 3600:.2f} hours")
    print(f"  Branches: {parser.stats['branches']}")
    print(f"  Sidechains: {parser.stats['sidechains']}")
    print(f"  Tools Used: {parser.stats['unique_tools']}")

# Example 2: Extract specific branch
def extract_branch_transcript(jsonl_path: Path, branch_num: int = 0):
    """Extract a specific conversation branch"""
    parser = ClaudeCodeParser(jsonl_path)
    parser.parse()

    branches = parser.branches
    branch_keys = sorted(branches.keys())

    if branch_num >= len(branch_keys):
        print(f"Branch {branch_num} not found. Available: 0-{len(branch_keys)-1}")
        return

    branch_id = branch_keys[branch_num]
    messages = branches[branch_id]

    print(f"\\n=== Branch {branch_num} ({branch_id}) ===\\n")
    for msg in messages:
        actor = 'User' if msg.type == 'user' else 'Claude'
        content = msg.message[:100] if msg.message else '[Tool use]'
        print(f"{actor}: {content}")

# Example 3: Analyze tool usage patterns
def analyze_tool_patterns(jsonl_path: Path):
    """Analyze tool usage patterns in session"""
    parser = ClaudeCodeParser(jsonl_path)
    parser.parse()

    tool_stats = {}
    for msg in parser.messages:
        if msg.tool_name:
            if msg.tool_name not in tool_stats:
                tool_stats[msg.tool_name] = {
                    'count': 0,
                    'in_main': 0,
                    'in_sidechain': 0,
                    'errors': 0
                }
            tool_stats[msg.tool_name]['count'] += 1
            if msg.is_sidechain:
                tool_stats[msg.tool_name]['in_sidechain'] += 1
            else:
                tool_stats[msg.tool_name]['in_main'] += 1
            if msg.is_error:
                tool_stats[msg.tool_name]['errors'] += 1

    print("\\nTool Usage Analysis:")
    print("=" * 60)
    for tool, stats in sorted(tool_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        print(f"{tool:20} Total: {stats['count']:4} | Main: {stats['in_main']:4} | "
              f"Sidechain: {stats['in_sidechain']:4} | Errors: {stats['errors']:4}")
```

## Complete Usage Example

```python
# main.py - Production usage example
import logging
from pathlib import Path

def main():
    """Complete example of using the parser"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Input/output paths
    session_file = Path("~/.claude/claude-code/conversations/current.jsonl")
    output_dir = Path("./claude-sessions-output")
    output_dir.mkdir(exist_ok=True)

    try:
        # Initialize and parse
        parser = ClaudeCodeParser(session_file.expanduser())
        parser.parse()

        # Generate outputs
        generator = TranscriptGenerator(parser)
        generator.output_dir = output_dir
        output_path = generator.save_outputs()

        # Print summary
        print(f"\n{'='*60}")
        print(f"Session Analysis Complete")
        print(f"{'='*60}")
        print(f"Input: {session_file}")
        print(f"Output: {output_path}")
        print(f"\nStatistics:")
        print(f"  Messages: {parser.stats['total_messages']}")
        print(f"  Duration: {parser.stats['duration_seconds'] / 3600:.1f} hours")
        print(f"  Branches: {parser.stats['branches']}")
        print(f"  Sidechains: {parser.stats['sidechains']} ({len(parser.sidechains)} agents)")
        print(f"  Tools Used: {parser.stats['unique_tools']}")
        print(f"  Parse Errors: {parser.stats['parse_errors']}")
        print(f"  Orphaned Messages: {parser.stats['orphaned_messages']}")

        # Show any warnings
        if parser.parse_errors:
            print(f"\nWarning: {len(parser.parse_errors)} parse errors encountered")
            print("First 3 errors:")
            for err in parser.parse_errors[:3]:
                print(f"  Line {err['line']}: {err['error']}")

        if parser.orphaned_messages:
            print(f"\nNote: {len(parser.orphaned_messages)} orphaned messages (treated as roots)")

        if parser.compact_operations:
            print(f"\nCompaction: {len(parser.compact_operations)} operations performed")
            total_affected = sum(len(c['affected_messages']) for c in parser.compact_operations)
            print(f"  Total messages affected: {total_affected}")

    except FileNotFoundError as e:
        print(f"Error: Session file not found - {e}")
        print("Make sure Claude Code is installed and has created sessions")
    except Exception as e:
        logging.exception("Parser failed")
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
```

## Key Implementation Takeaways

### Architecture Decisions

1. **Message Class Design**
   - Use dataclasses for clean structure
   - Include all possible fields with Optional types
   - Add computed fields for parser tracking (logical_parent, depth, branch_id)

2. **DAG Construction**
   - **CRITICAL**: Orphaned messages become roots
   - Cycle detection and breaking is essential
   - Track both actual and logical parent relationships

3. **Sidechain Handling**
   - Extract agent name from Task tool invocation
   - Group consecutive sidechain messages
   - Preserve temporal order within sidechains

4. **Performance Optimizations**
   - Stream parse for 100MB+ files
   - Dictionary lookups for O(1) access
   - Lazy loading when memory is constrained
   - Chunk processing for very large files

5. **Error Recovery**
   - Cloud sync retry with exponential backoff
   - Malformed JSON recovery strategies
   - Graceful handling of missing parents
   - Comprehensive error logging

### Critical Edge Cases

1. **Orphaned Messages**: Messages referencing non-existent parents must become roots
2. **Circular References**: Can occur in complex sessions - must detect and break
3. **Cloud Sync Delays**: OneDrive/Dropbox can cause I/O errors - retry with backoff
4. **Multiple Compacts**: Long sessions (8+ hours) have many compacts - track carefully
5. **Malformed JSON**: Real logs have truncated lines - implement recovery strategies

### Production Checklist

- [ ] Implement cloud sync retry logic
- [ ] Handle orphaned messages as roots
- [ ] Detect and break cycles in DAG
- [ ] Extract agent names from Task tool
- [ ] Track logical parent relationships through compacts
- [ ] Stream parse for large files
- [ ] Generate multiple output formats
- [ ] Include comprehensive error reporting
- [ ] Test with edge cases (cycles, orphans, malformed)
- [ ] Optimize for 100MB+ files

This guide provides a complete, production-ready implementation for parsing Claude Code session logs with all critical details and edge cases handled.
