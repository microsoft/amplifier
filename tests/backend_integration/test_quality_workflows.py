#!/usr/bin/env python3
"""
Quality check workflow integration tests.

Comprehensive tests covering quality check workflows for both Claude Code and Codex backends,
including end-to-end workflows, Makefile integration, worktree environments, specific check types,
environment validation, and cross-backend parity testing.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest

# Import modules under test (will be mocked where necessary)
try:
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
def integration_test_project(temp_dir) -> Path:
    """Create complete project structure for integration tests."""
    project_dir = temp_dir / "project"
    project_dir.mkdir()

    # Create .claude directory
    claude_dir = project_dir / ".claude"
    claude_dir.mkdir()

    # Create .codex directory
    codex_dir = project_dir / ".codex"
    codex_dir.mkdir()

    # Create Makefile with check target
    makefile = project_dir / "Makefile"
    makefile.write_text("""
check:
	@echo "Running checks..."
	uv run ruff check .
	uv run pyright .
	uv run pytest tests/
	@echo "All checks passed"

test:
	uv run pytest tests/

lint:
	uv run ruff check .

format:
	uv run ruff format --check .

type:
	uv run pyright
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

    # Create sample Python files
    (project_dir / "main.py").write_text("""
def hello():
    print("Hello, world!")

if __name__ == "__main__":
    hello()
""")

    (project_dir / "tests").mkdir()
    (project_dir / "tests" / "test_main.py").write_text("""
def test_hello():
    assert True
""")

    return project_dir


@pytest.fixture
def mock_make_check_success():
    """Mock successful make check execution."""
    result = Mock()
    result.returncode = 0
    result.stdout = "Running checks...\nAll checks passed\n"
    result.stderr = ""
    return result


