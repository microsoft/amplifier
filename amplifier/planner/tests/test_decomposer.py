"""Tests for the task decomposer module."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from amplifier.planner.decomposer import ProjectContext
from amplifier.planner.decomposer import decompose_goal
from amplifier.planner.decomposer import decompose_recursively
from amplifier.planner.models import Project
from amplifier.planner.models import Task


class TestDecomposer:
    """Test task decomposition functionality."""

    @pytest.fixture
    def sample_project(self):
        """Create a sample project for testing."""
        return Project(id="test-proj", name="Test Project")

    @pytest.fixture
    def sample_context(self, sample_project):
        """Create a sample project context."""
        return ProjectContext(project=sample_project, max_depth=2, min_tasks=2)

    def test_project_context_creation(self, sample_project):
        """Test ProjectContext dataclass creation."""
        context = ProjectContext(project=sample_project)

        assert context.project == sample_project
        assert context.max_depth == 3  # default
        assert context.min_tasks == 2  # default
        assert context.parent_task is None

    def test_project_context_with_parent(self, sample_project):
        """Test ProjectContext with parent task."""
        parent = Task(id="parent-1", title="Parent Task")
        context = ProjectContext(project=sample_project, parent_task=parent, max_depth=5, min_tasks=3)

        assert context.parent_task == parent
        assert context.max_depth == 5
        assert context.min_tasks == 3

    @pytest.mark.asyncio
    async def test_decompose_goal_validation(self, sample_context):
        """Test goal validation in decompose_goal."""
        # Test empty goal
        with pytest.raises(ValueError, match="Goal cannot be empty"):
            await decompose_goal("", sample_context)

        # Test whitespace-only goal
        with pytest.raises(ValueError, match="Goal cannot be empty"):
            await decompose_goal("   ", sample_context)

    @pytest.mark.asyncio
    async def test_decompose_goal_success(self, sample_context):
        """Test successful goal decomposition with mocked LLM."""
        mock_decomposition = MagicMock()
        mock_decomposition.tasks = [
            {"title": "Task 1", "description": "First task", "depends_on_indices": []},
            {"title": "Task 2", "description": "Second task", "depends_on_indices": [0]},
            {"title": "Task 3", "description": "Third task", "depends_on_indices": [0, 1]},
        ]

        mock_result = MagicMock()
        mock_result.output = mock_decomposition

        with patch("amplifier.planner.decomposer._get_decomposer_agent") as mock_agent:
            agent = AsyncMock()
            agent.run.return_value = mock_result
            mock_agent.return_value = agent

            tasks = await decompose_goal("Build a web application", sample_context)

            assert len(tasks) == 3
            assert all(isinstance(t, Task) for t in tasks)
            assert tasks[0].title == "Task 1"
            assert tasks[1].title == "Task 2"
            assert tasks[2].title == "Task 3"

            # Check dependencies
            assert len(tasks[0].depends_on) == 0
            assert len(tasks[1].depends_on) == 1
            assert tasks[1].depends_on[0] == tasks[0].id
            assert len(tasks[2].depends_on) == 2

    @pytest.mark.asyncio
    async def test_decompose_goal_min_tasks_retry(self, sample_context):
        """Test retry logic when minimum tasks not met."""
        sample_context.min_tasks = 3

        # First response with too few tasks
        mock_decomposition_1 = MagicMock()
        mock_decomposition_1.tasks = [{"title": "Task 1", "description": "Only task"}]

        # Second response with enough tasks
        mock_decomposition_2 = MagicMock()
        mock_decomposition_2.tasks = [
            {"title": "Task 1", "description": "First task"},
            {"title": "Task 2", "description": "Second task"},
            {"title": "Task 3", "description": "Third task"},
        ]

        mock_result_1 = MagicMock()
        mock_result_1.output = mock_decomposition_1
        mock_result_2 = MagicMock()
        mock_result_2.output = mock_decomposition_2

        with patch("amplifier.planner.decomposer._get_decomposer_agent") as mock_agent:
            agent = AsyncMock()
            agent.run.side_effect = [mock_result_1, mock_result_2]
            mock_agent.return_value = agent

            tasks = await decompose_goal("Simple task", sample_context)

            assert len(tasks) == 3
            assert agent.run.call_count == 2  # Should retry once

    @pytest.mark.asyncio
    async def test_decompose_recursively(self, sample_context):
        """Test recursive decomposition with mocked responses."""
        sample_context.max_depth = 2

        # Mock responses for different levels
        level1_decomposition = MagicMock()
        level1_decomposition.tasks = [
            {"title": "Design system", "description": "Design the system"},
            {"title": "Implement backend", "description": "Build backend"},
        ]

        level2_decomposition = MagicMock()
        level2_decomposition.tasks = [
            {"title": "Create database schema", "description": "Design DB"},
            {"title": "Write API endpoints", "description": "Create APIs"},
        ]

        mock_results = [MagicMock(output=level1_decomposition), MagicMock(output=level2_decomposition)]

        with patch("amplifier.planner.decomposer._get_decomposer_agent") as mock_agent:
            agent = AsyncMock()
            agent.run.side_effect = mock_results
            mock_agent.return_value = agent

            with patch("amplifier.planner.decomposer._is_atomic_task") as mock_atomic:
                # Return values for each task check (need enough for all tasks)
                mock_atomic.side_effect = [False, True, True, True]  # First not atomic, rest are

                tasks = await decompose_recursively("Build app", sample_context)

                # Should have tasks from both levels
                assert len(tasks) == 4  # 2 from level 1 + 2 from level 2 of first task

    def test_is_atomic_task(self):
        """Test atomic task detection."""
        from amplifier.planner.decomposer import _is_atomic_task

        # Atomic tasks
        atomic_tasks = [
            Task(id="1", title="Write unit tests"),
            Task(id="2", title="Create file structure"),
            Task(id="3", title="Implement login function"),
            Task(id="4", title="Fix bug in parser"),
            Task(id="5", title="Update configuration"),
            Task(id="6", title="Delete old files"),
            Task(id="7", title="Install dependencies"),
        ]

        for task in atomic_tasks:
            assert _is_atomic_task(task), f"{task.title} should be atomic"

        # Non-atomic tasks
        non_atomic_tasks = [
            Task(id="8", title="Build authentication system"),
            Task(id="9", title="Design user interface"),
            Task(id="10", title="Develop API layer"),
        ]

        for task in non_atomic_tasks:
            assert not _is_atomic_task(task), f"{task.title} should not be atomic"
