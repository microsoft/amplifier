# Verification Comments Implementation Status

## Summary

Implemented 4 out of 13 verification comments. The remaining 9 comments require additional decisions and test alignment.

## ✅ Completed (4/13)

### Comment 1: CodexBackend MCP Tool Invocation ✅
**Problem**: Direct imports of MCP server functions bypass async handling and ignore MCP protocol.

**Solution**:
- Created `.codex/tools/codex_mcp_client.py` - thin subprocess client
- Updated `CodexBackend.manage_tasks()`, `search_web()`, `fetch_url()` to use MCP client
- All tools now invoked via `codex tool <server>.<tool>` command
- Proper async handling and error response parsing

**Files Changed**:
- `amplifier/core/backend.py` (updated 3 methods)
- `.codex/tools/codex_mcp_client.py` (new file)

### Comment 2: Agent Context Bridge Import Path ✅
**Problem**: Invalid import path using sys.path hacks; `.codex` not an importable package.

**Solution**:
- Created `amplifier/codex_tools/` package
- Moved `agent_context_bridge.py` to `amplifier/codex_tools/`
- Created proper `__init__.py` with exports
- Updated imports in `agent_backend.py`
- Removed sys.path manipulation

**Files Changed**:
- `amplifier/codex_tools/__init__.py` (new)
- `amplifier/codex_tools/agent_context_bridge.py` (moved)
- `amplifier/core/agent_backend.py` (updated imports)

### Comment 3: Codex spawn_agent CLI Flags ✅
**Problem**: Duplicate `--context-file` flags; unclear separation of agent definition vs context.

**Solution**:
- Changed `--context-file` to `--agent` for agent definition
- Changed second `--context-file` to `--context` for session context
- Properly initialized `context_file` variable to avoid undefined errors
- Clear separation: `--agent=<agent.md>` for definition, `--context=<ctx.json>` for session data

**Files Changed**:
- `amplifier/core/agent_backend.py` (spawn_agent method)

### Comment 5: Auto Save/Check Scripts ✅
**Problem**: Missing `auto_save.py` and `auto_check.py` referenced in wrapper.

**Solution**:
- Files already existed but had linting errors (E402 - module imports not at top)
- Added `# noqa: E402` comments to both files
- Verified functionality - both scripts properly use BackendFactory

**Files Changed**:
- `.codex/tools/auto_save.py` (linting fix)
- `.codex/tools/auto_check.py` (linting fix)

## ⏳ Remaining Issues (9/13)

### Comment 4: Task Storage Path
**Issue**: Tasks saved to server folder, not `.codex/tasks/`
**Requires**: Config reading, path normalization

### Comment 6: --check-only Flag
**Issue**: Missing flag in wrapper
**Requires**: Bash argument parsing, prerequisite check refactor

### Comment 7: Web Research API
**Issue**: API divergence between implementation and tests
**Requires**: Decision on implementation approach (add classes vs update tests)

### Comment 8: Task Tracker Response Shapes
**Issue**: Inconsistent response schemas
**Requires**: Response shape standardization, test updates

### Comment 9: Claude Native Success Behavior
**Issue**: Returns `success: True` for native tools where tests expect `success: False`
**Requires**: Contract decision and test alignment

### Comment 10: spawn_agent_with_context API
**Issue**: Method only in CodexAgentBackend, not in AmplifierBackend
**Requires**: Abstract method addition, dual implementation

### Comment 11: Config Consumption
**Issue**: MCP servers don't read config values
**Requires**: Config loading in server __init__, remove hardcoded values

### Comment 12: Capability Check in Wrapper
**Issue**: Prints all tools regardless of which are enabled
**Requires**: Config parsing, conditional display

### Comment 13: Bash Shortcuts Error Handling
**Issue**: No error handling for missing prerequisites
**Requires**: Prerequisite checks, Python exception catching

## Next Steps

1. **Run make check** to verify current fixes don't introduce new linting errors
2. **Make architectural decisions** for remaining comments:
   - Comment 7: Which API design to use?
   - Comment 9: What should "native" tools return?
3. **Implement remaining fixes** in priority order:
   - High: Comments 4, 8, 11 (core functionality)
   - Medium: Comments 10 (API completeness)
   - Low: Comments 6, 12, 13 (UX improvements)
4. **Update tests** to match new implementations
5. **Document** in DISCOVERIES.md

## Key Learnings

1. **MCP Protocol over Direct Imports**: Using subprocess + JSON protocol is more robust than direct function imports
2. **Package Structure Matters**: Proper Python packages avoid sys.path hacks and make imports cleaner
3. **CLI Flag Clarity**: Separating concerns (agent vs context) via distinct flags prevents confusion
4. **Linting in CI**: Some linting rules (E402) need context-aware suppression

## Files Created

- `.codex/tools/codex_mcp_client.py`
- `amplifier/codex_tools/__init__.py`
- `amplifier/codex_tools/agent_context_bridge.py` (moved)
- `IMPLEMENTATION_SUMMARY.md`
- `VERIFICATION_FIXES_SUMMARY.md`

## Files Modified

- `amplifier/core/backend.py`
- `amplifier/core/agent_backend.py`
- `.codex/tools/auto_save.py`
- `.codex/tools/auto_check.py`
