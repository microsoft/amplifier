"""
Shared fixtures for backend integration tests.

This file provides comprehensive fixtures for testing backend integration workflows,
including project structures, mocking, environment setup, and sample data.
"""

import json
import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


# 1. Backend Setup Fixtures

@pytest.fixture
def mock_claude_cli():
    """Mock subprocess calls to `claude` CLI with configurable exit codes and output."""
    def _mock_claude_cli(exit_code=0, stdout="Claude Code executed successfully", stderr=""):
        result = Mock()
        result.returncode = exit_code
        result.stdout = stdout
        result.stderr = stderr
        return result
    return _mock_claude_cli


@pytest.fixture
def mock_codex_cli():
    """Mock subprocess calls to `codex` CLI with configurable exit codes and output."""
    def _mock_codex_cli(exit_code=0, stdout="Codex executed successfully", stderr=""):
        result = Mock()
        result.returncode = exit_code
        result.stdout = stdout
        result.stderr = stderr
        return result
    return _mock_codex_cli


@pytest.fixture
def mock_both_backends_available():
    """Mock both backends as available for testing backend switching."""
    with patch('amplifier.core.backend.ClaudeCodeBackend.is_available', return_value=True), \
         patch('amplifier.core.backend.CodexBackend.is_available', return_value=True), \
         patch('amplifier.core.config.is_backend_available') as mock_is_available:
        
        def side_effect(backend):
            return backend in ['claude', 'codex']
        mock_is_available.side_effect = side_effect
        
        yield


@pytest.fixture
def mock_only_claude_available():
    """Mock only Claude Code available."""
    with patch('amplifier.core.backend.ClaudeCodeBackend.is_available', return_value=True), \
         patch('amplifier.core.backend.CodexBackend.is_available', return_value=False), \
         patch('amplifier.core.config.is_backend_available') as mock_is_available:
        
        def side_effect(backend):
            return backend == 'claude'
        mock_is_available.side_effect = side_effect
        
        yield


@pytest.fixture
def mock_only_codex_available():
    """Mock only Codex available."""
    with patch('amplifier.core.backend.ClaudeCodeBackend.is_available', return_value=False), \
         patch('amplifier.core.backend.CodexBackend.is_available', return_value=True), \
         patch('amplifier.core.config.is_backend_available') as mock_is_available:
        
        def side_effect(backend):
            return backend == 'codex'
        mock_is_available.side_effect = side_effect
        
        yield


# 2. Project Structure Fixtures

@pytest.fixture
def integration_test_project(temp_dir) -> Path:
    """Create complete project structure with both .claude/ and .codex/ directories."""
    project_dir = temp_dir / "integration_project"
    project_dir.mkdir()
    
    # Create .claude/ directory structure
    claude_dir = project_dir / ".claude"
    claude_dir.mkdir()
    
    # Claude settings.json
    settings = {
        "mcpServers": {},
        "globalTools": ["Read", "Grep"],
        "customInstructions": "Test project for backend integration."
    }
    (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2))
    
    # Claude agents directory
    agents_dir = claude_dir / "agents"
    agents_dir.mkdir()
    
    # Claude tools directory
    tools_dir = claude_dir / "tools"
    tools_dir.mkdir()
    
    # Create .codex/ directory structure
    codex_dir = project_dir / ".codex"
    codex_dir.mkdir()
    
    # Codex config.toml
    config_toml = """
[profile.development]
mcp_servers = ["session_manager", "quality_checker", "transcript_saver"]
tools = ["Read", "Write", "Grep", "Bash"]

[profile.ci]
mcp_servers = ["quality_checker"]
tools = ["Read", "Grep"]

[profile.review]
mcp_servers = ["quality_checker", "transcript_saver"]
tools = ["Read", "Write", "Grep"]
"""
    (codex_dir / "config.toml").write_text(config_toml)
    
    # Codex agents directory
    codex_agents_dir = codex_dir / "agents"
    codex_agents_dir.mkdir()
    
    # Codex mcp_servers directory
    mcp_servers_dir = codex_dir / "mcp_servers"
    mcp_servers_dir.mkdir()
    
    # Codex tools directory
    codex_tools_dir = codex_dir / "tools"
    codex_tools_dir.mkdir()
    
    # Create Makefile
    makefile = project_dir / "Makefile"
    makefile.write_text("""
check:
	@echo "Running checks..."
	uv run ruff check .
	uv run pyright .
	uv run pytest tests/

test:
	uv run pytest tests/

lint:
	uv run ruff check .

format:
	uv run ruff format --check .
""")
    
    # Create pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text("""
[project]
name = "integration-test-project"
version = "0.1.0"

[tool.uv]
dev-dependencies = ["pytest", "ruff", "pyright"]

[tool.ruff]
line-length = 120

