# Troubleshooting FAQ - Common Issues & Solutions

## Quick Reference

- **Timeouts?** → Increase timeout to 120 seconds
- **SDK not working?** → Install Claude CLI globally: `npm install -g @anthropic-ai/claude-code`
- **Lost work?** → Check `.amplifier/sessions/` for recovery
- **Slow generation?** → Run agents in parallel, not sequentially
- **Type errors?** → Run `make check` before testing

---

## Setup Issues

### Q: "Claude CLI not found" error
**Symptom**: `RuntimeError: Claude CLI not found`

**Solution**:
```bash
# Install globally (required)
npm install -g @anthropic-ai/claude-code

# Verify installation
which claude  # Should show path like /usr/local/bin/claude

# If using nvm, might need to refresh
nvm use stable
npm install -g @anthropic-ai/claude-code
```

### Q: "No module named claude_code_sdk"
**Symptom**: Import error when running the tool

**Solution**:
```bash
# Install with uv (preferred)
uv add claude-code-sdk

# Or with pip
pip install claude-code-sdk

# Verify
python -c "import claude_code_sdk; print('SDK installed')"
```

### Q: API key not set
**Symptom**: `ANTHROPIC_API_KEY not set`

**Solution**:
```bash
# Set in environment
export ANTHROPIC_API_KEY="sk-ant-..."

# Or add to .env file
echo 'ANTHROPIC_API_KEY="sk-ant-..."' >> .env

# Or in Python directly
import os
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."
```

---

## Runtime Issues

### Q: Microtask timeouts frequently
**Symptom**: "Timeout after 10 seconds" errors

**Root Cause**: Some operations need more time, especially SPO extraction

**Solution**:
```python
# Increase timeout for complex operations
class ComplexAgent(MicrotaskAgent):
    def __init__(self):
        super().__init__(task_type="complex", timeout=30)  # 30 seconds

# For SDK operations, always use 120 seconds
async with asyncio.timeout(120):  # Standard for Claude SDK
    result = await sdk_operation()
```

### Q: Empty results from knowledge extraction
**Symptom**: Extraction returns empty but no error shown

**Causes & Solutions**:

1. **SDK timeout (most common)**:
   ```python
   # Ensure 120-second timeout for SDK
   async with asyncio.timeout(120):  # NOT 10 or 30
       result = await extract()
   ```

2. **Nested async loops**:
   ```python
   # BAD - nested event loops
   def extract(text):
       return asyncio.run(self._extract_async(text))

   # GOOD - properly async
   async def extract(text):
       return await self._extract_async(text)
   ```

3. **CLI not in PATH**:
   ```bash
   # Check CLI is accessible
   which claude || echo "CLI not found!"
   ```

### Q: Session recovery not working
**Symptom**: Can't resume after interruption

**Solution**:
```python
# Check session exists
import os
session_file = f".amplifier/sessions/{session_id}.json"
if not os.path.exists(session_file):
    print(f"Session not found: {session_id}")
    print("Available sessions:", os.listdir(".amplifier/sessions/"))

# Load with error handling
try:
    session = Session.load(session_id)
except FileNotFoundError:
    session = Session.new(tool_name)  # Start fresh
```

---

## Performance Issues

### Q: Tool generation takes too long
**Symptom**: Generation exceeds 15-minute target

**Solutions**:

1. **Run agents in parallel**:
   ```python
   # BAD - sequential
   result1 = await agent1.execute()
   result2 = await agent2.execute()

   # GOOD - parallel
   results = await asyncio.gather(
       agent1.execute(),
       agent2.execute()
   )
   ```

2. **Increase chunk size for processing**:
   ```python
   # Don't use tiny chunks
   config = ExtractionConfig(
       chunk_size=10000,  # Not 200!
   )
   ```

3. **Skip unnecessary retries**:
   ```python
   # Fail fast on non-recoverable errors
   if "authentication" in error_msg:
       raise  # Don't retry auth errors
   ```

### Q: High API token usage
**Symptom**: Using >10,000 tokens per tool

**Solutions**:

1. **Use focused prompts**:
   ```python
   # BAD - vague prompt
   "Analyze this and do what's needed"

   # GOOD - specific prompt
   "Extract the core problem statement in 1-2 sentences"
   ```

2. **Limit context in prompts**:
   ```python
   # Only include relevant data
   prompt = f"Analyze: {data[:1000]}"  # Truncate if needed
   ```

---

## Quality Issues

### Q: Generated code has syntax errors
**Symptom**: Python syntax errors in generated modules

**Solution**:
```bash
# Always run checks before testing
make check  # Runs lint, format, type check

# Fix specific issues
ruff check --fix .  # Auto-fix what's possible
```

### Q: Generated tool doesn't follow patterns
**Symptom**: Missing incremental save, no recovery, etc.

**Solution**:
```python
# Ensure pattern library is included
from amplifier_tool_builder.patterns import (
    MICROTASK_PATTERN,
    INCREMENTAL_SAVE_PATTERN,
    RECOVERY_PATTERN
)

# Verify in generation prompt
prompt = f"""
Generate code that MUST include:
1. {MICROTASK_PATTERN}
2. {INCREMENTAL_SAVE_PATTERN}
3. {RECOVERY_PATTERN}
"""
```

### Q: Tests failing for generated code
**Symptom**: Generated tests don't pass

**Solutions**:

