---
description: Manage extraction state and recovery
category: memory-system
allowed-tools: Bash, Read, BashOutput
argument-hint: (No arguments) Inspects state and offers appropriate actions
---

# Claude Command: Cleanup

## Primary Purpose

Manage memory extraction state and provide recovery options after interruptions, crashes, or errors. This command is the user's tool for inspecting what happened and deciding what to do next.

## Core Behavior

When the user runs `/cleanup`, the command:

1. **Detects current state** (no state, running, completed, cancelled, crashed)
2. **Shows state information** (what happened, when, progress)
3. **Offers appropriate actions** based on state
4. **Executes user's choice** (resume, view logs, clear state, exit)

## Understanding User Intent

This command is typically used when:
- User interrupted extraction with Ctrl+C
- Extraction crashed unexpectedly
- User wants to check extraction status
- User needs to resume partial work
- User wants to clear old state

## State Detection

The command first determines the current extraction state by checking `.data/memories/.extraction_state.json`:

### State: No State

**File doesn't exist** → No extraction in progress or interrupted

**Response**:
```
✓ No Extraction State Found

The memory system is clean - no interrupted extractions to recover.

Everything looks good!
```

**Action**: Nothing needed, exit

### State: Running

**File exists, status="running", PID alive** → Extraction currently in progress

**Response**:
```
⚡ Extraction In Progress

Started:  2m 15s ago
Progress: 2/5 transcripts completed
Current:  Processing transcript def456...

The extraction is running normally.

Options:
1. Let it continue (exit this command)
2. View live progress (tail logs)
3. Cancel extraction (requires confirmation)

Choose option:
```

**Actions available**:
- **Option 1**: Exit command, let extraction continue
- **Option 2**: `tail -f .data/memories/logs/extraction_TIMESTAMP.log`
- **Option 3**: Kill process, mark cancelled

### State: Completed

**File exists, status="completed"** → Successfully finished, state not cleaned up

**Response**:
```
✅ Extraction Completed Successfully

Processed:  5 transcripts
Extracted:  42 memories
Duration:   5m 30s
Completed:  15 minutes ago

State file exists but extraction already finished.

Options:
1. Clear state (cleanup completed)
2. View extraction logs
3. Exit (leave state)

Choose option:
```

**Actions available**:
- **Option 1**: Delete `.extraction_state.json`
- **Option 2**: Show logs
- **Option 3**: Exit without cleanup

### State: Cancelled

**File exists, status="cancelled"** → User pressed Ctrl+C during extraction

**Response**:
```
⏸️  Extraction Was Cancelled

Progress before cancellation:
• Transcripts processed: 2/5
• Remaining: 3 transcripts
• Last update: 10 minutes ago

Partial progress is saved. Completed transcripts will not be reprocessed.

Options:
1. Resume extraction (continue from where stopped)
2. View cancellation logs
3. Clear state (abandon remaining work)
4. Exit (decide later)

Choose option:
```

**Actions available**:
- **Option 1**: Resume (spawn watchdog for remaining transcripts)
- **Option 2**: Show logs
- **Option 3**: Delete state, mark transcripts unprocessed
- **Option 4**: Exit, preserve state

### State: Crashed

**File exists, status="running", PID dead** → Process died unexpectedly

**Response**:
```
⚠️  Extraction Process Crashed

Progress before crash:
• Transcripts processed: 2/5
• Remaining: 3 transcripts
• Last update: 1 hour ago (stale)
• Worker PID 12345 is no longer running

Partial progress is saved. Completed transcripts will not be reprocessed.

Options:
1. Resume extraction (continue from where crashed)
2. View crash logs (investigate what happened)
3. Clear state (abandon work)
4. Manual investigation (show state file)
5. Exit (decide later)

Choose option:
```

**Actions available**:
- **Option 1**: Resume (spawn new worker for remaining)
- **Option 2**: Show error logs
- **Option 3**: Delete state
- **Option 4**: `cat .data/memories/.extraction_state.json | python -m json.tool`
- **Option 5**: Exit, preserve state