[tool.pyright]
include = ["."]
""")
    
    # Create .git directory
    git_dir = project_dir / ".git"
    git_dir.mkdir()
    
    # Create sample Python files
    main_py = project_dir / "main.py"
    main_py.write_text("""
def main():
    print("Hello from integration test project")

if __name__ == "__main__":
    main()
""")
    
    test_py = project_dir / "tests" / "test_main.py"
    test_py.parent.mkdir()
    test_py.write_text("""
def test_main():
    assert True
""")
    
    # Create .data/ directory for memories and transcripts
    data_dir = project_dir / ".data"
    data_dir.mkdir()
    
    memories_dir = data_dir / "memories"
    memories_dir.mkdir()
    
    transcripts_dir = data_dir / "transcripts"
    transcripts_dir.mkdir()
    
    return project_dir


@pytest.fixture
def claude_project(temp_dir) -> Path:
    """Create project structure with only .claude/ setup."""
    project_dir = temp_dir / "claude_project"
    project_dir.mkdir()
    
    # Create .claude/ directory structure (same as integration_test_project)
    claude_dir = project_dir / ".claude"
    claude_dir.mkdir()
    
    settings = {
        "mcpServers": {},
        "globalTools": ["Read", "Grep"],
        "customInstructions": "Claude-only test project."
    }
    (claude_dir / "settings.json").write_text(json.dumps(settings, indent=2))
    
    agents_dir = claude_dir / "agents"
    agents_dir.mkdir()
    
    tools_dir = claude_dir / "tools"
    tools_dir.mkdir()
    
    # Create basic project files
    (project_dir / "pyproject.toml").write_text('[project]\nname = "claude-test"')
    (project_dir / ".git").mkdir()
    
    return project_dir


@pytest.fixture
def codex_project(temp_dir) -> Path:
    """Create project structure with only .codex/ setup."""
    project_dir = temp_dir / "codex_project"
    project_dir.mkdir()
    
    # Create .codex/ directory structure (same as integration_test_project)
    codex_dir = project_dir / ".codex"
    codex_dir.mkdir()
    
    config_toml = """
[profile.development]
mcp_servers = ["session_manager", "quality_checker", "transcript_saver"]
tools = ["Read", "Write", "Grep", "Bash"]
"""
    (codex_dir / "config.toml").write_text(config_toml)
    
    codex_agents_dir = codex_dir / "agents"
    codex_agents_dir.mkdir()
    
    mcp_servers_dir = codex_dir / "mcp_servers"
    mcp_servers_dir.mkdir()
    
    codex_tools_dir = codex_dir / "tools"
    codex_tools_dir.mkdir()
    
    # Create basic project files
    (project_dir / "pyproject.toml").write_text('[project]\nname = "codex-test"')
    (project_dir / ".git").mkdir()
    
    return project_dir


# 3. Memory System Fixtures

@pytest.fixture
def mock_memory_system():
    """Mock complete memory system (MemoryStore, MemorySearcher, MemoryExtractor) with sample data."""
    memory_store = Mock()
    memory_store.add_memories_batch.return_value = 5
    
    memory_searcher = Mock()
    memory_searcher.search.return_value = [
        {"content": "Relevant memory 1", "score": 0.9, "type": "fact"},
        {"content": "Relevant memory 2", "score": 0.8, "type": "pattern"},
    ]
    
    memory_extractor = Mock()
    memory_extractor.extract_from_messages.return_value = [
        {"content": "Extracted memory 1", "type": "fact"},
        {"content": "Extracted memory 2", "type": "pattern"},
    ]
    
    with patch('amplifier.memory.MemoryStore', return_value=memory_store), \
         patch('amplifier.search.MemorySearcher', return_value=memory_searcher), \
         patch('amplifier.extraction.MemoryExtractor', return_value=memory_extractor):
        
        yield {
            'store': memory_store,
            'searcher': memory_searcher,
            'extractor': memory_extractor
        }


@pytest.fixture
def sample_memories():
    """Return list of sample Memory objects for testing."""
    return [
        {
            "content": "Python functions should have docstrings",
            "type": "pattern",
            "score": 0.95,
            "timestamp": "2024-01-01T10:00:00Z"
        },
        {
            "content": "Use type hints for function parameters",
            "type": "fact",
            "score": 0.88,
            "timestamp": "2024-01-01T10:15:00Z"
        },
        {
            "content": "Handle exceptions gracefully in user-facing code",
            "type": "pattern",
            "score": 0.92,
            "timestamp": "2024-01-01T10:30:00Z"
        }
    ]


@pytest.fixture
def sample_messages():
    """Return list of sample conversation messages for extraction."""
    return [
        {"role": "user", "content": "How do I implement a memory system?"},
        {"role": "assistant", "content": "You need to create a MemoryStore class that can persist and retrieve memories based on relevance."},
        {"role": "user", "content": "What about searching memories?"},
        {"role": "assistant", "content": "Use semantic search with embeddings to find relevant memories for a given context."},
        {"role": "user", "content": "Should I use a database or files?"},
        {"role": "assistant", "content": "Start with JSON files for simplicity, then migrate to a database when needed."}
    ]


# 4. Agent Fixtures

@pytest.fixture
def sample_agent_definition():
    """Return complete agent definition markdown with YAML frontmatter."""
    return """---