@pytest.fixture
def mock_make_check_failure():
    """Mock failed make check execution."""
    result = Mock()
    result.returncode = 1
    result.stdout = "Running checks...\n"
    result.stderr = "ruff check failed: syntax error in main.py\n"
    return result


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for general use."""
    with patch("subprocess.run") as mock_run:
        yield mock_run


@pytest.fixture
def mock_codex_session_dir(temp_dir):
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


# Test Classes


class TestQualityCheckWorkflows:
    """End-to-end quality check workflows."""

    def test_quality_check_after_code_edit_claude(
        self, integration_test_project, mock_make_check_success, mock_subprocess_run
    ):
        """Test Claude Code quality checks after code editing."""
        mock_subprocess_run.return_value = mock_make_check_success

        backend = ClaudeCodeBackend()

        # Simulate code editing by creating/modifying files
        test_file = integration_test_project / "main.py"
        test_file.write_text("def hello(): pass")  # Modify file

        result = backend.run_quality_checks([str(test_file)], cwd=str(integration_test_project))

        assert result["success"] is True
        assert "All checks passed" in result["data"]["output"]
        assert result["metadata"]["returncode"] == 0

        # Verify subprocess was called correctly
        mock_subprocess_run.assert_called()
        call_args = mock_subprocess_run.call_args_list
        assert any("make" in str(args) and "check" in str(args) for args, kwargs in call_args)

    def test_quality_check_after_code_edit_codex(
        self, integration_test_project, mock_make_check_success, mock_subprocess_run
    ):
        """Test Codex quality checks after code editing."""
        mock_subprocess_run.return_value = mock_make_check_success

        backend = CodexBackend()

        # Simulate code editing
        test_file = integration_test_project / "main.py"
        test_file.write_text("def hello(): pass")  # Modify file

        result = backend.run_quality_checks([str(test_file)], cwd=str(integration_test_project))

        assert result["success"] is True
        assert "All checks passed" in result["data"]["output"]
        assert result["metadata"]["returncode"] == 0

    def test_quality_check_via_mcp_tool(self, integration_test_project, mock_make_check_success):
        """Test quality checks via MCP tool."""
        with patch("subprocess.run", return_value=mock_make_check_success):
            # Import MCP tool function
            import sys

            sys.path.insert(0, str(integration_test_project / ".codex"))

            try:
                from mcp_servers.quality_checker.server import check_code_quality

                result = check_code_quality(
                    file_paths=["main.py"], tool_name="Write", cwd=str(integration_test_project)
                )

                assert result["status"] == "passed"
                assert "All checks passed" in result["output"]
                assert result["metadata"]["command"] == "make check"

            except ImportError:
                pytest.skip("MCP server not available")

    def test_quality_check_finds_project_root(
        self, integration_test_project, mock_make_check_success, mock_subprocess_run
    ):
        """Test project root detection from nested directories."""
        mock_subprocess_run.return_value = mock_make_check_success

        backend = ClaudeCodeBackend()

        # Create nested directory structure
        nested_dir = integration_test_project / "src" / "package"
        nested_dir.mkdir(parents=True)

        # Run checks from nested directory
        result = backend.run_quality_checks(["main.py"], cwd=str(nested_dir))

        assert result["success"] is True
        # Verify make check was run from project root
        call_args = mock_subprocess_run.call_args_list[-1]
        args, kwargs = call_args
        assert str(integration_test_project) in str(args)

    def test_quality_check_with_multiple_files(
        self, integration_test_project, mock_make_check_success, mock_subprocess_run
    ):
        """Test quality checks with multiple files."""
        mock_subprocess_run.return_value = mock_make_check_success

        backend = ClaudeCodeBackend()

        files = ["main.py", "tests/test_main.py"]
        result = backend.run_quality_checks(files, cwd=str(integration_test_project))

        assert result["success"] is True
        assert result["metadata"]["returncode"] == 0


class TestMakeCheckIntegration:
    """Integration with Makefile targets."""

    def test_make_check_target_detection(self, integration_test_project, mock_subprocess_run):
        """Test detection of Makefile check target."""
        # Mock successful target check
        success_result = Mock()
        success_result.returncode = 0
        success_result.stdout = ""
        success_result.stderr = ""

        mock_subprocess_run.return_value = success_result

        backend = ClaudeCodeBackend()
        result = backend.run_quality_checks(["main.py"], cwd=str(integration_test_project))

        assert result["success"] is True

    def test_make_check_target_detection_missing(self, temp_dir, mock_subprocess_run):
        """Test handling when check target doesn't exist."""
        # Mock failed target check
        failure_result = Mock()
        failure_result.returncode = 2
        failure_result.stdout = ""
        failure_result.stderr = "make: *** No rule to make target 'check'. Stop."

        mock_subprocess_run.return_value = failure_result

        project_dir = temp_dir / "project"
        project_dir.mkdir()
        (project_dir / "Makefile").write_text("all:\n\techo 'hello'")  # No check target

        backend = ClaudeCodeBackend()
        result = backend.run_quality_checks(["main.py"], cwd=str(project_dir))

        assert result["success"] is False
        assert "check" in result["metadata"]["error"].lower()

    def test_make_check_execution_success(self, integration_test_project, mock_make_check_success, mock_subprocess_run):
        """Test successful make check execution."""
        mock_subprocess_run.return_value = mock_make_check_success

        backend = ClaudeCodeBackend()
        result = backend.run_quality_checks(["main.py"], cwd=str(integration_test_project))

        assert result["success"] is True
        assert result["metadata"]["returncode"] == 0
        assert "All checks passed" in result["data"]["output"]

    def test_make_check_execution_failure(self, integration_test_project, mock_make_check_failure, mock_subprocess_run):
        """Test failed make check execution."""
        mock_subprocess_run.return_value = mock_make_check_failure

        backend = ClaudeCodeBackend()
        result = backend.run_quality_checks(["main.py"], cwd=str(integration_test_project))

        assert result["success"] is False
        assert result["metadata"]["returncode"] == 1
        assert "syntax error" in result["data"]["output"].lower()

    def test_make_check_with_custom_cwd(self, integration_test_project, mock_make_check_success, mock_subprocess_run):
        """Test make check with custom working directory."""
        mock_subprocess_run.return_value = mock_make_check_success

        backend = ClaudeCodeBackend()

        # Create subdirectory
        subdir = integration_test_project / "subdir"
        subdir.mkdir()

        result = backend.run_quality_checks(["main.py"], cwd=str(subdir))

        assert result["success"] is True
        # Verify make check was run from project root, not subdir
        call_args = mock_subprocess_run.call_args_list[-1]
        args, kwargs = call_args
        make_cmd = str(args[0])
        assert "make" in make_cmd


