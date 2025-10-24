# Verify Codex CLI installation
codex --version

# Verify uv package manager
uv --version

# Verify Python version
python --version

# Verify project setup
make check
```

### First-Time Setup

1. **Clone and setup the project:**
```bash
git clone <repository-url>
cd amplifier-project
make install
```

2. **Configure Codex:**
```bash
# Initialize Codex configuration
codex --config .codex/config.toml

# Verify configuration
codex --profile development --help
```

3. **Test MCP servers:**
```bash
# Test session manager
uv run python .codex/mcp_servers/session_manager/server.py --help

# Test quality checker
uv run python .codex/mcp_servers/quality_checker/server.py --help

# Test transcript saver
uv run python .codex/mcp_servers/transcript_saver/server.py --help
```

### Hello World Example

```bash
# Start Codex with Amplifier integration
./amplify-codex.sh

# In Codex session, use MCP tools:
codex> initialize_session with prompt "Hello world project"

codex> check_code_quality with file_paths ["hello.py"]

codex> save_current_transcript with format "both"

# Exit Codex (Ctrl+D)
```

The wrapper script automatically handles session initialization, MCP server management, and cleanup.

## Architecture Overview

### MCP Server Architecture

Codex uses the Model Context Protocol (MCP) for tool integration, where each tool is implemented as a separate server process communicating via stdio with JSON-RPC messages.

**MCP Server Components:**
- **FastMCP Framework**: Minimal boilerplate for server implementation
- **Stdio Communication**: JSON-RPC over standard input/output
- **Tool Registration**: Decorators for automatic tool discovery
- **Error Isolation**: Server failures don't crash Codex

**Server Lifecycle:**
1. Codex spawns server subprocess
2. Server registers tools via MCP protocol
3. Codex invokes tools with JSON-RPC calls
4. Server processes requests and returns responses
5. Server exits when Codex session ends

### Backend Abstraction Layer

The `amplifier/core/backend.py` module provides a unified API for both Claude Code and Codex backends:

```python
from amplifier import get_backend

# Get appropriate backend based on AMPLIFIER_BACKEND env var
backend = get_backend()

# Unified API regardless of backend
result = backend.initialize_session("Working on feature")
result = backend.run_quality_checks(["file.py"])
result = backend.export_transcript()
```

**Key Benefits:**
- **Backend Agnostic**: Same code works with both backends
- **Easy Switching**: Change backends via environment variable
- **Testability**: Mock backends for comprehensive testing
- **Extensibility**: Add new backends without changing code

### Wrapper Script

The `amplify-codex.sh` bash script provides hook-like functionality for Codex:

**Features:**
- Validates prerequisites (Codex CLI, uv, virtual environment)
- Runs session initialization automatically
- Starts Codex with appropriate profile
- Displays MCP tool guidance
- Handles session cleanup on exit
- Provides error handling and user feedback

**Usage:**
```bash
# Full workflow automation
./amplify-codex.sh --profile development

# Skip initialization
./amplify-codex.sh --no-init

# Custom profile
./amplify-codex.sh --profile ci
```

### Session Lifecycle

**With Wrapper Script (Recommended):**
1. User runs `./amplify-codex.sh`
2. Script validates environment
3. Script runs `session_init.py` (loads memories)
4. Script starts Codex with MCP servers
5. User works in Codex session
6. User exits Codex
7. Script runs `session_cleanup.py` (extracts memories, exports transcript)

**Manual Workflow:**
1. Run `session_init.py` manually
2. Start Codex: `codex --profile development`
3. Use MCP tools explicitly during session
4. Run `session_cleanup.py` manually

**MCP Tool Integration:**
- `initialize_session` - Load context at start
- `check_code_quality` - Validate changes during work
- `save_current_transcript` - Export progress
- `finalize_session` - Extract memories at end

## Configuration Guide

### config.toml Structure

Codex uses TOML format for configuration, stored in `.codex/config.toml`:

```toml
# Model and basic settings
model = "claude-3-5-sonnet-20241022"
approval_policy = "on-request"

# MCP server configurations
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

# Profile definitions
[profiles.development]
mcp_servers = ["amplifier_session", "amplifier_quality", "amplifier_transcripts"]

