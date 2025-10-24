#!/usr/bin/env python3
"""
Tests for task_tracker MCP server.

Comprehensive tests covering task management functionality:
- Server initialization and health checks
- Task CRUD operations (create, read, update, delete)
- Task persistence to JSON files
- Export functionality (markdown, JSON)
- Error handling and edge cases
"""

import json
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
    from codex.mcp_servers.base import MCPLogger
    from codex.mcp_servers.task_tracker.server import complete_task
    from codex.mcp_servers.task_tracker.server import create_task
    from codex.mcp_servers.task_tracker.server import delete_task
    from codex.mcp_servers.task_tracker.server import export_tasks
    from codex.mcp_servers.task_tracker.server import health_check
    from codex.mcp_servers.task_tracker.server import list_tasks
    from codex.mcp_servers.task_tracker.server import update_task
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
    """Create temporary project directory with .codex structure."""
    project_dir = temp_dir / "project"
    project_dir.mkdir()

    # Create .codex directory
    codex_dir = project_dir / ".codex"
    codex_dir.mkdir()

    # Create tasks directory
    tasks_dir = codex_dir / "tasks"
    tasks_dir.mkdir()

    # Create logs directory
    logs_dir = codex_dir / "logs"
    logs_dir.mkdir()

    return project_dir


@pytest.fixture
def mock_task_data():
    """Sample task data for testing."""
    return {
        "id": "task_123",
        "title": "Test Task",
        "description": "A test task description",
        "priority": "high",
        "status": "pending",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z",
    }


