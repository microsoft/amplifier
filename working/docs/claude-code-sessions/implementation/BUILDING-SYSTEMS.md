# Building Systems with Claude Code Sessions

This guide covers building tools and systems that work with Claude Code session files.

## System Architecture

### Core Components

```python
class ClaudeCodeSystem:
    """Base system for working with Claude Code sessions."""

    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.sessions = {}
        self.current_session = None

    def load_session(self, file_path: Path):
        """Load and parse a session file."""
        dag = parse_session_file(file_path)
        session_id = file_path.stem
        self.sessions[session_id] = dag
        return dag

    def get_active_conversation(self, session_id: str):
        """Get the active conversation path."""
        if session_id not in self.sessions:
            return []
        return get_active_path(self.sessions[session_id])
```

## Common Use Cases

### Transcript Generation

Generate human-readable transcripts from sessions:

```python
class TranscriptBuilder:
    """Build formatted transcripts from sessions."""

    def __init__(self, dag: SessionDAG):
        self.dag = dag

    def build_transcript(self, include_sidechains: bool = False) -> str:
        """Generate a formatted transcript."""
        lines = []
        path = get_active_path(self.dag)

        for msg in path:
            # Format message based on type
            if msg.type == 'human':
                lines.append(f"User: {self.extract_text(msg)}")
            elif msg.type == 'assistant':
                lines.append(f"Assistant: {self.extract_text(msg)}")

                # Include tool invocations
                for tool in msg.tool_invocations:
                    lines.append(f"  [Tool: {tool['name']}]")

            elif msg.type == 'tool_result':
                # Show tool results inline
                for result in msg.tool_results:
                    if result.get('is_error'):
                        lines.append(f"  [Error: {result['content'][:100]}...]")
                    else:
                        lines.append(f"  [Result: {result['content'][:100]}...]")

            # Handle sidechains if requested
            if include_sidechains and msg.tool_invocations:
                for tool in msg.tool_invocations:
                    if tool.get('name') == 'Task':
                        sidechain = get_sidechain_messages(self.dag, msg)
                        if sidechain:
                            lines.append("  --- Sidechain Start ---")
                            for sc_msg in sidechain:
                                lines.append(f"    {self.format_sidechain_message(sc_msg)}")
                            lines.append("  --- Sidechain End ---")

        return "\n\n".join(lines)

    def extract_text(self, msg: Message) -> str:
        """Extract text content from a message."""
        content = msg.content

        if isinstance(content, str):
            return content

        if isinstance(content, dict):
            if 'content' in content:
                return self.extract_text({'content': content['content']})

        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    texts.append(item.get('text', ''))
            return " ".join(texts)

        return str(content)
```

### Session Analytics

Analyze session patterns and statistics:

```python
class SessionAnalyzer:
    """Analyze Claude Code sessions."""

    def __init__(self, dag: SessionDAG):
        self.dag = dag

    def get_statistics(self) -> dict:
        """Calculate session statistics."""
        stats = {
            'total_messages': len(self.dag.messages),
            'human_messages': 0,
            'assistant_messages': 0,
            'tool_invocations': 0,
            'tool_results': 0,
            'sidechains': 0,
            'branches': 0,
            'orphans': 0,
            'max_depth': 0
        }

        # Count message types
        for msg in self.dag.messages.values():
            if msg.type == 'human':
                stats['human_messages'] += 1
            elif msg.type == 'assistant':
                stats['assistant_messages'] += 1
            elif msg.type == 'tool_result':
                stats['tool_results'] += 1

            # Count tools
            stats['tool_invocations'] += len(msg.tool_invocations)

            # Count sidechains
            if msg.is_sidechain:
                stats['sidechains'] += 1

            # Count orphans
            if getattr(msg, 'is_orphan', False):
                stats['orphans'] += 1

        # Count branches
        for children in self.dag.children_by_parent.values():
            if len(children) > 1:
                stats['branches'] += 1

        # Calculate max depth
        stats['max_depth'] = self.calculate_max_depth()

        return stats

    def calculate_max_depth(self) -> int:
        """Calculate maximum conversation depth."""
        max_depth = 0

        for root_uuid in self.dag.roots:
            depth = self._get_depth(root_uuid, 0)
            max_depth = max(max_depth, depth)

        return max_depth

    def _get_depth(self, uuid: str, current_depth: int) -> int:
        """Recursively calculate depth."""
        msg = self.dag.messages.get(uuid)
        if not msg or not msg.children_uuids:
            return current_depth

        max_child_depth = current_depth
        for child_uuid in msg.children_uuids:
            child_depth = self._get_depth(child_uuid, current_depth + 1)
            max_child_depth = max(max_child_depth, child_depth)

        return max_child_depth
```

### Tool Usage Analysis

Analyze tool usage patterns:

