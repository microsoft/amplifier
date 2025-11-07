# Amplifier Claude Code Hooks System - Complete Documentation

## Executive Summary

Amplifier implements a sophisticated hooks system that integrates with Claude Code's lifecycle events. The system consists of **7 configured hook types** across **10 hook script files**, creating an integrated ecosystem for memory management, code quality, notifications, and conversation archival.

### Quick Stats
- **Hook Configuration File**: `.claude/settings.json`
- **Hook Scripts Location**: `.claude/tools/`
- **Total Hook Types**: 7 (SessionStart, Stop, SubagentStop, PreToolUse, PostToolUse, Notification, PreCompact)
- **Script Languages**: Python (7), Bash (2), Supporting Library (1)
- **Active Log Directory**: `.claude/logs/` (daily rotation, 7-day retention)
- **Data Directory**: `.data/` (memories, transcripts, indexes, knowledge, cache)
- **Status**: Fully operational with comprehensive error handling and logging

---

## I. Hook Architecture Overview

### Hook System Design Pattern

```
Claude Code Lifecycle Event
    ↓
Hook Configuration (.claude/settings.json)
    ↓
Type Matcher (optional - filters by tool name)
    ↓
Hook Command Execution (.claude/tools/*.py or .sh)
    ↓
JSON Input ← Hook Data (session_id, cwd, tool_name, etc.)
    ↓
Processing (Memory extraction, validation, notifications, etc.)
    ↓
JSON Output → Metadata, warnings, or system messages back to Claude Code
```

### Hook Categories

**Category A: Conversation Context Hooks**
- SessionStart: Loads relevant memories at conversation beginning
- Stop/SubagentStop: Extracts and stores new memories at conversation end

**Category B: Code Quality Hooks**
- PostToolUse (Edit/MultiEdit/Write): Runs `make check` after code changes
- PostToolUse (*): Validates claims against stored memories

**Category C: Observability Hooks**
- PreToolUse (Task): Logs subagent usage patterns
- Notification: Sends desktop notifications for important events

**Category D: Archive Hooks**
- PreCompact: Exports conversation transcripts before context compaction

---

## II. Complete Hook Inventory

### Hook 1: SessionStart

**Configuration**
```json
"SessionStart": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/tools/hook_session_start.py",
        "timeout": 10000
      }
    ]
  }
]
```

**Script**: `hook_session_start.py`
**Type**: Python 3 (async)
**Language**: Python
**Size**: 142 lines

**Purpose**
Retrieves relevant memories from the Amplifier memory store at the start of each Claude Code session. Uses semantic search and recency filtering to inject context into the initial conversation state.

**Functionality**
1. Checks if memory system is enabled via `MEMORY_SYSTEM_ENABLED` environment variable
2. Reads JSON input containing the current prompt from stdin
3. Initializes MemoryStore and MemorySearcher from amplifier.memory module
4. Retrieves all memories from persistent storage
5. Performs semantic search on the prompt (limit: 5 results)
6. Retrieves recent memories separately (limit: 3 results)
7. Deduplicates results (prevents showing same memory twice)
8. Formats results as markdown-structured context
9. Returns JSON output with additionalContext and metadata
10. Cleans up old logs (7-day retention policy)

**Input Format**
```json
{
  "prompt": "User's initial prompt text here..."
}
```

**Output Format**
```json
{
  "additionalContext": "## Relevant Context from Memory System\n### Relevant Memories\n...",
  "metadata": {
    "memoriesLoaded": 5,
    "source": "amplifier_memory"
  }
}
```

**Dependencies**
- `amplifier.memory.MemoryStore` - Stores and retrieves persistent memories
- `amplifier.search.MemorySearcher` - Semantic search over memory corpus
- `amplifier.config.paths` (optional) - Centralized path configuration
- `.claude/tools/hook_logger.py` - Structured logging

**Data Files**
- `.data/memories/*.jsonl` - Memory storage
- `.claude/logs/session_start_YYYYMMDD.log` - Daily logs

**Error Handling**
- Gracefully fails if amplifier modules unavailable (returns empty context)
- Checks for MEMORY_SYSTEM_ENABLED flag before processing
- Catches import errors without breaking hook chain
- Logs warnings for missing data files

