# Tools Directory

This directory contains utilities for the recipe-tool project.

## Core Utilities

### AI Context Generation

- `build_ai_context_files.py` - Main orchestrator for collecting project files into AI context documents
- `collect_files.py` - Core utility for pattern-based file collection with glob support
- `build_git_collector_files.py` - Downloads external documentation using git-collector

### Claude Code Session Transcript Builder

A comprehensive tool for building readable transcripts from Claude Code session JSONL files.

**Files:**
- `claude_transcript_builder.py` - Main CLI entry point
- `dag_loader.py` - Session data loader and validator
- `dag_navigator.py` - DAG traversal and branch reconstruction
- `transcript_formatter.py` - Markdown transcript generation

**Quick Start:**
```bash
# Process most recent session from current project
python tools/claude_transcript_builder.py

# List all available sessions
python tools/claude_transcript_builder.py --list

# Process specific project
python tools/claude_transcript_builder.py --project amplifier

# Get help
python tools/claude_transcript_builder.py --help
```

**Key Features:**
- DAG reconstruction - Rebuilds full conversation structure
- Branch support - Handles conversation branches and alternative paths
- Sidechain processing - Extracts and formats sub-agent conversations
- Multiple output formats - Simple and extended transcripts
- Auto-discovery - Finds sessions from current project automatically

For detailed documentation, see the full README in the Claude Code transcript builder files.

### Other Tools

- `list_by_filesize.py` - List files sorted by size for analysis
- `transcript_manager.py` - Manage conversation transcripts (Codex format)
- `codex_transcripts_builder.py` - Build transcripts from Codex sessions
- `worktree_manager.py` - Manage git worktrees with data copy support
