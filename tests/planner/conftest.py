"""
Pytest configuration and shared fixtures for super-planner tests.

This file provides common fixtures, test data builders, and utilities
for testing the super-planner system following amplifier's modular philosophy.
"""

import asyncio
import json
import tempfile
from collections.abc import Generator
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

# Import mock implementations
from tests.planner.mocks.mock_amplifier_task import MockAmplifierTaskTool
from tests.planner.mocks.mock_amplifier_task import create_mock_task_tool


@dataclass
class TestProject:
    """Test project data structure"""

    id: str
    name: str
    description: str
    tasks: list[dict[str, Any]]
    expected_outcomes: dict[str, Any]


@dataclass
class TestAgent:
    """Test agent data structure"""

    agent_id: str
    name: str
    capabilities: list[str]
    max_concurrent_tasks: int = 3
    failure_rate: float = 0.0


class TestDataBuilder:
    """Builder for creating consistent test data"""

    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.projects: dict[str, TestProject] = {}
        self.agents: dict[str, TestAgent] = {}

    def create_simple_project(self, task_count: int = 8, max_depth: int = 2) -> TestProject:
        """Create a simple test project with specified parameters"""
        project_id = f"test_project_{task_count}_{max_depth}"

        tasks = []
        for i in range(task_count):
            task = {
                "id": f"task_{i:03d}",
                "name": f"Test Task {i + 1}",
                "description": f"Description for task {i + 1}",
                "parent_id": f"task_{(i - 1) // 2:03d}" if i > 0 and i <= max_depth else None,
                "status": "NOT_STARTED",
                "priority": "medium",
                "estimated_effort": 5 + (i % 8),
                "capabilities_required": ["python"] if i % 2 == 0 else ["typescript"],
                "dependencies": [f"task_{i - 1:03d}"] if i > 0 and i % 3 == 0 else [],
                "metadata": {"component": f"component_{i % 3}", "type": "implementation"},
            }
            tasks.append(task)

        project = TestProject(
            id=project_id,
            name=f"Test Project {task_count} Tasks",
            description=f"Test project with {task_count} tasks and {max_depth} levels",
            tasks=tasks,
            expected_outcomes={
                "total_tasks": task_count,
                "max_depth": max_depth,
                "total_effort": sum(t["estimated_effort"] for t in tasks),
            },
        )

        self.projects[project_id] = project
        return project

    def create_complex_project(self, service_count: int = 8, tasks_per_service: int = 20) -> TestProject:
        """Create a complex microservices-style project"""
        project_id = f"complex_project_{service_count}_{tasks_per_service}"
        tasks = []

        services = [f"service_{i}" for i in range(service_count)]
        capabilities_map = {
            0: ["python", "fastapi"],
            1: ["typescript", "react"],
            2: ["python", "database"],
            3: ["devops", "kubernetes"],
            4: ["python", "analytics"],
            5: ["security", "oauth"],
            6: ["mobile", "react-native"],
            7: ["qa", "testing"],
        }

        task_id = 0
        for service_idx, service in enumerate(services):
            # Create service epic
            epic_task = {
                "id": f"epic_{service_idx:03d}",
                "name": f"{service.title()} Service",
                "description": f"Complete {service} implementation",
                "parent_id": None,
                "status": "NOT_STARTED",
                "priority": "high" if service_idx < 3 else "medium",
                "estimated_effort": tasks_per_service * 2,
                "capabilities_required": capabilities_map.get(service_idx, ["python"]),
                "dependencies": [f"epic_{i:03d}" for i in range(service_idx) if i % 3 == 0],
                "metadata": {"service": service, "type": "epic"},
            }
            tasks.append(epic_task)
            task_id += 1

            # Create implementation tasks for this service
            for task_idx in range(tasks_per_service):
                impl_task = {
                    "id": f"task_{task_id:03d}",
                    "name": f"{service} Feature {task_idx + 1}",
                    "description": f"Implement feature {task_idx + 1} for {service}",
                    "parent_id": f"epic_{service_idx:03d}",
                    "status": "NOT_STARTED",
                    "priority": "medium",
                    "estimated_effort": 3 + (task_idx % 5),
                    "capabilities_required": capabilities_map.get(service_idx, ["python"]),
                    "dependencies": [f"task_{task_id - 1:03d}"] if task_idx > 0 and task_idx % 4 == 0 else [],
                    "metadata": {"service": service, "type": "implementation"},
                }
                tasks.append(impl_task)
                task_id += 1

        total_tasks = len(tasks)
        project = TestProject(
            id=project_id,
            name=f"Complex Project - {service_count} Services",
            description=f"Complex project with {service_count} services and {total_tasks} tasks",
            tasks=tasks,
            expected_outcomes={
                "total_tasks": total_tasks,
                "service_count": service_count,
                "max_depth": 2,
                "total_effort": sum(t["estimated_effort"] for t in tasks),
                "parallel_branches": service_count,
            },
        )

        self.projects[project_id] = project
        return project

    def create_test_agents(self, count: int = 4) -> list[TestAgent]:
        """Create test agents with different capabilities"""
        agent_types = [
            ("python-dev", ["python", "fastapi", "pytest"]),
            ("typescript-dev", ["typescript", "react", "jest"]),
            ("devops", ["kubernetes", "docker", "terraform"]),
            ("qa", ["testing", "selenium", "performance"]),
            ("data", ["python", "analytics", "sql"]),
            ("security", ["security", "oauth", "compliance"]),
            ("mobile", ["react-native", "mobile", "ios"]),
            ("designer", ["ui-ux", "design", "figma"]),
        ]

        agents = []
        for i in range(count):
            agent_type, capabilities = agent_types[i % len(agent_types)]
            agent = TestAgent(
                agent_id=f"test_agent_{i:03d}",
                name=f"{agent_type}_agent_{i}",
                capabilities=capabilities,
                max_concurrent_tasks=3,
                failure_rate=0.0,
            )
            agents.append(agent)
            self.agents[agent.agent_id] = agent

        return agents

    def save_project_to_file(self, project: TestProject) -> Path:
        """Save project data to JSON file for testing"""
        project_file = self.temp_dir / f"{project.id}.json"

        project_data = {
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "created": datetime.now(UTC).isoformat(),
                "status": "NOT_STARTED",
            },
            "tasks": project.tasks,
            "expected_outcomes": project.expected_outcomes,
        }

        with open(project_file, "w") as f:
            json.dump(project_data, f, indent=2)

        return project_file


