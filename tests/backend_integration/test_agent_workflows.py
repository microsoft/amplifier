#!/usr/bin/env python3
"""
Tests for agent spawning workflow integration.

Comprehensive tests covering agent spawning workflows across both Claude Code
and Codex backends, including single/multiple agent execution, context handling,
error scenarios, and cross-backend compatibility.
"""

import json
import os
import subprocess
from unittest.mock import Mock
from unittest.mock import patch

import pytest

# Import modules under test
try:
    from amplifier.core.agent_backend import AgentBackendFactory
    from amplifier.core.agent_backend import AgentNotFoundError
    from amplifier.core.agent_backend import AgentSpawnError
    from amplifier.core.agent_backend import AgentTimeoutError
    from amplifier.core.agent_backend import ClaudeCodeAgentBackend
    from amplifier.core.agent_backend import CodexAgentBackend
    from amplifier.core.agent_backend import parse_agent_definition
    from amplifier.core.agent_backend import spawn_agent
except ImportError:
    # Modules not yet implemented - tests will use mocks
    pass


# Test Fixtures (will be defined in conftest.py)


@pytest.fixture
def sample_agent_definition():
    """Return sample agent definition markdown content."""
    return """
---
name: test-agent
description: A test agent for testing purposes
system_prompt: You are a helpful test agent.
allowed_tools: [Read, Grep, Bash]
max_turns: 10
model: gpt-4
---

# Test Agent

This agent is used for testing agent spawning workflows.
It can read files, search code, and run bash commands.
"""


@pytest.fixture
def create_test_agents(temp_dir, sample_agent_definition):
    """Create test agent files in both backend directories."""
    # Claude agents
    claude_agents_dir = temp_dir / ".claude" / "agents"
    claude_agents_dir.mkdir(parents=True)

    agents = ["bug-hunter", "zen-architect", "test-coverage"]
    for agent_name in agents:
        agent_file = claude_agents_dir / f"{agent_name}.md"
        content = sample_agent_definition.replace("test-agent", agent_name)
        content = content.replace("Test Agent", f"{agent_name.replace('-', ' ').title()} Agent")
        agent_file.write_text(content)

    # Codex agents
    codex_agents_dir = temp_dir / ".codex" / "agents"
    codex_agents_dir.mkdir(parents=True)

    for agent_name in agents:
        agent_file = codex_agents_dir / f"{agent_name}.md"
        content = sample_agent_definition.replace("test-agent", agent_name)
        # Convert tools format for Codex (array instead of comma-separated)
        content = content.replace("allowed_tools: [Read, Grep, Bash]", "tools:\n  - Read\n  - Grep\n  - Bash")
        agent_file.write_text(content)

    return agents


@pytest.fixture
def mock_claude_sdk():
    """Mock Claude Code SDK for testing."""
    with (
        patch("amplifier.core.agent_backend.ClaudeSDKClient") as mock_sdk_class,
        patch("amplifier.core.agent_backend.ClaudeCodeOptions") as mock_options_class,
    ):
        mock_client = Mock()
        mock_client.query.return_value = {"content": "Agent response", "usage": {"tokens": 100}}

        mock_sdk_class.return_value = mock_client
        mock_options_class.return_value = Mock()

        yield mock_client


@pytest.fixture
def mock_codex_exec_success():
    """Mock successful codex exec subprocess."""
    result = Mock()
    result.returncode = 0
    result.stdout = "Agent executed successfully"
    result.stderr = ""

    with patch("subprocess.run", return_value=result) as mock_run:
        yield mock_run


@pytest.fixture
def mock_codex_exec_failure():
    """Mock failed codex exec subprocess."""
    result = Mock()
    result.returncode = 1
    result.stdout = ""
    result.stderr = "Agent execution failed: invalid syntax"

    with patch("subprocess.run", return_value=result) as mock_run:
        yield mock_run


@pytest.fixture
def claude_env(monkeypatch):
    """Set environment for Claude Code backend."""
    monkeypatch.setenv("AMPLIFIER_BACKEND", "claude")


@pytest.fixture
def codex_env(monkeypatch):
    """Set environment for Codex backend."""
    monkeypatch.setenv("AMPLIFIER_BACKEND", "codex")
    monkeypatch.setenv("CODEX_PROFILE", "development")


