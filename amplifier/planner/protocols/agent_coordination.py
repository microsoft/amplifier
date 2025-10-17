"""
Multi-Agent Coordination Protocol

Manages task claiming, agent registration, load balancing, and resource contention
for the super-planner system. Ensures fair task distribution and prevents conflicts
between concurrent agents.
"""

import asyncio
import logging
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from datetime import timedelta

from ..core.models import Task

logger = logging.getLogger(__name__)


class ClaimError(Exception):
    """Raised when a task claim operation fails."""

    def __init__(self, message: str = "Task claim operation failed") -> None:
        super().__init__(message)


class LoadBalancingError(Exception):
    """Raised when load balancing constraints are violated."""

    def __init__(self, message: str = "Load balancing constraint violated") -> None:
        super().__init__(message)


@dataclass
class AgentInfo:
    """Information about a registered agent."""

    agent_id: str
    capabilities: set[str] = field(default_factory=set)
    max_concurrent_tasks: int = 3
    current_task_count: int = 0
    last_heartbeat: datetime | None = None
    is_active: bool = True


@dataclass
class TaskClaim:
    """Represents a claimed task with lease information."""

    task_id: str
    agent_id: str
    claimed_at: datetime
    lease_expires_at: datetime
    claim_version: int


class AgentCoordinationProtocol:
    """
    Manages coordination between multiple agents working on tasks.
    Handles claiming, load balancing, and resource contention.
    """

    def __init__(self, default_lease_duration: timedelta = timedelta(hours=1)):
        self.agents: dict[str, AgentInfo] = {}
        self.task_claims: dict[str, TaskClaim] = {}
        self.default_lease_duration = default_lease_duration
        self.heartbeat_timeout = timedelta(minutes=5)
        self._lock = asyncio.Lock()

    async def register_agent(self, agent_id: str, capabilities: set[str], max_concurrent_tasks: int = 3) -> None:
        """Register a new agent with the coordination system."""
        async with self._lock:
            self.agents[agent_id] = AgentInfo(
                agent_id=agent_id,
                capabilities=capabilities,
                max_concurrent_tasks=max_concurrent_tasks,
                last_heartbeat=datetime.now(UTC),
                is_active=True,
            )
            logger.info(f"Agent {agent_id} registered with capabilities: {capabilities}")

    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent and release its claimed tasks."""
        async with self._lock:
            if agent_id not in self.agents:
                return

            # Release all tasks claimed by this agent
            tasks_to_release = [task_id for task_id, claim in self.task_claims.items() if claim.agent_id == agent_id]

            for task_id in tasks_to_release:
                del self.task_claims[task_id]
                logger.info(f"Released task {task_id} from unregistered agent {agent_id}")

            del self.agents[agent_id]
            logger.info(f"Agent {agent_id} unregistered")

    async def heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat. Returns True if agent is still registered."""
        async with self._lock:
            if agent_id in self.agents:
                self.agents[agent_id].last_heartbeat = datetime.now(UTC)
                self.agents[agent_id].is_active = True
                return True
            return False

    async def claim_task(self, task_id: str, agent_id: str, expected_task_version: int | None = None) -> TaskClaim:
        """
        Attempt to claim a task for an agent.

        Args:
            task_id: ID of task to claim
            agent_id: ID of claiming agent
            expected_task_version: Expected task version for optimistic locking

        Returns:
            TaskClaim object if successful

        Raises:
            ClaimError: If claim fails due to conflicts or constraints
        """
        async with self._lock:
            # Check if agent is registered and active
            if agent_id not in self.agents:
                raise ClaimError(f"Agent {agent_id} not registered")

            agent = self.agents[agent_id]
            if not agent.is_active:
                raise ClaimError(f"Agent {agent_id} is inactive")

            # Check if task is already claimed
            if task_id in self.task_claims:
                existing_claim = self.task_claims[task_id]
                if existing_claim.lease_expires_at > datetime.now(UTC):
                    raise ClaimError(f"Task {task_id} already claimed by agent {existing_claim.agent_id}")
                # Claim has expired, remove it
                del self.task_claims[task_id]

            # Check agent's concurrent task limit
            if agent.current_task_count >= agent.max_concurrent_tasks:
                raise ClaimError(f"Agent {agent_id} at max concurrent tasks ({agent.max_concurrent_tasks})")

            # Create claim
            claim = TaskClaim(
                task_id=task_id,
                agent_id=agent_id,
                claimed_at=datetime.now(UTC),
                lease_expires_at=datetime.now(UTC) + self.default_lease_duration,
                claim_version=expected_task_version or 0,
            )

            # Store claim and update agent stats
            self.task_claims[task_id] = claim
            agent.current_task_count += 1

            logger.info(f"Task {task_id} claimed by agent {agent_id}")
            return claim

    async def release_task(self, task_id: str, agent_id: str) -> bool:
        """
        Release a claimed task.

        Args:
            task_id: ID of task to release
            agent_id: ID of agent releasing the task

        Returns:
            True if task was released, False if not claimed by this agent
        """
        async with self._lock:
            if task_id not in self.task_claims:
                return False

            claim = self.task_claims[task_id]
            if claim.agent_id != agent_id:
                logger.warning(f"Agent {agent_id} tried to release task {task_id} claimed by {claim.agent_id}")
                return False

            # Remove claim and update agent stats
            del self.task_claims[task_id]
            if agent_id in self.agents:
                self.agents[agent_id].current_task_count = max(0, self.agents[agent_id].current_task_count - 1)

            logger.info(f"Task {task_id} released by agent {agent_id}")
            return True

    async def renew_claim(self, task_id: str, agent_id: str) -> bool:
        """
        Renew a task claim to extend the lease.

        Args:
            task_id: ID of task to renew
            agent_id: ID of agent renewing the claim

        Returns:
            True if renewal successful, False otherwise
        """
        async with self._lock:
            if task_id not in self.task_claims:
                return False

            claim = self.task_claims[task_id]
            if claim.agent_id != agent_id:
                return False

            # Extend the lease
            claim.lease_expires_at = datetime.now(UTC) + self.default_lease_duration
            logger.info(f"Task {task_id} claim renewed by agent {agent_id}")
            return True

    def get_available_agents(self, required_capabilities: set[str] | None = None) -> list[AgentInfo]:
        """
        Get list of agents available for new tasks.

        Args:
            required_capabilities: Optional set of required capabilities

        Returns:
            List of available agents, sorted by current load
        """
        now = datetime.now(UTC)
        available_agents = []

        for agent in self.agents.values():
            # Check if agent is active and within heartbeat timeout
            if not agent.is_active:
                continue

            if agent.last_heartbeat and (now - agent.last_heartbeat) > self.heartbeat_timeout:
                continue

            # Check if agent has capacity
            if agent.current_task_count >= agent.max_concurrent_tasks:
                continue

            # Check capabilities if required
            if required_capabilities and not required_capabilities.issubset(agent.capabilities):
                continue

            available_agents.append(agent)

        # Sort by current load (ascending)
        available_agents.sort(key=lambda a: a.current_task_count)
        return available_agents

    def select_best_agent(self, task: Task) -> str | None:
        """
        Select the best agent for a given task using load balancing.

        Args:
            task: Task to assign

        Returns:
            Agent ID of best candidate, or None if no suitable agent available
        """
        # Extract required capabilities from task metadata
        required_capabilities = set()
        if task.metadata and "required_capabilities" in task.metadata:
            required_capabilities = set(task.metadata["required_capabilities"])

        available_agents = self.get_available_agents(required_capabilities)
        if not available_agents:
            return None

        # Simple load balancing: pick agent with lowest current load
        return available_agents[0].agent_id

    async def cleanup_expired_claims(self) -> int:
        """
        Clean up expired task claims.

        Returns:
            Number of claims cleaned up
        """
        async with self._lock:
            now = datetime.now(UTC)
            expired_claims = []

            for task_id, claim in self.task_claims.items():
                if claim.lease_expires_at <= now:
                    expired_claims.append(task_id)

            # Remove expired claims and update agent stats
            for task_id in expired_claims:
                claim = self.task_claims[task_id]
                del self.task_claims[task_id]

                if claim.agent_id in self.agents:
                    self.agents[claim.agent_id].current_task_count = max(
                        0, self.agents[claim.agent_id].current_task_count - 1
                    )

                logger.info(f"Expired claim for task {task_id} by agent {claim.agent_id}")

            return len(expired_claims)

    async def cleanup_inactive_agents(self) -> int:
        """
        Clean up agents that haven't sent heartbeats recently.

        Returns:
            Number of agents cleaned up
        """
        now = datetime.now(UTC)
        inactive_agents = []

        for agent_id, agent in self.agents.items():
            if agent.last_heartbeat and (now - agent.last_heartbeat) > self.heartbeat_timeout:
                inactive_agents.append(agent_id)

        for agent_id in inactive_agents:
            await self.unregister_agent(agent_id)

        return len(inactive_agents)

    def get_coordination_stats(self) -> dict:
        """Get current coordination system statistics."""
        now = datetime.now(UTC)
        active_agents = sum(1 for a in self.agents.values() if a.is_active)
        total_capacity = sum(a.max_concurrent_tasks for a in self.agents.values())
        used_capacity = sum(a.current_task_count for a in self.agents.values())
        active_claims = sum(1 for c in self.task_claims.values() if c.lease_expires_at > now)

        return {
            "total_agents": len(self.agents),
            "active_agents": active_agents,
            "total_capacity": total_capacity,
            "used_capacity": used_capacity,
            "utilization_rate": used_capacity / max(total_capacity, 1),
            "active_claims": active_claims,
            "expired_claims": len(self.task_claims) - active_claims,
        }


# Global coordination instance
coordination_protocol = AgentCoordinationProtocol()
