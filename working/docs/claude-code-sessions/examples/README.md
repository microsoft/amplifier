# Claude Code Session Examples

This directory contains working examples for parsing and processing Claude Code session files from real Claude Code sessions stored at `~/.claude/projects/`.

## Context-Aware Session Selection

When running the tools without arguments, they intelligently select sessions based on your current directory:

1. **If you're in a project directory**: Automatically uses sessions from that specific project
2. **Most specific match wins**: If multiple projects match your path, the most specific one is chosen
3. **Fallback to most recent**: If not in a project directory, uses the most recent session across all projects

For example, if you're working in `/home/user/repos/myproject` and have a corresponding Claude Code project, the tools will automatically use sessions from that project.

## Quick Start

### Using the Command-Line Tools

The example tools now work with real Claude Code sessions by default and save outputs to organized directories:

```bash
# Parse the most recent session across all projects
python example_parser.py
# Creates: ./output/{project}/{session}/analysis.md and session.jsonl

# Build a transcript from the most recent session
python example_transcript_builder.py
# Creates: ./output/{project}/{session}/transcript.md and session.jsonl

# Use custom output directory
python example_parser.py --output ./my-analysis
python example_transcript_builder.py --output ./my-transcripts

# List all available projects and sessions
python example_parser.py --list

# Parse most recent session from a specific project
python example_parser.py --project amplifier

# Parse a specific session file
python example_parser.py /path/to/session.jsonl

# Build transcript with system messages included
python example_transcript_builder.py --include-system
```

### Output Directory Structure

Both tools create organized output directories:

```
./output/                             # Default, or custom via --output
├── -home-user-repos-myproject/      # Project directory name
│   ├── abc123-session-id/           # Session UUID
│   │   ├── analysis.md              # Session analysis (from parser)
│   │   ├── transcript.md            # Human-readable transcript (from builder)
│   │   └── session.jsonl            # Copy of source JSONL file
│   └── def456-session-id/
│       ├── analysis.md
│       ├── transcript.md
│       └── session.jsonl
```

### Programmatic Usage

```python
from pathlib import Path
import json

def parse_session(file_path):
    """Parse a Claude Code session file."""
    messages = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                messages.append(json.loads(line))
    return messages

# Parse your session
session_file = Path.home() / ".claude/projects/your-project/session.jsonl"
messages = parse_session(session_file)
print(f"Session contains {len(messages)} messages")
```

## Command-Line Tools

### example_parser.py

A parser that analyzes Claude Code sessions and saves comprehensive analysis.

**Features:**

- Auto-discovers Claude Code projects in `~/.claude/projects/`
- Context-aware: automatically uses sessions from your current project directory
- Parses the most recent session by default (with smart project matching)
- Saves analysis to `{output}/{project}/{session}/analysis.md`
- Copies source JSONL to output directory
- Provides session statistics and tool usage analysis
- Supports fuzzy matching for project names

**Usage:**

```bash
# Default: parse most recent session, save to ./output/
python example_parser.py

# Use custom output directory
python example_parser.py --output ./my-analysis

# List all projects and sessions
python example_parser.py --list

# Parse from specific project (fuzzy match)
python example_parser.py --project amplifier
python example_parser.py -p "blog-writer"

# Parse specific session within a project
python example_parser.py --project amplifier --session c9153d95

# Parse a specific file
python example_parser.py /path/to/session.jsonl
```

### example_transcript_builder.py

Builds readable transcripts from Claude Code session files.

**Features:**

- Converts DAG structure to linear transcript
- Context-aware: automatically uses sessions from your current project directory
- Saves transcript to `{output}/{project}/{session}/transcript.md`
- Copies source JSONL to output directory
- Proper attribution (User, Claude, Sub-agent, System)
- Optional inclusion of system messages
- Automatic output file naming
- Configurable preview length

**Usage:**

```bash
# Default: build transcript for most recent session, save to ./output/
python example_transcript_builder.py

# Use custom output directory
python example_transcript_builder.py --output ./my-transcripts

# Include system messages (tool results)
python example_transcript_builder.py --include-system

# Specify project and session
python example_transcript_builder.py --project amplifier --session abc123

# Custom input and output files (overrides directory structure)
python example_transcript_builder.py input.jsonl specific-output.md

# Adjust preview length
python example_transcript_builder.py --preview-lines 50
```

## Complete Examples

### 1. Session Analyzer

Analyze a session for statistics and patterns:

```python
def analyze_session(messages):
    """Analyze session for patterns and statistics."""
    stats = {
        'total': len(messages),
        'by_type': {},
        'tools_used': set(),
        'sidechains': 0
    }

    for msg in messages:
        # Count by type
        msg_type = msg.get('type', 'unknown')
        stats['by_type'][msg_type] = stats['by_type'].get(msg_type, 0) + 1

        # Track tools
        if msg_type == 'assistant':
            content = msg.get('message', {}).get('content', [])
            if isinstance(content, list):
                for item in content:
                    if item.get('type') == 'tool_use':
                        stats['tools_used'].add(item.get('name'))

        # Count sidechains
        if msg.get('isSidechain'):
            stats['sidechains'] += 1

    return stats
```

