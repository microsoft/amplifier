"""
State Transition Management Protocol

Defines valid state transitions, guard conditions, and atomic state change operations
for the super-planner task management system. Ensures data integrity and prevents
invalid state changes through defensive programming patterns.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime

from ..core.models import Task
from ..core.models import TaskState

logger = logging.getLogger(__name__)


class TransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, message: str = "Invalid state transition attempted") -> None:
        super().__init__(message)


class ConcurrencyError(Exception):
    """Raised when a concurrent modification is detected."""

    def __init__(self, message: str = "Concurrent modification detected") -> None:
        super().__init__(message)


@dataclass(frozen=True)
class StateTransition:
    """Represents a state transition with validation and effects."""

    from_state: TaskState
    to_state: TaskState
    guard_condition: Callable[[Task], bool] | None = None
    side_effects: Callable[[Task], None] | None = None
    requires_assignment: bool = False
    description: str = ""

    def __hash__(self) -> int:
        """Make StateTransition hashable for use in sets."""
        return hash((self.from_state, self.to_state, self.requires_assignment, self.description))


class StateTransitionProtocol:
    """
    Manages valid state transitions for tasks with atomic operations,
    optimistic locking, and defensive error handling.
    """

    def __init__(self):
        self.transitions = self._define_valid_transitions()
        self.transition_map = self._build_transition_map()

    def _define_valid_transitions(self) -> set[StateTransition]:
        """Define all valid state transitions with their conditions."""
        return {
            # Initial transitions from NOT_STARTED
            StateTransition(
                TaskState.NOT_STARTED,
                TaskState.ASSIGNED,
                guard_condition=lambda t: t.assigned_to is not None,
                description="Assign task to agent",
            ),
            # Direct start without assignment (for human tasks)
            StateTransition(
                TaskState.NOT_STARTED,
                TaskState.IN_PROGRESS,
                guard_condition=lambda t: t.assigned_to is not None,
                side_effects=lambda t: setattr(t, "started_at", datetime.now(UTC)),
                description="Start task directly",
            ),
            # From ASSIGNED
            StateTransition(
                TaskState.ASSIGNED,
                TaskState.IN_PROGRESS,
                side_effects=lambda t: setattr(t, "started_at", datetime.now(UTC)),
                description="Begin working on assigned task",
            ),
            StateTransition(
                TaskState.ASSIGNED,
                TaskState.CANCELLED,
                side_effects=lambda t: setattr(t, "cancelled_at", datetime.now(UTC)),
                description="Cancel assigned task",
            ),
            # From IN_PROGRESS
            StateTransition(
                TaskState.IN_PROGRESS,
                TaskState.COMPLETED,
                side_effects=lambda t: setattr(t, "completed_at", datetime.now(UTC)),
                description="Complete task",
            ),
            StateTransition(
                TaskState.IN_PROGRESS,
                TaskState.BLOCKED,
                guard_condition=lambda t: bool(t.blocking_reason),
                side_effects=lambda t: setattr(t, "blocked_at", datetime.now(UTC)),
                description="Block task due to dependency or issue",
            ),
            StateTransition(
                TaskState.IN_PROGRESS,
                TaskState.CANCELLED,
                side_effects=lambda t: setattr(t, "cancelled_at", datetime.now(UTC)),
                description="Cancel in-progress task",
            ),
            # From BLOCKED
            StateTransition(
                TaskState.BLOCKED,
                TaskState.IN_PROGRESS,
                guard_condition=lambda t: not t.blocking_reason or t.blocking_reason.strip() == "",
                side_effects=lambda t: setattr(t, "blocked_at", None),
                description="Unblock and resume task",
            ),
            StateTransition(
                TaskState.BLOCKED,
                TaskState.CANCELLED,
                side_effects=lambda t: setattr(t, "cancelled_at", datetime.now(UTC)),
                description="Cancel blocked task",
            ),
            # Recovery transitions (for error handling)
            StateTransition(
                TaskState.ASSIGNED,
                TaskState.NOT_STARTED,
                side_effects=lambda t: setattr(t, "assigned_to", None),
                description="Unassign task (recovery)",
            ),
        }

    def _build_transition_map(self) -> dict[tuple, StateTransition]:
        """Build fast lookup map for transitions."""
        return {(t.from_state, t.to_state): t for t in self.transitions}

    def is_valid_transition(self, from_state: TaskState, to_state: TaskState) -> bool:
        """Check if a state transition is valid."""
        return (from_state, to_state) in self.transition_map

    def can_transition(self, task: Task, to_state: TaskState) -> tuple[bool, str | None]:
        """
        Check if a task can transition to the given state.
        Returns (can_transition, reason_if_not).
        """
        if task.state == to_state:
            return True, None  # Already in target state

        transition_key = (task.state, to_state)
        if transition_key not in self.transition_map:
            return False, f"No valid transition from {task.state} to {to_state}"

        transition = self.transition_map[transition_key]

        # Check guard condition if present
        if transition.guard_condition and not transition.guard_condition(task):
            return False, f"Guard condition failed for transition to {to_state}"

        return True, None

    def transition_task(self, task: Task, to_state: TaskState, expected_version: int | None = None) -> Task:
        """
        Atomically transition a task to a new state with optimistic locking.

        Args:
            task: Task to transition
            to_state: Target state
            expected_version: Expected version for optimistic locking

        Returns:
            Updated task with new state and incremented version

        Raises:
            TransitionError: If transition is invalid
            ConcurrencyError: If version conflict detected
        """
        # Optimistic locking check
        if expected_version is not None and task.version != expected_version:
            raise ConcurrencyError(f"Version conflict: expected {expected_version}, got {task.version}")

        # Validate transition
        can_transition, reason = self.can_transition(task, to_state)
        if not can_transition:
            raise TransitionError(f"Cannot transition task {task.id}: {reason}")

        # Get transition definition
        transition = self.transition_map[(task.state, to_state)]

        # Create updated task (immutable approach)
        updated_task = Task(
            id=task.id,
            title=task.title,
            description=task.description,
            state=to_state,  # New state
            priority=task.priority,
            estimated_effort=task.estimated_effort,
            assigned_to=task.assigned_to,
            dependencies=task.dependencies,
            metadata=task.metadata.copy() if task.metadata else {},
            parent_id=task.parent_id,
            subtask_ids=task.subtask_ids.copy() if task.subtask_ids else [],
            created_at=task.created_at,
            updated_at=datetime.now(UTC),  # Update timestamp
            started_at=task.started_at,
            completed_at=task.completed_at,
            cancelled_at=task.cancelled_at,
            blocked_at=task.blocked_at,
            blocking_reason=task.blocking_reason,
            version=task.version + 1,  # Increment version
        )

        # Apply side effects if present
        if transition.side_effects:
            try:
                transition.side_effects(updated_task)
            except Exception as e:
                logger.error(f"Side effect failed for task {task.id}: {e}")
                raise TransitionError(f"Transition side effect failed: {e}")

        logger.info(f"Task {task.id} transitioned from {task.state} to {to_state}")
        return updated_task

    def get_valid_next_states(self, current_state: TaskState) -> set[TaskState]:
        """Get all valid next states from the current state."""
        return {to_state for (from_state, to_state) in self.transition_map if from_state == current_state}

    def get_transition_description(self, from_state: TaskState, to_state: TaskState) -> str | None:
        """Get human-readable description of a transition."""
        transition_key = (from_state, to_state)
        if transition_key in self.transition_map:
            return self.transition_map[transition_key].description
        return None


# Global instance
state_protocol = StateTransitionProtocol()
