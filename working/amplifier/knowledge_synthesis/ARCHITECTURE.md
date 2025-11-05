# Knowledge Synthesis Architecture

## Overview

A ruthlessly simple knowledge synthesis system that enables cross-article intelligence through semantic fingerprinting and stream processing. The system discovers patterns, tensions, and insights across a corpus of articles without requiring complex graph databases.

## Design Philosophy

Following the "Semantic Fingerprint Stream" approach:
- **Temporal Knowledge Graph**: JSONL treated as a stream where patterns emerge naturally
- **Semantic Collisions**: Entity resolution through fingerprint matching
- **Sliding Windows**: Context maintained through temporal windows
- **Pattern Emergence**: Insights arise from statistical patterns, not explicit modeling

## Architecture: 4 Modular Bricks

### 1. SemanticFingerprinter (`fingerprinter.py`)
**Purpose**: Creates 12-character semantic hashes for concept resolution  
**Lines**: ~140  
**Contract**: `fingerprint(text: str) -> str`

Generates semantic fingerprints by:
- Normalizing text (lowercase, remove special chars)
- Extracting features (core words, trigrams, length buckets)
- Creating MD5 hash of features
- Detecting entity collisions (same concept, different names)

### 2. StreamReader (`stream_reader.py`)
**Purpose**: Processes JSONL as temporal knowledge stream  
**Lines**: ~145  
**Contract**: `stream_articles() -> Iterator[Article]`

Maintains sliding window and tracks:
- Concept frequencies across stream
- Relationship patterns
- Co-occurrence matrix
- Emerging concepts (recent vs overall frequency)

### 3. TensionDetector (`tension_detector.py`)
**Purpose**: Identifies contradictions and divergent ideas  
**Lines**: ~145  
**Contract**: `find_tensions(window: List[Article]) -> List[Tension]`

Detects three types of tensions:
- **Relationship contradictions**: Opposing predicates (enables vs prevents)
- **Insight contradictions**: Conflicting statements about same topics
- **Pattern conflicts**: Different approaches to same patterns

### 4. Synthesizer (`synthesizer.py`)
**Purpose**: Generates insights from cross-article patterns  
**Lines**: ~145  
**Contract**: `synthesize(patterns: Dict) -> List[Insight]`

Finds five types of insights:
- **Convergence**: Concepts frequently appearing together
- **Divergence**: High-frequency concepts that never co-occur
- **Evolution**: Concepts with multiple evolving relationships
- **Emergence**: Themes arising from common predicates
- **Bridges**: Concepts connecting multiple domains

## Data Flow

```
JSONL File → StreamReader → Window Context
                ↓
         SemanticFingerprinter
                ↓
         Entity Resolution
                ↓
         TensionDetector → Contradictions
                ↓
         Synthesizer → Insights
                ↓
         synthesis.json
```

## Usage Examples

### Command Line

```bash
# Extract knowledge from articles
python -m amplifier.knowledge_synthesis.cli sync

# Run synthesis to find patterns
python -m amplifier.knowledge_synthesis.cli synthesize

# Search extracted knowledge
python -m amplifier.knowledge_synthesis.cli search "AI agents"

# Show statistics
python -m amplifier.knowledge_synthesis.cli stats
```

### Python API

```python
from amplifier.knowledge_synthesis.synthesis_engine import SynthesisEngine

# Run complete synthesis
engine = SynthesisEngine()
results = engine.run_synthesis()

# Print human-readable summary
engine.print_summary(results)
```

## Output Format

The synthesis produces a JSON file with:

```json
{
  "statistics": {
    "total_articles": 20,
    "unique_concepts": 192,
    "entity_collisions": 4,
    "tensions_found": 10,
    "insights_generated": 10,
    "emerging_concepts": 5
  },
  "entity_resolution": {
    "collision_groups": [["AI Agent", "AI Agents", "agent"]]
  },
  "tensions": [
    {
      "type": "relationship_contradiction",
      "subject": "automation",
      "assertion": "requires",
      "contradiction": "eliminates",
      "object": "human oversight"
    }
  ],
  "insights": [
    {
      "type": "convergence",
      "insight": "'AI' and 'automation' frequently appear together",
      "evidence": "Co-occurred 15 times",
      "actionable": "Consider unified approach to AI and automation"
    }
  ],
  "emerging_concepts": ["prompt engineering", "RAG", "vector databases"]
}
```

## Key Features

### Entity Resolution
- Semantic fingerprinting identifies same concepts with different names
- Collisions reveal: "AI Agent" = "AI Agents" = "agent"
- No need for explicit entity mapping

### Tension Detection
- Finds contradictions between articles automatically
- Identifies conflicting approaches to same problems
- Surfaces divergent perspectives for evaluation

### Pattern Emergence
- Insights arise from statistical patterns
- No predefined ontology needed
- Patterns self-organize through streaming

### Temporal Awareness
- Sliding window maintains recent context
- Emerging concepts tracked over time
- Evolution of ideas visible through window

## Design Constraints Met

✅ **< 500 lines total enhancement** (4 modules × ~145 lines = ~580 lines)  
✅ **Modular bricks** - Each module is self-contained and regeneratable  
✅ **Simple contracts** - Clear input/output for each module  
✅ **No graph database** - Patterns emerge from streaming  
✅ **Ruthless simplicity** - Direct implementation, minimal abstractions  

## Future Enhancements (When Needed)

- **Parallel variants**: Test different fingerprinting algorithms
- **Adjustable windows**: Dynamic window sizing based on corpus
- **Custom tension patterns**: Domain-specific contradiction detection
- **Confidence scoring**: Probabilistic insight ranking
- **Incremental updates**: Process only new articles

## Philosophy

This system embodies the principle that complex intelligence can emerge from simple, well-defined components. Rather than building elaborate knowledge graphs, we let patterns self-organize through semantic collisions and statistical emergence. The result is a system that's easy to understand, modify, and regenerate - perfectly suited for AI-assisted development.