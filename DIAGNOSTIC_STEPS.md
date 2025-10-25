# MCP Server Diagnostic Steps

This guide provides step-by-step commands to diagnose MCP server startup failures. Use these steps BEFORE making configuration changes to understand the actual error.

## Prerequisites

- Project virtual environment created (`.venv/` directory exists)
- Dependencies installed (`make install` completed successfully)
- Working directory is project root

## Step 1: Verify Dependencies

First, ensure all required packages are installed:

```bash
cd /Users/aleksandarilic/Documents/github/acailic/improvements-ampl/amplifier-adding-codex
uv sync
```

**Expected output:**
```
Resolved X packages in Y.ZZs
```

**If this fails:**
- Check `pyproject.toml` exists
- Verify `uv` is installed: `uv --version`
- Look for dependency conflicts in the error message

## Step 2: Test MCP Package Import

Verify the `mcp` package is properly installed:

```bash
uv run python -c "from mcp.server.fastmcp import FastMCP; print('MCP package: OK')"
```

**Expected output:**
```
MCP package: OK
```

**If this fails:**
- The `mcp` package is missing or incompatible
- Check `pyproject.toml` for `mcp = ">=1.0.0"` in dependencies
- Run `uv add mcp` to install
- Verify Python version compatibility (requires Python 3.10+)

## Step 3: Test Amplifier Imports

Verify amplifier modules can be imported:

```bash
uv run python -c "from amplifier.memory import MemoryStore; print('Amplifier memory: OK')"
uv run python -c "from amplifier.search import MemorySearcher; print('Amplifier search: OK')"
```

**Expected output:**
```
Amplifier memory: OK
Amplifier search: OK
```

**If this fails:**
- PYTHONPATH is not set correctly
- Amplifier package is not installed in development mode
- Run from correct directory (project root)

## Step 4: Test Base MCP Server Import

Verify the base MCP server class can be imported:

```bash
cd /Users/aleksandarilic/Documents/github/acailic/improvements-ampl/amplifier-adding-codex
uv run python -c "import sys; sys.path.insert(0, '.'); from codex.base import AmplifierMCPServer; print('Base server: OK')"
```

**Expected output:**
```
Base server: OK
```

**If this fails:**
- Missing `__init__.py` files in `.codex/` or `.codex/mcp_servers/`
- Relative import path incorrect
- Working directory not set to project root

## Step 5: Manual Server Execution

Run each server manually to see the actual error. The server should start and wait for MCP protocol messages on stdin:

### Session Manager
```bash
cd /Users/aleksandarilic/Documents/github/acailic/improvements-ampl/amplifier-adding-codex
uv run python .codex/mcp_servers/session_manager/server.py
```

### Quality Checker
```bash
cd /Users/aleksandarilic/Documents/github/acailic/improvements-ampl/amplifier-adding-codex
uv run python .codex/mcp_servers/quality_checker/server.py
```

### Transcript Saver
```bash
cd /Users/aleksandarilic/Documents/github/acailic/improvements-ampl/amplifier-adding-codex
uv run python .codex/mcp_servers/transcript_saver/server.py
```

### Task Tracker
```bash
cd /Users/aleksandarilic/Documents/github/acailic/improvements-ampl/amplifier-adding-codex
uv run python .codex/mcp_servers/task_tracker/server.py
```

### Web Research
```bash
cd /Users/aleksandarilic/Documents/github/acailic/improvements-ampl/amplifier-adding-codex
uv run python .codex/mcp_servers/web_research/server.py
```

