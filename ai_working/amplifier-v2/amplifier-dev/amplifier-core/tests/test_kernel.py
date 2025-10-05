"""Tests for the kernel module."""

import asyncio

import pytest

from amplifier_core import AmplifierModule
from amplifier_core import BaseModelProvider
from amplifier_core import BaseTool
from amplifier_core import Event
from amplifier_core import Kernel


class MockModelProvider(BaseModelProvider):
    """Mock model provider for testing."""

    async def generate(self, prompt: str, *, system: str | None = None, **kwargs) -> str:
        return f"Response to: {prompt}"

    def get_config(self) -> dict:
        return {"model": "mock"}


class MockTool(BaseTool):
    """Mock tool for testing."""

    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "A mock tool for testing"

    async def run(self, **kwargs) -> dict:
        return {"result": "success", "params": kwargs}


class TestModule(AmplifierModule):
    """Test module for verifying plugin loading."""

    def __init__(self, kernel):
        super().__init__(kernel)
        self.initialized = False
        self.events_received = []

    async def initialize(self):
        self.initialized = True
        # Register a provider and tool
        self.kernel.register_model_provider("test_provider", MockModelProvider())
        self.kernel.register_tool("test_tool", MockTool())

        # Subscribe to events
        self.kernel.message_bus.subscribe("test.event", self.handle_test_event)

    async def handle_test_event(self, event: Event):
        self.events_received.append(event)


@pytest.mark.asyncio
async def test_kernel_initialization():
    """Test basic kernel initialization."""
    kernel = Kernel()

    assert kernel.message_bus is not None
    assert kernel.model_providers == {}
    assert kernel.tools == {}
    assert kernel.modules == []
    assert kernel._running is False


@pytest.mark.asyncio
async def test_kernel_lifecycle():
    """Test kernel start and shutdown."""
    kernel = Kernel()

    # Start kernel
    await kernel.start()
    assert kernel._running is True

    # Shutdown kernel
    await kernel.shutdown()
    assert kernel._running is False


@pytest.mark.asyncio
async def test_model_provider_registration():
    """Test registering and retrieving model providers."""
    kernel = Kernel()
    provider = MockModelProvider()

    kernel.register_model_provider("test", provider)

    retrieved = kernel.get_model_provider("test")
    assert retrieved is provider

    # Test non-existent provider
    assert kernel.get_model_provider("nonexistent") is None


@pytest.mark.asyncio
async def test_tool_registration():
    """Test registering and retrieving tools."""
    kernel = Kernel()
    tool = MockTool()

    kernel.register_tool("test", tool)

    retrieved = kernel.get_tool("test")
    assert retrieved is tool

    # Test non-existent tool
    assert kernel.get_tool("nonexistent") is None


@pytest.mark.asyncio
async def test_message_bus_pub_sub():
    """Test message bus publish/subscribe functionality."""
    kernel = Kernel()
    received_events = []

    async def handler(event: Event):
        received_events.append(event)

    # Subscribe to event
    kernel.message_bus.subscribe("test.event", handler)

    # Publish event
    test_event = Event(type="test.event", data={"test": "data"}, source="test")
    await kernel.message_bus.publish(test_event)

    # Give async tasks time to complete
    await asyncio.sleep(0.1)

    assert len(received_events) == 1
    assert received_events[0].type == "test.event"
    assert received_events[0].data == {"test": "data"}


@pytest.mark.asyncio
async def test_message_bus_concurrent_handlers():
    """Test that multiple handlers run concurrently."""
    kernel = Kernel()
    results = []

    async def slow_handler1(event: Event):
        await asyncio.sleep(0.1)
        results.append(1)

    async def slow_handler2(event: Event):
        await asyncio.sleep(0.05)
        results.append(2)

    # Subscribe both handlers
    kernel.message_bus.subscribe("test.event", slow_handler1)
    kernel.message_bus.subscribe("test.event", slow_handler2)

    # Publish event
    test_event = Event(type="test.event", data={}, source="test")
    await kernel.message_bus.publish(test_event)

    # Results should be [2, 1] if concurrent (handler2 finishes first)
    assert results == [2, 1]


@pytest.mark.asyncio
async def test_module_lifecycle():
    """Test module initialization and shutdown."""
    kernel = Kernel()
    module = TestModule(kernel)

    # Initialize module
    await module.initialize()
    assert module.initialized is True

    # Check registered components
    assert kernel.get_model_provider("test_provider") is not None
    assert kernel.get_tool("test_tool") is not None

    # Test event handling
    test_event = Event(type="test.event", data={"test": "data"}, source="test")
    await kernel.message_bus.publish(test_event)

    # Give async tasks time to complete
    await asyncio.sleep(0.1)

    assert len(module.events_received) == 1
    assert module.events_received[0].data == {"test": "data"}

    # Shutdown
    await module.shutdown()
