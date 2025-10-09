# Super-Planner Implementation Working Plan

## Project Context

**Branch**: `feature/super-planner` (currently checked out)
**Location**: `amplifier/planner/` (core library component, not scenarios)
**Philosophy**: Amplifier's "bricks and studs" modular design with ruthless simplicity

### Problem Statement
Build a text and file-based system within amplifier that manages large projects with multiple subtasks, supporting both multiple AI agents and humans working concurrently. The system breaks down tasks recursively, manages state (not started, assigned, in progress, completed), and coordinates strategic task assignment with sub-agent spawning.

### Key Requirements
- **Two Modes**: Planning (recursive AI task breakdown) and Working (strategic assignment + agent spawning)
- **File-Based Persistence**: All data in JSON files with git integration
- **Multi-Agent Coordination**: Multiple amplifier instances working together via Task tool
- **Strategic Assignment**: Analyze complete project plan for optimal task ordering
- **Amplifier Integration**: Uses same LLM calls, tools, and patterns as existing amplifier

### Architecture Overview
```
amplifier/planner/
├── core/           # Task, Project models, business logic
├── modes/          # PlanningMode, WorkingMode implementations
├── persistence/    # File storage + git integration
├── orchestrator/   # Agent spawning + coordination
├── session/        # LLM integration via CCSDK toolkit
└── tests/          # Golden test suite (28 scenarios)
```

### Integration Points
- **Task Tool**: For spawning sub-agents (`Task(subagent_type="zen-architect", prompt="...")`)
- **CCSDK Toolkit**: `SessionManager`, defensive utilities, `parse_llm_json`, `retry_with_feedback`
- **Git**: Auto-commit, recovery points, distributed coordination
- **Makefile**: CLI commands (`make planner-create`, `make planner-plan`, etc.)