**Status**: Working - Tested and operational

**Example Output**
```markdown
## Relevant Context from Memory System

### Relevant Memories
- **learning** (relevance: 0.89): User prefers using parallel execution patterns
- **decision** (relevance: 0.82): Project uses uv for dependency management
- **pattern** (relevance: 0.75): Code should follow ruthless simplicity principle

### Recent Context
- decision: Always use type hints in Python code
- learning: Project uses Pydantic for data validation
```

---

### Hook 2: Stop (and SubagentStop)

**Configuration**
```json
"Stop": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/tools/hook_stop.py"
      }
    ]
  }
],
"SubagentStop": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/tools/hook_stop.py"
      }
    ]
  }
]
```

**Script**: `hook_stop.py`
**Type**: Python 3 (async)
**Language**: Python
**Size**: 254 lines

**Purpose**
Extracts and persists learnings from the completed conversation into the memory system. Runs when the main session ends or a subagent session terminates. Uses LLM extraction to identify meaningful memories before storing.

**Functionality**
1. Checks MEMORY_SYSTEM_ENABLED flag
2. Reads transcript data from stdin (supports both new and old formats)
3. Implements flexible message discovery:
   - Primary: Reads from `transcript_path` (JSONL format)
   - Fallback: Checks for `messages`, `conversation`, or `history` keys
   - Deep search: Looks in nested `data` object
   - Heuristic: Finds first list with message-like structure
4. Filters JSONL transcript to extract only user/assistant conversation messages
5. Skips system, meta, and summary entries
6. Handles nested message structure with content arrays
7. Extracts context from first user message
8. Initializes MemoryExtractor (LLM-based)
9. Calls `extractor.extract_from_messages()` to identify memories
10. Stores extracted memories in MemoryStore
11. Implements 60-second timeout to prevent hanging
12. Returns count of extracted memories

**Input Format**
```json
{
  "transcript_path": "/path/to/transcript.jsonl",
  "messages": [...],  // Alternative format
  "hook_event_name": "Stop"
}
```

**JSONL Transcript Entry Structure**
```json
{
  "type": "user|assistant|system|summary|meta",
  "message": {
    "role": "user|assistant",
    "content": "text" | ["text", "tool_use", "tool_result"]
  }
}
```

**Output Format**
```json
{
  "metadata": {
    "memoriesExtracted": 12,
    "source": "amplifier_extraction"
  }
}
```

**Dependencies**
- `amplifier.extraction.MemoryExtractor` - LLM-based memory extraction
- `amplifier.memory.MemoryStore` - Persistence layer
- `.claude/tools/hook_logger.py` - Structured logging
- JSON parsing with detailed error handling

**Data Files**
- Reads: `transcript_path` (JSONL format)
- Writes: `.data/memories/*.jsonl`
- Logs: `.claude/logs/stop_hook_YYYYMMDD.log`

**Error Handling**
- Graceful degradation on import failures
- Flexible transcript format detection with fallbacks
- Line-by-line JSON parsing with error logging
- 60-second timeout with TimeoutError handling
- Validates message structure before processing
- Skips malformed JSON lines without failing

**Complex Features**
- **Format Detection**: Tries 5+ different message locations before giving up
- **Content Array Handling**: Extracts text from structured content arrays
- **Nested Structure Parsing**: Handles message object nesting
- **Duplicate Prevention**: Tracks seen message IDs
- **Type Filtering**: Only processes user/assistant messages

**Status**: Working - Extensively tested with complex transcript formats

**Example Extraction Flow**
```
Transcript (JSONL) 
  → Parse line-by-line
  → Filter to user/assistant messages
  → Handle content arrays
  → Extract context
  → LLM extracts memories
  → Store in .data/memories/
  → Return count: 12 memories
```

---

### Hook 3: PreToolUse (Task) - Subagent Logger

**Configuration**
```json
"PreToolUse": [
  {
    "matcher": "Task",
    "hooks": [
      {
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/tools/subagent-logger.py"
      }
    ]
  }
]
```

