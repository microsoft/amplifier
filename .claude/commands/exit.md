---
description: Exit with optional memory extraction
category: memory-system
allowed-tools: Bash, Read, BashOutput
argument-hint: (No arguments) Prompts to extract | 'force' or 'now' to skip checks
---

# Claude Command: Exit

## Primary Purpose

Provide users with control over memory extraction when ending their Claude Code session. This command offers the choice to extract learnings from unprocessed transcripts before exiting, ensuring valuable insights aren't lost.

## Core Behavior

When the user runs `/exit`, the command:

1. **Checks for unprocessed transcripts** in `.data/transcripts/`
2. **Prompts user**: "Extract memories before exit? (Y/n)"
3. **If Yes**: Runs synchronous extraction with visible progress
4. **If No**: Exits immediately
5. **Shows summary** of memories extracted (if extraction ran)

**Force Exit Mode**: `/exit force` or `/exit now` skips all checks and exits immediately.
This is useful when:
- Session is at context limit and needs compact
- Memory system is not configured
- User just wants to exit without any prompts

## Understanding User Intent

This command is typically used when:
- User is ending their Claude Code session
- User wants to capture learnings from current session
- User prefers manual control over automatic background processing

## Implementation Approach

### Step 0: Check for Force Exit

If user passed 'force' or 'now' as argument, exit immediately without any checks:

```
User: /exit force
→ Exit immediately, no prompts, no checks
```

### Step 1: Check for Unprocessed Transcripts (Robust Version)

Use the transcript tracking system with robust error handling:

```bash
python3 -c "
import sys
import os

# Ensure project root and amplifier submodule are in path
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Also add amplifier/ submodule if it exists (for projects using Amplifier as submodule)
amplifier_path = os.path.join(project_root, 'amplifier')
if os.path.isdir(amplifier_path) and amplifier_path not in sys.path:
    sys.path.insert(0, amplifier_path)

try:
    from amplifier.memory.transcript_tracker import load_transcripts
    transcripts = load_transcripts()
    unprocessed = [t for t in transcripts if not t.get('processed', False)]
    print(len(unprocessed))
except ImportError:
    # Memory system not installed/configured - graceful fallback
    print('0')
except Exception:
    # Any other error - fail safe, don't block exit
    print('0')
"
```

