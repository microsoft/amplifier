# Where Memory Extraction Data Comes From

## Short Answer

**The data comes from Claude Code's session files** stored at:
```
~/.claude/projects/<project-name>/*.jsonl
```

Each `.jsonl` file contains ONE message (user or assistant) in JSON format.

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOU TYPE IN CLAUDE CODE                       │
│  "I prefer JWT for authentication"                              │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│           CLAUDE CODE SAVES TO SESSION FILE                      │
│  ~/.claude/projects/-Users-max-Documents-GitHub-amplifier/      │
│    abc123def.jsonl                                               │
│                                                                  │
│  {"role": "user", "content": "I prefer JWT for authentication"} │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                 CLAUDE CODE RESPONDS                             │
│  "JWT is excellent for API-first architectures..."              │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│           CLAUDE CODE SAVES RESPONSE                             │
│    def456ghi.jsonl                                               │
│                                                                  │
│  {"role": "assistant", "content": "JWT is excellent..."}        │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│          MEMORY EXTRACTION READS THESE FILES                     │
│                                                                  │
│  1. Read all .jsonl files in session directory                  │
│  2. Parse JSON from each file                                   │
│  3. Build list of messages                                      │
│  4. Filter to last 20 messages                                  │
│  5. Send to Claude for extraction                               │
└─────────────────────────────────────────────────────────────────┘
```

## Real Example: File Locations

### Your Current Session

When you're using Claude Code in `/Users/max/Documents/GitHub/amplifier`, session files are stored at:

```bash
~/.claude/projects/-Users-max-Documents-GitHub-amplifier/

# Contains 6,753 files like:
001bc74c-ed99-42a3-83a3-a6f7523cd24d.jsonl
001d8e2a-fa00-4942-885d-5e6d2b0082fc.jsonl
003a0131-47f1-4d86-aecf-f67f0368415d.jsonl
...
fff1ad1d-338b-48a1-b24a-b365a56900a2.jsonl
```

**Each file = one message** (either user or assistant)

### File Structure

```json
// Single .jsonl file content:
{
  "role": "user",
  "content": "I prefer JWT for authentication",
  "type": "message",
  "id": "msg_abc123",
  "model": "claude-sonnet-4",
  "timestamp": "2025-10-17T16:30:00Z"
}
```

## How Memory Extraction Accesses This Data

### Step 1: Find Session Directory

```python
# Memory extraction looks for current session
import os
from pathlib import Path

# Claude Code stores sessions at:
session_dir = Path.home() / ".claude" / "projects" / project_name

# For amplifier project:
# ~/.claude/projects/-Users-max-Documents-GitHub-amplifier/
```

### Step 2: Read All Messages

```python
# Read all .jsonl files in directory
messages = []
for jsonl_file in session_dir.glob("*.jsonl"):
    with open(jsonl_file) as f:
        message_data = json.load(f)
        messages.append(message_data)

# Sort by timestamp to get chronological order
messages.sort(key=lambda m: m['timestamp'])
```

### Step 3: Filter Messages

```python
# Only keep user/assistant messages (not system)
conversation_messages = [
    m for m in messages
    if m['role'] in ['user', 'assistant']
]

# Only keep last 20 messages
recent_messages = conversation_messages[-20:]
```

### Step 4: Extract Memories

```python
# Format for extraction
formatted = []
for msg in recent_messages:
    formatted.append(f"{msg['role'].upper()}: {msg['content']}")

conversation_text = "\n\n".join(formatted)

# Send to Claude for extraction
memories = await extractor.extract_memories(conversation_text)
```

## Two Ways to Get Conversation Data

### Method 1: Read Session Files Directly (Current Method)

```python
# Amplifier reads from ~/.claude/projects/...
session_dir = Path.home() / ".claude" / "projects" / project_name
messages = read_session_files(session_dir)
```

**Pros**:
- ✅ Access to full conversation history
- ✅ Can read any past session
- ✅ No API limits

**Cons**:
- ❌ Requires file system access
- ❌ Must find correct session directory
- ❌ File format could change

### Method 2: Use Claude Code API (Alternative)

```python
# Could also use Claude Code SDK to get conversation
from claude_code_sdk import ClaudeSDKClient

async with ClaudeSDKClient() as client:
    messages = await client.get_conversation_history()
```

**Pros**:
- ✅ Official API
- ✅ Stable interface
- ✅ Handles complexity

**Cons**:
- ❌ May have token limits
- ❌ Requires SDK setup
- ❌ Less control over filtering

## Complete Data Flow Example

### Starting Point: Your Conversation

```
You: "I prefer JWT for authentication"
  ↓ Saved to file
Claude: "JWT is excellent for API-first architectures..."
  ↓ Saved to file
You: "What about caching?"
  ↓ Saved to file
Claude: "Redis is a great choice..."
  ↓ Saved to file
