# Amplifier Hooks Inventory

**Baseline Documentation - Phase 0**
**Created:** 2025-11-06
**Purpose:** Document all hooks configured in `.claude/settings.json` as of baseline

---

## Overview

Amplifier has **7 lifecycle hooks** configured in `.claude/settings.json` that integrate with Claude Code's workflow. These hooks enhance functionality for memory, validation, notifications, and code quality checks.

**Total Hooks:** 7
**Configuration File:** `.claude/settings.json`
**Scripts Location:** `.claude/tools/`

---

## Hook Inventory

### 1. SessionStart Hook

**When It Fires:** At the start of each Claude Code session

**Script:** `.claude/tools/hook_session_start.py`

**Purpose:** Memory retrieval system - loads relevant memories at session start

**What It Does:**
- Reads user prompt from session input
- Initializes Amplifier Memory Store and Searcher
- Searches for relevant memories (limit: 5)
- Retrieves recent memories (limit: 3)
- Returns memories as additional context
- Can be disabled via `MEMORY_SYSTEM_ENABLED=false`

**Key Functionality:**
```python
# Search for relevant memories
search_results = searcher.search(prompt, all_memories, limit=5)

# Get recent memories
recent = store.search_recent(limit=3)

# Format and return context
additionalContext: "## Relevant Context from Memory System\n..."
```

**Dependencies:**
- `amplifier.memory.MemoryStore`
- `amplifier.search.MemorySearcher`
- `hook_logger.HookLogger`

**Timeout:** 10 seconds

**Status:** ✅ Working

---

### 2. Stop Hook

**When It Fires:** When main session stops

**Script:** `.claude/tools/hook_stop.py`

**Purpose:** Memory extraction - saves important information from conversation

**What It Does:**
- Reads transcript file from session
- Parses JSONL conversation history
- Extracts memories using LLM extraction
- Stores memories in Memory Store
- Can be disabled via `MEMORY_SYSTEM_ENABLED=false`

**Key Functionality:**
```python
# Extract memories from messages
extracted = await extractor.extract_from_messages(messages, context)

# Store batch
store.add_memories_batch(extracted)
```

**Dependencies:**
- `amplifier.extraction.MemoryExtractor`
- `amplifier.memory.MemoryStore`
- `hook_logger.HookLogger`

**Timeout:** 60 seconds (enforced)

**Status:** ✅ Working

---

### 3. SubagentStop Hook

**When It Fires:** When a sub-agent (Task tool) completes

**Script:** `.claude/tools/hook_stop.py` (same as Stop)

**Purpose:** Memory extraction from sub-agent conversations

**Notes:**
- Uses identical script to Stop hook
- Captures memories from sub-agent work
- Prevents knowledge loss from parallel agent work

**Status:** ✅ Working

---

### 4. PreToolUse Hook (Task Tool Only)

**When It Fires:** Before Task tool is invoked (sub-agent launch)

**Matcher:** `Task` (only fires for this tool)

**Script:** `.claude/tools/subagent-logger.py`

**Purpose:** Log sub-agent invocations for analytics

**What It Does:**
- Logs sub-agent type, description, prompt
- Tracks usage statistics per subagent_type
- Creates daily JSONL logs
- Maintains summary.json with aggregated stats

**Key Functionality:**
```python
# Log entry structure
{
    "timestamp": "2025-11-06T...",
    "session_id": "abc123",
    "subagent_type": "zen-architect",
    "description": "...",
    "prompt_length": 1234,
    "prompt": "full prompt text"
}
```

**Output Files:**
- `.claude/logs/subagent-logs/subagent-usage-YYYY-MM-DD.jsonl`
- `.claude/logs/subagent-logs/summary.json`

**Dependencies:** None (stdlib only)

**Status:** ✅ Working

---

### 5. PostToolUse Hook #1 (Code Changes)

**When It Fires:** After Edit, MultiEdit, or Write tools complete

**Matcher:** `Edit|MultiEdit|Write`

**Script:** `.claude/tools/on_code_change_hook.sh`

**Purpose:** Automatic code quality checks after code modifications

**What It Does:**
- Detects file edits in project
- Finds project root (looks for Makefile or .git)
- Runs `make check` from appropriate directory
- Handles git worktrees and virtual environments
- Exits gracefully if no Makefile found

**Key Functionality:**
```bash
# Finds project root and runs checks
find_project_root() { ... }
make_target_exists() { ... }
setup_worktree_env() { ... }
make check  # Runs linting, formatting, type checking
```

**Environment:**
- Sets `PATH="/bin:/usr/bin:$PATH"`
- Sets `SHELL="/bin/bash"`
- Unsets `VIRTUAL_ENV` if local .venv exists

**Status:** ✅ Working

---

### 6. PostToolUse Hook #2 (All Tools)

**When It Fires:** After ANY tool completes

