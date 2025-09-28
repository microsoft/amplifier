# Claude Code Message DAG Architecture

## Overview

Claude Code messages form a Directed Acyclic Graph (DAG) structure that captures the complete conversation flow, including linear progressions, branches from edits, and parallel sidechains. Understanding this architecture is essential for properly parsing and reconstructing conversations.

## DAG Fundamentals

### Core Structure

Every message contains:
- `uuid`: Unique identifier
- `parentUuid`: Reference to parent message (optional)
- `timestamp`: Creation time
- `sessionId`: Session grouping

The parent-child relationships create a directed graph where:
- Messages flow from parent to child
- No cycles exist (acyclic property)
- Multiple roots are possible
- Branches represent alternative paths

### Visual Representation

```
Root Message (uuid: msg-001, parentUuid: null)
├── Assistant Response (uuid: msg-002, parentUuid: msg-001)
│   ├── User Continue (uuid: msg-003, parentUuid: msg-002) [ACTIVE]
│   │   └── Assistant Reply (uuid: msg-004, parentUuid: msg-003)
│   └── User Edit (uuid: msg-005, parentUuid: msg-002) [ABANDONED]
│       └── Assistant Alt Reply (uuid: msg-006, parentUuid: msg-005)
└── User Retry (uuid: msg-007, parentUuid: msg-001) [ABANDONED]
```

## Key Patterns

### 1. Linear Conversation

The simplest pattern - sequential message flow:

```python
def is_linear_conversation(messages):
    """Check if conversation has no branches"""
    parent_counts = {}
    for msg in messages:
        parent = msg.get('parentUuid')
        if parent:
            parent_counts[parent] = parent_counts.get(parent, 0) + 1

    # Linear if no parent has multiple children
    return all(count == 1 for count in parent_counts.values())
```

### 2. Branching from Edits

"Redo from here" creates branches:

```python
def identify_branch_points(messages):
    """Find messages where conversation branches"""
    children_map = {}

    for msg in messages:
        parent = msg.get('parentUuid')
        if parent:
            if parent not in children_map:
                children_map[parent] = []
            children_map[parent].append(msg['uuid'])

    branch_points = []
    for parent, children in children_map.items():
        if len(children) > 1:
            branch_points.append({
                'parent': parent,
                'branches': children,
                'branch_count': len(children)
            })

    return branch_points
```

### 3. Orphaned Messages as Roots

Messages with non-existent parents become roots:

```python
def find_all_roots(messages):
    """Find all root messages including orphans"""
    messages_by_uuid = {msg['uuid']: msg for msg in messages}
    roots = []

    for msg in messages:
        parent_uuid = msg.get('parentUuid')

        if not parent_uuid:
            # Explicit root (no parent specified)
            roots.append({'uuid': msg['uuid'], 'type': 'explicit'})

        elif parent_uuid not in messages_by_uuid:
            # Orphaned root (parent doesn't exist)
            roots.append({'uuid': msg['uuid'], 'type': 'orphan', 'missing_parent': parent_uuid})

    return roots
```

### 4. Active vs Abandoned Branches

File position determines the active branch:

```python
def determine_active_paths(messages):
    """Determine active vs abandoned branches"""
    # Build parent-child map with file positions
    children_by_parent = {}
    message_positions = {msg['uuid']: i for i, msg in enumerate(messages)}

    for msg in messages:
        parent = msg.get('parentUuid')
        if parent:
            if parent not in children_by_parent:
                children_by_parent[parent] = []
            children_by_parent[parent].append(msg['uuid'])

    # For each branch point, last child is active
    branch_status = {}
    for parent, children in children_by_parent.items():
        if len(children) > 1:
            # Sort by file position
            children.sort(key=lambda x: message_positions[x])

            for i, child in enumerate(children):
                is_active = (i == len(children) - 1)
                branch_status[child] = 'active' if is_active else 'abandoned'

    return branch_status
```

## DAG Construction

### Complete DAG Builder

```python
class MessageDAG:
    def __init__(self, messages):
        self.messages_by_uuid = {msg['uuid']: msg for msg in messages}
        self.children_by_parent = {}
        self.roots = []
        self.orphans = []
        self.build_dag(messages)

    def build_dag(self, messages):
        """Build complete DAG structure"""
        for msg in messages:
            uuid = msg['uuid']
            parent_uuid = msg.get('parentUuid')

            if not parent_uuid:
                # Explicit root
                self.roots.append(uuid)
            elif parent_uuid not in self.messages_by_uuid:
                # Orphaned message - treat as root
                self.orphans.append(uuid)
                self.roots.append(uuid)
            else:
                # Normal parent-child relationship
                if parent_uuid not in self.children_by_parent:
                    self.children_by_parent[parent_uuid] = []
                self.children_by_parent[parent_uuid].append(uuid)

    def get_children(self, uuid):
        """Get immediate children of a message"""
        return self.children_by_parent.get(uuid, [])

    def get_descendants(self, uuid):
        """Get all descendants of a message"""
        descendants = []
        to_visit = [uuid]

        while to_visit:
            current = to_visit.pop(0)
            children = self.get_children(current)
            descendants.extend(children)
            to_visit.extend(children)

        return descendants

    def get_ancestors(self, uuid):
        """Get all ancestors of a message"""
        ancestors = []
        current = uuid

        while current:
            msg = self.messages_by_uuid.get(current)
            if not msg:
                break

            parent = msg.get('parentUuid')
            if parent and parent in self.messages_by_uuid:
                ancestors.append(parent)
                current = parent
            else:
                break

        return list(reversed(ancestors))

    def get_path_to_root(self, uuid):
        """Get complete path from root to message"""
        path = self.get_ancestors(uuid)
        path.append(uuid)
        return path
```

