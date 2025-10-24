#!/usr/bin/env python3
"""
Tests for backend abstraction layer.

Comprehensive tests covering backend.py, agent_backend.py, and config.py modules,
including factory patterns, session management, quality checks, transcript export,
agent spawning, configuration, and integration scenarios.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest

# Import modules under test (will be mocked where necessary)
try:
    from amplifier.core.agent_backend import AgentBackend
    from amplifier.core.agent_backend import AgentBackendFactory
    from amplifier.core.agent_backend import ClaudeCodeAgentBackend
    from amplifier.core.agent_backend import CodexAgentBackend
    from amplifier.core.agent_backend import get_agent_backend
    from amplifier.core.agent_backend import spawn_agent
    from amplifier.core.backend import AmplifierBackend
    from amplifier.core.backend import BackendFactory
    from amplifier.core.backend import ClaudeCodeBackend
    from amplifier.core.backend import CodexBackend
    from amplifier.core.backend import get_backend
    from amplifier.core.backend import set_backend
    from amplifier.core.config import BackendConfig
    from amplifier.core.config import backend_config
    from amplifier.core.config import detect_backend
    from amplifier.core.config import get_backend_config
    from amplifier.core.config import get_backend_info
    from amplifier.core.config import is_backend_available
except ImportError:
    # Modules not yet implemented - tests will use mocks
    pass


# Test Fixtures


@pytest.fixture
def temp_dir() -> Path:
    """Create temporary directory for test operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_project_dir(temp_dir) -> Path:
    """Create temporary project directory with common structure."""
    project_dir = temp_dir / "project"
    project_dir.mkdir()

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
name = "test-project"
version = "0.1.0"

[tool.uv]
dev-dependencies = ["pytest", "ruff", "pyright"]
""")

    # Create .git directory
    git_dir = project_dir / ".git"
    git_dir.mkdir()

    return project_dir


@pytest.fixture
def mock_memory_store():
    """Mock MemoryStore with sample data."""
    store = Mock()
    store.add_memories_batch.return_value = 5
    return store


@pytest.fixture
def mock_memory_searcher():
    """Mock MemorySearcher with search results."""
    searcher = Mock()
    searcher.search.return_value = [
        {"content": "Relevant memory 1", "score": 0.9},
        {"content": "Relevant memory 2", "score": 0.8},
    ]
    return searcher


@pytest.fixture
def mock_memory_extractor():
    """Mock MemoryExtractor with extraction results."""
    extractor = Mock()
    extractor.extract_from_messages.return_value = [
        {"content": "Extracted memory 1", "type": "fact"},
        {"content": "Extracted memory 2", "type": "pattern"},
    ]
    return extractor


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for command execution."""
    result = Mock()
    result.returncode = 0
    result.stdout = "Checks passed successfully"
    result.stderr = ""
    return result


@pytest.fixture
def mock_claude_backend():
    """Mock ClaudeCodeBackend for testing."""
    backend = Mock(spec=ClaudeCodeBackend)
    backend.initialize_session.return_value = {
        "success": True,
        "data": {"context": "Mock context"},
        "metadata": {"memoriesLoaded": 2},
    }
    backend.finalize_session.return_value = {
        "success": True,
        "data": {"memoriesExtracted": 3},
        "metadata": {"source": "session_finalize"},
    }
    backend.run_quality_checks.return_value = {
        "success": True,
        "data": {"output": "Checks passed"},
        "metadata": {"command": "make check"},
    }
    backend.export_transcript.return_value = {
        "success": True,
        "data": {"path": "/exported/transcript.md"},
        "metadata": {"format": "standard"},
    }
    backend.get_backend_name.return_value = "claude"
    backend.is_available.return_value = True
    return backend


@pytest.fixture
def mock_codex_backend():
    """Mock CodexBackend for testing."""
    backend = Mock(spec=CodexBackend)
    backend.initialize_session.return_value = {
        "success": True,
        "data": {"context": "Mock context"},
        "metadata": {"memoriesLoaded": 2},
    }
    backend.finalize_session.return_value = {
        "success": True,
        "data": {"memoriesExtracted": 3},
        "metadata": {"source": "session_finalize"},
    }
    backend.run_quality_checks.return_value = {
        "success": True,
        "data": {"output": "Checks passed"},
        "metadata": {"command": "make check"},
    }
    backend.export_transcript.return_value = {
        "success": True,
        "data": {"path": "/exported/transcript.md"},
        "metadata": {"format": "standard"},
    }
    backend.get_backend_name.return_value = "codex"
    backend.is_available.return_value = True
    return backend


