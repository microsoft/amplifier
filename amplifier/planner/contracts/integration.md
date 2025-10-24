# Super-Planner Integration Contracts

This document specifies the integration contracts between the super-planner and the amplifier ecosystem, following the "bricks and studs" philosophy.

## Overview

The super-planner integrates with amplifier as a self-contained "brick" with well-defined "studs" (connection points). These contracts ensure the planner can be regenerated internally without breaking external integrations.

## Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Amplifier Ecosystem                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐           │
│  │   CLI    │   │   Task   │   │  CCSDK   │           │
│  │Commands  │   │   Tool   │   │ Toolkit  │           │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘           │
│       │              │              │                   │
│       ▼              ▼              ▼                   │
│  ┌─────────────────────────────────────────┐           │
│  │        Super-Planner Public API         │           │
│  │         (Stable Contract Layer)         │           │
│  └─────────────────────────────────────────┘           │
│                      │                                  │
│  ┌─────────────────────────────────────────┐           │
│  │         Internal Module Contracts       │           │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ │           │
│  │  │ Core │ │Modes │ │Persist│ │Orch. │ │           │
│  │  └──────┘ └──────┘ └──────┘ └──────┘ │           │
│  └─────────────────────────────────────────┘           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 1. CLI Integration Contract

### Make Commands

The planner exposes the following make commands in amplifier's Makefile:

```makefile
# Project Management
planner-new:
	@uv run python -m amplifier.planner new \
		--name "$(NAME)" \
		--goal "$(GOAL)" \
		--output "$(OUTPUT_DIR)"

planner-load:
	@uv run python -m amplifier.planner load \
		--project-id "$(PROJECT_ID)"

planner-status:
	@uv run python -m amplifier.planner status \
		--project-id "$(PROJECT_ID)" \
		--format "$(FORMAT)"  # json, table, summary

# Planning Mode
planner-decompose:
	@uv run python -m amplifier.planner decompose \
		--project-id "$(PROJECT_ID)" \
		--max-depth "$(MAX_DEPTH)" \
		--max-tasks "$(MAX_TASKS)"

planner-refine:
	@uv run python -m amplifier.planner refine \
		--project-id "$(PROJECT_ID)" \
		--feedback "$(FEEDBACK)"

# Working Mode  
planner-assign:
	@uv run python -m amplifier.planner assign \
		--project-id "$(PROJECT_ID)" \
		--strategy "$(STRATEGY)"  # optimal, round_robin, load_balanced

planner-execute:
	@uv run python -m amplifier.planner execute \
		--project-id "$(PROJECT_ID)" \
		--max-concurrent "$(MAX_CONCURRENT)"

planner-monitor:
	@uv run python -m amplifier.planner monitor \
		--project-id "$(PROJECT_ID)" \
		--follow
```

### Python Module Usage

Direct Python integration:

```python
from amplifier.planner import create_planner, load_planner

# Create new planner
planner = await create_planner({
    "persistence_dir": "data/projects",
    "git_enabled": True
})

# Create and decompose project
project = await planner.create_project(
    name="API Redesign",
    goal="Redesign user API following REST principles"
)

tasks = await planner.decompose_goal(project.goal)

# Assign and execute
assignments = await planner.assign_tasks([t.id for t in tasks])
await planner.execute_project(project.id)
```

## 2. Task Tool Integration Contract

### Spawning Sub-Agents

The planner uses amplifier's Task tool to spawn specialized agents:

```python
# Contract for agent spawning
async def spawn_agent(task_id: str, agent_type: str) -> Dict:
    """
    Spawn sub-agent using amplifier's Task tool.
    
    Returns:
        {
            "agent_id": "agent-123",
            "status": "spawning",
            "task_id": "task-456",
            "result_channel": "channel-789"
        }
    """
    
    # Build agent prompt from task
    task = await self.get_task(task_id)
    prompt = self._build_agent_prompt(task)
    
    # Call amplifier's Task tool
    result = await self.amplifier.spawn_task_agent(
        agent_type=agent_type,
        prompt=prompt,
        context={
            "task_id": task_id,
            "project_id": task.project_id,
            "dependencies": task.dependencies,
            "working_directory": self.get_working_dir(task.project_id)
        }
    )
    
    return result
```

### Agent Types Mapping

```python
AGENT_TYPE_MAPPING = {
    "architecture": "zen-architect",
    "implementation": "modular-builder",
    "testing": "test-coverage",
    "debugging": "bug-hunter",
    "refactoring": "refactor-architect",
    "integration": "integration-specialist",
    "database": "database-architect",
    "api": "api-contract-designer"
}
```