## Traversal Strategies

### 1. Depth-First Traversal

```python
def depth_first_traverse(dag, start_uuid=None):
    """Traverse DAG depth-first from start or all roots"""
    visited = set()
    traversal = []

    def dfs(uuid, depth=0):
        if uuid in visited:
            return

        visited.add(uuid)
        msg = dag.messages_by_uuid.get(uuid)
        if msg:
            traversal.append({
                'uuid': uuid,
                'depth': depth,
                'message': msg
            })

        for child in dag.get_children(uuid):
            dfs(child, depth + 1)

    if start_uuid:
        dfs(start_uuid)
    else:
        for root in dag.roots:
            dfs(root)

    return traversal
```

### 2. Breadth-First Traversal

```python
def breadth_first_traverse(dag):
    """Traverse DAG breadth-first from all roots"""
    visited = set()
    traversal = []
    queue = [(root, 0) for root in dag.roots]

    while queue:
        uuid, depth = queue.pop(0)

        if uuid in visited:
            continue

        visited.add(uuid)
        msg = dag.messages_by_uuid.get(uuid)
        if msg:
            traversal.append({
                'uuid': uuid,
                'depth': depth,
                'message': msg
            })

        for child in dag.get_children(uuid):
            if child not in visited:
                queue.append((child, depth + 1))

    return traversal
```

### 3. Active Path Traversal

```python
def traverse_active_path(dag, branch_status):
    """Traverse only the active conversation path"""
    visited = set()
    active_path = []

    def follow_active(uuid, depth=0):
        if uuid in visited:
            return

        visited.add(uuid)
        msg = dag.messages_by_uuid.get(uuid)
        if msg:
            active_path.append({
                'uuid': uuid,
                'depth': depth,
                'message': msg
            })

        children = dag.get_children(uuid)
        if children:
            # Choose active child or last child
            active_child = None
            for child in children:
                if branch_status.get(child) == 'active':
                    active_child = child
                    break

            if not active_child:
                # Default to last child if no explicit active
                active_child = children[-1]

            follow_active(active_child, depth + 1)

    for root in dag.roots:
        follow_active(root)

    return active_path
```

## Cycle Detection

### Defensive Programming

```python
def detect_cycles(messages):
    """Detect cycles in message DAG (should never happen)"""
    graph = {}

    # Build adjacency list
    for msg in messages:
        uuid = msg['uuid']
        parent = msg.get('parentUuid')

        if uuid not in graph:
            graph[uuid] = []

        if parent:
            if parent not in graph:
                graph[parent] = []
            graph[parent].append(uuid)

    # DFS cycle detection
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    cycles = []

    def dfs(node, path):
        color[node] = GRAY
        path.append(node)

        for neighbor in graph.get(node, []):
            if color[neighbor] == GRAY:
                # Found cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:]
                cycles.append(cycle)
            elif color[neighbor] == WHITE:
                dfs(neighbor, path[:])

        color[node] = BLACK

    for node in graph:
        if color[node] == WHITE:
            dfs(node, [])

    return cycles
```

## Path Extraction

### All Paths from Root to Leaves

```python
def extract_all_paths(dag):
    """Extract all complete paths from roots to leaves"""
    paths = []

    def find_paths(uuid, current_path):
        current_path = current_path + [uuid]
        children = dag.get_children(uuid)

        if not children:
            # Leaf node - complete path
            paths.append(current_path)
        else:
            # Continue to children
            for child in children:
                find_paths(child, current_path)

    for root in dag.roots:
        find_paths(root, [])

    return paths
```

### Longest Path

```python
def find_longest_path(dag):
    """Find the longest path in the DAG"""
    all_paths = extract_all_paths(dag)

    if not all_paths:
        return []

    longest = max(all_paths, key=len)
    return longest
```

## Sidechain Integration

### Sidechain-Aware DAG