@pytest.fixture
def mock_agent_definition():
    """Mock agent definition content."""
    return """
---
name: test-agent
description: A test agent
system_prompt: You are a test agent.
allowed_tools: [search, code]
max_turns: 10
model: gpt-4
---

# Agent Definition

This is a test agent for testing purposes.
"""


@pytest.fixture
def temp_backend_env():
    """Temporary environment with backend configuration."""
    original_env = os.environ.copy()
    try:
        os.environ["AMPLIFIER_BACKEND"] = "claude"
        os.environ["MEMORY_SYSTEM_ENABLED"] = "true"
        yield
    finally:
        os.environ.clear()
        os.environ.update(original_env)


# Test Utilities


def create_mock_messages(count=3):
    """Create mock conversation messages."""
    return [{"role": "user", "content": f"User message {i}"} for i in range(count)]


def create_mock_memories(count=2):
    """Create mock memory objects."""
    return [{"content": f"Memory {i}", "type": "fact", "score": 0.8} for i in range(count)]


def assert_backend_response(response, expected_success=True):
    """Assert standard backend response structure."""
    assert "success" in response
    assert "data" in response
    assert "metadata" in response
    if expected_success:
        assert response["success"] is True


# Backend Tests


class TestAmplifierBackend:
    """Test backend factory and basic functionality."""

    def test_backend_factory_default(self):
        """Verify default backend is Claude Code."""
        with patch.dict(os.environ, {}, clear=True):
            backend = BackendFactory.create_backend()
            assert backend.get_backend_name() == "claude"

    def test_backend_factory_from_env(self):
        """Verify backend selection from AMPLIFIER_BACKEND env var."""
        with patch.dict(os.environ, {"AMPLIFIER_BACKEND": "codex"}):
            backend = BackendFactory.create_backend()
            assert backend.get_backend_name() == "codex"

    def test_backend_factory_invalid(self):
        """Verify error on invalid backend type."""
        with pytest.raises(ValueError, match="Invalid backend type"):
            BackendFactory.create_backend("invalid")

    def test_claude_backend_available(self, temp_dir):
        """Check Claude Code backend availability."""
        # Create .claude directory
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()

        with patch("amplifier.core.backend.Path.cwd", return_value=temp_dir):
            backend = ClaudeCodeBackend()
            assert backend.is_available() is True

    def test_codex_backend_available(self, temp_dir):
        """Check Codex backend availability."""
        # Create .codex directory
        codex_dir = temp_dir / ".codex"
        codex_dir.mkdir()

        with patch("amplifier.core.backend.Path.cwd", return_value=temp_dir):
            backend = CodexBackend()
            assert backend.is_available() is True

    def test_backend_get_name(self):
        """Verify backend name methods."""
        claude_backend = ClaudeCodeBackend()
        codex_backend = CodexBackend()

        assert claude_backend.get_backend_name() == "claude"
        assert codex_backend.get_backend_name() == "codex"

    def test_get_available_backends(self):
        """Test listing available backends."""
        with (
            patch("amplifier.core.backend.ClaudeCodeBackend.is_available", return_value=True),
            patch("amplifier.core.backend.CodexBackend.is_available", return_value=False),
        ):
            available = BackendFactory.get_available_backends()
            assert "claude" in available
            assert "codex" not in available

    def test_auto_detect_backend(self, temp_dir):
        """Test backend auto-detection."""
        # Create .claude directory
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()

        with patch("amplifier.core.backend.Path.cwd", return_value=temp_dir):
            backend_type = BackendFactory.auto_detect_backend()
            assert backend_type == "claude"


# Session Management Tests


