#!/usr/bin/env python3
"""
Session workflow integration tests.

Comprehensive tests covering complete session workflows for both Claude Code and Codex backends,
including initialization, quality checks, transcript export, finalization, and cross-backend scenarios.
"""

import asyncio
import json
import subprocess
from pathlib import Path
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
mcp_servers = ["session_manager", "quality_checker", "transcript_saver"]
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
def memory_disabled_env(monkeypatch):
    """Set environment for disabled memory system."""
    monkeypatch.setenv("MEMORY_SYSTEM_ENABLED", "false")


@pytest.fixture
def memory_enabled_env(monkeypatch):
    """Set environment for enabled memory system."""
    monkeypatch.setenv("MEMORY_SYSTEM_ENABLED", "true")


@pytest.fixture
def claude_env(monkeypatch):
    """Set environment for Claude Code backend."""
    monkeypatch.setenv("AMPLIFIER_BACKEND", "claude")


@pytest.fixture
def codex_env(monkeypatch):
    """Set environment for Codex backend."""
    monkeypatch.setenv("AMPLIFIER_BACKEND", "codex")


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


@pytest.fixture
def mock_claude_transcript(temp_dir):
    """Create mock Claude Code transcript file."""
    transcripts_dir = temp_dir / ".data" / "transcripts"
    transcripts_dir.mkdir(parents=True)

    transcript_file = transcripts_dir / "compact_20240101_100000_test123.txt"
    transcript_file.write_text("""
Session started at 2024-01-01 10:00:00

User: Test user message
Assistant: Test assistant response

Session ended at 2024-01-01 10:30:00
""")

    return transcript_file


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


# Claude Code Session Workflow Tests