1. **Mock external dependencies**:
   ```python
   @patch('claude_code_sdk.ClaudeSDKClient')
   async def test_agent(mock_client):
       # Test without real API calls
   ```

2. **Use test fixtures**:
   ```python
   # Create test data
   @pytest.fixture
   def sample_spec():
       return ToolSpecification(name="test", ...)
   ```

---

## Data Issues

### Q: File I/O errors (OSError errno 5)
**Symptom**: Random I/O errors when saving files

**Root Cause**: Cloud sync services (OneDrive, Dropbox) delaying file access

**Solution**:
```python
# Use retry logic for file operations
from amplifier.utils.file_io import write_json, read_json

# These handle retries automatically
write_json(data, filepath)
data = read_json(filepath)

# Or implement retry manually
for attempt in range(3):
    try:
        with open(file, 'w') as f:
            json.dump(data, f)
        break
    except OSError as e:
        if e.errno == 5 and attempt < 2:
            time.sleep(1)
        else:
            raise
```

### Q: Session corruption
**Symptom**: Can't load session, JSON decode error

**Solution**:
```python
# Add corruption handling
try:
    with open(session_file) as f:
        data = json.load(f)
except json.JSONDecodeError:
    # Try backup
    backup = session_file.with_suffix('.backup')
    if backup.exists():
        with open(backup) as f:
            data = json.load(f)
    else:
        # Start fresh
        data = {"status": "new"}
```

---

## Integration Issues

### Q: MCP server connection fails
**Symptom**: Can't connect to MCP tools

**Solution**:
```bash
# Check MCP server is running
ps aux | grep mcp

# Start if needed
npm run mcp-server

# Verify endpoint
curl http://localhost:3000/health
```

### Q: Parallel execution not working
**Symptom**: Tasks still run sequentially

**Common Mistakes**:
```python
# WRONG - await blocks
tasks = []
for item in items:
    result = await process(item)  # Blocks!
    tasks.append(result)

# RIGHT - gather all
tasks = [process(item) for item in items]
results = await asyncio.gather(*tasks)
```

---

## Development Issues

### Q: Changes not taking effect
**Symptom**: Edits to code don't seem to work

**Solutions**:

1. **Restart Python interpreter**:
   ```bash
   # Full restart to reload modules
   exit()
   python
   ```

2. **Clear Python cache**:
   ```bash
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -type d -delete
   ```

3. **Reinstall in development mode**:
   ```bash
   pip install -e .
   ```

### Q: Can't run tests
**Symptom**: pytest not found or import errors

**Solution**:
```bash
# Ensure in virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install test dependencies
uv add --dev pytest pytest-asyncio pytest-cov

# Run tests
make test
```

---

## Debugging Techniques

### Enable Verbose Logging
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Trace Microtask Execution
```python
import time

class DebugAgent(MicrotaskAgent):
    async def execute(self, input_data):
        start = time.time()
        logger.info(f"Starting {self.task_type}")

        try:
            result = await super().execute(input_data)
            duration = time.time() - start
            logger.info(f"Completed {self.task_type} in {duration:.2f}s")
            return result
        except Exception as e:
            logger.error(f"Failed {self.task_type}: {e}")
            raise
```

### Inspect Session State
```python
# Debug helper to examine session
def debug_session(session_id):
    path = f".amplifier/sessions/{session_id}.json"
    with open(path) as f:
        data = json.load(f)

    print(f"Status: {data.get('status')}")
    print(f"Stage: {data.get('current_stage')}")
    print(f"Completed: {data.get('completed_agents', [])}")
    print(f"Last error: {data.get('last_error')}")

    return data
```

---

## Prevention Checklist

### Before Starting Development
- [ ] Claude CLI installed globally
- [ ] API key set in environment
- [ ] Virtual environment activated
- [ ] Dependencies installed with `uv sync`
- [ ] `make check` runs successfully

### During Development
- [ ] Save after EVERY operation
- [ ] Use 120-second timeout for SDK
- [ ] Run agents in parallel when possible
- [ ] Test recovery from interruption
- [ ] Check file permissions for cloud-synced folders

### Before Testing
- [ ] Run `make check` for syntax/type errors
- [ ] Clear Python cache if needed
- [ ] Check session directory exists
- [ ] Verify API key is valid
- [ ] Ensure Claude CLI is in PATH

---

## Getting More Help

### Check Logs
```bash
# View recent errors
tail -f .amplifier/logs/error.log

# Search for specific issues
grep -r "timeout" .amplifier/logs/
```

### Test Individual Components
```python
# Test a single agent
python -c "
import asyncio
from amplifier_tool_builder.agents.requirements import ProblemIdentifier
asyncio.run(ProblemIdentifier().execute({'description': 'test'}))
"
```

### Contact Support
1. Check this FAQ first
2. Review error logs
3. Create minimal reproduction case
4. File issue with:
   - Error message
   - Steps to reproduce
   - Environment details
   - Relevant logs

---

## Quick Fixes Reference

| Problem | Quick Fix |
|---------|-----------|
| Timeout | Use 120 seconds for SDK |
| No CLI | `npm install -g @anthropic-ai/claude-code` |
| Lost work | Check `.amplifier/sessions/` |
| Slow | Run parallel with `asyncio.gather()` |
| I/O error | Add retry logic |
| Import error | `uv sync` to install deps |
| Type error | `make check` before running |
| Empty result | Check timeout and async handling |

Remember: Most issues come from timeouts, missing CLI, or sequential execution. Start with these three!