"""Task Decomposition Module for Super-Planner

Purpose: Intelligently break down high-level goals into specific, actionable tasks using AI analysis.
This module provides a simple, self-contained interface for decomposing goals into hierarchical tasks.

Contract:
    Input: High-level goal string and project context
    Output: List of actionable Task objects with dependencies
    Behavior: Uses LLM to analyze goals and create structured task breakdowns
    Side Effects: Logs decomposition progress
    Dependencies: PydanticAI for LLM integration

Example:
    >>> from amplifier.planner import Project
    >>> from amplifier.planner.decomposer import decompose_goal, ProjectContext
    >>>
    >>> context = ProjectContext(
    ...     project=Project(id="proj1", name="New Feature"),
    ...     max_depth=3
    ... )
    >>> tasks = await decompose_goal("Build user authentication system", context)
    >>> print(f"Generated {len(tasks)} tasks")
"""

import logging
import uuid
from dataclasses import dataclass

from pydantic import BaseModel
from pydantic import Field
from pydantic_ai import Agent

from amplifier.planner.models import Project
from amplifier.planner.models import Task
from amplifier.planner.models import TaskState

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class ProjectContext:
    """Context for task decomposition within a project."""

    project: Project
    max_depth: int = 3  # Maximum decomposition depth
    min_tasks: int = 2  # Minimum tasks required from decomposition
    parent_task: Task | None = None  # Parent task if decomposing subtasks


class TaskDecomposition(BaseModel):
    """LLM response model for task decomposition."""

    tasks: list[dict] = Field(description="List of tasks with title, description, and dependencies")

    model_config = {
        "json_schema_extra": {
            "example": {
                "tasks": [
                    {
                        "title": "Design database schema",
                        "description": "Create tables for user authentication",
                        "depends_on_indices": [],
                    },
                    {
                        "title": "Implement login endpoint",
                        "description": "Create API endpoint for user login",
                        "depends_on_indices": [0],
                    },
                ]
            }
        }
    }


# Lazy-initialize the decomposition agent
_decomposer_agent = None


def _get_decomposer_agent():
    """Get or create the decomposer agent (lazy initialization)."""
    global _decomposer_agent
    if _decomposer_agent is None:
        _decomposer_agent = Agent(
            "claude-3-5-sonnet-20241022",
            output_type=TaskDecomposition,
            system_prompt=(
                "You are a task decomposition expert. Break down high-level goals into "
                "specific, actionable tasks. Each task should be concrete and achievable. "
                "Identify dependencies between tasks. Focus on practical implementation steps."
            ),
        )
    return _decomposer_agent


async def decompose_goal(goal: str, context: ProjectContext) -> list[Task]:
    """Decompose a high-level goal into actionable tasks.

    This function uses AI to intelligently break down a goal into specific tasks,
    establishing proper dependencies and hierarchical structure.

    Args:
        goal: High-level goal string to decompose
        context: Project context including existing project and constraints

    Returns:
        List of Task objects with proper IDs, descriptions, and dependencies

    Raises:
        ValueError: If goal is empty or decomposition produces too few tasks
        RuntimeError: If LLM decomposition fails

    Example:
        >>> context = ProjectContext(project=project, max_depth=2)
        >>> tasks = await decompose_goal("Add search functionality", context)
        >>> for task in tasks:
        ...     print(f"- {task.title}")
    """
    # Input validation
    if not goal or not goal.strip():
        raise ValueError("Goal cannot be empty")

    logger.info(f"Decomposing goal: {goal[:100]}...")

    # Build prompt with context
    prompt = _build_decomposition_prompt(goal, context)

    try:
        # Get the agent and call LLM for decomposition
        agent = _get_decomposer_agent()
        result = await agent.run(prompt)
        decomposition = result.output

        # Validate minimum tasks requirement
        if len(decomposition.tasks) < context.min_tasks:
            logger.warning(
                f"Decomposition produced only {len(decomposition.tasks)} tasks, minimum is {context.min_tasks}"
            )
            # Try once more with explicit instruction
            enhanced_prompt = (
                f"{prompt}\n\nIMPORTANT: Generate at least {context.min_tasks} distinct, actionable tasks."
            )
            result = await agent.run(enhanced_prompt)
            decomposition = result.output

            if len(decomposition.tasks) < context.min_tasks:
                raise ValueError(f"Could not generate minimum {context.min_tasks} tasks from goal")

        # Convert to Task objects
        tasks = _convert_to_tasks(decomposition, context)

        logger.info(f"Successfully decomposed into {len(tasks)} tasks")
        return tasks

    except Exception as e:
        logger.error(f"Failed to decompose goal: {e}")
        raise RuntimeError(f"Goal decomposition failed: {e}") from e