name: test-agent
description: A test agent for backend integration testing
system_prompt: You are a helpful test agent that assists with software development tasks.
allowed_tools: [Read, Grep, Write]
max_turns: 10
model: gpt-4
---

# Test Agent

This agent is designed for testing backend integration workflows.

## Capabilities

- Reading and analyzing code files
- Searching through codebases
- Writing and modifying code
- Providing development assistance

## Usage

Use this agent for testing agent spawning and execution workflows.
"""


@pytest.fixture
def create_test_agents():
    """Create sample agent files in appropriate directory for given backend."""
    def _create_test_agents(project_dir: Path, backend: str, agent_count: int = 2):
        if backend == "claude":
            agents_dir = project_dir / ".claude" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            
            for i in range(agent_count):
                agent_file = agents_dir / f"test-agent-{i}.md"
                content = f"""---
name: test-agent-{i}
description: Test agent {i} for Claude Code
system_prompt: You are test agent {i}.
allowed_tools: [Read, Grep]
max_turns: 10
model: gpt-4
---

# Test Agent {i}

Content for test agent {i}.
"""
                agent_file.write_text(content)
                
        elif backend == "codex":
            agents_dir = project_dir / ".codex" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            
            for i in range(agent_count):
                agent_file = agents_dir / f"test-agent-{i}.md"
                content = f"""---
name: test-agent-{i}
description: Test agent {i} for Codex
system_prompt: You are test agent {i}.
allowed_tools: ["Read", "Grep", "Write"]
max_turns: 10
model: gpt-4
---

# Test Agent {i}

Content for test agent {i}.
"""
                agent_file.write_text(content)
    
    return _create_test_agents


@pytest.fixture
def mock_claude_sdk():
    """Mock Claude Code SDK for agent spawning tests."""
    mock_client = Mock()
    mock_client.send_task.return_value = {"result": "Agent executed successfully"}
    
    with patch('amplifier.core.agent_backend.ClaudeSDKClient', return_value=mock_client):
        yield mock_client


# 5. Session Fixtures

@pytest.fixture
def mock_codex_session_dir(temp_dir):
    """Create mock Codex session directory with history.jsonl, meta.json."""
    sessions_dir = temp_dir / ".codex" / "sessions"
    sessions_dir.mkdir(parents=True)
    
    session_id = "test_session_123456"
    session_dir = sessions_dir / session_id
    session_dir.mkdir()
    
    # Create meta.json
    meta = {
        "session_id": session_id,
        "started_at": "2024-01-01T10:00:00Z",
        "cwd": str(temp_dir / "project"),
        "profile": "development"
    }
    (session_dir / "meta.json").write_text(json.dumps(meta))
    
    # Create history.jsonl
    history = [
        {"session_id": session_id, "ts": 1704105600, "text": "User: How do I start a session?"},
        {"session_id": session_id, "ts": 1704105660, "text": "Assistant: Use the session_init.py script"},
        {"session_id": session_id, "ts": 1704105720, "text": "User: What about cleanup?"},
        {"session_id": session_id, "ts": 1704105780, "text": "Assistant: Use session_cleanup.py"}
    ]
    history_content = "\n".join(json.dumps(h) for h in history)
    (session_dir / "history.jsonl").write_text(history_content)
    
    return session_dir


@pytest.fixture
def mock_claude_transcript(temp_dir):
    """Create mock Claude Code transcript file."""
    transcripts_dir = temp_dir / ".data" / "transcripts"
    transcripts_dir.mkdir(parents=True)
    
    transcript_file = transcripts_dir / "compact_20240101_100000_session123.txt"
    content = """# Claude Code Session Transcript
# Started: 2024-01-01 10:00:00
# Session ID: session123

User: How do I implement a backend?
Assistant: You need to create an abstract base class and concrete implementations.

User: What about testing?
Assistant: Use comprehensive integration tests with mocking.

