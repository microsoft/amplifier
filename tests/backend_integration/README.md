class TestClaudeSessionWorkflow:    # Claude Code specific tests
class TestCodexSessionWorkflow:     # Codex specific tests  
class TestCrossBackendWorkflows:    # Tests that work with both backends
```

This organization allows running tests for specific backends using pytest markers.

## Running Tests

### Run All Integration Tests

```bash
pytest tests/backend_integration/ -v
```

### Run Specific Workflow Tests

```bash
pytest tests/backend_integration/test_session_workflows.py -v
pytest tests/backend_integration/test_agent_workflows.py -v
pytest tests/backend_integration/test_mcp_server_integration.py -v
```

### Run Tests for Specific Backend

```bash
pytest tests/backend_integration/ -k "claude" -v
pytest tests/backend_integration/ -k "codex" -v
```

### Run with Coverage

```bash
pytest tests/backend_integration/ --cov=amplifier.core --cov=.codex/mcp_servers --cov-report=html
```

Coverage reports help identify untested code paths and ensure comprehensive validation.

## Test Fixtures

The `conftest.py` file provides shared fixtures that create realistic test environments. Fixtures are designed to be composable and reusable across test files.

### Backend Setup Fixtures

```python
@pytest.fixture
def mock_claude_cli():  # Mock subprocess calls to `claude` CLI
@pytest.fixture  
def mock_codex_cli():   # Mock subprocess calls to `codex` CLI
@pytest.fixture
def mock_both_backends_available():  # Both backends available
@pytest.fixture
def mock_only_claude_available():    # Only Claude available
@pytest.fixture
def mock_only_codex_available():     # Only Codex available
```

### Project Structure Fixtures

```python
@pytest.fixture
def integration_test_project(temp_dir):  # Complete project with .claude/ and .codex/
@pytest.fixture
def claude_project(temp_dir):            # Project with only .claude/ setup
@pytest.fixture
def codex_project(temp_dir):             # Project with only .codex/ setup
```

### Memory System Fixtures

```python
@pytest.fixture
def mock_memory_system():        # Mock complete memory system
@pytest.fixture
def sample_memories():           # List of sample Memory objects
@pytest.fixture
def sample_messages():           # List of sample conversation messages
```

### Environment Fixtures

```python
@pytest.fixture
def clean_env(monkeypatch):      # Clear all AMPLIFIER_* variables
@pytest.fixture
def claude_env(monkeypatch):     # Set AMPLIFIER_BACKEND=claude
@pytest.fixture
def codex_env(monkeypatch):      # Set AMPLIFIER_BACKEND=codex
@pytest.fixture
def memory_enabled_env(monkeypatch):   # MEMORY_SYSTEM_ENABLED=true
@pytest.fixture
def memory_disabled_env(monkeypatch):  # MEMORY_SYSTEM_ENABLED=false
```

### Fixture Composition Example

```python
def test_claude_complete_session_workflow(
    integration_test_project,    # Project structure
    mock_memory_system,          # Memory system mock
    mock_claude_cli,             # CLI mock
    memory_enabled_env           # Environment setup
):
    # Test uses all these fixtures together
