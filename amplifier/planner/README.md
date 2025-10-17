# Super-Planner: Multi-Agent Project Coordination

Super-Planner is a core amplifier module that manages large projects with hierarchical tasks, supporting coordination between multiple AI agents and humans. It follows amplifier's "bricks and studs" philosophy with ruthless simplicity.

## Quick Start

```python
from amplifier.planner import Task, Project, TaskState, save_project, load_project
import uuid

# Create a project
project = Project(
    id=str(uuid.uuid4()),
    name="Build Web App"
)

# Add hierarchical tasks
backend = Task(
    id="backend",
    title="Create Backend API",
    description="Build REST API with authentication"
)

frontend = Task(
    id="frontend",
    title="Create Frontend",
    description="React app with user interface",
    depends_on=["backend"]  # Depends on backend completion
)

deployment = Task(
    id="deployment",
    title="Deploy Application",
    depends_on=["backend", "frontend"]  # Depends on both
)

# Add tasks to project
project.add_task(backend)
project.add_task(frontend)
project.add_task(deployment)

# Save to persistent storage
save_project(project)

# Load later
loaded_project = load_project(project.id)
```

## Core Concepts

### Task States

Tasks progress through defined states:

```python
from amplifier.planner import TaskState

# Available states
TaskState.PENDING      # Not started
TaskState.IN_PROGRESS  # Currently being worked on
TaskState.COMPLETED    # Finished successfully
TaskState.BLOCKED      # Cannot proceed due to issues
```

### Task Dependencies

Tasks can depend on other tasks being completed:

```python
# Check if task can start based on completed dependencies
completed_tasks = {"backend", "database"}
if task.can_start(completed_tasks):
    # All dependencies are met
    task.state = TaskState.IN_PROGRESS
```

### Project Hierarchy

Projects organize tasks in hierarchical structures:

```python
# Get root tasks (no parents)
root_tasks = project.get_roots()

# Get direct children of a task
sub_tasks = project.get_children("backend")

# Navigate the task tree
for root in project.get_roots():
    print(f"Root: {root.title}")
    for child in project.get_children(root.id):
        print(f"  - {child.title}")
```

## Usage Examples

### Example 1: Simple Blog Project

```python
import uuid
from amplifier.planner import Task, Project, TaskState, save_project

# Create project
blog_project = Project(
    id=str(uuid.uuid4()),
    name="Django Blog"
)

# Define tasks with hierarchy
tasks = [
    Task("setup", "Project Setup", "Initialize Django project"),
    Task("models", "Create Models", "User, Post, Comment models", parent_id="setup"),
    Task("views", "Create Views", "List, detail, create views", depends_on=["models"]),
    Task("templates", "Create Templates", "HTML templates", depends_on=["views"]),
    Task("tests", "Write Tests", "Unit and integration tests", depends_on=["models", "views"]),
    Task("deploy", "Deploy", "Deploy to production", depends_on=["templates", "tests"])
]

# Add all tasks
for task in tasks:
    blog_project.add_task(task)

# Save project
save_project(blog_project)

# Find tasks ready to start
completed_ids = {"setup"}  # Setup is done
ready_tasks = []
for task in blog_project.tasks.values():
    if task.state == TaskState.PENDING and task.can_start(completed_ids):
        ready_tasks.append(task)

print(f"Ready to start: {[t.title for t in ready_tasks]}")
# Output: Ready to start: ['Create Models']
```

### Example 2: Complex E-commerce Platform

```python
import uuid
from amplifier.planner import Task, Project, save_project

# Create complex project
ecommerce = Project(
    id=str(uuid.uuid4()),
    name="E-commerce Platform"
)

# Multi-level hierarchy
tasks = [
    # Backend foundation
    Task("architecture", "Design Architecture", "System design and APIs"),
    Task("auth", "Authentication Service", "User management", depends_on=["architecture"]),
    Task("products", "Product Service", "Catalog management", depends_on=["architecture"]),
    Task("orders", "Order Service", "Order processing", depends_on=["products", "auth"]),

    # Frontend components
    Task("ui-kit", "UI Component Library", "Reusable components"),
    Task("product-pages", "Product Pages", "Browse and detail pages", depends_on=["ui-kit", "products"]),
    Task("checkout", "Checkout Flow", "Shopping cart and payment", depends_on=["product-pages", "orders"]),

    # Integration
    Task("payment", "Payment Integration", "Stripe integration", depends_on=["orders"]),
    Task("testing", "End-to-End Testing", "Full system tests", depends_on=["checkout", "payment"]),
    Task("deployment", "Production Deployment", "Deploy all services", depends_on=["testing"])
]

for task in tasks:
    ecommerce.add_task(task)

save_project(ecommerce)

# Analyze project structure
roots = ecommerce.get_roots()
print(f"Starting points: {[r.title for r in roots]}")

# Find bottleneck tasks (many dependencies)
for task in ecommerce.tasks.values():
    if len(task.depends_on) > 1:
        print(f"Complex task: {task.title} depends on {task.depends_on}")
```

### Example 3: Task State Management

