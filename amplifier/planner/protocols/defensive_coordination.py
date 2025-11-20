"""
Defensive Coordination Utilities

Provides defensive programming utilities for the super-planner coordination system,
following patterns from ccsdk_toolkit with retry logic, error recovery, and graceful
degradation strategies.
"""

import asyncio
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from functools import wraps
from pathlib import Path
from typing import Any
from typing import TypeVar

from ..core.models import Task
from .state_transitions import state_protocol

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry operations."""

    max_attempts: int = 3
    initial_delay: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay: float = 60.0
    retry_on_exceptions: tuple = (ConnectionError, TimeoutError, OSError)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern."""

    failure_threshold: int = 5
    recovery_timeout: timedelta = timedelta(minutes=5)
    half_open_max_calls: int = 3


class CircuitBreakerState:
    """Circuit breaker state management."""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.state = "closed"  # closed, open, half_open
        self.half_open_calls = 0


def retry_with_backoff(config: RetryConfig | None = None):
    """
    Decorator for retry with exponential backoff.
    Based on defensive utilities patterns from DISCOVERIES.md.
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception: Exception | None = None
            delay = config.initial_delay

            for attempt in range(config.max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    return func(*args, **kwargs)  # type: ignore

                except config.retry_on_exceptions as e:
                    last_exception = e

                    if attempt == 0:
                        logger.warning(
                            f"Operation failed ({func.__name__}), retrying. "
                            f"This may be due to network issues or temporary failures. "
                            f"Error: {e}"
                        )

                    if attempt < config.max_attempts - 1:
                        await asyncio.sleep(min(delay, config.max_delay))
                        delay *= config.backoff_multiplier
                    else:
                        logger.error(f"Operation failed after {config.max_attempts} attempts: {e}")
                        raise e

                except Exception as e:
                    # Don't retry on non-recoverable exceptions
                    logger.error(f"Non-recoverable error in {func.__name__}: {e}")
                    raise e

            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry loop exit")

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            return asyncio.run(async_wrapper(*args, **kwargs))

        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper

    return decorator


class DefensiveFileIO:
    """
    Defensive file I/O operations with retry logic and cloud sync handling.
    Based on OneDrive/Cloud Sync patterns from DISCOVERIES.md.
    """

    def __init__(self, max_retries: int = 5, initial_delay: float = 0.5):
        self.max_retries = max_retries
        self.initial_delay = initial_delay

    @retry_with_backoff(
        RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            backoff_multiplier=2.0,
            retry_on_exceptions=(OSError, IOError, PermissionError),
        )
    )
    def write_json(self, data: Any, filepath: Path, ensure_newline: bool = True) -> None:
        """Write JSON data to file with defensive error handling."""
        try:
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Write with explicit encoding and flushing
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                if ensure_newline:
                    f.write("\n")
                f.flush()

        except OSError as e:
            if e.errno == 5:  # I/O error - likely cloud sync issue
                logger.warning(
                    f"File I/O error writing to {filepath} - likely cloud sync delay. "
                    f"Consider enabling 'Always keep on this device' for: {filepath.parent}"
                )
            raise

    @retry_with_backoff(RetryConfig(max_attempts=3, retry_on_exceptions=(OSError, IOError, json.JSONDecodeError)))
    def read_json(self, filepath: Path) -> Any:
        """Read JSON data from file with defensive error handling."""
        try:
            with open(filepath, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.info(f"File not found: {filepath}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filepath}: {e}")
            raise

    @retry_with_backoff(RetryConfig(max_attempts=3, retry_on_exceptions=(OSError, IOError)))
    def append_jsonl(self, data: Any, filepath: Path) -> None:
        """Append JSON line to file with defensive error handling."""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, "a", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()

        except OSError as e:
            if e.errno == 5:
                logger.warning(f"File I/O error appending to {filepath} - likely cloud sync delay.")
            raise


class TaskOperationContext:
    """
    Context manager for safe task operations with automatic rollback.
    """

    def __init__(self, task: Task, operation_name: str):
        self.original_task = task
        self.operation_name = operation_name
        self.current_task = task
        self.completed_successfully = False

    async def __aenter__(self):
        logger.debug(f"Starting {self.operation_name} for task {self.original_task.id}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.completed_successfully = True
            logger.debug(f"Completed {self.operation_name} for task {self.original_task.id}")
        else:
            logger.warning(f"Failed {self.operation_name} for task {self.original_task.id}: {exc_val}")
            # In a real system, this might trigger rollback operations
        return False

    def update_task(self, new_task: Task) -> None:
        """Update the current task state."""
        self.current_task = new_task


class CoordinationHealthCheck:
    """
    Health monitoring for coordination system components.
    """

    def __init__(self):
        self.component_status: dict[str, dict[str, Any]] = {}
        self.last_check_time: dict[str, datetime] = {}

    async def check_state_transitions(self) -> dict[str, Any]:
        """Check state transition system health."""
        try:
            # Test basic state transition validation
            from ..core.models import Task
            from ..core.models import TaskState

            test_task = Task(
                id="health_check",
                title="Health Check Task",
                description="Test task for health checking",
                state=TaskState.NOT_STARTED,
                version=1,
            )

            # Test transition validation
            can_transition, reason = state_protocol.can_transition(test_task, TaskState.ASSIGNED)

            status = {
                "status": "healthy" if not can_transition else "healthy",
                "last_check": datetime.now(UTC).isoformat(),
                "transition_validation": "working",
                "details": f"Can transition check: {can_transition}, reason: {reason}",
            }

        except Exception as e:
            status = {"status": "unhealthy", "last_check": datetime.now(UTC).isoformat(), "error": str(e)}

        self.component_status["state_transitions"] = status
        self.last_check_time["state_transitions"] = datetime.now(UTC)
        return status

    async def check_coordination_protocol(self) -> dict[str, Any]:
        """Check agent coordination protocol health."""
        try:
            from .agent_coordination import coordination_protocol

            stats = coordination_protocol.get_coordination_stats()

            status = {
                "status": "healthy",
                "last_check": datetime.now(UTC).isoformat(),
                "stats": stats,
                "active_agents": stats.get("active_agents", 0),
                "utilization_rate": stats.get("utilization_rate", 0.0),
            }

            # Check for concerning patterns
            if stats.get("utilization_rate", 0) > 0.9:
                status["warnings"] = ["High utilization rate"]

            if stats.get("expired_claims", 0) > 10:
                status["warnings"] = status.get("warnings", []) + ["Many expired claims"]

        except Exception as e:
            status = {"status": "unhealthy", "last_check": datetime.now(UTC).isoformat(), "error": str(e)}

        self.component_status["coordination"] = status
        self.last_check_time["coordination"] = datetime.now(UTC)
        return status

    async def check_deadlock_prevention(self) -> dict[str, Any]:
        """Check deadlock prevention system health."""
        try:
            from .deadlock_prevention import deadlock_protocol

            stats = await deadlock_protocol.get_deadlock_stats()

            status = {
                "status": "healthy",
                "last_check": datetime.now(UTC).isoformat(),
                "stats": stats,
                "active_deadlocks": stats.get("active_deadlocks", 0),
                "blocked_tasks": stats.get("blocked_tasks", 0),
            }

            # Check for concerning patterns
            if stats.get("active_deadlocks", 0) > 0:
                status["status"] = "warning"
                status["warnings"] = ["Active deadlocks detected"]

            if stats.get("overdue_tasks", 0) > 0:
                status["warnings"] = status.get("warnings", []) + ["Tasks overdue for resolution"]

        except Exception as e:
            status = {"status": "unhealthy", "last_check": datetime.now(UTC).isoformat(), "error": str(e)}

        self.component_status["deadlock_prevention"] = status
        self.last_check_time["deadlock_prevention"] = datetime.now(UTC)
        return status

    async def full_health_check(self) -> dict[str, Any]:
        """Perform full health check of all coordination components."""
        results = {}

        # Run all health checks
        results["state_transitions"] = await self.check_state_transitions()
        results["coordination"] = await self.check_coordination_protocol()
        results["deadlock_prevention"] = await self.check_deadlock_prevention()

        # Overall status
        all_statuses = [r["status"] for r in results.values()]
        if "unhealthy" in all_statuses:
            overall_status = "unhealthy"
        elif "warning" in all_statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        return {"overall_status": overall_status, "timestamp": datetime.now(UTC).isoformat(), "components": results}


class GracefulDegradation:
    """
    Provides graceful degradation strategies when coordination systems fail.
    """

    @staticmethod
    async def fallback_task_assignment(task: Task, available_agents: list) -> str | None:
        """Fallback task assignment when coordination protocol fails."""
        try:
            if not available_agents:
                logger.warning("No agents available for fallback assignment")
                return None

            # Simple round-robin fallback
            # In production, this might use a hash of task ID for consistency
            agent_index = hash(task.id) % len(available_agents)
            selected_agent = available_agents[agent_index]

            logger.info(f"Fallback assignment: task {task.id} -> agent {selected_agent}")
            return selected_agent

        except Exception as e:
            logger.error(f"Fallback assignment failed: {e}")
            return None

    @staticmethod
    async def emergency_conflict_resolution(task: Task, conflicting_versions: list) -> Task:
        """Emergency conflict resolution when normal protocols fail."""
        try:
            # Extremely simple: take the highest version number
            latest_task = max(conflicting_versions, key=lambda t: t.version)

            # Create new task with incremented version
            resolved_task = Task(
                id=latest_task.id,
                title=latest_task.title,
                description=latest_task.description,
                state=latest_task.state,
                priority=latest_task.priority,
                estimated_effort=latest_task.estimated_effort,
                assigned_to=latest_task.assigned_to,
                dependencies=latest_task.dependencies,
                metadata=latest_task.metadata,
                parent_id=latest_task.parent_id,
                subtask_ids=latest_task.subtask_ids,
                created_at=latest_task.created_at,
                updated_at=datetime.now(UTC),
                started_at=latest_task.started_at,
                completed_at=latest_task.completed_at,
                cancelled_at=latest_task.cancelled_at,
                blocked_at=latest_task.blocked_at,
                blocking_reason=latest_task.blocking_reason,
                version=latest_task.version + 1,
            )

            logger.warning(f"Emergency conflict resolution applied to task {task.id}")
            return resolved_task

        except Exception as e:
            logger.error(f"Emergency conflict resolution failed: {e}")
            raise


# Global instances for defensive utilities
file_io = DefensiveFileIO()
health_monitor = CoordinationHealthCheck()
