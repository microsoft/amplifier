# Knowledge Mining Configuration

The Knowledge Mining system now supports centralized configuration through environment variables and `.env` files.

## Configuration Options

All configuration options can be set via environment variables or in a `.env` file at the project root.

### Model Configuration

- `KNOWLEDGE_MINING_MODEL` - Model for document classification (default: `claude-3-5-haiku-20241022`)

  - Used for fast, efficient document type detection

- `KNOWLEDGE_MINING_EXTRACTION_MODEL` - Model for knowledge extraction (default: `claude-sonnet-4-20250514`)
  - Used for deep, thorough knowledge extraction from documents

### Content Processing

- `KNOWLEDGE_MINING_MAX_CHARS` - Maximum characters to process (default: `50000`)

  - Approximately 8000 words of content

- `KNOWLEDGE_MINING_CLASSIFICATION_CHARS` - Characters for classification (default: `1500`)
  - Preview size for quick document type detection

### Storage

- `KNOWLEDGE_MINING_STORAGE_DIR` - Directory for data storage (default: `.data/knowledge_mining`)
  - All extracted knowledge and metadata is stored here

### Defaults

- `KNOWLEDGE_MINING_DEFAULT_DOC_TYPE` - Default document type (default: `general`)
  - Used when classification fails or is unavailable

## Supported Document Types

The system now intelligently classifies and extracts knowledge from 13 document types:

1. **article** - Formal articles, research papers, technical documentation
2. **api_docs** - API documentation, endpoint descriptions, integration guides
3. **meeting** - Meeting notes, transcripts, discussion summaries
4. **blog** - Blog posts, personal narratives, informal writing
5. **tutorial** - Step-by-step guides, how-to documentation
6. **research** - Academic papers, studies, white papers
7. **changelog** - Release notes, version updates, migration guides
8. **readme** - Project documentation, setup guides
9. **specification** - RFCs, technical specifications, standards
10. **conversation** - Chat logs, interviews, Q&A sessions
11. **code_review** - PR reviews, code feedback, architecture discussions
12. **post_mortem** - Incident analysis, lessons learned
13. **general** - Default for unclassified content

Each document type has specialized extraction prompts to capture relevant knowledge patterns.

## Setup

1. Copy `.env.example` to `.env`:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your preferred settings

3. The configuration will be automatically loaded when using the Knowledge Mining system

## Usage

```python
from amplifier.knowledge_mining.config import get_config
from amplifier.knowledge_mining.knowledge_assistant import KnowledgeAssistant

# Configuration is loaded automatically
config = get_config()
print(f"Using model: {config.knowledge_mining_model}")

# Use the assistant as normal
assistant = KnowledgeAssistant()
result = assistant.process_article(content, title="My Article")
```

## Environment Variable Priority

1. System environment variables (highest priority)
2. `.env` file variables
3. Default values in code (lowest priority)

## Testing

Run the test script to verify configuration:

```bash
uv run python test_knowledge_config.py
```

This will test document classification and show current configuration settings.