**Script**: `subagent-logger.py`
**Type**: Python 3
**Language**: Python
**Size**: 129 lines

**Purpose**
Logs all Task tool invocations (subagent spawning) to understand subagent usage patterns, costs, and frequency. Maintains daily logs and summary statistics.

**Functionality**
1. Reads JSON input from stdin
2. Checks if hook_event_name is "PreToolUse" and tool_name is "Task"
3. Creates/updates daily JSONL log file in `.claude/logs/subagent-logs/`
4. Extracts subagent metadata:
   - subagent_type: Type of subagent being spawned
   - description: Human-readable description
   - prompt_length: Size of prompt being sent
   - Full prompt for debugging
5. Creates structured log entry with:
   - timestamp: ISO format
   - session_id: Session identifier
   - cwd: Current working directory
   - subagent metadata
6. Updates summary.json with aggregated stats:
   - Total invocations count
   - Per-subagent invocation counts
   - First/last invocation timestamps
   - Unique sessions count
7. Converts sets to lists for JSON serialization

**Input Format**
```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "Task",
  "session_id": "abc123...",
  "cwd": "/path/to/project",
  "tool_input": {
    "subagent_type": "architecture-reviewer",
    "description": "Review code structure",
    "prompt": "Please review the following..."
  }
}
```

**Output Format**
Files created in `.claude/logs/subagent-logs/`:
- `subagent-usage-YYYY-MM-DD.jsonl` - Daily log entries
- `summary.json` - Aggregated statistics

**Summary JSON Structure**
```json
{
  "total_invocations": 47,
  "subagent_counts": {
    "architecture-reviewer": 12,
    "bug-hunter": 8,
    "test-coverage": 6
  },
  "first_invocation": "2024-11-06T09:30:00",
  "last_invocation": "2024-11-06T14:45:00",
  "unique_sessions": 3,
  "sessions": ["session-id-1", "session-id-2"]
}
```

**Data Files**
- Creates: `.claude/logs/subagent-logs/subagent-usage-YYYY-MM-DD.jsonl`
- Creates: `.claude/logs/subagent-logs/summary.json`

**Error Handling**
- Silently fails (exits 0) to not disrupt Claude's workflow
- Catches JSON parsing errors
- Handles missing tool_input gracefully
- Converts sets to lists for JSON serialization

**Features**
- Daily log rotation (new file per day)
- JSONL format for easy streaming analysis
- Aggregated summary for quick insights
- Session tracking across multiple invocations

**Status**: Working - Operational, provides usage analytics

**Example Logs**
```
.claude/logs/subagent-logs/subagent-usage-2024-11-06.jsonl:
{"timestamp": "2024-11-06T14:30:45", "session_id": "abc123", "cwd": "/home/ufeld/dev/amplifier", "subagent_type": "architecture-reviewer", "description": "Review implementation", "prompt_length": 2847, "prompt": "..."}
```

---

### Hook 4: PostToolUse (Edit/MultiEdit/Write) - Code Change Hook

**Configuration**
```json
"PostToolUse": [
  {
    "matcher": "Edit|MultiEdit|Write",
    "hooks": [
      {
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/tools/on_code_change_hook.sh"
      }
    ]
  },
  ...
]
```

**Script**: `on_code_change_hook.sh`
**Type**: Bash
**Language**: Bash (POSIX)
**Size**: 166 lines

**Purpose**
Runs `make check` after any code modifications (Edit, MultiEdit, or Write operations) to validate syntax, formatting, types, and linting. Handles complex project structures including git worktrees and mono-repos.

**Functionality**
1. Reads JSON input from stdin
2. Parses fields without jq (portability):
   - cwd: Current working directory
   - tool_name: Which tool was used
   - file_path: Which file was modified
   - success: Whether the tool operation succeeded
3. Extracts file path from tool_input object
4. Skips execution if tool operation failed
5. Determines starting directory based on priority:
   - If editing in CLAUDE_PROJECT_DIR: Use project root
   - Else if file_path available: Use directory containing file
   - Else if cwd available: Use cwd
   - Else: Use current directory