**Expected behavior:**
- Server starts without errors
- Process runs and waits for input (doesn't exit immediately)
- Press Ctrl+C to stop

**Common errors:**

1. **ImportError: No module named 'mcp'**
   - MCP package not installed
   - Fix: `uv add mcp`

2. **ImportError: No module named 'amplifier'**
   - PYTHONPATH not set or wrong working directory
   - Fix: Run from project root with PYTHONPATH set

3. **ImportError: attempted relative import with no known parent package**
   - Missing `__init__.py` files
   - Fix: Create `.codex/__init__.py` and `.codex/mcp_servers/__init__.py`

4. **ModuleNotFoundError: No module named 'codex.base'**
   - Python can't resolve the relative import path
   - Fix: Ensure `__init__.py` files exist and run from project root

5. **Server exits immediately with no output**
   - Likely a crash during initialization
   - Check server logs in `.codex/logs/`
   - Add `--verbose` flag if supported

## Step 6: Check Server Logs

After attempting to start Codex, check for server startup errors:

```bash
# List all server logs
ls -la .codex/logs/

# View most recent session manager log
tail -n 50 .codex/logs/session_manager_$(date +%Y%m%d).log

# View most recent quality checker log
tail -n 50 .codex/logs/quality_checker_$(date +%Y%m%d).log

# View most recent transcript saver log
tail -n 50 .codex/logs/transcript_saver_$(date +%Y%m%d).log

# View most recent task tracker log
tail -n 50 .codex/logs/task_tracker_$(date +%Y%m%d).log

# View most recent web research log
tail -n 50 .codex/logs/web_research_$(date +%Y%m%d).log
```

**What to look for:**
- Import errors
- Path-related errors
- Environment variable issues
- Dependency conflicts
- Unhandled exceptions during server initialization

## Step 7: Verify Codex Configuration

Ensure the project configuration is properly copied to Codex CLI's config location:

```bash
# Check if config exists in Codex CLI location
cat ~/.codex/config.toml

# Compare with project config
diff ~/.codex/config.toml .codex/config.toml
```

**Expected:**
- `~/.codex/config.toml` should match `.codex/config.toml`
- The wrapper script (`amplify-codex.sh`) handles this copy
- If different, either run wrapper script or manually copy

## Step 8: Test with Minimal Config

Create a minimal test config to isolate issues:

```toml
# Save as .codex/test_config.toml
model = "gpt-5-codex"

[mcp_servers.amplifier_tasks]
command = "uv"
args = ["run", "--directory", "/Users/aleksandarilic/Documents/github/acailic/improvements-ampl/amplifier-adding-codex", "python", ".codex/mcp_servers/task_tracker/server.py"]
env = { AMPLIFIER_ROOT = "/Users/aleksandarilic/Documents/github/acailic/improvements-ampl/amplifier-adding-codex", PYTHONPATH = "/Users/aleksandarilic/Documents/github/acailic/improvements-ampl/amplifier-adding-codex" }
timeout = 30
```

Copy to Codex location and test:
```bash
cp .codex/test_config.toml ~/.codex/config.toml
codex --version  # Should show Codex CLI version
```

If this works, gradually add other servers back until you identify the problematic one.

## Common Success Indicators

When everything is working correctly:

1. **Dependencies**: All imports succeed without errors
2. **Manual execution**: Servers start and wait for input (don't crash)
3. **Logs**: No error messages in `.codex/logs/` files
4. **Codex startup**: No "connection closed: initialize response" errors
5. **Tool availability**: MCP tools appear in Codex session

## Common Failure Patterns

| Error Pattern | Root Cause | Fix |
|---------------|------------|-----|
| "connection closed: initialize response" | Server crashes during startup | Check server logs, verify imports work |
| "No module named 'mcp'" | MCP package not installed | Run `uv add mcp` |
| "No module named 'amplifier'" | PYTHONPATH not set | Add PYTHONPATH to server env config |
| "attempted relative import" | Missing `__init__.py` | Create package marker files |
| Server exits immediately | Crash during initialization | Run manually to see error, check logs |
| Import timeout | Slow dependency loading | Increase timeout in config.toml |

## Next Steps

After diagnosing the issue:

1. Fix the root cause (dependencies, paths, config)
2. Verify fix with manual server execution (Step 5)
3. Update `.codex/config.toml` with proper configuration
4. Test with Codex CLI: `codex --version` then start a session
5. Verify tools are available in Codex session

## Getting Help

If these steps don't resolve the issue:

1. Save diagnostic output: `bash diagnostic_script.sh > diagnostic_output.txt 2>&1`
2. Include relevant log files from `.codex/logs/`
3. Note which step failed and the exact error message
4. Check if issue is specific to one server or affects all servers
5. Review `.codex/README.md` troubleshooting section
