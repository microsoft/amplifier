"""
Super-Planner API Contracts

This module defines the stable API contracts ("studs") for the super-planner system,
following amplifier's bricks-and-studs philosophy. These contracts enable module
regeneration without breaking external consumers.

The contracts are organized into:
- External APIs: Public interfaces for amplifier ecosystem integration
- Internal contracts: Module boundaries within the planner
- Data exchange formats: Standardized data structures
- Event schemas: Notification and audit trail formats
"""

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import Any
from typing import Optional
from typing import Protocol

# ============================================================================
# CORE DATA MODELS (Stable External Contracts)
# ============================================================================


class TaskStatus(str, Enum):
    """Task lifecycle states"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskType(str, Enum):
    """Task classification"""

    GOAL = "goal"
    TASK = "task"
    SUBTASK = "subtask"


class ProjectStatus(str, Enum):
    """Project lifecycle states"""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AgentType(str, Enum):
    """Available agent types from amplifier ecosystem"""

    ZEN_ARCHITECT = "zen-architect"
    MODULAR_BUILDER = "modular-builder"
    TEST_COVERAGE = "test-coverage"
    BUG_HUNTER = "bug-hunter"
    REFACTOR_ARCHITECT = "refactor-architect"
    INTEGRATION_SPECIALIST = "integration-specialist"
    DATABASE_ARCHITECT = "database-architect"
    API_CONTRACT_DESIGNER = "api-contract-designer"
    CUSTOM = "custom"


@dataclass
class Task:
    """Core task data model - stable external contract"""

    id: str
    project_id: str
    title: str
    description: str
    type: TaskType
    status: TaskStatus

    # Relationships
    parent_id: str | None = None
    dependencies: list[str] = field(default_factory=list)
    subtasks: list[str] = field(default_factory=list)

    # Assignment
    assigned_to: str | None = None
    suggested_agent: AgentType | None = None

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Results and metadata
    result: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    version: int = 1

    def to_json(self) -> str:
        """Serialize to JSON with sorted keys for git-friendly storage"""
        data = {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
            "status": self.status.value,
            "parent_id": self.parent_id,
            "dependencies": sorted(self.dependencies),
            "subtasks": sorted(self.subtasks),
            "assigned_to": self.assigned_to,
            "suggested_agent": self.suggested_agent.value if self.suggested_agent else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "metadata": self.metadata,
            "version": self.version,
        }
        return json.dumps(data, sort_keys=True, indent=2)

    @classmethod
    def from_json(cls, data: str) -> "Task":
        """Deserialize from JSON"""
        obj = json.loads(data)
        return cls(
            id=obj["id"],
            project_id=obj["project_id"],
            title=obj["title"],
            description=obj["description"],
            type=TaskType(obj["type"]),
            status=TaskStatus(obj["status"]),
            parent_id=obj.get("parent_id"),
            dependencies=obj.get("dependencies", []),
            subtasks=obj.get("subtasks", []),
            assigned_to=obj.get("assigned_to"),
            suggested_agent=AgentType(obj["suggested_agent"]) if obj.get("suggested_agent") else None,
            created_at=datetime.fromisoformat(obj["created_at"]),
            updated_at=datetime.fromisoformat(obj["updated_at"]),
            started_at=datetime.fromisoformat(obj["started_at"]) if obj.get("started_at") else None,
            completed_at=datetime.fromisoformat(obj["completed_at"]) if obj.get("completed_at") else None,
            result=obj.get("result"),
            metadata=obj.get("metadata", {}),
            version=obj.get("version", 1),
        )


@dataclass
class Project:
    """Project data model - stable external contract"""

    id: str
    name: str
    description: str
    goal: str
    status: ProjectStatus

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    version: int = 1

    def to_json(self) -> str:
        """Serialize to JSON with sorted keys"""
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "goal": self.goal,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
            "version": self.version,
        }
        return json.dumps(data, sort_keys=True, indent=2)

    @classmethod
    def from_json(cls, data: str) -> "Project":
        """Deserialize from JSON"""
        obj = json.loads(data)
        return cls(
            id=obj["id"],
            name=obj["name"],
            description=obj["description"],
            goal=obj["goal"],
            status=ProjectStatus(obj["status"]),
            created_at=datetime.fromisoformat(obj["created_at"]),
            updated_at=datetime.fromisoformat(obj["updated_at"]),
            completed_at=datetime.fromisoformat(obj["completed_at"]) if obj.get("completed_at") else None,
            metadata=obj.get("metadata", {}),
            version=obj.get("version", 1),
        )


# ============================================================================
# MODULE INTERFACES (Internal Contracts Between Planner Modules)
# ============================================================================


class CoreModule(Protocol):
    """Contract for the core task/project management module"""

    async def create_project(self, name: str, goal: str, description: str = "") -> Project:
        """Create a new project"""
        ...

    async def get_project(self, project_id: str) -> Project | None:
        """Retrieve project by ID"""
        ...

    async def update_project(self, project_id: str, **updates) -> Project:
        """Update project with optimistic locking"""
        ...

    async def create_task(self, project_id: str, title: str, **kwargs) -> Task:
        """Create a new task"""
        ...

    async def get_task(self, task_id: str) -> Task | None:
        """Retrieve task by ID"""
        ...

    async def update_task(self, task_id: str, **updates) -> Task:
        """Update task with optimistic locking"""
        ...

    async def transition_task(self, task_id: str, new_status: TaskStatus, reason: str = "") -> Task:
        """Transition task state with validation"""
        ...

    async def list_tasks(self, project_id: str, **filters) -> list[Task]:
        """List tasks with optional filtering"""
        ...


class PlanningMode(Protocol):
    """Contract for planning mode operations"""

    async def decompose_goal(self, goal: str, context: dict | None = None) -> list[Task]:
        """Decompose high-level goal into tasks using LLM"""
        ...

    async def refine_plan(self, tasks: list[Task], feedback: str) -> list[Task]:
        """Refine task breakdown based on feedback"""
        ...

    async def suggest_dependencies(self, tasks: list[Task]) -> dict[str, list[str]]:
        """Analyze and suggest task dependencies"""
        ...

    async def estimate_effort(self, task: Task) -> str:
        """Estimate task effort (xs, s, m, l, xl)"""
        ...


class WorkingMode(Protocol):
    """Contract for working mode operations"""

    async def assign_tasks(self, task_ids: list[str], strategy: str = "optimal") -> dict[str, str]:
        """Assign tasks to agents based on strategy"""
        ...

    async def spawn_agent(self, task_id: str, agent_type: AgentType) -> str:
        """Spawn sub-agent for task execution"""
        ...

    async def coordinate_agents(self, project_id: str) -> None:
        """Orchestrate multi-agent execution"""
        ...

    async def handle_deadlock(self, blocked_tasks: list[str]) -> None:
        """Resolve dependency deadlocks"""
        ...


class PersistenceLayer(Protocol):
    """Contract for persistence operations"""

    async def save_project(self, project: Project) -> None:
        """Persist project to storage"""
        ...

    async def load_project(self, project_id: str) -> Project | None:
        """Load project from storage"""
        ...

    async def save_task(self, task: Task) -> None:
        """Persist task to storage"""
        ...

    async def load_task(self, task_id: str) -> Task | None:
        """Load task from storage"""
        ...

    async def list_all_tasks(self, project_id: str) -> list[Task]:
        """Load all tasks for a project"""
        ...

    async def create_snapshot(self, project_id: str) -> str:
        """Create git snapshot, return commit hash"""
        ...

    async def restore_snapshot(self, project_id: str, commit_hash: str) -> None:
        """Restore from git snapshot"""
        ...


class EventSystem(Protocol):
    """Contract for event publishing and audit trail"""

    async def emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish event for subscribers"""
        ...

    async def subscribe(self, event_types: list[str]) -> AsyncIterator[dict]:
        """Subscribe to event stream"""
        ...

    async def get_audit_trail(self, entity_id: str) -> list[dict]:
        """Retrieve audit trail for entity"""
        ...