**Error Handling**:
- If Python import fails → Assume 0 unprocessed (graceful degradation)
- If any exception → Assume 0 unprocessed (don't block exit)
- Result: User can ALWAYS exit, even if memory system broken

If zero unprocessed transcripts → Skip extraction prompt, exit immediately

### Step 2: Prompt User

If unprocessed transcripts exist, present clear choice:

```
📝 Found N unprocessed transcript(s)

Extract memories before exit? (Y/n):
```

**Important**: This is the user's decision point. Respect their choice.

### Step 3A: If User Chooses "Yes" - Run Extraction

Execute the extraction worker via watchdog manager:

```bash
python -m amplifier.memory.watchdog
```

**What happens next**:
- Watchdog spawns extraction worker subprocess
- Worker processes unprocessed transcripts sequentially
- Progress updates stream to terminal in real-time
- User sees exactly what's happening (no hidden background work)

**Progress Display** (handled by watchdog):
```
📝 Memory Extraction

Transcripts: [████████░░] 2/3
Current: Processing transcript def456...

[TRIAGE]     Identifying important ranges... ✓
             Found 3 ranges (28% coverage)

[EXTRACTION] Processing 156 messages...
             [████████████████████████████░░] 85%

[STORAGE]    Saving memories... ✓
             Extracted 12 memories
```

**User Control**:
- Press Ctrl+C anytime to cancel → Graceful stop, progress preserved
- Extraction state tracked → Can resume later with `/cleanup`

### Step 3B: If User Chooses "No" - Exit Immediately

Simply exit without extraction. Transcripts remain in queue for future processing.

### Step 4: Show Completion Summary

After extraction completes (if run):

```
✅ Memory Extraction Complete

Processed:  3 transcripts
Extracted:  42 memories
Duration:   2m 15s
Location:   .data/memories/

Memories are now available in future sessions.
```

## Error Handling

### Missing API Key

If `ANTHROPIC_API_KEY` not configured:

```
⚠️  Memory System Not Configured

The memory system requires an Anthropic API key.

To enable:
1. Get API key from console.anthropic.com
2. Add to .env:
   ANTHROPIC_API_KEY=sk-ant-...
3. Set MEMORY_SYSTEM_ENABLED=true

For now, exiting without extraction.
```

### Extraction Errors

If extraction fails (API timeout, etc.):

```
❌ Extraction Failed

Error: API timeout after 3 retries

Partial progress saved. Run `/cleanup` to:
- Resume extraction
- View error logs
- Clear state

Logs: .data/memories/logs/extraction_TIMESTAMP.log
```

## Critical Implementation Details

### ⚠️ Subprocess Management

The watchdog pattern is critical:
- **Main process**: Claude Code (this command)
- **Child process**: Watchdog manager
- **Grandchild process**: Extraction worker

**Why**: Isolation. If worker crashes, main process unaffected. State preserved for recovery.

### ⚠️ Progress Streaming

The worker outputs progress via JSON-lines protocol:

```json
{"type": "start", "total_transcripts": 3}
{"type": "progress", "current": 1, "session_id": "abc123", "stage": "triage"}
{"type": "triage_complete", "ranges": 3, "coverage": 0.28}
...
```

The watchdog consumes these and renders the terminal UI. **Don't try to parse this in the command** - just let the subprocess handle it.

### ⚠️ State Tracking

Extraction state saved to `.data/memories/.extraction_state.json`:

```json
{
  "status": "running",
  "started_at": "2025-11-12T15:30:00",
  "pid": 12345,
  "transcripts": [
    {"id": "abc123", "status": "completed", "memories": 8},
    {"id": "def456", "status": "in_progress"},
    {"id": "ghi789", "status": "pending"}
  ]
}
```

**Purpose**: Crash recovery. If extraction interrupted, `/cleanup` can resume from last completed transcript.

## Configuration Requirements

Memory extraction requires:

```bash
# .env file
MEMORY_SYSTEM_ENABLED=true
ANTHROPIC_API_KEY=sk-ant-...  # From console.anthropic.com
```

Without these, extraction gracefully skips with helpful error message.

## Response Guidelines

### Be Clear About Progress

✅ **Good**: "Extracting memories from 3 transcripts... (2/3 complete)"
❌ **Bad**: "Processing..." (no context)

### Respect User Choice

✅ **Good**: Present option, accept decision
❌ **Bad**: Push user toward extraction or add friction to "No"

### Show Value After Completion

✅ **Good**: "Extracted 42 memories now available in future sessions"
❌ **Bad**: "Done" (no indication of what was accomplished)

## Integration Points

This command integrates with:

1. **Transcript Tracking** (`amplifier/memory/transcript_tracker.py`)
   - Identifies unprocessed transcripts
   - Marks transcripts processed after extraction

2. **Watchdog Manager** (`amplifier/memory/watchdog.py`)
   - Spawns and monitors worker subprocess
   - Handles progress streaming and UI rendering

3. **Extraction Worker** (`amplifier/memory/extraction_worker.py`)
   - Does actual extraction work in subprocess
   - Reports progress via JSON-lines protocol

4. **State Tracker** (`amplifier/memory/state_tracker.py`)
   - Tracks extraction progress for crash recovery
   - Enables `/cleanup` command to resume

## Related Commands

- **`/cleanup`**: Inspect/resume crashed or interrupted extractions
- **`/transcripts`**: Manage and restore conversation transcripts

## Documentation References

For complete details on how memory extraction works:

- **User Guide**: `docs/EXIT_COMMAND.md` - Complete usage documentation
- **Worker Architecture**: `docs/EXTRACTION_WORKER.md` - Subprocess design
- **Crash Recovery**: `docs/CRASH_RECOVERY.md` - State tracking system
- **Memory System**: `docs/MEMORY_SYSTEM.md` - Overall architecture

## Remember

This command embodies **user control**. The user decides:
- Whether to extract (not forced)
- When to stop (Ctrl+C anytime)
- Whether to resume (via `/cleanup` later)

The command's job is to:
1. Make the choice clear
2. Show progress transparently
3. Handle errors gracefully
4. Preserve work if interrupted

**Trust the subprocess architecture**. Don't try to manage extraction directly - just spawn the watchdog and let it handle the complexity.
