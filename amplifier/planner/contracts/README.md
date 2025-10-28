# Super-Planner API Contracts

This directory contains the comprehensive API contracts for the super-planner system, following amplifier's "bricks and studs" philosophy.

## Overview

The contracts defined here represent the stable "studs" (connection points) that enable the super-planner to be regenerated internally without breaking external integrations. These contracts are the promises we make to consumers of the planner API.

## Contract Files

### 1. `__init__.py` - Core Python API Contracts
- **Data Models**: `Task`, `Project`, `TaskStatus`, `ProjectStatus`, `AgentType`
- **Module Protocols**: `CoreModule`, `PlanningMode`, `WorkingMode`, `PersistenceLayer`, `EventSystem`
- **Integration Protocols**: `AmplifierIntegration`, `LLMService`
- **Event Schemas**: `TaskEvent`, `AgentEvent`
- **Factory Functions**: `create_planner()`, `load_planner()`

### 2. `openapi.yaml` - REST API Specification
- Complete OpenAPI 3.0 specification
- RESTful endpoints for projects, tasks, planning, orchestration
- Server-sent events (SSE) for real-time updates
- Standard error response formats
- Request/response schemas

### 3. `integration.md` - Ecosystem Integration
- CLI integration via make commands
- Task tool integration for agent spawning
- CCSDK toolkit integration with defensive utilities
- Git workflow integration
- Event system contracts
- Extension points for customization

### 4. `validation.py` - Contract Validation
- `ContractValidator`: Runtime validation of protocol implementations
- `ContractTest`: Base class for contract-based testing
- `ContractMonitor`: Production monitoring of contract compliance
- Validation utilities for data models, serialization, and API responses

## Design Principles

### 1. Ruthless Simplicity
Every endpoint and method has a single, clear purpose. No unnecessary complexity or premature abstraction.

### 2. Stable Connection Points
The external contracts (public API) remain stable even as internal implementations change. This enables module regeneration without breaking consumers.

### 3. Git-Friendly Persistence
All data serialization uses sorted JSON keys for clean git diffs and version control integration.

### 4. Defensive by Default
Integration with CCSDK defensive utilities for robust LLM interaction and error handling.

## Usage Examples

### Python Module Usage
```python
from amplifier.planner import create_planner

# Create planner with configuration
planner = await create_planner({
    "persistence_dir": "data/projects",
    "git_enabled": True,
    "max_concurrent_agents": 5
})

# Create and plan project
project = await planner.create_project(
    name="API Redesign",
    goal="Redesign user API following REST principles"
)

# Decompose into tasks
tasks = await planner.decompose_goal(project.goal)

# Assign and execute
await planner.assign_tasks([t.id for t in tasks])
await planner.execute_project(project.id)
```

### CLI Usage
```bash
# Create new project
make planner-new NAME="API Redesign" GOAL="Redesign user API"

# Decompose into tasks
make planner-decompose PROJECT_ID="project-123"

# Assign tasks to agents
make planner-assign PROJECT_ID="project-123" STRATEGY="optimal"

# Execute with monitoring
make planner-execute PROJECT_ID="project-123"
make planner-monitor PROJECT_ID="project-123"
```

### REST API Usage
```bash
# Create project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "API Redesign", "goal": "Redesign user API"}'

# Decompose goal
curl -X POST http://localhost:8000/api/v1/planning/decompose \
  -H "Content-Type: application/json" \
  -d '{"goal": "Redesign user API"}'

# Stream events
curl -N http://localhost:8000/api/v1/events/stream?project_id=project-123
```

## Contract Stability Guarantees

### Stable (Won't Break)
- Public API methods in `__init__.py`
- OpenAPI endpoint paths and response schemas
- Core data model fields (`Task`, `Project`)
- Event type names and required fields
- CLI command interfaces

### Evolvable (May Extend)
- Optional parameters and fields (additions okay)
- New endpoints (additions okay)
- New event types (additions okay)
- Internal module implementations (can be regenerated)
- Configuration options (new options with defaults okay)

### Versioned Changes
- Breaking changes require major version bump (v1 -> v2)
- Deprecation notices maintained for 2 major versions
- Migration tools provided for data format changes

## Testing Contracts

### Unit Testing
```python
from amplifier.planner.contracts.validation import ContractTest

class TestPlannerImplementation(ContractTest):
    def test_core_module_contract(self):
        core = MyCoreImplementation()
        self.assert_implements_protocol(core, CoreModule)
    
    def test_task_serialization(self):
        task = create_test_task()
        self.assert_serializable(task, Task)
```

### Runtime Monitoring
```python
from amplifier.planner.contracts.validation import ContractMonitor

monitor = ContractMonitor(logger)
monitor.check_protocol(my_implementation, PlanningMode)
monitor.check_data_model(task_instance, Task)

# Get violation report
report = monitor.get_report()
```

## Extension Points

The planner provides several extension points for customization without modifying core contracts:

1. **Custom Agent Types**: Register new agent types with selection criteria
2. **Assignment Strategies**: Implement custom task assignment algorithms  
3. **Persistence Backends**: Swap file-based storage for database or cloud
4. **Event Handlers**: Subscribe to events for custom workflows
5. **Planning Strategies**: Override decomposition algorithms

## Integration with Amplifier Philosophy

These contracts embody amplifier's core principles:

- **Ruthless Simplicity**: Minimal, focused APIs without over-engineering
- **Bricks and Studs**: Clear module boundaries with stable connection points
- **Regenerability**: Internal modules can be rebuilt without breaking contracts
- **Present-Focus**: Solve current needs, not hypothetical futures
- **Trust in Emergence**: Let complex behavior emerge from simple, well-defined pieces

## Compliance Checklist

When implementing or modifying the planner:

- [ ] All public methods match protocol signatures
- [ ] Data models serialize/deserialize correctly
- [ ] JSON uses sorted keys for git-friendliness
- [ ] API responses match OpenAPI schemas
- [ ] Events include required fields
- [ ] Error codes follow standard format
- [ ] Integration tests pass with mock implementations
- [ ] Contract validation tests pass
- [ ] Documentation updated for any contract changes

## Next Steps

1. Implement core modules following these contracts
2. Create contract tests for each module
3. Set up runtime contract monitoring
4. Build CLI and REST API layers
5. Integrate with amplifier's existing tools

The contracts defined here provide the stable foundation for building a robust, regenerable task planning and orchestration system that fits seamlessly into the amplifier ecosystem.