# Pytest fixtures
@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test operations"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def git_repo(temp_dir: Path) -> Generator[Path, None, None]:
    """Create temporary git repository for testing"""
    import subprocess

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=temp_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True, capture_output=True)

    # Create initial commit
    readme = temp_dir / "README.md"
    readme.write_text("# Test Repository\n\nTest repository for super-planner testing.\n")

    subprocess.run(["git", "add", "README.md"], cwd=temp_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, check=True, capture_output=True)

    yield temp_dir


@pytest.fixture
def test_data_builder(temp_dir: Path) -> TestDataBuilder:
    """Create test data builder for generating consistent test data"""
    return TestDataBuilder(temp_dir)


@pytest.fixture
def simple_project(test_data_builder: TestDataBuilder) -> TestProject:
    """Create simple test project"""
    return test_data_builder.create_simple_project(task_count=8, max_depth=2)


@pytest.fixture
def complex_project(test_data_builder: TestDataBuilder) -> TestProject:
    """Create complex test project"""
    return test_data_builder.create_complex_project(service_count=6, tasks_per_service=15)


@pytest.fixture
def test_agents(test_data_builder: TestDataBuilder) -> list[TestAgent]:
    """Create test agents with different capabilities"""
    return test_data_builder.create_test_agents(count=4)


@pytest.fixture
def mock_task_tool(temp_dir: Path) -> MockAmplifierTaskTool:
    """Create mock amplifier Task tool for testing"""
    return create_mock_task_tool(temp_dir)


@pytest.fixture
def mock_llm_service() -> MagicMock:
    """Create mock LLM service for testing task breakdown"""
    mock = MagicMock()

    # Mock task breakdown response
    def mock_breakdown_response(prompt: str) -> dict[str, Any]:
        # Simple mock: create 2-3 subtasks for any task
        task_name = "extracted_from_prompt"
        return {
            "subtasks": [
                {
                    "name": f"{task_name} - Implementation",
                    "description": f"Implement core functionality for {task_name}",
                    "estimated_effort": 5,
                    "capabilities_required": ["python"],
                },
                {
                    "name": f"{task_name} - Testing",
                    "description": f"Write tests for {task_name}",
                    "estimated_effort": 3,
                    "capabilities_required": ["python", "testing"],
                },
                {
                    "name": f"{task_name} - Documentation",
                    "description": f"Document {task_name} implementation",
                    "estimated_effort": 2,
                    "capabilities_required": ["documentation"],
                },
            ]
        }

    mock.break_down_task.side_effect = mock_breakdown_response
    return mock


@pytest.fixture
def mock_git_operations(temp_dir: Path) -> MagicMock:
    """Create mock git operations for testing"""
    mock = MagicMock()

    # Mock successful git operations
    mock.commit.return_value = True
    mock.push.return_value = True
    mock.create_branch.return_value = True
    mock.get_current_branch.return_value = "main"

    # Track calls for verification
    mock.commit_calls = []
    mock.push_calls = []

    def track_commit(*args, **kwargs):
        mock.commit_calls.append({"args": args, "kwargs": kwargs})
        return True

    def track_push(*args, **kwargs):
        mock.push_calls.append({"args": args, "kwargs": kwargs})
        return True

    mock.commit.side_effect = track_commit
    mock.push.side_effect = track_push

    return mock


