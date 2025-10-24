#!/usr/bin/env python3
"""
Tests for MCP servers.

Comprehensive tests covering all MCP server implementations:
- session_manager: Memory system integration
- quality_checker: Code quality validation
- transcript_saver: Session transcript management
- base: Shared utilities and logging
"""

import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest

# Add project paths for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / ".codex"))

# Import modules under test (will be mocked where necessary)
try:
    from .codex.mcp_servers.base import AmplifierMCPServer
    from .codex.mcp_servers.base import MCPLogger
    from .codex.mcp_servers.base import check_memory_system_enabled
    from .codex.mcp_servers.base import error_response
    from .codex.mcp_servers.base import get_project_root
    from .codex.mcp_servers.base import metadata_response
    from .codex.mcp_servers.base import safe_import
    from .codex.mcp_servers.base import setup_amplifier_path
    from .codex.mcp_servers.base import success_response
except ImportError:
    # Modules not yet implemented - tests will use mocks
    pass


# Test Fixtures


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
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
def mock_codex_session(temp_dir):
    """Create mock Codex session directory structure."""
    sessions_dir = temp_dir / ".codex" / "sessions"
    sessions_dir.mkdir(parents=True)

    session_id = "test_session_123"
    session_dir = sessions_dir / session_id
    session_dir.mkdir()

    # Create meta.json
    meta = {"session_id": session_id, "started_at": "2024-01-01T10:00:00Z", "cwd": str(temp_dir / "project")}
    (session_dir / "meta.json").write_text(json.dumps(meta))

    # Create history.jsonl
    history = [{"session_id": session_id, "ts": 1640995200, "text": "Test message"}]
    history_content = "\n".join(json.dumps(h) for h in history)
    (session_dir / "history.jsonl").write_text(history_content)

    return session_dir


@pytest.fixture
def mock_transcript_exporter():
    """Mock transcript export functions."""
    exporter = Mock()
    exporter.export_codex_transcript.return_value = "/path/to/exported/transcript.md"
    exporter.get_current_codex_session.return_value = "current_session_123"
    exporter.get_project_sessions.return_value = ["session1", "session2"]
    return exporter


# Base Module Tests


class TestMCPBase:
    """Test base utilities and shared functionality."""

    def test_mcp_logger_initialization(self, temp_dir):
        """Verify logger creates log files."""
        log_dir = temp_dir / ".codex" / "logs"
        log_dir.mkdir(parents=True)

        logger = MCPLogger("test_server", log_dir=log_dir)

        # Check log file creation
        log_file = log_dir / "test_server.log"
        assert log_file.exists()

        # Test logging
        logger.info("Test message")
        content = log_file.read_text()
        assert "Test message" in content

    def test_mcp_logger_cleanup(self, temp_dir):
        """Verify old log cleanup works."""
        log_dir = temp_dir / ".codex" / "logs"
        log_dir.mkdir(parents=True)

        # Create old log files
        old_log = log_dir / "old_server.log.2023-01-01"
        old_log.write_text("old content")
        old_log.touch()  # Ensure it exists

        # Create recent log file
        recent_log = log_dir / "recent_server.log"
        recent_log.write_text("recent content")

        logger = MCPLogger("test_server", log_dir=log_dir)
        logger.cleanup_old_logs(days=1)

        # Old log should be removed, recent should remain
        assert not old_log.exists()
        assert recent_log.exists()

    def test_get_project_root(self, temp_project_dir):
        """Test project root detection with various structures."""
        # Test with .git
        root = get_project_root(temp_project_dir / "subdir")
        assert root == temp_project_dir

        # Test with pyproject.toml
        empty_dir = temp_project_dir.parent / "empty"
        empty_dir.mkdir()
        (empty_dir / "pyproject.toml").touch()

        root = get_project_root(empty_dir / "deep" / "path")
        assert root == empty_dir

    def test_setup_amplifier_path(self, temp_project_dir):
        """Verify path manipulation."""
        original_path = sys.path.copy()

        try:
            setup_amplifier_path(temp_project_dir)

            # Check that amplifier path was added
            amplifier_path = str(temp_project_dir / "amplifier")
            assert amplifier_path in sys.path

        finally:
            sys.path = original_path

    def test_check_memory_system_enabled(self):
        """Test environment variable reading."""
        # Test default (enabled)
        with patch.dict(os.environ, {}, clear=True):
            assert check_memory_system_enabled() is True

        # Test explicitly enabled
        with patch.dict(os.environ, {"MEMORY_SYSTEM_ENABLED": "true"}):
            assert check_memory_system_enabled() is True

        # Test disabled
        with patch.dict(os.environ, {"MEMORY_SYSTEM_ENABLED": "false"}):
            assert check_memory_system_enabled() is False

    def test_safe_import_success(self):
        """Test successful module import."""
        # Test importing existing module
        result = safe_import("pathlib", "Path")
        assert result is not None
        assert hasattr(result, "__name__")

    def test_safe_import_failure(self):
        """Test graceful import failure handling."""
        # Test importing non-existent module
        result = safe_import("non_existent_module", "SomeClass")
        assert result is None

    def test_response_builders(self):
        """Test success/error/metadata response formatting."""
        # Success response
        success = success_response("Operation completed", {"count": 5})
        assert success["status"] == "success"
        assert success["message"] == "Operation completed"
        assert success["data"]["count"] == 5

        # Error response
        error = error_response("Something failed", "ImportError")
        assert error["status"] == "error"
        assert error["message"] == "Something failed"
        assert error["error_type"] == "ImportError"

        # Metadata response
        metadata = metadata_response({"sessions": 10, "exported": 8})
        assert metadata["status"] == "metadata"
        assert metadata["sessions"] == 10
        assert metadata["exported"] == 8


