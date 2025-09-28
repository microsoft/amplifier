# Claude Code Session Implementation Guide

## Overview

This guide provides complete implementation specifications for working with Claude Code session logs. It covers all critical patterns, edge cases, and production-ready code examples.

## Message DAG Architecture

### Core Principles

Claude Code messages form a Directed Acyclic Graph (DAG) structure:

- Each message has a unique `uuid` identifier
- Messages reference their parent via `parentUuid`
- Multiple children create branches (edits, retries)
- Missing parents indicate orphaned messages (session continuations)

### Orphaned Message Handling

**Critical**: Messages with non-existent `parentUuid` values are orphaned messages that must be treated as root nodes.

```python
def build_dag_with_orphans(messages):
    """Build DAG handling orphaned messages correctly"""
    messages_by_uuid = {msg['uuid']: msg for msg in messages}
    children_by_parent = {}
    roots = []
    orphans = []

    for msg in messages:
        parent_uuid = msg.get('parentUuid')

        if not parent_uuid:
            # True root (no parent specified)
            roots.append(msg)
        elif parent_uuid not in messages_by_uuid:
            # Orphaned message - parent doesn't exist
            orphans.append(msg)
            roots.append(msg)  # Treat as root for traversal
        else:
            # Normal parent-child relationship
            if parent_uuid not in children_by_parent:
                children_by_parent[parent_uuid] = []
            children_by_parent[parent_uuid].append(msg['uuid'])

    return {
        'messages': messages_by_uuid,
        'children': children_by_parent,
        'roots': roots,
        'orphans': orphans
    }
```

### Branch Detection

File position determines active vs abandoned branches:

```python
def identify_active_branch(messages_by_uuid, children_by_parent, parent_uuid):
    """Later children in file represent active branches"""
    children_uuids = children_by_parent.get(parent_uuid, [])
    if not children_uuids:
        return None

    # Sort by original file position (preserved in parse order)
    children = [messages_by_uuid[uuid] for uuid in children_uuids]

    # Last child in file = active branch
    return children[-1]['uuid']
```

## Compact Operations

### Architecture

Compact operations maintain session continuity while reducing context:

- **Trigger**: Manual (`/compact`) or automatic (~155k tokens)
- **Behavior**: Stay in same file, create new root
- **Continuity**: Tracked via `logicalParentUuid` field
- **Frequency**: Sessions can have 8+ compacts

### Implementation

```python
class CompactHandler:
    def __init__(self):
        self.compact_boundaries = []
        self.logical_parent_map = {}

    def process_compact(self, messages):
        """Process messages handling compact operations"""
        processed = []
        in_compact = False
        compact_root = None

        for msg in messages:
            if msg.get('type') == 'compact_system':
                if msg.get('message') == 'conversation_compacting':
                    in_compact = True
                    self.compact_boundaries.append({
                        'start': msg['uuid'],
                        'timestamp': msg['timestamp']
                    })
                elif msg.get('message') == 'conversation_compacted':
                    in_compact = False
                    compact_root = None
                    self.compact_boundaries[-1]['end'] = msg['uuid']

            # Track logical parent for continuity
            if msg.get('logicalParentUuid'):
                self.logical_parent_map[msg['uuid']] = msg['logicalParentUuid']

            # First message after compact becomes new root
            if not in_compact and compact_root is None:
                if msg.get('parentUuid') is None:
                    compact_root = msg['uuid']
                    if self.compact_boundaries:
                        msg['compact_session'] = len(self.compact_boundaries)

            processed.append(msg)

        return processed

    def get_logical_parent(self, uuid):
        """Get logical parent across compact boundaries"""
        return self.logical_parent_map.get(uuid)
```

## Sidechain Processing

### Agent Identification

Agent names come from the Task tool's `subagent_type` parameter, not from an "agent" field:

```python
def extract_agent_from_task(assistant_msg):
    """Extract agent name from Task tool invocation"""
    if assistant_msg.get('subtype') != 'tool_use':
        return None

    if assistant_msg.get('toolName') != 'Task':
        return None

    # Agent name is in subagent_type parameter
    tool_args = assistant_msg.get('toolArguments', {})
    return tool_args.get('subagent_type', 'unknown-agent')

def match_sidechains_to_agents(messages):
    """Match sidechain conversations to originating agents"""
    sidechain_agents = {}
    pending_task = None

    for msg in messages:
        # Check for Task tool invocation
        if msg.get('type') == 'assistant' and msg.get('toolName') == 'Task':
            agent = extract_agent_from_task(msg)
            task_prompt = msg.get('toolArguments', {}).get('task', '')
            pending_task = {
                'uuid': msg['uuid'],
                'agent': agent,
                'prompt': task_prompt
            }

        # Check for sidechain start
        if msg.get('isSidechain') and msg.get('type') == 'user':
            if pending_task and msg.get('parentUuid') == pending_task['uuid']:
                # Match sidechain to agent
                sidechain_agents[msg['uuid']] = pending_task['agent']
                pending_task = None

    return sidechain_agents
```