### State: Failed

**File exists, status="failed"** → Worker encountered errors, stopped cleanly

**Response**:
```
❌ Extraction Failed

Reason: API timeout after max retries

Progress before failure:
• Transcripts processed: 2/5
• Failed on: transcript def456
• Remaining: 3 transcripts

Error details in logs: .data/memories/logs/extraction_TIMESTAMP.log

Options:
1. Resume extraction (retry failed + remaining)
2. View error logs (understand what happened)
3. Clear state (abandon work)
4. Exit (decide later)

Choose option:
```

**Actions available**:
- **Option 1**: Resume (retry from failure point)
- **Option 2**: Show error logs
- **Option 3**: Delete state
- **Option 4**: Exit, preserve state

## Implementation Approach

### Step 1: Load and Analyze State

```bash
python -c "
from amplifier.memory.state_tracker import load_extraction_state
import os
import json

state = load_extraction_state()

if state is None:
    print('no_state')
elif state.status == 'completed':
    print('completed')
elif state.status == 'cancelled':
    print('cancelled')
elif state.status == 'failed':
    print('failed')
elif state.status == 'running':
    # Check if PID still exists
    try:
        os.kill(state.pid, 0)
        print('running')
    except OSError:
        print('crashed')
else:
    print('unknown')
"
```

### Step 2: Present State-Specific Options

Based on detected state, show appropriate menu (see State Detection section above).

### Step 3: Execute User's Choice

#### Action: Resume Extraction

**What it does**: Restarts extraction for remaining transcripts

**How**:
```bash
python -m amplifier.memory.watchdog --resume
```

**Behavior**:
- Loads existing state
- Identifies remaining transcripts (status != "completed")
- Processes only those transcripts
- Preserves completed work
- Updates state as it progresses

#### Action: View Logs

**What it does**: Shows recent extraction logs

**How**:
```bash
# Find most recent log
LOGFILE=$(ls -t .data/memories/logs/extraction_*.log | head -1)
tail -50 "$LOGFILE"
```

**Or for live viewing**:
```bash
tail -f .data/memories/logs/extraction_*.log
```

#### Action: Clear State

**What it does**: Removes state file, marks transcripts unprocessed

**How**:
```bash
python -c "
from amplifier.memory.state_tracker import clear_extraction_state
clear_extraction_state()
print('State cleared successfully')
"
```

**Warning**: Ask for confirmation if completed work exists:
```
⚠️  Warning: Clearing state will lose record of completed progress.

2 transcripts were successfully processed before interruption.

Clear state anyway? (y/N):
```

#### Action: Manual Investigation

**What it does**: Shows raw state file for inspection

**How**:
```bash
cat .data/memories/.extraction_state.json | python -m json.tool
```

**Useful for**:
- Debugging unexpected states
- Understanding what happened
- Manual recovery if needed

## Critical Implementation Details

### ⚠️ PID Checking

To detect crashes, check if the PID from state file still exists:

```python
import os

def process_exists(pid):
    try:
        os.kill(pid, 0)  # Signal 0 = existence check
        return True
    except OSError:
        return False
```

**Why**: Process might be dead but state says "running" → That's a crash.

### ⚠️ Stale State Detection

If `last_update` timestamp is old (10+ minutes) and status="running":

```python
from datetime import datetime

def is_stale(state):
    last_update = datetime.fromisoformat(state.last_update)
    elapsed = (datetime.now() - last_update).total_seconds()
    return elapsed > 600  # 10 minutes
```

**Treat stale state as crashed** → Process likely hung or terminated without cleanup.

### ⚠️ Resume Logic

When resuming, the watchdog:
1. Loads existing state
2. Counts completed transcripts (for summary)
3. Filters to remaining transcripts (status != "completed")
4. Processes only remaining
5. Adds new memories to completed count
6. Cleans up state on success

**Critical**: Never reprocess completed transcripts → Wastes API calls, time.