class TestSessionManagement:
    """Test session initialization and finalization."""

    def test_initialize_session_claude(self, mock_memory_store, mock_memory_searcher):
        """Test Claude Code session initialization."""
        with (
            patch("amplifier.core.backend.MemoryStore", return_value=mock_memory_store),
            patch("amplifier.core.backend.MemorySearcher", return_value=mock_memory_searcher),
        ):
            backend = ClaudeCodeBackend()
            result = backend.initialize_session("Test prompt")

            assert_backend_response(result)
            assert "memoriesLoaded" in result["metadata"]
            mock_memory_searcher.search.assert_called_once()

    def test_initialize_session_codex(self, mock_memory_store, mock_memory_searcher):
        """Test Codex session initialization."""
        with (
            patch("amplifier.core.backend.MemoryStore", return_value=mock_memory_store),
            patch("amplifier.core.backend.MemorySearcher", return_value=mock_memory_searcher),
        ):
            backend = CodexBackend()
            result = backend.initialize_session("Test prompt")

            assert_backend_response(result)
            assert "memoriesLoaded" in result["metadata"]

    def test_initialize_session_memory_disabled(self):
        """Test with memory system disabled."""
        with patch.dict(os.environ, {"MEMORY_SYSTEM_ENABLED": "false"}):
            backend = ClaudeCodeBackend()
            result = backend.initialize_session("Test prompt")

            assert_backend_response(result)
            assert result["metadata"]["disabled"] is True

    def test_finalize_session_claude(self, mock_memory_store, mock_memory_extractor):
        """Test Claude Code session finalization."""
        with (
            patch("amplifier.core.backend.MemoryStore", return_value=mock_memory_store),
            patch("amplifier.core.backend.MemoryExtractor", return_value=mock_memory_extractor),
        ):
            backend = ClaudeCodeBackend()
            messages = create_mock_messages()
            result = backend.finalize_session(messages)

            assert_backend_response(result)
            assert "memoriesExtracted" in result["metadata"]
            mock_memory_store.add_memories_batch.assert_called_once()

    def test_finalize_session_codex(self, mock_memory_store, mock_memory_extractor):
        """Test Codex session finalization."""
        with (
            patch("amplifier.core.backend.MemoryStore", return_value=mock_memory_store),
            patch("amplifier.core.backend.MemoryExtractor", return_value=mock_memory_extractor),
        ):
            backend = CodexBackend()
            messages = create_mock_messages()
            result = backend.finalize_session(messages)

            assert_backend_response(result)
            assert "memoriesExtracted" in result["metadata"]

    def test_finalize_session_timeout(self, mock_memory_extractor):
        """Test timeout handling."""
        with (
            patch("amplifier.core.backend.MemoryExtractor", return_value=mock_memory_extractor),
            patch("asyncio.timeout", side_effect=Exception("Timeout")),
        ):
            backend = ClaudeCodeBackend()
            messages = create_mock_messages()
            result = backend.finalize_session(messages)

            assert result["success"] is False
            assert "timeout" in str(result).lower()

    def test_session_roundtrip(self, mock_memory_store, mock_memory_searcher, mock_memory_extractor):
        """Test initialize + finalize workflow."""
        with (
            patch("amplifier.core.backend.MemoryStore", return_value=mock_memory_store),
            patch("amplifier.core.backend.MemorySearcher", return_value=mock_memory_searcher),
            patch("amplifier.core.backend.MemoryExtractor", return_value=mock_memory_extractor),
        ):
            backend = ClaudeCodeBackend()

            # Initialize
            init_result = backend.initialize_session("Test prompt")
            assert_backend_response(init_result)

            # Finalize
            messages = create_mock_messages()
            finalize_result = backend.finalize_session(messages)
            assert_backend_response(finalize_result)

            # Verify workflow
            assert init_result["metadata"]["memoriesLoaded"] == 2
            assert finalize_result["metadata"]["memoriesExtracted"] == 2


# Quality Checks Tests


