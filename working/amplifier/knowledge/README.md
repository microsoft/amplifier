# Knowledge Graph System

A modular graph-based knowledge synthesis system that transforms extracted knowledge into an explorable, queryable graph structure.

## Overview

This system builds on top of the knowledge extraction pipeline to create a NetworkX-based knowledge graph that enables:
- **Semantic search** - Find concepts using natural language
- **Path finding** - Discover connections between ideas
- **Tension detection** - Find productive contradictions
- **Interactive visualization** - Explore knowledge visually
- **Incremental updates** - Keep the graph current

## Architecture

```
knowledge/
├── graph_builder.py      # Core graph construction from extractions
├── graph_search.py       # Semantic search interface
├── tension_detector.py   # Productive contradiction finder
├── graph_updater.py      # Incremental update system
└── graph_visualizer.py   # Interactive HTML visualization
```

Each module is a self-contained "brick" (~150 lines) following ruthless simplicity principles.

## Quick Start

```bash
# Build initial graph from extractions
make knowledge-graph-build

# Search for concepts
make knowledge-graph-search Q="AI agents"

# Find tensions (productive contradictions)
make knowledge-graph-tensions

# Create interactive visualization
make knowledge-graph-viz NODES=100
```

## Modules

### graph_builder.py
**Purpose**: Builds NetworkX MultiDiGraph from knowledge extractions

**Key Features**:
- Entity resolution (merges similar concepts)
- Co-occurrence edges for concepts in same article
- Source attribution tracking
- Export to GEXF/GraphML formats

**Usage**:
```python
from amplifier.knowledge.graph_builder import GraphBuilder

gb = GraphBuilder()
extractions = gb.load_extractions()
graph = gb.build_graph()
gb.export_gexf(".data/knowledge/graph.gexf")
```

### graph_search.py
**Purpose**: Semantic search interface for Claude Code

**Key Features**:
- Fuzzy concept matching with difflib
- Shortest path finding between concepts
- N-hop neighborhood exploration
- PageRank-based result ranking
- Natural language query interface

**Usage**:
```python
from amplifier.knowledge.graph_search import GraphSearch

search = GraphSearch()
results = search.query("what relates to Claude Code?")
path = search.find_path("AI Agents", "Knowledge Graph")
neighbors = search.get_neighborhood("MCP", hops=2)
```

### tension_detector.py
**Purpose**: Finds productive contradictions in knowledge

**Key Features**:
- Detects opposing predicates (enables vs prevents)
- Finds conflicting statements from different sources
- Scores tension productivity
- Preserves source attribution

**Philosophy**: Tensions are first-class citizens that generate insights through productive friction.

**Usage**:
```python
from amplifier.knowledge.tension_detector import TensionDetector

detector = TensionDetector()
tensions = detector.get_all_tensions()
# Returns list of tensions with productivity scores
```

### graph_updater.py
**Purpose**: Incrementally updates graph with new knowledge

**Key Features**:
- Append-only approach (never deletes)
- Entity resolution for new concepts
- Temporal tracking (created_at, updated_at)
- Idempotent operations
- State persistence

**Usage**:
```python
from amplifier.knowledge.graph_updater import GraphUpdater

updater = GraphUpdater()
stats = updater.update()  # Only processes new extractions
```

### graph_visualizer.py
**Purpose**: Creates interactive HTML visualizations

**Key Features**:
- PyVis force-directed layout
- Node sizing by importance (PageRank)
- Community detection coloring
- Interactive controls (zoom, pan, search)
- Standalone HTML (no server required)

**Usage**:
```python
from amplifier.knowledge.graph_visualizer import GraphVisualizer

viz = GraphVisualizer()
viz.create_visualization(
    output_path=".data/knowledge/graph.html",
    max_nodes=100,
    threshold=0.5
)
```

## Make Commands

### Core Operations
```bash
# Build/rebuild graph from all extractions
make knowledge-graph-build

# Incremental update with new extractions
make knowledge-graph-update

# Show graph statistics
make knowledge-graph-stats
```

### Query Operations
```bash
# Semantic search
make knowledge-graph-search Q="your query"

# Find path between concepts
make knowledge-graph-path FROM="concept1" TO="concept2"

# Explore concept neighborhood
make knowledge-graph-neighbors CONCEPT="AI" HOPS=2
```

### Analysis Operations
```bash
# Find productive tensions
make knowledge-graph-tensions TOP=10

# Create visualization
make knowledge-graph-viz NODES=50

# Export for external tools
make knowledge-graph-export FORMAT=gexf
```

## Data Flow

```
1. Extractions (JSONL) → graph_builder → NetworkX Graph
2. Graph → graph_search → Semantic Queries
3. Graph → tension_detector → Productive Contradictions
4. New Extractions → graph_updater → Updated Graph
5. Graph → graph_visualizer → Interactive HTML
```

## Philosophy

Following the project's **ruthless simplicity** principles:
- **No unnecessary abstractions** - Direct NetworkX usage
- **Modular bricks** - Each module is self-contained
- **Clear contracts** - Simple input/output interfaces
- **Append-only** - Never lose data, only add
- **Tensions as features** - Contradictions generate insights

## Performance

- **Graph Build**: ~2 seconds for 200 articles
- **Semantic Search**: <100ms per query
- **Tension Detection**: ~1 second for full analysis
- **Incremental Update**: <500ms per article
- **Visualization**: ~3 seconds to generate HTML

## Current Statistics

With 257 processed articles:
- **3,587 nodes** (concepts, entities, sources)
- **15,018 edges** (relationships, co-occurrences)
- **49 productive tensions** discovered
- **Average tension productivity**: 0.934

## Integration with Claude Code

The system is designed for programmatic use by Claude Code:

```python
# Claude Code can query the knowledge graph
from amplifier.knowledge.graph_search import GraphSearch

search = GraphSearch()
# Natural language queries
insights = search.query("what are the key patterns in AI development?")

# Find connections
path = search.find_path("current problem", "potential solution")

# Explore related concepts
context = search.get_neighborhood("main topic", hops=3)
```

## Future Enhancements

Potential additions while maintaining simplicity:
- Vector embeddings for semantic similarity
- Temporal evolution tracking
- Multi-perspective graph layers
- Confidence scoring on edges
- Export to Neo4j for scale

## Troubleshooting

### "No extractions found"
Run `make knowledge-sync` first to extract knowledge from articles.

### "Graph too large for visualization"
Use `NODES` parameter to limit: `make knowledge-graph-viz NODES=50`

### "Module not found"
Ensure you're in the project root and virtual environment is activated.

## Contributing

When adding features:
1. Keep modules under 200 lines
2. No unnecessary abstractions
3. Direct, obvious code paths
4. Document the "brick" contract
5. Ensure compatibility with existing modules