## 3. CCSDK Integration Contract

### SessionManager Integration

```python
from amplifier.ccsdk_toolkit import SessionManager, ClaudeSession

class PlannerSession:
    """Integrates with CCSDK SessionManager for LLM operations"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.claude_session = None
    
    async def initialize(self):
        """Initialize Claude session with defensive utilities"""
        self.claude_session = await self.session_manager.create_session(
            model="claude-3-opus-20240229",
            use_defensive=True
        )
    
    async def decompose_with_llm(self, goal: str) -> List[Dict]:
        """Use CCSDK defensive utilities for robust JSON parsing"""
        from amplifier.ccsdk_toolkit.defensive import parse_llm_json
        
        response = await self.claude_session.generate(
            prompt=f"Decompose this goal into tasks: {goal}",
            system_prompt=DECOMPOSITION_PROMPT
        )
        
        # Use defensive JSON parsing
        tasks_data = parse_llm_json(response)
        return tasks_data.get("tasks", [])
```

### Defensive Utilities Usage

```python
from amplifier.ccsdk_toolkit.defensive import (
    parse_llm_json,
    retry_with_feedback,
    isolate_prompt
)

class PlannerLLM:
    """Uses CCSDK defensive utilities"""
    
    async def safe_decompose(self, goal: str) -> List[Task]:
        """Decompose with retry and error recovery"""
        
        # Isolate user content from system prompts
        clean_goal = isolate_prompt(goal)
        
        # Retry with feedback on failure
        result = await retry_with_feedback(
            async_func=self.decompose_goal,
            prompt=clean_goal,
            max_retries=3
        )
        
        # Parse JSON safely
        tasks_data = parse_llm_json(result)
        return self._convert_to_tasks(tasks_data)
```

## 4. Git Integration Contract

### File Structure

```
data/projects/
├── {project_id}/
│   ├── project.json       # Project metadata
│   ├── tasks/
│   │   ├── {task_id}.json # Individual task files
│   │   └── index.json     # Task index
│   ├── assignments/
│   │   └── index.json     # Agent assignments
│   ├── events/
│   │   └── {date}.jsonl   # Event log files
│   └── .git/              # Git repository
```

### Git Operations

```python
class GitPersistence:
    """Git integration for version control"""
    
    async def save_with_commit(self, project_id: str, message: str):
        """Save and commit changes"""
        # Save all JSON with sorted keys
        await self.save_project(project)
        await self.save_all_tasks(tasks)
        
        # Git operations
        await self.run_command(f"git add -A", cwd=project_dir)
        await self.run_command(
            f'git commit -m "{message}"',
            cwd=project_dir
        )
    
    async def create_checkpoint(self, project_id: str) -> str:
        """Create git tag for checkpoint"""
        timestamp = datetime.now().isoformat()
        tag = f"checkpoint-{timestamp}"
        await self.run_command(
            f'git tag {tag}',
            cwd=self.get_project_dir(project_id)
        )
        return tag
```

## 5. Event System Contract

### Event Publication

```python
class EventPublisher:
    """Publishes events for external consumers"""
    
    async def emit(self, event_type: str, data: Dict):
        """Emit event to subscribers"""
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # Write to event log
        await self.append_to_log(event)
        
        # Notify SSE subscribers if configured
        if self.sse_enabled:
            await self.sse_manager.broadcast(event)
```

### Standard Event Types

```python
EVENT_TYPES = {
    # Task events
    "task.created": "New task created",
    "task.updated": "Task updated",
    "task.started": "Task execution started",
    "task.completed": "Task completed successfully",
    "task.failed": "Task execution failed",
    "task.blocked": "Task blocked by dependencies",
    
    # Agent events
    "agent.spawned": "Sub-agent spawned",
    "agent.assigned": "Agent assigned to task",
    "agent.completed": "Agent completed task",
    "agent.failed": "Agent failed",
    
    # Project events
    "project.created": "Project created",
    "project.updated": "Project updated",
    "project.completed": "All tasks completed",
    
    # Planning events
    "planning.started": "Decomposition started",
    "planning.completed": "Decomposition completed",
    "planning.refined": "Plan refined"
}
```

## 6. Extension Points Contract

### Custom Agent Types

```python
class AgentRegistry:
    """Registry for custom agent types"""
    
    def register_agent_type(
        self,
        name: str,
        selector: Callable[[Task], bool],
        spawner: Callable[[Task], Dict]
    ):
        """Register custom agent type"""
        self.custom_agents[name] = {
            "selector": selector,  # Function to match tasks
            "spawner": spawner    # Function to spawn agent
        }
```