# End of transcript
"""
    transcript_file.write_text(content)
    
    return transcript_file


@pytest.fixture
def sample_session_data():
    """Return sample session data for testing."""
    return {
        "session_id": "test_session_123",
        "started_at": "2024-01-01T10:00:00Z",
        "cwd": "/test/project",
        "profile": "development",
        "messages": [
            {"role": "user", "content": "Test message 1"},
            {"role": "assistant", "content": "Test response 1"},
            {"role": "user", "content": "Test message 2"},
            {"role": "assistant", "content": "Test response 2"}
        ],
        "memories_loaded": 3,
        "quality_checks_passed": True
    }


# 6. Environment Fixtures

@pytest.fixture
def clean_env(monkeypatch):
    """Clear all AMPLIFIER_* environment variables for isolated tests."""
    # Store original environment
    original_env = os.environ.copy()
    
    # Clear AMPLIFIER_* variables
    keys_to_remove = [k for k in os.environ.keys() if k.startswith('AMPLIFIER_')]
    for key in keys_to_remove:
        monkeypatch.delenv(key, raising=False)
    
    # Also clear related variables
    related_vars = ['MEMORY_SYSTEM_ENABLED', 'CODEX_PROFILE']
    for var in related_vars:
        monkeypatch.delenv(var, raising=False)
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def claude_env(monkeypatch):
    """Set environment for Claude Code backend."""
    monkeypatch.setenv('AMPLIFIER_BACKEND', 'claude')
    monkeypatch.setenv('MEMORY_SYSTEM_ENABLED', 'true')


@pytest.fixture
def codex_env(monkeypatch):
    """Set environment for Codex backend."""
    monkeypatch.setenv('AMPLIFIER_BACKEND', 'codex')
    monkeypatch.setenv('CODEX_PROFILE', 'development')
    monkeypatch.setenv('MEMORY_SYSTEM_ENABLED', 'true')


@pytest.fixture
def memory_enabled_env(monkeypatch):
    """Set MEMORY_SYSTEM_ENABLED=true."""
    monkeypatch.setenv('MEMORY_SYSTEM_ENABLED', 'true')


@pytest.fixture
def memory_disabled_env(monkeypatch):
    """Set MEMORY_SYSTEM_ENABLED=false."""
    monkeypatch.setenv('MEMORY_SYSTEM_ENABLED', 'false')


# 7. Subprocess Mocking Fixtures

@pytest.fixture
def mock_make_check_success():
    """Mock successful `make check` execution."""
    result = Mock()
    result.returncode = 0
    result.stdout = "make check passed successfully"
    result.stderr = ""
    
    with patch('subprocess.run', return_value=result) as mock_run:
        yield mock_run


@pytest.fixture
def mock_make_check_failure():
    """Mock failed `make check` execution."""
    result = Mock()
    result.returncode = 1
    result.stdout = ""
    result.stderr = "Syntax error in test.py"
    
    with patch('subprocess.run', return_value=result) as mock_run:
        yield mock_run


@pytest.fixture
def mock_codex_exec_success():
    """Mock successful `codex exec` for agent spawning."""
    result = Mock()
    result.returncode = 0
    result.stdout = "Agent executed successfully"
    result.stderr = ""
    
    with patch('subprocess.run', return_value=result) as mock_run:
        yield mock_run


@pytest.fixture
def mock_codex_exec_failure():
    """Mock failed `codex exec`."""
    result = Mock()
    result.returncode = 1
    result.stdout = ""
    result.stderr = "Agent execution failed"
    
    with patch('subprocess.run', return_value=result) as mock_run:
        yield mock_run


# 8. File System Fixtures

@pytest.fixture
def capture_file_writes(monkeypatch):
    """Capture file writes for verification (session_context.md, metadata.json, etc.)."""
    written_files = {}
    
    original_open = open
    
    def mock_open(filename, mode='r', *args, **kwargs):
        if 'w' in mode or 'a' in mode:
            # Intercept writes
            import io
            string_io = io.StringIO()
            file_obj = string_io
            
            # Store reference to capture content
            written_files[str(filename)] = string_io
            
            # Return a mock file object that captures writes
            mock_file = Mock()
            mock_file.write = string_io.write
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=None)
            return mock_file
        else:
            # For reads, use real file operations
            return original_open(filename, mode, *args, **kwargs)
    
    monkeypatch.setattr('builtins.open', mock_open)
    
    yield written_files


@pytest.fixture
def mock_transcript_files(temp_dir):
    """Create mock transcript files for both backends."""
    # Create Claude transcript
    claude_transcript = temp_dir / ".data" / "transcripts" / "compact_20240101_100000_test.txt"
    claude_transcript.parent.mkdir(parents=True)
    claude_transcript.write_text("# Claude Code Transcript\nContent here")
    
    # Create Codex transcript directory
    codex_session = temp_dir / ".codex" / "transcripts" / "2024-01-01-10-00-PM__project__session123"
    codex_session.mkdir(parents=True)
    (codex_session / "transcript.md").write_text("# Codex Transcript\nContent here")
    (codex_session / "transcript_extended.md").write_text("# Extended Transcript\nDetailed content")
    
    return {
        'claude': claude_transcript,
        'codex': codex_session
    }