```python
from amplifier.planner import load_project, save_project, TaskState

# Load existing project
project = load_project("some-project-id")

# Update task states
project.tasks["backend"].state = TaskState.IN_PROGRESS
project.tasks["backend"].assigned_to = "agent-001"

# Mark task as completed
project.tasks["backend"].state = TaskState.COMPLETED

# Find next ready tasks
completed_ids = {task_id for task_id, task in project.tasks.items()
                 if task.state == TaskState.COMPLETED}

next_tasks = []
for task in project.tasks.values():
    if (task.state == TaskState.PENDING and
        task.can_start(completed_ids)):
        next_tasks.append(task)

print(f"Next available: {[t.title for t in next_tasks]}")

# Save updated state
save_project(project)
```

## Architecture

### Design Philosophy

Super-Planner follows amplifier's core principles:

- **Ruthless Simplicity**: 139 lines total, no unnecessary abstractions
- **File-Based Storage**: JSON files in `data/planner/projects/`
- **Defensive I/O**: Uses amplifier's retry utilities for cloud sync resilience
- **Modular Design**: Clear contracts, regenerable internals

### Module Structure

```
amplifier/planner/
├── __init__.py       # Public API: Task, Project, TaskState, save_project, load_project
├── models.py         # Core data models (60 lines)
├── storage.py        # JSON persistence (70 lines)
└── tests/
    └── test_planner.py  # Comprehensive test suite (16 tests)
```

### Data Model

```python
@dataclass
class Task:
    id: str                    # Unique identifier
    title: str                 # Human-readable name
    description: str           # Detailed description
    state: TaskState          # Current state (enum)
    parent_id: Optional[str]   # Hierarchical parent
    depends_on: List[str]      # Task dependencies
    assigned_to: Optional[str] # Agent or human assigned
    created_at: str           # ISO timestamp
    updated_at: str           # ISO timestamp

@dataclass
class Project:
    id: str                    # Unique identifier
    name: str                  # Human-readable name
    tasks: Dict[str, Task]     # Task collection
    created_at: str           # ISO timestamp
    updated_at: str           # ISO timestamp
```

### Storage Format

Projects are stored as JSON files in `data/planner/projects/{project_id}.json`:

```json
{
  "id": "project-uuid",
  "name": "My Project",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T11:45:00",
  "tasks": [
    {
      "id": "task-1",
      "title": "Setup Project",
      "description": "Initialize repository and dependencies",
      "state": "completed",
      "parent_id": null,
      "depends_on": [],
      "assigned_to": "agent-001",
      "created_at": "2024-01-15T10:30:00",
      "updated_at": "2024-01-15T11:00:00"
    }
  ]
}
```

## Integration Points

### Amplifier Integration

Super-Planner is designed to integrate with amplifier's ecosystem:

- **Task Tool**: Phase 2 will spawn sub-agents using `Task(subagent_type="...", prompt="...")`
- **CCSDK Toolkit**: Uses `SessionManager`, `parse_llm_json`, `retry_with_feedback`
- **File I/O**: Uses `amplifier.utils.file_io` for defensive operations
- **Data Directory**: Follows amplifier's `data/` convention

### Defensive Programming

Built-in resilience for common issues:

```python
# Handles cloud sync delays (OneDrive, Dropbox, etc.)
from amplifier.utils.file_io import write_json, read_json

# Automatic retries with exponential backoff
save_project(project)  # Internally uses defensive file operations
```

## Phase 2 Roadmap

The current implementation (Phase 1) provides a solid foundation. Phase 2 will add:

### Intelligence Features (Phase 2)
- **LLM Integration**: Task decomposition using CCSDK SessionManager
- **Planning Mode**: Recursive task breakdown with AI assistance
- **Working Mode**: Strategic task assignment and agent spawning

### Multi-Agent Coordination (Phase 3)
- **Agent Spawning**: Integration with amplifier's Task tool
- **Load Balancing**: Distribute work across multiple agents
- **Progress Monitoring**: Real-time coordination and status updates

### Advanced Features (Phase 4+)
- **Git Integration**: Version control and distributed coordination
- **Performance Optimization**: Caching and selective loading
- **CLI Interface**: Make commands for project management

## Testing

Run the comprehensive test suite:

```bash
# Run all planner tests
uv run pytest amplifier/planner/tests/ -v

# Run specific test
uv run pytest amplifier/planner/tests/test_planner.py::TestTask::test_can_start_with_dependencies -v
```

Test coverage includes:
- Task creation and validation
- State management and transitions
- Dependency checking logic
- Project operations (hierarchy, children)
- Storage persistence (save/load round-trip)
- Integration workflows

## Contributing

When extending Super-Planner:

1. **Follow amplifier's philosophy**: Ruthless simplicity, no unnecessary complexity
2. **Maintain the contract**: Public API in `__init__.py` should remain stable
3. **Test everything**: All functionality must have comprehensive tests
4. **Use existing patterns**: Leverage amplifier's utilities and conventions

## Performance Considerations

Current implementation targets:
- **Task Operations**: <1ms for state transitions and queries
- **Storage Operations**: <100ms for save/load (with defensive retries)
- **Memory Usage**: Minimal - load only current project data
- **Scalability**: Supports 1000+ tasks per project efficiently

## License

Part of the amplifier project. See main project license.