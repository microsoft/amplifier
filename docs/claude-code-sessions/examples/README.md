# Claude Code Session Examples

This directory contains working examples for parsing and processing Claude Code session files.

## Quick Start

```python
# Basic session parsing
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
session_file = Path("~/.claude/conversations/project/session.jsonl")
messages = parse_session(session_file)
print(f"Session contains {len(messages)} messages")
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

# Analyze your session
stats = analyze_session(messages)
print(f"Message types: {stats['by_type']}")
print(f"Tools used: {stats['tools_used']}")
print(f"Sidechain messages: {stats['sidechains']}")
```

### 2. Transcript Builder

Build a readable transcript from a session:

```python
def build_transcript(messages):
    """Build a human-readable transcript."""
    transcript = []

    for msg in messages:
        msg_type = msg.get('type')

        if msg_type == 'human':
            content = extract_text(msg.get('message', {}))
            transcript.append(f"User: {content}")

        elif msg_type == 'assistant':
            content = extract_text(msg.get('message', {}))
            transcript.append(f"Assistant: {content}")

            # Note tool uses
            tools = extract_tools(msg.get('message', {}))
            for tool in tools:
                transcript.append(f"  [Tool: {tool}]")

        elif msg_type == 'tool_result':
            # Show brief result
            result = extract_result(msg.get('message', {}))
            if result:
                preview = result[:100] + '...' if len(result) > 100 else result
                transcript.append(f"  [Result: {preview}]")

    return '\n\n'.join(transcript)

def extract_text(message):
    """Extract text content from message structure."""
    if isinstance(message, str):
        return message

    content = message.get('content', '')
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                texts.append(item.get('text', ''))
        return ' '.join(texts)

    return str(content)

def extract_tools(message):
    """Extract tool names from message."""
    tools = []
    content = message.get('content', [])
    if isinstance(content, list):
        for item in content:
            if item.get('type') == 'tool_use':
                tools.append(item.get('name'))
    return tools

def extract_result(message):
    """Extract tool result content."""
    content = message.get('content', [])
    if isinstance(content, list):
        for item in content:
            if item.get('type') == 'tool_result':
                return item.get('content', '')
    return None

# Build transcript
transcript = build_transcript(messages)
print(transcript[:1000])  # Print first 1000 chars
```

### 3. DAG Navigator

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

# Build DAG and get active path
dag = build_dag(messages)
active_path = get_conversation_path(dag)
print(f"Active conversation has {len(active_path)} messages")
```

### 4. Tool Correlation

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
        if msg.get('type') == 'tool_result':
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

# Correlate tools
tool_correlations = correlate_tools(messages)
for corr in tool_correlations[:5]:  # Show first 5
    inv = corr['invocation']
    print(f"Tool: {inv['name']}")
    if corr['is_error']:
        print(f"  Error: {corr['result'][:100]}")
    else:
        print(f"  Success: {corr['result'][:100] if corr['result'] else 'No output'}")
```

### 5. Sidechain Extractor

Extract sidechain conversations:

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

def find_sidechain_agent(sidechain_messages, all_messages):
    """Find the agent for a sidechain."""
    if not sidechain_messages:
        return 'unknown'

    # First sidechain message's parent should have Task tool
    first_msg = sidechain_messages[0]
    parent_uuid = first_msg.get('parentUuid')

    # Find parent message
    for msg in all_messages:
        if msg.get('uuid') == parent_uuid:
            # Look for Task tool
            content = msg.get('message', {}).get('content', [])
            if isinstance(content, list):
                for item in content:
                    if item.get('type') == 'tool_use' and item.get('name') == 'Task':
                        return item.get('input', {}).get('subagent_type', 'unknown')

    return 'unknown'

# Extract sidechains
sidechains = extract_sidechains(messages)
for sc_id, sc_messages in sidechains.items():
    agent = find_sidechain_agent(sc_messages, messages)
    print(f"Sidechain with {agent}: {len(sc_messages)} messages")
```

## Running the Examples

1. Update the session file path to point to your actual session:
   ```python
   session_file = Path.home() / ".claude/conversations/your-project/session.jsonl"
   ```

2. Run any example:
   ```bash
   python analyze_session.py
   ```

3. Combine examples for more complex analysis:
   ```python
   # Complete analysis
   messages = parse_session(session_file)
   dag = build_dag(messages)
   stats = analyze_session(messages)
   transcript = build_transcript(messages)
   tools = correlate_tools(messages)
   sidechains = extract_sidechains(messages)

   print(f"Session overview:")
   print(f"  Total messages: {stats['total']}")
   print(f"  Tools used: {len(stats['tools_used'])}")
   print(f"  Sidechains: {len(sidechains)}")
   print(f"  Successful tool uses: {sum(1 for t in tools if not t['is_error'])}")
   ```

## Advanced Examples

For more advanced examples including:
- Performance optimization for large files
- Real-time session monitoring
- Export to various formats
- Branch analysis and navigation

See the implementation guides in the parent documentation.