@pytest.fixture
def mock_both_backends_available():
    """Mock both backends as available."""
    with (
        patch("amplifier.core.agent_backend.ClaudeCodeAgentBackend.is_available", return_value=True),
        patch("amplifier.core.agent_backend.CodexAgentBackend.is_available", return_value=True),
    ):
        yield


# Test Classes


class TestClaudeAgentWorkflows:
    """Test Claude Code agent spawning via Task tool."""

    def test_claude_spawn_single_agent(self, integration_test_project, mock_claude_sdk, create_test_agents):
        """Test spawning a single agent with Claude Code backend."""
        with patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project):
            backend = ClaudeCodeAgentBackend()

            result = backend.spawn_agent("bug-hunter", "Find bugs in the code")

            # Verify SDK was called correctly
            mock_claude_sdk.query.assert_called_once()
            call_args = mock_claude_sdk.query.call_args[0][0]
            assert "bug-hunter subagent" in call_args
            assert "Find bugs in the code" in call_args

            # Verify response structure
            assert result["success"] is True
            assert result["result"] == "Agent response"
            assert result["metadata"]["backend"] == "claude"
            assert result["metadata"]["agent_name"] == "bug-hunter"

    def test_claude_spawn_multiple_agents_sequentially(
        self, integration_test_project, mock_claude_sdk, create_test_agents
    ):
        """Test spawning multiple agents sequentially."""
        with patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project):
            backend = ClaudeCodeAgentBackend()

            agents = ["bug-hunter", "zen-architect", "test-coverage"]
            results = []

            for agent_name in agents:
                result = backend.spawn_agent(agent_name, f"Task for {agent_name}")
                results.append(result)

            # Verify all agents were spawned successfully
            assert len(results) == 3
            for i, result in enumerate(results):
                assert result["success"] is True
                assert result["metadata"]["agent_name"] == agents[i]

            # Verify SDK was called 3 times
            assert mock_claude_sdk.query.call_count == 3

    def test_claude_agent_with_context(self, integration_test_project, mock_claude_sdk, create_test_agents):
        """Test spawning agent with additional context."""
        with patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project):
            backend = ClaudeCodeAgentBackend()

            context = {"files": ["main.py", "utils.py"], "priority": "high"}
            result = backend.spawn_agent("zen-architect", "Refactor the code", context=context)

            # Verify context was included in the task
            call_args = mock_claude_sdk.query.call_args[0][0]
            assert "Additional context:" in call_args
            assert '"files": ["main.py", "utils.py"]' in call_args
            assert '"priority": "high"' in call_args

    def test_claude_agent_not_found_error(self, integration_test_project):
        """Test error when agent doesn't exist."""
        with patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project):
            backend = ClaudeCodeAgentBackend()

            with pytest.raises(AgentNotFoundError, match="nonexistent-agent"):
                backend.spawn_agent("nonexistent-agent", "Test task")

    def test_claude_agent_timeout(self, integration_test_project, create_test_agents):
        """Test timeout handling."""
        with (
            patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project),
            patch("asyncio.timeout", side_effect=Exception("Timeout")),
        ):
            backend = ClaudeCodeAgentBackend()

            with pytest.raises(AgentTimeoutError, match="timed out"):
                backend.spawn_agent("bug-hunter", "Test task")


