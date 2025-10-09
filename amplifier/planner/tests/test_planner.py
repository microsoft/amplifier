"""Comprehensive tests for the Super-Planner system."""

import tempfile
from datetime import UTC
from datetime import datetime
from pathlib import Path

import pytest

from amplifier.planner import Project
from amplifier.planner import Task
from amplifier.planner import TaskState
from amplifier.planner import load_project
from amplifier.planner import save_project


class TestTask:
    """Test Task functionality."""

    def test_task_creation(self):
        """Test basic task creation."""
        task = Task(id="t1", title="Test Task", description="A test task")
        assert task.id == "t1"
        assert task.title == "Test Task"
        assert task.description == "A test task"
        assert task.state == TaskState.PENDING
        assert task.parent_id is None
        assert task.depends_on == []
        assert task.assigned_to is None
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_task_with_all_fields(self):
        """Test task creation with all fields."""
        now = datetime.now()
        task = Task(
            id="t2",
            title="Complex Task",
            description="A complex task",
            state=TaskState.IN_PROGRESS,
            parent_id="t1",
            depends_on=["t0"],
            assigned_to="user1",
            created_at=now,
            updated_at=now,
        )
        assert task.state == TaskState.IN_PROGRESS
        assert task.parent_id == "t1"
        assert task.depends_on == ["t0"]
        assert task.assigned_to == "user1"

    def test_can_start_no_dependencies(self):
        """Test can_start with no dependencies."""
        task = Task(id="t1", title="Independent Task")
        assert task.can_start(set()) is True
        assert task.can_start({"t0"}) is True

    def test_can_start_with_dependencies(self):
        """Test can_start with dependencies."""
        task = Task(id="t1", title="Dependent Task", depends_on=["t0", "t2"])
        assert task.can_start(set()) is False
        assert task.can_start({"t0"}) is False
        assert task.can_start({"t0", "t2"}) is True
        assert task.can_start({"t0", "t2", "t3"}) is True

    def test_task_state_values(self):
        """Test all task state values."""
        assert TaskState.PENDING.value == "pending"
        assert TaskState.IN_PROGRESS.value == "in_progress"
        assert TaskState.COMPLETED.value == "completed"
        assert TaskState.BLOCKED.value == "blocked"


class TestProject:
    """Test Project functionality."""

    def test_project_creation(self):
        """Test basic project creation."""
        project = Project(id="p1", name="Test Project")
        assert project.id == "p1"
        assert project.name == "Test Project"
        assert project.tasks == {}
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.updated_at, datetime)

    def test_add_task(self):
        """Test adding tasks to project."""
        project = Project(id="p1", name="Test Project")
        original_updated = project.updated_at

        # Small delay to ensure timestamp difference
        import time

        time.sleep(0.01)

        task1 = Task(id="t1", title="Task 1")
        project.add_task(task1)

        assert "t1" in project.tasks
        assert project.tasks["t1"] == task1
        assert project.updated_at > original_updated

        task2 = Task(id="t2", title="Task 2")
        project.add_task(task2)
        assert len(project.tasks) == 2

    def test_get_roots(self):
        """Test getting root tasks."""
        project = Project(id="p1", name="Test Project")

        # Add root tasks
        root1 = Task(id="r1", title="Root 1")
        root2 = Task(id="r2", title="Root 2")
        project.add_task(root1)
        project.add_task(root2)

        # Add child tasks
        child1 = Task(id="c1", title="Child 1", parent_id="r1")
        child2 = Task(id="c2", title="Child 2", parent_id="r2")
        project.add_task(child1)
        project.add_task(child2)

        roots = project.get_roots()
        assert len(roots) == 2
        assert root1 in roots
        assert root2 in roots
        assert child1 not in roots
        assert child2 not in roots

    def test_get_children(self):
        """Test getting child tasks."""
        project = Project(id="p1", name="Test Project")

        # Add parent task
        parent = Task(id="parent", title="Parent Task")
        project.add_task(parent)

        # Add children
        child1 = Task(id="c1", title="Child 1", parent_id="parent")
        child2 = Task(id="c2", title="Child 2", parent_id="parent")
        child3 = Task(id="c3", title="Child 3", parent_id="other")
        project.add_task(child1)
        project.add_task(child2)
        project.add_task(child3)

        children = project.get_children("parent")
        assert len(children) == 2
        assert child1 in children
        assert child2 in children
        assert child3 not in children

    def test_hierarchical_structure(self):
        """Test complex hierarchical task structure."""
        project = Project(id="p1", name="Hierarchical Project")

        # Create hierarchy:
        # root1
        #   ├── child1
        #   │   └── grandchild1
        #   └── child2
        # root2

        root1 = Task(id="r1", title="Root 1")
        root2 = Task(id="r2", title="Root 2")
        child1 = Task(id="c1", title="Child 1", parent_id="r1")
        child2 = Task(id="c2", title="Child 2", parent_id="r1")
        grandchild1 = Task(id="gc1", title="Grandchild 1", parent_id="c1")

        for task in [root1, root2, child1, child2, grandchild1]:
            project.add_task(task)

        # Test structure
        roots = project.get_roots()
        assert len(roots) == 2

        r1_children = project.get_children("r1")
        assert len(r1_children) == 2
        assert child1 in r1_children
        assert child2 in r1_children

        c1_children = project.get_children("c1")
        assert len(c1_children) == 1
        assert grandchild1 in c1_children

        r2_children = project.get_children("r2")
        assert len(r2_children) == 0