[profiles.ci]
mcp_servers = ["amplifier_quality"]

[profiles.review]
mcp_servers = ["amplifier_quality", "amplifier_transcripts"]
```

### Profiles

**Development Profile:**
- **Purpose**: Full-featured development workflow
- **Servers**: All three MCP servers enabled
- **Use Case**: Interactive development with memory system and quality checks

**CI Profile:**
- **Purpose**: Automated quality assurance
- **Servers**: Quality checker only
- **Use Case**: CI/CD pipelines, automated testing

**Review Profile:**
- **Purpose**: Code review and documentation
- **Servers**: Quality checker + transcript saver
- **Use Case**: Code reviews, documentation generation

### Environment Variables

**Core Variables:**
- `AMPLIFIER_BACKEND=codex` - Select Codex backend
- `CODEX_PROFILE=development` - Default profile to use
- `MEMORY_SYSTEM_ENABLED=true` - Enable/disable memory system

**MCP Server Variables:**
- `AMPLIFIER_ROOT` - Project root directory (auto-detected)
- `VIRTUAL_ENV` - Python virtual environment path
- `PATH` - System executable path

**Configuration Overrides:**
```bash
# Override profile
CODEX_PROFILE=ci ./amplify-codex.sh

# Disable memory system
MEMORY_SYSTEM_ENABLED=false codex --profile development

# Custom project root
AMPLIFIER_ROOT=/custom/path codex
```

### Configuration Precedence

1. **Command Line Arguments**: Highest precedence (`--profile ci`)
2. **Environment Variables**: Override config file (`CODEX_PROFILE=ci`)
3. **Config File**: `.codex/config.toml` settings
4. **Defaults**: Built-in fallback values

### Advanced Configuration

**Custom MCP Server:**
```toml
[mcp_servers.custom_tool]
command = "python"
args = ["custom_server.py"]
env = { "CUSTOM_CONFIG" = "value" }
```

**Profile Inheritance:**
```toml
[profiles.base]
mcp_servers = ["amplifier_session"]

[profiles.extended]
mcp_servers = ["amplifier_session", "amplifier_quality", "custom_tool"]
```

## MCP Tools Reference

### Session Manager Tools

#### `initialize_session`

Load relevant memories at session start.

**Parameters:**
- `prompt` (string): Session prompt for memory search
- `context` (optional string): Additional context information

**Returns:**
```json
{
  "memories": [
    {
      "content": "Previous work on authentication...",
      "timestamp": "2024-01-01T10:00:00Z",
      "source": "session_123"
    }
  ],
  "metadata": {
    "memoriesLoaded": 5,
    "source": "amplifier_memory"
  }
}
```

**Usage Examples:**
```bash
# Basic initialization
codex> initialize_session with prompt "Working on user authentication"

# With additional context
codex> initialize_session with prompt "Refactoring API" and context "Following REST principles"
```

**Error Handling:**
- Returns empty memories array if memory system disabled
- Graceful degradation if memory search fails
- Logs errors but doesn't break session

#### `finalize_session`

Extract and store memories from session.

**Parameters:**
- `messages` (array): Session conversation messages
- `context` (optional string): Additional context

**Returns:**
```json
{
  "metadata": {
    "memoriesExtracted": 3,
    "source": "amplifier_extraction"
  }
}
```

**Usage Examples:**
```bash
# Extract memories from conversation
codex> finalize_session with recent conversation messages

# With context
codex> finalize_session with messages and context "Completed authentication refactor"
```

**Error Handling:**
- Continues if extraction fails (logs error)
- Partial success if some memories extracted
- Timeout protection (60 second limit)

#### `health_check`

Verify server and memory system status.

**Parameters:** None

**Returns:**
```json
{
  "status": "healthy",
  "memory_enabled": true,
  "modules_available": ["memory", "search", "extraction"]
}
```

**Usage Examples:**
```bash
codex> health_check
```

### Quality Checker Tools

#### `check_code_quality`

Run make check on specified files.

**Parameters:**
- `file_paths` (array): Files to check
- `tool_name` (optional string): Specific tool to run
- `cwd` (optional string): Working directory

**Returns:**
```json
{
  "passed": true,
  "output": "All checks passed\nLint: OK\nType check: OK\nTests: 15 passed",
  "issues": [],
  "metadata": {
    "tools_run": ["ruff", "pyright", "pytest"],
    "execution_time": 2.3
  }
}
```

**Usage Examples:**
```bash
# Check specific files
codex> check_code_quality with file_paths ["src/auth.py", "tests/test_auth.py"]

