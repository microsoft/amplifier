# Git Worktree Guide for Amplifier

Git worktrees are a powerful feature that allow you to have multiple branches checked out simultaneously in different directories. Amplifier extends this with additional features for managing parallel development workflows.

## Table of Contents

- [Quick Start](#quick-start)
- [Core Features](#core-features)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Basic Workflow

```bash
# Create a new worktree for experimentation
make worktree my-feature

# Navigate to the new worktree
cd ../amplifier.my-feature

# Work on your feature (already has .venv set up!)
# ...make changes, test, etc...

# When done, remove it
make worktree-rm my-feature
```

### Why Use Worktrees?

1. **Parallel Experiments**: Test multiple approaches simultaneously
2. **Clean Isolation**: Each worktree has its own branch, files, and virtual environment
3. **Fast Switching**: No stashing/unstashing or branch switching needed
4. **Risk-Free**: Experiment freely without affecting your main work

## Core Features

### Creating Worktrees

```bash
# Basic usage
make worktree feature-name

# With namespaced branches (e.g., for teams)
make worktree username/feature-name
```

**What happens:**
- Creates directory: `../amplifier.feature-name/`
- Creates/uses branch: `feature-name` (or `username/feature-name`)
- Copies `.data/` directory for knowledge base access
- Sets up isolated Python virtual environment
- Ready to use immediately!

### Directory Naming Convention

Amplifier uses a dot (`.`) separator between repo name and feature:
- `amplifier.feature-name` - Clear separation
- `amplifier.complex-feature-name` - Handles hyphens in names
- `amplifier.feature-name` (from `username/feature-name`) - Strips namespace from directory

### Listing and Removing

```bash
# List all active worktrees
make worktree-list

# Remove a worktree and its branch
make worktree-rm feature-name

# Force remove (even with uncommitted changes)
make worktree-rm-force feature-name
```

## Advanced Features

### Hiding Worktrees (Stash/Unstash)

Sometimes you want to declutter your workspace without losing work. The stash feature hides worktrees from `git worktree list` and VSCode while preserving the directory and all files.

```bash
# Hide a worktree from git (keeps directory intact)
make worktree-stash feature-name

# List all hidden worktrees
make worktree-list-stashed

# Restore a hidden worktree
make worktree-unstash feature-name
```

**Use cases:**
- Too many worktrees cluttering VSCode's git view
- Temporarily pause work without losing state
- Clean up workspace for focused work

**How it works:**
- Removes git's tracking metadata only
- Directory and all files remain untouched
- Can be restored anytime with full history

### Adopting Remote Branches

Pull down branches created on other machines or by teammates:

```bash
# Create worktree from a remote branch
make worktree-adopt origin/feature-name

# Or if someone else created it
make worktree-adopt teammate/cool-feature
```

**What happens:**
- Fetches latest from origin
- Creates local worktree tracking the remote branch
- Sets up directory as `amplifier.cool-feature`
- Ready to continue work started elsewhere

**Perfect for:**
- Continuing work started on another machine
- Checking out a colleague's branch for review
- Testing branches from CI/CD pipelines

## Best Practices

### 1. Naming Conventions

```bash
# Feature development
make worktree feat-authentication

# Bug fixes
make worktree fix-login-error

# Experiments
make worktree exp-new-algorithm

# With namespaces
make worktree myname/feat-caching
```

### 2. Parallel Experimentation Pattern

```bash
# Create multiple approaches
make worktree approach-redis
make worktree approach-memcached
make worktree approach-inmemory

# Test each in parallel
cd ../amplifier.approach-redis && make test
cd ../amplifier.approach-memcached && make test
cd ../amplifier.approach-inmemory && make test

# Keep the winner, remove the rest
make worktree-rm approach-memcached
make worktree-rm approach-inmemory
```

### 3. Stash Inactive Work

```bash
# Working on multiple features
make worktree-list  # Shows 8 worktrees - too many!

# Stash the ones not actively being worked on
make worktree-stash old-feature-1
make worktree-stash old-feature-2
make worktree-stash experimental-thing

make worktree-list  # Now shows only 5 active ones

# Later, when ready to resume
make worktree-unstash experimental-thing
```

### 4. Cross-Machine Workflow

**Machine A (office):**
```bash
make worktree my-feature
# ...work on feature...
cd ../amplifier.my-feature
git push -u origin my-feature
```

**Machine B (home):**
```bash
make worktree-adopt my-feature
cd ../amplifier.my-feature
# ...continue work...
```

## Virtual Environment Management

Each worktree gets its own isolated Python environment automatically. See [WORKTREE_VENV_MANAGEMENT.md](WORKTREE_VENV_MANAGEMENT.md) for details.

**Key points:**
- Automatic `.venv` creation in each worktree
- No conflicts between worktrees
- Dependencies isolated per experiment
- `make check` handles environment switching automatically

## Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `make worktree NAME` | Create new worktree | `make worktree my-feature` |
| `make worktree-list` | List active worktrees | `make worktree-list` |
| `make worktree-rm NAME` | Remove worktree and branch | `make worktree-rm my-feature` |
| `make worktree-rm-force NAME` | Force remove with changes | `make worktree-rm-force my-feature` |
| `make worktree-stash NAME` | Hide worktree (keep files) | `make worktree-stash old-feature` |
| `make worktree-unstash NAME` | Restore hidden worktree | `make worktree-unstash old-feature` |
| `make worktree-list-stashed` | List hidden worktrees | `make worktree-list-stashed` |
| `make worktree-adopt BRANCH` | Create from remote branch | `make worktree-adopt origin/feature` |

## Troubleshooting

### "Worktree already exists" Error

If you get this error, the branch might already have a worktree:
```bash
make worktree-list  # Check existing worktrees
make worktree-rm old-one  # Remove if needed
```

### Can't Remove Worktree

If normal remove fails:
```bash
# Force remove (loses uncommitted changes!)
make worktree-rm-force stubborn-feature

# Manual cleanup if completely broken
rm -rf ../amplifier.stubborn-feature
rm -rf .git/worktrees/amplifier.stubborn-feature
git branch -D stubborn-feature
```

### Stashed Worktree Won't Restore

If unstash fails:
```bash
# Check if directory still exists
ls ../amplifier.feature-name

# Check stash manifest
cat .git/worktree-stash.json

# If directory is gone, remove from stash
# Edit .git/worktree-stash.json to remove the entry
```

### VSCode Not Recognizing Worktree

VSCode might need a restart after creating worktrees:
1. Create worktree
2. Open the worktree directory in VSCode
3. If git features aren't working, reload VSCode window (Ctrl+Shift+P → "Reload Window")

## Advanced Tips

### 1. Global .gitignore for Worktrees

Add to your global gitignore to keep worktrees clean:
```bash
echo "amplifier-*/" >> ~/.gitignore_global
echo "amplifier.*/" >> ~/.gitignore_global
```

### 2. Quickly Navigate Between Worktrees

Add aliases to your shell:
```bash
# In ~/.bashrc or ~/.zshrc
alias wt-main='cd ~/repos/amplifier'
alias wt-list='cd ~/repos/amplifier && make worktree-list'
alias wt-cd='cd ~/repos/amplifier..$1'
```

### 3. Clean Up All Stale Worktrees

```bash
# Remove all prunable worktrees at once
git worktree prune

# List and remove all stale worktrees
for wt in $(git worktree list --porcelain | grep "prunable" -B 2 | grep "worktree" | cut -d' ' -f2); do
  rm -rf "$wt"
done
```

### 4. Worktree Templates

Create a template for common worktree setups:
```bash
#!/bin/bash
# save as make-feature-worktree.sh
make worktree $1
cd ../amplifier.$1
echo "# $1 Feature" > NOTES.md
mkdir -p tests docs
echo "Ready to work on $1!"
```

## Integration with Amplifier Features

### Using Agents Across Worktrees

Each worktree can use all Amplifier agents:
```bash
cd ../amplifier.my-experiment
claude  # Start Claude with all agents available
# "Use zen-architect to design this experiment"
```

### Knowledge Base Access

All worktrees share the same knowledge base (if using external `AMPLIFIER_DATA_DIR`):
```bash
# In any worktree
make knowledge-query Q="authentication patterns"
# Gets same results across all worktrees
```

### Parallel Testing with Transcripts

Test multiple approaches while preserving conversation history:
```bash
# In worktree 1
claude  # Design approach A
# /compact when needed (auto-saves transcript)

# In worktree 2
claude  # Design approach B
# /compact when needed (separate transcript)

# Later, compare transcripts
make transcript-search TERM="performance"
```

## Summary

Git worktrees in Amplifier provide a powerful way to:
- **Experiment freely** without fear of breaking your main work
- **Test in parallel** to find the best solution faster
- **Manage complexity** by hiding inactive work
- **Collaborate easily** by adopting branches from anywhere

The stash/unstash and adopt features extend git's native worktrees to handle real-world development workflows where you need to juggle multiple experiments, pause and resume work, and collaborate across machines.