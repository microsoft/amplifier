# Codex Integration for Amplifier

This directory provides [Codex CLI](https://www.anthropic.com/codex) integration for the Amplifier project, establishing dual-backend support alongside the existing Claude Code integration in `.claude/`.

## Overview

Codex CLI is Anthropic's command-line interface for AI-powered development. Unlike Claude Code's VS Code-specific integration, Codex provides a standalone CLI experience with different architectural patterns:

- **Hooks vs MCP Servers**: Claude Code uses native hooks; Codex uses MCP (Model Context Protocol) servers
- **Session Storage**: Codex stores sessions in `~/.codex/`; Claude Code uses internal VS Code storage
- **Configuration**: Codex uses TOML format; Claude Code uses JSON
- **Agent Execution**: Codex uses `codex exec`; Claude Code uses the Task tool

The wrapper script (`amplify-codex.sh`) provides a seamless experience similar to Claude Code's automatic hooks, handling session initialization and cleanup automatically. For advanced users, the session management tools can be invoked manually for fine-grained control.

## Directory Structure

```
.codex/
├── config.toml          # Main Codex configuration file
├── README.md           # This documentation
├── mcp_servers/        # MCP server implementations (replaces Claude Code hooks)
├── agents/             # Codex-compatible agent definitions
├── commands/           # Command implementations for Codex
└── tools/              # Helper scripts and utilities
```

### mcp_servers/

Contains fully implemented Python-based MCP servers using FastMCP:

- **session_manager/** - Replaces `SessionStart.py` and `SessionStop.py` hooks
- **quality_checker/** - Replaces `PostToolUse.py` hook
- **transcript_saver/** - Replaces `PreCompact.py` hook

Each MCP server is a self-contained module with its own directory and server script. Server logs are written to `.codex/logs/`.

### agents/

Stores Codex-compatible agent definitions converted from `.claude/agents/`. Since Codex doesn't have Claude Code's Task tool, agents are executed via `codex exec` with appropriate context and instructions.

### commands/

Houses command implementations for Codex. Since Codex doesn't have native slash commands like Claude Code (`/architect`, `/review`, etc.), this directory contains command scripts that can be invoked via MCP tools or wrapper scripts.

### tools/

Contains Codex-specific automation tools and helper scripts including:
- Session initialization scripts
- Cleanup utilities
- Integration helpers for the existing `tools/codex_transcripts_builder.py`

## Architecture Overview

### Hook System Mapping

Codex uses MCP servers to provide functionality equivalent to Claude Code's hooks:

| Claude Code Hook | Codex MCP Server | Purpose |
|------------------|------------------|---------|
| `SessionStart.py` | `amplifier_session` | Initialize session context, set up workspace |
| `SessionStop.py` | `amplifier_session` | Handle session cleanup |
| `PostToolUse.py` | `amplifier_quality` | Run code quality checks after tool usage |
| `PreCompact.py` | `amplifier_transcripts` | Save and manage session transcripts |

### Agent Execution Differences

**Claude Code**: Uses the Task tool to spawn agents with context
```
<task>
Use the architect agent to analyze this codebase
</task>
```

**Codex**: Uses `codex exec` command with agent files
```bash
codex exec .codex/agents/architect.md --context="Analyze this codebase"
```

### Configuration Management

**Claude Code** (`.claude/settings.json`):
```json
{
  "claude": {
    "model": "claude-3-5-sonnet-20241022",
    "maxTokens": 8192
  },
  "hooks": {
    "enabled": true
  }
}
```

**Codex** (`.codex/config.toml`):
```toml
model = "claude-3-5-sonnet-20241022"
approval_policy = "on-request"

[mcp_servers.amplifier_session]
command = "uv"
args = ["run", "python", ".codex/mcp_servers/session_manager/server.py"]
```

## Configuration Guide

### MCP Server Tools Reference

#### Session Manager Tools

**`initialize_session`** - Load relevant memories (replaces SessionStart hook)
- **Input**: `{"prompt": str, "context": Optional[str]}`
- **Output**: `{"memories": [...], "metadata": {"memoriesLoaded": int, "source": "amplifier_memory"}}`
- **Usage**: Call at session start to provide context from previous work

**`finalize_session`** - Extract and store memories (replaces Stop/SubagentStop hooks)
- **Input**: `{"messages": List[dict], "context": Optional[str]}`
- **Output**: `{"metadata": {"memoriesExtracted": int, "source": "amplifier_extraction"}}`
- **Usage**: Call at session end to capture learnings

**`health_check`** - Verify server and memory system status
- **Input**: `{}`
- **Output**: `{"status": "healthy", "memory_enabled": bool, "modules_available": [...]}`
- **Usage**: Verify setup before using other tools

#### Quality Checker Tools

**`check_code_quality`** - Run make check (replaces PostToolUse hook)
- **Input**: `{"file_paths": List[str], "tool_name": Optional[str], "cwd": Optional[str]}`
- **Output**: `{"passed": bool, "output": str, "issues": [...], "metadata": {...}}`
- **Usage**: Call after editing files to validate changes

**`run_specific_checks`** - Run individual tools (ruff, pyright, pytest)
- **Input**: `{"check_type": str, "file_paths": Optional[List[str]], "args": Optional[List[str]]}`
- **Output**: `{"passed": bool, "output": str, "tool": str, "issues": [...]}`
- **Usage**: Run targeted checks (e.g., just linting or just tests)

**`validate_environment`** - Check development environment setup
- **Input**: `{}`
- **Output**: `{"valid": bool, "issues": [...], "environment": {...}}`
- **Usage**: Diagnose setup issues before running checks

#### Transcript Saver Tools

**`save_current_transcript`** - Export current session (replaces PreCompact hook)
- **Input**: `{"session_id": Optional[str], "format": str = "both", "output_dir": Optional[str]}`
- **Output**: `{"exported_path": str, "metadata": {"file_size": int, "event_count": int}}`
- **Usage**: Save session before ending work

**`save_project_transcripts`** - Batch export project sessions
- **Input**: `{"project_dir": str, "format": str = "standard", "incremental": bool = True}`
- **Output**: `{"exported_sessions": [...], "skipped": [...], "metadata": {...}}`
- **Usage**: Bulk export for project documentation

**`list_available_sessions`** - Discover exportable sessions
- **Input**: `{"project_only": bool = False, "limit": int = 10}`
- **Output**: `{"sessions": [...], "total_count": int, "project_sessions": int}`
- **Usage**: Find sessions to export or analyze

**`convert_transcript_format`** - Convert between formats
- **Input**: `{"session_id": str, "from_format": str, "to_format": str, "output_path": Optional[str]}`
- **Output**: `{"converted_path": str, "metadata": {"original_format": str, "target_format": str}}`
- **Usage**: Standardize transcript formats for analysis

### Basic Setup

1. **Install Codex CLI** (follow Anthropic's installation guide)

2. **MCP Server Status**: All three MCP servers are implemented and ready to use. Profiles are configured with appropriate server combinations.

3. **Profile Usage**:
   ```bash
   # Start Codex with development profile (all servers enabled)
   codex --profile development

   # Start with CI profile (quality checks only)
   codex --profile ci

   # Start with review profile (quality + transcripts)
   codex --profile review
   ```

### Using MCP Servers

MCP servers are now fully implemented and integrated into Codex profiles. Each server provides specific functionality that replaces Claude Code hooks:

#### Session Manager (`amplifier_session`)
- **Purpose**: Memory system integration at session boundaries
- **Tools**: `initialize_session`, `finalize_session`, `health_check`
- **Usage**: Automatically loads context at session start and saves memories at end

#### Quality Checker (`amplifier_quality`)
- **Purpose**: Code quality validation after changes
- **Tools**: `check_code_quality`, `run_specific_checks`, `validate_environment`
- **Usage**: Run quality checks after editing files

#### Transcript Saver (`amplifier_transcripts`)
- **Purpose**: Session transcript management and export
- **Tools**: `save_current_transcript`, `save_project_transcripts`, `list_available_sessions`, `convert_transcript_format`
- **Usage**: Export and manage session transcripts

#### Invoking Tools from Codex

Tools are invoked using natural language or direct tool calls:

```bash
# Load session context
codex> initialize_session with prompt "Working on user authentication"

# Check code quality
codex> check_code_quality with file_paths ["src/auth.py"]

# Save current transcript
codex> save_current_transcript with format "both"
```

#### Profile Configuration

Servers are enabled per profile in `config.toml`:

- **Development**: All servers (`amplifier_session`, `amplifier_quality`, `amplifier_transcripts`)
- **CI**: Quality checks only (`amplifier_quality`)
- **Review**: Quality + transcripts (`amplifier_quality`, `amplifier_transcripts`)

### Environment Variables

The configuration exposes essential environment variables:
- `PATH`: System path for tool access
- `HOME`: User home directory
- `AMPLIFIER_ROOT`: Project root directory
- `VIRTUAL_ENV`: Python virtual environment
- `CONDA_DEFAULT_ENV`: Conda environment

## Integration with Existing Systems

### Transcript Management

Codex integration leverages the existing `tools/codex_transcripts_builder.py` for transcript handling:

- **Global Transcripts**: Stored in `~/.codex/transcripts/`
- **Project Transcripts**: Optional local storage in `.codex/transcripts/`
- **Format Compatibility**: Maintains compatibility with Claude Code transcript formats
- **Builder Integration**: Automatic integration with existing transcript builder

### Knowledge Systems

Future MCP server implementations will provide access to:
- Knowledge synthesis workflows (`amplifier/knowledge_synthesis/`)
- Memory systems (`amplifier/memory/`)
- Content loading and extraction (`amplifier/content_loader/`, `amplifier/extraction/`)

**Note**: Knowledge system integration will be added in a later development phase.

## Transcript Format Comparison

Understanding the differences between Claude Code and Codex transcript formats is crucial for working with both backends effectively.

### Storage Locations

| Backend | Location | Format | Description |
|---------|----------|--------|-------------|
| **Claude Code** | `.data/transcripts/compact_YYYYMMDD_HHMMSS_<session-id>.txt` | Single text file | Project-local storage with compact format |
| **Codex Global** | `~/.codex/transcripts/YYYY-MM-DD-HH-MM-PM__<cwd>__<short-id>/` | Directory per session | Global storage, all Codex sessions |
| **Codex Local** | `.codex/transcripts/` | Directory per session | Optional project-local storage |

**Why the difference?** Codex uses directories because each session generates multiple files (history, standard transcript, extended transcript, metadata), while Claude Code compacts everything into a single file.

### File Structure Differences

#### Claude Code Structure
```
.data/transcripts/
├── compact_20240101_100000_a1b2c3d4-e5f6-7890-abcd-ef1234567890.txt
├── compact_20240101_110000_f1e2d3c4-b5a6-9870-dcba-fe0987654321.txt
└── ...
```

#### Codex Structure
```
~/.codex/transcripts/
├── 2024-01-01-10-00-AM__home-user-project__a1b2c3d4/
│   ├── history.jsonl              # Raw history entries
│   ├── transcript.md              # Conversation-focused markdown
│   ├── transcript_extended.md     # Detailed markdown with all events
│   └── meta.json                  # Session metadata
├── 2024-01-01-11-00-AM__home-user-other__f1e2d3c4/
│   └── ...
```

### Content Format Differences

#### Message Formatting

**Claude Code Format:**
```text
[USER]: Hello, can you help me analyze this code?

[ASSISTANT]: I'd be happy to help you analyze your code. Could you please share the code you'd like me to review?

[THINKING]: The user is asking for code analysis. I should ask them to provide the code first before I can help.

[TOOL USE: file_reader]
{
  "path": "src/main.py"
}

[TOOL RESULT]
def main():
    print("Hello, world!")

[ASSISTANT]: I can see your code is a simple "Hello, world!" program. Here's my analysis...
```

**Codex Format (transcript.md):**
```markdown
- **User** · 2024-01-01 10:00:00
  Hello, can you help me analyze this code?

- **Assistant** · 2024-01-01 10:00:01
  I'd be happy to help you analyze your code. Could you please share the code you'd like me to review?

- **Assistant [thinking]** · 2024-01-01 10:00:02
  The user is asking for code analysis. I should ask them to provide the code first before I can help.

- **Tool Call (file_reader)** · 2024-01-01 10:00:03
  ```json
  {
    "path": "src/main.py"
  }
  ```

- **Tool Result** · 2024-01-01 10:00:04
  ```python
  def main():
      print("Hello, world!")
  ```

- **Assistant** · 2024-01-01 10:00:05
  I can see your code is a simple "Hello, world!" program. Here's my analysis...
```

### Metadata Differences

#### Claude Code Header
```text
# Amplifier Claude Code Transcript Export
# Exported: 2024-01-01 12:00:00 PST
# Session ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
# Compact trigger: Auto-compact after 50 interactions
# Custom instructions: You are a helpful AI assistant for code analysis.

================================================================================
```

#### Codex Metadata
```markdown
# Codex Session Transcript

**Session ID:** a1b2c3d4-e5f6-7890-abcd-ef1234567890
**Started:** 2024-01-01T10:00:00-08:00
**Working Directory:** /home/user/project
**Event Count:** 127
**Message Count:** 45
**Tool Usage Count:** 12
**Exported:** 2024-01-01T12:00:00-08:00

---
```

### Session Identification

| Backend | Session ID Format | Example | Location |
|---------|------------------|---------|----------|
| **Claude Code** | Full UUID in filename | `compact_20240101_100000_a1b2c3d4-e5f6-7890-abcd-ef1234567890.txt` | Filename |
| **Codex** | Short ID in directory, full in metadata | Directory: `.../__a1b2c3d4/`, Metadata: full UUID | Directory name + metadata |

**Implications:**
- Claude Code: Direct lookup by full session ID in filename
- Codex: Requires directory scanning or metadata parsing for full session ID

### Timestamp Handling

#### Claude Code
- **Export Timestamp**: Single timestamp when transcript was exported
- **Message Timestamps**: Embedded in content as relative times or not at all
- **Format**: Local timezone, human-readable

#### Codex
- **Per-Event Timestamps**: Each event has precise timestamp
- **Timezone Support**: ISO 8601 format with timezone information
- **Configurable Display**: Can show in local time or UTC

**Example Timestamp Formats:**
```text
# Claude Code
Exported: 2024-01-01 12:00:00 PST

# Codex
Started: 2024-01-01T10:00:00-08:00
Event: 2024-01-01T10:05:23.456789-08:00
```

### Tool Interaction Representation

#### Claude Code
```text
[TOOL USE: file_reader]
{
  "path": "test.py",
  "lines": [1, 50]
}

[TOOL RESULT]
def function():
    return "result"

# Content may be truncated...
```

#### Codex
```markdown
- **Tool Call (file_reader)** · 2024-01-01 10:00:02
  ```json
  {
    "path": "test.py",
    "lines": [1, 50],
    "call_id": "call_abc123"
  }
  ```

- **Tool Result** · 2024-01-01 10:00:03
  ```python
  def function():
      return "result"
  ```
  *Call ID: call_abc123*
```

**Key Differences:**
- **Call Matching**: Codex uses `call_id` to match tool calls with results
- **Formatting**: Codex uses markdown code blocks with syntax highlighting
- **Metadata**: Codex includes additional metadata like call IDs and precise timestamps

### Duplicate Detection Mechanisms

#### Claude Code (hook_precompact.py)
- Detects embedded transcripts via session ID patterns in content
- Scans for file references and session IDs in export headers
- Marks sections as "previously loaded" to avoid re-processing

#### Codex
- Deduplicates user messages by normalized text + timestamp
- Uses session directory existence to skip already-processed sessions
- Tracks embedded transcript sections via metadata markers

**Example Detection Patterns:**
```text
# Claude Code looks for:
"Session ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890"
"compact_20240101_100000_*.txt"

# Codex looks for:
"# Embedded Transcript: a1b2c3d4"
Directory: "2024-01-01-10-00-AM__*__a1b2c3d4/"
```

## Working with Transcripts

The enhanced `tools/transcript_manager.py` provides a unified interface for working with both transcript formats.

### Listing Transcripts

```bash
# List all transcripts from both backends
python tools/transcript_manager.py list

# List only Claude Code transcripts
python tools/transcript_manager.py list --backend claude

# List only Codex transcripts
python tools/transcript_manager.py list --backend codex

# Get JSON output with metadata
python tools/transcript_manager.py list --json
```

### Loading Specific Transcripts

```bash
# Load by session ID (works with both full and short IDs)
python tools/transcript_manager.py load a1b2c3d4

# Load by filename (Claude Code)
python tools/transcript_manager.py load compact_20240101_100000_session.txt

# Load Codex transcript with format preference
python tools/transcript_manager.py load a1b2c3d4 --format extended
```

### Searching Across Backends

```bash
# Search in both backends
python tools/transcript_manager.py search "error handling"

# Search only in Codex transcripts
python tools/transcript_manager.py search "tool usage" --backend codex

# Search with context
python tools/transcript_manager.py search "function definition" --context 3
```

### Converting Between Formats

```bash
# Convert Claude Code transcript to Codex format
python tools/transcript_manager.py convert claude-session-123 --from claude --to codex

# Convert Codex to Claude Code format
python tools/transcript_manager.py convert codex-session-456 --from codex --to claude
```

## Transcript Processing Tools

### Enhanced Codex Transcripts Builder

The enhanced `tools/codex_transcripts_builder.py` now supports project filtering and robust error handling:

```bash
# Process all sessions (original behavior)
python tools/codex_transcripts_builder.py

# Process only sessions from current project
python tools/codex_transcripts_builder.py --project-dir .

# Process specific session
python tools/codex_transcripts_builder.py --session-id a1b2c3d4

# Incremental processing (skip already processed)
python tools/codex_transcripts_builder.py --incremental

# Skip errors and continue processing
python tools/codex_transcripts_builder.py --skip-errors --verbose

# Generate compact format
python tools/codex_transcripts_builder.py --output-format compact
```

### Codex Transcript Exporter

The new `.codex/tools/transcript_exporter.py` provides Claude Code hook-like functionality:

```bash
# Export current session
python .codex/tools/transcript_exporter.py --current

# Export specific session
python .codex/tools/transcript_exporter.py --session-id a1b2c3d4

# Export all project sessions
python .codex/tools/transcript_exporter.py --project-only

# Export with different formats
python .codex/tools/transcript_exporter.py --current --format both
python .codex/tools/transcript_exporter.py --current --format compact

# Custom output directory
python .codex/tools/transcript_exporter.py --current --output-dir ./exports
```

### Unified Transcript Manager

Use `tools/transcript_manager.py` as a single interface for both backends:

```bash
# Restore complete conversation lineage from both backends
python tools/transcript_manager.py restore

# Restore only from specific backend
python tools/transcript_manager.py restore --backend codex

# Export current session (detects backend automatically)
python tools/transcript_manager.py export --current

# List with backend indicators
python tools/transcript_manager.py list --show-backend
```

## Example Workflows

### Daily Development Workflow

```bash
# 1. Start work - check recent sessions
python tools/transcript_manager.py list --last 5

# 2. Load context from recent session
python tools/transcript_manager.py load recent-session-id

# 3. During work - export current session periodically
python .codex/tools/transcript_exporter.py --current --output-dir .codex/transcripts

# 4. End of day - restore full lineage for review
python tools/transcript_manager.py restore > daily_summary.md
```

### Project Analysis Workflow

```bash
# 1. Get all project-related sessions
python tools/codex_transcripts_builder.py --project-dir . --verbose

# 2. Search for specific topics across all transcripts
python tools/transcript_manager.py search "architecture decision"
python tools/transcript_manager.py search "bug fix" --context 2

# 3. Convert key insights to preferred format
python tools/transcript_manager.py convert key-session --to claude --output insights.txt
```

### Cross-Backend Migration

```bash
# 1. List transcripts from old backend
python tools/transcript_manager.py list --backend claude --json > claude_inventory.json

# 2. Convert important sessions to new format
for session in important_sessions.txt; do
  python tools/transcript_manager.py convert $session --from claude --to codex
done

# 3. Verify conversion
python tools/transcript_manager.py list --backend codex
```

## Troubleshooting Transcripts

### Missing Transcripts

**Problem**: Can't find expected transcripts
**Solutions**:
```bash
# Check both global and local locations
ls ~/.codex/transcripts/
ls .codex/transcripts/
ls .data/transcripts/

# Use transcript manager to scan all locations
python tools/transcript_manager.py list --backend auto --verbose

# Check if sessions exist but transcripts weren't generated
ls ~/.codex/sessions/
python tools/codex_transcripts_builder.py --session-id <id> --verbose
```

### Session ID Mismatches

**Problem**: Session ID doesn't match between systems
**Solutions**:
```bash
# Use fuzzy matching (prefix search)
python tools/transcript_manager.py load a1b2c3  # Matches a1b2c3d4-e5f6-...

# List with session ID details
python tools/transcript_manager.py list --show-ids

# Check both short and full ID formats
grep -r "a1b2c3" ~/.codex/transcripts/
grep -r "a1b2c3d4-e5f6" .data/transcripts/
```

### Timezone Confusion

**Problem**: Timestamps don't match expected times
**Solutions**:
```bash
# Check timezone settings in Codex
python tools/codex_transcripts_builder.py --timezone "America/New_York"

# Convert existing transcripts to local timezone
python tools/transcript_manager.py convert session-id --timezone-convert local

# Check system timezone
date
echo $TZ
```

### Large Transcript Handling

**Problem**: Transcripts are too large to process
**Solutions**:
```bash
# Use compact format for large sessions
python tools/codex_transcripts_builder.py --output-format compact

# Split large transcripts by time
python tools/transcript_manager.py split large-session --by-date

# Search instead of loading full content
python tools/transcript_manager.py search "specific topic" --session large-session
```

## Real Transcript Examples

### Claude Code Transcript Excerpt
```text
# Amplifier Claude Code Transcript Export
# Exported: 2024-01-01 12:00:00 PST
# Session ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890

================================================================================

[USER]: I need help refactoring this Python function to be more efficient.

[ASSISTANT]: I'd be happy to help you refactor your Python function for better efficiency. Could you please share the function you'd like me to review?

[TOOL USE: file_reader]
{
  "path": "src/utils.py",
  "lines": [10, 25]
}

[TOOL RESULT]
def process_data(items):
    result = []
    for item in items:
        if item.status == 'active':
            processed = item.value * 2
            result.append(processed)
    return result

[ASSISTANT]: I can see your function processes a list of items. Here are some efficiency improvements...
```

### Codex transcript.md Excerpt
```markdown
# Codex Session Transcript

**Session ID:** a1b2c3d4-e5f6-7890-abcd-ef1234567890
**Started:** 2024-01-01T10:00:00-08:00
**Working Directory:** /home/user/amplifier-project
**Exported:** 2024-01-01T12:00:00-08:00

---

## Conversation

- **User** · 2024-01-01 10:00:00
  I need help refactoring this Python function to be more efficient.

- **Assistant** · 2024-01-01 10:00:01
  I'd be happy to help you refactor your Python function for better efficiency. Could you please share the function you'd like me to review?

- **Tool Call (file_reader)** · 2024-01-01 10:00:02
  ```json
  {
    "path": "src/utils.py",
    "lines": [10, 25],
    "call_id": "call_abc123"
  }
  ```

- **Tool Result** · 2024-01-01 10:00:03
  *Call ID: call_abc123*
  ```python
  def process_data(items):
      result = []
      for item in items:
          if item.status == 'active':
              processed = item.value * 2
              result.append(processed)
      return result
  ```

- **Assistant** · 2024-01-01 10:00:04
  I can see your function processes a list of items. Here are some efficiency improvements...
```

### Codex transcript_extended.md Excerpt
```markdown
# Codex Session Transcript (Extended)

**Session ID:** a1b2c3d4-e5f6-7890-abcd-ef1234567890
**Started:** 2024-01-01T10:00:00-08:00
**Event Count:** 127
**Message Count:** 45
**Tool Usage Count:** 12

---

## Raw Events

### Event 1 · 2024-01-01T10:00:00.123456-08:00
**Type:** user_message
**Source:** history
```json
{
  "timestamp": "2024-01-01T10:00:00.123456-08:00",
  "type": "user_message",
  "content": {
    "text": "I need help refactoring this Python function to be more efficient."
  },
  "metadata": {
    "input_tokens": 156,
    "context_window": 8192
  }
}
```

### Event 2 · 2024-01-01T10:00:01.234567-08:00
**Type:** assistant_message
**Source:** history
```json
{
  "timestamp": "2024-01-01T10:00:01.234567-08:00",
  "type": "assistant_message",
  "content": {
    "text": "I'd be happy to help you refactor your Python function for better efficiency. Could you please share the function you'd like me to review?"
  },
  "metadata": {
    "output_tokens": 234,
    "reasoning_time_ms": 1250
  }
}
```

---

## Summary Statistics
- **Total Events:** 127
- **User Messages:** 23
- **Assistant Messages:** 22
- **Tool Calls:** 12
- **Tool Results:** 12
- **Thinking Blocks:** 8
- **Session Duration:** 45 minutes
- **Total Tokens:** 12,543 (input: 8,231, output: 4,312)
```

These examples highlight the key visual and structural differences between the formats, helping users understand what to expect when working with each backend.

## Key Differences from Claude Code

| Aspect | Claude Code | Codex |
|--------|-------------|-------|
| **Hooks** | Native Python hooks | MCP servers |
| **Commands** | Slash commands (`/architect`) | Natural language or MCP tools |
| **Sessions** | VS Code internal storage | `~/.codex/sessions/` |
| **Config** | JSON in `.claude/settings.json` | TOML in `.codex/config.toml` |
| **Agent Spawning** | Task tool | `codex exec` command |
| **Integration** | VS Code extension | Standalone CLI |

## Getting Started

### Prerequisites

- Codex CLI installed and configured
- Project dependencies installed (`make install`)
- Virtual environment activated

### Quick Start with Wrapper Script

The easiest way to use Codex with Amplifier is via the wrapper script:

```bash
# Make wrapper executable (first time only)
chmod +x ../amplify-codex.sh

# Start Codex with Amplifier integration
../amplify-codex.sh

# The wrapper will:
# 1. Initialize session and load memories
# 2. Start Codex with MCP servers
# 3. Display available tools and workflow guidance
# 4. Clean up and save memories when you exit
```

### Manual Workflow (Without Wrapper)

If you prefer to manage sessions manually:

```bash
# 1. Initialize session
uv run python .codex/tools/session_init.py --prompt "Working on feature X"

# 2. Start Codex
codex --profile development

# 3. Use MCP tools during session
# - initialize_session (if not run manually)
# - check_code_quality after changes
# - save_current_transcript before ending
# - finalize_session to save memories

# 4. Clean up after session
uv run python .codex/tools/session_cleanup.py
```

## Session Management Tools

Amplifier provides standalone tools for session initialization and cleanup:

### session_init.py

Loads relevant memories before starting a Codex session.

**Usage:**
```bash
# Basic usage (uses default context)
uv run python .codex/tools/session_init.py

# With specific context
uv run python .codex/tools/session_init.py --prompt "Refactoring authentication module"

# Custom output location
uv run python .codex/tools/session_init.py --output ./my_context.md

# Verbose logging
uv run python .codex/tools/session_init.py --verbose
```

**Output:**
- `.codex/session_context.md` - Formatted memories for reference
- `.codex/session_init_metadata.json` - Metadata for programmatic access
- `.codex/logs/session_init.log` - Detailed logs

**Environment Variables:**
- `MEMORY_SYSTEM_ENABLED` - Enable/disable memory loading (default: true)
- `CODEX_SESSION_CONTEXT` - Default context if no --prompt provided

### session_cleanup.py

Extracts memories and exports transcript after a Codex session.

**Usage:**
```bash
# Basic usage (auto-detects latest session)
uv run python .codex/tools/session_cleanup.py

# Specific session
uv run python .codex/tools/session_cleanup.py --session-id a1b2c3d4

# Skip memory extraction
uv run python .codex/tools/session_cleanup.py --no-memory

# Custom transcript format
uv run python .codex/tools/session_cleanup.py --format extended

# Verbose logging
uv run python .codex/tools/session_cleanup.py --verbose
```

**Output:**
- `.codex/transcripts/<session-dir>/` - Exported transcript files
- `.codex/session_cleanup_metadata.json` - Cleanup metadata
- `.codex/logs/session_cleanup.log` - Detailed logs
- Updated memory store in `.data/memories/`

**Environment Variables:**
- `MEMORY_SYSTEM_ENABLED` - Enable/disable memory extraction (default: true)
- `CODEX_SESSION_ID` - Session to process if not provided via --session-id

### Wrapper Script (amplify-codex.sh)

Orchestrates session initialization, Codex execution, and cleanup.

**Usage:**
```bash
# Basic usage
./amplify-codex.sh

# With specific profile
./amplify-codex.sh --profile ci

# Skip initialization
./amplify-codex.sh --no-init

# Skip cleanup
./amplify-codex.sh --no-cleanup

# Show help
./amplify-codex.sh --help
```

**Features:**
- Validates prerequisites (Codex CLI, uv, virtual environment)
- Runs session_init.py before starting Codex
- Displays user guidance with available MCP tools
- Runs session_cleanup.py after Codex exits
- Handles errors gracefully with clear messages
- Logs all operations for debugging

**Environment Variables:**
- `AMPLIFIER_BACKEND` - Set to "codex" (automatically set by wrapper)
- `CODEX_PROFILE` - Profile to use (default: development)
- `MEMORY_SYSTEM_ENABLED` - Enable/disable memory system (default: true)

## Troubleshooting

**MCP Server Connection Issues**:
- Verify Python environment: `uv run python --version`
- Check server script paths in `config.toml`
- Review server logs in `.codex/logs/`
- Ensure amplifier modules are importable

**Server-Specific Issues**:
- **Session Manager**: Check `MEMORY_SYSTEM_ENABLED` environment variable
- **Quality Checker**: Verify `Makefile` exists and has `check` target
- **Transcript Saver**: Ensure transcript export tools are available

**Environment Variable Problems**:
- Ensure `AMPLIFIER_ROOT` is set correctly
- Verify virtual environment activation
- Check `env_allow` section in `config.toml`

**Agent Execution Failures**:
- Confirm agent files exist in `.codex/agents/`
- Verify execution timeout settings
- Check working directory configuration

**Viewing Server Logs**:
```bash
# View all server logs
tail -f .codex/logs/*.log

# View specific server log
tail -f .codex/logs/session_manager.log
```

### Session Management Issues

**session_init.py fails:**
- Check memory system is enabled: `echo $MEMORY_SYSTEM_ENABLED`
- Verify memory data exists: `ls .data/memories/`
- Check logs: `cat .codex/logs/session_init.log`
- Run with --verbose for detailed output

**session_cleanup.py can't find session:**
- Check Codex session directory: `ls ~/.codex/sessions/`
- Provide explicit session ID: `--session-id <id>`
- Verify session has history.jsonl file
- Check logs: `cat .codex/logs/session_cleanup.log`

**Wrapper script issues:**
- Ensure script is executable: `chmod +x amplify-codex.sh`
- Check Codex is installed: `codex --version`
- Verify uv is available: `uv --version`
- Check virtual environment: `ls .venv/`
- Review wrapper output for specific error messages

**Memory extraction timeout:**
- Large sessions may timeout (60 second limit)
- Run cleanup manually with --no-memory to skip extraction
- Process session in smaller chunks if possible
- Check for memory system performance issues

## Future Development

Phase 3 (MCP servers) is now complete. Subsequent phases will implement:

- Wrapper scripts for enhanced CLI integration
- Backend abstraction layer for unified API
- Agent migration from Claude Code to Codex
- Advanced cross-backend features

## Performance Notes

- **Server Startup**: Typically <1 second with FastMCP
- **Tool Invocation**: Minimal overhead for MCP protocol
- **Memory System**: Performance depends on dataset size
- **Quality Checks**: Run only when needed to avoid delays

## Integration Examples

### Code Review Workflow
1. Start Codex with review profile
2. Invoke `check_code_quality` after changes
3. Invoke `save_current_transcript` for documentation
4. Review combined quality report and transcript

### Session Continuity
1. Start new session with `initialize_session`
2. Work on tasks
3. End session with `finalize_session` to save context
4. Next session loads relevant memories automatically

### Batch Processing
1. Use `list_available_sessions` to find project sessions
2. Invoke `save_project_transcripts` for bulk export
3. Use `convert_transcript_format` for standardization

### Complete Session with Wrapper

```bash
# Start session with wrapper
./amplify-codex.sh --profile development

# Wrapper automatically:
# 1. Loads 5 relevant memories
# 2. Starts Codex with all MCP servers
# 3. Displays tool guidance

# During session, use MCP tools:
codex> check_code_quality with file_paths ["src/auth.py"]
codex> save_current_transcript with format "both"

# Exit Codex (Ctrl+D or exit command)

# Wrapper automatically:
# 1. Extracts memories from session
# 2. Exports transcript to .codex/transcripts/
# 3. Displays summary
```

## Design Principles

Following the project's core philosophy from `AGENTS.md`:

- **Minimal Intrusion**: All Codex integration stays within `.codex/` directory
- **Cross-platform Compatibility**: Works on Windows, macOS, and Linux
- **Fail Gracefully**: Degrades gracefully when MCP servers are unavailable
- **User Control**: Extensive configuration options and profile support
- **Interoperability**: Maintains compatibility with existing Claude Code workflows

## Related Documentation

- [`AGENTS.md`](../AGENTS.md) - AI Assistant guidance and sub-agent optimization
- [`tools/codex_transcripts_builder.py`](../tools/codex_transcripts_builder.py) - Existing Codex transcript integration
- [`.claude/README.md`](../.claude/README.md) - Claude Code integration documentation
- [`docs/`](../docs/) - Additional project documentation

For questions or issues with Codex integration, refer to the project's main documentation or create an issue in the repository.