"""
Conflict Resolution and Consistency Protocol

Handles concurrent task modifications, merge strategies, human escalation,
and maintains consistency across distributed operations in the task system.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from enum import Enum
from typing import Any

from ..core.models import Task

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of conflicts that can occur."""

    VERSION_MISMATCH = "version_mismatch"
    CONCURRENT_STATE_CHANGE = "concurrent_state_change"
    ASSIGNMENT_CONFLICT = "assignment_conflict"
    DEPENDENCY_CONFLICT = "dependency_conflict"
    METADATA_CONFLICT = "metadata_conflict"


class ResolutionStrategy(Enum):
    """Conflict resolution strategies."""

    LAST_WRITER_WINS = "last_writer_wins"
    FIRST_WRITER_WINS = "first_writer_wins"
    MERGE_CHANGES = "merge_changes"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    REJECT_CONFLICT = "reject_conflict"


@dataclass
class ConflictRecord:
    """Record of a conflict and its resolution."""

    conflict_id: str
    task_id: str
    conflict_type: ConflictType
    conflicting_versions: list[int]
    conflicting_agents: list[str]
    detected_at: datetime
    resolution_strategy: ResolutionStrategy | None = None
    resolved_at: datetime | None = None
    resolution_details: dict[str, Any] = field(default_factory=dict)
    escalated: bool = False


@dataclass
class TaskModification:
    """Represents a modification to a task."""

    task_id: str
    agent_id: str
    timestamp: datetime
    previous_version: int
    changes: dict[str, Any]
    new_task_state: Task