class TestStorage:
    """Test storage operations."""

    @pytest.fixture
    def temp_data_dir(self, monkeypatch):
        """Use temporary directory for data storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Patch the get_project_path to use temp directory
            def mock_get_path(project_id):
                base = tmpdir_path / "data" / "planner" / "projects"
                base.mkdir(parents=True, exist_ok=True)
                return base / f"{project_id}.json"

            monkeypatch.setattr("amplifier.planner.storage.get_project_path", mock_get_path)
            yield tmpdir_path

    def test_save_and_load_simple(self, temp_data_dir):
        """Test saving and loading a simple project."""
        project = Project(id="p1", name="Test Project")
        task = Task(id="t1", title="Test Task", description="Description")
        project.add_task(task)

        # Save project
        save_project(project)

        # Load project
        loaded = load_project("p1")

        assert loaded.id == "p1"
        assert loaded.name == "Test Project"
        assert len(loaded.tasks) == 1
        assert "t1" in loaded.tasks
        assert loaded.tasks["t1"].title == "Test Task"
        assert loaded.tasks["t1"].description == "Description"

    def test_save_and_load_complex(self, temp_data_dir):
        """Test saving and loading project with all task fields."""
        project = Project(id="p2", name="Complex Project")

        # Create tasks with various states and relationships
        task1 = Task(
            id="t1",
            title="Task 1",
            description="First task",
            state=TaskState.COMPLETED,
            assigned_to="user1",
        )

        task2 = Task(
            id="t2",
            title="Task 2",
            description="Second task",
            state=TaskState.IN_PROGRESS,
            parent_id="t1",
            depends_on=["t1"],
            assigned_to="user2",
        )

        task3 = Task(
            id="t3",
            title="Task 3",
            state=TaskState.BLOCKED,
            depends_on=["t1", "t2"],
        )

        project.add_task(task1)
        project.add_task(task2)
        project.add_task(task3)

        # Save and reload
        save_project(project)
        loaded = load_project("p2")

        # Verify all data preserved
        assert len(loaded.tasks) == 3

        # Check task1
        t1 = loaded.tasks["t1"]
        assert t1.title == "Task 1"
        assert t1.state == TaskState.COMPLETED
        assert t1.assigned_to == "user1"

        # Check task2
        t2 = loaded.tasks["t2"]
        assert t2.state == TaskState.IN_PROGRESS
        assert t2.parent_id == "t1"
        assert t2.depends_on == ["t1"]
        assert t2.assigned_to == "user2"

        # Check task3
        t3 = loaded.tasks["t3"]
        assert t3.state == TaskState.BLOCKED
        assert t3.depends_on == ["t1", "t2"]

    def test_round_trip_preserves_timestamps(self, temp_data_dir):
        """Test that timestamps are preserved through save/load."""
        now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

        project = Project(id="p3", name="Timestamp Test", created_at=now, updated_at=now)

        task = Task(
            id="t1",
            title="Task",
            created_at=now,
            updated_at=now,
        )
        project.tasks["t1"] = task  # Add directly to avoid updating timestamp

        save_project(project)
        loaded = load_project("p3")

        assert loaded.created_at == now
        assert loaded.updated_at == now
        assert loaded.tasks["t1"].created_at == now
        assert loaded.tasks["t1"].updated_at == now

    def test_empty_project(self, temp_data_dir):
        """Test saving and loading empty project."""
        project = Project(id="empty", name="Empty Project")
        save_project(project)

        loaded = load_project("empty")
        assert loaded.id == "empty"
        assert loaded.name == "Empty Project"
        assert loaded.tasks == {}

    def test_task_state_enum_serialization(self, temp_data_dir):
        """Test that TaskState enum values are correctly serialized."""
        project = Project(id="p4", name="Enum Test")

        for state in TaskState:
            task = Task(id=state.value, title=f"{state.value} task", state=state)
            project.add_task(task)

        save_project(project)
        loaded = load_project("p4")

        for state in TaskState:
            assert state.value in loaded.tasks
            assert loaded.tasks[state.value].state == state


class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def temp_data_dir(self, monkeypatch):
        """Use temporary directory for data storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            def mock_get_path(project_id):
                base = tmpdir_path / "data" / "planner" / "projects"
                base.mkdir(parents=True, exist_ok=True)
                return base / f"{project_id}.json"

            monkeypatch.setattr("amplifier.planner.storage.get_project_path", mock_get_path)
            yield tmpdir_path

    def test_complete_workflow(self, temp_data_dir):
        """Test a complete project workflow."""
        # Create project
        project = Project(id="workflow", name="Complete Workflow")

        # Add epic (root task)
        epic = Task(
            id="epic1",
            title="Build Feature X",
            description="Complete implementation of Feature X",
            assigned_to="team-lead",
        )
        project.add_task(epic)

        # Add stories under epic
        story1 = Task(
            id="story1",
            title="Design API",
            parent_id="epic1",
            assigned_to="architect",
        )
        story2 = Task(
            id="story2",
            title="Implement Backend",
            parent_id="epic1",
            depends_on=["story1"],
            assigned_to="backend-dev",
        )
        story3 = Task(
            id="story3",
            title="Create UI",
            parent_id="epic1",
            depends_on=["story1"],
            assigned_to="frontend-dev",
        )
        story4 = Task(
            id="story4",
            title="Integration Testing",
            parent_id="epic1",
            depends_on=["story2", "story3"],
            assigned_to="qa",
        )

        for story in [story1, story2, story3, story4]:
            project.add_task(story)

        # Test dependency checking
        completed = set()
        assert story1.can_start(completed) is True  # No dependencies
        assert story2.can_start(completed) is False  # Depends on story1
        assert story3.can_start(completed) is False  # Depends on story1

        # Complete story1
        completed.add("story1")
        story1.state = TaskState.COMPLETED

        assert story2.can_start(completed) is True  # Dependencies met
        assert story3.can_start(completed) is True  # Dependencies met
        assert story4.can_start(completed) is False  # Needs story2 and story3

        # Save and reload
        save_project(project)
        loaded = load_project("workflow")

        # Verify structure preserved
        roots = loaded.get_roots()
        assert len(roots) == 1
        assert roots[0].id == "epic1"

        children = loaded.get_children("epic1")
        assert len(children) == 4
        child_ids = {c.id for c in children}
        assert child_ids == {"story1", "story2", "story3", "story4"}

        # Verify dependencies preserved
        assert loaded.tasks["story4"].depends_on == ["story2", "story3"]