# Check after editing
codex> check_code_quality with file_paths ["modified_file.py"]
```

**Error Handling:**
- Continues with partial results if some tools fail
- Captures stderr output in issues array
- Handles missing Makefile gracefully

#### `run_specific_checks`

Run individual quality tools.

**Parameters:**
- `check_type` (string): Type of check ("lint", "type", "test")
- `file_paths` (optional array): Specific files to check
- `args` (optional array): Additional arguments

**Returns:**
```json
{
  "passed": true,
  "output": "15 tests passed, 0 failed",
  "tool": "pytest",
  "issues": []
}
```

**Usage Examples:**
```bash
# Run only linting
codex> run_specific_checks with check_type "lint"

# Run tests on specific files
codex> run_specific_checks with check_type "test" and file_paths ["test_auth.py"]
```

#### `validate_environment`

Check development environment setup.

**Parameters:** None

**Returns:**
```json
{
  "valid": true,
  "issues": [],
  "environment": {
    "venv_exists": true,
    "makefile_exists": true,
    "uv_available": true
  }
}
```

### Transcript Saver Tools

#### `save_current_transcript`

Export current session transcript.

**Parameters:**
- `session_id` (optional string): Specific session ID
- `format` (string): Export format ("standard", "extended", "both", "compact")
- `output_dir` (optional string): Custom output directory

**Returns:**
```json
{
  "exported_path": ".codex/transcripts/2024-01-01-10-00-AM__project__abc123/",
  "metadata": {
    "file_size": 15432,
    "event_count": 127,
    "format": "both"
  }
}
```

**Usage Examples:**
```bash
# Save current session
codex> save_current_transcript with format "both"

# Save with custom directory
codex> save_current_transcript with output_dir "./exports" and format "compact"
```

#### `save_project_transcripts`

Batch export project sessions.

**Parameters:**
- `project_dir` (string): Project directory
- `format` (string): Export format
- `incremental` (boolean): Skip already exported sessions

**Returns:**
```json
{
  "exported_sessions": ["session1", "session2"],
  "skipped": ["already_exported"],
  "metadata": {
    "total_sessions": 15,
    "exported_count": 2
  }
}
```

#### `list_available_sessions`

Discover exportable sessions.

**Parameters:**
- `project_only` (boolean): Filter to current project
- `limit` (integer): Maximum sessions to return

**Returns:**
```json
{
  "sessions": [
    {
      "session_id": "abc123",
      "start_time": "2024-01-01T10:00:00Z",
      "cwd": "/project",
      "message_count": 45
    }
  ],
  "total_count": 15,
  "project_sessions": 8
}
```

#### `convert_transcript_format`

Convert between transcript formats.

**Parameters:**
- `session_id` (string): Session to convert
- `from_format` (string): Source format
- `to_format` (string): Target format
- `output_path` (optional string): Custom output path

**Returns:**
```json
{
  "converted_path": ".data/transcripts/compact_20240101_100000_abc123.txt",
  "metadata": {
    "original_format": "codex",
    "target_format": "claude"
  }
}
```

## Workflow Patterns

### Daily Development Workflow

1. **Start Session:**
```bash
./amplify-codex.sh --profile development
```

2. **Initialize Context:**
```bash
# Automatically loads relevant memories
# Displays available MCP tools
```

3. **Development Work:**
```bash
# Edit code files
# Use Codex for assistance
```

4. **Quality Checks:**
```bash
codex> check_code_quality with file_paths ["modified_files.py"]
```

5. **Save Progress:**
```bash
codex> save_current_transcript with format "standard"
```

6. **End Session:**
```bash
# Exit Codex (Ctrl+D)
# Wrapper automatically extracts memories and exports transcript
```

### CI/CD Integration

**GitHub Actions Example:**
```yaml
- name: Code Quality Check
  run: |
    export AMPLIFIER_BACKEND=codex
    export CODEX_PROFILE=ci
    codex exec "check_code_quality with file_paths ['src/', 'tests/']"
