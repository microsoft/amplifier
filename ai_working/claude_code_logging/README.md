# Claude Code Logging Documentation

This directory contains comprehensive documentation about Claude Code's session logging system, discovered through empirical analysis and testing.

## Core Documentation Files

### 📖 [session_format_specification.md](session_format_specification.md)

**The primary technical reference** for understanding Claude Code's logging system.

Contains:

- Log file format and structure (JSONL)
- Core message schema with all fields
- Message DAG (Directed Acyclic Graph) structure
- Session behaviors (forking, branching, compacting)
- Message types and patterns
- Path extraction algorithms
- Implementation strategies

Key discoveries:

- Messages form DAGs, not linear chains
- "Redo from here" creates internal branches
- Compact operations create new roots in same file
- Sessions can be forked across files

### 📊 [summary_files_analysis.md](summary_files_analysis.md)

**Analysis of summary files** and their role in session management.

Contains:

- What summary files are (checkpoint snapshots)
- Structure of summary entries
- Branch checkpointing behavior
- How to leverage summary files for search/navigation

Key discoveries:

- Summary files catalog conversation branches
- Each branch gets its own summary entry
- LeafUuid references enable branch navigation

### ✅ [compact_operations_validation.md](compact_operations_validation.md)

**Validation report** from testing compact operations across multiple projects.

Contains:

- Compact operation behavior confirmation
- Parser validation results
- Statistics from 18 compact operations
- Trigger patterns (manual vs automatic)
- Token threshold analysis

Key findings:

- Compacts typically trigger at ~155k tokens
- Both manual (39%) and automatic (61%) triggers
- Sessions can have 8+ compacts in single file

## How to Use This Documentation

### For Building Tools

1. Start with `session_format_specification.md` for complete technical specs
2. Reference the message schema and DAG structures
3. Use the path extraction algorithms as implementation guides
4. Test against the validation patterns in `compact_operations_validation.md`

### For Understanding Behavior

1. Review session behaviors section for operations like --continue, --restore
2. Understand compact operations for long conversations
3. Learn about summary files for session indexing

### Key Concepts to Understand

**Message DAG Structure:**

- Every message has a UUID and optional parentUuid
- Multiple children create branches (fork points)
- File position determines abandoned vs active branches

**Compact Operations:**

- Stay in same file (no new file created)
- Create new root with null parentUuid
- Maintain continuity via logicalParentUuid
- Can be manual (/compact) or automatic (~155k tokens)

**Session Forking:**

- Operations like --continue create new session files
- Copy all history with original sessionIds
- New messages get new sessionId

## Related Tools

See the `/tools` directory for:

- `claude_code_transcripts_builder.py`: Tool to build conversation transcripts from logs
