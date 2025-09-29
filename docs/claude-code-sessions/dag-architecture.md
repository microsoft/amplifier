# Message DAG Architecture Specification

## Structure Definition

Claude Code messages form a Directed Acyclic Graph (DAG) with the following properties:

### Core Components
- `uuid`: Unique message identifier
- `parentUuid`: Reference to parent message (optional)
- `timestamp`: Message creation time
- `sessionId`: Session grouping identifier

### Graph Properties
- Directed edges flow from parent to child
- No cycles exist (acyclic constraint)
- Multiple roots permitted
- Branches represent conversation alternatives

### Visual Structure

```
Root (uuid: msg-001, parentUuid: null)
├── Response (uuid: msg-002, parentUuid: msg-001)
│   ├── Continue (uuid: msg-003, parentUuid: msg-002) [ACTIVE]
│   │   └── Reply (uuid: msg-004, parentUuid: msg-003)
│   └── Edit (uuid: msg-005, parentUuid: msg-002) [ABANDONED]
│       └── Alt Reply (uuid: msg-006, parentUuid: msg-005)
└── Retry (uuid: msg-007, parentUuid: msg-001) [ABANDONED]
```

## DAG Patterns

### Linear Conversation Pattern

Sequential message flow without branches:

```python
def is_linear(messages):
    """Determine if conversation has no branches"""
    parent_counts = {}
    for msg in messages:
        parent = msg.get('parentUuid')
        if parent:
            parent_counts[parent] = parent_counts.get(parent, 0) + 1
    return all(count == 1 for count in parent_counts.values())
```

### Branch Point Identification

Messages with multiple children create branches:

```python
def identify_branches(messages):
    """Find branch points in conversation"""
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
                'count': len(children)
            })
    return branch_points
```

### Root Message Identification

Messages without parents or with non-existent parents are roots:

```python
def find_roots(messages):
    """Identify all root messages including orphans"""
    messages_by_uuid = {msg['uuid']: msg for msg in messages}
    roots = []

    for msg in messages:
        parent_uuid = msg.get('parentUuid')
        if not parent_uuid:
            roots.append({'uuid': msg['uuid'], 'type': 'explicit'})
        elif parent_uuid not in messages_by_uuid:
            roots.append({'uuid': msg['uuid'], 'type': 'orphan'})

    return roots
```

### Active Branch Determination

File position determines active vs abandoned branches:

```python
def determine_active(messages):
    """Identify active branches by file position"""
    children_by_parent = {}
    message_positions = {msg['uuid']: i for i, msg in enumerate(messages)}

    for msg in messages:
        parent = msg.get('parentUuid')
        if parent:
            if parent not in children_by_parent:
                children_by_parent[parent] = []
            children_by_parent[parent].append(msg['uuid'])

    branch_status = {}
    for parent, children in children_by_parent.items():
        if len(children) > 1:
            children.sort(key=lambda x: message_positions[x])
            for i, child in enumerate(children):
                branch_status[child] = 'active' if i == len(children) - 1 else 'abandoned'

    return branch_status
```

## DAG Construction

### Complete DAG Implementation

```python
class MessageDAG:
    def __init__(self, messages):
        self.messages_by_uuid = {msg['uuid']: msg for msg in messages}
        self.children_by_parent = {}
        self.roots = []
        self.orphans = []
        self.build(messages)

    def build(self, messages):
        """Construct DAG structure"""
        for msg in messages:
            uuid = msg['uuid']
            parent_uuid = msg.get('parentUuid')

            if not parent_uuid:
                self.roots.append(uuid)
            elif parent_uuid not in self.messages_by_uuid:
                self.orphans.append(uuid)
                self.roots.append(uuid)
            else:
                if parent_uuid not in self.children_by_parent:
                    self.children_by_parent[parent_uuid] = []
                self.children_by_parent[parent_uuid].append(uuid)

    def get_children(self, uuid):
        """Get immediate children"""
        return self.children_by_parent.get(uuid, [])

    def get_descendants(self, uuid):
        """Get all descendants"""
        descendants = []
        queue = [uuid]
        while queue:
            current = queue.pop(0)
            children = self.get_children(current)
            descendants.extend(children)
            queue.extend(children)
        return descendants

    def get_ancestors(self, uuid):
        """Get all ancestors"""
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
```

## Traversal Methods

### Depth-First Traversal

```python
def depth_first(dag, start_uuid=None):
    """DFS traversal from start or all roots"""
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

### Breadth-First Traversal

```python
def breadth_first(dag):
    """BFS traversal from all roots"""
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

### Active Path Traversal

```python
def traverse_active(dag, branch_status):
    """Follow only active conversation paths"""
    visited = set()
    active_path = []

    def follow(uuid, depth=0):
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
            active_child = None
            for child in children:
                if branch_status.get(child) == 'active':
                    active_child = child
                    break
            if not active_child:
                active_child = children[-1]
            follow(active_child, depth + 1)

    for root in dag.roots:
        follow(root)

    return active_path
```

