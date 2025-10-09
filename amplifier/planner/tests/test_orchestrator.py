"""Tests for the orchestrator module."""

from datetime import datetime

import pytest

from amplifier.planner.models import Project
from amplifier.planner.models import Task
from amplifier.planner.orchestrator import ExecutionResults
from amplifier.planner.orchestrator import TaskResult
from amplifier.planner.orchestrator import orchestrate_execution


@pytest.mark.asyncio
async def test_orchestrate_empty_project():
    """Test orchestrating an empty project."""
    project = Project(id="test-empty", name="Empty Project")
    results = await orchestrate_execution(project)

    assert results.project_id == "test-empty"
    assert results.status == "completed"
    assert results.total_tasks == 0
    assert results.completed_tasks == 0
    assert results.failed_tasks == 0


@pytest.mark.asyncio
async def test_orchestrate_single_task():
    """Test orchestrating a project with a single task."""
    project = Project(id="test-single", name="Single Task Project")
    task = Task(id="task1", title="First Task", description="Do something")
    project.add_task(task)

    results = await orchestrate_execution(project)

    assert results.project_id == "test-single"
    assert results.status == "completed"
    assert results.total_tasks == 1
    assert results.completed_tasks == 1
    assert results.failed_tasks == 0
    assert "task1" in results.task_results
    assert results.task_results["task1"].status == "success"


@pytest.mark.asyncio
async def test_orchestrate_parallel_tasks():
    """Test orchestrating parallel tasks without dependencies."""
    project = Project(id="test-parallel", name="Parallel Tasks")

    # Add multiple independent tasks
    for i in range(3):
        task = Task(id=f"task{i}", title=f"Task {i}", description=f"Do task {i}")
        project.add_task(task)

    results = await orchestrate_execution(project, max_parallel=2)

    assert results.status == "completed"
    assert results.total_tasks == 3
    assert results.completed_tasks == 3
    assert all(r.status == "success" for r in results.task_results.values())


@pytest.mark.asyncio
async def test_orchestrate_with_dependencies():
    """Test orchestrating tasks with dependencies."""
    project = Project(id="test-deps", name="Dependent Tasks")

    # Create a chain: task1 -> task2 -> task3
    task1 = Task(id="task1", title="First", description="Do first")
    task2 = Task(id="task2", title="Second", description="Do second", depends_on=["task1"])
    task3 = Task(id="task3", title="Third", description="Do third", depends_on=["task2"])

    project.add_task(task1)
    project.add_task(task2)
    project.add_task(task3)

    results = await orchestrate_execution(project)

    assert results.status == "completed"
    assert results.completed_tasks == 3

    # Verify execution order (task1 should complete before task2, etc.)
    task1_result = results.task_results["task1"]
    task2_result = results.task_results["task2"]
    task3_result = results.task_results["task3"]

    assert task1_result.completed_at is not None
    assert task2_result.completed_at is not None
    assert task1_result.completed_at < task2_result.started_at
    assert task2_result.completed_at < task3_result.started_at


@pytest.mark.asyncio
async def test_orchestrate_complex_dependencies():
    """Test orchestrating with complex dependency graph."""
    project = Project(id="test-complex", name="Complex Dependencies")

    # Create a diamond dependency graph:
    #     task1
    #     /   \
    #  task2  task3
    #     \   /
    #     task4

    task1 = Task(id="task1", title="Root", description="Root task")
    task2 = Task(id="task2", title="Left", description="Left branch", depends_on=["task1"])
    task3 = Task(id="task3", title="Right", description="Right branch", depends_on=["task1"])
    task4 = Task(id="task4", title="Join", description="Join task", depends_on=["task2", "task3"])

    project.add_task(task1)
    project.add_task(task2)
    project.add_task(task3)
    project.add_task(task4)

    results = await orchestrate_execution(project, max_parallel=2)

    assert results.status == "completed"
    assert results.completed_tasks == 4

    # Task4 should start after both task2 and task3 complete
    task2_result = results.task_results["task2"]
    task3_result = results.task_results["task3"]
    task4_result = results.task_results["task4"]

    assert task2_result.completed_at is not None
    assert task3_result.completed_at is not None
    assert task2_result.completed_at < task4_result.started_at
    assert task3_result.completed_at < task4_result.started_at


@pytest.mark.asyncio
async def test_task_result_tracking():
    """Test that TaskResult properly tracks execution details."""
    result = TaskResult(task_id="test", status="success")

    assert result.task_id == "test"
    assert result.status == "success"
    assert result.attempts == 1
    assert isinstance(result.started_at, datetime)
    assert result.completed_at is None

    # Update result
    result.completed_at = datetime.now()
    result.output = {"data": "test output"}

    assert result.completed_at is not None
    assert result.output == {"data": "test output"}


def test_execution_results_counters():
    """Test ExecutionResults counter methods."""
    results = ExecutionResults(project_id="test", status="in_progress", total_tasks=5)

    # Add successful task
    results.add_result(TaskResult(task_id="t1", status="success"))
    assert results.completed_tasks == 1
    assert results.failed_tasks == 0
    assert results.skipped_tasks == 0

    # Add failed task
    results.add_result(TaskResult(task_id="t2", status="failed"))
    assert results.completed_tasks == 1
    assert results.failed_tasks == 1
    assert results.skipped_tasks == 0

    # Add skipped task
    results.add_result(TaskResult(task_id="t3", status="skipped"))
    assert results.completed_tasks == 1
    assert results.failed_tasks == 1
    assert results.skipped_tasks == 1

    # Finalize with partial completion
    results.finalize()
    assert results.status == "partial"
    assert results.completed_at is not None


def test_execution_results_finalization():
    """Test ExecutionResults status finalization logic."""
    # All tasks completed
    results = ExecutionResults(project_id="test", status="in_progress", total_tasks=2)
    results.add_result(TaskResult(task_id="t1", status="success"))
    results.add_result(TaskResult(task_id="t2", status="success"))
    results.finalize()
    assert results.status == "completed"

    # Some tasks failed but some completed
    results = ExecutionResults(project_id="test", status="in_progress", total_tasks=3)
    results.add_result(TaskResult(task_id="t1", status="success"))
    results.add_result(TaskResult(task_id="t2", status="failed"))
    results.add_result(TaskResult(task_id="t3", status="skipped"))
    results.finalize()
    assert results.status == "partial"

    # All tasks failed
    results = ExecutionResults(project_id="test", status="in_progress", total_tasks=2)
    results.add_result(TaskResult(task_id="t1", status="failed"))
    results.add_result(TaskResult(task_id="t2", status="skipped"))
    results.finalize()
    assert results.status == "failed"


@pytest.mark.asyncio
async def test_orchestrate_with_assigned_agents():
    """Test orchestrating tasks with assigned agents."""
    project = Project(id="test-agents", name="Agent Assignment Test")

    task1 = Task(id="task1", title="Code Review", assigned_to="code-reviewer")
    task2 = Task(id="task2", title="Bug Fix", assigned_to="bug-fixer", depends_on=["task1"])

    project.add_task(task1)
    project.add_task(task2)

    results = await orchestrate_execution(project)

    assert results.status == "completed"
    assert results.completed_tasks == 2

    # Check that agent assignments were used
    assert "code-reviewer" in results.task_results["task1"].output
    assert "bug-fixer" in results.task_results["task2"].output