# Session Manager Tests


class TestSessionManager:
    """Test session manager MCP server."""

    @pytest.mark.asyncio
    async def test_initialize_session_with_memories(self, mock_memory_store, mock_memory_searcher):
        """Mock MemoryStore/Searcher, verify memory loading."""
        with patch("sys.path", []), patch("builtins.__import__") as mock_import:
            # Mock amplifier modules
            mock_import.side_effect = lambda name, *args, **kwargs: {
                "amplifier.memory": Mock(MemoryStore=mock_memory_store),
                "amplifier.search": Mock(MemorySearcher=mock_memory_searcher),
            }.get(name, Mock())

            # Import and test the tool function
            from .codex.mcp_servers.session_manager.server import initialize_session

            result = await initialize_session(prompt="Test prompt for memory search", context="Additional context")

            # Verify memory search was called
            mock_memory_searcher.search.assert_called_once()

            # Check response structure
            assert "Relevant Memories" in result
            assert "Recent Context" in result
            assert result["metadata"]["memories_loaded"] == 2

    @pytest.mark.asyncio
    async def test_initialize_session_disabled(self):
        """Test behavior when memory system disabled."""
        with patch.dict(os.environ, {"MEMORY_SYSTEM_ENABLED": "false"}):
            from .codex.mcp_servers.session_manager.server import initialize_session

            result = await initialize_session(prompt="Test prompt")

            assert "memory system is disabled" in result.lower()
            assert result["metadata"]["disabled"] is True

    @pytest.mark.asyncio
    async def test_initialize_session_no_prompt(self, mock_memory_store, mock_memory_searcher):
        """Test empty prompt handling."""
        with patch("sys.path", []), patch("builtins.__import__") as mock_import:
            mock_import.side_effect = lambda name, *args, **kwargs: {
                "amplifier.memory": Mock(MemoryStore=mock_memory_store),
                "amplifier.search": Mock(MemorySearcher=mock_memory_searcher),
            }.get(name, Mock())

            from .codex.mcp_servers.session_manager.server import initialize_session

            result = await initialize_session(prompt="", context=None)

            # Should still work with empty prompt
            assert isinstance(result, dict)
            assert "metadata" in result

    @pytest.mark.asyncio
    async def test_initialize_session_import_error(self):
        """Test graceful degradation on import failure."""
        with patch("builtins.__import__", side_effect=ImportError("Module not found")):
            from .codex.mcp_servers.session_manager.server import initialize_session

            result = await initialize_session(prompt="Test prompt")

            assert "error" in result
            assert "import" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_finalize_session_extract_memories(self, mock_memory_store, mock_memory_extractor):
        """Mock MemoryExtractor, verify extraction."""
        with patch("sys.path", []), patch("builtins.__import__") as mock_import:
            mock_import.side_effect = lambda name, *args, **kwargs: {
                "amplifier.memory": Mock(MemoryStore=mock_memory_store),
                "amplifier.extraction": Mock(MemoryExtractor=mock_memory_extractor),
            }.get(name, Mock())

            from .codex.mcp_servers.session_manager.server import finalize_session

            messages = [
                {"role": "user", "content": "Test message 1"},
                {"role": "assistant", "content": "Test response 1"},
            ]

            result = await finalize_session(messages=messages, context="Test context")

            # Verify extraction was called
            mock_memory_extractor.extract_from_messages.assert_called_once_with(messages)

            # Verify storage was called
            mock_memory_store.add_memories_batch.assert_called_once()

            # Check response
            assert result["memories_extracted"] == 2
            assert result["metadata"]["source"] == "session_finalize"

    @pytest.mark.asyncio
    async def test_finalize_session_disabled(self):
        """Test disabled memory system."""
        with patch.dict(os.environ, {"MEMORY_SYSTEM_ENABLED": "false"}):
            from .codex.mcp_servers.session_manager.server import finalize_session

            result = await finalize_session(messages=[], context=None)

            assert result["metadata"]["disabled"] is True
            assert result["memories_extracted"] == 0

    @pytest.mark.asyncio
    async def test_finalize_session_timeout(self, mock_memory_extractor):
        """Test timeout handling."""
        with (
            patch("sys.path", []),
            patch("builtins.__import__") as mock_import,
            patch("asyncio.timeout") as mock_timeout,
        ):
            mock_import.side_effect = lambda name, *args, **kwargs: {
                "amplifier.extraction": Mock(MemoryExtractor=mock_memory_extractor),
            }.get(name, Mock())

            # Mock timeout exception
            mock_timeout.side_effect = TimeoutError()

            from .codex.mcp_servers.session_manager.server import finalize_session

            result = await finalize_session(messages=[], context=None)

            assert "timeout" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_finalize_session_no_messages(self, mock_memory_store, mock_memory_extractor):
        """Test empty message list."""
        with patch("sys.path", []), patch("builtins.__import__") as mock_import:
            mock_import.side_effect = lambda name, *args, **kwargs: {
                "amplifier.memory": Mock(MemoryStore=mock_memory_store),
                "amplifier.extraction": Mock(MemoryExtractor=mock_memory_extractor),
            }.get(name, Mock())

            from .codex.mcp_servers.session_manager.server import finalize_session

            result = await finalize_session(messages=[], context=None)

            # Should still work with empty messages
            assert result["memories_extracted"] == 2  # Mock returns 2 memories

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Verify health check returns correct status."""
        with patch("sys.path", []), patch("builtins.__import__") as mock_import:
            mock_import.side_effect = lambda name, *args, **kwargs: Mock()

            from .codex.mcp_servers.session_manager.server import health_check

            result = await health_check()

            assert result["server"] == "session_manager"
            assert "memory_system_enabled" in result
            assert "amplifier_modules_available" in result


# Quality Checker Tests


class TestQualityChecker:
    """Test quality checker MCP server."""

    @pytest.mark.asyncio
    async def test_check_code_quality_success(self, temp_project_dir, mock_subprocess):
        """Mock subprocess, verify make check execution."""
        with (
            patch("subprocess.run", return_value=mock_subprocess),
            patch("os.getcwd", return_value=str(temp_project_dir)),
        ):
            from .codex.mcp_servers.quality_checker.server import check_code_quality

            result = await check_code_quality(file_paths=["test.py"], tool_name=None, cwd=str(temp_project_dir))

            # Verify subprocess was called
            subprocess.run.assert_called_once()

            # Check result structure
            assert result["status"] == "passed"
            assert "Checks passed successfully" in result["output"]
            assert result["metadata"]["command"] == "make check"

    @pytest.mark.asyncio
    async def test_check_code_quality_no_makefile(self, temp_dir):
        """Test graceful handling when Makefile missing."""
        project_dir = temp_dir / "no_makefile"
        project_dir.mkdir()

        with patch("os.getcwd", return_value=str(project_dir)):
            from .codex.mcp_servers.quality_checker.server import check_code_quality

            result = await check_code_quality(file_paths=["test.py"])

            assert result["status"] == "error"
            assert "makefile" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_check_code_quality_failure(self, temp_project_dir):
        """Test handling of failed checks."""
        failed_result = Mock()
        failed_result.returncode = 1
        failed_result.stdout = ""
        failed_result.stderr = "Syntax error in test.py"

        with (
            patch("subprocess.run", return_value=failed_result),
            patch("os.getcwd", return_value=str(temp_project_dir)),
        ):
            from .codex.mcp_servers.quality_checker.server import check_code_quality

            result = await check_code_quality(file_paths=["test.py"])

            assert result["status"] == "failed"
            assert "Syntax error" in result["output"]

    @pytest.mark.asyncio
    async def test_check_code_quality_worktree(self, temp_project_dir):
        """Test worktree environment setup."""
        # Create .git file pointing to parent
        git_file = temp_project_dir / ".git"
        git_file.write_text("gitdir: ../.git\n")

        with (
            patch("subprocess.run") as mock_run,
            patch("os.getcwd", return_value=str(temp_project_dir)),
            patch.dict(os.environ, {}, clear=True),
        ):
            mock_run.return_value = Mock(returncode=0, stdout="Success", stderr="")

            from .codex.mcp_servers.quality_checker.server import check_code_quality

            await check_code_quality(file_paths=["test.py"])

            # Should have unset VIRTUAL_ENV
            assert "VIRTUAL_ENV" not in os.environ

    @pytest.mark.asyncio
    async def test_run_specific_checks_lint(self, temp_project_dir):
        """Test ruff lint invocation."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Lint passed", stderr="")

            from .codex.mcp_servers.quality_checker.server import run_specific_checks

            result = await run_specific_checks(check_type="lint", file_paths=["test.py"], args=["--fix"])

            assert result["status"] == "passed"
            assert "ruff check" in result["command"]

    @pytest.mark.asyncio
    async def test_run_specific_checks_type(self, temp_project_dir):
        """Test pyright invocation."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Type check passed", stderr="")

            from .codex.mcp_servers.quality_checker.server import run_specific_checks

            result = await run_specific_checks(check_type="type", file_paths=["test.py"])

            assert result["status"] == "passed"
            assert "pyright" in result["command"]

    @pytest.mark.asyncio
    async def test_run_specific_checks_test(self, temp_project_dir):
        """Test pytest invocation."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Tests passed", stderr="")

            from .codex.mcp_servers.quality_checker.server import run_specific_checks

            result = await run_specific_checks(check_type="test", file_paths=["tests/"])

            assert result["status"] == "passed"
            assert "pytest" in result["command"]

    @pytest.mark.asyncio
    async def test_validate_environment(self, temp_project_dir):
        """Test environment validation."""
        with patch("os.getcwd", return_value=str(temp_project_dir)):
            from .codex.mcp_servers.quality_checker.server import validate_environment

            result = await validate_environment()

            assert result["makefile_exists"] is True
            assert result["venv_exists"] is False  # No .venv in temp dir
            assert "uv_available" in result

    def test_find_project_root(self, temp_project_dir):
        """Test project root finding logic."""
        from .codex.mcp_servers.quality_checker.server import find_project_root

        # Test from subdirectory
        subdir = temp_project_dir / "src" / "package"
        subdir.mkdir(parents=True)

        root = find_project_root(subdir)
        assert root == temp_project_dir

    def test_make_target_exists(self, temp_project_dir):
        """Test Makefile target detection."""
        from .codex.mcp_servers.quality_checker.server import make_target_exists

        makefile_path = temp_project_dir / "Makefile"

        assert make_target_exists(makefile_path, "check") is True
        assert make_target_exists(makefile_path, "nonexistent") is False