### Multi-Turn Sidechain Tracking

```python
class SidechainProcessor:
    def __init__(self):
        self.current_agent = None
        self.sidechain_stack = []

    def process_message(self, msg, sidechain_agents):
        """Process message with sidechain context"""
        is_sidechain = msg.get('isSidechain', False)

        if is_sidechain:
            # Check if new sidechain starting
            if msg['uuid'] in sidechain_agents:
                self.current_agent = sidechain_agents[msg['uuid']]
                self.sidechain_stack.append({
                    'agent': self.current_agent,
                    'start': msg['uuid'],
                    'messages': [msg]
                })
            elif self.sidechain_stack:
                # Continue current sidechain
                self.sidechain_stack[-1]['messages'].append(msg)

            # Determine actor
            if msg['type'] == 'user':
                actor = 'Claude'  # Claude acts as user in sidechains
            else:
                actor = self.current_agent or 'SubAgent'
        else:
            # Main conversation
            if self.sidechain_stack:
                # Exiting sidechain
                completed = self.sidechain_stack.pop()
                self.current_agent = None

            if msg['type'] == 'user':
                actor = 'Human'
            else:
                actor = 'Claude'

        return {
            'actor': actor,
            'in_sidechain': is_sidechain,
            'agent': self.current_agent if is_sidechain else None
        }
```

## File I/O with Retry Logic

### Cloud Sync Handling

OneDrive, Dropbox, and other cloud sync services can cause I/O errors. Implement retry logic:

```python
import time
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def write_with_retry(file_path, data, max_retries=3):
    """Write file with retry logic for cloud sync issues"""
    retry_delay = 0.1

    for attempt in range(max_retries):
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                if isinstance(data, (dict, list)):
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    f.write(str(data))
                f.flush()

            return True

        except OSError as e:
            if e.errno == 5 and attempt < max_retries - 1:
                if attempt == 0:
                    logger.warning(
                        f"I/O error writing to {file_path} - retrying. "
                        "This may be due to cloud-synced files (OneDrive, Dropbox, etc.). "
                        "Consider enabling 'Always keep on this device' for better performance."
                    )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise

    return False

def read_with_retry(file_path, max_retries=3):
    """Read file with retry logic for cloud sync issues"""
    retry_delay = 0.1

    for attempt in range(max_retries):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()

        except OSError as e:
            if e.errno == 5 and attempt < max_retries - 1:
                if attempt == 0:
                    logger.warning(f"I/O error reading {file_path} - retrying (cloud sync delay)")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise

    return None
```

## Session File Organization

### Best Practice Structure

```
~/.claude/projects/{project-name}/
├── {timestamp}__{project}__{sessionid}/
│   ├── history.jsonl           # Original session data
│   ├── transcript.md           # Human-readable main thread
│   ├── transcript_extended.md  # Full details with sidechains
│   ├── branches/              # Alternative conversation paths
│   │   ├── branch_001.md
│   │   └── branch_002.md
│   ├── sidechains/            # Extracted sub-agent conversations
│   │   ├── sidechain_001_zen-architect.md
│   │   └── sidechain_002_bug-hunter.md
│   └── manifest.json          # Session metadata and statistics
```

### Implementation