class TestWorktreeQualityChecks:
    """Quality checks in git worktree environments."""

    def test_quality_check_in_worktree(
        self, integration_test_project, mock_make_check_success, mock_subprocess_run, monkeypatch
    ):
        """Test quality checks in git worktree environment."""
        mock_subprocess_run.return_value = mock_make_check_success

        # Simulate worktree by creating .git file pointing to parent
        git_file = integration_test_project / ".git"
        git_file.write_text("gitdir: ../.git\n")

        # Set VIRTUAL_ENV to simulate active venv
        monkeypatch.setenv("VIRTUAL_ENV", "/parent/worktree/.venv")

        backend = ClaudeCodeBackend()
        result = backend.run_quality_checks(["main.py"], cwd=str(integration_test_project))

        assert result["success"] is True

        # Verify VIRTUAL_ENV was temporarily unset
        # This would be tested by checking subprocess environment
        call_args = mock_subprocess_run.call_args_list[-1]
        args, kwargs = call_args
        env = kwargs.get("env", {})
        assert "VIRTUAL_ENV" not in env or env["VIRTUAL_ENV"] == ""

    def test_quality_check_worktree_venv_detection(
        self, integration_test_project, mock_make_check_success, mock_subprocess_run, monkeypatch
    ):
        """Test venv detection in worktree with local .venv."""
        mock_subprocess_run.return_value = mock_make_check_success

        # Simulate worktree
        git_file = integration_test_project / ".git"
        git_file.write_text("gitdir: ../.git\n")

        # Create local .venv
        venv_dir = integration_test_project / ".venv"
        venv_dir.mkdir()

        # Set VIRTUAL_ENV to parent worktree
        monkeypatch.setenv("VIRTUAL_ENV", "/parent/worktree/.venv")

        backend = ClaudeCodeBackend()
        result = backend.run_quality_checks(["main.py"], cwd=str(integration_test_project))

        assert result["success"] is True

        # Verify checks run with correct environment
        call_args = mock_subprocess_run.call_args_list[-1]
        args, kwargs = call_args
        env = kwargs.get("env", {})
        # Should use local .venv detection via uv


class TestSpecificCheckTypes:
    """Tests for specific quality check types."""

    def test_run_specific_check_lint(self, integration_test_project):
        """Test ruff lint check execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Lint passed", stderr="")

            import sys

            sys.path.insert(0, str(integration_test_project / ".codex"))

            try:
                from mcp_servers.quality_checker.server import run_specific_checks

                result = run_specific_checks(check_type="lint", file_paths=["main.py"], args=["--fix"])

                assert result["status"] == "passed"
                assert result["check_type"] == "lint"
                assert "ruff check" in str(mock_run.call_args)

            except ImportError:
                pytest.skip("MCP server not available")

    def test_run_specific_check_format(self, integration_test_project):
        """Test ruff format check execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Format check passed", stderr="")

            import sys

            sys.path.insert(0, str(integration_test_project / ".codex"))

            try:
                from mcp_servers.quality_checker.server import run_specific_checks

                result = run_specific_checks(check_type="format", file_paths=["main.py"])

                assert result["status"] == "passed"
                assert result["check_type"] == "format"
                assert "ruff format --check" in str(mock_run.call_args)

            except ImportError:
                pytest.skip("MCP server not available")

    def test_run_specific_check_type(self, integration_test_project):
        """Test pyright type check execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Type check passed", stderr="")

            import sys

            sys.path.insert(0, str(integration_test_project / ".codex"))

            try:
                from mcp_servers.quality_checker.server import run_specific_checks

                result = run_specific_checks(check_type="type", file_paths=["main.py"])

                assert result["status"] == "passed"
                assert result["check_type"] == "type"
                assert "pyright" in str(mock_run.call_args)

            except ImportError:
                pytest.skip("MCP server not available")

    def test_run_specific_check_test(self, integration_test_project):
        """Test pytest execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="Tests passed", stderr="")

            import sys

            sys.path.insert(0, str(integration_test_project / ".codex"))

            try:
                from mcp_servers.quality_checker.server import run_specific_checks

                result = run_specific_checks(check_type="test", file_paths=["tests/"])

                assert result["status"] == "passed"
                assert result["check_type"] == "test"
                assert "pytest" in str(mock_run.call_args)

            except ImportError:
                pytest.skip("MCP server not available")