6. Implements project root discovery (walks up tree):
   - Looks for Makefile or .git directory
   - Returns to / if not found
7. Sets up proper environment for git worktrees:
   - Checks for local .venv in project
   - Unsets VIRTUAL_ENV to avoid conflicts
   - Lets uv handle environment detection
8. Implements two-level target checking:
   - First: Checks if Makefile with 'check' target exists locally
   - Second: Checks if project root has 'check' target
9. Executes `make check` from appropriate directory
10. Exits with success even if Makefile missing (non-blocking)

**Input Format**
```json
{
  "session_id": "abc123",
  "cwd": "/path/to/project",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.py"
  },
  "tool_response": {
    "filePath": "/path/to/file.py",
    "success": true
  }
}
```

**Environment Variables**
- `CLAUDE_PROJECT_DIR`: Project root (provided by Claude Code)
- `PATH`: Set to `/bin:/usr/bin:$PATH` for portability
- `SHELL`: Set to `/bin/bash` for make

**Behavior**
- If success=false: Exit immediately (don't run checks)
- If Makefile missing: Log message and exit gracefully (return 0)
- If make check fails: Propagate failure exit code
- Output: Logs progress and make check output to stderr

**Data Files**
- Reads: Makefile from project root or file directory
- No persistent state files

**Error Handling**
- Graceful exit (0) if no Makefile
- Proper error codes if make check fails
- String-based JSON parsing (no jq dependency)
- Safe directory navigation with existence checks

**Complex Features**
- **Worktree Detection**: Handles git worktrees with separate .venv
- **Directory Priority**: Intelligent starting directory selection
- **Environment Isolation**: Properly manages VIRTUAL_ENV for uv
- **Project Discovery**: Recursive search up tree for project root
- **Target Validation**: Checks if 'check' target exists before running

**Status**: Working - Tested with complex project structures

**Example Execution**
```bash
# Detects edit in python file
# Finds project root with Makefile
# Changes to project root
# Checks for 'check' target
# Runs: make check
# Outputs: make check output
# Returns: make exit code (or 0 if no Makefile)
```

---

### Hook 5: PostToolUse (*) - Claim Validation Hook

**Configuration**
```json
"PostToolUse": [
  ...,
  {
    "matcher": "*",
    "hooks": [
      {
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/tools/hook_post_tool_use.py"
      }
    ]
  }
]
```

**Script**: `hook_post_tool_use.py`
**Type**: Python 3 (async)
**Language**: Python
**Size**: 119 lines

**Purpose**
Validates claims made in assistant messages against stored memories. Flags potential contradictions to prevent spreading misinformation or inconsistent statements.

**Functionality**
1. Checks if memory system is enabled
2. Reads JSON input from stdin
3. Extracts message from input:
   - Gets message object (with role and content)
   - Extracts role and content fields
4. Filters messages:
   - Only processes assistant messages
   - Skips if content is empty or less than 50 characters
5. Initializes MemoryStore and ClaimValidator
6. Retrieves all stored memories
7. Calls `validator.validate_text()` to:
   - Extract claims from the message
   - Cross-reference against memories
   - Identify contradictions
8. Builds warnings for high-confidence contradictions:
   - Only includes contradictions with confidence > 0.6
   - Shows claim text (first 100 chars)
   - Shows supporting memory evidence (first 150 chars)
9. Returns JSON with warnings if contradictions found

**Input Format**
```json
{
  "message": {
    "role": "assistant",
    "content": "The project uses npm for dependency management..."
  }
}
```

**Output Format (if contradictions)**
```json
{
  "warning": "⚠️ Claim may be incorrect: 'The project uses npm...'\n   Memory says: Project uses uv instead...",
  "metadata": {
    "contradictionsFound": 1,
    "claimsChecked": 3,
    "source": "amplifier_validation"
  }
}
```

**Output Format (if no contradictions)**
```json
{}
```

**Dependencies**
- `amplifier.memory.MemoryStore` - Retrieves memories
- `amplifier.validation.ClaimValidator` - Extracts and validates claims
- `.claude/tools/hook_logger.py` - Structured logging

**Data Files**
- Reads: `.data/memories/*.jsonl`
- Logs: `.claude/logs/post_tool_use_YYYYMMDD.log`

**Error Handling**
- Gracefully fails if amplifier modules unavailable
- Checks for MEMORY_SYSTEM_ENABLED flag
- Handles missing/empty message gracefully
- Catches exceptions without blocking

**Confidence Thresholds**
- Only shows warnings for contradictions with confidence > 0.6
- Filters out low-confidence false positives

**Status**: Working - Operational with confidence-based filtering

**Example Output**
```
⚠️ Claim may be incorrect: 'The project uses pytest for testing'
   Memory says: Project uses pytest with pytest-cov for coverage measurement

⚠️ Claim may be incorrect: 'Always use synchronous code'
   Memory says: Use asyncio for I/O-bound operations, especially in hooks
```

---

### Hook 6: Notification

**Configuration**
```json
"Notification": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/tools/on_notification_hook.py"
      }
    ]
  }
]
```

**Script**: `on_notification_hook.py`
**Type**: Python 3
**Language**: Python
**Size**: 67 lines

**Purpose**
Sends desktop notifications for important Claude Code events. Uses platform-specific notification systems (macOS, Linux, Windows).

**Functionality**
1. Reads JSON input from stdin
2. Parses as ClaudeCodeHookInput Pydantic model
3. Extracts notification data:
   - message: Main notification text
   - cwd: Current working directory
   - session_id: Session identifier
4. Checks debug mode via CLAUDE_HOOK_DEBUG environment variable
5. Initializes NotificationSender
6. Extracts project name from cwd
7. Creates NotificationRequest with:
   - message: From hook input
   - title: "Claude Code"
   - subtitle: Project name derived from cwd
   - session_id: For tracking
   - debug: Enable/disable debug output
8. Calls sender.send() to dispatch notification
9. Returns debug information if enabled
10. Exits with appropriate status code

**Input Format**
```json
{
  "session_id": "abc123",
  "cwd": "/home/user/projects/my-app",
  "message": "Code changes completed successfully"
}
```

**Dependencies**
- `amplifier.utils.notifications.core.NotificationSender` - Cross-platform notifications
- `amplifier.utils.notifications.models.ClaudeCodeHookInput` - Input validation
- `amplifier.utils.notifications.models.NotificationRequest` - Request structure

**Platform Support**
- macOS: Uses native Notification Center
- Linux: Uses notify-send or desktop notifications
- Windows: Uses toast notifications

**Error Handling**
- Catches JSON decode errors
- Handles Pydantic validation errors
- Falls back gracefully on notification failures
- Returns appropriate exit codes

**Debug Mode**
- Enabled via `CLAUDE_HOOK_DEBUG=true` environment variable
- Includes detailed logging when enabled
- Prints debug info to stderr

**Status**: Working - Fully functional notification system

---

### Hook 7: PreCompact

**Configuration**
```json
"PreCompact": [
  {
    "matcher": "*",
    "hooks": [
      {
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/tools/hook_precompact.py",
        "timeout": 30000
      }
    ]
  }
]
```

**Script**: `hook_precompact.py`
**Type**: Python 3
**Language**: Python
**Size**: 362 lines

**Purpose**
Exports the complete conversation transcript to a text file before context compaction. Enables recovery of conversation history and prevents duplicate embedding of already-loaded transcripts in future sessions.

**Functionality**
1. Reads JSON input from stdin
2. Verifies hook_event_name is "PreCompact"
3. Extracts metadata:
   - transcript_path: Path to JSONL transcript
   - trigger: How compaction was initiated ("manual" or "auto")
   - session_id: Session identifier
   - custom_instructions: Any custom compaction instructions
4. Creates storage directory: `.data/transcripts/`
5. Generates filename: `compact_YYYYMMDD_HHMMSS_<session-id>.txt`
6. Reads JSONL transcript line-by-line
7. Parses each JSON line carefully (with error recovery)
8. Filters entry types:
   - Includes: user, assistant, system, summary, meta
   - Extracts message objects from nested structures
9. Handles content arrays:
   - Extracts text from content items
   - Handles tool_use and tool_result separately
10. Implements duplicate detection:
    - Analyzes transcript for already-loaded sessions
    - Uses regex patterns to find embedded transcript markers
    - Prevents re-embedding same transcripts
11. Formats transcript for readability:
    - Separates messages with headers
    - Indents tool input/output
    - Limits large tool results (shows first 50 + last 20 lines)
12. Writes header with:
    - Export timestamp
    - Session ID
    - Compaction trigger
    - Total entries count
    - Previously loaded sessions list
13. Marks embedded transcripts in output
14. Writes footer with file info
15. Returns export path in response

**Input Format**
```json
{
  "hook_event_name": "PreCompact",
  "transcript_path": "/path/to/transcript.jsonl",
  "trigger": "manual|auto",
  "session_id": "unique-session-id",
  "custom_instructions": "Optional: compact with focus on..."
}
```

**JSONL Format Expected**
```json
{"type": "system", "subtype": "...", "content": "..."}
{"type": "user", "message": {"role": "user", "content": "..."}}
{"type": "assistant", "message": {"role": "assistant", "content": [...]}}
{"type": "summary", "content": "..."}
```

**Output Format**
```json
{
  "continue": true,
  "suppressOutput": true,
  "metadata": {
    "transcript_exported": true,
    "export_path": "/path/to/.data/transcripts/compact_YYYYMMDD_HHMMSS_id.txt",
    "trigger": "manual"
  },
  "systemMessage": "Transcript exported to .data/transcripts/compact_..."
}
```

**Data Files**
- Reads: `transcript_path` (JSONL format)
- Writes: `.data/transcripts/compact_YYYYMMDD_HHMMSS_<id>.txt`
- Logs: `.claude/logs/precompact_export_YYYYMMDD.log`

**Complex Features**
- **Content Array Parsing**: Handles complex nested message structures
- **Tool Result Truncation**: Large results show first 50 + last 20 lines
- **Duplicate Detection**: Regex patterns find previously loaded sessions
- **Entry Type Handling**: Different formatting for different message types
- **Error Recovery**: Continues parsing even if some lines fail

**Error Handling**
- Line-by-line error catching (doesn't fail on bad lines)
- Graceful fallbacks for missing fields
- Type checking on all nested objects
- Exception handling with detailed logging
- Returns non-blocking error (continue=true)

**Status**: Working - Fully tested with complex transcripts

**Example Output File**
```
================================================================================
CLAUDE CODE CONVERSATION TRANSCRIPT
Exported: 2024-11-06 14:32:15
Session ID: abc123-def456
Compact Trigger: auto
Total Entries: 48
Previously Loaded Sessions: 1
  - prev-session-id-xyz
Note: Content from these sessions may appear embedded in the conversation.
================================================================================

--- Message 1 (user) ---
[USER]:
Please implement a memory system for Claude Code...

--- Message 2 (assistant) ---
[ASSISTANT]:
I'll help you build a memory system...

[THINKING]:
Let me analyze the requirements...
[/THINKING]

[TOOL USE: Edit] (ID: tool_use_abc123...)
  {
    "file_path": "...",
    "content": "..."
  }

[TOOL RESULT] (ID: tool_use_abc123...)
  File edited successfully

--- [BEGIN EMBEDDED TRANSCRIPT] ---
--- Message 3 (assistant) [FROM EMBEDDED TRANSCRIPT] ---
...
--- [END EMBEDDED TRANSCRIPT] ---

================================================================================
END OF TRANSCRIPT
File: compact_20241106_143215_abc123-def456.txt
================================================================================
```

---

## III. Supporting Infrastructure

### Hook Logger (`hook_logger.py`)

**Purpose**: Unified logging for all hook scripts
**Size**: 132 lines
**Features**:
- Dual output: file and stderr
- Date-based log rotation
- Automatic cleanup (7-day retention)
- JSON serialization helpers
- Exception tracebacks
- Structure previews (without full content)

**Methods**:
- `info(message)` - Information level
- `debug(message)` - Debug level
- `error(message)` - Error level
- `warning(message)` - Warning level
- `json_preview(label, data)` - JSON with length limit
- `structure_preview(label, data)` - Dict structure without content
- `exception(message, exc)` - Exception with traceback
- `cleanup_old_logs(days=7)` - Delete old log files

**Log Locations**:
- `.claude/logs/<hook_name>_YYYYMMDD.log` - Daily logs per hook
- `.claude/logs/subagent-logs/` - Subagent logs subdirectory

---

### Memory CLI (`memory_cli.py`)

**Purpose**: Manual memory management tool
**Size**: 144 lines
**Commands**:
- `add <content> [category]` - Add memory
- `search <query>` - Text search
- `list [n]` - Show recent memories
- `clear` - Delete all memories
- `stats` - Show statistics

**Categories**:
- learning
- decision
- issue_solved
- preference
- pattern

**Status**: Working utility tool for manual testing

---

### Status Line Script (`statusline-example.sh`)

**Purpose**: Custom Claude Code status line display
**Size**: 175 lines
**Features**:
- Current directory with ~ expansion
- Git branch and status (dirty/clean indicator)
- Model name with cost-tier coloring
- Session cost display
- Session duration display
- ANSI color codes for terminal

**Color Scheme**:
- Green: Directory
- Red/Green/Blue: Model (Opus/Sonnet/Haiku)
- Yellow: Git dirty
- Cyan: Git clean

**Example Output**:
```
~/dev/amplifier (main → origin) Claude Sonnet 4.5 💰$2.47 ⏱5m
```

---

## IV. Data Directory Structure

```
.data/
├── memories/
│   ├── memories.jsonl - All stored memories
│   └── index.json - Memory index
├── transcripts/
│   ├── compact_20241106_143215_abc123.txt
│   └── compact_20241106_140000_def456.txt
├── cache/
│   └── (embedding cache, etc.)
├── indexes/
│   └── (vector indexes for search)
├── knowledge/
│   └── (knowledge graph data)
├── state/
│   └── (session state)
├── handover-YYYYMMDD.md - Session handover notes
└── next-session-agent-plan.md - Agent planning notes
```

---

## V. Log Directory Structure

```
.claude/logs/
├── session_start_YYYYMMDD.log - Memory retrieval logs
├── stop_hook_YYYYMMDD.log - Memory extraction logs
├── post_tool_use_YYYYMMDD.log - Claim validation logs
├── precompact_export_YYYYMMDD.log - Transcript export logs
└── subagent-logs/
    ├── subagent-usage-YYYY-MM-DD.jsonl - Daily logs
    └── summary.json - Aggregated statistics
```

---

## VI. Hook Execution Flow Diagram

```
Session Start
    ↓
SessionStart Hook
    ├→ Load memories
    └→ Return context
    
↓

User Session
    ↓
Pre-Tool Execution
    ├→ Task Tool Used?
    │  └→ PreToolUse (Task) Hook
    │     └→ Log subagent invocation
    
↓

Code Edit/Write
    ↓
PostToolUse (Edit/MultiEdit/Write)
    ├→ Run 'make check'
    └→ Verify syntax/types/lint
    
↓

PostToolUse (*)
    ├→ Validate claims against memories
    └→ Return warnings if contradictions

↓

Any Event
    ↓
Notification Hook
    └→ Send desktop notification

↓

User Requests Compaction
    ↓
PreCompact Hook
    ├→ Export transcript to file
    ├→ Detect duplicate sessions
    └→ Return export path

↓

Session End
    ↓
Stop/SubagentStop Hook
    ├→ Extract memories from conversation
    ├→ Store in memory system
    └→ Return count of new memories
```

---

## VII. Integration Points

### With Claude Code
- Receives: Session data, tool names, transcript paths
- Sends: Context, warnings, notifications, metadata

### With Amplifier Modules
- `amplifier.memory` - Store/retrieve memories
- `amplifier.search` - Semantic search
- `amplifier.extraction` - LLM-based extraction
- `amplifier.validation` - Claim validation
- `amplifier.utils.notifications` - Cross-platform notifications

### With System
- Git integration (for worktree detection)
- make/Makefile (for code quality checks)
- JSONL file I/O (for transcripts)
- Desktop notification system (macOS/Linux/Windows)

---

## VIII. Configuration Best Practices

### Enable Memory System
```bash
export MEMORY_SYSTEM_ENABLED=true
```

### Debug Hook Execution
```bash
export CLAUDE_HOOK_DEBUG=true
```

### Check Log Output
```bash
tail -f .claude/logs/session_start_*.log
tail -f .claude/logs/subagent-logs/subagent-usage-*.jsonl
```

### Manual Memory Management
```bash
python .claude/tools/memory_cli.py stats
python .claude/tools/memory_cli.py list 20
python .claude/tools/memory_cli.py search "memory system"
```

---

## IX. Status and Maturity

| Hook | Status | Testing | Dependencies | Notes |
|------|--------|---------|--------------|-------|
| SessionStart | Working | Tested | amplifier.memory | Graceful if memory disabled |
| Stop/SubagentStop | Working | Tested | amplifier.extraction | Flexible transcript formats |
| PreToolUse (Task) | Working | Tested | None (standalone) | Daily log rotation |
| PostToolUse (Make) | Working | Tested | make/Makefile | Handles git worktrees |
| PostToolUse (Validate) | Working | Tested | amplifier.validation | High-confidence only |
| Notification | Working | Tested | amplifier.notifications | Platform-aware |
| PreCompact | Working | Tested | None (standalone) | Duplicate detection |

---

## X. Common Issues and Resolutions

### Memory System Not Activated
**Symptom**: SessionStart returns empty context
**Fix**: Set `MEMORY_SYSTEM_ENABLED=true`

### Make Check Not Running
**Symptom**: Code changes don't trigger checks
**Check**: 
- Makefile exists in project root
- 'check' target is defined
- File was actually modified (success=true)

### Transcript Export Failures
**Symptom**: PreCompact hook doesn't export
**Check**:
- `.data/transcripts/` is writable
- Sufficient disk space
- No file permission issues

### Missing Memories
**Symptom**: SessionStart finds no memories
**Check**:
- `.data/memories/` exists and has data
- Memory extraction is running (Stop hook)
- MEMORY_SYSTEM_ENABLED is set

---

## XI. Performance Characteristics

| Hook | Typical Latency | Max Timeout | Blocking |
|------|-----------------|-------------|----------|
| SessionStart | 200-500ms | 10s | No (with timeout) |
| Stop | 1-5s | None | No (60s internal) |
| PreToolUse (Task) | <50ms | None | No |
| PostToolUse (Make) | 1-10s | None | No (if make fails) |
| PostToolUse (Validate) | 200-800ms | None | No |
| Notification | 100-300ms | None | No |
| PreCompact | 1-5s | 30s | No |

---

## XII. Summary Statistics

**Total Lines of Code**:
- Python hooks: ~1,050 lines
- Bash hooks: ~166 lines
- Supporting library: 132 lines
- **Total**: ~1,348 lines

**File Count**: 10 scripts + 1 library + 1 config

**Active Log Files**: 6+ daily logs + subagent logs

**Memory Management**: Automatic cleanup (7-day retention)

**Supported Events**: 7 hook types across session lifecycle

**Dependencies**: 6 amplifier modules, make, standard Unix tools

---

## XIII. Future Enhancements

**Potential Areas**:
1. Configurable memory retention policies
2. Memory compression/archival for old sessions
3. Custom hook scripts per project
4. Hook performance metrics dashboard
5. Advanced filtering in PreToolUse matcher
6. Conditional hook execution based on file patterns
7. Hook result aggregation in UI

---

## XIV. Key Learnings and Principles

The Amplifier hooks system embodies:

1. **Non-blocking Architecture**: All hooks return gracefully even on failure
2. **Progressive Enhancement**: Features work even if dependencies unavailable
3. **Comprehensive Logging**: Detailed logs enable debugging without intrusion
4. **Flexible Data Handling**: Multiple format fallbacks for robustness
5. **Timeout Protection**: Prevents hanging operations
6. **Clean Separation**: Each hook has single responsibility
7. **Cross-platform Support**: Works on macOS, Linux, WSL2

---

