"""
Integration tests for Amplifier v2 System

Tests the complete integration between:
- Core kernel and module loading
- Message bus event routing
- LLM provider registration and calls
- Philosophy injection into prompts
- Tool registration and execution
- Agent registry management
- End-to-end workflows

These are integration tests, not unit tests - they verify components work together.
"""

import asyncio
import logging
from typing import Any, Dict, List
from pathlib import Path
import sys

# Add parent dirs to path for imports
test_dir = Path(__file__).parent
repos_dir = test_dir.parent / "repos"
sys.path.insert(0, str(repos_dir / "amplifier-core"))

import pytest
from amplifier_core.kernel import Kernel
from amplifier_core.message_bus import Event, MessageBus
from amplifier_core.plugin import AmplifierModule
from amplifier_core.interfaces.model import BaseModelProvider
from amplifier_core.interfaces.tool import BaseTool

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Test fixtures and mock implementations

class MockModelProvider(BaseModelProvider):
    """Mock LLM provider for testing."""

    def __init__(self, name: str = "mock-gpt"):
        self.name = name
        self.calls: List[Dict[str, Any]] = []

    async def generate(self, prompt: str, *, system: str | None = None, **kwargs: Any) -> str:
        """Track calls and return test response."""
        self.calls.append({
            "prompt": prompt,
            "system": system,
            "kwargs": kwargs
        })
        return f"Mock response to: {prompt[:50]}..."

    def get_config(self) -> dict[str, Any]:
        """Return mock configuration."""
        return {
            "provider": self.name,
            "model": "test-model",
            "max_tokens": 1000
        }


class MockTool(BaseTool):
    """Mock tool for testing."""

    def __init__(self, tool_name: str = "mock-tool"):
        self._name = tool_name
        self.executions: List[Dict[str, Any]] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"Mock tool: {self._name}"

    async def run(self, **kwargs: Any) -> dict[str, Any]:
        """Track executions and return test result."""
        self.executions.append(kwargs)
        return {
            "status": "success",
            "tool": self._name,
            "input": kwargs,
            "output": f"Processed by {self._name}"
        }


class TestModule(AmplifierModule):
    """Test module that registers providers and tools."""

    def __init__(self, kernel: Kernel):
        super().__init__(kernel)
        self.initialized = False
        self.shutdown_called = False
        self.events_received: List[Event] = []

    async def initialize(self) -> None:
        """Initialize test module - register components and subscriptions."""
        # Register a mock model provider
        provider = MockModelProvider("test-provider")
        self.kernel.register_model_provider("test-provider", provider)

        # Register a mock tool
        tool = MockTool("test-tool")
        self.kernel.register_tool("test-tool", tool)

        # Subscribe to events
        self.kernel.message_bus.subscribe("test.event", self.handle_test_event)
        self.kernel.message_bus.subscribe("kernel.started", self.handle_kernel_started)

        self.initialized = True
        logger.info("TestModule initialized")

    async def handle_test_event(self, event: Event) -> None:
        """Handle test events."""
        self.events_received.append(event)
        logger.info(f"TestModule received event: {event.type}")

    async def handle_kernel_started(self, event: Event) -> None:
        """Handle kernel started event."""
        self.events_received.append(event)
        logger.info("TestModule: Kernel started!")

    async def shutdown(self) -> None:
        """Cleanup on shutdown."""
        self.shutdown_called = True
        logger.info("TestModule shutting down")


class PhilosophyTestModule(AmplifierModule):
    """Module to test philosophy injection."""

    def __init__(self, kernel: Kernel):
        super().__init__(kernel)
        self.philosophy_guidance = "\n\n[PHILOSOPHY: Always be helpful and concise.]"

    async def initialize(self) -> None:
        """Subscribe to prompt events for philosophy injection."""
        self.kernel.message_bus.subscribe(
            "prompt:before_send",
            self.inject_philosophy
        )
        logger.info("PhilosophyTestModule initialized")

    async def inject_philosophy(self, event: Event) -> None:
        """Inject philosophy into prompts."""
        if "prompt" in event.data:
            original_prompt = event.data["prompt"]
            event.data["prompt"] = original_prompt + self.philosophy_guidance
            event.data["philosophy_injected"] = True
            logger.info("Philosophy injected into prompt")


