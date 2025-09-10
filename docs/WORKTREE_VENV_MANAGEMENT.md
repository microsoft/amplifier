# Virtual Environment Management in Git Worktrees

This document explains how Amplifier handles virtual environments across git worktrees to avoid conflicts.

## The Problem

When using git worktrees for parallel development, all worktrees inherit the `VIRTUAL_ENV` environment variable from your shell, which points to the main repository's `.venv`. This causes issues with `uv` (the package manager), which expects each project to use its own local `.venv`.

The error looks like:
```
warning: `VIRTUAL_ENV=/Users/you/src/amplifier/.venv` does not match the project 
environment path `.venv` and will be ignored
```

## The Solution

We've implemented a three-part solution:

### 1. Automatic venv Setup in New Worktrees

When you create a worktree with `make worktree <branch-name>`, it now:
- Creates the worktree as before
- Copies the `.data` directory
- **Automatically creates a local `.venv` using `uv`**
- Installs all dependencies

### 2. Makefile Handles VIRTUAL_ENV Conflicts

The `make check` target now:
- Detects when `VIRTUAL_ENV` points to a different directory
- Unsets `VIRTUAL_ENV` to let `uv` use the local `.venv`
- Runs all checks using the correct environment

### 3. Make-Check Hook Handles Worktrees

The Claude Code hook (`.claude/tools/make-check.sh`) now:
- Detects when running in a worktree
- Unsets mismatched `VIRTUAL_ENV` variables
- Uses the worktree's local `.venv`

## Usage

### Creating a New Worktree

```bash
# Create worktree with automatic venv setup
make worktree my-feature

# The output will show:
# 🐍 Setting up virtual environment for worktree...
# ✅ Virtual environment created and dependencies installed!

# Navigate to the worktree
cd ../amplifier-my-feature

# The venv is already set up and ready to use!
```

### If venv Setup Fails

If automatic setup fails (e.g., `uv` not available), you can set it up manually:

```bash
cd ../amplifier-my-feature
make install  # This creates .venv and installs dependencies
```

### Running Checks

Just run `make check` as normal - it handles the environment automatically:

```bash
make check
# Output: Detected virtual environment mismatch - using local .venv
# Then runs all checks normally
```

## Technical Details

### What Changed

1. **`tools/create_worktree.py`**:
   - Added `setup_worktree_venv()` function
   - Runs `uv venv` and `uv sync --group dev` after creating worktree

2. **`Makefile`**:
   - `check` target unsets mismatched `VIRTUAL_ENV`
   - Uses `VIRTUAL_ENV=` prefix on `uv run` commands

3. **`.claude/tools/make-check.sh`**:
   - Added `setup_worktree_env()` function
   - Unsets `VIRTUAL_ENV` when mismatch detected

4. **`pyproject.toml`**:
   - Added exclude patterns to pyright config
   - Prevents type-checking errors from optional dependencies

## Benefits

- **No manual venv activation needed** - Each worktree has its own `.venv`
- **No more VIRTUAL_ENV warnings** - Conflicts are handled automatically
- **Seamless workflow** - Just `make worktree` and start coding
- **Claude Code hooks work** - No more make check failures

## Troubleshooting

### "uv not found" during worktree creation

Install uv first:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### VIRTUAL_ENV warnings still appearing

Make sure you're using the updated Makefile. The fix requires:
- Updated `tools/create_worktree.py`
- Updated `Makefile` with VIRTUAL_ENV handling
- Updated `.claude/tools/make-check.sh`

### Pyright errors about missing imports

These are from optional dependencies. The fix excludes these directories from pyright checking.

## Future Improvements

Potential enhancements:
- Auto-activate venv when entering worktree directory
- Share package cache between worktrees to save disk space
- Option to use symlinks for large dependencies