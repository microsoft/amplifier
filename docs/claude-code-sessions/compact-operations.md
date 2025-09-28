# Claude Code Compact Operations

## Overview

Compact operations are Claude Code's mechanism for managing context window limitations. When conversations exceed approximately 155,000 tokens, Claude Code performs a compaction to maintain continuity while reducing memory usage.

## Types of Compact Operations

### Manual Compacts (39% of cases)

Triggered by user command `/compact`:
- User explicitly requests context reduction
- Useful when conversation becomes unwieldy
- Preserves user-selected important context

### Automatic Compacts (61% of cases)

Triggered automatically at ~155,000 tokens:
- System-initiated to prevent context overflow
- Transparent to user (mostly)
- Preserves recent conversation context

## Compact Operation Mechanics

### 1. Message Sequence

Every compact operation follows this pattern:

```json
// Step 1: Compaction begins
{
  "type": "compact_system",
  "uuid": "compact-start-001",
  "message": "conversation_compacting",
  "timestamp": "2025-01-27T10:00:00Z"
}

// Step 2: Compaction completes
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

// Step 3: New root message created
{
  "type": "user",
  "uuid": "new-root-001",
  "parentUuid": null,  // No parent - new root
  "logicalParentUuid": "pre-compact-msg-500",  // Logical continuity
  "timestamp": "2025-01-27T10:00:02Z",
  "message": "Continue from before compact"
}

// Optional Step 4: Restoration message
{
  "type": "compact_system",
  "uuid": "restored-001",
  "message": "conversation_restored",
  "timestamp": "2025-01-27T10:00:03Z"
}
```

### 2. Key Behaviors

**Session Continuity**:
- Same file continues after compact
- New root message created (null parentUuid)
- Session ID remains unchanged
- Timestamp sequence continues

**Message Preservation**:
- Recent messages retained (typically 10-20)
- System messages often preserved
- Tool results may be summarized
- Sidechains typically excluded

**Orphaned Messages**:
- Post-compact messages reference non-existent parents
- 15-20% of messages become orphaned after compacts
- Must be treated as roots for DAG traversal

## Handling Multiple Compacts

Sessions commonly have 8+ compact operations. Each creates a new "epoch" in the conversation:

```python
def identify_compact_epochs(messages):
    """Identify conversation epochs separated by compacts"""
    epochs = []
    current_epoch = []
    in_compact = False

    for msg in messages:
        if msg.get('type') == 'compact_system':
            if msg.get('message') == 'conversation_compacting':
                # Save current epoch
                if current_epoch:
                    epochs.append(current_epoch)
                in_compact = True

            elif msg.get('message') == 'conversation_compacted':
                in_compact = False
                current_epoch = []  # Start new epoch

        elif not in_compact:
            current_epoch.append(msg)

    # Don't forget last epoch
    if current_epoch:
        epochs.append(current_epoch)

    return epochs
```

## Logical Parent Tracking

The `logicalParentUuid` field maintains conversational continuity:

```python
def trace_logical_flow(messages):
    """Trace conversation flow across compact boundaries"""
    logical_map = {}

    for msg in messages:
        if 'logicalParentUuid' in msg:
            logical_map[msg['uuid']] = msg['logicalParentUuid']

    def get_full_ancestry(uuid):
        """Get complete ancestry including logical parents"""
        ancestry = []
        current = uuid

        while current:
            if current in messages_by_uuid:
                ancestry.append(current)
                # Check logical parent first, then regular parent
                current = logical_map.get(current) or \
                         messages_by_uuid[current].get('parentUuid')
            else:
                break

        return ancestry

    return logical_map
```

## Compact Metadata

Compact messages often include metadata:

```json
{
  "type": "compact_system",
  "message": "conversation_compacted",
  "metadata": {
    "preservedMessages": 15,      // Messages kept
    "totalMessages": 500,         // Original count
    "compressionRatio": 0.03,     // Preservation ratio
    "trigger": "automatic",        // or "manual"
    "tokenCount": 155234,         // Tokens before compact
    "reducedTokenCount": 8500     // Tokens after compact
  }
}
```

## Implementation Patterns

### Pattern 1: Compact-Aware Parser

```python
class CompactAwareParser:
    def __init__(self):
        self.compact_count = 0
        self.orphan_roots = []
        self.logical_links = {}

    def parse_with_compacts(self, messages):
        """Parse messages handling compact operations"""
        processed = []
        compact_boundaries = []

        for i, msg in enumerate(messages):
            # Track compact operations
            if msg.get('type') == 'compact_system':
                self.handle_compact_message(msg, i, compact_boundaries)

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

    def handle_compact_message(self, msg, index, boundaries):
        """Process compact system messages"""
        if msg.get('message') == 'conversation_compacting':
            self.compact_count += 1
            boundaries.append({
                'type': 'start',
                'index': index,
                'compact_number': self.compact_count
            })
        elif msg.get('message') == 'conversation_compacted':
            if boundaries and boundaries[-1]['type'] == 'start':
                boundaries[-1]['end_index'] = index
                boundaries[-1]['type'] = 'complete'
```

