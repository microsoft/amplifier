# Architecture & Integration Discoveries

Patterns and solutions related to system architecture, backend integration, and service communication.

---

## 2025-10-24 – Dual Backend Integration: Claude Code vs Codex

### Issue

Implementing dual backend support (Claude Code and Codex) revealed several architectural differences and limitations that affect feature parity and testing strategies.

### Root Cause

Claude Code and Codex have fundamentally different architectures:

1. **Automation Model**: Claude Code uses automatic hooks (SessionStart, PostToolUse, PreCompact, Stop) while Codex requires explicit MCP tool invocation or wrapper scripts
2. **Agent Spawning**: Claude Code has native Task tool for seamless agent spawning; Codex uses `codex exec` subprocess with different invocation model
3. **Configuration**: Claude Code uses JSON (settings.json) with limited profiles; Codex uses TOML (config.toml) with rich profile support
4. **Transcript Format**: Claude Code uses single text files (compact_*.txt); Codex uses session directories with multiple files (transcript.md, transcript_extended.md, history.jsonl)
5. **Tool Availability**: Claude Code has Task, TodoWrite, WebFetch, WebSearch; Codex has Read, Write, Edit, Grep, Glob, Bash

### Solutions Implemented

**1. Backend Abstraction Layer** (`amplifier/core/backend.py`):
- Created `AmplifierBackend` abstract base class with methods: `initialize_session()`, `finalize_session()`, `run_quality_checks()`, `export_transcript()`
- Implemented `ClaudeCodeBackend` and `CodexBackend` concrete classes
- Both backends delegate to same amplifier modules (memory, extraction, search) ensuring consistency
- Factory pattern (`BackendFactory`) for backend instantiation based on environment/config

**2. Agent Abstraction Layer** (`amplifier/core/agent_backend.py`):
- Created `AgentBackend` abstract base class with `spawn_agent()` method
- `ClaudeCodeAgentBackend` uses Claude Code SDK Task tool
- `CodexAgentBackend` uses `codex exec` subprocess
- Agent definitions converted from Claude format to Codex format (removed Task tool references, adapted tools array)

**3. MCP Servers for Codex** (`.codex/mcp_servers/`):
- Implemented three MCP servers to replace Claude Code hooks:
  - `session_manager` - Replaces SessionStart/Stop hooks
  - `quality_checker` - Replaces PostToolUse hook
  - `transcript_saver` - Replaces PreCompact hook
- Used FastMCP framework for rapid development
- Servers expose tools that must be explicitly invoked (vs automatic hooks)

**4. Wrapper Scripts**:
- `amplify-codex.sh` - Bash wrapper providing hook-like experience for Codex
- `amplify.py` - Unified Python CLI for both backends
- `.codex/tools/session_init.py` and `session_cleanup.py` - Standalone session management

**5. Configuration System** (`amplifier/core/config.py`):
- Pydantic `BackendConfig` with environment variable support
- Configuration precedence: CLI args > env vars > .env file > defaults
- Auto-detection when `AMPLIFIER_BACKEND` not set
- Validation for backend types and profiles

### Key Learnings

1. **Abstraction enables testing**: Backend abstraction layer allows testing workflows without requiring real CLIs
2. **Mock at boundaries**: Mock subprocess calls and file I/O, but test real backend logic
3. **Shared modules ensure consistency**: Both backends using same amplifier modules (memory, extraction, search) guarantees identical behavior
4. **Configuration is critical**: Proper configuration management (precedence, validation, defaults) is essential for dual-backend support
5. **Documentation prevents confusion**: Comprehensive docs (CODEX_INTEGRATION.md, BACKEND_COMPARISON.md, MIGRATION_GUIDE.md) are essential for users
6. **Smoke tests validate critical paths**: Fast smoke tests catch regressions without full integration test suite
7. **Wrapper scripts bridge gaps**: amplify-codex.sh provides hook-like experience for Codex despite lack of native hooks

### Prevention