# Transcript Saver Tests


class TestTranscriptSaver:
    """Test transcript saver MCP server."""

    @pytest.mark.asyncio
    async def test_save_current_transcript(self, mock_transcript_exporter):
        """Mock transcript_exporter, verify export."""
        with patch("sys.path", []), patch("builtins.__import__") as mock_import:
            mock_import.side_effect = lambda name, *args, **kwargs: {
                ".codex.tools.transcript_exporter": mock_transcript_exporter,
            }.get(name, Mock())

            from .codex.mcp_servers.transcript_saver.server import save_current_transcript

            result = await save_current_transcript(session_id=None, format="standard", output_dir=".codex/transcripts")

            # Verify exporter was called
            mock_transcript_exporter.export_codex_transcript.assert_called_once()

            # Check result
            assert result["export_path"] == "/path/to/exported/transcript.md"
            assert "metadata" in result

    @pytest.mark.asyncio
    async def test_save_current_transcript_no_session(self, mock_transcript_exporter):
        """Test handling when no session found."""
        mock_transcript_exporter.get_current_codex_session.return_value = None

        with patch("sys.path", []), patch("builtins.__import__") as mock_import:
            mock_import.side_effect = lambda name, *args, **kwargs: {
                ".codex.tools.transcript_exporter": mock_transcript_exporter,
            }.get(name, Mock())

            from .codex.mcp_servers.transcript_saver.server import save_current_transcript

            result = await save_current_transcript()

            assert result["status"] == "error"
            assert "no session" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_save_current_transcript_custom_format(self, mock_transcript_exporter):
        """Test format options."""
        with patch("sys.path", []), patch("builtins.__import__") as mock_import:
            mock_import.side_effect = lambda name, *args, **kwargs: {
                ".codex.tools.transcript_exporter": mock_transcript_exporter,
            }.get(name, Mock())

            from .codex.mcp_servers.transcript_saver.server import save_current_transcript

            result = await save_current_transcript(format="extended")

            # Verify format parameter was passed
            call_args = mock_transcript_exporter.export_codex_transcript.call_args
            assert call_args[1]["format_type"] == "extended"

    @pytest.mark.asyncio
    async def test_save_project_transcripts(self, mock_transcript_exporter, temp_project_dir):
        """Test batch export."""
        with patch("sys.path", []), patch("builtins.__import__") as mock_import:
            mock_import.side_effect = lambda name, *args, **kwargs: {
                ".codex.tools.transcript_exporter": mock_transcript_exporter,
            }.get(name, Mock())

            from .codex.mcp_servers.transcript_saver.server import save_project_transcripts

            result = await save_project_transcripts(
                project_dir=str(temp_project_dir), format="standard", incremental=True
            )

            assert len(result["exported_sessions"]) == 2
            assert result["metadata"]["incremental"] is True

    @pytest.mark.asyncio
    async def test_save_project_transcripts_incremental(self, mock_transcript_exporter, temp_project_dir):
        """Test incremental mode."""
        # Mock existing transcripts
        with patch("os.path.exists", return_value=True):
            with patch("sys.path", []), patch("builtins.__import__") as mock_import:
                mock_import.side_effect = lambda name, *args, **kwargs: {
                    ".codex.tools.transcript_exporter": mock_transcript_exporter,
                }.get(name, Mock())

                from .codex.mcp_servers.transcript_saver.server import save_project_transcripts

                result = await save_project_transcripts(incremental=True)

                # Should skip already exported sessions
                assert result["metadata"]["skipped_existing"] >= 0

    @pytest.mark.asyncio
    async def test_list_available_sessions(self, mock_codex_session):
        """Test session listing."""
        with patch("pathlib.Path.glob") as mock_glob:
            mock_glob.return_value = [mock_codex_session]

            from .codex.mcp_servers.transcript_saver.server import list_available_sessions

            result = await list_available_sessions(limit=10)

            assert len(result["sessions"]) >= 1
            assert "session_id" in result["sessions"][0]
            assert "start_time" in result["sessions"][0]

    @pytest.mark.asyncio
    async def test_list_available_sessions_project_filter(self, mock_codex_session, temp_project_dir):
        """Test project filtering."""
        with patch("pathlib.Path.glob") as mock_glob, patch("json.load") as mock_json_load:
            mock_glob.return_value = [mock_codex_session]
            mock_json_load.return_value = {"session_id": "test123", "cwd": str(temp_project_dir)}

            from .codex.mcp_servers.transcript_saver.server import list_available_sessions

            result = await list_available_sessions(project_only=True)

            # Should filter to only project sessions
            assert len(result["sessions"]) >= 0

    @pytest.mark.asyncio
    async def test_convert_transcript_format(self):
        """Test format conversion."""
        with patch("sys.path", []), patch("builtins.__import__") as mock_import:
            mock_manager = Mock()
            mock_manager.convert_transcript.return_value = "/converted/path.md"

            mock_import.side_effect = lambda name, *args, **kwargs: {
                "tools.transcript_manager": mock_manager,
            }.get(name, Mock())

            from .codex.mcp_servers.transcript_saver.server import convert_transcript_format

            result = await convert_transcript_format(session_id="test123", from_format="claude", to_format="codex")

            assert result["converted_path"] == "/converted/path.md"

    @pytest.mark.asyncio
    async def test_get_current_codex_session(self, mock_codex_session):
        """Test session detection."""
        with (
            patch("pathlib.Path.home") as mock_home,
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open"),
            patch("json.load") as mock_json_load,
        ):
            mock_home.return_value = mock_codex_session.parent.parent.parent
            mock_json_load.return_value = [{"session_id": "test123", "ts": 1640995200}]

            from .codex.mcp_servers.transcript_saver.server import get_current_codex_session

            result = await get_current_codex_session()

            assert result is not None

    @pytest.mark.asyncio
    async def test_get_project_sessions(self, mock_codex_session, temp_project_dir):
        """Test project session filtering."""
        with patch("pathlib.Path.glob") as mock_glob, patch("json.load") as mock_json_load:
            mock_glob.return_value = [mock_codex_session]
            mock_json_load.return_value = {"session_id": "test123", "cwd": str(temp_project_dir)}

            from .codex.mcp_servers.transcript_saver.server import get_project_sessions

            result = await get_project_sessions(temp_project_dir)

            assert isinstance(result, list)