**Matcher:** `*` (all tools)

**Script:** `.claude/tools/hook_post_tool_use.py`

**Purpose:** Claim validation - checks assistant output against memories

**What It Does:**
- Validates assistant messages for factual claims
- Compares claims against stored memories
- Returns warnings if contradictions detected
- Requires confidence > 0.6 for warnings
- Can be disabled via `MEMORY_SYSTEM_ENABLED=false`

**Key Functionality:**
```python
# Validate text for claims
validation_result = validator.validate_text(content, memories)

# Return warnings for contradictions
if claim_validation.contradicts and confidence > 0.6:
    warnings.append(f"⚠️ Claim may be incorrect: '{claim}'...")
```

**Dependencies:**
- `amplifier.memory.MemoryStore`
- `amplifier.validation.ClaimValidator`
- `hook_logger.HookLogger`

**Status:** ✅ Working

---

### 7. Notification Hook

**When It Fires:** When Claude Code sends a notification

**Script:** `.claude/tools/on_notification_hook.py`

**Purpose:** Desktop notification system integration

**What It Does:**
- Receives notification from Claude Code
- Extracts project name from working directory
- Sends desktop notification via Amplifier notification module
- Supports debug mode via `CLAUDE_HOOK_DEBUG` env var

**Key Functionality:**
```python
# Create notification request
request = NotificationRequest(
    message=hook_data.message,
    title="Claude Code",
    subtitle=project_name,
    session_id=hook_data.session_id
)

# Send notification
response = sender.send(request)
```

**Dependencies:**
- `amplifier.utils.notifications.core.NotificationSender`
- `amplifier.utils.notifications.models.*`

**Status:** ✅ Working

---

### 8. PreCompact Hook

**When It Fires:** Before conversation is compacted

**Matcher:** `*` (all compact operations)

**Script:** `.claude/tools/hook_precompact.py`

**Purpose:** Export full conversation transcript before compaction

**What It Does:**
- Reads JSONL transcript file
- Formats all messages (user, assistant, system)
- Includes tool uses, tool results, thinking blocks
- Detects previously loaded transcripts (avoids duplication)
- Exports to `.data/transcripts/compact_YYYYMMDD_HHMMSS_<session_id>.txt`

**Key Functionality:**
```python
# Export complete transcript with formatting
format_message(msg)  # Handles text, tool_use, tool_result, thinking

# Detect duplicate embeddings
loaded_sessions = extract_loaded_session_ids(entries)

# Write formatted transcript
f.write("CLAUDE CODE CONVERSATION TRANSCRIPT\n")
f.write(format_message(msg))
```

**Output Format:**
- Header with metadata
- All messages formatted with roles
- Tool uses/results included
- Thinking blocks preserved
- Marks embedded transcripts

**Timeout:** 30 seconds

**Dependencies:**
- `hook_logger.HookLogger`

**Status:** ✅ Working

---

## Hook Execution Order

**Session Lifecycle:**
```
1. SessionStart → Memory retrieval
2. [User interaction]
3. PreToolUse (if Task) → Log sub-agent
4. [Tool execution]
5. PostToolUse (#1) → Code checks (if Edit/Write)
6. PostToolUse (#2) → Claim validation
7. [More interaction]
8. PreCompact → Export transcript
9. [Compact happens]
10. Stop/SubagentStop → Memory extraction
```

---

## Configuration Structure

**Location:** `.claude/settings.json`

```json
{
  "hooks": {
    "SessionStart": [{ "hooks": [{ "type": "command", "command": "...", "timeout": 10000 }] }],
    "Stop": [{ "hooks": [{ "type": "command", "command": "..." }] }],
    "SubagentStop": [{ "hooks": [{ "type": "command", "command": "..." }] }],
    "PreToolUse": [{ "matcher": "Task", "hooks": [{ "type": "command", "command": "..." }] }],
    "PostToolUse": [
      { "matcher": "Edit|MultiEdit|Write", "hooks": [{ "type": "command", "command": "..." }] },
      { "matcher": "*", "hooks": [{ "type": "command", "command": "..." }] }
    ],
    "Notification": [{ "hooks": [{ "type": "command", "command": "..." }] }],
    "PreCompact": [{ "matcher": "*", "hooks": [{ "type": "command", "command": "...", "timeout": 30000 }] }]
  }
}
```

---

## Supporting Infrastructure

### Hook Logger

**File:** `.claude/tools/hook_logger.py`

**Purpose:** Centralized logging for all hooks

**Features:**
- Structured logging with levels (DEBUG, INFO, WARNING, ERROR)
- Automatic log rotation (keeps 7 days)
- JSON preview for complex objects
- Structure analysis without full dumps

**Used By:** All Python hooks

---

## Memory System Toggle

**Environment Variable:** `MEMORY_SYSTEM_ENABLED`