- Use backend abstraction layer for all backend operations (don't call CLIs directly)
- Test both backends for any new feature to ensure parity
- Document limitations clearly when features can't be replicated
- Use wrapper scripts to provide consistent user experience across backends
- Keep backend-specific code isolated in `.claude/` and `.codex/` directories
- Maintain comprehensive documentation for both backends
- Run smoke tests in CI to catch regressions early
- Update DISCOVERIES.md when new limitations are found

---

## 2025-10-26 – MCP Server Handshake Failures: Working Directory and Path Issues

### Issue

All five Codex MCP servers (`amplifier_session`, `amplifier_quality`, `amplifier_transcripts`, `amplifier_tasks`, `amplifier_web`) failed to start with "connection closed: initialize response" errors when launched by Codex CLI. The servers would crash during startup before completing the MCP protocol handshake, preventing any MCP tools from being available in Codex sessions.

### Root Cause

The MCP servers were being launched by Codex CLI with `uv run python .codex/mcp_servers/<server>/server.py` without proper working directory context. This caused multiple failures:

1. **Relative imports failed**: `from ..base import AmplifierMCPServer` could not resolve because `.codex/` and `.codex/mcp_servers/` lacked `__init__.py` files
2. **Amplifier module imports failed**: `from amplifier.memory import MemoryStore` could not resolve because PYTHONPATH was not set to project root
3. **Working directory mismatch**: `uv run` was being executed from a different directory than the project root, causing path resolution failures
4. **Server processes crashed**: Before completing the MCP handshake, servers would exit due to import errors, resulting in "connection closed: initialize response"

The `env = { AMPLIFIER_ROOT = "." }` configuration used relative paths which didn't work when Codex invoked the servers from a different context.

### Solution

Implemented **Solution Approach A**: Modified `.codex/config.toml` to add explicit working directory and PYTHONPATH for all five MCP servers:

**Configuration changes:**
```toml
# Before (broken):
[mcp_servers.amplifier_tasks]
command = "uv"
args = ["run", "python", ".codex/mcp_servers/task_tracker/server.py"]
env = { AMPLIFIER_ROOT = "." }

# After (working):
[mcp_servers.amplifier_tasks]
command = "uv"
args = ["run", "--directory", "/absolute/path/to/project", "python", ".codex/mcp_servers/task_tracker/server.py"]
env = {
  AMPLIFIER_ROOT = "/absolute/path/to/project",
  PYTHONPATH = "/absolute/path/to/project"
}
```

**Python package structure:**
- Created `.codex/__init__.py` to make `.codex/` a proper Python package
- Created `.codex/mcp_servers/__init__.py` to enable relative imports in server modules

**Alternative solution (wrapper scripts):**
Also created bash wrapper scripts (`.codex/mcp_servers/<server>/run.sh`) as an alternative approach. These scripts:
1. Navigate to project root using relative path from script location
2. Set AMPLIFIER_ROOT and PYTHONPATH environment variables
3. Execute the server with `exec uv run python`

Wrapper scripts are provided as Solution Approach B for users who prefer not to hardcode absolute paths in config.toml.

### Key Learnings

1. **MCP servers must run from project root**: Relative imports and module resolution require proper working directory context
2. **`uv run` needs explicit `--directory` flag**: When invoked from different context, uv run won't automatically find the correct project directory
3. **PYTHONPATH is critical for module imports**: Without PYTHONPATH set to project root, amplifier module imports fail even with correct working directory
4. **MCP handshake errors often indicate startup crashes**: "connection closed: initialize response" doesn't mean protocol issues - it means the server process crashed before responding
5. **Manual server execution is essential for diagnosis**: Running servers manually (`uv run python .codex/mcp_servers/<server>/server.py` from project root) immediately reveals import errors and other startup issues
6. **Absolute paths vs relative paths in config**: Relative paths in MCP server configs don't work reliably when Codex CLI invokes servers from different directories
7. **Python package structure matters**: Missing `__init__.py` files prevent relative imports from working, causing immediate crashes
8. **Server logs are invaluable**: `.codex/logs/<server>_<date>.log` files show the actual errors when servers crash during startup

### Prevention

1. **Always test MCP servers manually before configuring in Codex**: Run `uv run python .codex/mcp_servers/<server>/server.py` from project root to verify server starts without errors
2. **Use absolute paths or explicit working directories in MCP server configs**: Avoid relative paths that break when invoked from different contexts
3. **Ensure proper `__init__.py` files for Python package structure**: Any directory with Python modules that use relative imports needs to be a proper package
4. **Set PYTHONPATH in server environment configuration**: Always include PYTHONPATH pointing to project root for servers that import project modules
5. **Check `.codex/logs/` for server startup errors**: When servers fail to start, always check log files for the actual error before modifying configuration
6. **Create diagnostic documentation**: Maintain `DIAGNOSTIC_STEPS.md` with step-by-step troubleshooting commands for future issues
7. **Provide alternative solutions**: Offer both config-based (absolute paths) and script-based (wrapper scripts) approaches to accommodate different preferences
8. **Document configuration requirements**: Clearly explain in `.codex/mcp_servers/README.md` why working directory and PYTHONPATH are required
