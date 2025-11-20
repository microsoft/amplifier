"""JSON storage operations for Super-Planner."""

from datetime import datetime
from pathlib import Path

from amplifier.planner.models import Project
from amplifier.planner.models import Task
from amplifier.planner.models import TaskState
from amplifier.utils.file_io import read_json
from amplifier.utils.file_io import write_json


def get_project_path(project_id: str) -> Path:
    """Get the storage path for a project."""
    base = Path("data/planner/projects")
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{project_id}.json"


def save_project(project: Project) -> None:
    """Save project to JSON file."""
    data = {
        "id": project.id,
        "name": project.name,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
        "tasks": {
            task_id: {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "state": task.state.value,
                "parent_id": task.parent_id,
                "depends_on": task.depends_on,
                "assigned_to": task.assigned_to,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }
            for task_id, task in project.tasks.items()
        },
    }
    write_json(data, get_project_path(project.id))


def load_project(project_id: str) -> Project:
    """Load project from JSON file."""
    data = read_json(get_project_path(project_id))

    # Reconstruct tasks with proper TaskState enum
    tasks = {}
    for task_id, task_data in data.get("tasks", {}).items():
        tasks[task_id] = Task(
            id=task_data["id"],
            title=task_data["title"],
            description=task_data["description"],
            state=TaskState(task_data["state"]),
            parent_id=task_data["parent_id"],
            depends_on=task_data["depends_on"],
            assigned_to=task_data["assigned_to"],
            created_at=datetime.fromisoformat(task_data["created_at"]),
            updated_at=datetime.fromisoformat(task_data["updated_at"]),
        )

    return Project(
        id=data["id"],
        name=data["name"],
        tasks=tasks,
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
    )