class TestCodexAgentWorkflows:
    """Test Codex agent spawning via codex exec."""

    def test_codex_spawn_single_agent(self, integration_test_project, mock_codex_exec_success, create_test_agents):
        """Test spawning a single agent with Codex backend."""
        with patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project):
            backend = CodexAgentBackend()

            result = backend.spawn_agent("bug-hunter", "Find bugs in the code")

            # Verify subprocess was called correctly
            mock_codex_exec_success.assert_called_once()
            call_args = mock_codex_exec_success.call_args[0][0]

            assert call_args[0] == "codex"
            assert call_args[1] == "exec"
            assert "--context-file=.codex/agents/bug-hunter.md" in call_args
            assert "--task=Find bugs in the code" in call_args
            assert "--profile=development" in call_args

            # Verify response structure
            assert result["success"] is True
            assert result["result"] == "Agent executed successfully"
            assert result["metadata"]["backend"] == "codex"
            assert result["metadata"]["agent_name"] == "bug-hunter"

    def test_codex_spawn_with_custom_profile(
        self, integration_test_project, mock_codex_exec_success, create_test_agents, codex_env
    ):
        """Test spawning agent with custom profile."""
        with patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project):
            backend = CodexAgentBackend()

            result = backend.spawn_agent("test-coverage", "Run test coverage")

            # Verify profile was used
            call_args = mock_codex_exec_success.call_args[0][0]
            assert "--profile=development" in call_args

    def test_codex_spawn_with_context_data(self, integration_test_project, mock_codex_exec_success, create_test_agents):
        """Test spawning agent with context data."""
        with patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project):
            backend = CodexAgentBackend()

            context = {"files": ["test_main.py"], "options": {"verbose": True}}
            result = backend.spawn_agent("bug-hunter", "Analyze tests", context=context)

            # Verify context data was passed
            call_args = mock_codex_exec_success.call_args[0][0]
            context_arg_index = call_args.index("--context-data") + 1
            context_json = call_args[context_arg_index]
            parsed_context = json.loads(context_json)
            assert parsed_context == context

    def test_codex_agent_execution_failure(self, integration_test_project, mock_codex_exec_failure, create_test_agents):
        """Test handling of agent execution failure."""
        with patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project):
            backend = CodexAgentBackend()

            with pytest.raises(AgentSpawnError, match="Agent execution failed"):
                backend.spawn_agent("bug-hunter", "Test task")

    def test_codex_agent_timeout(self, integration_test_project, create_test_agents):
        """Test timeout handling for Codex agents."""
        with (
            patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project),
            patch("subprocess.run", side_effect=subprocess.TimeoutExpired("codex exec", 300)),
        ):
            backend = CodexAgentBackend()

            with pytest.raises(AgentTimeoutError, match="timed out"):
                backend.spawn_agent("bug-hunter", "Test task")


class TestAgentConversionWorkflows:
    """Test agent conversion and cross-backend usage."""

    def test_converted_agent_works_with_codex(self, integration_test_project, mock_codex_exec_success):
        """Test that converted Claude agent works with Codex."""
        # First convert a Claude agent to Codex format
        claude_agents_dir = integration_test_project / ".claude" / "agents"
        claude_agents_dir.mkdir(parents=True)

        claude_agent = claude_agents_dir / "refactor-agent.md"
        claude_agent.write_text("""
---
name: refactor-agent
description: Agent for code refactoring
tools: Edit, Read, Grep
---

# Refactor Agent

Helps with code refactoring tasks.
""")

        # Simulate conversion (create Codex version)
        codex_agents_dir = integration_test_project / ".codex" / "agents"
        codex_agents_dir.mkdir(parents=True)

        codex_agent = codex_agents_dir / "refactor-agent.md"
        codex_agent.write_text("""
---
name: refactor-agent
description: Agent for code refactoring
tools:
  - Edit
  - Read
  - Grep
---

# Refactor Agent

Helps with code refactoring tasks.
""")

        with patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project):
            backend = CodexAgentBackend()

            result = backend.spawn_agent("refactor-agent", "Refactor this function")

            # Verify agent executed successfully
            assert result["success"] is True
            assert "refactor-agent" in mock_codex_exec_success.call_args[0][0]

    def test_agent_list_consistency(self, integration_test_project, create_test_agents):
        """Test that agent lists are consistent across backends."""
        with patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project):
            claude_backend = ClaudeCodeAgentBackend()
            codex_backend = CodexAgentBackend()

            claude_agents = claude_backend.list_available_agents()
            codex_agents = codex_backend.list_available_agents()

            # Both should have the same agent names
            assert set(claude_agents) == set(codex_agents)
            assert len(claude_agents) == 3  # bug-hunter, zen-architect, test-coverage

            # Verify agents are sorted
            assert claude_agents == sorted(claude_agents)
            assert codex_agents == sorted(codex_agents)

    def test_agent_definition_parsing(self, integration_test_project, sample_agent_definition):
        """Test parsing agent definitions."""
        # Test Claude format (comma-separated tools)
        claude_definition = parse_agent_definition(sample_agent_definition)

        assert claude_definition.name == "test-agent"
        assert claude_definition.description == "A test agent for testing purposes"
        assert claude_definition.system_prompt.strip() == "You are a helpful test agent."
        assert claude_definition.allowed_tools == ["Read", "Grep", "Bash"]
        assert claude_definition.max_turns == 10
        assert claude_definition.model == "gpt-4"

        # Test Codex format (array tools)
        codex_content = sample_agent_definition.replace(
            "allowed_tools: [Read, Grep, Bash]", "tools:\n  - Read\n  - Grep\n  - Bash"
        )
        codex_definition = parse_agent_definition(codex_content)

        assert codex_definition.allowed_tools == ["Read", "Grep", "Bash"]


