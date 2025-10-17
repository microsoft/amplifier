# Task State Management and Coordination Protocols

This document provides an overview of the comprehensive protocol system designed for the super-planner's task state management and multi-agent coordination capabilities.

## Architecture Overview

The protocol system consists of five core components that work together to ensure reliable, coordinated task management across multiple agents:

1. **State Transition Protocol** - Manages valid task state changes
2. **Agent Coordination Protocol** - Handles multi-agent task claiming and load balancing
3. **Deadlock Prevention Protocol** - Detects and resolves circular dependencies
4. **Conflict Resolution Protocol** - Manages concurrent task modifications
5. **Defensive Coordination Utilities** - Provides robust error handling and recovery

## Protocol Components

### 1. State Transition Protocol (`state_transitions.py`)

Manages atomic state transitions for tasks with optimistic locking and validation.

**Key Features:**
- Valid transition definitions with guard conditions and side effects
- Optimistic locking with version numbers to prevent concurrent modification conflicts
- Immutable task updates with automatic version incrementing
- Comprehensive transition validation and error handling

**State Flow:**
```
NOT_STARTED → ASSIGNED → IN_PROGRESS → COMPLETED
     ↓           ↓            ↓
  IN_PROGRESS  CANCELLED   BLOCKED → IN_PROGRESS
     ↓                       ↓
  COMPLETED               CANCELLED
```

**Usage:**
```python
from amplifier.planner.protocols import state_protocol

# Transition a task
updated_task = state_protocol.transition_task(task, TaskState.IN_PROGRESS, expected_version=task.version)

# Check valid transitions
can_transition, reason = state_protocol.can_transition(task, TaskState.COMPLETED)
```

### 2. Agent Coordination Protocol (`agent_coordination.py`)

Manages multi-agent coordination, task claiming, and load balancing to prevent conflicts.

**Key Features:**
- Agent registration with capabilities and capacity limits
- Task claiming with time-based leases and automatic expiration
- Load balancing based on current agent utilization
- Heartbeat monitoring and automatic cleanup of inactive agents
- Capability-based task assignment matching

**Core Operations:**
- `register_agent()` - Register agent with capabilities and limits
- `claim_task()` - Atomically claim a task with lease
- `release_task()` - Release a claimed task
- `select_best_agent()` - Load-balanced agent selection
- `cleanup_expired_claims()` - Remove expired leases

**Usage:**
```python
from amplifier.planner.protocols import coordination_protocol

# Register an agent
await coordination_protocol.register_agent("ai_agent_1", {"python", "analysis"}, max_concurrent_tasks=5)

# Claim a task
claim = await coordination_protocol.claim_task("task_123", "ai_agent_1")

# Get agent recommendations
best_agent = coordination_protocol.select_best_agent(task)
```

### 3. Deadlock Prevention Protocol (`deadlock_prevention.py`)

Prevents and resolves deadlocks through cycle detection, dependency tracking, and automatic resolution.

**Key Features:**
- Real-time circular dependency detection using graph algorithms
- Dependency depth limiting to prevent infinite chains
- Multiple deadlock resolution strategies (weakest link, most recent task)
- Timeout-based escalation for long-blocked tasks
- Comprehensive deadlock cycle analysis and severity assessment

**Core Operations:**
- `add_dependency()` - Add dependency with cycle checking
- `detect_deadlocks()` - Find all active deadlock cycles
- `resolve_deadlock()` - Attempt automatic resolution
- `check_timeout_violations()` - Find overdue blocked tasks

**Usage:**
```python
from amplifier.planner.protocols import deadlock_protocol

# Add a dependency (with cycle prevention)
success = await deadlock_protocol.add_dependency("task_a", "task_b")

# Check for deadlocks
cycles = await deadlock_protocol.detect_deadlocks()

# Resolve if found
for cycle in cycles:
    resolved = await deadlock_protocol.resolve_deadlock(cycle)
```

### 4. Conflict Resolution Protocol (`conflict_resolution.py`)

Handles concurrent task modifications with intelligent merge strategies and escalation.

**Key Features:**
- Multiple conflict detection types (version, state, assignment, dependency)
- Configurable resolution strategies (last writer wins, merge, escalate)
- Intelligent change merging for compatible modifications
- Automatic retry with exponential backoff
- Human escalation for complex conflicts

**Resolution Strategies:**
- **Last Writer Wins** - Use most recent modification
- **First Writer Wins** - Use earliest modification
- **Merge Changes** - Intelligently combine non-conflicting changes
- **Escalate to Human** - Require manual intervention
- **Reject Conflict** - Block the conflicting change

**Usage:**
```python
from amplifier.planner.protocols import conflict_protocol

# Apply modification with automatic conflict resolution
resolved_task = await conflict_protocol.apply_modification_with_retry(current_task, modification)

# Get conflicts needing human intervention
escalated = conflict_protocol.get_escalated_conflicts()
```

