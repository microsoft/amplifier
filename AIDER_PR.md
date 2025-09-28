# Add Aider Tools for AI-Powered Code Regeneration

## Summary

This PR adds standalone Aider tools to Amplifier, enabling AI-powered module regeneration using different development philosophies.

## What's Included

- **`amplifier/tools/aider_regenerator.py`**: Core regeneration tool with support for three philosophies (fractalized, modular, zen)
- **`scripts/setup-aider.sh`**: Installation script for setting up Aider in an isolated environment
- **`docs/aider-tools.md`**: Comprehensive documentation

## Key Features

- **Philosophy-based regeneration**: Choose between fractalized thinking, modular design, or zen simplicity
- **Batch processing**: Regenerate multiple modules at once
- **Specification support**: Regenerate based on explicit specifications
- **Isolated installation**: Aider runs in its own virtual environment to avoid dependency conflicts

## Usage

```bash
# Setup
bash scripts/setup-aider.sh

# Regenerate a module
python amplifier/tools/aider_regenerator.py amplifier/my_module.py --philosophy zen
```

## Why This Matters

AI-powered code regeneration allows for:
- Consistent code quality improvements
- Philosophy-aligned refactoring
- Automated technical debt reduction
- Faster iteration on module design

## Testing

The tool has been tested with:
- Single module regeneration
- Batch processing
- Different philosophy modes
- Error handling (missing files, timeout scenarios)