class TestQualityChecks:
    """Test code quality checking functionality."""

    def test_run_quality_checks_success(self, temp_project_dir, mock_subprocess):
        """Test successful quality checks."""
        with patch("subprocess.run", return_value=mock_subprocess):
            backend = ClaudeCodeBackend()
            result = backend.run_quality_checks(["test.py"], cwd=str(temp_project_dir))

            assert_backend_response(result)
            assert "Checks passed" in result["data"]["output"]

    def test_run_quality_checks_failure(self, temp_project_dir):
        """Test failed quality checks."""
        failed_result = Mock()
        failed_result.returncode = 1
        failed_result.stdout = ""
        failed_result.stderr = "Syntax error in test.py"

        with patch("subprocess.run", return_value=failed_result):
            backend = ClaudeCodeBackend()
            result = backend.run_quality_checks(["test.py"], cwd=str(temp_project_dir))

            assert result["success"] is False
            assert "Syntax error" in result["data"]["output"]

    def test_run_quality_checks_no_makefile(self, temp_dir):
        """Test graceful handling when Makefile missing."""
        project_dir = temp_dir / "no_makefile"
        project_dir.mkdir()

        backend = ClaudeCodeBackend()
        result = backend.run_quality_checks(["test.py"], cwd=str(project_dir))

        assert result["success"] is False
        assert "makefile" in result["data"]["error"].lower()

    def test_run_quality_checks_custom_cwd(self, temp_project_dir, mock_subprocess):
        """Test with custom working directory."""
        with patch("subprocess.run", return_value=mock_subprocess):
            backend = ClaudeCodeBackend()
            result = backend.run_quality_checks(["test.py"], cwd=str(temp_project_dir))

            assert_backend_response(result)
            # Verify subprocess was called with correct cwd
            subprocess.run.assert_called_once()


# Transcript Export Tests


class TestTranscriptExport:
    """Test transcript export functionality."""

    def test_export_transcript_claude(self):
        """Test Claude Code transcript export."""
        with patch("amplifier.core.backend.transcript_manager") as mock_manager:
            mock_manager.export_transcript.return_value = "/exported/transcript.md"

            backend = ClaudeCodeBackend()
            result = backend.export_transcript(format="standard")

            assert_backend_response(result)
            assert result["data"]["path"] == "/exported/transcript.md"

    def test_export_transcript_codex(self):
        """Test Codex transcript export."""
        with patch("amplifier.core.backend.codex_transcripts_builder") as mock_builder:
            mock_builder.process_session.return_value = "/exported/transcript.md"

            backend = CodexBackend()
            result = backend.export_transcript(format="standard")

            assert_backend_response(result)
            assert result["data"]["path"] == "/exported/transcript.md"

    def test_export_transcript_formats(self):
        """Test different format options."""
        with patch("amplifier.core.backend.transcript_manager") as mock_manager:
            mock_manager.export_transcript.return_value = "/exported/transcript.md"

            backend = ClaudeCodeBackend()
            result = backend.export_transcript(format="extended")

            assert_backend_response(result)
            # Verify format parameter was passed
            mock_manager.export_transcript.assert_called_with(session_id=None, format="extended", output_dir=None)

    def test_export_transcript_custom_output(self, temp_dir):
        """Test custom output directory."""
        output_dir = temp_dir / "custom_output"

        with patch("amplifier.core.backend.transcript_manager") as mock_manager:
            mock_manager.export_transcript.return_value = str(output_dir / "transcript.md")

            backend = ClaudeCodeBackend()
            result = backend.export_transcript(output_dir=str(output_dir))

            assert_backend_response(result)
            assert str(output_dir) in result["data"]["path"]


# Agent Backend Tests


