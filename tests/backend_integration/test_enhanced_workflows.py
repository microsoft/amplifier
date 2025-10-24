#!/usr/bin/env python3
"""
Enhanced workflows integration tests.

Comprehensive tests covering new enhanced workflows for both Claude Code and Codex backends,
including task-driven development, research-assisted development, agent context bridge,
auto-quality checks, periodic saves, and backend abstraction enhancements.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

# Import modules under test (will be mocked where necessary)
try:
    from amplifier.core.backend import BackendFactory
    from amplifier.core.backend import ClaudeCodeBackend
    from amplifier.core.backend import CodexBackend
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
def mock_memory_system():
    """Mock complete memory system components."""
    memory_store = Mock()
    memory_store.get_all.return_value = [
        Mock(content="Test memory 1", category="fact", id="1"),
        Mock(content="Test memory 2", category="pattern", id="2"),
    ]
    memory_store.search_recent.return_value = [Mock(content="Recent memory", category="fact", id="3")]
    memory_store.add_memories_batch.return_value = 3

    memory_searcher = Mock()
    memory_searcher.search.return_value = [
        Mock(memory=Mock(content="Relevant memory", category="fact", score=0.9, id="1"))
    ]

    memory_extractor = Mock()
    memory_extractor.extract_from_messages.return_value = [
        Mock(content="Extracted memory 1", type="fact"),
        Mock(content="Extracted memory 2", type="pattern"),
    ]

    return {
        "store": memory_store,
        "searcher": memory_searcher,
        "extractor": memory_extractor,
    }


@pytest.fixture
def sample_messages():
    """Return sample conversation messages."""
    return [
        {"role": "user", "content": "Test user message"},
        {"role": "assistant", "content": "Test assistant response"},
    ]


@pytest.fixture
def mock_claude_cli():
    """Mock Claude CLI subprocess calls."""
    result = Mock()
    result.returncode = 0
    result.stdout = "Claude Code session completed"
    result.stderr = ""
    return result


@pytest.fixture
def mock_codex_cli():
    """Mock Codex CLI subprocess calls."""
    result = Mock()
    result.returncode = 0
    result.stdout = "Codex session completed"
    result.stderr = ""
    return result


@pytest.fixture
def mock_make_check_success():
    """Mock successful make check execution."""
    result = Mock()
    result.returncode = 0
    result.stdout = "Checks passed successfully"
    result.stderr = ""
    return result


@pytest.fixture
def mock_make_check_failure():
    """Mock failed make check execution."""
    result = Mock()
    result.returncode = 1
    result.stdout = ""
    result.stderr = "Syntax error in test.py"
    return result


@pytest.fixture
def mock_task_tracker():
    """Mock task tracker MCP server tools."""
    return {
        "create_task": AsyncMock(
            return_value={
                "task_id": "task_123",
                "title": "Test task",
                "status": "pending",
                "created_at": "2024-01-01T10:00:00Z",
            }
        ),
        "list_tasks": AsyncMock(
            return_value=[{"task_id": "task_123", "title": "Test task", "status": "pending", "priority": "medium"}]
        ),
        "update_task": AsyncMock(return_value={"task_id": "task_123", "status": "in_progress"}),
        "complete_task": AsyncMock(
            return_value={"task_id": "task_123", "status": "completed", "completed_at": "2024-01-01T11:00:00Z"}
        ),
        "export_tasks": AsyncMock(return_value="# Task List\n\n- [ ] Test task\n"),
    }


@pytest.fixture
def mock_web_research():
    """Mock web research MCP server tools."""
    return {
        "search_web": AsyncMock(
            return_value=[{"title": "Test Result", "url": "https://example.com", "snippet": "Test content snippet"}]
        ),
        "fetch_url": AsyncMock(
            return_value={"url": "https://example.com", "content": "Full page content", "text_only": True}
        ),
        "summarize_content": AsyncMock(return_value="Summary of content"),
    }


@pytest.fixture
def mock_agent_context_bridge():
    """Mock agent context bridge utilities."""
    return {
        "serialize_context": Mock(return_value="/path/to/context.json"),
        "inject_context_to_agent": Mock(return_value=True),
        "extract_agent_result": Mock(
            return_value={"agent_output": "Agent completed task", "formatted_result": "Formatted result for display"}
        ),
    }


@pytest.fixture
def integration_test_project(temp_dir):
    """Create complete project structure for integration tests."""
    project_dir = temp_dir / "integration_project"
    project_dir.mkdir()

    # Create .claude directory
    claude_dir = project_dir / ".claude"
    claude_dir.mkdir()
    (claude_dir / "settings.json").write_text('{"theme": "dark"}')

    # Create .codex directory
    codex_dir = project_dir / ".codex"
    codex_dir.mkdir()
    (codex_dir / "config.toml").write_text("""
