# Backend Abstraction Layer

The backend abstraction layer provides a unified API for working with both Claude Code and Codex backends, enabling seamless switching between development environments while maintaining feature parity.

## Overview

### Purpose

The backend abstraction layer solves the challenge of supporting dual AI development backends (Claude Code and Codex) with different architectures and integration patterns. Instead of maintaining separate code paths for each backend, the abstraction layer provides a single, consistent interface for:

- Session management (initialization and finalization)
- Quality checks
- Transcript export
- Agent spawning

### Problem Solved

Before this abstraction layer, code had to directly import backend-specific modules like `ClaudeCodeOptions` and `ClaudeSDKClient`, creating tight coupling and making it difficult to:

- Switch between backends
- Test backend operations
- Add support for new backends
- Maintain backward compatibility

### Key Benefits

- **Unified API**: Single interface regardless of backend
- **Easy Backend Switching**: Change backends via environment variable
- **Testability**: Mock backends for comprehensive testing
- **Extensibility**: Add new backends without changing existing code
- **Backward Compatibility**: Existing code continues to work unchanged

## Architecture

The backend abstraction layer consists of three main modules organized in the `amplifier/core/` directory:

### Core Modules

#### `backend.py` - Core Backend Abstraction

Provides the main `AmplifierBackend` abstract base class and concrete implementations for session management, quality checks, and transcript export.

- **Abstract Base Class**: `AmplifierBackend` defines the interface
- **Concrete Implementations**: `ClaudeCodeBackend`, `CodexBackend`
- **Factory Pattern**: `BackendFactory` for backend instantiation

#### `agent_backend.py` - Agent Spawning Abstraction

Handles the differences between Claude Code's Task tool and Codex's `codex exec` command for agent spawning.

- **Abstract Base Class**: `AgentBackend` defines agent operations
- **Concrete Implementations**: `ClaudeCodeAgentBackend`, `CodexAgentBackend`
- **Factory Pattern**: `AgentBackendFactory` for agent backend instantiation

#### `config.py` - Backend Configuration Management

Centralizes all backend-related configuration using Pydantic settings.

- **Configuration Class**: `BackendConfig` with environment variable integration
- **Validation**: Backend type and path validation
- **Utilities**: Auto-detection and availability checking

### Factory Pattern

The abstraction uses factory patterns to instantiate appropriate backend implementations:

```python
# Backend Factory
backend = BackendFactory.create_backend()  # Uses AMPLIFIER_BACKEND env var

# Agent Backend Factory  
agent_backend = AgentBackendFactory.create_agent_backend()
```

### Class Hierarchy

```
AmplifierBackend (ABC)
├── ClaudeCodeBackend
└── CodexBackend

AgentBackend (ABC)
├── ClaudeCodeAgentBackend
└── CodexAgentBackend

BackendConfig (Pydantic BaseSettings)
└── Global instance: backend_config
```

## Quick Start

### Basic Usage

```python
from amplifier import get_backend

# Get backend (uses AMPLIFIER_BACKEND env var)
backend = get_backend()

# Initialize session with memory loading
result = backend.initialize_session(
    prompt="Working on authentication feature",
    context="Refactoring login flow"
)
print(f"Loaded {result['metadata']['memoriesLoaded']} memories")

# Finalize session with memory extraction
messages = [{"role": "user", "content": "..."}]
result = backend.finalize_session(messages)
print(f"Extracted {result['metadata']['memoriesExtracted']} memories")

# Run quality checks
result = backend.run_quality_checks(["src/auth.py", "src/api.py"])
if result['success']:
    print("Quality checks passed!")

# Export transcript
result = backend.export_transcript(format="extended")
print(f"Transcript saved to {result['data']['path']}")
```

### Return Format

All methods return a consistent format:

```python
{
    "success": bool,           # Operation success status
    "data": Any,              # Operation-specific data
    "metadata": Dict[str, Any] # Additional metadata
}
```

## Agent Spawning

### Basic Agent Spawning

