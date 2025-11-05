---
description: Restore conversation after compact or manage past transcripts
category: session-management
allowed-tools: Bash, Read, Glob, Write
argument-hint: (No arguments = restore full conversation) OR describe what you want (e.g., "export this chat", "find when we talked about X")
---

# Claude Command: Transcripts

## 🔴 CRITICAL: NEVER REDIRECT OUTPUT ON FIRST RUN 🔴

**The transcript_manager.py tool MUST output directly to stdout to load content into context.**
**NEVER use `>` or `|` - this BREAKS the entire purpose of the tool!**

## Primary Purpose

Help users manage and restore conversation transcripts, especially after compaction events that summarize and remove detailed context.

## Understanding User Intent

User request: $ARGUMENTS

When no arguments are provided, **default to restoring the full conversation lineage** - this is the most common use case after a compact.

Otherwise, interpret the user's natural language request to understand what they want to do with transcripts.

## Available Actions

### Core Capabilities
1. **Restore** - Output full conversation history back to the beginning
2. **Search** - Find specific topics or terms in past conversations
3. **List** - Show available transcripts with metadata
4. **Export** - Save conversations in shareable formats
5. **Load** - Output a specific transcript by identifier

### The transcript_manager.py Tool

Located at `tools/transcript_manager.py`, this CLI tool provides:
- `restore` - Outputs complete conversation lineage content
- `load SESSION_ID` - Outputs specific transcript
- `list [--json]` - Returns transcript metadata
- `search TERM` - Outputs matching content with context
- `export --session-id ID --format text` - Saves to file

## ⚠️ CRITICAL: Output Handling Requirements ⚠️

**The tool outputs raw content directly to stdout. This content MUST flow into the conversation context.**

### 🚫 NEVER DO THIS:
```bash
# WRONG - This PREVENTS context loading!
python tools/transcript_manager.py restore > /tmp/output.txt

# WRONG - This also PREVENTS context loading!
python tools/transcript_manager.py restore | head -100
```

### ✅ ALWAYS DO THIS:
```bash
# CORRECT - Let the output flow directly to stdout
python tools/transcript_manager.py restore

# The content automatically becomes part of the conversation
```

**WHY THIS MATTERS**: The entire purpose of this tool is to inject transcript content into the conversation context. Redirecting or piping the output defeats this purpose entirely!

## Implementation Approach

1. **Interpret the user's request** using your natural language understanding
2. **Call the appropriate transcript_manager command** to get the content or perform the action
3. **Present results naturally** to the user

### For Restoration (Most Common)

When restoring (default or explicit request), simply run:

```bash
python tools/transcript_manager.py restore
```

The full conversation content will be automatically loaded into the current context.

### For Other Actions

Apply your understanding to map the request to the appropriate tool command and present results in a user-friendly way.

## Response Guidelines

- Use natural, conversational language
- Avoid technical jargon (prefer "conversation" over "session", "chat" over "transcript")
- Focus on what the user can do with the results

## Examples of Natural Responses

**After restoration:**
"✅ Your entire conversation thread has been successfully restored! The full history is now available in our current context."

**After search:**
"I found 3 places where we discussed authentication. Here are the relevant excerpts..."

**After listing:**
"Here are your recent conversations:
- 2 hours ago: Started with a question about hooks...
- Yesterday: Working on the synthesis pipeline..."

## Remember

The transcript_manager.py is a simple tool that outputs content. Your role is to:
1. Understand what the user wants
2. Get the content from the tool
3. Present it naturally

Trust your language understanding capabilities to interpret requests and choose appropriate actions.