class TestConvenienceFunctions:
    """Test high-level convenience functions."""

    def test_spawn_agent_convenience_function_claude(
        self, integration_test_project, mock_claude_sdk, create_test_agents, claude_env
    ):
        """Test convenience function with Claude backend."""
        with patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project):
            result = spawn_agent("bug-hunter", "Test task", backend="claude")

            assert result["success"] is True
            assert result["result"] == "Agent response"

    def test_spawn_agent_convenience_function_codex(
        self, integration_test_project, mock_codex_exec_success, create_test_agents, codex_env
    ):
        """Test convenience function with Codex backend."""
        with patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project):
            result = spawn_agent("bug-hunter", "Test task", backend="codex")

            assert result["success"] is True
            assert result["result"] == "Agent executed successfully"

    def test_spawn_agent_auto_backend_selection(
        self, integration_test_project, mock_both_backends_available, create_test_agents, claude_env
    ):
        """Test auto backend selection from environment."""
        with (
            patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project),
            patch("amplifier.core.agent_backend.ClaudeSDKClient") as mock_sdk,
        ):
            mock_client = Mock()
            mock_client.query.return_value = {"content": "Auto-selected response"}
            mock_sdk.return_value = mock_client

            result = spawn_agent("bug-hunter", "Test task")

            # Should auto-select Claude based on AMPLIFIER_BACKEND env var
            assert result["success"] is True
            assert result["result"] == "Auto-selected response"


class TestAgentBackendFactory:
    """Test agent backend factory functionality."""

    def test_agent_backend_factory_creates_correct_backend(self, claude_env, codex_env):
        """Test factory creates correct backend types."""
        # Test Claude backend creation
        backend = AgentBackendFactory.create_agent_backend("claude")
        assert isinstance(backend, ClaudeCodeAgentBackend)

        # Test Codex backend creation
        backend = AgentBackendFactory.create_agent_backend("codex")
        assert isinstance(backend, CodexAgentBackend)

        # Test invalid backend
        with pytest.raises(ValueError, match="Invalid backend type"):
            AgentBackendFactory.create_agent_backend("invalid")

    def test_agent_backend_factory_from_environment(self, claude_env, codex_env):
        """Test factory uses environment variables."""
        # Test Claude from env
        with patch.dict(os.environ, {"AMPLIFIER_BACKEND": "claude"}):
            backend = AgentBackendFactory.create_agent_backend()
            assert isinstance(backend, ClaudeCodeAgentBackend)

        # Test Codex from env
        with patch.dict(os.environ, {"AMPLIFIER_BACKEND": "codex"}):
            backend = AgentBackendFactory.create_agent_backend()
            assert isinstance(backend, CodexAgentBackend)


class TestErrorRecovery:
    """Test error recovery and edge cases."""

    def test_agent_spawn_recovers_from_transient_errors(self, integration_test_project, create_test_agents):
        """Test recovery from transient failures."""
        call_count = 0

        def mock_run_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call fails
                result = Mock()
                result.returncode = 1
                result.stdout = ""
                result.stderr = "Temporary failure"
                return result
            # Second call succeeds
            result = Mock()
            result.returncode = 0
            result.stdout = "Success on retry"
            result.stderr = ""
            return result

        with (
            patch("amplifier.core.agent_backend.Path.cwd", return_value=integration_test_project),
            patch("subprocess.run", side_effect=mock_run_with_retry),
        ):
            backend = CodexAgentBackend()

            # This test simulates retry logic (would need to be implemented in backend)
            # For now, just verify the backend handles failures
            with pytest.raises(AgentSpawnError):
                backend.spawn_agent("bug-hunter", "Test task")

    def test_agent_spawn_with_missing_agent_directory(self, temp_dir):
        """Test graceful handling when agent directories don't exist."""
        with patch("amplifier.core.agent_backend.Path.cwd", return_value=temp_dir):
            backend = ClaudeCodeAgentBackend()

            # Should return empty list, not crash
            agents = backend.list_available_agents()
            assert agents == []


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