```python
class ToolAnalyzer:
    """Analyze tool usage in sessions."""

    def __init__(self, dag: SessionDAG):
        self.dag = dag

    def get_tool_usage(self) -> dict:
        """Analyze tool usage patterns."""
        tools = {}

        for msg in self.dag.messages.values():
            for tool in msg.tool_invocations:
                tool_name = tool.get('name')
                if tool_name not in tools:
                    tools[tool_name] = {
                        'count': 0,
                        'success': 0,
                        'error': 0,
                        'examples': []
                    }

                tools[tool_name]['count'] += 1

                # Find corresponding result
                tool_id = tool.get('id')
                if tool_id in self.dag.tool_results_by_id:
                    result = self.dag.tool_results_by_id[tool_id]
                    if result.get('is_error'):
                        tools[tool_name]['error'] += 1
                    else:
                        tools[tool_name]['success'] += 1

                    # Store example
                    if len(tools[tool_name]['examples']) < 3:
                        tools[tool_name]['examples'].append({
                            'input': tool.get('input'),
                            'result': result.get('result')[:200] if result.get('result') else None
                        })

        return tools

    def find_failed_tools(self) -> list:
        """Find all failed tool invocations."""
        failures = []

        for tool_id, result in self.dag.tool_results_by_id.items():
            if result.get('is_error'):
                # Find the invocation
                for msg in self.dag.messages.values():
                    for tool in msg.tool_invocations:
                        if tool.get('id') == tool_id:
                            failures.append({
                                'tool_name': tool.get('name'),
                                'input': tool.get('input'),
                                'error': result.get('result'),
                                'message_uuid': msg.uuid
                            })

        return failures
```

### Session Export

Export sessions to different formats:

```python
class SessionExporter:
    """Export sessions to various formats."""

    def __init__(self, dag: SessionDAG):
        self.dag = dag

    def to_markdown(self) -> str:
        """Export to Markdown format."""
        lines = ["# Claude Code Session\n"]

        path = get_active_path(self.dag)
        for msg in path:
            if msg.type == 'human':
                lines.append(f"## User\n\n{self.extract_text(msg)}\n")
            elif msg.type == 'assistant':
                lines.append(f"## Assistant\n\n{self.extract_text(msg)}\n")

                # Include code blocks for tools
                for tool in msg.tool_invocations:
                    if tool.get('name') in ['Write', 'Edit']:
                        content = tool.get('input', {}).get('content', '')
                        if content:
                            lines.append(f"```python\n{content}\n```\n")

        return "\n".join(lines)

    def to_json(self) -> dict:
        """Export to structured JSON."""
        return {
            'session_id': list(self.dag.messages.values())[0].session_id if self.dag.messages else None,
            'messages': [
                {
                    'uuid': msg.uuid,
                    'type': msg.type,
                    'timestamp': msg.timestamp,
                    'content': self.extract_text(msg),
                    'tools': msg.tool_invocations
                }
                for msg in get_active_path(self.dag)
            ],
            'statistics': SessionAnalyzer(self.dag).get_statistics()
        }
```

## Streaming Processing

Handle large sessions efficiently:

```python
class StreamingProcessor:
    """Process large sessions without loading entire file."""

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def count_messages(self) -> int:
        """Count messages without loading full file."""
        count = 0
        with open(self.file_path, 'r') as f:
            for line in f:
                if line.strip():
                    count += 1
        return count

    def find_messages_by_type(self, msg_type: str):
        """Stream find messages of specific type."""
        with open(self.file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue

                data = json.loads(line)
                if data.get('type') == msg_type:
                    yield line_num, data

    def extract_time_range(self) -> tuple:
        """Get timestamp range without loading full file."""
        min_time = float('inf')
        max_time = 0

        with open(self.file_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue

                data = json.loads(line)
                timestamp = data.get('timestamp', 0)
                min_time = min(min_time, timestamp)
                max_time = max(max_time, timestamp)

        return min_time, max_time
```

## Session Monitoring

Monitor active sessions for changes:

```python
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SessionMonitor(FileSystemEventHandler):
    """Monitor session files for changes."""

    def __init__(self, session_dir: Path, callback):
        self.session_dir = session_dir
        self.callback = callback
        self.sessions = {}

    def on_modified(self, event):
        """Handle file modifications."""
        if event.is_directory:
            return

        if event.src_path.endswith('.jsonl'):
            file_path = Path(event.src_path)

            # Parse new messages since last check
            self.process_new_messages(file_path)

    def process_new_messages(self, file_path: Path):
        """Process only new messages in file."""
        session_id = file_path.stem

        # Get last processed line
        last_line = self.sessions.get(session_id, 0)

        with open(file_path, 'r') as f:
            # Skip to last processed line
            for _ in range(last_line):
                f.readline()

            # Process new lines
            line_num = last_line
            for line in f:
                line_num += 1
                if line.strip():
                    data = json.loads(line)
                    self.callback(session_id, data)

            self.sessions[session_id] = line_num

    def start_monitoring(self):
        """Start monitoring session directory."""
        observer = Observer()
        observer.schedule(self, str(self.session_dir), recursive=False)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
```

## Usage Examples

### Complete System

```python
# Initialize system
system = ClaudeCodeSystem(Path("~/.claude/conversations/project"))

# Load session
session_file = Path("~/.claude/conversations/project/session.jsonl")
dag = system.load_session(session_file)

# Generate transcript
transcript = TranscriptBuilder(dag).build_transcript(include_sidechains=True)
print(transcript)

# Analyze session
stats = SessionAnalyzer(dag).get_statistics()
print(f"Session contains {stats['total_messages']} messages")
print(f"Tools invoked {stats['tool_invocations']} times")

# Export to markdown
exporter = SessionExporter(dag)
markdown = exporter.to_markdown()
with open("session.md", "w") as f:
    f.write(markdown)

# Monitor for changes
def on_new_message(session_id, message):
    print(f"New message in {session_id}: {message['type']}")

monitor = SessionMonitor(system.session_dir, on_new_message)
monitor.start_monitoring()
```