### Custom Assignment Strategies

```python
class AssignmentStrategy(Protocol):
    """Protocol for custom assignment strategies"""
    
    async def assign(
        self,
        tasks: List[Task],
        available_agents: List[str]
    ) -> Dict[str, str]:
        """Return task_id -> agent_id mapping"""
        ...

# Register custom strategy
planner.register_strategy("my_strategy", MyCustomStrategy())
```

### Custom Persistence Backends

```python
class PersistenceBackend(Protocol):
    """Protocol for custom persistence"""
    
    async def save(self, key: str, data: str) -> None:
        """Save data with key"""
        ...
    
    async def load(self, key: str) -> Optional[str]:
        """Load data by key"""
        ...
    
    async def list(self, prefix: str) -> List[str]:
        """List keys with prefix"""
        ...
```

## 7. Resource Management Contract

### Concurrency Control

```python
class ResourceManager:
    """Manages concurrent agent execution"""
    
    MAX_CONCURRENT_AGENTS = 5
    MAX_MEMORY_PER_AGENT = "1GB"
    MAX_TIME_PER_TASK = 300  # seconds
    
    async def acquire_slot(self, agent_id: str) -> bool:
        """Acquire execution slot for agent"""
        if self.active_count < self.MAX_CONCURRENT_AGENTS:
            self.active_agents[agent_id] = datetime.now()
            return True
        return False
    
    async def release_slot(self, agent_id: str):
        """Release execution slot"""
        self.active_agents.pop(agent_id, None)
```

## 8. Error Handling Contract

### Standard Error Codes

```python
class PlannerError(Exception):
    """Base planner exception"""
    code: str
    message: str
    details: Dict[str, Any]

ERROR_CODES = {
    "PROJECT_NOT_FOUND": "Project does not exist",
    "TASK_NOT_FOUND": "Task does not exist",
    "INVALID_TRANSITION": "Invalid state transition",
    "AGENT_SPAWN_FAILED": "Failed to spawn agent",
    "DEPENDENCY_CYCLE": "Circular dependency detected",
    "RESOURCE_EXHAUSTED": "No available execution slots",
    "PERSISTENCE_ERROR": "Failed to save/load data",
    "GIT_ERROR": "Git operation failed",
    "LLM_ERROR": "LLM generation failed"
}
```

## 9. Configuration Contract

### Configuration Schema

```yaml
# planner.config.yaml
persistence:
  type: file  # file, database, memory
  directory: data/projects
  git_enabled: true
  auto_commit: true

orchestration:
  max_concurrent_agents: 5
  agent_timeout: 300
  retry_failed_tasks: true
  deadlock_timeout: 60

planning:
  max_decomposition_depth: 3
  max_tasks_per_goal: 50
  use_defensive_parsing: true
  
llm:
  model: claude-3-opus-20240229
  temperature: 0.7
  max_retries: 3
  
monitoring:
  emit_events: true
  enable_sse: false
  log_level: info
```

## 10. Testing Contract

### Mock Implementations

```python
class MockAmplifierIntegration:
    """Mock for testing without real amplifier"""
    
    async def spawn_task_agent(self, agent_type: str, prompt: str, context: Dict):
        return {
            "agent_id": f"mock-agent-{uuid.uuid4()}",
            "status": "ready",
            "task_id": context["task_id"]
        }

class MockLLMService:
    """Mock LLM for deterministic testing"""
    
    async def generate(self, prompt: str, **kwargs):
        return '{"tasks": [{"title": "Mock task", "type": "task"}]}'
```

## Contract Stability Guarantees

1. **Public API Stability**: The contracts defined in `contracts/__init__.py` are stable and will not break without major version change

2. **Internal Module Boundaries**: Internal contracts between modules can evolve but must maintain protocol compatibility

3. **Data Format Stability**: JSON serialization formats are stable for git-friendly storage

4. **Event Schema Stability**: Event formats are append-only (new fields okay, removal requires version bump)

5. **Configuration Compatibility**: New config options are optional with defaults, removal requires migration

## Migration Path

When contracts need to evolve:

1. **Minor changes**: Add optional fields, new endpoints, additional event types
2. **Major changes**: Create v2 contracts alongside v1, support both during transition
3. **Deprecation**: Mark old contracts deprecated, maintain for 2 major versions
4. **Migration tools**: Provide automated migration for data format changes

---

This integration contract ensures the super-planner can be regenerated internally while maintaining stable connections to the amplifier ecosystem. The "studs" defined here won't change even as the internal "brick" implementation evolves.