```

**Pre-commit Hook:**
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run quality checks
codex --profile ci exec "check_code_quality with file_paths [$(git diff --cached --name-only | tr '\n' ',')]"
```

### Code Review Workflow

1. **Setup Review Environment:**
```bash
./amplify-codex.sh --profile review
```

2. **Load Code for Review:**
```bash
codex> read_file with path "src/feature.py"
```

3. **Run Quality Checks:**
```bash
codex> check_code_quality with file_paths ["src/feature.py"]
```

4. **Generate Review Documentation:**
```bash
codex> save_current_transcript with format "extended"
```

5. **Export Review Summary:**
```bash
codex> convert_transcript_format with session_id "review_session" to "claude"
```

### Batch Processing Workflow

**Process Multiple Sessions:**
```bash
# Export all project transcripts
codex> save_project_transcripts with project_dir "." and incremental true

# Convert to consistent format
for session in $(list_sessions.py); do
  codex exec "convert_transcript_format with session_id $session to claude"
done
```

**Automated Quality Assurance:**
```bash
# Check all Python files
find . -name "*.py" -exec codex exec "check_code_quality with file_paths [{}]" \;

# Generate quality report
codex exec "save_project_transcripts with format compact"
```

## Agent System

### Agent Conversion

Agents are converted from Claude Code format using `tools/convert_agents.py`:

```bash
# Convert all agents
python tools/convert_agents.py

# Convert specific agent
python tools/convert_agents.py --agent bug-hunter
```

**Conversion Process:**
1. Reads Claude Code agent from `.claude/agents/`
2. Removes Task tool references
3. Adapts tool array format
4. Preserves methodology and description
5. Saves to `.codex/agents/`

### Available Agents by Category

#### Architecture & Design
- **zen-architect**: Minimal complexity architecture design
- **database-architect**: Database schema design
- **api-contract-designer**: API contract design

#### Implementation
- **modular-builder**: Modular code implementation
- **integration-specialist**: System integration

#### Quality & Testing
- **bug-hunter**: Bug investigation and fixing
- **test-coverage**: Test coverage analysis
- **security-guardian**: Security vulnerability identification

#### Analysis
- **analysis-engine**: Deep code analysis
- **pattern-emergence**: Pattern identification
- **insight-synthesizer**: Insight synthesis

#### Knowledge
- **concept-extractor**: Concept extraction
- **knowledge-archaeologist**: Knowledge discovery
- **content-researcher**: Information research

### Invocation Methods

#### Automatic Selection
```bash
# Codex auto-selects based on description
codex exec "Find and fix the authentication bug"
# Routes to bug-hunter agent
```

#### Manual Selection
```bash
# Explicit agent selection
codex exec --agent zen-architect "Design the caching layer"
```

#### Programmatic Usage
```python
from amplifier import spawn_agent

result = spawn_agent(
    agent_name="bug-hunter",
    task="Investigate memory leak",
    backend="codex"
)
```

### Spawning Differences from Claude Code

| Aspect | Claude Code | Codex |
|--------|-------------|-------|
| **Invocation** | `Task(agent_name, task)` | `codex exec --agent <name> "<task>"` |
| **Tool Access** | Task, TodoWrite, WebFetch | Read, Grep, Glob, Bash, Write |
| **Execution** | Automatic via Task tool | Explicit `codex exec` command |
| **Context** | Automatic conversation context | Manual context passing |
| **Output** | Integrated in conversation | Separate command output |

## Transcript Management

### Transcript Formats

#### Standard Format (`transcript.md`)
- **Purpose**: Conversation-focused markdown
- **Content**: User/assistant messages with tool interactions
- **Use Case**: Human-readable session review

#### Extended Format (`transcript_extended.md`)
- **Purpose**: Detailed session analysis
- **Content**: All events, raw JSON, metadata, statistics
- **Use Case**: Debugging, detailed analysis