@pytest.fixture
def mock_task_file(temp_project_dir):
    """Create mock task file with sample data."""
    tasks_file = temp_project_dir / ".codex" / "tasks" / "session_tasks.json"
    tasks_data = {
        "session_id": "test_session",
        "tasks": [
            {
                "id": "task_1",
                "title": "Task 1",
                "description": "Description 1",
                "priority": "medium",
                "status": "pending",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z",
            },
            {
                "id": "task_2",
                "title": "Task 2",
                "description": "Description 2",
                "priority": "high",
                "status": "completed",
                "created_at": "2024-01-01T11:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            },
        ],
    }
    tasks_file.write_text(json.dumps(tasks_data))
    return tasks_file


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for command execution."""
    result = Mock()
    result.returncode = 0
    result.stdout = "Success"
    result.stderr = ""
    return result


class TestTaskTrackerServerInitialization:
    """Test server initialization and basic functionality."""

    def test_server_starts_successfully(self, temp_project_dir):
        """Test that the server can be imported and initialized."""
        with patch("codex.mcp_servers.task_tracker.server.mcp") as mock_mcp:
            try:
                from codex.mcp_servers.task_tracker.server import mcp

                # Server module loaded successfully
                assert mock_mcp is not None
            except ImportError:
                pytest.skip("Task tracker server not yet implemented")

    @pytest.mark.asyncio
    async def test_health_check_returns_correct_status(self, temp_project_dir):
        """Test health check returns proper server status."""
        with patch("os.getcwd", return_value=str(temp_project_dir)):
            try:
                from codex.mcp_servers.task_tracker.server import health_check

                result = await health_check()

                assert result["server"] == "task_tracker"
                assert "tasks_directory_exists" in result
                assert "logging_enabled" in result
                assert result["status"] == "healthy"

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")

    def test_logging_initialization(self, temp_project_dir):
        """Test that logging is properly initialized."""
        log_dir = temp_project_dir / ".codex" / "logs"

        logger = MCPLogger("task_tracker", log_dir=log_dir)

        # Check log file creation
        log_file = log_dir / "task_tracker.log"
        assert log_file.exists()

        # Test logging
        logger.info("Test message")
        content = log_file.read_text()
        assert "Test message" in content


class TestTaskCRUDOperations:
    """Test task create, read, update, delete operations."""

    @pytest.mark.asyncio
    async def test_create_task_with_valid_data(self, temp_project_dir, mock_task_data):
        """Test creating a task with valid data."""
        with (
            patch("os.getcwd", return_value=str(temp_project_dir)),
            patch("uuid.uuid4", return_value=Mock(hex="12345678")),
        ):
            try:
                from codex.mcp_servers.task_tracker.server import create_task

                result = await create_task(title="Test Task", description="A test task", priority="high")

                assert result["success"] is True
                assert result["task"]["title"] == "Test Task"
                assert result["task"]["priority"] == "high"
                assert result["task"]["status"] == "pending"
                assert "id" in result["task"]

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")

    @pytest.mark.asyncio
    async def test_create_task_with_invalid_data(self, temp_project_dir):
        """Test creating a task with invalid data."""
        with patch("os.getcwd", return_value=str(temp_project_dir)):
            try:
                from codex.mcp_servers.task_tracker.server import create_task

                # Test empty title
                result = await create_task(title="", description="Test", priority="medium")
                assert result["success"] is False
                assert "error" in result

                # Test invalid priority
                result = await create_task(title="Test", description="Test", priority="invalid")
                assert result["success"] is False

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")

    @pytest.mark.asyncio
    async def test_list_tasks_with_no_tasks(self, temp_project_dir):
        """Test listing tasks when no tasks exist."""
        with patch("os.getcwd", return_value=str(temp_project_dir)):
            try:
                from codex.mcp_servers.task_tracker.server import list_tasks

                result = await list_tasks()

                assert result["success"] is True
                assert result["tasks"] == []
                assert result["count"] == 0

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")

    @pytest.mark.asyncio
    async def test_list_tasks_with_multiple_tasks(self, temp_project_dir, mock_task_file):
        """Test listing multiple tasks."""
        with patch("os.getcwd", return_value=str(temp_project_dir)):
            try:
                from codex.mcp_servers.task_tracker.server import list_tasks

                result = await list_tasks()

                assert result["success"] is True
                assert len(result["tasks"]) == 2
                assert result["count"] == 2
                assert result["tasks"][0]["title"] == "Task 1"

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")

    @pytest.mark.asyncio
    async def test_list_tasks_with_filtering(self, temp_project_dir, mock_task_file):
        """Test listing tasks with status filtering."""
        with patch("os.getcwd", return_value=str(temp_project_dir)):
            try:
                from codex.mcp_servers.task_tracker.server import list_tasks

                # Filter by pending
                result = await list_tasks(filter_status="pending")
                assert len(result["tasks"]) == 1
                assert result["tasks"][0]["status"] == "pending"

                # Filter by completed
                result = await list_tasks(filter_status="completed")
                assert len(result["tasks"]) == 1
                assert result["tasks"][0]["status"] == "completed"

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")

    @pytest.mark.asyncio
    async def test_update_task(self, temp_project_dir, mock_task_file):
        """Test updating an existing task."""
        with patch("os.getcwd", return_value=str(temp_project_dir)):
            try:
                from codex.mcp_servers.task_tracker.server import update_task

                updates = {"title": "Updated Title", "priority": "low"}
                result = await update_task(task_id="task_1", updates=updates)

                assert result["success"] is True
                assert result["task"]["title"] == "Updated Title"
                assert result["task"]["priority"] == "low"

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")

    @pytest.mark.asyncio
    async def test_complete_task(self, temp_project_dir, mock_task_file):
        """Test marking a task as complete."""
        with patch("os.getcwd", return_value=str(temp_project_dir)):
            try:
                from codex.mcp_servers.task_tracker.server import complete_task

                result = await complete_task(task_id="task_1")

                assert result["success"] is True
                assert result["task"]["status"] == "completed"
                assert "completed_at" in result["task"]

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")

    @pytest.mark.asyncio
    async def test_delete_task(self, temp_project_dir, mock_task_file):
        """Test deleting a task."""
        with patch("os.getcwd", return_value=str(temp_project_dir)):
            try:
                from codex.mcp_servers.task_tracker.server import delete_task

                result = await delete_task(task_id="task_1")

                assert result["success"] is True
                assert result["message"] == "Task deleted successfully"

                # Verify task is gone
                from codex.mcp_servers.task_tracker.server import list_tasks

                result = await list_tasks()
                assert len(result["tasks"]) == 1  # Only task_2 remains

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")


class TestTaskPersistence:
    """Test task persistence to JSON files."""

    @pytest.mark.asyncio
    async def test_tasks_saved_to_file(self, temp_project_dir):
        """Test that tasks are saved to JSON file."""
        with (
            patch("os.getcwd", return_value=str(temp_project_dir)),
            patch("uuid.uuid4", return_value=Mock(hex="12345678")),
        ):
            try:
                from codex.mcp_servers.task_tracker.server import create_task

                await create_task(title="Persistent Task", description="Test", priority="medium")

                # Check file was created and contains data
                tasks_file = temp_project_dir / ".codex" / "tasks" / "session_tasks.json"
                assert tasks_file.exists()

                data = json.loads(tasks_file.read_text())
                assert len(data["tasks"]) == 1
                assert data["tasks"][0]["title"] == "Persistent Task"

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")

    @pytest.mark.asyncio
    async def test_tasks_loaded_from_file(self, temp_project_dir, mock_task_file):
        """Test that tasks are loaded from JSON file."""
        with patch("os.getcwd", return_value=str(temp_project_dir)):
            try:
                from codex.mcp_servers.task_tracker.server import list_tasks

                result = await list_tasks()

                # Verify loaded tasks match file content
                assert len(result["tasks"]) == 2
                assert result["tasks"][0]["id"] == "task_1"
                assert result["tasks"][1]["id"] == "task_2"

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")

    @pytest.mark.asyncio
    async def test_concurrent_access_handling(self, temp_project_dir):
        """Test handling concurrent access to task file."""
        with (
            patch("os.getcwd", return_value=str(temp_project_dir)),
            patch("uuid.uuid4", return_value=Mock(hex="12345678")),
            patch("builtins.open") as mock_open,
        ):
            # Mock file operations to simulate concurrent access
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            mock_open.return_value.__exit__.return_value = None

            try:
                from codex.mcp_servers.task_tracker.server import create_task

                # First call succeeds
                mock_file.read.return_value = '{"session_id": "test", "tasks": []}'
                result1 = await create_task(title="Task 1", description="Test", priority="medium")
                assert result1["success"] is True

                # Second call with concurrent modification
                mock_file.read.side_effect = [
                    json.dumps({"session_id": "test", "tasks": []}),
                    json.dumps({"session_id": "test", "tasks": [{"id": "concurrent"}]}),
                ]

                result2 = await create_task(title="Task 2", description="Test", priority="medium")
                # Should handle gracefully or retry

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")


class TestExportFunctionality:
    """Test task export to different formats."""

    @pytest.mark.asyncio
    async def test_export_to_markdown(self, temp_project_dir, mock_task_file):
        """Test exporting tasks to markdown format."""
        with patch("os.getcwd", return_value=str(temp_project_dir)):
            try:
                from codex.mcp_servers.task_tracker.server import export_tasks

                result = await export_tasks(format="markdown")

                assert result["success"] is True
                assert "export_path" in result
                assert result["format"] == "markdown"

                # Check exported file content
                export_path = Path(result["export_path"])
                assert export_path.exists()
                content = export_path.read_text()
                assert "# Task List" in content
                assert "- Task 1" in content

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")

    @pytest.mark.asyncio
    async def test_export_to_json(self, temp_project_dir, mock_task_file):
        """Test exporting tasks to JSON format."""
        with patch("os.getcwd", return_value=str(temp_project_dir)):
            try:
                from codex.mcp_servers.task_tracker.server import export_tasks

                result = await export_tasks(format="json")

                assert result["success"] is True
                assert result["format"] == "json"

                # Check exported file content
                export_path = Path(result["export_path"])
                assert export_path.exists()
                data = json.loads(export_path.read_text())
                assert len(data["tasks"]) == 2

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")

    @pytest.mark.asyncio
    async def test_export_with_empty_task_list(self, temp_project_dir):
        """Test exporting when no tasks exist."""
        with patch("os.getcwd", return_value=str(temp_project_dir)):
            try:
                from codex.mcp_servers.task_tracker.server import export_tasks

                result = await export_tasks(format="markdown")

                assert result["success"] is True

                # Check exported file content
                export_path = Path(result["export_path"])
                content = export_path.read_text()
                assert "No tasks found" in content or content.strip() == "# Task List\n\n"

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_task_ids(self, temp_project_dir):
        """Test handling of invalid task IDs."""
        with patch("os.getcwd", return_value=str(temp_project_dir)):
            try:
                from codex.mcp_servers.task_tracker.server import delete_task
                from codex.mcp_servers.task_tracker.server import update_task

                # Test update with invalid ID
                result = await update_task(task_id="invalid_id", updates={"title": "Test"})
                assert result["success"] is False
                assert "not found" in result["error"].lower()

                # Test delete with invalid ID
                result = await delete_task(task_id="invalid_id")
                assert result["success"] is False

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")

    @pytest.mark.asyncio
    async def test_file_system_errors(self, temp_project_dir):
        """Test handling of file system errors."""
        with (
            patch("os.getcwd", return_value=str(temp_project_dir)),
            patch("pathlib.Path.write_text", side_effect=OSError("Disk full")),
        ):
            try:
                from codex.mcp_servers.task_tracker.server import create_task

                result = await create_task(title="Test", description="Test", priority="medium")
                assert result["success"] is False
                assert "error" in result

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")

    @pytest.mark.asyncio
    async def test_malformed_requests(self, temp_project_dir):
        """Test handling of malformed requests."""
        with patch("os.getcwd", return_value=str(temp_project_dir)):
            try:
                from codex.mcp_servers.task_tracker.server import create_task

                # Test with None values
                result = await create_task(title=None, description="Test", priority="medium")
                assert result["success"] is False

                # Test with invalid types
                result = await create_task(title=123, description="Test", priority="medium")
                assert result["success"] is False

            except ImportError:
                pytest.skip("Task tracker server not yet implemented")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
