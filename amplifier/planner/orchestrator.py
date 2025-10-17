"""Task execution orchestrator for the Super-Planner system.

This module coordinates parallel agent execution while respecting task dependencies.
It follows the modular "bricks and studs" philosophy with a clear public contract.

Public Contract:
    orchestrate_execution(project: Project) -> ExecutionResults

    Purpose: Coordinate parallel execution of project tasks via agents

    Input: Project with tasks and dependencies
    Output: ExecutionResults with status, progress, and outcomes

    Behavior:
    - Resolves task dependencies to determine execution order
    - Spawns agents in parallel where dependencies allow
    - Tracks progress and handles failures gracefully
    - Returns comprehensive execution results
"""

import asyncio
import logging
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any

from amplifier.planner.models import Project
from amplifier.planner.models import Task
from amplifier.planner.models import TaskState

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Result from executing a single task."""

    task_id: str
    status: str  # "success", "failed", "skipped"
    output: Any = None
    error: str | None = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    attempts: int = 1


@dataclass
class ExecutionResults:
    """Results from orchestrating project execution."""

    project_id: str
    status: str  # "completed", "partial", "failed"
    task_results: dict[str, TaskResult] = field(default_factory=dict)
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    skipped_tasks: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None

    def add_result(self, result: TaskResult) -> None:
        """Add a task result and update counters."""
        self.task_results[result.task_id] = result

        if result.status == "success":
            self.completed_tasks += 1
        elif result.status == "failed":
            self.failed_tasks += 1
        elif result.status == "skipped":
            self.skipped_tasks += 1

    def finalize(self) -> None:
        """Finalize results and set overall status."""
        self.completed_at = datetime.now()

        if self.failed_tasks == 0 and self.completed_tasks == self.total_tasks:
            self.status = "completed"
        elif self.completed_tasks > 0:
            self.status = "partial"
        else:
            self.status = "failed"


async def orchestrate_execution(project: Project, max_parallel: int = 5, max_retries: int = 2) -> ExecutionResults:
    """Orchestrate parallel execution of project tasks.

    Args:
        project: Project containing tasks to execute
        max_parallel: Maximum number of agents to run in parallel
        max_retries: Maximum retry attempts for failed tasks

    Returns:
        ExecutionResults with comprehensive execution information
    """
    results = ExecutionResults(project_id=project.id, status="in_progress", total_tasks=len(project.tasks))

    if not project.tasks:
        logger.warning(f"Project {project.id} has no tasks to execute")
        results.status = "completed"
        results.finalize()
        return results

    # Track task states
    completed_ids: set[str] = set()
    in_progress_ids: set[str] = set()
    failed_ids: set[str] = set()
    queued_ids: set[str] = set()  # Track what's been queued

    # Create execution queue
    execution_queue = asyncio.Queue()

    # Start with tasks that have no dependencies
    for task in project.tasks.values():
        if task.can_start(completed_ids):
            await execution_queue.put(task)
            queued_ids.add(task.id)

    # Semaphore to limit parallel execution
    semaphore = asyncio.Semaphore(max_parallel)

    async def execute_task(task: Task) -> TaskResult:
        """Execute a single task with retries."""
        result = TaskResult(task_id=task.id, status="failed")

        for attempt in range(1, max_retries + 1):
            try:
                async with semaphore:
                    logger.info(f"Executing task {task.id}: {task.title} (attempt {attempt})")
                    in_progress_ids.add(task.id)

                    # Update task state
                    task.state = TaskState.IN_PROGRESS
                    task.updated_at = datetime.now()

                    # Execute via agent (simplified for now - would integrate with Task tool)
                    output = await _execute_with_agent(task)

                    # Success
                    result.status = "success"
                    result.output = output
                    result.attempts = attempt
                    result.completed_at = datetime.now()

                    task.state = TaskState.COMPLETED
                    task.updated_at = datetime.now()

                    in_progress_ids.discard(task.id)
                    completed_ids.add(task.id)

                    logger.info(f"Task {task.id} completed successfully")
                    break

            except Exception as e:
                logger.error(f"Task {task.id} failed (attempt {attempt}): {e}")
                result.error = str(e)
                result.attempts = attempt

                if attempt == max_retries:
                    result.status = "failed"
                    result.completed_at = datetime.now()

                    task.state = TaskState.BLOCKED
                    task.updated_at = datetime.now()

                    in_progress_ids.discard(task.id)
                    failed_ids.add(task.id)
                else:
                    # Exponential backoff
                    await asyncio.sleep(2**attempt)

        return result

    async def process_queue():
        """Process tasks from the queue."""
        active_tasks = []

        while execution_queue.qsize() > 0 or active_tasks:
            # Start new tasks
            while not execution_queue.empty() and len(active_tasks) < max_parallel:
                try:
                    task = execution_queue.get_nowait()
                    active_tasks.append(asyncio.create_task(execute_task(task)))
                except asyncio.QueueEmpty:
                    break

            # Wait for at least one task to complete
            if active_tasks:
                done, pending = await asyncio.wait(active_tasks, return_when=asyncio.FIRST_COMPLETED)

                # Process completed tasks
                for task_future in done:
                    result = await task_future
                    results.add_result(result)
                    active_tasks.remove(task_future)

                    # Check for newly unblocked tasks only after successful completion
                    if result.status == "success":
                        # Look for tasks that are now ready to run
                        for task_id, task in project.tasks.items():
                            if (
                                task_id not in queued_ids  # Not already queued
                                and task.can_start(completed_ids)
                            ):
                                await execution_queue.put(task)
                                queued_ids.add(task_id)

                # Update active tasks list
                active_tasks = list(pending)

            # Brief pause to avoid busy waiting
            if execution_queue.empty() and active_tasks:
                await asyncio.sleep(0.1)

    # Execute all tasks
    await process_queue()

    # Handle any remaining unexecuted tasks (due to failed dependencies)
    for task_id in project.tasks:
        if task_id not in results.task_results:
            result = TaskResult(
                task_id=task_id, status="skipped", error="Dependencies failed or not met", completed_at=datetime.now()
            )
            results.add_result(result)
            logger.warning(f"Task {task_id} skipped due to unmet dependencies")

    # Finalize results
    results.finalize()

    logger.info(
        f"Orchestration complete for project {project.id}: "
        f"{results.completed_tasks}/{results.total_tasks} completed, "
        f"{results.failed_tasks} failed, {results.skipped_tasks} skipped"
    )

    return results


async def _execute_with_agent(task: Task) -> Any:
    """Execute task with assigned agent.

    This is a simplified placeholder. In production, this would:
    1. Use the Task tool to spawn the appropriate agent
    2. Pass the task description and context
    3. Wait for and return the agent's output

    Args:
        task: Task to execute

    Returns:
        Agent execution output
    """
    # Simulate agent execution
    await asyncio.sleep(0.5)  # Simulate work

    if task.assigned_to:
        logger.debug(f"Would execute with agent: {task.assigned_to}")
        return f"Executed by {task.assigned_to}: {task.title}"
    logger.debug(f"Executing task without specific agent: {task.title}")
    return f"Executed: {task.title}"


# Public exports
__all__ = ["orchestrate_execution", "ExecutionResults", "TaskResult"]