```python
# Spawn a sub-agent
from amplifier import spawn_agent

result = spawn_agent(
    agent_name="bug-hunter",
    task="Find potential bugs in src/auth.py"
)
print(result['result'])

# List available agents
from amplifier import get_agent_backend

agent_backend = get_agent_backend()
agents = agent_backend.list_available_agents()
print(f"Available agents: {', '.join(agents)}")
```

### Agent Definition Format

Agents are defined in backend-specific directories:

- **Claude Code**: `.claude/agents/{agent_name}.md`
- **Codex**: `.codex/agents/{agent_name}.md`

Agent definitions use YAML frontmatter for configuration:

```markdown
---
name: bug-hunter
description: Finds potential bugs in code
allowed_tools: [grep_search, read_file]
max_turns: 10
---

You are a bug hunting specialist...
```

## Backend Selection

### Selection Methods

#### 1. Environment Variable (Recommended)

```bash
# Use Claude Code
export AMPLIFIER_BACKEND=claude

# Use Codex
export AMPLIFIER_BACKEND=codex
```

#### 2. Programmatic Selection

```python
from amplifier import set_backend

# Set backend programmatically
set_backend("codex")
```

#### 3. Auto-Detection

```bash
# Enable auto-detection
export AMPLIFIER_BACKEND_AUTO_DETECT=true
```

### Precedence Order

1. **Programmatic**: `set_backend()` calls (highest precedence)
2. **Environment Variable**: `AMPLIFIER_BACKEND` env var
3. **Auto-Detection**: When `AMPLIFIER_BACKEND_AUTO_DETECT=true`
4. **Default**: "claude" (lowest precedence)

### Checking Active Backend

```python
from amplifier import get_backend

backend = get_backend()
print(f"Active backend: {backend.get_backend_name()}")

# Check availability
if backend.is_available():
    print("Backend is available")
```

## Configuration

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `AMPLIFIER_BACKEND` | Backend selection | `"claude"` | `"codex"` |
| `AMPLIFIER_BACKEND_AUTO_DETECT` | Auto-detect backend | `true` | `false` |
| `CLAUDE_CLI_PATH` | Path to Claude CLI | Auto-detected | `"/usr/local/bin/claude"` |
| `CODEX_CLI_PATH` | Path to Codex CLI | Auto-detected | `"/usr/local/bin/codex"` |
| `CODEX_PROFILE` | Codex profile to use | `"development"` | `"ci"` |
| `MEMORY_SYSTEM_ENABLED` | Enable memory system | `true` | `false` |

### Configuration Examples

```bash
# Basic Claude Code setup
export AMPLIFIER_BACKEND=claude

# Codex with custom CLI path
export AMPLIFIER_BACKEND=codex
export CODEX_CLI_PATH=/opt/codex/bin/codex
export CODEX_PROFILE=development

# Auto-detection with memory disabled
export AMPLIFIER_BACKEND_AUTO_DETECT=true
export MEMORY_SYSTEM_ENABLED=false
```

### Overriding for Testing

```python
from amplifier.core.config import BackendConfig

# Override configuration for testing
config = BackendConfig(
    amplifier_backend="codex",
    memory_system_enabled=False
)
```

## Backend Comparison

### Feature Comparison

| Feature | Claude Code | Codex |
|---------|-------------|-------|
| **Session Management** | Native hooks | MCP servers + standalone scripts |
| **Agent Spawning** | Task tool | `codex exec` command |
| **Configuration** | JSON (`settings.json`) | TOML (`config.toml`) |
| **Transcript Format** | Single file (`compact_*.txt`) | Directory per session |
| **Availability** | VS Code extension | Standalone CLI |
| **Integration** | Automatic hooks | Manual MCP server calls |

### When to Use Each Backend

#### Claude Code
- **Best for**: VS Code users, automatic integration, seamless workflow
- **Advantages**: Native hooks, automatic session management, integrated UI
- **Use when**: Working primarily in VS Code, want automatic quality checks