### 5. Defensive Coordination Utilities (`defensive_coordination.py`)

Provides robust error handling, health monitoring, and graceful degradation capabilities.

**Key Features:**
- Retry decorators with exponential backoff and configurable exceptions
- Defensive file I/O with cloud sync error handling (from DISCOVERIES.md patterns)
- Health monitoring for all coordination components
- Circuit breaker patterns for failing services
- Graceful degradation strategies when protocols fail

**Core Utilities:**
- `@retry_with_backoff` - Decorator for automatic retries
- `DefensiveFileIO` - Cloud-sync aware file operations
- `CoordinationHealthCheck` - System health monitoring
- `TaskOperationContext` - Safe operation context manager
- `GracefulDegradation` - Fallback strategies

**Usage:**
```python
from amplifier.planner.protocols import file_io, health_monitor, retry_with_backoff

# Defensive file operations
file_io.write_json(data, Path("tasks.json"))

# Health monitoring
health_status = await health_monitor.full_health_check()

# Retry decorator
@retry_with_backoff()
async def risky_operation():
    # Operation that might fail
    pass
```

## Integration Patterns

### Task Lifecycle Management

```python
from amplifier.planner.protocols import (
    state_protocol,
    coordination_protocol,
    deadlock_protocol,
    conflict_protocol
)

async def process_task_lifecycle(task):
    # 1. Assign to agent
    best_agent = coordination_protocol.select_best_agent(task)
    claim = await coordination_protocol.claim_task(task.id, best_agent)

    # 2. Transition to assigned state
    task = state_protocol.transition_task(task, TaskState.ASSIGNED)

    # 3. Check for dependency issues
    cycles = await deadlock_protocol.detect_deadlocks()
    if cycles:
        for cycle in cycles:
            await deadlock_protocol.resolve_deadlock(cycle)

    # 4. Start work
    task = state_protocol.transition_task(task, TaskState.IN_PROGRESS)

    # 5. Handle concurrent modifications
    if modifications:
        task = await conflict_protocol.apply_modification_with_retry(task, modification)

    # 6. Complete and release
    task = state_protocol.transition_task(task, TaskState.COMPLETED)
    await coordination_protocol.release_task(task.id, best_agent)
```

### Health Monitoring and Recovery

```python
from amplifier.planner.protocols import health_monitor, coordination_protocol, deadlock_protocol

async def system_health_check():
    # Full system health check
    health = await health_monitor.full_health_check()

    if health["overall_status"] == "unhealthy":
        # Cleanup and recovery
        await coordination_protocol.cleanup_expired_claims()
        await coordination_protocol.cleanup_inactive_agents()

        # Check for deadlocks
        violations = await deadlock_protocol.check_timeout_violations()
        for task_id in violations:
            # Escalate overdue tasks
            pass
```

## Error Handling Strategy

The protocol system uses a layered error handling approach:

1. **Prevention** - Validate operations before execution
2. **Detection** - Monitor for conflicts, deadlocks, and failures
3. **Automatic Recovery** - Retry with backoff, resolve conflicts automatically
4. **Graceful Degradation** - Fallback strategies when protocols fail
5. **Human Escalation** - Manual intervention for complex cases

## Configuration and Customization

Each protocol supports configuration for different deployment scenarios:

```python
# Custom retry configuration
retry_config = RetryConfig(
    max_attempts=5,
    initial_delay=1.0,
    backoff_multiplier=2.0,
    retry_on_exceptions=(ConnectionError, TimeoutError)
)

# Custom deadlock thresholds
deadlock_protocol = DeadlockPreventionProtocol(
    max_block_duration=timedelta(hours=2),
    escalation_threshold=timedelta(minutes=30),
    max_dependency_depth=5
)

# Custom conflict resolution strategies
conflict_protocol.resolution_strategies[ConflictType.ASSIGNMENT_CONFLICT] = ResolutionStrategy.LAST_WRITER_WINS
```

## Performance and Scalability

The protocol system is designed for scalability:

- **Lock-free where possible** - Uses optimistic locking instead of blocking
- **Asynchronous operations** - All protocols support async/await
- **Efficient data structures** - Fast lookups for agents, tasks, dependencies
- **Incremental cleanup** - Background processes for expired claims and inactive agents
- **Batched operations** - Support for bulk operations where appropriate

## Git Integration

The protocols are designed to work with git-based workflows:

- **File-based persistence** - Uses JSON files that can be committed
- **Conflict-free merging** - Task modifications can be merged across branches
- **Incremental updates** - Only changed data is written to files
- **Defensive I/O** - Handles cloud sync issues that are common in git repos

This protocol system provides a robust foundation for coordinated multi-agent task management while maintaining simplicity and reliability principles from the project's implementation philosophy.