**Affects:**
- SessionStart hook (memory retrieval)
- Stop/SubagentStop hooks (memory extraction)
- PostToolUse #2 hook (claim validation)

**Values:**
- `true`, `1`, `yes` → Enabled
- `false`, `0`, `no`, or unset → Disabled

---

## File System Impact

### Directories Created

```
.claude/
├── logs/
│   └── subagent-logs/         # Sub-agent usage logs
├── tools/                      # Hook scripts
└── settings.json               # Hook configuration

.data/
└── transcripts/                # Exported conversation transcripts

amplifier/
└── .data/
    └── memories.jsonl          # Memory store
```

### Log Files

```
.claude/logs/subagent-logs/
├── subagent-usage-2025-11-06.jsonl
├── subagent-usage-2025-11-05.jsonl
└── summary.json

.claude/logs/hooks/
├── session_start_20251106.log
├── stop_hook_20251106.log
├── post_tool_use_20251106.log
└── precompact_export_20251106.log
```

---

## Testing Status

| Hook | Last Tested | Status | Notes |
|------|------------|--------|-------|
| SessionStart | 2025-11-06 | ✅ Working | Memory retrieval functional |
| Stop | 2025-11-06 | ✅ Working | Memory extraction functional |
| SubagentStop | 2025-11-06 | ✅ Working | Same as Stop |
| PreToolUse (Task) | 2025-11-06 | ✅ Working | Sub-agent logging functional |
| PostToolUse (Code) | 2025-11-06 | ✅ Working | Make check runs correctly |
| PostToolUse (All) | 2025-11-06 | ✅ Working | Claim validation functional |
| Notification | 2025-11-06 | ✅ Working | Desktop notifications work |
| PreCompact | 2025-11-06 | ✅ Working | Transcript export functional |

---

## Dependencies Summary

**Python Modules (Internal):**
- `amplifier.memory` - Memory storage and retrieval
- `amplifier.extraction` - LLM-based memory extraction
- `amplifier.search` - Semantic memory search
- `amplifier.validation` - Claim validation
- `amplifier.utils.notifications` - Desktop notifications
- `amplifier.config.paths` - Path configuration

**System Requirements:**
- Python 3.11+
- bash
- make (for code check hook)

**External Dependencies:**
- None for hooks themselves
- Amplifier modules have their own dependencies

---

## Maintenance Notes

### Common Operations

**Disable all memory hooks:**
```bash
export MEMORY_SYSTEM_ENABLED=false
```

**View sub-agent usage:**
```bash
cat .claude/logs/subagent-logs/summary.json
```

**Check recent transcripts:**
```bash
ls -lt .data/transcripts/ | head -10
```

**View hook logs:**
```bash
tail -f .claude/logs/hooks/session_start_$(date +%Y%m%d).log
```

### Troubleshooting

**Hook not firing:**
1. Check `.claude/settings.json` syntax
2. Verify script has execute permissions
3. Check hook logs in `.claude/logs/hooks/`

**Memory system issues:**
4. Verify `MEMORY_SYSTEM_ENABLED` not set to false
5. Check `amplifier/.data/memories.jsonl` exists and writable
6. Review memory hook logs

**Code check hook not running:**
7. Verify Makefile exists with `check` target
8. Ensure `make` is in PATH
9. Check `.venv` exists for Python projects

---

## Risk Assessment

**If hooks disabled:**
- ❌ No memory retrieval (lose context)
- ❌ No memory extraction (lose learnings)
- ❌ No claim validation (may make incorrect statements)
- ❌ No code quality checks (may introduce errors)
- ❌ No transcript backups (lose conversation history)
- ❌ No sub-agent analytics (lose usage insights)
- ✅ Base Claude Code functionality still works

**Critical hooks (must not break):**
1. Stop/SubagentStop (memory loss if broken)
2. PreCompact (transcript loss if broken)
3. PostToolUse #1 (code quality if broken)

**Non-critical hooks:**
- Notification (convenience only)
- SubagentLogger (analytics only)

---

## Integration Points

**With Amplifier modules:**
- Memory system (`amplifier/memory/`)
- Validation system (`amplifier/validation/`)
- Notification system (`amplifier/utils/notifications/`)

**With Claude Code:**
- Session lifecycle events
- Tool execution pipeline
- Notification system
- Compact workflow

---

## Future Considerations

**Potential enhancements:**
- [ ] Add hook for PreToolUse (all tools) to check memory before operations
- [ ] Add hook for PostCompact to clean up old transcripts
- [ ] Add metrics collection for hook performance
- [ ] Add hook health checks in SessionStart

**Known limitations:**
- No hook for detecting transcript loading (relies on pattern matching)
- No hook for detecting subagent failure (only success)
- Memory system requires manual environment variable toggle

---

**Baseline Status:** ✅ Complete and documented
**All hooks:** 7 configured, 7 functional
**Last verified:** 2025-11-06