```

## Mocking Strategy

### Approach

Integration tests mock at subprocess boundaries to avoid requiring real CLIs while testing real backend logic. This validates command construction, argument passing, and orchestration without external dependencies.

### What Is Mocked

- **CLI Calls**: `subprocess.run()` calls to `claude`, `codex`, `make check`
- **Amplifier Modules**: Memory system components (optional, for isolation)
- **File I/O**: Selective mocking of file operations (when testing logic, not effects)
- **External APIs**: Claude Code SDK calls, network requests

### What Is NOT Mocked

- **Backend Abstraction Logic**: Real `ClaudeCodeBackend` and `CodexBackend` classes
- **Configuration Loading**: Real Pydantic config validation and precedence
- **Argument Parsing**: Real CLI argument processing in `amplify.py`
- **MCP Protocol**: Real JSON-RPC message formatting and parsing

### Why This Approach

- **Validates Real Code Paths**: Tests exercise actual backend abstraction logic
- **Avoids External Dependencies**: No need to install Claude CLI or Codex CLI
- **Fast and Reliable**: Tests run quickly without network calls or subprocess overhead
- **Deterministic**: Fixed mock responses ensure consistent test results
- **Maintainable**: Changes to backend logic are caught by tests

## Test Patterns

### Session Workflow Pattern

```python
def test_claude_complete_session_workflow(integration_test_project, mock_memory_system):
    # 1. Setup: Create project structure and mock dependencies
    backend = ClaudeCodeBackend()
    
    # 2. Initialize: Call backend.initialize_session()
    result = backend.initialize_session("test prompt")
    assert result["success"] == True
    
    # 3. Work: Simulate code editing, tool usage
    # (In real usage, this would be interactive work)
    
    # 4. Check: Call backend.run_quality_checks()
    quality_result = backend.run_quality_checks()
    assert quality_result["success"] == True
    
    # 5. Finalize: Call backend.finalize_session()
    messages = [{"role": "user", "content": "test"}]
    final_result = backend.finalize_session(messages)
    assert final_result["success"] == True
    
    # 6. Verify: Assert files created, memory updated, results correct
    assert Path(".data/transcripts/compact_*.txt").exists()
    # Verify memory system was called correctly
```

### Agent Workflow Pattern

```python
def test_claude_spawn_single_agent(integration_test_project, mock_claude_sdk, create_test_agents):
    # 1. Setup: Create agent definitions
    agent_name = "test-agent"
    
    # 2. Spawn: Call backend.spawn_agent()
    backend = ClaudeCodeAgentBackend()
    result = backend.spawn_agent(agent_name, "test task")
    
    # 3. Verify: Assert subprocess called correctly, response structure valid
    assert result["success"] == True
    assert "output" in result
    
    # 4. Check: Verify agent output is captured
    assert len(result["output"]) > 0
```

### MCP Server Pattern

```python
def test_initialize_session_tool_via_mcp(integration_test_project, mock_memory_system):
    # 1. Start: Launch MCP server as subprocess
    server_process = subprocess.Popen([...])
    
    # 2. Call: Send JSON-RPC tool call via stdin
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "initialize_session",
            "arguments": {"prompt": "test"}
        }
    }
    server_process.stdin.write(json.dumps(request).encode())
    
    # 3. Receive: Read JSON-RPC response from stdout
    response = json.loads(server_process.stdout.readline())
    
    # 4. Verify: Assert response format and content
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert response["result"]["success"] == True
    
    # 5. Shutdown: Stop server gracefully
    server_process.terminate()
```

## Common Issues

### Import Errors in Tests

**Symptoms**: `ModuleNotFoundError` or `ImportError` when running tests.

**Causes**:
- Project root not in `sys.path`
- Amplifier modules not importable
- Incorrect fixture imports

**Solutions**:
```python
# Ensure project root is in path
import sys
sys.path.insert(0, Path(__file__).parent.parent.parent)

# Check amplifier modules are importable
from amplifier.core.backend import BackendFactory
```

### Async Test Failures

**Symptoms**: Tests fail with async-related errors.

**Solutions**:
- Use `@pytest.mark.asyncio` decorator for async tests
- Install `pytest-asyncio` plugin
- Use `await` for async function calls

```python
@pytest.mark.asyncio
async def test_async_backend_operation():
    result = await backend.async_method()
```

### Mock Not Working

**Symptoms**: Mocked functions not being called or returning unexpected values.

**Solutions**:
- Verify mock patch path uses full module path
- Ensure mock is applied before function is called
- Use `return_value` for sync, `side_effect` for async

```python
# Correct: Full module path
@patch('amplifier.core.backend.subprocess.run')
def test_backend_call(mock_subprocess):
    mock_subprocess.return_value = Mock(returncode=0)
    # Test code