class AgentRegistryModule(AmplifierModule):
    """Module to test agent registry functionality."""

    def __init__(self, kernel: Kernel):
        super().__init__(kernel)
        self.agents: Dict[str, Dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Set up agent registry."""
        # Subscribe to agent-related events
        self.kernel.message_bus.subscribe("agent.register", self.register_agent)
        self.kernel.message_bus.subscribe("agent.list", self.list_agents)
        self.kernel.message_bus.subscribe("agent.execute", self.execute_agent)

        logger.info("AgentRegistryModule initialized")

    async def register_agent(self, event: Event) -> None:
        """Register a new agent."""
        agent_data = event.data
        agent_id = agent_data.get("id")
        if agent_id:
            self.agents[agent_id] = agent_data
            logger.info(f"Agent registered: {agent_id}")

            # Publish success event
            await self.kernel.message_bus.publish(Event(
                type="agent.registered",
                data={"id": agent_id, "status": "success"},
                source="agent-registry"
            ))

    async def list_agents(self, event: Event) -> None:
        """List all registered agents."""
        await self.kernel.message_bus.publish(Event(
            type="agent.list.response",
            data={"agents": list(self.agents.keys())},
            source="agent-registry"
        ))

    async def execute_agent(self, event: Event) -> None:
        """Execute an agent."""
        agent_id = event.data.get("id")
        if agent_id in self.agents:
            # Simulate agent execution
            result = {
                "agent_id": agent_id,
                "status": "completed",
                "result": f"Agent {agent_id} executed successfully"
            }

            await self.kernel.message_bus.publish(Event(
                type="agent.execution.complete",
                data=result,
                source="agent-registry"
            ))


# Integration Tests

@pytest.mark.asyncio
async def test_kernel_module_loading():
    """Test that kernel can load and initialize modules."""
    kernel = Kernel()

    # Manually add test module (simulating entry point discovery)
    test_module = TestModule(kernel)
    await test_module.initialize()
    kernel.modules.append(test_module)

    # Start kernel
    await kernel.start()

    # Verify module was initialized
    assert test_module.initialized
    assert len(test_module.events_received) > 0

    # Check kernel started event was received
    kernel_started_events = [
        e for e in test_module.events_received
        if e.type == "kernel.started"
    ]
    assert len(kernel_started_events) == 1

    # Shutdown
    await kernel.shutdown()
    assert test_module.shutdown_called


@pytest.mark.asyncio
async def test_message_bus_event_routing():
    """Test that message bus correctly routes events between modules."""
    kernel = Kernel()

    # Create two modules that communicate
    module1 = TestModule(kernel)
    module2 = TestModule(kernel)

    await module1.initialize()
    await module2.initialize()

    kernel.modules.extend([module1, module2])

    # Publish test event
    test_event = Event(
        type="test.event",
        data={"message": "Hello modules!"},
        source="test"
    )
    await kernel.message_bus.publish(test_event)

    # Both modules should receive the event
    assert len(module1.events_received) == 1
    assert len(module2.events_received) == 1
    assert module1.events_received[0].data["message"] == "Hello modules!"


@pytest.mark.asyncio
async def test_model_provider_registration():
    """Test LLM provider registration and retrieval."""
    kernel = Kernel()

    # Register providers
    provider1 = MockModelProvider("gpt-4")
    provider2 = MockModelProvider("claude")

    kernel.register_model_provider("gpt-4", provider1)
    kernel.register_model_provider("claude", provider2)

    # Retrieve and test providers
    retrieved_provider = kernel.get_model_provider("gpt-4")
    assert retrieved_provider is provider1

    # Test provider functionality
    response = await retrieved_provider.generate("Test prompt")
    assert "Mock response" in response
    assert len(provider1.calls) == 1
    assert provider1.calls[0]["prompt"] == "Test prompt"

    # Test missing provider
    assert kernel.get_model_provider("nonexistent") is None


@pytest.mark.asyncio
async def test_tool_registration_and_execution():
    """Test tool registration and execution."""
    kernel = Kernel()

    # Register tools
    tool1 = MockTool("calculator")
    tool2 = MockTool("web-search")

    kernel.register_tool("calculator", tool1)
    kernel.register_tool("web-search", tool2)

    # Retrieve and execute tool
    calc_tool = kernel.get_tool("calculator")
    assert calc_tool is tool1

    result = await calc_tool.run(operation="add", a=5, b=3)
    assert result["status"] == "success"
    assert result["tool"] == "calculator"
    assert len(tool1.executions) == 1
    assert tool1.executions[0]["operation"] == "add"


@pytest.mark.asyncio
async def test_philosophy_injection():
    """Test that philosophy can be injected into prompts."""
    kernel = Kernel()

    # Add philosophy module
    philosophy_module = PhilosophyTestModule(kernel)
    await philosophy_module.initialize()
    kernel.modules.append(philosophy_module)

    # Create event that triggers philosophy injection
    prompt_event = Event(
        type="prompt:before_send",
        data={"prompt": "What is 2+2?"},
        source="test"
    )

    # Publish event
    await kernel.message_bus.publish(prompt_event)

    # Check philosophy was injected
    assert "philosophy_injected" in prompt_event.data
    assert "[PHILOSOPHY:" in prompt_event.data["prompt"]
    assert "What is 2+2?" in prompt_event.data["prompt"]


@pytest.mark.asyncio
async def test_agent_registry():
    """Test agent registration and management."""
    kernel = Kernel()

    # Add agent registry module
    registry_module = AgentRegistryModule(kernel)
    await registry_module.initialize()
    kernel.modules.append(registry_module)

    # Track response events
    responses = []

    async def capture_response(event: Event):
        responses.append(event)

    kernel.message_bus.subscribe("agent.registered", capture_response)
    kernel.message_bus.subscribe("agent.list.response", capture_response)
    kernel.message_bus.subscribe("agent.execution.complete", capture_response)

    # Register an agent
    await kernel.message_bus.publish(Event(
        type="agent.register",
        data={
            "id": "test-agent",
            "name": "Test Agent",
            "capabilities": ["testing", "mocking"]
        },
        source="test"
    ))

    # Wait for async processing
    await asyncio.sleep(0.1)

    # Check registration response
    registration_responses = [r for r in responses if r.type == "agent.registered"]
    assert len(registration_responses) == 1
    assert registration_responses[0].data["id"] == "test-agent"

    # List agents
    await kernel.message_bus.publish(Event(
        type="agent.list",
        data={},
        source="test"
    ))

    await asyncio.sleep(0.1)

    # Check list response
    list_responses = [r for r in responses if r.type == "agent.list.response"]
    assert len(list_responses) == 1
    assert "test-agent" in list_responses[0].data["agents"]

    # Execute agent
    await kernel.message_bus.publish(Event(
        type="agent.execute",
        data={"id": "test-agent", "task": "run test"},
        source="test"
    ))

    await asyncio.sleep(0.1)

    # Check execution response
    exec_responses = [r for r in responses if r.type == "agent.execution.complete"]
    assert len(exec_responses) == 1
    assert exec_responses[0].data["agent_id"] == "test-agent"
    assert exec_responses[0].data["status"] == "completed"


@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test complete end-to-end workflow with multiple modules interacting."""
    kernel = Kernel()

    # Set up all modules
    test_module = TestModule(kernel)
    philosophy_module = PhilosophyTestModule(kernel)
    agent_registry = AgentRegistryModule(kernel)

    # Initialize modules
    await test_module.initialize()
    await philosophy_module.initialize()
    await agent_registry.initialize()

    kernel.modules.extend([test_module, philosophy_module, agent_registry])

    # Start kernel
    await kernel.start()

    # Workflow: Register agent -> Create prompt -> Execute tool -> Complete

    # Step 1: Register an AI agent
    await kernel.message_bus.publish(Event(
        type="agent.register",
        data={
            "id": "workflow-agent",
            "name": "Workflow Test Agent",
            "model_provider": "test-provider"
        },
        source="workflow"
    ))

    await asyncio.sleep(0.1)

    # Step 2: Prepare prompt with philosophy injection
    prompt_event = Event(
        type="prompt:before_send",
        data={"prompt": "Execute workflow task"},
        source="workflow"
    )
    await kernel.message_bus.publish(prompt_event)

    # Verify philosophy was injected
    assert "[PHILOSOPHY:" in prompt_event.data["prompt"]

    # Step 3: Get model provider and generate response
    provider = kernel.get_model_provider("test-provider")
    assert provider is not None

    response = await provider.generate(prompt_event.data["prompt"])
    assert "Mock response" in response

    # Step 4: Execute tool based on response
    tool = kernel.get_tool("test-tool")
    assert tool is not None

    tool_result = await tool.run(
        action="process",
        input=response
    )
    assert tool_result["status"] == "success"

    # Step 5: Execute agent with tool result
    execution_complete = []

    async def capture_execution(event: Event):
        execution_complete.append(event)

    kernel.message_bus.subscribe("agent.execution.complete", capture_execution)

    await kernel.message_bus.publish(Event(
        type="agent.execute",
        data={
            "id": "workflow-agent",
            "task": "process",
            "tool_result": tool_result
        },
        source="workflow"
    ))

    await asyncio.sleep(0.1)

    # Verify complete workflow
    assert len(execution_complete) == 1
    assert execution_complete[0].data["status"] == "completed"

    # Verify all components were used
    assert len(provider.calls) == 1  # Model was called
    assert len(tool.executions) == 1  # Tool was executed
    assert "workflow-agent" in agent_registry.agents  # Agent was registered

    # Shutdown
    await kernel.shutdown()
    assert test_module.shutdown_called


@pytest.mark.asyncio
async def test_concurrent_event_handling():
    """Test that message bus handles concurrent events correctly."""
    kernel = Kernel()

    # Track event processing
    processed_events = []
    processing_lock = asyncio.Lock()

    async def slow_handler(event: Event):
        """Handler that takes time to process."""
        await asyncio.sleep(0.1)  # Simulate processing time
        async with processing_lock:
            processed_events.append(event.data["id"])

    # Subscribe handler to event type
    kernel.message_bus.subscribe("concurrent.test", slow_handler)

    # Publish multiple events concurrently
    events = [
        Event(
            type="concurrent.test",
            data={"id": i},
            source="test"
        )
        for i in range(5)
    ]

    # Publish all events at once
    await asyncio.gather(*[
        kernel.message_bus.publish(event)
        for event in events
    ])

    # All events should be processed
    assert len(processed_events) == 5
    assert set(processed_events) == {0, 1, 2, 3, 4}


@pytest.mark.asyncio
async def test_error_handling_in_modules():
    """Test that errors in one module don't crash the system."""
    kernel = Kernel()

    class FaultyModule(AmplifierModule):
        async def initialize(self):
            raise ValueError("Initialization failed!")

    class HealthyModule(AmplifierModule):
        async def initialize(self):
            self.initialized = True

    # Try to add both modules
    faulty = FaultyModule(kernel)
    healthy = HealthyModule(kernel)

    # Faulty module should fail gracefully
    with pytest.raises(ValueError):
        await faulty.initialize()

    # Healthy module should still work
    await healthy.initialize()
    assert healthy.initialized

    # Kernel should continue functioning
    kernel.modules.append(healthy)
    await kernel.start()
    await kernel.shutdown()


@pytest.mark.asyncio
async def test_module_discovery_simulation():
    """Test simulation of module discovery via entry points."""
    # This test simulates what would happen with real entry points

    # Mock entry point discovery
    discovered_modules = [
        TestModule,
        PhilosophyTestModule,
        AgentRegistryModule
    ]

    kernel = Kernel()

    # Simulate loading discovered modules
    for module_class in discovered_modules:
        module = module_class(kernel)
        await module.initialize()
        kernel.modules.append(module)

    # Verify all modules loaded
    assert len(kernel.modules) == 3

    # Verify each module type is present
    module_types = {type(m).__name__ for m in kernel.modules}
    assert "TestModule" in module_types
    assert "PhilosophyTestModule" in module_types
    assert "AgentRegistryModule" in module_types


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "-s"])