#### Codex
- **Best for**: CLI users, custom workflows, standalone development
- **Advantages**: Standalone CLI, MCP server extensibility, cross-editor support
- **Use when**: Working outside VS Code, need programmatic control, custom integrations

### Feature Parity

- **Full Parity**: Memory system integration, quality checks, transcript export
- **Backend-Specific**: Agent spawning mechanisms, session storage locations
- **Unified**: All features accessible through abstraction layer

## Advanced Usage

### Custom Backend Implementation

```python
from amplifier.core.backend import AmplifierBackend
from typing import Dict, Any, List, Optional

class CustomBackend(AmplifierBackend):
    def initialize_session(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        # Custom implementation
        return {
            "success": True,
            "data": {"context": "Custom context"},
            "metadata": {"memoriesLoaded": 0}
        }
    
    def finalize_session(self, messages: List[Dict[str, Any]], context: Optional[str] = None) -> Dict[str, Any]:
        # Custom implementation
        return {
            "success": True,
            "data": {},
            "metadata": {"memoriesExtracted": 0}
        }
    
    def run_quality_checks(self, file_paths: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        # Custom implementation
        return {
            "success": True,
            "data": {"output": "Checks passed"},
            "metadata": {}
        }
    
    def export_transcript(self, session_id: Optional[str] = None, format: str = "standard", output_dir: Optional[str] = None) -> Dict[str, Any]:
        # Custom implementation
        return {
            "success": True,
            "data": {"path": "/path/to/transcript"},
            "metadata": {}
        }
    
    def get_backend_name(self) -> str:
        return "custom"
    
    def is_available(self) -> bool:
        return True
```

### Testing Strategies

#### Mocking Backends

```python
import pytest
from unittest.mock import Mock
from amplifier.core.backend import AmplifierBackend

@pytest.fixture
def mock_backend():
    backend = Mock(spec=AmplifierBackend)
    backend.initialize_session.return_value = {
        "success": True,
        "data": {"context": "Mock context"},
        "metadata": {"memoriesLoaded": 5}
    }
    backend.get_backend_name.return_value = "mock"
    backend.is_available.return_value = True
    return backend

def test_session_workflow(mock_backend):
    result = mock_backend.initialize_session("Test prompt")
    assert result["success"] is True
    assert result["metadata"]["memoriesLoaded"] == 5
```

#### Integration Testing

```python
def test_backend_integration():
    # Test with real backend
    backend = get_backend()
    
    # Skip if backend not available
    if not backend.is_available():
        pytest.skip(f"Backend {backend.get_backend_name()} not available")
    
    # Test actual functionality
    result = backend.initialize_session("Integration test")
    assert result["success"] is True
```

### Async Usage

```python
import asyncio
from amplifier import get_backend

async def async_session_workflow():
    backend = get_backend()
    
    # Initialize session
    result = await asyncio.to_thread(
        backend.initialize_session,
        "Async workflow"
    )
    
    # Process results
    if result["success"]:
        print(f"Loaded {result['metadata']['memoriesLoaded']} memories")
    
    # Finalize session
    messages = [{"role": "user", "content": "Async test"}]
    result = await asyncio.to_thread(
        backend.finalize_session,
        messages
    )
    
    return result

# Run async workflow
asyncio.run(async_session_workflow())
```

## API Reference

### AmplifierBackend (Abstract Base Class)

#### Methods

##### `initialize_session(prompt: str, context: Optional[str] = None) -> Dict[str, Any]`

Load relevant memories at session start.

**Parameters:**
- `prompt` (str): Session prompt for memory search
- `context` (Optional[str]): Additional context

**Returns:** Dict with success status, context data, and metadata

##### `finalize_session(messages: List[Dict[str, Any]], context: Optional[str] = None) -> Dict[str, Any]`

Extract and store memories at session end.

**Parameters:**
- `messages` (List[Dict]): Session messages for extraction
- `context` (Optional[str]): Additional context

**Returns:** Dict with success status and extraction metadata

##### `run_quality_checks(file_paths: List[str], cwd: Optional[str] = None) -> Dict[str, Any]`