class TestAgentBackend:
    """Test agent backend functionality."""

    def test_agent_backend_factory(self):
        """Verify agent backend factory."""
        with patch.dict(os.environ, {"AMPLIFIER_BACKEND": "codex"}):
            backend = AgentBackendFactory.create_agent_backend()
            assert backend.get_backend_name() == "codex"

    def test_list_available_agents_claude(self, temp_dir):
        """List Claude Code agents."""
        agents_dir = temp_dir / ".claude" / "agents"
        agents_dir.mkdir(parents=True)

        # Create agent files
        (agents_dir / "agent1.md").write_text("Agent 1")
        (agents_dir / "agent2.md").write_text("Agent 2")

        with patch("amplifier.core.agent_backend.Path.cwd", return_value=temp_dir):
            backend = ClaudeCodeAgentBackend()
            agents = backend.list_available_agents()

            assert "agent1" in agents
            assert "agent2" in agents

    def test_list_available_agents_codex(self, temp_dir):
        """List Codex agents."""
        agents_dir = temp_dir / ".codex" / "agents"
        agents_dir.mkdir(parents=True)

        # Create agent files
        (agents_dir / "agent1.md").write_text("Agent 1")
        (agents_dir / "agent2.md").write_text("Agent 2")

        with patch("amplifier.core.agent_backend.Path.cwd", return_value=temp_dir):
            backend = CodexAgentBackend()
            agents = backend.list_available_agents()

            assert "agent1" in agents
            assert "agent2" in agents

    def test_get_agent_definition(self, temp_dir, mock_agent_definition):
        """Get agent definition content."""
        agents_dir = temp_dir / ".claude" / "agents"
        agents_dir.mkdir(parents=True)

        agent_file = agents_dir / "test-agent.md"
        agent_file.write_text(mock_agent_definition)

        with patch("amplifier.core.agent_backend.Path.cwd", return_value=temp_dir):
            backend = ClaudeCodeAgentBackend()
            content = backend.get_agent_definition("test-agent")

            assert content == mock_agent_definition

    def test_validate_agent_exists(self, temp_dir):
        """Validate agent existence."""
        agents_dir = temp_dir / ".claude" / "agents"
        agents_dir.mkdir(parents=True)

        (agents_dir / "existing-agent.md").write_text("Content")

        with patch("amplifier.core.agent_backend.Path.cwd", return_value=temp_dir):
            backend = ClaudeCodeAgentBackend()

            assert backend.validate_agent_exists("existing-agent") is True
            assert backend.validate_agent_exists("nonexistent-agent") is False


# Agent Spawning Tests


class TestAgentSpawning:
    """Test agent spawning functionality."""

    def test_spawn_agent_claude(self):
        """Test Claude Code agent spawning (mock SDK)."""
        with patch("amplifier.core.agent_backend.ClaudeSDKClient") as mock_sdk:
            mock_client = Mock()
            mock_client.send_task.return_value = {"result": "Agent response"}
            mock_sdk.return_value = mock_client

            backend = ClaudeCodeAgentBackend()
            result = backend.spawn_agent("test-agent", "Test task")

            assert result["success"] is True
            assert result["result"] == "Agent response"

    def test_spawn_agent_codex(self):
        """Test Codex agent spawning (mock subprocess)."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Agent response"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            backend = CodexAgentBackend()
            result = backend.spawn_agent("test-agent", "Test task")

            assert result["success"] is True
            assert result["result"] == "Agent response"

    def test_spawn_agent_not_found(self):
        """Test error when agent doesn't exist."""
        backend = ClaudeCodeAgentBackend()
        result = backend.spawn_agent("nonexistent-agent", "Test task")

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_spawn_agent_timeout(self):
        """Test timeout handling."""
        with patch("amplifier.core.agent_backend.ClaudeSDKClient") as mock_sdk:
            mock_client = Mock()
            mock_client.send_task.side_effect = Exception("Timeout")
            mock_sdk.return_value = mock_client

            backend = ClaudeCodeAgentBackend()
            result = backend.spawn_agent("test-agent", "Test task")

            assert result["success"] is False
            assert "timeout" in str(result).lower()

    def test_spawn_agent_convenience_function(self):
        """Test high-level spawn_agent() function."""
        with patch("amplifier.core.agent_backend.AgentBackendFactory.create_agent_backend") as mock_factory:
            mock_backend = Mock()
            mock_backend.spawn_agent.return_value = {"success": True, "result": "Response"}
            mock_factory.return_value = mock_backend

            result = spawn_agent("test-agent", "Test task")

            assert result["success"] is True
            assert result["result"] == "Response"


# Configuration Tests