```python
class SessionOrganizer:
    def __init__(self, session_file):
        self.session_file = Path(session_file)
        self.messages = self.parse_session()
        self.output_dir = self.create_output_structure()

    def create_output_structure(self):
        """Create organized output directory"""
        timestamp = self.messages[0]['timestamp'].replace(':', '-')
        session_id = self.messages[0]['sessionId']
        project = self.session_file.parent.name

        dir_name = f"{timestamp}__{project}__{session_id}"
        output_dir = self.session_file.parent / dir_name

        # Create subdirectories
        (output_dir / 'branches').mkdir(parents=True, exist_ok=True)
        (output_dir / 'sidechains').mkdir(parents=True, exist_ok=True)

        # Copy original file
        import shutil
        shutil.copy(self.session_file, output_dir / 'history.jsonl')

        return output_dir

    def generate_transcripts(self):
        """Generate all transcript files"""
        # Main transcript
        main_thread = self.extract_main_thread()
        self.write_transcript(main_thread, self.output_dir / 'transcript.md')

        # Extended transcript
        full_convo = self.extract_full_conversation()
        self.write_extended_transcript(full_convo, self.output_dir / 'transcript_extended.md')

        # Branches
        branches = self.extract_branches()
        for i, branch in enumerate(branches, 1):
            path = self.output_dir / 'branches' / f'branch_{i:03d}.md'
            self.write_transcript(branch, path)

        # Sidechains
        sidechains = self.extract_sidechains_with_agents()
        for i, (agent, sidechain) in enumerate(sidechains.items(), 1):
            path = self.output_dir / 'sidechains' / f'sidechain_{i:03d}_{agent}.md'
            self.write_sidechain(sidechain, path, agent)

        # Manifest
        self.write_manifest()

    def write_manifest(self):
        """Write session metadata and statistics"""
        manifest = {
            'session_id': self.messages[0]['sessionId'],
            'project': self.session_file.parent.name,
            'message_count': len(self.messages),
            'duration': self.calculate_duration(),
            'branches': self.count_branches(),
            'sidechains': self.count_sidechains(),
            'compact_operations': self.count_compacts(),
            'tools_used': self.get_unique_tools(),
            'agents_invoked': self.get_unique_agents(),
            'orphaned_messages': len(self.find_orphans())
        }

        write_with_retry(
            self.output_dir / 'manifest.json',
            manifest
        )
```

## Complete Implementation Example

```python
class ClaudeCodeSessionProcessor:
    """Production-ready Claude Code session processor"""

    def __init__(self, session_file):
        self.session_file = Path(session_file)
        self.messages = []
        self.dag = None
        self.compact_handler = CompactHandler()
        self.sidechain_processor = SidechainProcessor()
        self.errors = []

    def parse(self):
        """Parse session with all edge case handling"""
        # Read with retry for cloud sync
        content = read_with_retry(self.session_file)
        if not content:
            raise ValueError(f"Could not read {self.session_file}")

        # Parse messages
        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if not line:
                continue

            try:
                msg = json.loads(line)
                self.messages.append(msg)
            except json.JSONDecodeError as e:
                self.errors.append({
                    'line': line_num,
                    'error': str(e)
                })

        # Process compact operations
        self.messages = self.compact_handler.process_compact(self.messages)

        # Build DAG with orphan handling
        self.dag = build_dag_with_orphans(self.messages)

        # Match sidechains to agents
        self.sidechain_agents = match_sidechains_to_agents(self.messages)

        return self

    def get_complete_conversation(self, include_sidechains=True):
        """Get full conversation with proper actor identification"""
        conversation = []

        for msg in self.messages:
            # Process with sidechain context
            context = self.sidechain_processor.process_message(
                msg, self.sidechain_agents
            )

            # Skip sidechains if not included
            if not include_sidechains and context['in_sidechain']:
                continue

            # Build conversation entry
            entry = {
                'uuid': msg['uuid'],
                'timestamp': msg['timestamp'],
                'actor': context['actor'],
                'type': msg['type'],
                'message': msg.get('message', ''),
                'in_sidechain': context['in_sidechain'],
                'agent': context['agent']
            }

            # Add tool information
            if msg.get('subtype') == 'tool_use':
                entry['tool'] = msg.get('toolName')
                entry['tool_args'] = msg.get('toolArguments')

            conversation.append(entry)

        return conversation

    def export_session(self, output_dir=None):
        """Export complete organized session"""
        if not output_dir:
            output_dir = self.session_file.parent

        organizer = SessionOrganizer(self.session_file)
        organizer.messages = self.messages
        organizer.generate_transcripts()

        return organizer.output_dir

# Usage
if __name__ == "__main__":
    processor = ClaudeCodeSessionProcessor("~/.claude/projects/myproject/session.jsonl")
    processor.parse()

    # Export organized session
    output_dir = processor.export_session()
    print(f"Session exported to: {output_dir}")

    # Get conversation with agents identified
    conversation = processor.get_complete_conversation()
    for entry in conversation[:10]:
        if entry['in_sidechain']:
            print(f"[{entry['actor']} via {entry['agent']}]: {entry['message'][:50]}...")
        else:
            print(f"[{entry['actor']}]: {entry['message'][:50]}...")
```

## Key Implementation Requirements

1. **Always handle orphaned messages** - Treat as roots, not errors
2. **Implement retry logic** - Essential for cloud-synced directories
3. **Extract agent names from Task tools** - Not from message fields
4. **Track compact continuity** - Via `logicalParentUuid` when present
5. **Preserve file position** - Determines active branches
6. **Match sidechains to agents** - Required for proper identification
7. **Handle multi-turn sidechains** - Track agent throughout conversation
8. **Organize output systematically** - Use subdirectory structure