### Key Design Decisions Made
1. **Core library in amplifier/** (not scenarios/) - infrastructure component
2. **File-based storage** with git (not database) - follows amplifier patterns
3. **JSON with sorted keys** - git-friendly diffs
4. **Per-project git repos** - isolation and parallel development
5. **Optimistic locking** - version numbers prevent conflicts
6. **Agent spawning via Task tool** - reuses existing amplifier capability
7. **Three-phase implementation** - Foundation → Intelligence → Coordination

### Testing Strategy
- **Spec and Test Forward**: Golden tests define behavior before implementation
- **28 Test Scenarios**: End-to-end workflows, multi-agent coordination, failure recovery
- **60-30-10 Pyramid**: Unit (state transitions) → Integration (mode switching) → E2E (real projects)
- **Sample Projects**: Simple (8 tasks), Complex (22 tasks), Enterprise (1000+ tasks)
- **Performance Targets**: 1000 tasks <30s load, 20 concurrent agents, <100ms state transitions

## Implementation Tasks

### Phase 1: Foundation (Core + Persistence)
**Priority**: P0 - Essential foundation
**Estimated Time**: 8-12 hours
**Dependencies**: None

#### Core Module (`amplifier/planner/core/`)
- [ ] **models.py** - Complete Task, Project, TaskState data models
  - Task model with 20+ fields (id, title, description, state, dependencies, metadata, etc.)
  - Project model with goals, constraints, success_criteria
  - TaskState enum (NOT_STARTED, ASSIGNED, IN_PROGRESS, COMPLETED, BLOCKED, CANCELLED)
  - JSON serialization with sorted keys for git-friendly diffs
  - Validation methods and constraints

- [ ] **task_manager.py** - Task lifecycle management
  - State transition validation with guard conditions
  - Dependency graph operations (add, remove, validate)
  - Cycle detection algorithms
  - Task hierarchy navigation (parents, children, siblings)

- [ ] **project_manager.py** - Project-level operations
  - Project creation and initialization
  - Task tree operations (get_task_tree, get_ready_tasks)
  - Project statistics and health metrics
  - Bulk operations on task collections

#### Persistence Module (`amplifier/planner/persistence/`)
- [ ] **storage.py** - File-based storage with defensive I/O
  - ProjectStorage class with save/load operations
  - Incremental task saves (critical for multi-agent coordination)
  - Use `amplifier.ccsdk_toolkit.defensive` utilities for cloud sync resilience
  - File structure: `projects/{project_id}/project.json`, `tasks/{task_id}.json`
  - Assignment indexes for strategic queries

- [ ] **git_sync.py** - Git integration for persistence
  - GitPersistence class with auto-commit functionality
  - Semantic commit messages from operation batches
  - Recovery point creation and restoration
  - Per-project repository management
  - Conflict detection and resolution

#### Foundation Tests
- [ ] **test_models.py** - Data model validation
  - Task creation, validation, serialization
  - Project initialization and task association
  - State transition validation (all valid/invalid combinations)
  - Dependency cycle detection edge cases

- [ ] **test_storage.py** - File persistence validation
  - Save/load operations with various data scenarios
  - Concurrent access simulation
  - File corruption recovery
  - Cloud sync error simulation (OneDrive/Dropbox issues)

- [ ] **test_git_integration.py** - Git workflow validation
  - Auto-commit functionality
  - Recovery point creation/restoration
  - Conflict resolution scenarios
  - Multi-repository coordination

### Phase 2: Intelligence (Session + Modes)
**Priority**: P0 - Core AI functionality
**Estimated Time**: 10-15 hours
**Dependencies**: Phase 1 complete

#### Session Module (`amplifier/planner/session/`)
- [ ] **planner_session.py** - LLM integration wrapper
  - PlannerSession class wrapping CCSDK SessionManager
  - Task decomposition prompts and response parsing
  - Strategic task analysis (complexity, tool requirements, human vs AI)
  - Integration with `parse_llm_json` for reliable response handling
  - Retry logic with `retry_with_feedback` for API failures

#### Modes Module (`amplifier/planner/modes/`)
- [ ] **base.py** - Mode interface and switching logic
  - PlannerMode abstract base class
  - Mode switching protocols (planning ↔ working)
  - Context preservation across mode changes
  - State validation for mode transitions

- [ ] **planning.py** - AI-driven task decomposition
  - PlanningMode implementation with recursive breakdown
  - LLM prompts for project analysis and task creation
  - Task depth limits and complexity assessment
  - Integration with existing project structure
  - Incremental saves after each decomposition

- [ ] **working.py** - Strategic execution mode
  - WorkingMode implementation with agent coordination
  - Ready task identification (satisfied dependencies)
  - Agent capability matching and task assignment
  - Progress monitoring and state updates
  - New task scheduling as work completes

#### Intelligence Tests
- [ ] **test_session.py** - LLM integration validation
  - Mock LLM responses for deterministic testing
  - Error handling for API failures, timeouts, rate limits
  - Response parsing validation (malformed JSON, unexpected formats)
  - Retry logic verification

- [ ] **test_modes.py** - Mode operation validation
  - Planning mode task decomposition scenarios
  - Working mode task assignment logic
  - Mode switching with state preservation
  - Error recovery during mode operations

### Phase 3: Coordination (Orchestrator)
**Priority**: P0 - Multi-agent capability
**Estimated Time**: 12-18 hours
**Dependencies**: Phase 2 complete

#### Orchestrator Module (`amplifier/planner/orchestrator/`)
- [ ] **coordinator.py** - Agent spawning and lifecycle management
  - AgentCoordinator class for managing multiple amplifier agents
  - Integration with amplifier's Task tool for agent spawning
  - Agent status tracking (starting, running, completed, failed)
  - Resource management (concurrent agent limits)
  - Agent cleanup and failure recovery

- [ ] **task_assigner.py** - Strategic task assignment
  - TaskAssigner class for intelligent task matching
  - Task analysis (complexity, required tools, urgency)
  - Agent capability matching and load balancing
  - Priority-based scheduling algorithms
  - Dependency-aware assignment ordering

#### API and CLI Integration
- [ ] **__init__.py** - Public API contracts ("studs")
  - Main entry points: `create_planner()`, `load_planner()`
  - Public classes: Task, Project, PlannerMode, etc.
  - Integration protocols for other amplifier modules
  - Version management and backward compatibility

- [ ] **cli.py** - Command-line interface
  - Make command integration (`planner-create`, `planner-plan`, `planner-work`)
  - Project management commands (create, list, delete)
  - Task operations (show, assign, complete)
  - Agent coordination commands (spawn, monitor, cleanup)

#### Coordination Tests
- [ ] **test_orchestrator.py** - Multi-agent coordination
  - Agent spawning with real Task tool integration
  - Concurrent task execution simulation
  - Resource contention and load balancing
  - Agent failure recovery scenarios

- [ ] **test_integration.py** - Full system integration
  - End-to-end workflows with real LLM calls
  - Multi-agent project execution
  - Git operations under concurrent load
  - Performance validation at scale

### Phase 4: Golden Test Suite Implementation
**Priority**: P1 - Quality assurance
**Estimated Time**: 6-10 hours
**Dependencies**: Phase 3 complete

#### Golden Test Data
- [ ] **fixtures/simple_web_app.json** - Basic workflow validation
  - 8-task Django blog project
  - 2-3 levels of task hierarchy
  - Expected completion in ~2 hours with 2-3 agents

- [ ] **fixtures/complex_microservices.json** - Multi-agent coordination
  - 22-task e-commerce platform
  - 4-5 levels of task hierarchy
  - Expected completion in ~1 week with 8-10 agents

- [ ] **fixtures/enterprise_migration.json** - Scale validation
  - 500-1000 tasks legacy system migration
  - 5+ levels of task hierarchy
  - Expected completion in ~3 months with 15-20 agents

#### Integration Test Scenarios
- [ ] **test_golden_workflows.py** - Complete workflow validation
  - Simple project end-to-end execution
  - Complex project multi-agent coordination
  - Enterprise project scale testing
  - Performance benchmark validation

- [ ] **test_failure_scenarios.py** - Reliability validation
  - Network partition during agent coordination
  - File corruption and recovery
  - Agent crashes mid-execution
  - Git conflicts during concurrent updates
  - LLM API failures and recovery

### Phase 5: Documentation and Deployment
**Priority**: P2 - Production readiness
**Estimated Time**: 4-6 hours
**Dependencies**: Phase 4 complete

#### Documentation
- [ ] **README.md** - Main module documentation
  - Quick start guide and usage examples
  - Architecture overview and philosophy
  - API reference and integration points
  - Troubleshooting and FAQ

- [ ] **CONTRACTS.md** - API contract specifications
  - Public API stability guarantees
  - Integration protocols documentation
  - Extension points for customization
  - Version management strategy

#### Production Integration
- [ ] **Makefile integration** - Add planner commands to main Makefile
  - `make planner-create PROJECT="name"` - Create new project
  - `make planner-plan PROJECT_ID="uuid"` - Run planning mode
  - `make planner-work PROJECT_ID="uuid"` - Run working mode
  - `make planner-status PROJECT_ID="uuid"` - Show project status

- [ ] **VSCode integration** - Workspace configuration
  - Exclude planner data files from search
  - Git integration for planner repositories
  - Task highlighting and navigation

## Current Status

**Completed Design Work:**
- ✅ Complete architecture design with all module specifications
- ✅ Comprehensive data model design with file structure
- ✅ Coordination protocols for multi-agent workflow
- ✅ Sub-agent spawning mechanisms via Task tool
- ✅ Git integration and persistence strategy
- ✅ Golden test specifications (28 scenarios)
- ✅ API contracts and integration points

**Ready to Begin Implementation:**
- Phase 1 specifications are complete and detailed
- Test requirements are clearly defined
- Integration points with existing amplifier code are mapped
- File structure and data formats are specified
- Git workflow is designed and validated

**Implementation Priority:**
1. Start with Phase 1 (Foundation) - most critical for system stability
2. Implement golden tests alongside each module for validation
3. Use existing amplifier patterns (ccsdk_toolkit, defensive utilities)
4. Follow "bricks and studs" philosophy - stable contracts, regenerable internals

## Key Implementation Notes

### Critical Integration Points
- **CCSDK Toolkit**: Use `SessionManager`, `parse_llm_json`, `retry_with_feedback`
- **Defensive File I/O**: Handle OneDrive/cloud sync issues with retry patterns
- **Task Tool**: Agent spawning via `Task(subagent_type="...", prompt="...")`
- **Git Workflow**: Auto-commit with semantic messages, recovery points

### Performance Considerations
- **Incremental saves**: Save after every task state change
- **Selective loading**: Only load tasks needed for current operation
- **Batch operations**: Group related changes into single git commits
- **Caching**: Task data caching with file modification time checks

### Error Handling Patterns
- **Optimistic locking**: Version numbers prevent concurrent modification conflicts
- **Retry with backoff**: File I/O, LLM API calls, git operations
- **Circuit breakers**: Graceful degradation when components fail
- **Recovery points**: Git tags for rollback capability

### Testing Strategy
- **Test-first development**: Implement golden tests before each module
- **Real integration**: Use actual Task tool, LLM APIs, git operations
- **Failure simulation**: Network issues, file corruption, agent crashes
- **Performance validation**: Scale testing with 1000+ tasks, 20 agents

This working plan captures the complete context needed to implement the Super-Planner system. Future sessions can pick up from any phase and understand the full scope, design decisions, and implementation requirements.