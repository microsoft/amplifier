# Compact Operations Specification

## Operation Definition

Compact operations reduce conversation context when approaching token limits. Operations maintain session continuity within the same file while creating new conversation roots.

## Trigger Conditions

### Manual Trigger
- User command: `/compact`
- Immediate execution upon request

### Automatic Trigger
- Token count threshold: ~155,000 tokens
- System-initiated without user intervention

## Operation Sequence

### Message Flow Structure

```json
// Phase 1: Initiation
{
  "type": "compact_system",
  "uuid": "compact-start-001",
  "message": "conversation_compacting",
  "timestamp": "2025-01-27T10:00:00Z"
}

// Phase 2: Completion
{
  "type": "compact_system",
  "uuid": "compact-end-001",
  "message": "conversation_compacted",
  "timestamp": "2025-01-27T10:00:01Z",
  "metadata": {
    "preservedMessages": 15,
    "totalMessages": 500,
    "compressionRatio": 0.03
  }
}

// Phase 3: New Root Creation
{
  "type": "user",
  "uuid": "new-root-001",
  "parentUuid": null,
  "logicalParentUuid": "pre-compact-msg-500",
  "timestamp": "2025-01-27T10:00:02Z"
}

// Phase 4: Optional Restoration
{
  "type": "compact_system",
  "uuid": "restored-001",
  "message": "conversation_restored",
  "timestamp": "2025-01-27T10:00:03Z"
}
```

## Behavioral Specifications

### Session Continuity
- File persistence: Same file continues post-compact
- Root creation: New message with null `parentUuid`
- Session ID: Remains unchanged
- Timestamp sequence: Continues incrementally

### Message Preservation
- Retention count: 10-20 recent messages typically preserved
- System messages: Often retained for context
- Tool results: May be summarized or excluded
- Sidechains: Typically excluded from preserved set

### Orphaned Message Generation
- Post-compact messages reference pre-compact parents
- Orphan rate: 15-20% of messages post-compact
- Required handling: Treat orphaned messages as DAG roots

## Multi-Compact Handling

Sessions support multiple compact operations, creating distinct conversation epochs:

```python
def identify_epochs(messages):
    """Identify conversation epochs separated by compacts"""
    epochs = []
    current_epoch = []
    in_compact = False

    for msg in messages:
        if msg.get('type') == 'compact_system':
            if msg.get('message') == 'conversation_compacting':
                if current_epoch:
                    epochs.append(current_epoch)
                in_compact = True
            elif msg.get('message') == 'conversation_compacted':
                in_compact = False
                current_epoch = []
        elif not in_compact:
            current_epoch.append(msg)

    if current_epoch:
        epochs.append(current_epoch)

    return epochs
```

## Logical Parent Tracking

The `logicalParentUuid` field maintains conversational continuity across compact boundaries:

```python
def trace_logical_continuity(messages):
    """Trace conversation flow using logical parents"""
    logical_map = {}

    for msg in messages:
        if 'logicalParentUuid' in msg:
            logical_map[msg['uuid']] = msg['logicalParentUuid']

    return logical_map
```

## Compact Metadata Structure

```json
{
  "type": "compact_system",
  "message": "conversation_compacted",
  "metadata": {
    "preservedMessages": 15,      // Messages retained
    "totalMessages": 500,         // Pre-compact count
    "compressionRatio": 0.03,     // Retention ratio
    "trigger": "automatic",        // "manual" or "automatic"
    "tokenCount": 155234,         // Pre-compact tokens
    "reducedTokenCount": 8500     // Post-compact tokens
  }
}
```

## Implementation Requirements

### Compact-Aware Parser

```python
class CompactParser:
    def __init__(self):
        self.compact_count = 0
        self.orphan_roots = []
        self.logical_links = {}

    def parse(self, messages):
        """Parse messages with compact handling"""
        processed = []
        compact_boundaries = []

        for i, msg in enumerate(messages):
            # Track compact operations
            if msg.get('type') == 'compact_system':
                self.process_compact(msg, i, compact_boundaries)

            # Handle orphaned messages
            if msg.get('parentUuid'):
                if not self.parent_exists(msg['parentUuid'], processed):
                    self.orphan_roots.append(msg['uuid'])
                    msg['is_orphan_root'] = True

            # Track logical parents
            if 'logicalParentUuid' in msg:
                self.logical_links[msg['uuid']] = msg['logicalParentUuid']

            processed.append(msg)

        return processed, compact_boundaries
```

