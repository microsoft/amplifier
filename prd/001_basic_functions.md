# PRD 001: FMA Basic Functions

## User Intent

Build foundational Python modules for FMA (Feature Management Agent) CLI tool to enable:
- Automated git worktree creation for PRD implementation
- State tracking in both worktree and central database
- Unique identification system for revision management

## Why This Matters

Enables isolated PRD development with full state synchronization between worktree and central orchestration database. Foundation for multi-agent workflow where builder/reviewer agents coordinate through shared state.

## Completed Implementation

### Module Structure
Created `fma/` package with modular organization:
```
fma/
├── cli.py                    # CLI entry point
└── src/
    ├── revisions/
    │   ├── revision.py       # Workflow orchestration
    │   └── revision_state.py # State dataclass
    └── utils/
        ├── db_utils.py       # Database read/write
        └── git_utils.py      # Git worktree operations
```

### Core Components

**RevisionState Class** (`revision_state.py`):
- Full state dataclass: id, prd_name, worktree_path, state, agent, history
- `create_initial()` - Factory for new revisions
- `to_dict()` / `from_dict()` - JSON serialization
- `add_history_entry()` - Track state changes
- `transition_to()` - State machine transitions
- State definitions: building → review_pending → in_review → approved/rejected → merged

**Database Utilities** (`db_utils.py`):
- `write_state(state)` - Write to `$LAMP_DB_HOME/database/{id}/state.json`
- `read_state(id)` - Read from database
- `write_xfma_state(path, state)` - Write to worktree `.xfma/state.json`
- `read_xfma_state(path)` - Read from worktree
- `update_state(id, updates)` - Update and sync both locations
- `list_all_states()` - Query all revisions
- `delete_state(id)` - Cleanup

**Git Utilities** (`git_utils.py`):
- `get_repo_name()` - Extract repo name
- `generate_worktree_name(prd)` - Format: `repo-prd-timestamp-claude`
- `create_worktree(prd, branch)` - Create git worktree

**Revision Workflow** (`revision.py`):
- `create_xfma_state()` - Initialize RevisionState, write to `.xfma/`
- `create_database_record()` - Write to central database
- `setup_prd_worktree()` - Orchestrate full workflow

**CLI** (`cli.py`):
- `fma build <number>` - Find PRD, create worktree, initialize state

### Integration
- CLI entry point in `pyproject.toml`: `fma = "fma.cli:main"`
- Uses existing uv/pyproject.toml setup
- Environment: `$LAMP_HOME` or `$LAMP_DB_HOME` for database location

### What Was Built

**When `fma build 001` runs:**
1. Finds `prd/001_basic_functions.md`
2. Generates unique ID: `basic-functions_{uuid}`
3. Creates worktree: `../lamp-basic-functions-20231114-152345-claude/`
4. Creates `RevisionState` object with full history tracking
5. Writes state to `.xfma/state.json` in worktree
6. Writes same state to `$LAMP_DB_HOME/database/{id}/state.json`
7. Returns worktree info for next steps

**State synchronization**: Both `.xfma/` and database contain identical RevisionState with:
- Unique ID for tracking
- PRD reference
- Worktree location
- Current state and agent
- Full history of transitions

## Phase 1: Complete ✅

All basic functions implemented and integrated.

## Phase 2: Next Steps

- Add `xfma` orchestration command
- Implement agent coordination workflow
- Add state transition commands
- Build PR automation