# ============================================================================
# EXTERNAL INTEGRATION CONTRACTS
# ============================================================================


class AmplifierIntegration(Protocol):
    """Contract for integration with amplifier ecosystem"""

    async def spawn_task_agent(self, agent_type: str, prompt: str, context: dict) -> dict:
        """Spawn sub-agent using amplifier's Task tool"""
        ...

    async def get_ccsdk_session(self) -> Any:
        """Get CCSDK SessionManager instance"""
        ...

    async def call_defensive_utility(self, utility: str, **kwargs) -> Any:
        """Call CCSDK defensive utility"""
        ...


class LLMService(Protocol):
    """Contract for LLM service integration"""

    async def generate(self, prompt: str, system_prompt: str = "", **kwargs) -> str:
        """Generate LLM response"""
        ...

    async def parse_json_response(self, response: str) -> dict:
        """Parse JSON from LLM response using defensive utilities"""
        ...


# ============================================================================
# EVENT SCHEMAS
# ============================================================================


@dataclass
class TaskEvent:
    """Standard event format for task changes"""

    event_type: str  # task_created, task_updated, task_completed, etc.
    task_id: str
    project_id: str
    timestamp: datetime
    actor: str | None = None  # User or agent ID
    changes: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps(
            {
                "event_type": self.event_type,
                "task_id": self.task_id,
                "project_id": self.project_id,
                "timestamp": self.timestamp.isoformat(),
                "actor": self.actor,
                "changes": self.changes,
                "metadata": self.metadata,
            },
            sort_keys=True,
        )


