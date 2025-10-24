Codex CLI ──── stdio ──── MCP Server Process
    │                           │
    ├── Tool Call Request       ├── FastMCP Framework
    ├── JSON-RPC Messages       ├── Tool Registration
    └── Response Handling       └── Error Management
```

**Key Characteristics**:
- **Stateless communication**: Each tool call is independent
- **JSON-RPC protocol**: Structured request/response format
- **Subprocess lifecycle**: Servers start/stop with Codex sessions
- **Error isolation**: Server crashes don't affect Codex

### FastMCP Framework

We use [FastMCP](https://github.com/modelcontextprotocol/python-sdk) for server implementation:

**Why FastMCP?**
- **Minimal boilerplate**: Decorators for tool registration
- **Automatic protocol handling**: No manual JSON-RPC implementation
- **High-level API**: Focus on tool logic, not transport details
- **Active maintenance**: Official Anthropic-supported SDK
- **Stdio built-in**: Automatic subprocess communication setup

**Basic Server Structure**:
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("server_name")

@mcp.tool()
def my_tool(param: str) -> dict:
    # Tool implementation
    return {"result": "success"}

if __name__ == "__main__":
    mcp.run()  # Handles stdio automatically
```

### Shared Base Module

All servers inherit from `base.py` which provides:

**Logging Infrastructure** (`MCPLogger`):
- Structured JSON logging with rotation
- Log levels: `info`, `debug`, `error`, `exception`
- Automatic cleanup of old logs
- Consistent log format across servers

**Base Server Class** (`AmplifierMCPServer`):
- Project root detection and path setup
- Amplifier module import handling
- Common error handling wrappers
- Health check tool inheritance

**Utility Functions**:
- `get_project_root()` - Find project root via markers
- `setup_amplifier_path()` - Add amplifier to Python path
- `safe_import()` - Graceful module import with fallbacks
- Response builders: `success_response()`, `error_response()`

### Server Lifecycle

1. **Initialization**: Codex spawns server subprocess
2. **Registration**: Server registers tools with MCP protocol
3. **Tool Calls**: Codex invokes tools via JSON-RPC over stdio
4. **Response**: Server returns structured results
5. **Termination**: Server exits when Codex session ends

## Server Descriptions

### 1. Session Manager (`session_manager/server.py`)

**Purpose**: Integrates memory system at session boundaries, loading relevant context at start and extracting/storing memories at end.

#### Tools

**`initialize_session`** - Load relevant memories (replaces SessionStart hook)
- **Input**: `{"prompt": str, "context": Optional[str]}`
- **Output**: `{"memories": [...], "metadata": {"memoriesLoaded": int, "source": "amplifier_memory"}}`
- **Behavior**: Searches for relevant memories using prompt, loads recent context
- **Usage**: Call at session start to provide context from previous work

**`finalize_session`** - Extract and store memories (replaces Stop/SubagentStop hooks)
- **Input**: `{"messages": List[dict], "context": Optional[str]}`
- **Output**: `{"metadata": {"memoriesExtracted": int, "source": "amplifier_extraction"}}`
- **Behavior**: Extracts memories from conversation, stores in memory system
- **Usage**: Call at session end to capture learnings

**`health_check`** - Verify server and memory system status
- **Input**: `{}`
- **Output**: `{"status": "healthy", "memory_enabled": bool, "modules_available": [...]}`
- **Behavior**: Checks amplifier module imports and memory system configuration
- **Usage**: Verify setup before using other tools

#### Usage Examples

```bash
# Load context at session start
codex> initialize_session with prompt "Working on user authentication"

# Extract memories at session end
codex> finalize_session with recent conversation messages

# Check system status
codex> health_check
```

#### Configuration

- **Environment Variables**:
  - `MEMORY_SYSTEM_ENABLED=true` - Enable/disable memory operations
- **Dependencies**: `amplifier.memory`, `amplifier.search`, `amplifier.extraction`

### 2. Quality Checker (`quality_checker/server.py`)

**Purpose**: Runs code quality checks after file modifications, ensuring code standards are maintained.

#### Tools

**`check_code_quality`** - Run make check (replaces PostToolUse hook)
- **Input**: `{"file_paths": List[str], "tool_name": Optional[str], "cwd": Optional[str]}`
- **Output**: `{"passed": bool, "output": str, "issues": [...], "metadata": {...}}`
- **Behavior**: Finds project root, runs `make check`, parses results
- **Usage**: Call after editing files to validate changes

**`run_specific_checks`** - Run individual tools (ruff, pyright, pytest)
- **Input**: `{"check_type": str, "file_paths": Optional[List[str]], "args": Optional[List[str]]}`
- **Output**: `{"passed": bool, "output": str, "tool": str, "issues": [...]}`
- **Behavior**: Runs specific linter/type checker/test tool via `uv run`
- **Usage**: Run targeted checks (e.g., just linting or just tests)

**`validate_environment`** - Check development environment setup
- **Input**: `{}`
- **Output**: `{"valid": bool, "issues": [...], "environment": {...}}`
- **Behavior**: Verifies virtual environment, uv availability, Makefile presence
- **Usage**: Diagnose setup issues before running checks