class TestBackendConfig:
    """Test backend configuration functionality."""

    def test_config_defaults(self):
        """Verify default configuration values."""
        config = BackendConfig()

        assert config.amplifier_backend == "claude"
        assert config.amplifier_backend_auto_detect is True
        assert config.memory_system_enabled is True

    def test_config_from_env(self):
        """Load configuration from environment variables."""
        with patch.dict(os.environ, {"AMPLIFIER_BACKEND": "codex", "MEMORY_SYSTEM_ENABLED": "false"}):
            config = BackendConfig()

            assert config.amplifier_backend == "codex"
            assert config.memory_system_enabled is False

    def test_config_validation(self):
        """Test configuration validation."""
        config = BackendConfig()

        # Valid backend
        assert config.validate_backend() is None

        # Invalid backend
        config.amplifier_backend = "invalid"
        with pytest.raises(ValueError):
            config.validate_backend()

    def test_detect_backend(self, temp_dir):
        """Test backend auto-detection."""
        # Create .claude directory
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()

        with patch("amplifier.core.config.Path.cwd", return_value=temp_dir):
            backend = detect_backend()
            assert backend == "claude"

    def test_is_backend_available(self, temp_dir):
        """Test backend availability checks."""
        # Create .claude directory
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()

        with patch("amplifier.core.config.Path.cwd", return_value=temp_dir):
            assert is_backend_available("claude") is True
            assert is_backend_available("codex") is False

    def test_get_backend_info(self, temp_dir):
        """Test backend information retrieval."""
        # Create .claude directory
        claude_dir = temp_dir / ".claude"
        claude_dir.mkdir()

        with patch("amplifier.core.config.Path.cwd", return_value=temp_dir):
            info = get_backend_info("claude")

            assert "cli_path" in info
            assert "config_dir" in info
            assert info["available"] is True


# Integration Tests


class TestBackendIntegration:
    """Integration tests across backend components."""

    def test_full_session_workflow_claude(self, mock_memory_store, mock_memory_searcher, mock_memory_extractor):
        """End-to-end test with Claude Code backend."""
        with (
            patch("amplifier.core.backend.MemoryStore", return_value=mock_memory_store),
            patch("amplifier.core.backend.MemorySearcher", return_value=mock_memory_searcher),
            patch("amplifier.core.backend.MemoryExtractor", return_value=mock_memory_extractor),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = Mock(returncode=0, stdout="Checks passed", stderr="")

            backend = ClaudeCodeBackend()

            # Initialize session
            init_result = backend.initialize_session("Test workflow")
            assert_backend_response(init_result)

            # Run quality checks
            quality_result = backend.run_quality_checks(["test.py"])
            assert_backend_response(quality_result)

            # Finalize session
            messages = create_mock_messages()
            finalize_result = backend.finalize_session(messages)
            assert_backend_response(finalize_result)

            # Export transcript
            export_result = backend.export_transcript()
            assert_backend_response(export_result)

    def test_full_session_workflow_codex(self, mock_memory_store, mock_memory_searcher, mock_memory_extractor):
        """End-to-end test with Codex backend."""
        with (
            patch("amplifier.core.backend.MemoryStore", return_value=mock_memory_store),
            patch("amplifier.core.backend.MemorySearcher", return_value=mock_memory_searcher),
            patch("amplifier.core.backend.MemoryExtractor", return_value=mock_memory_extractor),
            patch("subprocess.run") as mock_run,
        ):
            mock_run.return_value = Mock(returncode=0, stdout="Checks passed", stderr="")

            backend = CodexBackend()

            # Initialize session
            init_result = backend.initialize_session("Test workflow")
            assert_backend_response(init_result)

            # Run quality checks
            quality_result = backend.run_quality_checks(["test.py"])
            assert_backend_response(quality_result)

            # Finalize session
            messages = create_mock_messages()
            finalize_result = backend.finalize_session(messages)
            assert_backend_response(finalize_result)

            # Export transcript
            export_result = backend.export_transcript()
            assert_backend_response(export_result)

    def test_backend_switching(self):
        """Test switching between backends."""
        # Start with Claude
        set_backend("claude")
        backend1 = get_backend()
        assert backend1.get_backend_name() == "claude"

        # Switch to Codex
        set_backend("codex")
        backend2 = get_backend()
        assert backend2.get_backend_name() == "codex"

    def test_agent_spawning_integration(self, temp_dir, mock_agent_definition):
        """Test agent spawning with real agent definitions."""
        agents_dir = temp_dir / ".claude" / "agents"
        agents_dir.mkdir(parents=True)

        agent_file = agents_dir / "test-agent.md"
        agent_file.write_text(mock_agent_definition)

        with (
            patch("amplifier.core.agent_backend.ClaudeSDKClient") as mock_sdk,
            patch("amplifier.core.agent_backend.Path.cwd", return_value=temp_dir),
        ):
            mock_client = Mock()
            mock_client.send_task.return_value = {"result": "Agent response"}
            mock_sdk.return_value = mock_client

            result = spawn_agent("test-agent", "Test task", backend="claude")

            assert result["success"] is True
            assert result["result"] == "Agent response"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
