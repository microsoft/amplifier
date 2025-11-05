# Content Loader Module

A self-contained module for loading content from configured directories. This module scans directories for text-based content files and provides a unified interface for accessing them.

## Purpose

Provides a generic, reusable way to load content from filesystem directories. Designed to be simple, reliable, and easy to integrate with various content processing pipelines.

## Contract Specification

### Inputs

- **Environment Variable**: `AMPLIFIER_CONTENT_DIRS` - Comma-separated list of directory paths
- **Alternative**: Pass `content_dirs` list directly to `ContentLoader` constructor

### Outputs

- **ContentItem**: Standardized content object with:
  - `content_id`: Unique 16-character hash identifier
  - `title`: Extracted or generated title
  - `content`: The actual text content
  - `source_path`: Absolute path to source file
  - `format`: File format ('md', 'txt', 'json')
  - `metadata`: Additional metadata (from JSON files)

### Side Effects

- Reads files from filesystem
- Logs warnings for inaccessible files
- No files are written or modified

## Public Interface

```python
from amplifier.content_loader import ContentLoader, ContentItem

# Initialize loader
loader = ContentLoader()  # Uses AMPLIFIER_CONTENT_DIRS env var
# OR
loader = ContentLoader(content_dirs=["/path/to/content", "/another/path"])

# Load all content
for item in loader.load_all():
    print(f"{item.title}: {item.content_id}")

# Search content
for item in loader.search("keyword"):
    print(f"Found in: {item.title}")

# Get specific item
item = loader.get_by_id("abc123def456")
```

## Supported File Formats

- **`.md`** - Markdown files (extracts H1 for title)
- **`.txt`** - Plain text files (uses filename for title)
- **`.json`** - JSON files (expects 'content' field, optional 'title' field)

## Configuration

Set the `AMPLIFIER_CONTENT_DIRS` environment variable:

```bash
export AMPLIFIER_CONTENT_DIRS="/home/user/content,/data/articles"
```

Or configure programmatically:

```python
loader = ContentLoader(content_dirs=["/path/to/content"])
```

## Error Handling

- **Invalid directories**: Logged as warning, skipped
- **Unreadable files**: Logged as warning, skipped
- **Invalid JSON**: Logged as warning, file skipped
- **No directories configured**: Warning logged, empty iterator returned

## Performance Characteristics

- **Lazy loading**: Files are loaded on-demand during iteration
- **Memory efficient**: Uses generators, doesn't load all content at once
- **I/O bound**: Performance depends on filesystem speed
- **No caching**: Each iteration reads files fresh from disk

## Testing

```python
# Create test content
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as tmpdir:
    # Create test files
    test_md = Path(tmpdir) / "test.md"
    test_md.write_text("# Test Title\n\nTest content")
    
    # Test loading
    loader = ContentLoader(content_dirs=[tmpdir])
    items = list(loader.load_all())
    assert len(items) == 1
    assert items[0].title == "Test Title"
```

## Regeneration Specification

This module can be regenerated from this specification alone. Key invariants:

- **Public API**: `ContentLoader` class with `load_all()`, `search()`, `get_by_id()` methods
- **Data structure**: `ContentItem` dataclass with specified fields
- **Behavior**: Skip invalid files with warnings, support three file formats
- **Configuration**: Environment variable or constructor parameter

## Implementation Notes

- Uses SHA256 hash (truncated to 16 chars) for content IDs
- Title extraction: First H1 for markdown, filename for others
- JSON files can contain arbitrary metadata beyond content/title
- All file I/O uses UTF-8 encoding
- Recursive directory scanning with `rglob('*')`