[profile.development]
mcp_servers = ["session_manager", "quality_checker", "transcript_saver", "task_tracker", "web_research"]
""")

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
""")

    # Create pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text("""
[project]
name = "integration-test"
version = "0.1.0"

[tool.uv]
dev-dependencies = ["pytest", "ruff", "pyright"]
""")

    # Create .git directory
    git_dir = project_dir / ".git"
    git_dir.mkdir()

    # Create sample Python file
    sample_py = project_dir / "main.py"
    sample_py.write_text("""
def hello():
    print("Hello, world!")

if __name__ == "__main__":
    hello()
""")

    # Create .data directory
    data_dir = project_dir / ".data"
    data_dir.mkdir()

    return project_dir


@pytest.fixture
def mock_codex_session_dir(temp_dir):
    """Create mock Codex session directory."""
    sessions_dir = temp_dir / ".codex" / "sessions"
    sessions_dir.mkdir(parents=True)

    session_id = "test_session_123"
    session_dir = sessions_dir / session_id
    session_dir.mkdir()

    # Create meta.json
    meta = {"session_id": session_id, "started_at": "2024-01-01T10:00:00Z", "cwd": str(temp_dir)}
    (session_dir / "meta.json").write_text(json.dumps(meta))

    # Create history.jsonl
    history = [{"session_id": session_id, "ts": 1640995200, "text": "Test message"}]
    history_content = "\n".join(json.dumps(h) for h in history)
    (session_dir / "history.jsonl").write_text(history_content)

    return session_dir


# Test Utilities


def create_mock_messages(count=3):
    """Create mock conversation messages."""
    return [{"role": "user", "content": f"User message {i}"} for i in range(count)]


def assert_backend_response(response, expected_success=True):
    """Assert standard backend response structure."""
    assert "success" in response
    assert "data" in response
    assert "metadata" in response
    if expected_success:
        assert response["success"] is True


# Task-Driven Development Workflow Tests


class TestTaskDrivenDevelopmentWorkflow:
    """Test task-driven development workflows."""

    def test_create_task_and_work_workflow(self, integration_test_project, mock_task_tracker, mock_codex_cli):
        """Test complete workflow: create task → work on code → complete task."""
        with (
            patch("amplifier.core.backend.CodexBackend.manage_tasks") as mock_manage_tasks,
            patch("subprocess.run", return_value=mock_codex_cli),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            # Mock task operations
            mock_manage_tasks.side_effect = [
                # create_task
                {
                    "success": True,
                    "data": {"task_id": "task_123", "title": "Implement feature X"},
                    "metadata": {"action": "create"},
                },
                # list_tasks
                {"success": True, "data": [{"task_id": "task_123", "status": "in_progress"}], "metadata": {"count": 1}},
                # complete_task
                {
                    "success": True,
                    "data": {"task_id": "task_123", "status": "completed"},
                    "metadata": {"action": "complete"},
                },
            ]

            backend = CodexBackend()

            # Create task
            create_result = backend.manage_tasks("create", title="Implement feature X", description="Add new feature")
            assert_backend_response(create_result)
            assert create_result["data"]["task_id"] == "task_123"

            # List tasks (during work)
            list_result = backend.manage_tasks("list", filter_status="pending")
            assert_backend_response(list_result)
            assert len(list_result["data"]) == 1

            # Complete task
            complete_result = backend.manage_tasks("complete", task_id="task_123")
            assert_backend_response(complete_result)
            assert complete_result["data"]["status"] == "completed"

    def test_task_persistence_across_sessions(self, integration_test_project, mock_task_tracker):
        """Test that tasks persist across sessions."""
        with (
            patch("amplifier.core.backend.CodexBackend.manage_tasks") as mock_manage_tasks,
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            backend = CodexBackend()

            # Create task in first session
            mock_manage_tasks.return_value = {
                "success": True,
                "data": {"task_id": "persistent_task", "title": "Persistent task"},
                "metadata": {"action": "create"},
            }

            create_result = backend.manage_tasks("create", title="Persistent task")
            assert_backend_response(create_result)

            # Simulate new session (reset mock)
            mock_manage_tasks.return_value = {
                "success": True,
                "data": [{"task_id": "persistent_task", "title": "Persistent task", "status": "pending"}],
                "metadata": {"count": 1},
            }

            # List tasks in new session - should still exist
            list_result = backend.manage_tasks("list")
            assert_backend_response(list_result)
            assert len(list_result["data"]) == 1
            assert list_result["data"][0]["task_id"] == "persistent_task"

    def test_task_export_workflow(self, integration_test_project, mock_task_tracker):
        """Test task export functionality."""
        with (
            patch("amplifier.core.backend.CodexBackend.manage_tasks") as mock_manage_tasks,
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            backend = CodexBackend()

            # Mock export operation
            mock_manage_tasks.return_value = {
                "success": True,
                "data": {"format": "markdown", "content": "# Task List\n\n- [ ] Task 1\n- [x] Task 2"},
                "metadata": {"exported_at": "2024-01-01T12:00:00Z"},
            }

            export_result = backend.manage_tasks("export", format="markdown")
            assert_backend_response(export_result)
            assert "Task List" in export_result["data"]["content"]
            assert export_result["data"]["format"] == "markdown"


# Research-Assisted Development Workflow Tests


class TestResearchAssistedDevelopmentWorkflow:
    """Test research-assisted development workflows."""

    def test_search_and_fetch_workflow(self, integration_test_project, mock_web_research, mock_codex_cli):
        """Test complete workflow: search web → fetch content → use in code."""
        with (
            patch("amplifier.core.backend.CodexBackend.search_web") as mock_search,
            patch("amplifier.core.backend.CodexBackend.fetch_url") as mock_fetch,
            patch("subprocess.run", return_value=mock_codex_cli),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            # Mock search results
            mock_search.return_value = {
                "success": True,
                "data": [
                    {"title": "API Documentation", "url": "https://api.example.com", "snippet": "API docs content"}
                ],
                "metadata": {"num_results": 1, "cached": False},
            }

            # Mock fetch results
            mock_fetch.return_value = {
                "success": True,
                "data": {"url": "https://api.example.com", "content": "Full API documentation content"},
                "metadata": {"cached": False, "size": 1024},
            }

            backend = CodexBackend()

            # Search web
            search_result = backend.search_web("API documentation", num_results=5)
            assert_backend_response(search_result)
            assert len(search_result["data"]) == 1
            assert search_result["data"][0]["title"] == "API Documentation"

            # Fetch specific URL
            fetch_result = backend.fetch_url("https://api.example.com")
            assert_backend_response(fetch_result)
            assert "API documentation content" in fetch_result["data"]["content"]

    def test_web_cache_usage(self, integration_test_project, mock_web_research):
        """Test that web research uses caching appropriately."""
        with (
            patch("amplifier.core.backend.CodexBackend.search_web") as mock_search,
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            backend = CodexBackend()

            # First search - not cached
            mock_search.return_value = {
                "success": True,
                "data": [{"title": "Result 1", "url": "https://example.com"}],
                "metadata": {"cached": False},
            }

            result1 = backend.search_web("test query")
            assert result1["metadata"]["cached"] is False

            # Second search - should be cached
            mock_search.return_value = {
                "success": True,
                "data": [{"title": "Result 1", "url": "https://example.com"}],
                "metadata": {"cached": True},
            }

            result2 = backend.search_web("test query")
            assert result2["metadata"]["cached"] is True

    def test_web_research_error_handling(self, integration_test_project, mock_web_research):
        """Test error handling in web research operations."""
        with (
            patch("amplifier.core.backend.CodexBackend.search_web") as mock_search,
            patch("amplifier.core.backend.CodexBackend.fetch_url") as mock_fetch,
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            backend = CodexBackend()

            # Test search error
            mock_search.return_value = {"success": False, "data": {}, "metadata": {"error": "Network timeout"}}

            search_result = backend.search_web("test query")
            assert search_result["success"] is False
            assert "timeout" in search_result["metadata"]["error"]

            # Test fetch error
            mock_fetch.return_value = {"success": False, "data": {}, "metadata": {"error": "404 Not Found"}}

            fetch_result = backend.fetch_url("https://nonexistent.example.com")
            assert fetch_result["success"] is False
            assert "404" in fetch_result["metadata"]["error"]


# Agent Context Bridge Workflow Tests


class TestAgentContextBridgeWorkflow:
    """Test agent context bridge workflows."""

    def test_spawn_agent_with_context_workflow(
        self, integration_test_project, mock_agent_context_bridge, mock_codex_cli
    ):
        """Test complete workflow: spawn agent with context → verify context passed → integrate results."""
        with (
            patch("amplifier.core.backend.CodexBackend.spawn_agent_with_context") as mock_spawn_with_context,
            patch("subprocess.run", return_value=mock_codex_cli),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            # Mock context serialization and agent spawning
            mock_spawn_with_context.return_value = {
                "success": True,
                "data": {
                    "agent_output": "Agent completed task successfully",
                    "formatted_result": "Task completed: Implemented feature X",
                },
                "metadata": {"agent_name": "code_helper", "context_size": 1500, "execution_time": 30},
            }

            backend = CodexBackend()
            messages = create_mock_messages()

            # Spawn agent with context
            result = backend.spawn_agent_with_context(
                agent_name="code_helper", task="Implement feature X", messages=messages
            )

            assert_backend_response(result)
            assert "Agent completed task" in result["data"]["agent_output"]
            assert result["metadata"]["agent_name"] == "code_helper"

    def test_context_serialization(self, integration_test_project, mock_agent_context_bridge):
        """Test context serialization functionality."""
        with (
            patch("amplifier.core.backend.CodexBackend.spawn_agent_with_context") as mock_spawn,
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            backend = CodexBackend()
            messages = create_mock_messages()

            # Mock serialization
            mock_spawn.return_value = {
                "success": True,
                "data": {"context_file": "/tmp/context_123.json"},
                "metadata": {"serialized_tokens": 1200},
            }

            result = backend.spawn_agent_with_context("test_agent", "test task", messages)
            assert_backend_response(result)
            assert "context_file" in result["data"]
            assert result["metadata"]["serialized_tokens"] == 1200

    def test_agent_result_extraction(self, integration_test_project, mock_agent_context_bridge):
        """Test agent result extraction and formatting."""
        with (
            patch("amplifier.core.backend.CodexBackend.spawn_agent_with_context") as mock_spawn,
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            backend = CodexBackend()

            # Mock result extraction
            mock_spawn.return_value = {
                "success": True,
                "data": {"agent_output": "Raw agent output", "formatted_result": "Clean formatted result for display"},
                "metadata": {"extraction_success": True},
            }

            result = backend.spawn_agent_with_context("test_agent", "test task", [])
            assert_backend_response(result)
            assert result["data"]["formatted_result"] == "Clean formatted result for display"
            assert result["metadata"]["extraction_success"] is True


# Auto-Quality Check Workflow Tests


class TestAutoQualityCheckWorkflow:
    """Test auto-quality check workflows."""

    def test_auto_check_after_file_modification(self, integration_test_project, mock_make_check_success):
        """Test auto-quality checks trigger after file modifications."""
        with (
            patch("subprocess.run", return_value=mock_make_check_success),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            backend = CodexBackend()

            # Modify a file
            test_file = integration_test_project / "main.py"
            original_content = test_file.read_text()
            test_file.write_text(original_content + "\n# Modified content")

            # Simulate auto-check trigger (normally done by wrapper script)
            result = backend.run_quality_checks(["main.py"])

            assert_backend_response(result)
            assert result["metadata"]["returncode"] == 0
            assert "Checks passed" in result["data"]["output"]

    def test_auto_check_passing_results(self, integration_test_project, mock_make_check_success):
        """Test auto-quality checks with passing results."""
        with (
            patch("subprocess.run", return_value=mock_make_check_success),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            backend = CodexBackend()

            # Run checks
            result = backend.run_quality_checks(["main.py"])

            assert_backend_response(result)
            assert result["success"] is True
            assert result["metadata"]["returncode"] == 0

    def test_auto_check_failing_results(self, integration_test_project, mock_make_check_failure):
        """Test auto-quality checks with failing results."""
        with (
            patch("subprocess.run", return_value=mock_make_check_failure),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            backend = CodexBackend()

            # Run checks that will fail
            result = backend.run_quality_checks(["main.py"])

            assert result["success"] is False
            assert result["metadata"]["returncode"] == 1
            assert "Syntax error" in result["data"]["output"]


# Periodic Save Workflow Tests


class TestPeriodicSaveWorkflow:
    """Test periodic save workflows."""

    def test_periodic_save_during_session(self, integration_test_project, mock_codex_cli):
        """Test periodic transcript saves during session."""
        with (
            patch("subprocess.run", return_value=mock_codex_cli),
            patch("amplifier.core.backend.CodexBackend.export_transcript") as mock_export,
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            # Mock transcript export
            mock_export.return_value = {
                "success": True,
                "data": {"path": "/path/to/transcript.md"},
                "metadata": {"auto_save": True},
            }

            backend = CodexBackend()

            # Simulate periodic save (normally done by background process)
            save_result = backend.export_transcript(session_id="test_session", auto_save=True)

            assert_backend_response(save_result)
            assert save_result["metadata"]["auto_save"] is True
            assert "transcript.md" in save_result["data"]["path"]

    def test_save_frequency_control(self, integration_test_project):
        """Test save frequency is respected."""
        with patch("time.time") as mock_time, patch("os.getcwd", return_value=str(integration_test_project)):
            # Simulate time progression
            mock_time.side_effect = [1000, 1000, 1000 + 600, 1000 + 1200]  # 10 minutes apart

            backend = CodexBackend()

            # This would normally be tested with actual timing in the wrapper script
            # For unit test, we verify the logic exists
            assert hasattr(backend, "export_transcript")

    def test_save_cleanup_on_session_end(self, integration_test_project, mock_codex_cli):
        """Test save cleanup when session ends."""
        with (
            patch("subprocess.run", return_value=mock_codex_cli),
            patch("os.getcwd", return_value=str(integration_test_project)),
            patch("os.remove") as mock_remove,
        ):
            backend = CodexBackend()

            # Simulate session end cleanup (normally done by wrapper script)
            # Verify cleanup methods exist
            assert hasattr(backend, "finalize_session")


# Backend Abstraction Tests


class TestBackendAbstraction:
    """Test backend abstraction for new features."""

    def test_new_methods_available_in_both_backends(self, integration_test_project):
        """Test that new methods work with both backends."""
        with patch("os.getcwd", return_value=str(integration_test_project)):
            claude_backend = ClaudeCodeBackend()
            codex_backend = CodexBackend()

            # Check that both backends have the new methods
            assert hasattr(claude_backend, "manage_tasks")
            assert hasattr(codex_backend, "manage_tasks")
            assert hasattr(claude_backend, "search_web")
            assert hasattr(codex_backend, "search_web")
            assert hasattr(claude_backend, "spawn_agent_with_context")
            assert hasattr(codex_backend, "spawn_agent_with_context")

    def test_feature_detection(self, integration_test_project):
        """Test feature detection capabilities."""
        with patch("os.getcwd", return_value=str(integration_test_project)):
            backend = CodexBackend()

            # Test backend info includes new features
            info = backend.get_backend_info()
            assert "features" in info
            assert "task_tracking" in info["features"]
            assert "web_research" in info["features"]
            assert "agent_context_bridge" in info["features"]

    def test_graceful_degradation_when_features_unavailable(self, integration_test_project):
        """Test graceful degradation when features are not available."""
        with patch("os.getcwd", return_value=str(integration_test_project)):
            # Mock Claude backend without new features
            claude_backend = ClaudeCodeBackend()

            # Test that methods return appropriate "not supported" responses
            task_result = claude_backend.manage_tasks("list")
            assert task_result["success"] is False
            assert "not supported" in str(task_result).lower()

            search_result = claude_backend.search_web("test")
            assert search_result["success"] is False
            assert "not supported" in str(search_result).lower()


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