```

### Storage: Individual .jsonl Files

```
~/.claude/projects/-Users-max-Documents-GitHub-amplifier/
  msg001.jsonl: {"role": "user", "content": "I prefer JWT..."}
  msg002.jsonl: {"role": "assistant", "content": "JWT is excellent..."}
  msg003.jsonl: {"role": "user", "content": "What about caching?"}
  msg004.jsonl: {"role": "assistant", "content": "Redis is..."}
```

### Memory Extraction Reads Files

```python
# 1. Find all .jsonl files
files = glob("~/.claude/projects/-Users-max-Documents-GitHub-amplifier/*.jsonl")

# 2. Read and parse each file
messages = []
for file in files:
    with open(file) as f:
        messages.append(json.load(f))

# 3. Sort chronologically
messages.sort(key=lambda m: m['timestamp'])

# 4. Filter to last 20
recent = messages[-20:]

# 5. Format for extraction
conversation = format_messages(recent)
# Result:
# USER: I prefer JWT...
# ASSISTANT: JWT is excellent...
# USER: What about caching?
# ASSISTANT: Redis is...

# 6. Send to Claude
memories = await extract_memories(conversation)
```

### Extracted Memories Saved

```json
// Saved to .data/memory.json
{
  "memories": [
    {
      "id": "mem-123",
      "content": "User prefers JWT for authentication",
      "category": "preference",
      "source": "conversation"
    },
    {
      "id": "mem-124",
      "content": "Redis is preferred caching solution",
      "category": "preference",
      "source": "conversation"
    }
  ]
}
```

## Session File Details

### Location Pattern

```
~/.claude/projects/<encoded-project-path>/*.jsonl

Examples:
~/.claude/projects/-Users-max-Documents-GitHub-amplifier/*.jsonl
~/.claude/projects/-Users-max--claude/*.jsonl
~/.claude/projects/-Users-max-Documents-GitHub-mage-ai/*.jsonl
```

The project path is encoded with:
- `/` → `-`
- Leading slash removed

### File Naming

Each message gets a **UUID filename**:
```
001bc74c-ed99-42a3-83a3-a6f7523cd24d.jsonl
06003a97-d78f-4802-90e9-5c6bbf32932b.jsonl
```

### File Contents

```json
{
  "role": "user" | "assistant" | "system",
  "content": "message text" | [structured content array],
  "type": "message",
  "id": "msg_uuid",
  "model": "claude-sonnet-4",
  "timestamp": "2025-10-17T16:30:00.000Z",
  "thinking": null | "thinking content",
  "tool_calls": [] | [tool use objects]
}
```

### Your Session Stats

```bash
# Check your amplifier session
ls -l ~/.claude/projects/-Users-max-Documents-GitHub-amplifier/ | wc -l
# Output: 6,753 files

# That's 6,753 messages in your current session!
# Memory extraction only reads the last 20 for each extraction
```

## Why This Design?

### Advantages

1. **Persistence**: Conversation survives crashes
2. **Streaming**: Messages saved as they come
3. **Compaction**: Old messages can be archived
4. **Recovery**: Can restore from files
5. **Debugging**: Easy to inspect conversation

### How Memory Extraction Uses It

1. **Read session files**: Get all messages
2. **Filter intelligently**: Last 20 only
3. **Remove noise**: Filter system messages
4. **Extract memories**: Send to Claude
5. **Save memories**: Store in .data/memory.json

## Summary

```
┌──────────────────────────────────────────────────────────────┐
│  DATA SOURCE: Claude Code Session Files                      │
│  Location: ~/.claude/projects/<project>/                     │
│  Format: One .jsonl file per message                         │
│  Total Files: 6,753 in your current session                  │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│  MEMORY EXTRACTION READS                                      │
│  - Reads all .jsonl files                                    │
│  - Parses JSON from each                                     │
│  - Sorts chronologically                                     │
│  - Filters to last 20 messages                               │
│  - Removes system/hook messages                              │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│  FORMATTED FOR EXTRACTION                                     │
│  USER: I prefer JWT...                                       │
│  ASSISTANT: JWT is excellent...                              │
│  [~700 chars, ~175 tokens]                                   │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│  SENT TO CLAUDE FOR EXTRACTION                                │
│  Cost: $0.0004                                               │
│  Time: 3-8 seconds                                           │
└──────────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────┐
│  MEMORIES STORED                                              │
│  File: .data/memory.json                                     │
│  Memories: 3 extracted                                       │
└──────────────────────────────────────────────────────────────┘
```

## Quick Check Commands

```bash
# See your session files
ls ~/.claude/projects/-Users-max-Documents-GitHub-amplifier/ | wc -l

# Look at a single message file
cat ~/.claude/projects/-Users-max-Documents-GitHub-amplifier/06003a97-d78f-4802-90e9-5c6bbf32932b.jsonl | python3 -m json.tool

# Count message types
grep -h '"role"' ~/.claude/projects/-Users-max-Documents-GitHub-amplifier/*.jsonl | sort | uniq -c
```

The data literally comes from the conversation you're having right now with Claude Code! Every message you type and every response I give is saved to these session files, and memory extraction reads them to find what's worth remembering.