```python
class SidechainDAG(MessageDAG):
    def __init__(self, messages):
        super().__init__(messages)
        self.sidechains = self.identify_sidechains()

    def identify_sidechains(self):
        """Identify sidechain boundaries in DAG"""
        sidechains = []
        current_sidechain = None

        for msg in self.messages_by_uuid.values():
            is_sidechain = msg.get('isSidechain', False)

            if is_sidechain:
                if not current_sidechain:
                    # Start new sidechain
                    current_sidechain = {
                        'start': msg['uuid'],
                        'messages': [msg['uuid']]
                    }
                else:
                    # Continue sidechain
                    current_sidechain['messages'].append(msg['uuid'])
            else:
                if current_sidechain:
                    # End sidechain
                    current_sidechain['end'] = current_sidechain['messages'][-1]
                    sidechains.append(current_sidechain)
                    current_sidechain = None

        return sidechains

    def get_main_thread(self):
        """Extract main conversation excluding sidechains"""
        main_thread = []

        for uuid in self.traverse_all():
            msg = self.messages_by_uuid[uuid]
            if not msg.get('isSidechain', False):
                main_thread.append(uuid)

        return main_thread
```

## Visualization

### DAG to Graphviz

```python
def dag_to_graphviz(dag):
    """Convert DAG to Graphviz DOT format"""
    lines = ['digraph conversation {']
    lines.append('  rankdir=TB;')

    # Add nodes
    for uuid, msg in dag.messages_by_uuid.items():
        label = msg.get('type', 'unknown')
        color = {
            'user': 'lightblue',
            'assistant': 'lightgreen',
            'system': 'lightgray'
        }.get(label, 'white')

        lines.append(f'  "{uuid}" [label="{label}", fillcolor={color}, style=filled];')

    # Add edges
    for parent, children in dag.children_by_parent.items():
        for child in children:
            lines.append(f'  "{parent}" -> "{child}";')

    lines.append('}')
    return '\n'.join(lines)
```

### ASCII Tree

```python
def print_dag_tree(dag, uuid=None, prefix="", is_last=True):
    """Print DAG as ASCII tree"""
    if uuid is None:
        # Start from roots
        for i, root in enumerate(dag.roots):
            is_last = (i == len(dag.roots) - 1)
            print_dag_tree(dag, root, "", is_last)
        return

    msg = dag.messages_by_uuid.get(uuid, {})
    msg_type = msg.get('type', 'unknown')
    connector = "└── " if is_last else "├── "

    print(f"{prefix}{connector}{msg_type} ({uuid[:8]}...)")

    children = dag.get_children(uuid)
    extension = "    " if is_last else "│   "

    for i, child in enumerate(children):
        is_last_child = (i == len(children) - 1)
        print_dag_tree(dag, child, prefix + extension, is_last_child)
```

## Performance Optimizations

### Lazy Loading

```python
class LazyDAG:
    """DAG with lazy evaluation for large sessions"""

    def __init__(self, message_generator):
        self.message_generator = message_generator
        self._messages_cache = {}
        self._children_cache = {}
        self._loaded = False

    def _ensure_loaded(self):
        """Load messages on first access"""
        if not self._loaded:
            for msg in self.message_generator():
                self._messages_cache[msg['uuid']] = msg
                parent = msg.get('parentUuid')
                if parent:
                    if parent not in self._children_cache:
                        self._children_cache[parent] = []
                    self._children_cache[parent].append(msg['uuid'])
            self._loaded = True

    def get_message(self, uuid):
        """Get message with lazy loading"""
        self._ensure_loaded()
        return self._messages_cache.get(uuid)
```

### Index-Based Lookups

```python
class IndexedDAG(MessageDAG):
    """DAG with multiple indexes for fast lookups"""

    def __init__(self, messages):
        super().__init__(messages)
        self.build_indexes()

    def build_indexes(self):
        """Build additional indexes for performance"""
        self.by_type = {}
        self.by_session = {}
        self.by_timestamp = []

        for msg in self.messages_by_uuid.values():
            # Index by type
            msg_type = msg.get('type')
            if msg_type not in self.by_type:
                self.by_type[msg_type] = []
            self.by_type[msg_type].append(msg['uuid'])

            # Index by session
            session = msg.get('sessionId')
            if session:
                if session not in self.by_session:
                    self.by_session[session] = []
                self.by_session[session].append(msg['uuid'])

            # Index by timestamp
            timestamp = msg.get('timestamp')
            if timestamp:
                self.by_timestamp.append((timestamp, msg['uuid']))

        # Sort timestamp index
        self.by_timestamp.sort()
```

## Key Takeaways

1. **DAG structure is fundamental**: All parsing must respect parent-child relationships
2. **Orphans are roots**: Messages with missing parents start new trees
3. **File position matters**: Later children represent active branches
4. **Cycles shouldn't exist**: But implement detection for safety
5. **Multiple traversal strategies**: Choose based on use case
6. **Sidechains complicate traversal**: Filter or handle separately
7. **Performance matters**: Use appropriate data structures and caching