# Path Configuration Module

## Purpose

Central path configuration and resolution for the Amplifier project. This module is a self-contained "brick" that provides consistent path resolution and directory management across the entire system.

## Contract

### Inputs

- `AMPLIFIER_DATA_DIR`: Environment variable for data directory location (optional)
- `AMPLIFIER_CONTENT_DIRS`: Environment variable for content directories (optional, comma-separated)
- `repo_root`: Repository root directory for relative path resolution (optional)

### Outputs

- `Path` objects: Absolute, resolved paths for all directories
- Auto-created directory structure when accessed

### Side Effects

- Creates directories on disk when `ensure_data_dirs()` is called (automatic on init)
- Reads environment variables on initialization

### Dependencies

- `pathlib` (standard library)
- `os` (standard library)

## Public Interface

```python
from amplifier.config import paths

# Access pre-configured paths
data_dir = paths.data_dir           # Path to data directory
content_dirs = paths.content_dirs   # List of content directory Paths

# Resolve any path string
absolute_path = paths.resolve_path("~/my/path")
absolute_path = paths.resolve_path("relative/path")
absolute_path = paths.resolve_path("/absolute/path")

# Get existing content directories
existing_dirs = paths.get_all_content_paths()

# Ensure all directories exist
paths.ensure_data_dirs()
```

## Directory Structure

The module automatically creates the following directory structure:

```
${AMPLIFIER_DATA_DIR}/
├── knowledge/      # Knowledge graphs and extracted data
├── indexes/        # Search indexes
├── state/          # Application state
├── memories/       # Memory system storage
└── cache/          # Temporary cache data

```

## Environment Variables

| Variable                 | Default         | Description                                         |
| ------------------------ | --------------- | --------------------------------------------------- |
| `AMPLIFIER_DATA_DIR`     | `.data`         | Main data directory for all application data        |
| `AMPLIFIER_CONTENT_DIRS` | `.data/content` | Comma-separated list of content directories to scan |

## Path Resolution Rules

1. **Home directory paths** (`~/...`) are expanded to absolute paths
2. **Absolute paths** (`/...`) are used as-is
3. **Relative paths** are resolved from the repository root

## Usage Examples

### Basic Usage

```python
from amplifier.config import paths

# Access data directory
knowledge_file = paths.data_dir / "knowledge" / "graph.json"

# Work with content directories
for content_dir in paths.content_dirs:
    print(f"Scanning {content_dir}")

# Save to content directory
article_path = paths.content_dirs[0] / "my-article.md"
```

### Custom Configuration

```python
from amplifier.config import PathConfig

# Create custom configuration with different repo root
custom_paths = PathConfig(repo_root="/path/to/repo")

# All paths will be resolved relative to this root
data_dir = custom_paths.data_dir
```

### Environment Variable Configuration

```bash
# Set custom paths via environment
export AMPLIFIER_DATA_DIR="~/amplifier"
export AMPLIFIER_CONTENT_DIRS=".data/content,~/amplifier/content"

# Run application - paths will use these values
python -m amplifier.main
```

## Design Principles

This module follows the "bricks and studs" philosophy:

- **Self-contained**: All path logic is contained within this module
- **Clear contract**: Well-defined inputs, outputs, and behavior
- **Regeneratable**: Can be rebuilt from this specification without breaking other modules
- **Minimal dependencies**: Only uses standard library
- **Single responsibility**: Only handles path configuration and resolution

## Testing

The module is designed to be easily testable:

```python
# Test with mock environment
import os
os.environ["AMPLIFIER_DATA_DIR"] = "/tmp/test-data"

from amplifier.config import PathConfig
test_paths = PathConfig()
assert test_paths.data_dir == Path("/tmp/test-data")
```

## Migration from Legacy Code

This module provides backward compatibility with code that uses `.data` as the default data directory. Simply import and use:

```python
# Old code
data_path = Path(".data") / "knowledge" / "file.json"

# New code (automatic)
from amplifier.config import paths
data_path = paths.data_dir / "knowledge" / "file.json"
```

The paths will automatically resolve to the same location if `AMPLIFIER_DATA_DIR` is not set.