def _build_decomposition_prompt(goal: str, context: ProjectContext) -> str:
    """Build the decomposition prompt with context."""
    prompt_parts = [
        f"Goal: {goal}",
        f"Project: {context.project.name}",
    ]

    if context.parent_task:
        prompt_parts.append(f"Parent task: {context.parent_task.title}")
        prompt_parts.append("Create subtasks for this parent task.")

    # Add existing tasks context if any
    if context.project.tasks:
        existing_titles = [task.title for task in context.project.tasks.values()][:5]
        prompt_parts.append(f"Existing tasks in project: {', '.join(existing_titles)}")

    prompt_parts.append(
        "\nBreak this down into specific, actionable tasks. "
        "Each task should be concrete and independently achievable. "
        "Identify dependencies between tasks using indices (0-based)."
    )

    return "\n".join(prompt_parts)


def _convert_to_tasks(decomposition: TaskDecomposition, context: ProjectContext) -> list[Task]:
    """Convert LLM decomposition to Task objects with proper IDs and relationships."""
    tasks = []
    task_ids = []  # Track IDs for dependency mapping

    # Generate IDs first
    for _ in decomposition.tasks:
        task_ids.append(str(uuid.uuid4()))

    # Create Task objects
    for i, task_data in enumerate(decomposition.tasks):
        # Map dependency indices to actual task IDs
        dependencies = []
        if "depends_on_indices" in task_data:
            for dep_idx in task_data.get("depends_on_indices", []):
                if 0 <= dep_idx < len(task_ids) and dep_idx != i:
                    dependencies.append(task_ids[dep_idx])

        task = Task(
            id=task_ids[i],
            title=task_data.get("title", f"Task {i + 1}"),
            description=task_data.get("description", ""),
            state=TaskState.PENDING,
            parent_id=context.parent_task.id if context.parent_task else None,
            depends_on=dependencies,
        )

        tasks.append(task)

        logger.debug(f"Created task: {task.title} (deps: {len(dependencies)})")

    return tasks


async def decompose_recursively(goal: str, context: ProjectContext, current_depth: int = 0) -> list[Task]:
    """Recursively decompose a goal into tasks up to max_depth.

    This function decomposes a goal and then recursively decomposes each
    resulting task until reaching the maximum depth or tasks become atomic.

    Args:
        goal: High-level goal to decompose
        context: Project context with constraints
        current_depth: Current recursion depth (internal)

    Returns:
        Flat list of all tasks from all decomposition levels

    Example:
        >>> context = ProjectContext(project=project, max_depth=2)
        >>> all_tasks = await decompose_recursively("Build app", context)
        >>> print(f"Total tasks across all levels: {len(all_tasks)}")
    """
    if current_depth >= context.max_depth:
        logger.debug(f"Reached maximum decomposition depth: {context.max_depth}")
        return []

    # Decompose current goal
    tasks = await decompose_goal(goal, context)
    all_tasks = tasks.copy()

    # Recursively decompose each task
    for task in tasks:
        # Skip tasks that seem atomic or too specific
        if _is_atomic_task(task):
            logger.debug(f"Skipping atomic task: {task.title}")
            continue

        # Create context for subtask decomposition
        sub_context = ProjectContext(
            project=context.project,
            max_depth=context.max_depth,
            min_tasks=2,  # Subtasks can have fewer requirements
            parent_task=task,
        )

        try:
            subtasks = await decompose_recursively(task.title, sub_context, current_depth + 1)
            all_tasks.extend(subtasks)
        except Exception as e:
            logger.warning(f"Could not decompose '{task.title}': {e}")
            # Continue with other tasks

    return all_tasks


def _is_atomic_task(task: Task) -> bool:
    """Determine if a task is atomic and shouldn't be decomposed further."""
    # Simple heuristics for atomic tasks
    atomic_keywords = [
        "write",
        "create file",
        "implement",
        "add test",
        "update",
        "fix",
        "remove",
        "delete",
        "install",
        "configure",
    ]

    title_lower = task.title.lower()
    return any(keyword in title_lower for keyword in atomic_keywords)
