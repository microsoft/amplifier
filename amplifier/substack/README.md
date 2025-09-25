# Substack Integration Module

This module provides tools for extracting and processing Substack articles through Amplifier's knowledge mining system.

## Components

### `extractor.py`
- Extracts articles from any Substack publication
- Handles pagination to get all articles
- Saves articles in markdown format

### `process_articles.py`
- Processes extracted articles through Amplifier's knowledge mining
- Extracts concepts, insights, and relationships
- Uses Claude Code SDK for AI-powered extraction

### `integrate.py`
- Integrates extracted knowledge into visualization format
- Formats data for the stellar knowledge visualization
- Creates JSON output for web interface

### `constellation.py`
- Original knowledge constellation visualization generator
- Creates interactive HTML visualizations

## Usage

```python
# Extract articles from Substack
from amplifier.substack import SubstackExtractor

extractor = SubstackExtractor("https://michaeljjabbour.substack.com/")
articles = extractor.extract_all_articles()
extractor.save_articles("data/articles/raw")

# Process through knowledge mining
from amplifier.substack.process_articles import process_articles
knowledge_graph = process_articles()

# Integrate for visualization
from amplifier.substack.integrate import integrate_knowledge
integrate_knowledge()
```

## Output

- Articles saved to: `data/articles/raw/`
- Knowledge graph: `data/substack_knowledge_graph.json`
- Visualization: `data/stellar_knowledge.html`