### 2. DAG Navigator

Navigate the conversation DAG:

```python
def build_dag(messages):
    """Build DAG structure from messages."""
    dag = {
        'messages': {},
        'children': {},
        'roots': []
    }

    for msg in messages:
        uuid = msg.get('uuid')
        parent_uuid = msg.get('parentUuid')

        # Store message
        dag['messages'][uuid] = msg

        # Track parent-child relationships
        if parent_uuid:
            if parent_uuid not in dag['children']:
                dag['children'][parent_uuid] = []
            dag['children'][parent_uuid].append(uuid)
        else:
            # No parent = root
            dag['roots'].append(uuid)

    return dag

def get_conversation_path(dag, start_uuid=None):
    """Get the active conversation path."""
    path = []

    # Start from root if not specified
    if not start_uuid and dag['roots']:
        start_uuid = dag['roots'][0]

    current_uuid = start_uuid
    while current_uuid:
        msg = dag['messages'].get(current_uuid)
        if msg:
            path.append(msg)

        # Get children
        children = dag['children'].get(current_uuid, [])
        if children:
            # Take last child (most recent)
            current_uuid = children[-1]
        else:
            current_uuid = None

    return path
```

### 3. Tool Correlation

Match tool invocations with their results:

```python
def correlate_tools(messages):
    """Correlate tool invocations with results."""
    invocations = {}
    correlations = []

    # First pass: collect invocations
    for msg in messages:
        if msg.get('type') == 'assistant':
            content = msg.get('message', {}).get('content', [])
            if isinstance(content, list):
                for item in content:
                    if item.get('type') == 'tool_use':
                        tool_id = item.get('id')
                        invocations[tool_id] = {
                            'name': item.get('name'),
                            'input': item.get('input'),
                            'message_uuid': msg.get('uuid')
                        }

    # Second pass: find results
    for msg in messages:
        if msg.get('type') == 'user':
            content = msg.get('message', {}).get('content', [])
            if isinstance(content, list):
                for item in content:
                    if item.get('type') == 'tool_result':
                        tool_use_id = item.get('tool_use_id')
                        if tool_use_id in invocations:
                            correlations.append({
                                'invocation': invocations[tool_use_id],
                                'result': item.get('content'),
                                'is_error': item.get('is_error', False)
                            })

    return correlations
```

### 4. Sidechain Extractor

Extract sidechain conversations (sub-agent interactions):

```python
def extract_sidechains(messages):
    """Extract all sidechain conversations."""
    sidechains = {}
    current_sidechain = None

    for msg in messages:
        if msg.get('isSidechain'):
            # Find which sidechain this belongs to
            if not current_sidechain:
                # New sidechain starting
                current_sidechain = msg.get('uuid')
                sidechains[current_sidechain] = []

            sidechains[current_sidechain].append(msg)

        elif current_sidechain:
            # Sidechain ended
            current_sidechain = None

    return sidechains
```

## Important Notes

### Real Session Format vs Documentation

The actual Claude Code session format has some differences from the documented format:

1. **Message structure**: Real sessions use nested `message` objects with `content` arrays
2. **Tool results**: Appear as `user` messages with `tool_result` content items
3. **Sidechains**: Sub-agent interactions are marked with `isSidechain: true`
4. **Attribution**: Message attribution depends on context (main vs sidechain conversation)

### Session File Locations

Claude Code sessions are stored at:

```
~/.claude/projects/<project-name>/<session-uuid>.jsonl
```

Project names are sanitized versions of the working directory path with `-` separators.

### Performance Considerations

- Session files can be large (several MB for long conversations)
- The examples use simple in-memory processing suitable for most sessions
- For very large sessions, consider streaming processing approaches

## Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

The examples use only Python standard library, but the requirements file includes optional packages for enhanced functionality.

## Advanced Usage

### Custom Session Processing

```python
from example_parser import SimpleParser
from example_transcript_builder import TranscriptBuilder

# Parse session
parser = SimpleParser()
messages = parser.parse_file("session.jsonl")

# Analyze tools
tools = parser.find_tools()
print(f"Found {len(tools)} tool invocations")

# Build transcript
builder = TranscriptBuilder()
builder.load_session("session.jsonl")
transcript = builder.build_transcript(include_system=True)

# Save to file
with open("transcript.txt", "w") as f:
    f.write(transcript)
```

### Batch Processing

Process all sessions in a project:

```python
from pathlib import Path

project_dir = Path.home() / ".claude/projects/-home-user-myproject"

for session_file in project_dir.glob("*.jsonl"):
    print(f"Processing {session_file.name}")
    parser = SimpleParser()
    parser.parse_file(session_file)
    parser.print_summary()
    print("-" * 40)
```

## Contributing

These examples are designed to be simple and educational. Feel free to:

- Extend them for your specific use cases
- Add new analysis capabilities
- Contribute improvements back to the documentation

## License

These examples are provided as part of the Claude Code session documentation and are available for use in your own projects.