#### Compact Format
- **Purpose**: Space-efficient storage
- **Content**: Condensed conversation without metadata
- **Use Case**: Archival, bulk processing

### Storage Locations

| Backend | Location | Structure |
|---------|----------|-----------|
| **Codex Global** | `~/.codex/transcripts/` | Session directories |
| **Codex Local** | `.codex/transcripts/` | Project-specific exports |
| **Claude Code** | `.data/transcripts/` | Individual files |

### Session Directory Structure

```
2024-01-01-10-00-AM__project__abc123/
├── transcript.md              # Standard format
├── transcript_extended.md     # Extended format
├── history.jsonl             # Raw event log
└── meta.json                 # Session metadata
```

### Working with Transcripts

#### Using Transcript Manager

```bash
# List all transcripts
python tools/transcript_manager.py list

# Load specific transcript
python tools/transcript_manager.py load abc123

# Search across backends
python tools/transcript_manager.py search "error handling"

# Convert formats
python tools/transcript_manager.py convert abc123 --from codex --to claude
```

#### Direct Codex Tools

```bash
# Export current session
codex> save_current_transcript with format "both"

# List available sessions
codex> list_available_sessions

# Batch export project
codex> save_project_transcripts with project_dir "."
```

### Format Conversion

**Codex to Claude Code:**
```bash
python tools/transcript_manager.py convert session_id --from codex --to claude
```

**Claude Code to Codex:**
```bash
python tools/transcript_manager.py convert session_id --from claude --to codex
```

**Bidirectional Conversion:**
- Preserves conversation content
- Adapts metadata format
- Maintains tool interaction details
- Handles format-specific features

## Session Management

### Wrapper Script Usage

**Basic Usage:**
```bash
./amplify-codex.sh
```

**Profile Selection:**
```bash
./amplify-codex.sh --profile ci
./amplify-codex.sh --profile review
```

**Manual Control:**
```bash
# Skip initialization
./amplify-codex.sh --no-init

# Skip cleanup
./amplify-codex.sh --no-cleanup
```

### Manual Session Management

**Initialize Session:**
```bash
uv run python .codex/tools/session_init.py --prompt "Working on feature"
```

**Start Codex:**
```bash
codex --profile development
```

**Use MCP Tools During Session:**
```bash
codex> initialize_session with prompt "Continue working"
codex> check_code_quality with file_paths ["file.py"]
codex> save_current_transcript
```

**Cleanup Session:**
```bash
uv run python .codex/tools/session_cleanup.py
```

### Session Lifecycle

1. **Initialization Phase:**
   - Load relevant memories
   - Create session context
   - Start MCP servers

2. **Active Session Phase:**
   - User interacts with Codex
   - MCP tools called as needed
   - Progress saved periodically

3. **Cleanup Phase:**
   - Extract memories from conversation
   - Export transcript
   - Clean up temporary files

### MCP Tool Integration

**Session Start:**
```bash
codex> initialize_session with prompt "Starting new feature"
```

**During Work:**
```bash
codex> check_code_quality with file_paths ["modified.py"]
codex> save_current_transcript with format "standard"
```

**Session End:**
```bash
codex> finalize_session with recent messages
```

## Backend Abstraction

### Programmatic Usage

```python
from amplifier import get_backend, set_backend

# Set backend
set_backend("codex")

# Get backend instance
backend = get_backend()

# Unified API
result = backend.initialize_session("Working on feature")
result = backend.run_quality_checks(["file.py"])
result = backend.export_transcript(format="extended")
```

### Configuration Management

```python
from amplifier.core.config import get_backend_config

config = get_backend_config()
print(f"Backend: {config.amplifier_backend}")
print(f"Profile: {config.codex_profile}")
```

### Integration Examples

**Custom Script:**
```python
#!/usr/bin/env python3
from amplifier import get_backend

def development_workflow():
    backend = get_backend()
    
    # Initialize
    result = backend.initialize_session("New feature development")
    print(f"Loaded {result['metadata']['memoriesLoaded']} memories")
    
    # Quality checks
    result = backend.run_quality_checks(["src/feature.py"])
    if not result["success"]:
        print("Quality checks failed!")
        return
    
    # Export transcript
    result = backend.export_transcript()
    print(f"Transcript saved to {result['data']['path']}")

if __name__ == "__main__":
    development_workflow()
```

