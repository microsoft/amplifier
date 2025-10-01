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
- `compact_tracer.py` - Traces compact operation lineage across sessions
- `subagent_mapper.py` - Maps Task tool invocations to subagent sessions

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
- Compact lineage tracing - Follows session chains through compact operations
- Subagent detection - Identifies and properly attributes subagent sessions
- Multiple output formats - Simple and extended transcripts
- Auto-discovery - Finds sessions from current project automatically
- Session filtering - Excludes legacy subagent sessions from root processing

**Subagent Mapping:**

The `subagent_mapper.py` module identifies which sessions are subagents spawned via the Task tool:

```python
from tools.subagent_mapper import SubagentMapper
from pathlib import Path

# Create mapper and build mapping
session_files = list(Path("/home/user/.claude/projects").glob("*.jsonl"))
mapper = SubagentMapper(session_files)
mapping = mapper.build_mapping()

# Check if a session is a subagent
if mapper.is_subagent_session("session-id"):
    info = mapper.get_subagent_info("session-id")
    print(f"Parent: {info.parent_session_id}")
    print(f"Type: {info.subagent_type}")
```

Features:
- Hash-based matching using SHA256 of normalized prompts
- Supports both sidechain messages (embedded) and separate session files
- Handles both string and structured content formats
- Creates synthetic session IDs for sidechains (`parent-id_sidechain_uuid`)

For detailed documentation, see the implementation files in this directory.

### Other Tools

- `list_by_filesize.py` - List files sorted by size for analysis
- `transcript_manager.py` - Manage conversation transcripts (Codex format)
- `codex_transcripts_builder.py` - Build transcripts from Codex sessions
- `worktree_manager.py` - Manage git worktrees with data copy support