class ConflictResolutionProtocol:
    """
    Manages conflict detection and resolution for concurrent task modifications.
    Provides multiple resolution strategies and escalation paths.
    """

    def __init__(self, auto_retry_attempts: int = 3, escalation_timeout: timedelta = timedelta(minutes=30)):
        self.conflicts: dict[str, ConflictRecord] = {}
        self.pending_modifications: dict[str, list[TaskModification]] = defaultdict(list)
        self.resolution_strategies: dict[ConflictType, ResolutionStrategy] = {
            ConflictType.VERSION_MISMATCH: ResolutionStrategy.MERGE_CHANGES,
            ConflictType.CONCURRENT_STATE_CHANGE: ResolutionStrategy.LAST_WRITER_WINS,
            ConflictType.ASSIGNMENT_CONFLICT: ResolutionStrategy.ESCALATE_TO_HUMAN,
            ConflictType.DEPENDENCY_CONFLICT: ResolutionStrategy.MERGE_CHANGES,
            ConflictType.METADATA_CONFLICT: ResolutionStrategy.MERGE_CHANGES,
        }
        self.auto_retry_attempts = auto_retry_attempts
        self.escalation_timeout = escalation_timeout

    def detect_conflict(self, current_task: Task, modification: TaskModification) -> ConflictType | None:
        """
        Detect if a modification conflicts with the current task state.

        Args:
            current_task: Current task state
            modification: Proposed modification

        Returns:
            ConflictType if conflict detected, None otherwise
        """
        # Version mismatch
        if current_task.version != modification.previous_version:
            return ConflictType.VERSION_MISMATCH

        # Concurrent state changes
        proposed_task = modification.new_task_state
        if current_task.state != proposed_task.state and current_task.updated_at > modification.timestamp:
            return ConflictType.CONCURRENT_STATE_CHANGE

        # Assignment conflicts
        if (
            current_task.assigned_to != proposed_task.assigned_to
            and current_task.assigned_to is not None
            and proposed_task.assigned_to is not None
            and current_task.assigned_to != proposed_task.assigned_to
        ):
            return ConflictType.ASSIGNMENT_CONFLICT

        # Dependency conflicts (simplified check)
        current_deps = set(current_task.dependencies or [])
        proposed_deps = set(proposed_task.dependencies or [])
        if current_deps != proposed_deps and len(current_deps) > 0 and len(proposed_deps) > 0:
            return ConflictType.DEPENDENCY_CONFLICT

        return None

    async def resolve_conflict(
        self, conflict_record: ConflictRecord, current_task: Task, conflicting_modifications: list[TaskModification]
    ) -> Task:
        """
        Resolve a conflict using the appropriate strategy.

        Args:
            conflict_record: Record of the conflict
            current_task: Current task state
            conflicting_modifications: List of conflicting modifications

        Returns:
            Resolved task state

        Raises:
            ValueError: If conflict cannot be resolved automatically
        """
        strategy = self.resolution_strategies.get(conflict_record.conflict_type, ResolutionStrategy.ESCALATE_TO_HUMAN)

        conflict_record.resolution_strategy = strategy

        if strategy == ResolutionStrategy.LAST_WRITER_WINS:
            return await self._resolve_last_writer_wins(current_task, conflicting_modifications)

        if strategy == ResolutionStrategy.FIRST_WRITER_WINS:
            return await self._resolve_first_writer_wins(current_task, conflicting_modifications)

        if strategy == ResolutionStrategy.MERGE_CHANGES:
            return await self._resolve_merge_changes(current_task, conflicting_modifications)

        if strategy == ResolutionStrategy.ESCALATE_TO_HUMAN:
            await self._escalate_conflict(conflict_record, current_task, conflicting_modifications)
            raise ValueError(f"Conflict {conflict_record.conflict_id} escalated to human intervention")

        if strategy == ResolutionStrategy.REJECT_CONFLICT:
            raise ValueError(f"Conflict {conflict_record.conflict_id} rejected")

        raise ValueError(f"Unknown resolution strategy: {strategy}")

    async def _resolve_last_writer_wins(self, current_task: Task, modifications: list[TaskModification]) -> Task:
        """Resolve conflict by using the most recent modification."""
        latest_mod = max(modifications, key=lambda m: m.timestamp)

        # Apply the latest modification with version increment
        resolved_task = Task(
            id=current_task.id,
            title=latest_mod.new_task_state.title,
            description=latest_mod.new_task_state.description,
            state=latest_mod.new_task_state.state,
            priority=latest_mod.new_task_state.priority,
            estimated_effort=latest_mod.new_task_state.estimated_effort,
            assigned_to=latest_mod.new_task_state.assigned_to,
            dependencies=latest_mod.new_task_state.dependencies,
            metadata=latest_mod.new_task_state.metadata,
            parent_id=latest_mod.new_task_state.parent_id,
            subtask_ids=latest_mod.new_task_state.subtask_ids,
            created_at=current_task.created_at,
            updated_at=datetime.now(UTC),
            started_at=latest_mod.new_task_state.started_at,
            completed_at=latest_mod.new_task_state.completed_at,
            cancelled_at=latest_mod.new_task_state.cancelled_at,
            blocked_at=latest_mod.new_task_state.blocked_at,
            blocking_reason=latest_mod.new_task_state.blocking_reason,
            version=current_task.version + 1,
        )

        logger.info(f"Resolved conflict using last writer wins: agent {latest_mod.agent_id}")
        return resolved_task

    async def _resolve_first_writer_wins(self, current_task: Task, modifications: list[TaskModification]) -> Task:
        """Resolve conflict by using the earliest modification."""
        earliest_mod = min(modifications, key=lambda m: m.timestamp)

        # Apply the earliest modification with version increment
        resolved_task = Task(
            id=current_task.id,
            title=earliest_mod.new_task_state.title,
            description=earliest_mod.new_task_state.description,
            state=earliest_mod.new_task_state.state,
            priority=earliest_mod.new_task_state.priority,
            estimated_effort=earliest_mod.new_task_state.estimated_effort,
            assigned_to=earliest_mod.new_task_state.assigned_to,
            dependencies=earliest_mod.new_task_state.dependencies,
            metadata=earliest_mod.new_task_state.metadata,
            parent_id=earliest_mod.new_task_state.parent_id,
            subtask_ids=earliest_mod.new_task_state.subtask_ids,
            created_at=current_task.created_at,
            updated_at=datetime.now(UTC),
            started_at=earliest_mod.new_task_state.started_at,
            completed_at=earliest_mod.new_task_state.completed_at,
            cancelled_at=earliest_mod.new_task_state.cancelled_at,
            blocked_at=earliest_mod.new_task_state.blocked_at,
            blocking_reason=earliest_mod.new_task_state.blocking_reason,
            version=current_task.version + 1,
        )

        logger.info(f"Resolved conflict using first writer wins: agent {earliest_mod.agent_id}")
        return resolved_task

    async def _resolve_merge_changes(self, current_task: Task, modifications: list[TaskModification]) -> Task:
        """
        Resolve conflict by intelligently merging non-conflicting changes.
        """
        # Start with current task as base
        merged_task = current_task

        # Sort modifications by timestamp
        sorted_mods = sorted(modifications, key=lambda m: m.timestamp)

        for mod in sorted_mods:
            merged_task = await self._merge_single_modification(merged_task, mod)

        # Update version and timestamp
        merged_task = Task(
            id=merged_task.id,
            title=merged_task.title,
            description=merged_task.description,
            state=merged_task.state,
            priority=merged_task.priority,
            estimated_effort=merged_task.estimated_effort,
            assigned_to=merged_task.assigned_to,
            dependencies=merged_task.dependencies,
            metadata=merged_task.metadata,
            parent_id=merged_task.parent_id,
            subtask_ids=merged_task.subtask_ids,
            created_at=merged_task.created_at,
            updated_at=datetime.now(UTC),
            started_at=merged_task.started_at,
            completed_at=merged_task.completed_at,
            cancelled_at=merged_task.cancelled_at,
            blocked_at=merged_task.blocked_at,
            blocking_reason=merged_task.blocking_reason,
            version=current_task.version + 1,
        )

        logger.info(f"Resolved conflict by merging changes from {len(modifications)} modifications")
        return merged_task

    async def _merge_single_modification(self, base_task: Task, modification: TaskModification) -> Task:
        """Merge a single modification into the base task."""
        new_state = modification.new_task_state

        # Merge metadata (additive)
        merged_metadata = (base_task.metadata or {}).copy()
        if new_state.metadata:
            merged_metadata.update(new_state.metadata)

        # Merge dependencies (union)
        base_deps = set(base_task.dependencies or [])
        new_deps = set(new_state.dependencies or [])
        merged_deps = list(base_deps.union(new_deps))

        # Merge subtasks (union)
        base_subtasks = set(base_task.subtask_ids or [])
        new_subtasks = set(new_state.subtask_ids or [])
        merged_subtasks = list(base_subtasks.union(new_subtasks))

        # For other fields, prefer non-null values from modification
        return Task(
            id=base_task.id,
            title=new_state.title if new_state.title != base_task.title else base_task.title,
            description=new_state.description
            if new_state.description != base_task.description
            else base_task.description,
            state=new_state.state if new_state.state != base_task.state else base_task.state,
            priority=new_state.priority if new_state.priority != base_task.priority else base_task.priority,
            estimated_effort=new_state.estimated_effort
            if new_state.estimated_effort != base_task.estimated_effort
            else base_task.estimated_effort,
            assigned_to=new_state.assigned_to or base_task.assigned_to,
            dependencies=merged_deps,
            metadata=merged_metadata,
            parent_id=new_state.parent_id or base_task.parent_id,
            subtask_ids=merged_subtasks,
            created_at=base_task.created_at,
            updated_at=base_task.updated_at,
            started_at=new_state.started_at or base_task.started_at,
            completed_at=new_state.completed_at or base_task.completed_at,
            cancelled_at=new_state.cancelled_at or base_task.cancelled_at,
            blocked_at=new_state.blocked_at or base_task.blocked_at,
            blocking_reason=new_state.blocking_reason or base_task.blocking_reason,
            version=base_task.version,
        )

    async def _escalate_conflict(
        self, conflict_record: ConflictRecord, current_task: Task, modifications: list[TaskModification]
    ) -> None:
        """Escalate conflict to human intervention."""
        conflict_record.escalated = True

        # Log detailed conflict information
        logger.critical(f"CONFLICT ESCALATION: {conflict_record.conflict_id}")
        logger.critical(f"Task ID: {current_task.id}")
        logger.critical(f"Conflict Type: {conflict_record.conflict_type}")
        logger.critical(f"Conflicting Agents: {conflict_record.conflicting_agents}")
        logger.critical(f"Versions: {conflict_record.conflicting_versions}")

        # Store detailed information for human review
        conflict_record.resolution_details = {
            "current_task": self._task_to_dict(current_task),
            "modifications": [
                {
                    "agent_id": mod.agent_id,
                    "timestamp": mod.timestamp.isoformat(),
                    "changes": mod.changes,
                    "new_state": self._task_to_dict(mod.new_task_state),
                }
                for mod in modifications
            ],
            "escalated_at": datetime.now(UTC).isoformat(),
        }

    def _task_to_dict(self, task: Task) -> dict[str, Any]:
        """Convert task to dictionary for logging/storage."""
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "state": task.state.value,
            "priority": task.priority,
            "estimated_effort": task.estimated_effort,
            "assigned_to": task.assigned_to,
            "dependencies": task.dependencies,
            "metadata": task.metadata,
            "parent_id": task.parent_id,
            "subtask_ids": task.subtask_ids,
            "version": task.version,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "cancelled_at": task.cancelled_at.isoformat() if task.cancelled_at else None,
            "blocked_at": task.blocked_at.isoformat() if task.blocked_at else None,
            "blocking_reason": task.blocking_reason,
        }

    async def apply_modification_with_retry(self, current_task: Task, modification: TaskModification) -> Task:
        """
        Apply a modification with automatic conflict resolution and retry.

        Args:
            current_task: Current task state
            modification: Modification to apply

        Returns:
            Updated task after resolution

        Raises:
            ValueError: If modification cannot be applied after retries
        """
        for attempt in range(self.auto_retry_attempts):
            conflict_type = self.detect_conflict(current_task, modification)

            if conflict_type is None:
                # No conflict, apply modification directly
                return modification.new_task_state

            # Create conflict record
            conflict_id = f"{modification.task_id}_{modification.timestamp.timestamp()}"
            conflict_record = ConflictRecord(
                conflict_id=conflict_id,
                task_id=modification.task_id,
                conflict_type=conflict_type,
                conflicting_versions=[current_task.version, modification.previous_version],
                conflicting_agents=[modification.agent_id],
                detected_at=datetime.now(UTC),
            )

            self.conflicts[conflict_id] = conflict_record

            try:
                # Attempt to resolve conflict
                resolved_task = await self.resolve_conflict(conflict_record, current_task, [modification])

                conflict_record.resolved_at = datetime.now(UTC)
                logger.info(f"Resolved conflict {conflict_id} on attempt {attempt + 1}")

                return resolved_task

            except ValueError as e:
                if "escalated" in str(e):
                    # Human intervention required
                    raise e

                if attempt == self.auto_retry_attempts - 1:
                    # Final attempt failed
                    logger.error(f"Failed to resolve conflict {conflict_id} after {self.auto_retry_attempts} attempts")
                    raise e

                # Retry with exponential backoff
                import asyncio

                await asyncio.sleep(2**attempt)
                logger.warning(f"Retrying conflict resolution for {conflict_id}, attempt {attempt + 2}")

        raise ValueError(f"Could not resolve conflict after {self.auto_retry_attempts} attempts")

    def get_escalated_conflicts(self) -> list[ConflictRecord]:
        """Get all conflicts that require human intervention."""
        return [conflict for conflict in self.conflicts.values() if conflict.escalated and conflict.resolved_at is None]

    def get_conflict_stats(self) -> dict[str, Any]:
        """Get conflict resolution statistics."""
        total_conflicts = len(self.conflicts)
        resolved_conflicts = sum(1 for c in self.conflicts.values() if c.resolved_at is not None)
        escalated_conflicts = sum(1 for c in self.conflicts.values() if c.escalated)

        conflict_types = defaultdict(int)
        for conflict in self.conflicts.values():
            conflict_types[conflict.conflict_type.value] += 1

        resolution_strategies = defaultdict(int)
        for conflict in self.conflicts.values():
            if conflict.resolution_strategy:
                resolution_strategies[conflict.resolution_strategy.value] += 1

        return {
            "total_conflicts": total_conflicts,
            "resolved_conflicts": resolved_conflicts,
            "escalated_conflicts": escalated_conflicts,
            "resolution_rate": resolved_conflicts / max(total_conflicts, 1),
            "conflict_types": dict(conflict_types),
            "resolution_strategies": dict(resolution_strategies),
        }


# Global conflict resolution instance
conflict_protocol = ConflictResolutionProtocol()