## Error Handling

### Corrupt State File

If state file is invalid JSON:

```
⚠️  State File Corrupted

Unable to parse .data/memories/.extraction_state.json

This can happen if:
- Disk error during write
- Manual edit went wrong
- System crash during save

Options:
1. View raw file (try to salvage)
2. Delete corrupt state (lose recovery info)
3. Exit (manual investigation)

Choose option:
```

### Missing Dependencies

If watchdog or worker modules missing:

```
❌ Memory System Not Installed

Required modules not found:
- amplifier.memory.watchdog
- amplifier.memory.extraction_worker

Run `make install` to set up dependencies.
```

## Response Guidelines

### Be Informative

✅ **Good**: "2 of 5 transcripts processed before crash. 3 remaining."
❌ **Bad**: "Crashed." (no context)

### Offer Clear Choices

✅ **Good**: Numbered menu with explicit actions
❌ **Bad**: "What do you want to do?" (vague)

### Explain Consequences

✅ **Good**: "Clearing state will lose record of 2 completed transcripts"
❌ **Bad**: "Clear state?" (unclear impact)

### Respect Uncertainty

✅ **Good**: "Exit to decide later" option always available
❌ **Bad**: Force immediate decision

## Configuration Requirements

This command works with existing state files - no API keys or configuration needed.

However, **resuming extraction** requires:

```bash
# .env file
MEMORY_SYSTEM_ENABLED=true
ANTHROPIC_API_KEY=sk-ant-...
```

If missing, show helpful error when user chooses "Resume".

## Integration Points

This command integrates with:

1. **State Tracker** (`amplifier/memory/state_tracker.py`)
   - `load_extraction_state()` - Read current state
   - `clear_extraction_state()` - Delete state file

2. **Watchdog Manager** (`amplifier/memory/watchdog.py`)
   - Resume capability (`--resume` flag)
   - Handles remaining transcript processing

3. **Transcript Tracker** (`amplifier/memory/transcript_tracker.py`)
   - Identifies which transcripts completed
   - Updates processed status

## Related Commands

- **`/exit`**: Starts extraction (which this command might need to resume)
- **`/transcripts`**: Manages conversation transcripts

## Documentation References

For complete details:

- **User Guide**: `docs/CLEANUP_COMMAND.md` - Complete usage documentation
- **Crash Recovery**: `docs/CRASH_RECOVERY.md` - State tracking and recovery system
- **State Tracker**: `docs/CRASH_RECOVERY.md#state-tracking` - State file format
- **Memory System**: `docs/MEMORY_SYSTEM.md` - Overall architecture

## Examples of Natural Responses

### After Detecting No State

```
✓ All Clear

No interrupted extractions found. The memory system is ready for new work.
```

### After Resuming Successfully

```
✅ Extraction Resumed and Completed

Previous:   2 transcripts (15 memories)
This run:   3 transcripts (27 memories)
Total:      5 transcripts (42 memories)

All memories now available in future sessions.
```

### After Viewing Logs

```
📋 Recent Extraction Log (last 50 lines)

[2025-11-12 15:30:00] Starting extraction of 3 transcripts
[2025-11-12 15:31:15] Transcript abc123: Extracted 8 memories
[2025-11-12 15:32:30] Transcript def456: Triage found 3 ranges
[2025-11-12 15:33:45] ERROR: API timeout on transcript def456
[2025-11-12 15:34:00] Extraction failed, state saved for recovery

Full logs: .data/memories/logs/extraction_20251112_153000.log
```

## Remember

This command is about **user control and recovery**. Users should feel:
- **Informed** - Know exactly what state they're in
- **Empowered** - Clear options for what to do next
- **Safe** - Partial work preserved, not lost
- **Unhurried** - "Decide later" always available

The command's job is to:
1. Detect state accurately
2. Explain clearly what happened
3. Offer appropriate actions
4. Execute choices safely
5. Provide feedback on results

**Trust the state tracking system** - it records everything needed for recovery.