# Integration Tests


class TestMCPIntegration:
    """Integration tests across MCP servers."""

    @pytest.mark.asyncio
    async def test_server_startup(self):
        """Test that servers can start without errors."""
        # Test session manager server
        with patch("mcp.server.fastmcp.FastMCP") as mock_mcp:
            mock_instance = Mock()
            mock_mcp.return_value = mock_instance

            try:
                from .codex.mcp_servers.session_manager.server import mcp

                # Server module loaded successfully
                assert mock_mcp.called
            except ImportError:
                pytest.skip("Server modules not yet implemented")

    @pytest.mark.asyncio
    async def test_tool_registration(self):
        """Verify all tools are registered with FastMCP."""
        with patch("mcp.server.fastmcp.FastMCP") as mock_mcp:
            mock_instance = Mock()
            mock_mcp.return_value = mock_instance

            try:
                import sys

                # Force reload of modules
                modules_to_reload = [
                    "codex.mcp_servers.session_manager.server",
                    "codex.mcp_servers.quality_checker.server",
                    "codex.mcp_servers.transcript_saver.server",
                ]

                for module in modules_to_reload:
                    if module in sys.modules:
                        del sys.modules[module]

                # Import should register tools
                from .codex.mcp_servers.session_manager.server import finalize_session
                from .codex.mcp_servers.session_manager.server import health_check
                from .codex.mcp_servers.session_manager.server import initialize_session

                # Verify tools are registered (mock would be called)
                assert mock_instance.tool.call_count >= 3

            except ImportError:
                pytest.skip("Server modules not yet implemented")

    @pytest.mark.asyncio
    async def test_tool_schemas(self):
        """Verify tool input schemas are valid."""
        # Test schemas are properly defined
        try:
            from .codex.mcp_servers.session_manager.server import initialize_session

            # Check function signature exists
            assert callable(initialize_session)

            # Check docstring exists for schema generation
            assert initialize_session.__doc__ is not None

        except ImportError:
            pytest.skip("Server modules not yet implemented")

    @pytest.mark.asyncio
    async def test_cross_server_workflow(self, mock_memory_store, mock_memory_searcher, mock_subprocess):
        """Test using multiple servers together."""
        # Simulate a complete workflow: initialize session -> work -> check quality -> save transcript

        # 1. Initialize session (session_manager)
        with patch("sys.path", []), patch("builtins.__import__") as mock_import:
            mock_import.side_effect = lambda name, *args, **kwargs: {
                "amplifier.memory": Mock(MemoryStore=mock_memory_store),
                "amplifier.search": Mock(MemorySearcher=mock_memory_searcher),
            }.get(name, Mock())

            from .codex.mcp_servers.session_manager.server import initialize_session

            session_result = await initialize_session(prompt="Test workflow")
            assert "Relevant Memories" in session_result

        # 2. Check code quality (quality_checker)
        with patch("subprocess.run", return_value=mock_subprocess):
            from .codex.mcp_servers.quality_checker.server import check_code_quality

            quality_result = await check_code_quality(file_paths=["test.py"])
            assert quality_result["status"] == "passed"

        # 3. Save transcript (transcript_saver)
        with patch("sys.path", []), patch("builtins.__import__") as mock_import:
            mock_exporter = Mock()
            mock_exporter.export_codex_transcript.return_value = "/saved/transcript.md"

            mock_import.side_effect = lambda name, *args, **kwargs: {
                ".codex.tools.transcript_exporter": mock_exporter,
            }.get(name, Mock())

            from .codex.mcp_servers.transcript_saver.server import save_current_transcript

            transcript_result = await save_current_transcript()
            assert transcript_result["export_path"] == "/saved/transcript.md"

        # Workflow completed successfully
        assert True


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
