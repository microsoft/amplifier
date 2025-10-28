"""
Deadlock Prevention and Recovery Protocol

Detects circular dependencies, handles blocked task chains, implements timeout policies,
and provides escalation procedures to prevent and resolve deadlocks in the task system.
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from datetime import timedelta

logger = logging.getLogger(__name__)


class DeadlockError(Exception):
    """Raised when a deadlock is detected."""

    def __init__(self, message: str = "Deadlock detected in task execution") -> None:
        super().__init__(message)


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected."""

    def __init__(self, message: str = "Circular dependency detected") -> None:
        super().__init__(message)


@dataclass
class BlockedTaskInfo:
    """Information about a blocked task."""

    task_id: str
    blocked_at: datetime
    blocking_reason: str
    dependencies: list[str]
    escalated: bool = False


@dataclass
class DeadlockCycle:
    """Represents a detected deadlock cycle."""

    task_ids: list[str]
    cycle_length: int
    detected_at: datetime
    severity: str = "medium"  # low, medium, high, critical


class DeadlockPreventionProtocol:
    """
    Prevents and resolves deadlocks in the task dependency system.
    Uses cycle detection, timeouts, and escalation to maintain system health.
    """

    def __init__(
        self,
        max_block_duration: timedelta = timedelta(hours=4),
        escalation_threshold: timedelta = timedelta(hours=1),
        max_dependency_depth: int = 10,
    ):
        self.blocked_tasks: dict[str, BlockedTaskInfo] = {}
        self.dependency_graph: dict[str, set[str]] = defaultdict(set)
        self.reverse_graph: dict[str, set[str]] = defaultdict(set)
        self.max_block_duration = max_block_duration
        self.escalation_threshold = escalation_threshold
        self.max_dependency_depth = max_dependency_depth
        self._lock = asyncio.Lock()

    async def add_dependency(self, dependent_task_id: str, dependency_task_id: str) -> bool:
        """
        Add a dependency between tasks, checking for cycles.

        Args:
            dependent_task_id: Task that depends on another
            dependency_task_id: Task that is depended upon

        Returns:
            True if dependency added successfully, False if it would create a cycle

        Raises:
            CircularDependencyError: If adding the dependency would create a cycle
        """
        async with self._lock:
            # Check if adding this dependency would create a cycle
            if self._would_create_cycle(dependent_task_id, dependency_task_id):
                raise CircularDependencyError(
                    f"Adding dependency {dependent_task_id} -> {dependency_task_id} would create a circular dependency"
                )

            # Check dependency depth
            depth = self._calculate_dependency_depth(dependency_task_id)
            if depth >= self.max_dependency_depth:
                logger.warning(
                    f"Dependency chain too deep ({depth}) for {dependency_task_id}, "
                    f"maximum is {self.max_dependency_depth}"
                )
                return False

            # Add dependency
            self.dependency_graph[dependent_task_id].add(dependency_task_id)
            self.reverse_graph[dependency_task_id].add(dependent_task_id)

            logger.info(f"Added dependency: {dependent_task_id} depends on {dependency_task_id}")
            return True

    async def remove_dependency(self, dependent_task_id: str, dependency_task_id: str) -> bool:
        """Remove a dependency between tasks."""
        async with self._lock:
            if dependency_task_id in self.dependency_graph[dependent_task_id]:
                self.dependency_graph[dependent_task_id].discard(dependency_task_id)
                self.reverse_graph[dependency_task_id].discard(dependent_task_id)

                # Clean up empty entries
                if not self.dependency_graph[dependent_task_id]:
                    del self.dependency_graph[dependent_task_id]
                if not self.reverse_graph[dependency_task_id]:
                    del self.reverse_graph[dependency_task_id]

                logger.info(f"Removed dependency: {dependent_task_id} no longer depends on {dependency_task_id}")
                return True
            return False

    async def mark_task_blocked(
        self, task_id: str, blocking_reason: str, dependencies: list[str] | None = None
    ) -> None:
        """Mark a task as blocked and track it for deadlock detection."""
        async with self._lock:
            self.blocked_tasks[task_id] = BlockedTaskInfo(
                task_id=task_id,
                blocked_at=datetime.now(UTC),
                blocking_reason=blocking_reason,
                dependencies=dependencies or list(self.dependency_graph.get(task_id, [])),
            )
            logger.info(f"Task {task_id} marked as blocked: {blocking_reason}")

    async def mark_task_unblocked(self, task_id: str) -> bool:
        """Mark a task as unblocked and remove from tracking."""
        async with self._lock:
            if task_id in self.blocked_tasks:
                del self.blocked_tasks[task_id]
                logger.info(f"Task {task_id} marked as unblocked")
                return True
            return False

    def _would_create_cycle(self, from_task: str, to_task: str) -> bool:
        """Check if adding a dependency would create a cycle using DFS."""
        # If to_task can reach from_task, then adding from_task -> to_task creates a cycle
        return self._can_reach(to_task, from_task)

    def _can_reach(self, start_task: str, target_task: str) -> bool:
        """Check if start_task can reach target_task through dependencies."""
        if start_task == target_task:
            return True

        visited = set()
        stack = [start_task]

        while stack:
            current = stack.pop()
            if current == target_task:
                return True

            if current in visited:
                continue

            visited.add(current)
            stack.extend(self.dependency_graph.get(current, []))

        return False

    def _calculate_dependency_depth(self, task_id: str) -> int:
        """Calculate the maximum depth of the dependency chain starting from task_id."""
        visited = set()

        def dfs_depth(current_task: str) -> int:
            if current_task in visited:
                return 0  # Avoid infinite recursion

            visited.add(current_task)
            max_depth = 0

            for dependency in self.dependency_graph.get(current_task, []):
                depth = 1 + dfs_depth(dependency)
                max_depth = max(max_depth, depth)

            visited.remove(current_task)
            return max_depth

        return dfs_depth(task_id)

    async def detect_deadlocks(self) -> list[DeadlockCycle]:
        """
        Detect all deadlock cycles in the current task system.

        Returns:
            List of detected deadlock cycles
        """
        async with self._lock:
            cycles = []
            visited_global = set()

            # Check each unvisited node for cycles
            for task_id in self.dependency_graph:
                if task_id not in visited_global:
                    cycle = self._detect_cycle_from_node(task_id, visited_global)
                    if cycle:
                        cycles.append(
                            DeadlockCycle(
                                task_ids=cycle,
                                cycle_length=len(cycle),
                                detected_at=datetime.now(UTC),
                                severity=self._assess_cycle_severity(cycle),
                            )
                        )

            if cycles:
                logger.warning(f"Detected {len(cycles)} deadlock cycles")

            return cycles

    def _detect_cycle_from_node(self, start_node: str, visited_global: set) -> list[str] | None:
        """Detect cycle starting from a specific node using DFS."""
        stack = []
        visited_local = set()

        def dfs(node: str) -> list[str] | None:
            if node in visited_local:
                # Found a cycle, extract it
                cycle_start = stack.index(node)
                return stack[cycle_start:] + [node]

            if node in visited_global:
                return None

            visited_local.add(node)
            visited_global.add(node)
            stack.append(node)

            for neighbor in self.dependency_graph.get(node, []):
                result = dfs(neighbor)
                if result:
                    return result

            stack.pop()
            return None

        return dfs(start_node)

    def _assess_cycle_severity(self, cycle: list[str]) -> str:
        """Assess the severity of a deadlock cycle based on various factors."""
        cycle_length = len(cycle)
        blocked_tasks_in_cycle = sum(1 for task_id in cycle if task_id in self.blocked_tasks)

        if blocked_tasks_in_cycle >= len(cycle):
            return "critical"  # All tasks in cycle are blocked
        if cycle_length <= 2:
            return "high"  # Simple direct cycle
        if blocked_tasks_in_cycle > len(cycle) // 2:
            return "medium"  # More than half the cycle is blocked
        return "low"  # Potential future deadlock

    async def resolve_deadlock(self, cycle: DeadlockCycle) -> bool:
        """
        Attempt to resolve a deadlock by breaking the cycle.

        Args:
            cycle: Deadlock cycle to resolve

        Returns:
            True if deadlock was resolved, False if manual intervention needed
        """
        async with self._lock:
            logger.warning(f"Attempting to resolve deadlock cycle: {cycle.task_ids}")

            # Strategy 1: Find the weakest link to break
            weakest_dependency = self._find_weakest_dependency(cycle.task_ids)
            if weakest_dependency:
                from_task, to_task = weakest_dependency
                await self.remove_dependency(from_task, to_task)
                logger.info(f"Broke deadlock by removing dependency: {from_task} -> {to_task}")
                return True

            # Strategy 2: Cancel the most recently blocked task in the cycle
            most_recent_blocked = self._find_most_recent_blocked_task(cycle.task_ids)
            if most_recent_blocked:
                # This would need to be handled by the task manager
                logger.info(f"Recommended canceling task {most_recent_blocked} to break deadlock")
                return True

            # Strategy 3: Escalate to human intervention
            logger.error(f"Could not automatically resolve deadlock cycle: {cycle.task_ids}")
            await self._escalate_deadlock(cycle)
            return False

    def _find_weakest_dependency(self, cycle_tasks: list[str]) -> tuple[str, str] | None:
        """Find the weakest dependency link in the cycle to break."""
        # Look for dependencies where the target task is not blocked
        # or has the least number of dependents
        min_dependents = float("inf")
        weakest_link = None

        for i in range(len(cycle_tasks)):
            from_task = cycle_tasks[i]
            to_task = cycle_tasks[(i + 1) % len(cycle_tasks)]

            if to_task in self.dependency_graph[from_task]:
                # Count how many tasks depend on to_task
                dependent_count = len(self.reverse_graph.get(to_task, []))

                # Prefer non-blocked tasks
                if to_task not in self.blocked_tasks:
                    dependent_count -= 100  # Strong preference

                if dependent_count < min_dependents:
                    min_dependents = dependent_count
                    weakest_link = (from_task, to_task)

        return weakest_link

    def _find_most_recent_blocked_task(self, cycle_tasks: list[str]) -> str | None:
        """Find the most recently blocked task in the cycle."""
        most_recent_task = None
        most_recent_time = None

        for task_id in cycle_tasks:
            if task_id in self.blocked_tasks:
                blocked_info = self.blocked_tasks[task_id]
                if most_recent_time is None or blocked_info.blocked_at > most_recent_time:
                    most_recent_time = blocked_info.blocked_at
                    most_recent_task = task_id

        return most_recent_task

    async def _escalate_deadlock(self, cycle: DeadlockCycle) -> None:
        """Escalate deadlock to human intervention."""
        # Mark all tasks in cycle as escalated
        for task_id in cycle.task_ids:
            if task_id in self.blocked_tasks:
                self.blocked_tasks[task_id].escalated = True

        # Log detailed information for human review
        logger.critical(f"DEADLOCK ESCALATION REQUIRED: Cycle {cycle.task_ids}")
        logger.critical(f"Cycle severity: {cycle.severity}")
        logger.critical(f"Cycle detected at: {cycle.detected_at}")

        # In a real system, this would trigger alerts, notifications, etc.

    async def check_timeout_violations(self) -> list[str]:
        """
        Check for tasks that have been blocked too long and need intervention.

        Returns:
            List of task IDs that have exceeded timeout thresholds
        """
        now = datetime.now(UTC)
        violations = []

        for task_id, blocked_info in self.blocked_tasks.items():
            time_blocked = now - blocked_info.blocked_at

            if time_blocked > self.max_block_duration:
                violations.append(task_id)
                logger.error(f"Task {task_id} blocked for {time_blocked}, exceeds maximum {self.max_block_duration}")
            elif time_blocked > self.escalation_threshold and not blocked_info.escalated:
                # Mark for escalation
                blocked_info.escalated = True
                logger.warning(f"Task {task_id} blocked for {time_blocked}, escalating")

        return violations

    async def get_deadlock_stats(self) -> dict:
        """Get current deadlock prevention system statistics."""
        cycles = await self.detect_deadlocks()
        now = datetime.now(UTC)

        escalated_count = sum(1 for info in self.blocked_tasks.values() if info.escalated)
        overdue_count = sum(
            1 for info in self.blocked_tasks.values() if (now - info.blocked_at) > self.max_block_duration
        )

        return {
            "total_dependencies": sum(len(deps) for deps in self.dependency_graph.values()),
            "blocked_tasks": len(self.blocked_tasks),
            "active_deadlocks": len(cycles),
            "escalated_tasks": escalated_count,
            "overdue_tasks": overdue_count,
            "max_dependency_depth": max(
                (self._calculate_dependency_depth(task_id) for task_id in self.dependency_graph), default=0
            ),
        }


# Global deadlock prevention instance
deadlock_protocol = DeadlockPreventionProtocol()
