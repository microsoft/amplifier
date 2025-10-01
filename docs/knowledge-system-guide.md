# Amplifier Knowledge System Guide

## Overview

The Amplifier Knowledge System provides intelligent access to extracted knowledge from AI-First Principles. It includes concepts, patterns, insights, and a comprehensive knowledge graph that can guide development decisions.

## Key Components

### 1. Knowledge Storage
- **Location**: `amplifier/data/knowledge/`
- **Files**:
  - `principles_knowledge.json` - Extracted knowledge data
  - `synthesis_report.md` - Human-readable synthesis report

### 2. Knowledge Access APIs

#### Python API
```python
from amplifier.knowledge.manager import get_knowledge_manager

# Get the singleton manager
manager = get_knowledge_manager()

# Access concepts
concepts = manager.get_concepts()

# Search for specific concepts
results = manager.search_concepts("testing")

# Get recommendations for a context
recs = manager.get_recommendations_for_context("building a RAG system")

# Access patterns and insights
patterns = manager.get_patterns()
insights = manager.get_insights()
```

#### CLI Commands
```bash
# Show system status
amplifier knowledge status

# Search for concepts
amplifier knowledge search "prompt engineering"

# Get recommendations
amplifier knowledge recommend "building an AI testing framework"

# Show patterns
amplifier knowledge patterns

# Show insights
amplifier knowledge insights

# Export knowledge
amplifier knowledge export -o my_knowledge.json

# Reload from disk
amplifier knowledge reload
```

## Available Knowledge

### Extracted Content
- **454 unique concepts** from AI principles
- **8 patterns** with confidence scores
- **8 strategic insights** with recommendations
- **Knowledge graph** with 493 nodes and 814 edges

### Top Concepts
1. **Reasoning** (340 occurrences) - Core to AI decision-making
2. **Evaluation** (188 occurrences) - Quality assurance
3. **Retrieval** (176 occurrences) - RAG and memory systems
4. **Validation** (172 occurrences) - Ensuring correctness
5. **Iteration** (160 occurrences) - Continuous improvement

### Key Patterns
1. **Iterative Refinement** (90% confidence)
   - Continuous improvement through systematic iteration
   - Found in principles: #45, #48, #49, #50, #51, #52, #53, #55

2. **Context Optimization** (95% confidence)
   - Efficient use of limited context windows
   - Found in ALL 11 principles

3. **Agent Orchestration** (85% confidence)
   - Coordinating multiple agents for complex tasks
   - Found in ALL 11 principles

4. **Systematic Evaluation** (90% confidence)
   - Data-driven testing and validation
   - Found in principles: #45, #46, #47, #48, #49, #50, #52, #53, #55

### Strategic Insights

1. **The AI Development Triangle**
   - Balance iteration, context management, and evaluation
   - Implement prompt iteration workflows from day one
   - Build context curation pipelines before scaling

2. **Modular AI System Design**
   - Break complex prompts into specialized agents
   - Implement tool use for external capabilities
   - Use RAG for knowledge-intensive tasks

3. **Adaptive Learning Systems**
   - Implement few-shot learning with dynamic examples
   - Build memory systems for agent state
   - Track and analyze iteration outcomes

4. **Transparent Reasoning Systems**
   - Use chain-of-thought for complex decisions
   - Implement structured prompt patterns
   - Log reasoning traces for debugging

## Usage Examples

### Example 1: Finding Relevant Concepts
```python
from amplifier.knowledge.manager import get_knowledge_manager

manager = get_knowledge_manager()

# Search for testing-related concepts
concepts = manager.search_concepts("test")
for concept in concepts[:5]:
    print(f"{concept['name']}: {concept['frequency']} occurrences")
```

### Example 2: Getting Task Recommendations
```python
# Get recommendations for a specific task
context = "implementing a multi-agent orchestration system"
recommendations = manager.get_recommendations_for_context(context)

for rec in recommendations:
    print(f"{rec['title']}: {', '.join(rec['items'][:3])}")
    print(f"Principles: {rec['principles'][:5]}")
```

### Example 3: Exploring the Knowledge Graph
```python
# Get neighbors of a concept in the graph
loader = manager.loader
neighbors = loader.get_graph_neighbors("pattern:Iterative Refinement")
print(f"Connected to: {neighbors}")
```

### Example 4: Filtering Concepts by Principles
```python
# Get concepts related to specific principles
concepts = manager.get_concepts_for_principles([45, 46, 47])
print(f"Found {len(concepts)} concepts in principles 45-47")
```

## Integration with Other Systems

### With Principles CLI
The knowledge system works seamlessly with the principles CLI:
```bash
# Extract fresh knowledge
amplifier principles extract-knowledge -o data.json -r report.md

# Then use knowledge commands
amplifier knowledge reload
amplifier knowledge status
```

### With Development Workflow
Use knowledge to guide development decisions:

1. **During Planning**: Get recommendations for your task
2. **During Implementation**: Search for relevant patterns
3. **During Review**: Check insights for best practices
4. **During Testing**: Find evaluation strategies

## Updating Knowledge

To update the knowledge base with new principles:

1. Add new principle markdown files to `ai-first-principles/principles/`
2. Re-run knowledge extraction:
   ```bash
   amplifier principles extract-knowledge \
     -o amplifier/data/knowledge/principles_knowledge.json \
     -r amplifier/data/knowledge/synthesis_report.md
   ```
3. Reload in running systems:
   ```bash
   amplifier knowledge reload
   ```

## Architecture

### Singleton Pattern
The `KnowledgeManager` uses a singleton pattern for global access:
```python
# Always returns the same instance
manager = get_knowledge_manager()
```

### Lazy Loading
Knowledge is loaded on first access, not at import time:
- Reduces startup time
- Avoids loading if not needed
- Automatic initialization on first use

### Data Structure
Knowledge is stored as:
```json
{
  "concepts": [...],      // List of concept objects
  "patterns": [...],      // List of pattern objects
  "insights": [...],      // List of insight objects
  "knowledge_graph": {    // Graph adjacency list
    "node_id": ["connected_node1", "connected_node2", ...]
  },
  "statistics": {...}     // Summary statistics
}
```

## Performance Considerations

- **Initial Load**: ~50ms for 454 concepts
- **Search**: O(n) linear search, fast for current size
- **Graph Traversal**: O(1) neighbor lookup
- **Memory Usage**: ~2MB for full knowledge base

## Troubleshooting

### Knowledge Not Loading
```bash
# Check if files exist
ls -la amplifier/data/knowledge/

# Test loading directly
amplifier knowledge status

# Force reload
amplifier knowledge reload
```

### Search Not Finding Results
- Try broader search terms
- Check exact concept names with `amplifier knowledge status`
- Use partial matching (searches are substring-based)

### Recommendations Empty
- Break down complex contexts into simpler terms
- Check that knowledge files are properly loaded
- Verify principle numbers in recommendations

## Future Enhancements

Potential improvements to the knowledge system:

1. **Semantic Search**: Use embeddings for better concept matching
2. **Dynamic Updates**: Auto-reload when principles change
3. **Caching**: Memory-mapped files for faster loads
4. **Visualization**: Interactive knowledge graph explorer
5. **Learning**: Track which recommendations are most useful
6. **Integration**: Connect with code analysis tools