@pytest.fixture(autouse=True)
def setup_test_environment(temp_dir: Path):
    """Setup common test environment for all tests"""
    # Create directory structure
    (temp_dir / "projects").mkdir(exist_ok=True)
    (temp_dir / "tasks").mkdir(exist_ok=True)
    (temp_dir / "logs").mkdir(exist_ok=True)
    (temp_dir / "temp").mkdir(exist_ok=True)

    # Set environment variables for testing
    import os

    os.environ["PLANNER_DATA_DIR"] = str(temp_dir)
    os.environ["PLANNER_LOG_LEVEL"] = "DEBUG"
    os.environ["PLANNER_TEST_MODE"] = "true"

    yield

    # Cleanup
    for key in ["PLANNER_DATA_DIR", "PLANNER_LOG_LEVEL", "PLANNER_TEST_MODE"]:
        os.environ.pop(key, None)


# Test utilities
class TestAssertions:
    """Custom assertions for super-planner tests"""

    @staticmethod
    def assert_task_state_valid(task: dict[str, Any]):
        """Assert that a task has valid state"""
        required_fields = ["id", "name", "status", "priority"]
        for field in required_fields:
            assert field in task, f"Task missing required field: {field}"

        valid_statuses = ["NOT_STARTED", "ASSIGNED", "IN_PROGRESS", "COMPLETED", "BLOCKED", "CANCELLED"]
        assert task["status"] in valid_statuses, f"Invalid task status: {task['status']}"

        valid_priorities = ["low", "medium", "high", "critical"]
        assert task["priority"] in valid_priorities, f"Invalid task priority: {task['priority']}"

    @staticmethod
    def assert_no_circular_dependencies(tasks: list[dict[str, Any]]):
        """Assert that task dependencies don't form cycles"""
        task_deps = {}
        for task in tasks:
            task_deps[task["id"]] = task.get("dependencies", [])

        def has_cycle(node: str, visited: set, rec_stack: set) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for dep in task_deps.get(node, []):
                if dep not in visited:
                    if has_cycle(dep, visited, rec_stack):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        visited = set()
        rec_stack = set()

        for task_id in task_deps:
            if task_id not in visited:
                assert not has_cycle(task_id, visited, rec_stack), f"Circular dependency detected involving {task_id}"

    @staticmethod
    def assert_load_balanced(assignments: dict[str, list[str]], tolerance: float = 0.2):
        """Assert that task assignments are reasonably load-balanced"""
        if not assignments:
            return

        task_counts = [len(tasks) for tasks in assignments.values()]
        avg_tasks = sum(task_counts) / len(task_counts)
        max_deviation = max(abs(count - avg_tasks) for count in task_counts)

        max_allowed_deviation = avg_tasks * tolerance
        assert max_deviation <= max_allowed_deviation, (
            f"Load imbalance detected: max deviation {max_deviation} > {max_allowed_deviation}"
        )

    @staticmethod
    def assert_dependencies_satisfied(task: dict[str, Any], completed_tasks: set[str]):
        """Assert that all task dependencies are satisfied"""
        dependencies = task.get("dependencies", [])
        unsatisfied = set(dependencies) - completed_tasks

        assert not unsatisfied, f"Task {task['id']} has unsatisfied dependencies: {unsatisfied}"

    @staticmethod
    def assert_git_commit_created(git_mock: MagicMock, message_pattern: str | None = None):
        """Assert that git commit was created with optional message pattern"""
        assert git_mock.commit.called, "Expected git commit to be called"

        if message_pattern:
            commit_calls = git_mock.commit_calls
            assert commit_calls, "No commit calls recorded"

            messages = [call.get("args", [None])[0] or call.get("kwargs", {}).get("message") for call in commit_calls]
            matching = [msg for msg in messages if msg and message_pattern in msg]

            assert matching, f"No commit message matched pattern '{message_pattern}'. Messages: {messages}"


@pytest.fixture
def assert_utils() -> TestAssertions:
    """Provide test assertion utilities"""
    return TestAssertions()


# Performance measurement utilities
class PerformanceTracker:
    """Track performance metrics during tests"""

    def __init__(self):
        self.metrics: dict[str, list[float]] = {}
        self.start_times: dict[str, float] = {}

    def start_timer(self, metric_name: str):
        """Start timing a metric"""
        import time

        self.start_times[metric_name] = time.time()

    def end_timer(self, metric_name: str):
        """End timing and record the metric"""
        import time

        if metric_name not in self.start_times:
            raise ValueError(f"Timer '{metric_name}' was not started")

        elapsed = time.time() - self.start_times[metric_name]
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []

        self.metrics[metric_name].append(elapsed)
        del self.start_times[metric_name]

    def get_average(self, metric_name: str) -> float:
        """Get average time for a metric"""
        if metric_name not in self.metrics:
            return 0.0

        values = self.metrics[metric_name]
        return sum(values) / len(values)

    def assert_performance(self, metric_name: str, max_time: float):
        """Assert that average performance meets requirements"""
        avg_time = self.get_average(metric_name)
        assert avg_time <= max_time, f"Performance requirement failed: {metric_name} avg {avg_time:.2f}s > {max_time}s"


@pytest.fixture
def performance_tracker() -> PerformanceTracker:
    """Provide performance tracking utilities"""
    return PerformanceTracker()


# Async test utilities
@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