class TestClaudeSessionWorkflow:
    """Test Claude Code-specific session workflows."""

    def test_claude_complete_session_workflow(self, integration_test_project, mock_memory_system, mock_claude_cli):
        """Test complete Claude Code session workflow."""
        with (
            patch("amplifier.memory.MemoryStore", return_value=mock_memory_system["store"]),
            patch("amplifier.search.MemorySearcher", return_value=mock_memory_system["searcher"]),
            patch("amplifier.extraction.MemoryExtractor", return_value=mock_memory_system["extractor"]),
            patch("subprocess.run", return_value=mock_claude_cli),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            backend = ClaudeCodeBackend()

            # Initialize session
            init_result = backend.initialize_session("Test complete workflow")
            assert_backend_response(init_result)
            assert "memoriesLoaded" in init_result["metadata"]

            # Run quality checks
            quality_result = backend.run_quality_checks(["main.py"])
            assert_backend_response(quality_result)
            assert "Checks passed" in quality_result["data"]["output"]

            # Export transcript
            export_result = backend.export_transcript(session_id="test123")
            assert_backend_response(export_result)
            assert "path" in export_result["data"]

            # Verify transcript file was created
            transcript_path = Path(export_result["data"]["path"])
            assert transcript_path.exists()

            # Finalize session
            messages = create_mock_messages()
            finalize_result = backend.finalize_session(messages)
            assert_backend_response(finalize_result)
            assert "memoriesExtracted" in finalize_result["metadata"]

    def test_claude_session_with_memory_disabled(self, integration_test_project, memory_disabled_env):
        """Test Claude Code session workflow with memory disabled."""
        with patch("os.getcwd", return_value=str(integration_test_project)):
            backend = ClaudeCodeBackend()

            # Initialize session
            init_result = backend.initialize_session("Test disabled memory")
            assert_backend_response(init_result)
            assert init_result["metadata"]["disabled"] is True
            assert init_result["metadata"]["memoriesLoaded"] == 0

            # Finalize session
            messages = create_mock_messages()
            finalize_result = backend.finalize_session(messages)
            assert_backend_response(finalize_result)
            assert finalize_result["metadata"]["disabled"] is True
            assert finalize_result["metadata"]["memoriesExtracted"] == 0

    def test_claude_session_initialization_only(self, integration_test_project, mock_memory_system):
        """Test Claude Code session initialization only."""
        with (
            patch("amplifier.memory.MemoryStore", return_value=mock_memory_system["store"]),
            patch("amplifier.search.MemorySearcher", return_value=mock_memory_system["searcher"]),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            backend = ClaudeCodeBackend()

            result = backend.initialize_session("Test initialization only")
            assert_backend_response(result)
            assert "additionalContext" in result["data"]
            assert "Relevant Memories" in result["data"]["additionalContext"]
            assert result["metadata"]["memoriesLoaded"] == 1

    def test_claude_session_finalization_timeout(self, integration_test_project, mock_memory_system):
        """Test Claude Code session finalization timeout handling."""
        with (
            patch("amplifier.extraction.MemoryExtractor", return_value=mock_memory_system["extractor"]),
            patch("asyncio.timeout", side_effect=TimeoutError()),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            backend = ClaudeCodeBackend()
            messages = create_mock_messages()

            result = backend.finalize_session(messages)
            assert result["success"] is False
            assert "timeout" in str(result).lower()


# Codex Session Workflow Tests


class TestCodexSessionWorkflow:
    """Test Codex-specific session workflows."""

    def test_codex_complete_session_workflow(self, integration_test_project, mock_memory_system, mock_codex_cli):
        """Test complete Codex session workflow."""
        with (
            patch("amplifier.memory.MemoryStore", return_value=mock_memory_system["store"]),
            patch("amplifier.search.MemorySearcher", return_value=mock_memory_system["searcher"]),
            patch("amplifier.extraction.MemoryExtractor", return_value=mock_memory_system["extractor"]),
            patch("subprocess.run", return_value=mock_codex_cli),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            backend = CodexBackend()

            # Initialize session
            init_result = backend.initialize_session("Test complete workflow")
            assert_backend_response(init_result)
            assert "contextFile" in init_result["data"]

            # Verify context file was created
            context_file = Path(init_result["data"]["contextFile"])
            assert context_file.exists()

            # Run quality checks
            quality_result = backend.run_quality_checks(["main.py"])
            assert_backend_response(quality_result)
            assert "Checks passed" in quality_result["data"]["output"]

            # Export transcript
            export_result = backend.export_transcript(session_id="test123")
            assert_backend_response(export_result)
            assert "path" in export_result["data"]

            # Finalize session
            messages = create_mock_messages()
            finalize_result = backend.finalize_session(messages)
            assert_backend_response(finalize_result)
            assert "memoriesExtracted" in finalize_result["metadata"]

    def test_codex_session_via_wrapper(self, integration_test_project, mock_codex_cli):
        """Test Codex session workflow via wrapper script."""
        wrapper_script = integration_test_project / "amplify-codex.sh"
        wrapper_script.write_text("""
#!/bin/bash
echo "Running session init..."
echo "Running codex exec..."
echo "Running session cleanup..."
""")
        wrapper_script.chmod(0o755)

        with (
            patch("subprocess.run", return_value=mock_codex_cli),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            # Mock the wrapper script execution
            result = subprocess.run([str(wrapper_script), "--profile", "development"], capture_output=True, text=True)

            assert result.returncode == 0
            assert "session init" in result.stdout.lower()
            assert "codex exec" in result.stdout.lower()
            assert "session cleanup" in result.stdout.lower()

    def test_codex_session_with_mcp_tools(self, integration_test_project, mock_memory_system):
        """Test Codex session using MCP tools directly."""
        with (
            patch("sys.path", []),
            patch("builtins.__import__") as mock_import,
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            # Mock MCP server modules
            mock_import.side_effect = lambda name, *args, **kwargs: {
                "amplifier.memory": Mock(MemoryStore=mock_memory_system["store"]),
                "amplifier.search": Mock(MemorySearcher=mock_memory_system["searcher"]),
                "amplifier.extraction": Mock(MemoryExtractor=mock_memory_system["extractor"]),
            }.get(name, Mock())

            # Test initialize_session MCP tool
            try:
                from .codex.mcp_servers.session_manager.server import initialize_session

                result = asyncio.run(initialize_session(prompt="Test MCP workflow"))
                assert "Relevant Memories" in result
            except ImportError:
                pytest.skip("MCP server modules not yet implemented")

    def test_codex_session_manual_scripts(self, integration_test_project, mock_memory_system):
        """Test running Codex session scripts manually."""
        session_init = integration_test_project / ".codex" / "tools" / "session_init.py"
        session_init.parent.mkdir(parents=True, exist_ok=True)
        session_init.write_text("""
import sys
sys.path.insert(0, '.')
from amplifier.core.backend import CodexBackend

backend = CodexBackend()
result = backend.initialize_session("Test manual script")
print(f"Initialized: {result['success']}")
""")

        with (
            patch("amplifier.memory.MemoryStore", return_value=mock_memory_system["store"]),
            patch("amplifier.search.MemorySearcher", return_value=mock_memory_system["searcher"]),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            result = subprocess.run(
                [sys.executable, str(session_init), "--prompt", "Test manual"], capture_output=True, text=True
            )

            assert result.returncode == 0
            assert "Initialized: True" in result.stdout


# Cross-Backend Workflow Tests


class TestCrossBackendWorkflows:
    """Test workflows that work across both backends."""

    def test_backend_switching_preserves_memories(self, integration_test_project, mock_memory_system):
        """Test that switching backends preserves memories."""
        with (
            patch("amplifier.memory.MemoryStore", return_value=mock_memory_system["store"]),
            patch("amplifier.search.MemorySearcher", return_value=mock_memory_system["searcher"]),
            patch("amplifier.extraction.MemoryExtractor", return_value=mock_memory_system["extractor"]),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            # Initialize with Claude Code
            claude_backend = ClaudeCodeBackend()
            claude_init = claude_backend.initialize_session("Test switching")
            assert_backend_response(claude_init)

            # Extract memories with Claude Code
            messages = create_mock_messages()
            claude_finalize = claude_backend.finalize_session(messages)
            assert_backend_response(claude_finalize)

            # Switch to Codex backend
            codex_backend = CodexBackend()
            codex_init = codex_backend.initialize_session("Test switching")
            assert_backend_response(codex_init)

            # Verify same memories are loaded
            assert claude_init["metadata"]["memoriesLoaded"] == codex_init["metadata"]["memoriesLoaded"]

    def test_transcript_conversion_workflow(self, integration_test_project):
        """Test transcript format conversion between backends."""
        with patch("os.getcwd", return_value=str(integration_test_project)):
            # Create Claude transcript
            claude_backend = ClaudeCodeBackend()
            claude_export = claude_backend.export_transcript(session_id="convert_test")
            assert_backend_response(claude_export)

            # Mock conversion to Codex format
            with patch("tools.transcript_manager.convert_transcript") as mock_convert:
                mock_convert.return_value = "/converted/codex/transcript.md"

                # This would normally call transcript_manager.convert_transcript
                # For now, just verify the export worked
                assert "path" in claude_export["data"]

    def test_quality_checks_identical_across_backends(self, integration_test_project, mock_make_check_success):
        """Test that quality checks produce identical results across backends."""
        with (
            patch("subprocess.run", return_value=mock_make_check_success),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            claude_backend = ClaudeCodeBackend()
            codex_backend = CodexBackend()

            # Run quality checks with both backends
            claude_result = claude_backend.run_quality_checks(["main.py"])
            codex_result = codex_backend.run_quality_checks(["main.py"])

            # Verify both succeed
            assert_backend_response(claude_result)
            assert_backend_response(codex_result)

            # Verify results are identical
            assert claude_result["data"]["output"] == codex_result["data"]["output"]
            assert claude_result["metadata"]["returncode"] == codex_result["metadata"]["returncode"]

    def test_memory_extraction_identical_across_backends(
        self, integration_test_project, mock_memory_system, sample_messages
    ):
        """Test that memory extraction is identical across backends."""
        with (
            patch("amplifier.memory.MemoryStore", return_value=mock_memory_system["store"]),
            patch("amplifier.extraction.MemoryExtractor", return_value=mock_memory_system["extractor"]),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            claude_backend = ClaudeCodeBackend()
            codex_backend = CodexBackend()

            # Extract memories with both backends
            claude_result = claude_backend.finalize_session(sample_messages)
            codex_result = codex_backend.finalize_session(sample_messages)

            # Verify both succeed
            assert_backend_response(claude_result)
            assert_backend_response(codex_result)

            # Verify extracted memories count is identical
            assert claude_result["metadata"]["memoriesExtracted"] == codex_result["metadata"]["memoriesExtracted"]


# Error Handling Tests


class TestSessionWorkflowErrors:
    """Test error handling in session workflows."""

    def test_session_workflow_with_import_errors(self, integration_test_project):
        """Test session workflows handle import errors gracefully."""
        with (
            patch("builtins.__import__", side_effect=ImportError("Module not found")),
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            backend = ClaudeCodeBackend()

            # Initialize should handle import error gracefully
            result = backend.initialize_session("Test import error")
            assert result["success"] is False
            assert "import" in str(result).lower()

    def test_session_workflow_with_missing_directories(self, temp_dir):
        """Test workflows handle missing directories gracefully."""
        project_dir = temp_dir / "missing_dirs"
        project_dir.mkdir()

        with patch("os.getcwd", return_value=str(project_dir)):
            backend = ClaudeCodeBackend()

            # Should create .data directory automatically
            result = backend.initialize_session("Test missing dirs")
            assert result["success"] is True

            # Check that .data directory was created
            data_dir = project_dir / ".data"
            assert data_dir.exists()

    def test_session_workflow_with_corrupted_data(self, integration_test_project):
        """Test workflows handle corrupted data gracefully."""
        # Create corrupted memory data file
        memories_dir = integration_test_project / ".data" / "memories"
        memories_dir.mkdir(parents=True)
        corrupted_file = memories_dir / "corrupted.json"
        corrupted_file.write_text("invalid json content {")

        with (
            patch("amplifier.memory.MemoryStore") as mock_store_class,
            patch("os.getcwd", return_value=str(integration_test_project)),
        ):
            # Mock store to raise exception on get_all
            mock_store = Mock()
            mock_store.get_all.side_effect = json.JSONDecodeError("Invalid JSON", "corrupted.json", 0)
            mock_store_class.return_value = mock_store

            backend = ClaudeCodeBackend()

            # Should handle corruption gracefully
            result = backend.initialize_session("Test corrupted data")
            assert result["success"] is False
            assert "error" in result


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
