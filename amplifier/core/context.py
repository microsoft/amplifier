"""
Project Context Detection and Management.

Automatically detects project planning context and provides persistent state
management across amplifier invocations.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from amplifier.planner import Project
from amplifier.planner import load_project


@dataclass
class ProjectContext:
    """Amplifier project context with planning integration."""

    project_root: Path
    project_id: str
    project_name: str
    config_file: Path
    planner_project: Project | None = None
    has_planning: bool = False

    @classmethod
    def from_config(cls, config_path: Path) -> "ProjectContext":
        """Create context from .amplifier/project.json config."""
        with open(config_path) as f:
            config = json.load(f)

        project_root = config_path.parent.parent
        context = cls(
            project_root=project_root,
            project_id=config["project_id"],
            project_name=config["project_name"],
            config_file=config_path,
            has_planning=config.get("has_planning", False),
        )

        # Load planner project if planning is enabled
        if context.has_planning:
            import contextlib

            with contextlib.suppress(FileNotFoundError):
                context.planner_project = load_project(context.project_id)

        return context

    def enable_planning(self) -> None:
        """Enable planning for this project."""
        if not self.has_planning:
            self.has_planning = True
            self.save_config()

    def save_config(self) -> None:
        """Save project configuration."""
        config = {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "has_planning": self.has_planning,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)


def detect_project_context(start_dir: Path | None = None) -> ProjectContext | None:
    """
    Detect amplifier project context by looking for .amplifier/project.json.

    Walks up directory tree from start_dir (or cwd) looking for project config.
    Returns None if no project context found.
    """
    if start_dir is None:
        start_dir = Path.cwd()

    # Walk up directory tree looking for .amplifier/project.json
    current = Path(start_dir).absolute()

    while current != current.parent:  # Not at filesystem root
        config_file = current / ".amplifier" / "project.json"
        if config_file.exists():
            try:
                return ProjectContext.from_config(config_file)
            except (json.JSONDecodeError, KeyError, OSError):
                # Invalid config, continue searching up
                pass
        current = current.parent

    return None


def create_project_context(
    project_name: str, project_root: Path | None = None, enable_planning: bool = True
) -> ProjectContext:
    """Create new amplifier project context."""
    if project_root is None:
        project_root = Path.cwd()

    # Generate project ID from name and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_id = f"{project_name.lower().replace(' ', '_')}_{timestamp}"

    config_file = project_root / ".amplifier" / "project.json"

    context = ProjectContext(
        project_root=project_root,
        project_id=project_id,
        project_name=project_name,
        config_file=config_file,
        has_planning=enable_planning,
    )

    context.save_config()
    return context
