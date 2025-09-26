# CCSDK Tool Templates

This directory contains templates for creating ready-to-use CCSDK tools, based upon learnings and best practices that embody our philosophy of ruthless simplicity and modular design.

## Quick Start

To create a new tool from the template:

```bash
# 1. Copy the template
cp amplifier/ccsdk_toolkit/templates/tool_template.py \
   ai_working/my_new_tool/cli.py

# 2. Replace placeholders
# [TOOL_NAME] -> Your tool name
# [ONE_LINE_PURPOSE] -> Brief description
# [EXPECTED_INPUTS] -> What it expects
# [EXPECTED_OUTPUTS] -> What it produces
# [HOW_IT_FAILS] -> Failure modes

# 3. Remove or update sections to fit your needs

# 4. Implement your logic in process_item()

# 5. Test it
python ai_working/my_new_tool/cli.py input_dir/

# 6. Add to Makefile if permanent
```

## Philosophy

### Ruthless Simplicity

- Direct solutions without unnecessary abstractions
- Trust standard libraries (use `Path.glob()` not custom walking)
- Prefer 50 lines that work over 200 with "features"

### Modular Design (Bricks & Studs)

- **Brick**: Core logic in `ToolProcessor` class (regeneratable)
- **Stud**: CLI interface via `@click.command()` (stable connection)
- Clear separation allows AI to regenerate core without breaking interface

### Fail Fast and Loud

```python
if not processor.validate_inputs(files, min_files):
    logger.error("Descriptive error message")
    sys.exit(1)
```

## Key Features

### 1. Recursive File Discovery

```python
# Default pattern finds ALL nested files
files = list(input_path.glob("**/*.md"))  # NOT "*.md"
```

### 2. Input Validation

```python
# Minimum file check prevents silent failures
if len(items) < min_required:
    logger.error(f"Need at least {min_required} items, found {len(items)}")
    return False
```

### 3. Progress Visibility

```python
# Users see what's happening
logger.info(f"[{i}/{len(files)}]: Processing {file.name}")
```

### 4. Incremental Saving

```python
# Save after each item - interruption safe
self.state["processed"].append(str(item))
self._save_state()
```

### 5. Resume Capability

```python
# Skip already processed items
if str(item) in self.state["processed"]:
    logger.info(f"Skipping already processed: {item}")
    return {}
```

### 6. Graceful Degradation

```python
# Continue on partial failures
except Exception as e:
    logger.error(f"Failed to process {file}: {e}")
    continue  # Don't stop everything
```

### 7. Defensive LLM Parsing

```python
# Handle any LLM response format
result = parse_llm_json(response.content, default={})
```

### 8. Cloud Sync Aware I/O

```python
# Automatic retry for OneDrive/Dropbox issues
write_json_with_retry(data, filepath)
```

## Common Patterns

### LLM Processing Pattern

```python
async with ClaudeSession(options) as session:
    response = await session.query(prompt)
    result = parse_llm_json(response.content, default={})
```

### Batch Processing Pattern

```python
for i, item in enumerate(items, 1):
    logger.info(f"[{i}/{len(items)}]: {item.name}")
    result = await process(item)
    save_progress()
```

### Parallel Processing Pattern

```python
tasks = [process_item(item) for item in items]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

## Production Checklist

Before deploying a tool:

- [ ] Replaces ALL template placeholders
- [ ] Uses recursive glob (`**/*.ext`) for file discovery
- [ ] Validates minimum inputs before processing
- [ ] Shows clear progress to user
- [ ] Saves state incrementally
- [ ] Handles partial failures gracefully
- [ ] Uses defensive utilities from toolkit
- [ ] Includes meaningful error messages
- [ ] Has resume capability
- [ ] Follows philosophy (simple, direct, clear)

## Directory Structure

Production tools should consider following this structure, unless simplicity, complexity, or modular design philosophy dictates otherwise:

```
ai_working/tool_name/        # Or amplifier/tools/ for permanent
├── __init__.py              # Exports public interface
├── cli.py                   # CLI wrapper (the "stud")
├── core.py                  # Core logic (the "brick")
├── README.md                # Tool specification
└── test_tool.py            # Basic tests
```

## Testing

Minimal tests to include:

```python
def test_recursive_discovery():
    """Ensure finds nested files."""

def test_minimum_validation():
    """Ensure fails with too few inputs."""

def test_resume_capability():
    """Ensure skips processed items."""
```

## Remember

> "It's easier to add complexity later than to remove it"
>
> "Code you don't write has no bugs"
>
> "The best code is often the simplest"

This template embodies these principles. Start here, stay simple, evolve only when proven necessary.