**CI/CD Integration:**
```python
# ci_check.py
from amplifier import get_backend

def ci_quality_check():
    backend = get_backend()
    
    # Get changed files
    import subprocess
    result = subprocess.run(["git", "diff", "--name-only", "HEAD~1"], 
                          capture_output=True, text=True)
    files = result.stdout.strip().split('\n')
    
    # Run checks
    result = backend.run_quality_checks(files)
    return result["success"]

if __name__ == "__main__":
    success = ci_quality_check()
    exit(0 if success else 1)
```

## Advanced Topics

### Custom MCP Servers

**Create New Server:**
```python
# .codex/mcp_servers/custom/server.py
from mcp.server.fastmcp import FastMCP
from ..base import MCPLogger

logger = MCPLogger("custom")
mcp = FastMCP("amplifier_custom")

@mcp.tool()
def custom_tool(param: str) -> dict:
    """Custom tool description"""
    # Implementation
    return {"result": "custom output"}

if __name__ == "__main__":
    mcp.run()
```

**Add to Configuration:**
```toml
[mcp_servers.amplifier_custom]
command = "uv"
args = ["run", "python", ".codex/mcp_servers/custom/server.py"]

[profiles.custom]
mcp_servers = ["amplifier_session", "amplifier_custom"]
```

### Extending Existing Servers

**Add Tool to Session Manager:**
```python
# In session_manager/server.py
@mcp.tool()
def custom_memory_search(query: str, limit: int = 5) -> dict:
    """Search memories with custom logic"""
    # Custom search implementation
    return {"memories": [], "count": 0}
```

### Performance Optimization

**Memory System Tuning:**
```bash
# Disable memory system for faster startup
MEMORY_SYSTEM_ENABLED=false codex --profile development

# Use compact transcripts for faster export
codex> save_current_transcript with format "compact"
```

**MCP Server Optimization:**
- Keep tool implementations lightweight
- Use async operations where possible
- Cache expensive computations
- Implement proper error handling

**Profile Optimization:**
```toml
[profiles.fast]
mcp_servers = ["amplifier_quality"]  # Minimal servers
```

## Troubleshooting

### Installation Issues

**Codex CLI not found:**
```bash
# Check installation
which codex

# Reinstall Codex
# Follow: https://docs.anthropic.com/codex/installation

# Add to PATH
export PATH="$HOME/.codex/bin:$PATH"
```

**uv not available:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

**Python version issues:**
```bash
# Check Python version
python --version  # Should be 3.11+

# Use specific Python
uv run --python 3.11 python --version
```

### Configuration Issues

**Config file not found:**
```bash
# Create config directory
mkdir -p .codex

# Initialize config
codex --config .codex/config.toml --init

# Verify config
cat .codex/config.toml
```

**Profile not working:**
```bash
# List available profiles
codex --list-profiles

# Check profile syntax
codex --profile development --validate-config
```

**Environment variables not recognized:**
```bash
# Check variable setting
echo $AMPLIFIER_BACKEND

# Set in current session
export AMPLIFIER_BACKEND=codex
export CODEX_PROFILE=development
```

### MCP Server Issues

**Server startup failures:**
```bash
# Check server logs
tail -f .codex/logs/session_manager.log

# Test server directly
uv run python .codex/mcp_servers/session_manager/server.py

# Verify imports
python -c "from amplifier.memory import MemoryStore"
```

**Tool registration errors:**
```bash
# Check MCP protocol
mcp-inspector uv run python .codex/mcp_servers/session_manager/server.py

# Validate tool definitions
python -c "from .codex.mcp_servers.session_manager.server import mcp; print(mcp.list_tools())"
```

**Communication failures:**
```bash
# Test stdio communication
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | \
uv run python .codex/mcp_servers/session_manager/server.py

# Check for JSON parsing errors
tail -f .codex/logs/*.log | grep -i error
```

### Memory System Issues

**Memory loading failures:**
```bash
# Check memory system status
python -c "from amplifier.memory import MemoryStore; print('Memory system OK')"

# Verify memory files exist
ls .data/memories/

# Check memory system enabled
echo $MEMORY_SYSTEM_ENABLED
```