#### Usage Examples

```bash
# Run full quality check after editing
codex> check_code_quality with file_paths ["src/main.py", "tests/test_main.py"]

# Run just linting
codex> run_specific_checks with check_type "lint"

# Check environment setup
codex> validate_environment
```

#### Configuration

- **Project Requirements**: `Makefile` with `check` target
- **Virtual Environment**: Uses `uv run` for tool execution
- **Worktree Support**: Handles git worktree virtual environments

### 3. Transcript Saver (`transcript_saver/server.py`)

**Purpose**: Manages session transcripts, providing export capabilities and format conversion between Claude Code and Codex formats.

#### Tools

**`save_current_transcript`** - Export current session (replaces PreCompact hook)
- **Input**: `{"session_id": Optional[str], "format": str = "both", "output_dir": Optional[str]}`
- **Output**: `{"exported_path": str, "metadata": {"file_size": int, "event_count": int}}`
- **Behavior**: Exports current Codex session to specified format(s)
- **Usage**: Save session before ending work

**`save_project_transcripts`** - Batch export project sessions
- **Input**: `{"project_dir": str, "format": str = "standard", "incremental": bool = True}`
- **Output**: `{"exported_sessions": [...], "skipped": [...], "metadata": {...}}`
- **Behavior**: Exports all project-related sessions, with incremental option
- **Usage**: Bulk export for project documentation

**`list_available_sessions`** - Discover exportable sessions
- **Input**: `{"project_only": bool = False, "limit": int = 10}`
- **Output**: `{"sessions": [...], "total_count": int, "project_sessions": int}`
- **Behavior**: Lists Codex sessions with metadata, optionally filtered by project
- **Usage**: Find sessions to export or analyze

**`convert_transcript_format`** - Convert between formats
- **Input**: `{"session_id": str, "from_format": str, "to_format": str, "output_path": Optional[str]}`
- **Output**: `{"converted_path": str, "metadata": {"original_format": str, "target_format": str}}`
- **Behavior**: Converts between Claude Code and Codex transcript formats
- **Usage**: Standardize transcript formats for analysis

#### Usage Examples

```bash
# Save current session
codex> save_current_transcript with format "both"

# Export all project transcripts
codex> save_project_transcripts with project_dir "." and incremental true

# List recent sessions
codex> list_available_sessions with limit 5

# Convert format for compatibility
codex> convert_transcript_format with session_id "abc123" from "codex" to "claude"
```

#### Configuration

- **Output Directories**: Default to `.codex/transcripts/` (project-local)
- **Format Options**: "standard", "extended", "both", "compact"
- **Session Detection**: Scans `~/.codex/sessions/` for available sessions

## Development Guide

### Local Testing with MCP Dev

Test servers locally using FastMCP's development mode:

```bash
# Test session manager
cd .codex/mcp_servers/session_manager
uv run mcp dev server.py

# Test quality checker
cd .codex/mcp_servers/quality_checker
uv run mcp dev server.py

# Test transcript saver
cd .codex/mcp_servers/transcript_saver
uv run mcp dev server.py
```

**MCP Dev Features**:
- Interactive tool testing
- Request/response inspection
- Error debugging
- Hot reload on code changes

### Debugging with MCP Inspector

Use the MCP Inspector for advanced debugging:

```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Run server with inspector
mcp-inspector uv run python .codex/mcp_servers/session_manager/server.py
```

**Inspector Capabilities**:
- Real-time message monitoring
- Tool call tracing
- Performance profiling
- Error analysis

### Adding New Tools

To add tools to existing servers:

1. **Define tool function** in `server.py`:
```python
@mcp.tool()
def new_tool_name(param1: str, param2: int = 0) -> dict:
    """Tool description for Codex"""
    # Implementation
    return {"result": "success"}
```

2. **Add comprehensive docstring** (used by Codex for tool descriptions)

3. **Handle errors gracefully** using base utilities

4. **Test locally** with `mcp dev`

5. **Update documentation** in this README

### Creating New MCP Servers

Follow the established pattern:

1. **Create directory**: `.codex/mcp_servers/new_server/`

2. **Add `__init__.py`**: Empty package marker

3. **Create `server.py`**:
```python
from mcp.server.fastmcp import FastMCP
from ..base import MCPLogger, AmplifierMCPServer

logger = MCPLogger("new_server")
mcp = FastMCP("amplifier_new_server")

class NewServer(AmplifierMCPServer):
    pass

@mcp.tool()
def example_tool() -> dict:
    return {"status": "ok"}

if __name__ == "__main__":
    mcp.run()
```

4. **Update config.toml**: Add server configuration

5. **Update profiles**: Enable in appropriate profiles

## Testing Section

### Unit Testing Approach

Test MCP tools independently of Codex:

```python
# Example test structure
import pytest
from unittest.mock import patch, MagicMock

def test_initialize_session_with_memories():
    # Mock amplifier modules
    with patch('amplifier.memory.MemoryStore') as mock_store:
        mock_store.return_value.get_all.return_value = [...]
        mock_store.return_value.search_recent.return_value = [...]

        # Test tool function directly
        result = initialize_session("test prompt")

        assert result["metadata"]["memoriesLoaded"] > 0
```

**Testing Strategy**:
- Mock external dependencies (amplifier modules, subprocess, file system)
- Test tool functions directly (not through MCP protocol)
- Use `pytest-asyncio` for async tools
- Cover error paths and edge cases

### Integration Testing with Codex

Test end-to-end with Codex:

```bash
# 1. Start Codex with test profile
codex --profile test --config .codex/config.toml

# 2. Test tool invocation
initialize_session with prompt "test"

# 3. Verify results and logs
tail -f .codex/logs/session_manager.log
```

**Integration Test Checklist**:
- Server startup without errors
- Tool registration with Codex
- Parameter passing and validation
- Response formatting
- Error handling in Codex UI

### Manual Testing Procedures

**Session Manager Testing**:
1. Start Codex with session manager enabled
2. Call `health_check` - verify memory system status
3. Call `initialize_session` - check memory loading
4. Work in session, then call `finalize_session`
5. Verify memories were extracted and stored

**Quality Checker Testing**:
1. Create/modify a Python file
2. Call `check_code_quality` - verify make check runs
3. Call `run_specific_checks` with different check_types
4. Call `validate_environment` - verify setup detection

**Transcript Saver Testing**:
1. Work in a Codex session
2. Call `save_current_transcript` - verify export
3. Call `list_available_sessions` - verify session discovery
4. Call `convert_transcript_format` - verify conversion

### Troubleshooting Common Issues

**Test Failures**:
- Check mock setup - ensure all external calls are mocked
- Verify import paths in test environment
- Check async/await usage in tool functions

**Integration Issues**:
- Verify config.toml server configuration
- Check server logs for startup errors
- Ensure amplifier modules are available in test environment

## Comparison with Claude Code Hooks

### Hook vs MCP Tool Mappings

| Claude Code Hook | MCP Server Tool | Trigger | Invocation |
|------------------|-----------------|---------|------------|
| `SessionStart.py` | `initialize_session` | Session start | Explicit |
| `Stop.py` | `finalize_session` | Session end | Explicit |
| `PostToolUse.py` | `check_code_quality` | After tool use | Explicit |
| `PreCompact.py` | `save_current_transcript` | Before compact | Explicit |

### Key Differences

**Automatic vs Explicit**:
- **Hooks**: Trigger automatically on events (session start, tool use, etc.)
- **MCP Tools**: Must be invoked manually by user or configured workflows

**Input/Output**:
- **Hooks**: Receive JSON via stdin, write JSON to stdout
- **MCP Tools**: Receive structured parameters, return typed responses

**Error Handling**:
- **Hooks**: Can break session if they fail critically
- **MCP Tools**: Isolated failures don't affect Codex operation

**Configuration**:
- **Hooks**: Configured in `.claude/settings.json`
- **MCP Servers**: Configured in `.codex/config.toml`

### Workflow Adaptations

**Claude Code Workflow**:
```
Session Start → Hook loads memories automatically
Edit Code → Hook runs quality checks automatically
Session End → Hook extracts memories automatically
Compact → Hook saves transcript automatically
```

**Codex Workflow**:
```
Session Start → Manually call initialize_session
Edit Code → Manually call check_code_quality
Session End → Manually call finalize_session
End Session → Manually call save_current_transcript
```

**Recommended Integration**:
- Create Codex "macros" or custom commands for common sequences
- Configure automatic tool calls in development workflows
- Use session templates that include tool invocations

## Configuration Reference

### Environment Variables

| Variable | Purpose | Default | Used By |
|----------|---------|---------|---------|
| `MEMORY_SYSTEM_ENABLED` | Enable/disable memory operations | `false` | session_manager |
| `AMPLIFIER_ROOT` | Project root directory | Auto-detected | All servers |
| `VIRTUAL_ENV` | Python virtual environment | System default | quality_checker |
| `PATH` | System executable path | System PATH | All servers |

### Config.toml Server Entries

```toml
[mcp_servers.amplifier_session]
command = "uv"
args = ["run", "python", ".codex/mcp_servers/session_manager/server.py"]
env = { "MEMORY_SYSTEM_ENABLED" = "true" }

[mcp_servers.amplifier_quality]
command = "uv"
args = ["run", "python", ".codex/mcp_servers/quality_checker/server.py"]

[mcp_servers.amplifier_transcripts]
command = "uv"
args = ["run", "python", ".codex/mcp_servers/transcript_saver/server.py"]
```

### Enabling/Disabling Servers

**Per-Profile Configuration**:
```toml
[profiles.development]
mcp_servers = ["amplifier_session", "amplifier_quality", "amplifier_transcripts"]

[profiles.ci]
mcp_servers = ["amplifier_quality"]

[profiles.review]
mcp_servers = ["amplifier_quality", "amplifier_transcripts"]