## Cycle Detection

### Implementation

```python
def detect_cycles(messages):
    """Detect cycles in DAG (should not exist)"""
    graph = {}

    for msg in messages:
        uuid = msg['uuid']
        parent = msg.get('parentUuid')
        if uuid not in graph:
            graph[uuid] = []
        if parent:
            if parent not in graph:
                graph[parent] = []
            graph[parent].append(uuid)

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    cycles = []

    def dfs(node, path):
        color[node] = GRAY
        path.append(node)

        for neighbor in graph.get(node, []):
            if color[neighbor] == GRAY:
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

### All Paths Extraction

```python
def extract_paths(dag):
    """Extract all paths from roots to leaves"""
    paths = []

    def find_paths(uuid, current_path):
        current_path = current_path + [uuid]
        children = dag.get_children(uuid)

        if not children:
            paths.append(current_path)
        else:
            for child in children:
                find_paths(child, current_path)

    for root in dag.roots:
        find_paths(root, [])

    return paths
```

### Longest Path Identification

```python
def find_longest(dag):
    """Find longest path in DAG"""
    all_paths = extract_paths(dag)
    if not all_paths:
        return []
    return max(all_paths, key=len)
```

## Sidechain Integration

### Sidechain-Aware DAG

```python
class SidechainDAG(MessageDAG):
    def __init__(self, messages):
        super().__init__(messages)
        self.sidechains = self.identify_sidechains()

    def identify_sidechains(self):
        """Identify sidechain boundaries"""
        sidechains = []
        current = None

        for msg in self.messages_by_uuid.values():
            is_sidechain = msg.get('isSidechain', False)

            if is_sidechain:
                if not current:
                    current = {
                        'start': msg['uuid'],
                        'messages': [msg['uuid']]
                    }
                else:
                    current['messages'].append(msg['uuid'])
            else:
                if current:
                    current['end'] = current['messages'][-1]
                    sidechains.append(current)
                    current = None

        return sidechains

    def get_main_thread(self):
        """Extract main conversation thread"""
        main_thread = []
        for uuid, msg in self.messages_by_uuid.items():
            if not msg.get('isSidechain', False):
                main_thread.append(uuid)
        return main_thread
```

## Visualization Formats

### Graphviz DOT Format

```python
def to_graphviz(dag):
    """Convert DAG to Graphviz DOT format"""
    lines = ['digraph conversation {', '  rankdir=TB;']

    for uuid, msg in dag.messages_by_uuid.items():
        msg_type = msg.get('type', 'unknown')
        color = {
            'user': 'lightblue',
            'assistant': 'lightgreen',
            'system': 'lightgray'
        }.get(msg_type, 'white')
        lines.append(f'  "{uuid}" [label="{msg_type}", fillcolor={color}, style=filled];')

    for parent, children in dag.children_by_parent.items():
        for child in children:
            lines.append(f'  "{parent}" -> "{child}";')

    lines.append('}')
    return '\n'.join(lines)
```

### ASCII Tree Format

```python
def print_tree(dag, uuid=None, prefix="", is_last=True):
    """Print DAG as ASCII tree"""
    if uuid is None:
        for i, root in enumerate(dag.roots):
            is_last = (i == len(dag.roots) - 1)
            print_tree(dag, root, "", is_last)
        return

    msg = dag.messages_by_uuid.get(uuid, {})
    msg_type = msg.get('type', 'unknown')
    connector = "└── " if is_last else "├── "

    print(f"{prefix}{connector}{msg_type} ({uuid[:8]}...)")

    children = dag.get_children(uuid)
    extension = "    " if is_last else "│   "

    for i, child in enumerate(children):
        is_last_child = (i == len(children) - 1)
        print_tree(dag, child, prefix + extension, is_last_child)
```

## Performance Optimizations

### Lazy Loading

```python
class LazyDAG:
    """DAG with lazy evaluation"""

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

### Indexed Lookups

```python
class IndexedDAG(MessageDAG):
    """DAG with multiple indexes"""

    def __init__(self, messages):
        super().__init__(messages)
        self.build_indexes()

    def build_indexes(self):
        """Build performance indexes"""
        self.by_type = {}
        self.by_session = {}
        self.by_timestamp = []

        for msg in self.messages_by_uuid.values():
            msg_type = msg.get('type')
            if msg_type not in self.by_type:
                self.by_type[msg_type] = []
            self.by_type[msg_type].append(msg['uuid'])

            session = msg.get('sessionId')
            if session:
                if session not in self.by_session:
                    self.by_session[session] = []
                self.by_session[session].append(msg['uuid'])

            timestamp = msg.get('timestamp')
            if timestamp:
                self.by_timestamp.append((timestamp, msg['uuid']))

        self.by_timestamp.sort()
```

## Key Specifications

- DAG structure enforced: No cycles permitted
- Orphaned messages treated as roots
- File position determines active branches
- Multiple traversal strategies supported
- Sidechains identified by `isSidechain` flag
- Performance optimizations for large sessions