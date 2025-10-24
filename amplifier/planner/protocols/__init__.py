"""
Task State Management and Coordination Protocols

This package provides comprehensive protocols for managing task state transitions,
multi-agent coordination, deadlock prevention, conflict resolution, and defensive
programming patterns for the super-planner system.

Key Components:
- State Transition Protocol: Manages valid task state changes with optimistic locking
- Agent Coordination Protocol: Handles task claiming, load balancing, and resource contention
- Deadlock Prevention Protocol: Detects and resolves circular dependencies and blocked chains
- Conflict Resolution Protocol: Manages concurrent modifications with merge strategies
- Defensive Coordination Utilities: Provides retry logic, health monitoring, and graceful degradation

Usage Example:
    from amplifier.planner.protocols import (
        state_protocol,
        coordination_protocol,
        deadlock_protocol,
        conflict_protocol,
        file_io,
        health_monitor
    )

    # Transition a task state
    updated_task = state_protocol.transition_task(task, TaskState.IN_PROGRESS)

    # Register an agent for coordination
    await coordination_protocol.register_agent("agent_1", {"python", "ai"})

    # Claim a task
    claim = await coordination_protocol.claim_task("task_123", "agent_1")

    # Check for deadlocks
    cycles = await deadlock_protocol.detect_deadlocks()

    # Resolve conflicts
    resolved_task = await conflict_protocol.apply_modification_with_retry(task, modification)

    # Health monitoring
    health_status = await health_monitor.full_health_check()
"""

from .agent_coordination import AgentCoordinationProtocol
from .agent_coordination import coordination_protocol
from .conflict_resolution import ConflictResolutionProtocol
from .conflict_resolution import conflict_protocol
from .deadlock_prevention import DeadlockPreventionProtocol
from .deadlock_prevention import deadlock_protocol
from .defensive_coordination import CoordinationHealthCheck
from .defensive_coordination import DefensiveFileIO
from .defensive_coordination import GracefulDegradation
from .defensive_coordination import TaskOperationContext
from .defensive_coordination import file_io
from .defensive_coordination import health_monitor
from .defensive_coordination import retry_with_backoff
from .state_transitions import StateTransitionProtocol
from .state_transitions import state_protocol

__all__ = [
    # Protocol classes
    "StateTransitionProtocol",
    "AgentCoordinationProtocol",
    "DeadlockPreventionProtocol",
    "ConflictResolutionProtocol",
    "DefensiveFileIO",
    "CoordinationHealthCheck",
    "GracefulDegradation",
    "TaskOperationContext",
    # Global instances
    "state_protocol",
    "coordination_protocol",
    "deadlock_protocol",
    "conflict_protocol",
    "file_io",
    "health_monitor",
    # Utilities
    "retry_with_backoff",
]
