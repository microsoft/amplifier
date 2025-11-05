# Knowledge Synthesis Path Configuration

The knowledge synthesis tools have been updated to use the centralized path configuration system.

## Key Changes

### 1. Centralized Path Management
- All paths now use `amplifier.config.paths` module
- No more hardcoded `.data` references
- Configurable via environment variables

### 2. Multi-Directory Content Scanning
- Scans ALL configured content directories
- Looks for content files in configured directories
- Tracks source directory for each file in metadata

### 3. Environment Variables
```bash
# Set custom data directory (default: .data)
export AMPLIFIER_DATA_DIR="~/.amplifier"

# Set multiple content directories (comma-separated, default: .)
export AMPLIFIER_CONTENT_DIRS="., ~/repos/external-content, /shared/team/content"
```

### 4. Storage Locations
- **Extractions**: `{AMPLIFIER_DATA_DIR}/knowledge/extractions.jsonl`
- **Events**: `{AMPLIFIER_DATA_DIR}/knowledge/events.jsonl`
- **Synthesis**: `{AMPLIFIER_DATA_DIR}/knowledge/synthesis.json`

### 5. Content Discovery
The sync command now:
1. Iterates through all configured content directories
2. Looks for content files (markdown, text, etc.) in each directory
3. Tracks which content directory each file came from
4. Stores this provenance in the extraction metadata

## Usage Examples

```bash
# Use default configuration
python -m amplifier.knowledge_synthesis.cli sync

# Configure custom paths
export AMPLIFIER_DATA_DIR="~/.amplifier"
export AMPLIFIER_CONTENT_DIRS="~/content, ~/repos/articles, /shared/team"
python -m amplifier.knowledge_synthesis.cli sync

# View extracted knowledge
python -m amplifier.knowledge_synthesis.cli stats
python -m amplifier.knowledge_synthesis.cli search "AI"
```

## Benefits

1. **Centralized Configuration**: All path logic in one place
2. **Multi-Source Support**: Scan content from multiple locations
3. **Clean Separation**: Data storage separate from content sources
4. **Backward Compatible**: Still works with default `.data` directory
5. **Provenance Tracking**: Know where each piece of knowledge came from