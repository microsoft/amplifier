# Verification Comments Implementation Summary

This document summarizes the implementation of all 13 verification comments.

## ✅ Completed Comments

### Comment 1: Fix CodexBackend MCP tool invocation
**Status**: ✅ COMPLETE

**Implementation**:
- Created `.codex/tools/codex_mcp_client.py` - thin MCP client that invokes tools via `codex tool` CLI
- Updated `CodexBackend.manage_tasks()` to use MCP client instead of direct imports
- Updated `CodexBackend.search_web()` to use MCP client
- Updated `CodexBackend.fetch_url()` to use MCP client
- All methods now properly invoke MCP tools via subprocess, ensuring async compatibility

**Files Modified**:
- `amplifier/core/backend.py`
- `.codex/tools/codex_mcp_client.py` (new)

### Comment 2: Fix agent context bridge import path
**Status**: ✅ COMPLETE

**Implementation**:
- Created `amplifier/codex_tools/` package directory
- Moved `agent_context_bridge.py` to `amplifier/codex_tools/agent_context_bridge.py`
- Created `amplifier/codex_tools/__init__.py` with proper exports
- Updated `amplifier/core/agent_backend.py` to import from `amplifier.codex_tools`
- Removed sys.path hacks

**Files Modified**:
- `amplifier/codex_tools/__init__.py` (new)
- `amplifier/codex_tools/agent_context_bridge.py` (moved from `.codex/tools/`)
- `amplifier/core/agent_backend.py`

### Comment 3: Fix Codex spawn_agent CLI flags
**Status**: ✅ COMPLETE

**Implementation**:
- Changed `--context-file` to `--agent` for agent definition
- Changed second `--context-file` to `--context` for session context
- Removed duplicate `--context-file` flags
- Properly separated agent definition from context data
- Added proper `context_file` initialization to avoid undefined variable errors

**Files Modified**:
- `amplifier/core/agent_backend.py`

## 🔄 In Progress / Remaining Comments

### Comment 4: Fix task storage path and schema
**Status**: PENDING

**Required Changes**:
1. Update `.codex/mcp_servers/task_tracker/server.py`:
   - Change `self.tasks_dir = Path(__file__).parent.parent.parent / "tasks"` to read from config
   - Default to `.codex/tasks/`
   - Load `task_storage_path` from `[mcp_server_config.task_tracker]` in config.toml
2. Ensure `.codex/tasks/` directory exists
3. Normalize task schema to single format

**Files to Modify**:
- `.codex/mcp_servers/task_tracker/server.py`

### Comment 5: Add missing auto_save.py and auto_check.py
**Status**: PENDING

**Required Changes**:
1. Create `.codex/tools/auto_save.py`:
   - Calls `amplifier_transcripts.save_current_transcript` MCP tool via codex CLI
   - Or uses CodexMCPClient to invoke the tool
2. Create `.codex/tools/auto_check.py`:
   - Calls `amplifier_quality.check_code_quality` MCP tool via codex CLI
   - Or uses CodexMCPClient to invoke the tool
3. Alternative: Update `amplify-codex.sh` to call MCP tools directly via `codex tool` command

**Files to Create**:
- `.codex/tools/auto_save.py` (new)
- `.codex/tools/auto_check.py` (new)

### Comment 6: Add --check-only flag to wrapper
**Status**: PENDING

**Required Changes**:
1. Add `--check-only` flag parsing in `amplify-codex.sh`
2. When flag is set:
   - Run prerequisite checks
   - Run configuration validation
   - Print results
   - Exit without launching Codex
3. Update help output

**Files to Modify**:
- `amplify-codex.sh`

### Comment 7: Standardize web research server API
**Status**: PENDING

**Required Changes**:
1. Decide on implementation approach:
   - Option A: Implement WebCache, RateLimiter, TextSummarizer classes
   - Option B: Update tests/docs to match simple implementation
2. Standardize response schema: `{success, data{...}, metadata{...}}`
3. Align field names across all tools

**Files to Modify**:
- `.codex/mcp_servers/web_research/server.py`
- `tests/test_web_research_mcp.py`

### Comment 8: Standardize task tracker response shapes
**Status**: PENDING

**Required Changes**:
1. Standardize to: `{success, data: {task: {...}}}` for CRUD
2. Use: `{success, data: {tasks: [...], count: n}}` for listing
3. Add `completed_at` timestamp when completing tasks
4. Update export to write file if tests require `export_path`

**Files to Modify**:
- `.codex/mcp_servers/task_tracker/server.py`
- `tests/test_task_tracker_mcp.py`

### Comment 9: Fix Claude native success behavior
**Status**: PENDING

**Required Changes**:
1. Decide on contract:
   - Option A: Return `success: False` with `metadata.unsupported=true`
   - Option B: Implement real bridging to Claude Code SDK
2. Update tests to match chosen behavior

**Files to Modify**:
- `amplifier/core/backend.py` (ClaudeCodeBackend methods)
- `tests/backend_integration/test_enhanced_workflows.py`

### Comment 10: Add spawn_agent_with_context to AmplifierBackend
**Status**: PENDING

**Required Changes**:
1. Add `spawn_agent_with_context()` to `AmplifierBackend` abstract class
2. Implement in both `ClaudeCodeBackend` and `CodexBackend`
3. Delegate to agent backend
4. Update tests

**Files to Modify**:
- `amplifier/core/backend.py`
- `amplifier/core/agent_backend.py`
- `tests/backend_integration/test_enhanced_workflows.py`

### Comment 11: Fix config consumption in MCP servers
**Status**: PENDING

**Required Changes**:
1. Load server config in `TaskTrackerServer.__init__()`:
   - Read `task_storage_path`, `max_tasks_per_session` from config
2. Load server config in `WebResearchServer.__init__()`:
   - Read `cache_enabled`, `cache_ttl_hours`, `max_results` from config
3. Use `AmplifierMCPServer.config` utility to access config values
4. Remove hardcoded paths

**Files to Modify**:
- `.codex/mcp_servers/task_tracker/server.py`
- `.codex/mcp_servers/web_research/server.py`

### Comment 12: Add capability check to wrapper tool list
**Status**: PENDING

**Required Changes**:
1. Parse `.codex/config.toml` to detect enabled MCP servers for profile
2. Only print tools for active servers
3. Optionally run health check via `codex tool <server>.health_check`

**Files to Modify**:
- `amplify-codex.sh`

### Comment 13: Add error handling to bash shortcuts
**Status**: PENDING

**Required Changes**:
1. Add checks at start of each function:
   - Verify `codex --version` works
   - Check `.codex/config.toml` exists
2. Catch Python exceptions and print clear error messages
3. Optionally adapt output based on backend capabilities

**Files to Modify**:
- `.codex/tools/codex_shortcuts.sh`

## Next Steps

1. Run `make check` to ensure current changes don't break linting
2. Implement remaining comments 4-13
3. Update tests to match new implementations
4. Run full test suite
5. Update DISCOVERIES.md with lessons learned
