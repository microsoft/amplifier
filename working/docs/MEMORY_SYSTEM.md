# Memory System Documentation

## Overview

The Amplifier Memory System provides persistent memory extraction and retrieval capabilities for Claude Code conversations. It automatically extracts key learnings, decisions, and solutions from conversations and makes them available in future sessions.

## Features

- **Automatic extraction** of memories from conversations
- **Pattern-based extraction** for reliable operation outside Claude Code environment
- **Session persistence** across multiple conversations
- **Relevance search** for contextual memory retrieval
- **Opt-in system** via environment variable

## Configuration

The memory system is **disabled by default** and must be explicitly enabled.

### Enabling the Memory System

Set the following environment variable in your `.env` file or shell:

```bash
MEMORY_SYSTEM_ENABLED=true
```

### Configuration Options

All configuration options can be set via environment variables:

```bash
# Enable/disable the memory system
MEMORY_SYSTEM_ENABLED=false  # true/1/yes to enable, false/0/no to disable

# Model for memory extraction (fast model recommended)
MEMORY_EXTRACTION_MODEL=claude-3-5-haiku-20241022

# Extraction settings
MEMORY_EXTRACTION_TIMEOUT=120          # Timeout in seconds
MEMORY_EXTRACTION_MAX_MESSAGES=20      # Max messages to process
MEMORY_EXTRACTION_MAX_CONTENT_LENGTH=500  # Max chars per message
MEMORY_EXTRACTION_MAX_MEMORIES=10      # Max memories per session

# Storage location
MEMORY_STORAGE_DIR=.data/memories
```

## Architecture

### Components

1. **Claude Code Hooks** (`.claude/tools/`)
   - `hook_stop.py` - Extracts memories at conversation end
   - `hook_session_start.py` - Retrieves relevant memories at start
   - `hook_post_tool_use.py` - Validates claims against memories

2. **Memory Extraction** (`amplifier/extraction/`)
   - Pattern-based extraction fallback
   - Claude Code SDK support when available
   - Quality filtering and validation

3. **Memory Storage** (`amplifier/memory/`)
   - JSON-based persistent storage
   - Categorized memories with metadata
   - Search and retrieval capabilities

### Memory Categories

- **learning** - New knowledge and insights
- **decision** - Important decisions made
- **issue_solved** - Problems solved and their solutions
- **pattern** - Recurring patterns identified
- **context** - Important contextual information

## How It Works

### 1. Memory Extraction

When a conversation ends (Stop or SubagentStop event), the system:
1. Checks if memory system is enabled via environment variable
2. Reads the conversation transcript
3. Filters to user and assistant messages only
4. Extracts key memories using pattern matching
5. Stores memories with metadata (timestamp, tags, importance)

### 2. Memory Retrieval

At conversation start (SessionStart event), the system:
1. Checks if memory system is enabled
2. Searches for relevant memories based on user prompt
3. Retrieves recent memories for context
4. Provides memories as additional context to Claude

### 3. Claim Validation

After tool use (PostToolUse event), the system:
1. Checks if memory system is enabled
2. Validates assistant claims against stored memories
3. Provides warnings if contradictions found

## Memory Storage Format

Memories are stored in JSON format at `.data/memory.json`:

```json
{
  "memories": [
    {
      "content": "Memory content text",
      "category": "learning",
      "metadata": {
        "tags": ["sdk", "claude"],
        "importance": 0.8,
        "extraction_method": "pattern_fallback"
      },
      "id": "uuid",
      "timestamp": "2025-08-26T10:10:13.391379",
      "accessed_count": 2
    }
  ],
  "metadata": {
    "version": "2.0",
    "created": "2025-08-23T05:00:26",
    "last_updated": "2025-08-26T10:26:23",
    "count": 25
  },
  "decisions_made": ["List of decisions"],
  "issues_solved": ["List of solved issues"],
  "key_learnings": ["List of learnings"]
}
```

## Debugging

### Log Files

When enabled, the memory system logs to `.claude/logs/`:
- `stop_hook_YYYYMMDD.log` - Stop hook logs
- `session_start_YYYYMMDD.log` - Session start logs  
- `post_tool_use_YYYYMMDD.log` - Post tool use logs

Logs are automatically rotated after 7 days.

### Common Issues

1. **Memory system not activating**
   - Ensure `MEMORY_SYSTEM_ENABLED=true` is set
   - Check logs in `.claude/logs/` for errors

2. **No memories being extracted**
   - Verify conversation has substantive content
   - Check extraction patterns are matching
   - Review logs for timeout errors

3. **Timeout issues**
   - Default timeout is 120 seconds
   - May need adjustment for longer conversations
   - Pattern extraction is used as fallback

## Implementation Philosophy

The memory system follows the project's core philosophies:

- **Ruthless Simplicity** - Pattern-based extraction, JSON storage
- **Modular Design** - Self-contained hooks and modules
- **Fail Gracefully** - Opt-in system that doesn't break workflows
- **Direct Integration** - Minimal wrappers around functionality

## Security Considerations

- Memories may contain sensitive information
- Storage is local to the machine
- No external API calls for storage
- Pattern extraction filters system messages

## Future Enhancements

Potential improvements while maintaining simplicity:

- Vector similarity search for better retrieval
- Memory decay/aging for relevance
- Cross-project memory sharing
- Memory export/import capabilities