# Git Hooks for Amplifier

This directory contains optional git hooks for the Amplifier project.

## Available Hooks

### pre-commit-aider

Automatically regenerates modified Python modules using Aider before committing.

#### Installation

```bash
# Link the hook to your git hooks directory
ln -sf ../../.githooks/pre-commit-aider .git/hooks/pre-commit

# Or add to existing pre-commit hook
echo "source $(pwd)/.githooks/pre-commit-aider" >> .git/hooks/pre-commit
```

#### Configuration

Control the hook behavior with environment variables:

```bash
# Enable/disable regeneration (default: false)
export AIDER_REGENERATE=true

# Choose philosophy: fractalized, modular, or zen (default: fractalized)
export AIDER_PHILOSOPHY=fractalized

# Auto-add regenerated files to staging (default: true)
export AIDER_AUTO_ADD=true
```

You can set these in your shell profile or create a `.aider-config` file:

```bash
# .aider-config
AIDER_REGENERATE=true
AIDER_PHILOSOPHY=fractalized
AIDER_AUTO_ADD=true
```

Then source it before committing:

```bash
source .aider-config && git commit
```

#### Per-Commit Control

Enable regeneration for a single commit:

```bash
AIDER_REGENERATE=true git commit -m "Regenerate and commit"
```

#### Files Excluded from Regeneration

The hook automatically skips:
- Test files (`test_*.py` or files in `tests/` directories)
- `__init__.py` files
- Configuration files (`setup.py`, `pyproject.toml`)

## Philosophy-Based Regeneration

The hook supports three philosophies:

1. **fractalized** (default) - Patient, thread-finding approach
2. **modular** - Brick-and-stud modular design
3. **zen** - Ruthless simplicity

Choose based on your current development focus and the nature of the changes.