@dataclass
class AgentEvent:
    """Standard event format for agent coordination"""

    event_type: str  # agent_spawned, agent_completed, agent_failed
    agent_id: str
    agent_type: str
    task_id: str | None
    timestamp: datetime
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None

    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps(
            {
                "event_type": self.event_type,
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "task_id": self.task_id,
                "timestamp": self.timestamp.isoformat(),
                "status": self.status,
                "result": self.result,
                "error": self.error,
            },
            sort_keys=True,
        )


# ============================================================================
# PUBLIC API EXPORTS (The "Studs" for External Use)
# ============================================================================

__all__ = [
    # Core data models
    "Task",
    "Project",
    "TaskStatus",
    "TaskType",
    "ProjectStatus",
    "AgentType",
    # Module interfaces
    "CoreModule",
    "PlanningMode",
    "WorkingMode",
    "PersistenceLayer",
    "EventSystem",
    # Integration contracts
    "AmplifierIntegration",
    "LLMService",
    # Event schemas
    "TaskEvent",
    "AgentEvent",
]


# ============================================================================
# PYTHON MODULE INTERFACE (For Direct Import)
# ============================================================================


async def create_planner(config: dict[str, Any] | None = None):
    """
    Factory function to create configured planner instance.
    This is the main entry point for Python code using the planner.

    Usage:
        from amplifier.planner import create_planner

        planner = await create_planner({
            "persistence_dir": "/path/to/data",
            "git_enabled": True,
            "max_concurrent_agents": 5
        })

        project = await planner.create_project("My Project", "Build awesome feature")
        tasks = await planner.decompose_goal(project.goal)
    """
    # Implementation will be in the main module
    from amplifier.planner.main import Planner

    return await Planner.create(config or {})


async def load_planner(project_id: str, config: dict[str, Any] | None = None):
    """
    Load existing planner with project.

    Usage:
        planner = await load_planner("project-123")
        tasks = await planner.list_tasks()
    """
    from amplifier.planner.main import Planner

    planner = await Planner.create(config or {})
    await planner.load_project(project_id)
    return planner


# ============================================================================
# CLI INTERFACE CONTRACT
# ============================================================================


class CLICommands:
    """
    Defines the CLI interface for make commands.
    These map to the main entry points in __main__.py
    """

    # Project commands
    PLANNER_NEW = "planner-new"  # Create new project
    PLANNER_LOAD = "planner-load"  # Load existing project
    PLANNER_STATUS = "planner-status"  # Show project status

    # Planning mode
    PLANNER_DECOMPOSE = "planner-decompose"  # Decompose goal into tasks
    PLANNER_REFINE = "planner-refine"  # Refine task breakdown

    # Working mode
    PLANNER_ASSIGN = "planner-assign"  # Assign tasks to agents
    PLANNER_EXECUTE = "planner-execute"  # Start execution
    PLANNER_MONITOR = "planner-monitor"  # Monitor progress

    # Utilities
    PLANNER_EXPORT = "planner-export"  # Export project data
    PLANNER_IMPORT = "planner-import"  # Import project data