### Session Reconstruction

```python
def reconstruct_session(messages):
    """Reconstruct full session across compacts"""
    epochs = identify_epochs(messages)
    session_data = []

    for epoch_num, epoch in enumerate(epochs):
        epoch_info = {
            'number': epoch_num + 1,
            'messages': epoch,
            'has_orphans': False,
            'root_count': 0
        }

        for msg in epoch:
            if not msg.get('parentUuid'):
                epoch_info['root_count'] += 1
            elif msg.get('is_orphan_root'):
                epoch_info['has_orphans'] = True

        session_data.append(epoch_info)

    return session_data
```

### Context Window Estimation

```python
def estimate_compact_trigger(messages, encoding):
    """Estimate compact trigger points"""
    token_count = 0
    trigger_points = []

    for i, msg in enumerate(messages):
        content = msg.get('message', '')
        if content:
            tokens = len(encoding.encode(content))
            token_count += tokens

        if token_count > 150000 and not trigger_points:
            trigger_points.append({
                'message_index': i,
                'estimated_tokens': token_count
            })

    return trigger_points
```

## Required Behaviors

### Orphan Handling

```python
def safe_parent_lookup(msg, messages_by_uuid):
    """Safely resolve parent with orphan handling"""
    parent_uuid = msg.get('parentUuid')

    if not parent_uuid:
        return None  # Explicit root

    if parent_uuid not in messages_by_uuid:
        # Orphaned - treat as root
        return None

    return messages_by_uuid[parent_uuid]
```

### Compact Statistics Tracking

```python
def analyze_compacts(session_files):
    """Analyze compact patterns across sessions"""
    stats = {
        'total_sessions': 0,
        'sessions_with_compacts': 0,
        'total_compacts': 0,
        'max_compacts_per_session': 0
    }

    for file in session_files:
        messages = parse_session(file)
        compacts = find_compact_operations(messages)

        stats['total_sessions'] += 1
        if compacts:
            stats['sessions_with_compacts'] += 1
            stats['total_compacts'] += len(compacts)
            stats['max_compacts_per_session'] = max(
                stats['max_compacts_per_session'],
                len(compacts)
            )

    return stats
```

### Conversation Flow Preservation

```python
def maintain_flow(messages):
    """Maintain conversation flow across compacts"""
    conversation = []
    logical_parent_map = {}

    for msg in messages:
        # Skip compact system messages
        if msg.get('type') == 'compact_system':
            continue

        # Track logical parents
        if 'logicalParentUuid' in msg:
            logical_parent_map[msg['uuid']] = msg['logicalParentUuid']

        conversation.append({
            'uuid': msg['uuid'],
            'content': msg.get('message', ''),
            'physical_parent': msg.get('parentUuid'),
            'logical_parent': logical_parent_map.get(msg['uuid']),
            'is_post_compact': msg.get('parentUuid') is None and
                              msg['uuid'] in logical_parent_map
        })

    return conversation
```

## Test Validation

```python
def test_compact_handling():
    """Validate compact handling implementation"""
    test_messages = [
        # Pre-compact
        {'uuid': 'msg-1', 'type': 'user', 'parentUuid': None},
        {'uuid': 'msg-2', 'type': 'assistant', 'parentUuid': 'msg-1'},

        # Compact operation
        {'type': 'compact_system', 'message': 'conversation_compacting'},
        {'type': 'compact_system', 'message': 'conversation_compacted',
         'metadata': {'preservedMessages': 0, 'totalMessages': 2}},

        # Post-compact orphan
        {'uuid': 'msg-3', 'type': 'user', 'parentUuid': 'msg-2',
         'logicalParentUuid': 'msg-2'},
    ]

    parser = CompactParser()
    processed, boundaries = parser.parse(test_messages)

    assert parser.compact_count == 1
    assert len(parser.orphan_roots) == 1
    assert 'msg-3' in parser.orphan_roots
```

## Key Specifications

- Compact operations occur within 8+ times per session
- Orphan rate: 15-20% of messages post-compact
- Logical parent tracking via `logicalParentUuid` field
- Session file continuity maintained
- Conversation flow preserved across boundaries
- Orphaned messages treated as DAG roots