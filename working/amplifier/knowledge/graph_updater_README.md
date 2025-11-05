# Graph Updater Module

## Purpose
Incrementally update the knowledge graph with new extractions without rebuilding from scratch.

## Contract

### Inputs
- `extractions_path`: Path to JSONL file with knowledge extractions
- `graph_path`: Path to persist graph (GEXF format)
- `state_path`: Path to persist processing state (JSON)

### Outputs
- Updated graph file (GEXF)
- State file tracking processed sources
- Summary dict with update statistics

### Side Effects
- Writes graph to disk
- Writes state to disk
- Updates graph metrics (centrality, PageRank)

### Dependencies
- networkx: Graph operations
- graph_builder: Entity normalization

## Public Interface

```python
from amplifier.knowledge.graph_updater import GraphUpdater

# Initialize updater
updater = GraphUpdater(
    graph_path=Path(".data/knowledge/graph.gexf"),
    state_path=Path(".data/knowledge/graph_state.json")
)

# Run incremental update
summary = updater.update(Path(".data/knowledge/extractions.jsonl"))

# Summary contains:
# - new_extractions: count of new sources processed
# - nodes_added: new nodes added to graph
# - edges_added: new edges added to graph
# - nodes_after/edges_after: final counts
```

## Key Features

1. **Append-only**: Never deletes data, only adds or marks obsolete
2. **Idempotent**: Safe to run multiple times on same data
3. **Entity Resolution**: Normalizes and merges duplicate concepts
4. **Temporal Tracking**: Records when concepts were added/updated
5. **State Persistence**: Tracks which sources have been processed

## CLI Usage

```bash
# Basic update
python -m amplifier.knowledge.graph_updater

# Custom paths
python -m amplifier.knowledge.graph_updater \
    --input extractions.jsonl \
    --graph my_graph.gexf \
    --state my_state.json
```

## Integration with Other Modules

- **graph_builder.py**: Uses for entity normalization
- **graph_search.py**: Can search the updated graph
- **tension_detector.py**: Can analyze tensions in updated graph

## Design Principles

- Simple state tracking using JSON
- Clear separation between new and existing data
- Preserves all historical information
- No complex migrations or schema changes