Run code quality checks on specified files.

**Parameters:**
- `file_paths` (List[str]): Files to check
- `cwd` (Optional[str]): Working directory

**Returns:** Dict with success status and check results

##### `export_transcript(session_id: Optional[str] = None, format: str = "standard", output_dir: Optional[str] = None) -> Dict[str, Any]`

Export session transcript.

**Parameters:**
- `session_id` (Optional[str]): Specific session ID
- `format` (str): Export format ("standard", "extended", "compact")
- `output_dir` (Optional[str]): Output directory

**Returns:** Dict with success status and export path

##### `get_backend_name() -> str`

Return backend identifier.

**Returns:** Backend name ("claude" or "codex")

##### `is_available() -> bool`

Check if backend is available.

**Returns:** True if backend is configured and available

### AgentBackend (Abstract Base Class)

#### Methods

##### `spawn_agent(agent_name: str, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`

Spawn a sub-agent with given task.

**Parameters:**
- `agent_name` (str): Name of agent to spawn
- `task` (str): Task for agent to perform
- `context` (Optional[Dict]): Additional context

**Returns:** Dict with success status and agent result

##### `list_available_agents() -> List[str]`

List available agent definitions.

**Returns:** List of agent names

##### `get_agent_definition(agent_name: str) -> Optional[str]`

Get agent definition content.

**Parameters:**
- `agent_name` (str): Agent name

**Returns:** Agent definition content or None

##### `validate_agent_exists(agent_name: str) -> bool`

Check if agent definition exists.

**Parameters:**
- `agent_name` (str): Agent name

**Returns:** True if agent exists

### BackendConfig (Configuration Class)

#### Attributes

- `amplifier_backend: str` - Backend selection
- `amplifier_backend_auto_detect: bool` - Auto-detect flag
- `claude_cli_path: Optional[str]` - Claude CLI path
- `codex_cli_path: Optional[str]` - Codex CLI path
- `codex_profile: str` - Codex profile
- `memory_system_enabled: bool` - Memory system flag

#### Methods

##### `validate_backend() -> None`

Validate backend configuration.

##### `get_backend_cli_path(backend: str) -> Optional[str]`

Get CLI path for specified backend.

### Factory Classes

#### BackendFactory

##### `create_backend(backend_type: Optional[str] = None) -> AmplifierBackend`

Create backend instance.

##### `get_available_backends() -> List[str]`

Get list of available backends.

##### `auto_detect_backend() -> str`

Auto-detect available backend.

#### AgentBackendFactory

##### `create_agent_backend(backend_type: Optional[str] = None) -> AgentBackend`

Create agent backend instance.

### Convenience Functions

#### `get_backend() -> AmplifierBackend`

Get backend instance using configuration.

#### `set_backend(backend_type: str) -> None`

Set backend type.

#### `spawn_agent(agent_name: str, task: str, backend: Optional[str] = None) -> Dict[str, Any]`

Spawn agent with optional backend override.

#### `get_agent_backend() -> AgentBackend`

Get agent backend instance.

## Troubleshooting

### Common Issues

#### Backend Not Available

**Error:** `BackendNotAvailableError`

**Solutions:**
```bash
# Check backend availability
python -c "from amplifier import get_backend; print(get_backend().is_available())"

# Install missing CLI
# Claude Code: Install VS Code extension
# Codex: Follow Anthropic's installation guide

# Check CLI paths
which claude  # For Claude Code
which codex   # For Codex
```

#### Environment Variable Not Recognized

**Error:** Backend selection ignored

**Solutions:**
```bash
# Check environment variable
echo $AMPLIFIER_BACKEND

# Set variable properly
export AMPLIFIER_BACKEND=codex

# Restart Python session (environment variables aren't reloaded)
```

#### Import Errors

**Error:** `ModuleNotFoundError`

**Solutions:**
```bash
# Install dependencies
uv add pydantic python-dotenv

# Check Python path
python -c "import amplifier.core.backend"

# Verify package structure
ls amplifier/core/
```

