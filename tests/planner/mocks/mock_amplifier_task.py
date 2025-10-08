"""
Mock implementation of amplifier's Task tool for testing super-planner integration.

This mock simulates the behavior of spawning sub-agents via amplifier's Task tool,
allowing tests to run without requiring the full amplifier environment.
"""

import asyncio
import json
import uuid
from dataclasses import asdict
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class MockTaskResult:
    """Mock result from a Task tool execution"""

    task_id: str
    agent_name: str
    status: str  # "started", "completed", "failed"
    output: dict[str, Any]
    execution_time: float
    created_at: str


@dataclass
class MockAgent:
    """Mock agent instance spawned by Task tool"""

    agent_id: str
    name: str
    capabilities: list[str]
    status: str  # "starting", "active", "idle", "failed", "stopped"
    current_task: str | None
    tasks_completed: int
    start_time: str
    last_heartbeat: str


class MockAmplifierTaskTool:
    """
    Mock implementation of amplifier's Task tool.

    Simulates spawning and managing sub-agents for task execution.
    This mock allows testing the super-planner's agent coordination
    without requiring the full amplifier environment.
    """

    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.agents: dict[str, MockAgent] = {}
        self.task_results: dict[str, MockTaskResult] = {}
        self.execution_delay = 0.1  # Simulate brief execution time
        self.failure_rate = 0.0  # Configurable failure rate for testing

        # Mock agent capabilities available for assignment
        self.available_agent_types = {
            "python-dev": ["python", "fastapi", "sqlalchemy", "pytest"],
            "typescript-dev": ["typescript", "react", "nodejs", "jest"],
            "devops": ["docker", "kubernetes", "terraform", "ci-cd"],
            "qa": ["testing", "automation", "selenium", "performance"],
            "data": ["python", "pandas", "sql", "analytics"],
            "security": ["security", "oauth", "encryption", "compliance"],
            "mobile": ["react-native", "ios", "android", "mobile-ui"],
            "designer": ["ui-ux", "figma", "design-systems", "accessibility"],
        }

    async def spawn_agent(self, agent_type: str, task_description: str, capabilities_required: list[str]) -> str:
        """
        Mock spawning of a sub-agent via amplifier Task tool.

        Args:
            agent_type: Type of agent to spawn
            task_description: Description of work to be done
            capabilities_required: Required capabilities for the task

        Returns:
            agent_id: Unique identifier for the spawned agent
        """
        agent_id = str(uuid.uuid4())

        # Simulate agent startup time
        await asyncio.sleep(self.execution_delay)

        # Check if this agent type exists
        if agent_type not in self.available_agent_types:
            raise ValueError(f"Unknown agent type: {agent_type}")

        # Create mock agent instance
        agent = MockAgent(
            agent_id=agent_id,
            name=f"{agent_type}-{agent_id[:8]}",
            capabilities=self.available_agent_types[agent_type],
            status="starting",
            current_task=None,
            tasks_completed=0,
            start_time=datetime.now(UTC).isoformat(),
            last_heartbeat=datetime.now(UTC).isoformat(),
        )

        # Simulate occasional startup failures
        if self._should_fail():
            agent.status = "failed"
            self.agents[agent_id] = agent
            raise RuntimeError(f"Failed to start agent {agent_type}: simulated failure")

        agent.status = "active"
        self.agents[agent_id] = agent

        # Log agent creation for test verification
        self._log_agent_event(
            agent_id,
            "spawned",
            {
                "agent_type": agent_type,
                "task_description": task_description,
                "capabilities_required": capabilities_required,
            },
        )

        return agent_id

    async def assign_task_to_agent(self, agent_id: str, task_id: str, task_data: dict[str, Any]) -> bool:
        """
        Mock task assignment to a spawned agent.

        Args:
            agent_id: ID of agent to assign task to
            task_id: ID of task being assigned
            task_data: Task data and requirements

        Returns:
            bool: True if assignment successful
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")

        agent = self.agents[agent_id]

        # Check if agent is available
        if agent.status not in ["active", "idle"]:
            return False

        if agent.current_task is not None:
            return False  # Agent already busy

        # Assign task
        agent.current_task = task_id
        agent.status = "active"
        agent.last_heartbeat = datetime.now(UTC).isoformat()

        # Log task assignment
        self._log_agent_event(
            agent_id, "task_assigned", {"task_id": task_id, "task_name": task_data.get("name", "Unknown")}
        )

        # Start background task execution simulation
        asyncio.create_task(self._simulate_task_execution(agent_id, task_id, task_data))

        return True

    async def get_agent_status(self, agent_id: str) -> dict[str, Any] | None:
        """Get current status of an agent."""
        if agent_id not in self.agents:
            return None

        agent = self.agents[agent_id]
        return {
            "agent_id": agent_id,
            "name": agent.name,
            "status": agent.status,
            "current_task": agent.current_task,
            "tasks_completed": agent.tasks_completed,
            "last_heartbeat": agent.last_heartbeat,
        }

    async def get_task_result(self, task_id: str) -> MockTaskResult | None:
        """Get result of a completed task."""
        return self.task_results.get(task_id)

    async def stop_agent(self, agent_id: str) -> bool:
        """Stop a running agent."""
        if agent_id not in self.agents:
            return False

        agent = self.agents[agent_id]
        agent.status = "stopped"
        agent.current_task = None

        self._log_agent_event(agent_id, "stopped", {})
        return True

    async def list_agents(self) -> list[dict[str, Any]]:
        """List all agents and their current status."""
        return [asdict(agent) for agent in self.agents.values()]

    def configure_failure_rate(self, failure_rate: float):
        """Configure simulated failure rate for testing (0.0 to 1.0)."""
        self.failure_rate = max(0.0, min(1.0, failure_rate))

    def configure_execution_delay(self, delay: float):
        """Configure simulated execution delay in seconds."""
        self.execution_delay = max(0.0, delay)

    async def _simulate_task_execution(self, agent_id: str, task_id: str, task_data: dict[str, Any]):
        """Simulate agent executing a task in the background."""
        agent = self.agents[agent_id]
        start_time = datetime.now(UTC)

        try:
            # Simulate work time based on task complexity
            work_time = self._estimate_work_time(task_data)
            await asyncio.sleep(work_time)

            # Simulate occasional task failures
            if self._should_fail():
                raise RuntimeError("Simulated task execution failure")

            # Task completed successfully
            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            result = MockTaskResult(
                task_id=task_id,
                agent_name=agent.name,
                status="completed",
                output={
                    "success": True,
                    "files_modified": self._generate_mock_file_changes(task_data),
                    "tests_passed": True,
                    "commits_created": 1,
                },
                execution_time=execution_time,
                created_at=datetime.now(UTC).isoformat(),
            )

            # Update agent status
            agent.current_task = None
            agent.status = "idle"
            agent.tasks_completed += 1
            agent.last_heartbeat = datetime.now(UTC).isoformat()

            # Store result
            self.task_results[task_id] = result

            self._log_agent_event(agent_id, "task_completed", {"task_id": task_id, "execution_time": execution_time})

        except Exception as e:
            # Task failed
            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            result = MockTaskResult(
                task_id=task_id,
                agent_name=agent.name,
                status="failed",
                output={"success": False, "error": str(e), "partial_work": True},
                execution_time=execution_time,
                created_at=datetime.now(UTC).isoformat(),
            )

            # Update agent status
            agent.current_task = None
            agent.status = "idle"  # Agent can retry other tasks
            agent.last_heartbeat = datetime.now(UTC).isoformat()

            # Store result
            self.task_results[task_id] = result

            self._log_agent_event(
                agent_id, "task_failed", {"task_id": task_id, "error": str(e), "execution_time": execution_time}
            )

    def _estimate_work_time(self, task_data: dict[str, Any]) -> float:
        """Estimate work time based on task complexity."""
        base_time = 0.5  # Base execution time

        # Factor in estimated effort
        effort = task_data.get("estimated_effort", 5)
        effort_factor = min(effort / 10.0, 2.0)  # Cap at 2x base time

        # Add some randomness
        import random

        random_factor = random.uniform(0.8, 1.2)

        return base_time * effort_factor * random_factor

    def _generate_mock_file_changes(self, task_data: dict[str, Any]) -> list[str]:
        """Generate mock file changes for task completion."""
        task_name = task_data.get("name", "task")
        component = task_data.get("metadata", {}).get("component", "main")

        # Generate realistic file paths based on task type
        files = [
            f"src/{component}/{task_name.lower().replace(' ', '_')}.py",
            f"tests/test_{component}_{task_name.lower().replace(' ', '_')}.py",
        ]

        return files

    def _should_fail(self) -> bool:
        """Determine if this operation should fail based on configured failure rate."""
        import random

        return random.random() < self.failure_rate

    def _log_agent_event(self, agent_id: str, event_type: str, data: dict[str, Any]):
        """Log agent events for test verification."""
        log_file = self.temp_dir / "mock_agent_events.jsonl"

        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "agent_id": agent_id,
            "event_type": event_type,
            "data": data,
        }

        with open(log_file, "a") as f:
            f.write(json.dumps(event) + "\n")


# Test fixtures and helpers
def create_mock_task_tool(temp_dir: Path, **config) -> MockAmplifierTaskTool:
    """Create configured mock Task tool for testing."""
    mock = MockAmplifierTaskTool(temp_dir)

    # Apply configuration
    if "failure_rate" in config:
        mock.configure_failure_rate(config["failure_rate"])

    if "execution_delay" in config:
        mock.configure_execution_delay(config["execution_delay"])

    return mock


async def simulate_realistic_agent_work(
    mock_tool: MockAmplifierTaskTool, tasks: list[dict[str, Any]]
) -> list[MockTaskResult]:
    """
    Simulate realistic multi-agent work on a set of tasks.

    This helper spawns appropriate agents and assigns tasks based on
    capabilities, simulating a realistic super-planner workflow.
    """
    results = []

    # Group tasks by required capabilities
    capability_groups = {}
    for task in tasks:
        caps = tuple(sorted(task.get("capabilities_required", [])))
        if caps not in capability_groups:
            capability_groups[caps] = []
        capability_groups[caps].append(task)

    # Spawn agents for each capability group
    agents = []
    for capabilities in capability_groups:
        # Find appropriate agent type
        agent_type = find_best_agent_type(list(capabilities), mock_tool.available_agent_types)
        if agent_type:
            agent_id = await mock_tool.spawn_agent(
                agent_type=agent_type,
                task_description=f"Handle tasks requiring {capabilities}",
                capabilities_required=list(capabilities),
            )
            agents.append((agent_id, capabilities))

    # Assign and execute tasks
    for (agent_id, _capabilities), task_list in zip(agents, capability_groups.values(), strict=False):
        for task in task_list:
            await mock_tool.assign_task_to_agent(agent_id, task["id"], task)

    # Wait for all tasks to complete
    await wait_for_all_tasks_complete(mock_tool, [t["id"] for t in tasks])

    # Collect results
    for task in tasks:
        result = await mock_tool.get_task_result(task["id"])
        if result:
            results.append(result)

    return results


def find_best_agent_type(required_caps: list[str], available_types: dict[str, list[str]]) -> str | None:
    """Find the agent type that best matches required capabilities."""
    best_match = None
    best_score = 0

    for agent_type, agent_caps in available_types.items():
        # Count how many required capabilities this agent has
        matches = len(set(required_caps) & set(agent_caps))
        if matches > best_score:
            best_score = matches
            best_match = agent_type

    return best_match


async def wait_for_all_tasks_complete(mock_tool: MockAmplifierTaskTool, task_ids: list[str], timeout: float = 30.0):
    """Wait for all tasks to complete or timeout."""
    start_time = datetime.now()

    while (datetime.now() - start_time).total_seconds() < timeout:
        all_complete = True

        for task_id in task_ids:
            result = await mock_tool.get_task_result(task_id)
            if result is None:
                all_complete = False
                break

        if all_complete:
            return

        await asyncio.sleep(0.1)

    raise TimeoutError(f"Tasks did not complete within {timeout} seconds")
