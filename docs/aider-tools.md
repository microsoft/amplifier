# Aider Tools for Amplifier

AI-powered code regeneration tools using [Aider](https://aider.chat/).

## Overview

The Aider tools provide AI-powered module regeneration capabilities, enabling automated code improvements based on different development philosophies.

## Installation

Run the setup script to install Aider in an isolated environment:

```bash
bash scripts/setup-aider.sh
```

This creates a `.aider-venv` virtual environment with Aider installed.

## Configuration

Set your API key for the AI model:

```bash
export ANTHROPIC_API_KEY='your-api-key'
```

## Usage

### Command Line

Regenerate a single module:

```bash
python amplifier/tools/aider_regenerator.py amplifier/some_module.py --philosophy zen
```

Regenerate with a specification:

```bash
python amplifier/tools/aider_regenerator.py amplifier/module.py --spec specs/module_spec.md
```

Batch regeneration:

```bash
python amplifier/tools/aider_regenerator.py amplifier/*.py --philosophy modular
```

### Python API

```python
from pathlib import Path
from amplifier.tools.aider_regenerator import AiderRegenerator

# Initialize regenerator
regenerator = AiderRegenerator()

# Regenerate a module
success = regenerator.regenerate_module(
    module_path=Path("amplifier/my_module.py"),
    philosophy="fractalized",
    auto_commit=False
)

# Batch regeneration
modules = list(Path("amplifier").glob("*.py"))
results = regenerator.batch_regenerate(
    modules,
    philosophy="zen"
)
```

## Development Philosophies

The regenerator supports three philosophies:

### Fractalized Thinking
- Start with the smallest, simplest working piece
- Patiently untangle complexity thread by thread
- Build bridges between simple components
- Let patterns emerge naturally

### Modular Design
- Create self-contained bricks with clear interfaces
- Each brick has one clear responsibility
- Contracts are stable, implementations can change
- Prefer regeneration over patching

### Zen Simplicity
- Ruthless simplicity - remove everything unnecessary
- Direct solutions without unnecessary abstractions
- Trust in emergence from simple components
- Handle only what's needed now

## Options

- `--philosophy`: Choose regeneration philosophy (fractalized, modular, zen)
- `--spec`: Path to specification file
- `--auto-commit`: Automatically commit changes
- `--model`: AI model to use (default: claude-3-5-sonnet)
- `--verbose`: Enable debug output

## Pre-commit Hook (Optional)

To automatically regenerate modified files before commits, create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Auto-regenerate modified Python files

if [ "$AIDER_REGENERATE" = "true" ]; then
    # Get modified Python files
    files=$(git diff --cached --name-only --diff-filter=M | grep '\.py$')

    if [ -n "$files" ]; then
        echo "Regenerating modified Python files..."
        python amplifier/tools/aider_regenerator.py $files \
            --philosophy ${AIDER_PHILOSOPHY:-fractalized} \
            ${AIDER_AUTO_ADD:+--auto-commit}
    fi
fi
```

Then enable with:

```bash
export AIDER_REGENERATE=true
git commit -m "Your message"
```

## Notes

- Aider requires an API key for the chosen AI model
- Regeneration typically takes 30-60 seconds per module
- The tool preserves file structure while improving code quality
- Always review regenerated code before committing