#### Backend Operation Failures

**Error:** Operations return `success: false`

**Solutions:**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check backend logs
# Claude Code: Check VS Code output
# Codex: Check .codex/logs/

# Test backend availability
from amplifier import get_backend
backend = get_backend()
print(f"Backend: {backend.get_backend_name()}")
print(f"Available: {backend.is_available()}")
```

### Debug Logging

```python
import logging
from amplifier.core.backend import BackendFactory

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s'
)

# Create backend with logging
backend = BackendFactory.create_backend()
```

### Checking Backend Availability

```python
from amplifier.core.config import get_backend_config

config = get_backend_config()

# Check backend availability
available = config.is_backend_available("codex")
print(f"Codex available: {available}")

# Get backend info
info = config.get_backend_info("codex")
print(f"CLI path: {info.get('cli_path')}")
print(f"Config dir: {info.get('config_dir')}")
```

## Migration Guide

### Before (Direct Backend Usage)

```python
# Direct Claude Code imports
from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient
from amplifier.memory import MemoryStore
from amplifier.search import MemorySearcher

# Manual session initialization
store = MemoryStore()
searcher = MemorySearcher()
memories = store.get_all()
results = searcher.search(prompt, memories)

# Format context manually
context = "\n".join([f"- {m.content}" for m in results])
```

### After (Backend Abstraction)

```python
# Unified API
from amplifier import get_backend

# Automatic backend selection
backend = get_backend()

# Single method call
result = backend.initialize_session(prompt)
context = result["data"]["context"]
```

### Backward Compatibility

- **Existing Code**: Continues to work unchanged
- **New Code**: Can use abstraction layer optionally
- **Migration**: Gradual, no breaking changes
- **Environment Variables**: Same variables work with both approaches

### Breaking Changes

None. The abstraction layer is purely additive and maintains full backward compatibility.

## Design Principles

### Interface-Based Design

The abstraction uses abstract base classes to define clear contracts:

- **AmplifierBackend**: Defines core backend operations
- **AgentBackend**: Defines agent spawning operations
- **Consistent Returns**: All methods return structured dictionaries

### Factory Pattern Rationale

Factories provide:
- **Configuration-Driven**: Environment variable selection
- **Validation**: Backend type and availability checking
- **Extensibility**: Easy addition of new backends
- **Testing**: Mock factory injection for tests

### Abstract vs Concrete Methods

- **Abstract Methods**: Core operations that must be implemented by each backend
- **Concrete Methods**: Common utilities shared across backends
- **Thin Implementations**: Backends delegate to existing code, don't duplicate logic

### Error Handling Strategy

- **Custom Exceptions**: Specific error types for different failure modes
- **Graceful Degradation**: Operations fail safely without breaking workflows
- **Detailed Logging**: Comprehensive logging for debugging
- **Timeout Protection**: Operations protected against hanging

## Future Enhancements

### Planned Features

- **Async Support**: Native async/await support for all operations
- **Backend Plugins**: Dynamic loading of custom backends
- **Metrics Collection**: Performance and usage metrics
- **Caching Layer**: Response caching for improved performance
- **Batch Operations**: Bulk processing for multiple sessions

### Potential New Backends

- **Cursor**: Anthropic's new IDE integration
- **Windsor**: Microsoft's AI coding assistant
- **GitHub Copilot**: Extended integration capabilities
- **Custom AI Services**: Generic backend for custom AI APIs

### Areas for Improvement

- **Performance**: Optimize memory search and extraction
- **Error Recovery**: Automatic retry mechanisms
- **Monitoring**: Health checks and alerting
- **Documentation**: Interactive API documentation
- **Testing**: More comprehensive integration tests

### Roadmap Links

- [Backend Abstraction Issues](https://github.com/your-repo/issues?q=backend+abstraction)
- [Future Backend Support](https://github.com/your-repo/issues?q=new+backend)
- [Performance Optimization](https://github.com/your-repo/issues?q=backend+performance)