**Memory extraction timeouts:**
```bash
# Increase timeout (if configurable)
# Check logs for timeout details
tail -f .codex/logs/session_manager.log

# Run extraction manually
uv run python .codex/tools/session_cleanup.py --no-timeout
```

### Quality Check Issues

**make check not found:**
```bash
# Verify Makefile exists
ls Makefile

# Check make target
make check

# Verify uv available in PATH
which uv
```

**Tool execution failures:**
```bash
# Test tools individually
uv run ruff check .
uv run pyright
uv run pytest

# Check tool installation
uv pip list | grep -E "(ruff|pyright|pytest)"
```

**Worktree environment issues:**
```bash
# Check VIRTUAL_ENV
echo $VIRTUAL_ENV

# Temporarily unset for worktree
unset VIRTUAL_ENV
make check
```

### Transcript Issues

**Session not found:**
```bash
# List available sessions
codex> list_available_sessions

# Check session directory
ls ~/.codex/sessions/

# Verify session ID format
ls ~/.codex/sessions/ | head -5
```

**Export failures:**
```bash
# Check write permissions
touch .codex/transcripts/test.txt

# Verify session data
ls ~/.codex/sessions/session_id/

# Check logs for export errors
tail -f .codex/logs/transcript_saver.log
```

**Format conversion issues:**
```bash
# Test conversion tool
python tools/transcript_manager.py convert session_id --from codex --to claude

# Check source transcript exists
ls .codex/transcripts/session_id/

# Verify conversion logs
tail -f .codex/logs/conversion.log
```

### Agent Issues

**Agent not found:**
```bash
# List available agents
ls .codex/agents/

# Check agent file format
head .codex/agents/bug-hunter.md

# Verify YAML frontmatter
python -c "import yaml; print(yaml.safe_load(open('.codex/agents/bug-hunter.md')))"
```

**Agent execution failures:**
```bash
# Test agent spawning
codex exec --agent bug-hunter "test task"

# Check Codex logs
codex --log-level debug exec --agent bug-hunter "test"

# Verify tool permissions
cat .codex/config.toml | grep -A 5 "tool_permissions"
```

### Wrapper Script Issues

**Script not executable:**
```bash
# Make executable
chmod +x amplify-codex.sh

# Check permissions
ls -la amplify-codex.sh
```

**Prerequisite checks failing:**
```bash
# Test prerequisites manually
./amplify-codex.sh --check-only

# Check Codex installation
codex --version

# Check virtual environment
ls .venv/

# Check uv
uv --version
```

**Session initialization failures:**
```bash
# Run initialization manually
uv run python .codex/tools/session_init.py --verbose

# Check logs
cat .codex/logs/session_init.log

# Verify memory system
echo $MEMORY_SYSTEM_ENABLED
```

## Best Practices

### When to Use Codex

**Choose Codex when:**
- Working in headless environments (servers, CI/CD)
- Needing programmatic control over AI interactions
- Using editors other than VS Code
- Requiring custom MCP server integrations
- Working in team environments with mixed IDE preferences

**Choose Claude Code when:**
- Primary development in VS Code
- Preferring automatic hook-based workflows
- Needing TodoWrite and WebFetch tools
- Wanting seamless IDE integration

### Workflow Recommendations

**Daily Development:**
1. Use wrapper script for full automation
2. Start with memory loading via `initialize_session`
3. Run quality checks after significant changes
4. Save transcripts periodically
5. Let cleanup handle memory extraction

**CI/CD Integration:**
1. Use minimal profiles (ci/review)
2. Run quality checks on changed files
3. Export transcripts for audit trails
4. Fail builds on quality check failures

**Code Review:**
1. Use review profile with quality + transcript servers
2. Load code under review
3. Run comprehensive quality checks
4. Generate detailed transcripts for documentation

### Performance Tips

**Optimize Memory System:**
```bash
# Disable for fast sessions
MEMORY_SYSTEM_ENABLED=false ./amplify-codex.sh

# Use selective memory loading
codex> initialize_session with prompt "specific topic"