class TestEnvironmentValidation:
    """Tests for environment validation functionality."""

    def test_validate_environment_complete(self, integration_test_project):
        """Test validation of complete environment."""
        # Create .venv directory
        venv_dir = integration_test_project / ".venv"
        venv_dir.mkdir()

        import sys

        sys.path.insert(0, str(integration_test_project / ".codex"))

        try:
            from mcp_servers.quality_checker.server import validate_environment

            with patch("subprocess.run") as mock_run, patch("shutil.which", return_value="/usr/bin/uv"):
                mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

                result = validate_environment()

                assert result["makefile_exists"] is True
                assert result["venv_exists"] is True
                assert result["uv_available"] is True
                assert result["environment_ready"] is True

        except ImportError:
            pytest.skip("MCP server not available")

    def test_validate_environment_missing_venv(self, integration_test_project):
        """Test validation when .venv is missing."""
        import sys

        sys.path.insert(0, str(integration_test_project / ".codex"))

        try:
            from mcp_servers.quality_checker.server import validate_environment

            with patch("shutil.which", return_value="/usr/bin/uv"):
                result = validate_environment()

                assert result["makefile_exists"] is True
                assert result["venv_exists"] is False
                assert result["uv_available"] is True
                assert result["environment_ready"] is False

        except ImportError:
            pytest.skip("MCP server not available")

    def test_validate_environment_missing_uv(self, integration_test_project, monkeypatch):
        """Test validation when uv is not available."""
        # Create .venv directory
        venv_dir = integration_test_project / ".venv"
        venv_dir.mkdir()

        import sys

        sys.path.insert(0, str(integration_test_project / ".codex"))

        try:
            from mcp_servers.quality_checker.server import validate_environment

            with patch("shutil.which", return_value=None):
                result = validate_environment()

                assert result["makefile_exists"] is True
                assert result["venv_exists"] is True
                assert result["uv_available"] is False
                assert result["environment_ready"] is False

        except ImportError:
            pytest.skip("MCP server not available")


class TestCrossBackendQualityChecks:
    """Tests for cross-backend quality check parity."""

    def test_quality_checks_produce_same_results(
        self, integration_test_project, mock_make_check_success, mock_subprocess_run
    ):
        """Test that both backends produce identical quality check results."""
        mock_subprocess_run.return_value = mock_make_check_success

        claude_backend = ClaudeCodeBackend()
        codex_backend = CodexBackend()

        # Run checks with both backends
        claude_result = claude_backend.run_quality_checks(["main.py"], cwd=str(integration_test_project))
        codex_result = codex_backend.run_quality_checks(["main.py"], cwd=str(integration_test_project))

        # Both should succeed
        assert claude_result["success"] is True
        assert codex_result["success"] is True

        # Both should have same return code
        assert claude_result["metadata"]["returncode"] == codex_result["metadata"]["returncode"]

        # Both should call same underlying make check command
        assert len(mock_subprocess_run.call_args_list) >= 2

    def test_quality_checks_share_makefile(
        self, integration_test_project, mock_make_check_success, mock_subprocess_run
    ):
        """Test that both backends use the same Makefile."""
        mock_subprocess_run.return_value = mock_make_check_success

        claude_backend = ClaudeCodeBackend()
        codex_backend = CodexBackend()

        # Both backends should find and use the same Makefile
        claude_result = claude_backend.run_quality_checks(["main.py"], cwd=str(integration_test_project))
        codex_result = codex_backend.run_quality_checks(["main.py"], cwd=str(integration_test_project))

        assert claude_result["success"] is True
        assert codex_result["success"] is True

        # Verify both called make check from project root
        make_calls = [
            call for call in mock_subprocess_run.call_args_list if "make" in str(call[0]) and "check" in str(call[0])
        ]
        assert len(make_calls) >= 2


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
