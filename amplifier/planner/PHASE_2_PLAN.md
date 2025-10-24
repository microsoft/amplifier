# Super-Planner Phase 2 Implementation Plan

## Status: Ready to Begin

**Phase 1 Foundation**: ✅ COMPLETED
- Core models and storage (139 lines)
- 16 comprehensive tests passing
- Clean public API following amplifier philosophy

## Phase 2 Architecture: Hybrid CLI Tools

Based on amplifier-cli-architect guidance, Phase 2 will be implemented as CLI tools in `scenarios/planner/` using the hybrid "code for structure, AI for intelligence" pattern.

### Target Structure

```
amplifier/planner/           # Phase 1 foundation (UNCHANGED)
├── models.py               # Core data models
├── storage.py              # Persistence layer
└── tests/

scenarios/planner/           # Phase 2 CLI tools (NEW)
├── __init__.py
├── planner_cli.py          # Main CLI entry point
├── decomposer.py           # Task decomposition with AI
├── strategic_assigner.py   # Agent assignment logic
├── session_wrapper.py      # CCSDK SessionManager integration
├── README.md               # Modeled after @scenarios/blog_writer/
├── HOW_TO_CREATE_YOUR_OWN.md
├── tests/
└── examples/
```

### Implementation Strategy

#### 1. Use CCSDK Toolkit Foundation
- Start with `amplifier/ccsdk_toolkit/templates/tool_template.py`
- Import: `ClaudeSession`, `SessionManager`, `parse_llm_json`
- Use defensive LLM response handling from toolkit

#### 2. Session Persistence Pattern
```python
async def decompose_task(task: Task, storage: Storage):
    session_mgr = SessionManager()
    session = session_mgr.load_or_create(f"planner_{task.id}")

    # Resume from existing decomposition
    subtasks = session.context.get("subtasks", [])

    async with ClaudeSession(SessionOptions(
        system_prompt="You are a task decomposition expert..."
    )) as claude:
        if not subtasks:
            response = await claude.query(f"Decompose: {task.description}")
            subtasks = parse_llm_json(response)
            session.context["subtasks"] = subtasks
            session_mgr.save(session)

    return subtasks
```

#### 3. Agent Spawning Integration
```python
from amplifier.tools import Task as AgentTask

async def spawn_agents(assignments: list):
    """Spawn multiple agents in parallel for assigned tasks"""
    agent_calls = []
    for assignment in assignments:
        agent_calls.append(
            AgentTask.run(
                agent=assignment['agent'],
                prompt=assignment['prompt']
            )
        )
    results = await asyncio.gather(*agent_calls)
    return results
```

### Make Command Integration

Add to main Makefile:
```makefile
planner-create: ## Create new project with AI decomposition
	@echo "Creating project with AI planning..."
	uv run python -m scenarios.planner create $(ARGS)

planner-plan: ## Decompose project tasks recursively
	@echo "Planning project tasks..."
	uv run python -m scenarios.planner plan --project-id=$(PROJECT_ID)

planner-assign: ## Assign tasks to agents strategically
	@echo "Assigning tasks to agents..."
	uv run python -m scenarios.planner assign --project-id=$(PROJECT_ID)

planner-execute: ## Execute assigned tasks via Task tool
	@echo "Executing planned tasks..."
	uv run python -m scenarios.planner execute --project-id=$(PROJECT_ID)
```

### Core Components

#### 1. Task Decomposition (decomposer.py)
- **Purpose**: Use AI to break down high-level tasks into specific subtasks
- **Pattern**: Iterative decomposition with depth limits
- **Integration**: Uses CCSDK SessionManager for resume capability
- **Output**: Creates hierarchical Task objects using Phase 1 models

#### 2. Strategic Assignment (strategic_assigner.py)
- **Purpose**: Analyze task requirements and assign to appropriate agents
- **Pattern**: Complexity analysis + capability matching
- **Integration**: Uses Task tool for agent spawning
- **Output**: Assignment queue with agent specifications

#### 3. Session Management (session_wrapper.py)
- **Purpose**: Wrap CCSDK toolkit for planner-specific workflows
- **Pattern**: Project-level session persistence
- **Integration**: Bridges Phase 1 storage with CCSDK sessions
- **Output**: Resumable planning workflows

### Key Implementation Principles

#### 1. Hybrid Architecture
- **Code handles**: Project structure, task coordination, agent spawning
- **AI handles**: Task understanding, decomposition strategy, assignment logic

#### 2. Incremental Progress
- Save after every major operation
- Support workflow interruption and resume
- Use SessionManager for session state

#### 3. Defensive Programming
- Use `parse_llm_json` for all LLM responses
- Implement retry logic for API failures
- Handle cloud sync issues via existing file_io utilities

#### 4. Integration with Phase 1
- Import Phase 1 models: `from amplifier.planner import Task, Project, save_project, load_project`
- Extend but don't modify existing data models
- Use existing storage layer for persistence

### Development Phases

#### Phase 2a: Basic Decomposition (Week 1)
- CLI interface for project creation
- Simple task decomposition with AI
- Integration with Phase 1 storage

#### Phase 2b: Strategic Assignment (Week 2)
- Task complexity analysis
- Agent capability matching
- Assignment queue generation

#### Phase 2c: Execution Orchestration (Week 3)
- Agent spawning via Task tool
- Progress monitoring
- Status updates to project storage

#### Phase 2d: Full Integration (Week 4)
- End-to-end workflows
- Comprehensive testing
- Documentation completion

### Success Criteria

- Can create projects from natural language descriptions
- Recursively decomposes tasks to actionable granularity
- Strategically assigns tasks based on complexity and agent capabilities
- Spawns multiple agents in parallel via Task tool
- Handles interruption and resume gracefully
- Follows amplifier's simplicity philosophy

### Resources to Reference

- **@scenarios/README.md**: Philosophy for user-facing tools
- **@scenarios/blog_writer/**: THE exemplar for documentation and structure
- **@amplifier/ccsdk_toolkit/DEVELOPER_GUIDE.md**: Complete technical guide
- **@amplifier/ccsdk_toolkit/templates/tool_template.py**: Starting point
- **@DISCOVERIES.md**: File I/O retry patterns and LLM response handling

### Next Steps

1. **Create scenarios/planner/ directory structure**
2. **Copy and customize tool_template.py as planner_cli.py**
3. **Implement basic decomposer.py using CCSDK patterns**
4. **Add make commands to main Makefile**
5. **Create README.md modeled after blog_writer/**

This plan leverages amplifier's hybrid architecture while building on the solid Phase 1 foundation. The result will be a production-ready multi-agent planning system that embodies amplifier's design philosophy.