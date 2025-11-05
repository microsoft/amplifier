# Knowledge System Workflow

## Complete Content Processing Pipeline

### 1. Adding New Content

**Preparing Content:**
1. Place content files (markdown, text, etc.) in your configured content directories
2. Content is automatically discovered during processing
3. Supports any text-based format

### 2. Processing Content

**Single Command (Recommended):**
```bash
make knowledge-update  # Does everything: extract and synthesize
```

**Or Step-by-Step:**
```bash
make knowledge-sync       # Extract knowledge (concepts, relationships, insights)
make knowledge-synthesize # Find cross-content patterns
```

### 3. Using the Knowledge

**Query for Specific Topics:**
```bash
# Human-readable output
make knowledge-query Q="MCP servers"

# JSON output for AI processing
make knowledge-query Q="authentication patterns" FORMAT=json
```

**View Statistics:**
```bash
make knowledge-stats
```

**Export Everything:**
```bash
make knowledge-export FORMAT=json > my_knowledge.json
```

## For AI Assistants (Claude Code)

### Leveraging Knowledge for Development

When working on new features, AI assistants can query the knowledge base to find relevant patterns and insights from your curated content:

```bash
# Example: Building an authentication system
make knowledge-query Q="authentication" FORMAT=json

# The query returns:
# - Concepts with descriptions and importance scores
# - Relationships showing how concepts connect
# - Actionable insights from articles
# - Recurring patterns across content
```

### Knowledge Files

AI assistants can reference these files directly:
- `.data/knowledge/extractions.jsonl` - All extracted knowledge
- `.data/knowledge/synthesis.json` - Cross-content patterns and insights

### Synthesis Intelligence

The synthesis system provides:
- **Entity Resolution** - Identifies same concepts with different names (e.g., "AI" = "AI Agent" = "artificial intelligence")
- **Contradiction Detection** - Finds conflicting advice across content
- **Pattern Emergence** - Discovers recurring themes
- **Meta-Insights** - Insights about insights

## System Architecture

### Modular Components

#### Knowledge Synthesis
```
knowledge_synthesis/
├── extractor.py      # Extracts concepts, relationships, insights
├── store.py          # JSON Lines storage with incremental saves
├── fingerprinter.py  # Semantic fingerprinting for entity resolution
├── stream_reader.py  # Temporal knowledge streaming
├── tension_detector.py # Finds contradictions and tensions
├── synthesizer.py    # Generates cross-content insights
└── cli.py           # Command-line interface
```

#### Knowledge Graph
```
knowledge/
├── graph_builder.py  # Builds NetworkX graph from extractions
├── graph_search.py   # Semantic search with fuzzy matching
├── tension_detector.py # Finds productive contradictions
├── graph_updater.py  # Incremental graph updates
└── graph_visualizer.py # Interactive HTML visualization
```

### Data Flow
1. **Content** → Text files from configured directories
2. **Extraction** → Concepts, relationships, insights, patterns
3. **Fingerprinting** → Semantic hashes for entity resolution
4. **Synthesis** → Cross-content patterns and contradictions
5. **Query** → Search and retrieve relevant knowledge

## Philosophy

The system follows principles of **ruthless simplicity**:
- Single JSONL file for all knowledge (no complex databases)
- Semantic fingerprints instead of entity databases
- Patterns emerge from data, not pre-defined rules
- Each module < 150 lines, regeneratable by AI
- Direct, obvious code paths

## Troubleshooting

### "No Claude Code SDK available"
- Knowledge extraction requires Claude Code environment
- Outside Claude Code, extraction returns empty results

### "Content not found"
```bash
# Ensure content files are in configured directories
# Check AMPLIFIER_CONTENT_DIRS environment variable
```

### Processing Takes Too Long
```bash
# Process in batches
make knowledge-sync-batch N=10  # Process 10 files at a time
```

## Advanced Usage

### Finding Contradictions
The synthesis system automatically detects when content gives conflicting advice:
- Relationship contradictions (X enables Y vs X prevents Y)
- Insight conflicts (do this vs don't do this)
- Pattern tensions (trending up vs trending down)

### Tracking Concept Evolution
The temporal streaming shows how concepts evolve over time as you add more content.

### Building on Knowledge
When the AI queries return relevant patterns, it can:
1. Apply proven approaches from your curated content
2. Avoid known pitfalls mentioned in articles
3. Combine insights from multiple sources
4. Navigate contradictions with awareness

## Maintenance

### Regular Updates
```bash
# Weekly or whenever you add new content
make knowledge-update
```

### Storage
- Content: Configured directories (AMPLIFIER_CONTENT_DIRS)
- Knowledge: `.data/knowledge/` (~10KB per file)
- Synthesis: `.data/knowledge/synthesis.json` (regenerated each run)

### Backup
The JSONL format is version-control friendly:
```bash
git add .data/knowledge/extractions.jsonl
git commit -m "Knowledge snapshot $(date +%Y-%m-%d)"
```

## Knowledge Graph Features

### Building the Graph

After extracting knowledge, build a NetworkX graph for advanced analysis:

```bash
# Initial graph build from all extractions
make knowledge-graph-build

# Or incrementally update with new extractions
make knowledge-graph-update
```

### Semantic Search

Query the graph with natural language:

```bash
# Search for concepts
make knowledge-graph-search Q="AI agent patterns"

# Find paths between concepts
make knowledge-graph-path FROM="Claude Code" TO="Knowledge Graph"

# Explore concept neighborhoods
make knowledge-graph-neighbors CONCEPT="MCP" HOPS=2
```

### Finding Tensions

Discover productive contradictions in your knowledge:

```bash
# Find top 10 tensions (contradictions that generate insights)
make knowledge-graph-tensions

# Or specify how many to show
make knowledge-graph-tensions TOP=20
```

### Interactive Visualization

Create an interactive HTML visualization:

```bash
# Visualize top 50 nodes (default)
make knowledge-graph-viz

# Or specify node count
make knowledge-graph-viz NODES=100

# Opens .data/knowledge/knowledge_graph.html in your browser
```

### Graph Export

Export for external analysis tools:

```bash
# Export as GEXF (for Gephi)
make knowledge-graph-export FORMAT=gexf

# Export as GraphML (for yEd, Cytoscape)
make knowledge-graph-export FORMAT=graphml
```

### Graph Statistics

View graph metrics:

```bash
make knowledge-graph-stats

# Shows:
# - Total nodes and edges
# - Graph density
# - Top concepts by PageRank
# - Number of productive tensions
```

## Performance

- **Extraction**: ~10-30 seconds per file (depends on Claude Code SDK)
- **Synthesis**: ~5 seconds for 100 files
- **Query**: Instant (grep-speed on JSONL)
- **Graph Build**: ~2 seconds for 200 files
- **Graph Search**: <100ms for semantic queries
- **Tension Detection**: ~1 second for full analysis
- **Visualization**: ~3 seconds to generate HTML
- **Incremental**: Saves after each file (Ctrl+C safe)