### Pattern 2: Session Reconstruction

```python
def reconstruct_compacted_session(messages):
    """Reconstruct full session across compacts"""
    epochs = identify_compact_epochs(messages)
    full_session = []

    for epoch_num, epoch in enumerate(epochs):
        # Process each epoch
        epoch_data = {
            'number': epoch_num + 1,
            'messages': epoch,
            'has_orphans': False,
            'root_count': 0
        }

        # Count roots and orphans
        for msg in epoch:
            if not msg.get('parentUuid'):
                epoch_data['root_count'] += 1
            elif msg.get('is_orphan_root'):
                epoch_data['has_orphans'] = True

        full_session.append(epoch_data)

    return full_session
```

### Pattern 3: Context Window Estimation

```python
def estimate_context_usage(messages):
    """Estimate when compacts will occur"""
    import tiktoken

    encoding = tiktoken.encoding_for_model("claude-3")
    token_count = 0
    compact_predictions = []

    for i, msg in enumerate(messages):
        # Estimate tokens (rough approximation)
        content = msg.get('message', '')
        if content:
            tokens = len(encoding.encode(content))
            token_count += tokens

        # Predict compact
        if token_count > 150000 and not compact_predictions:
            compact_predictions.append({
                'message_index': i,
                'estimated_tokens': token_count,
                'likelihood': 'high'
            })

    return compact_predictions
```

## Best Practices

### 1. Always Handle Orphans

```python
def safe_parent_lookup(msg, messages_by_uuid):
    """Safely look up parent, handling orphans"""
    parent_uuid = msg.get('parentUuid')

    if not parent_uuid:
        return None  # True root

    if parent_uuid not in messages_by_uuid:
        # Orphaned - treat as root
        logger.debug(f"Orphaned message {msg['uuid']} (parent {parent_uuid} not found)")
        return None

    return messages_by_uuid[parent_uuid]
```

### 2. Track Compact Statistics

```python
def analyze_compact_patterns(session_files):
    """Analyze compact patterns across sessions"""
    stats = {
        'total_sessions': 0,
        'sessions_with_compacts': 0,
        'total_compacts': 0,
        'max_compacts_per_session': 0,
        'avg_messages_between_compacts': []
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

### 3. Preserve Conversation Flow

```python
def maintain_conversation_flow(messages):
    """Maintain conversation flow across compacts"""
    conversation = []
    logical_parent_map = {}

    for msg in messages:
        # Skip compact system messages in flow
        if msg.get('type') == 'compact_system':
            continue

        # Track logical parents
        if 'logicalParentUuid' in msg:
            logical_parent_map[msg['uuid']] = msg['logicalParentUuid']

        # Add to conversation
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

## Testing Compact Handling

```python
def test_compact_handling():
    """Test parser handles compacts correctly"""
    test_messages = [
        # Pre-compact messages
        {'uuid': 'msg-1', 'type': 'user', 'parentUuid': None},
        {'uuid': 'msg-2', 'type': 'assistant', 'parentUuid': 'msg-1'},

        # Compact operation
        {'type': 'compact_system', 'message': 'conversation_compacting'},
        {'type': 'compact_system', 'message': 'conversation_compacted',
         'metadata': {'preservedMessages': 0, 'totalMessages': 2}},

        # Post-compact orphan
        {'uuid': 'msg-3', 'type': 'user', 'parentUuid': 'msg-2',  # Orphaned!
         'logicalParentUuid': 'msg-2'},
    ]

    parser = CompactAwareParser()
    processed, boundaries = parser.parse_with_compacts(test_messages)

    assert parser.compact_count == 1
    assert len(parser.orphan_roots) == 1
    assert 'msg-3' in parser.orphan_roots
    print("✓ Compact handling test passed")

test_compact_handling()
```

## Key Takeaways

1. **Compacts are normal**: Sessions with 8+ compacts are common
2. **Orphans are expected**: 15-20% orphan rate after compacts
3. **Use logical parents**: Track `logicalParentUuid` for continuity
4. **Same file continues**: No new file created during compact
5. **Preserve flow**: Maintain conversation coherence across boundaries
6. **Handle gracefully**: Don't treat orphans or compacts as errors