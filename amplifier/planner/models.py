"""Task and Project data models for the Super-Planner system."""

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import Enum


class TaskState(Enum):
    """Task states for workflow management."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


@dataclass
class Task:
    """Task with hierarchical structure and dependencies."""

    id: str
    title: str
    description: str = ""
    state: TaskState = TaskState.PENDING
    parent_id: str | None = None
    depends_on: list[str] = field(default_factory=list)
    assigned_to: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def can_start(self, completed_ids: set[str]) -> bool:
        """Check if task can start based on dependency completion."""
        if not self.depends_on:
            return True
        return all(dep_id in completed_ids for dep_id in self.depends_on)


@dataclass
class Project:
    """Project container for hierarchical tasks."""

    id: str
    name: str
    tasks: dict[str, Task] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_task(self, task: Task) -> None:
        """Add task to project and update timestamp."""
        self.tasks[task.id] = task
        self.updated_at = datetime.now()

    def get_roots(self) -> list[Task]:
        """Get all root tasks (no parent)."""
        return [task for task in self.tasks.values() if task.parent_id is None]

    def get_children(self, parent_id: str) -> list[Task]:
        """Get direct children of a task."""
        return [task for task in self.tasks.values() if task.parent_id == parent_id]
