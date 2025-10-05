"""Basic example of using the Amplifier Core kernel."""

import asyncio
import logging

from amplifier_core import AmplifierModule
from amplifier_core import BaseModelProvider
from amplifier_core import BaseTool
from amplifier_core import Event
from amplifier_core import Kernel

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


# Example model provider
class SimpleModelProvider(BaseModelProvider):
    """Simple mock model provider."""

    async def generate(self, prompt: str, *, system: str | None = None, **kwargs) -> str:
        """Generate a response."""
        return f"[Mock response to: {prompt}]"

    def get_config(self) -> dict:
        """Get configuration."""
        return {"model": "simple", "version": "1.0"}


# Example tool
class CalculatorTool(BaseTool):
    """Simple calculator tool."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Performs basic arithmetic operations"

    async def run(self, operation: str = "add", a: float = 0, b: float = 0, **kwargs) -> dict:
        """Execute calculation."""
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            result = a / b if b != 0 else "Error: Division by zero"
        else:
            result = f"Unknown operation: {operation}"

        return {"operation": operation, "a": a, "b": b, "result": result}


# Example module
class MathModule(AmplifierModule):
    """Module providing math capabilities."""

    async def initialize(self):
        """Initialize the module."""
        # Register our calculator tool
        self.kernel.register_tool("calculator", CalculatorTool())

        # Subscribe to calculation requests
        self.kernel.message_bus.subscribe("calculation.request", self.handle_calculation)

    async def handle_calculation(self, event: Event):
        """Handle calculation requests."""
        data = event.data
        tool = self.kernel.get_tool("calculator")
        if tool:
            result = await tool.run(**data)
            # Publish result
            await self.kernel.message_bus.publish(Event(type="calculation.result", data=result, source="math_module"))


async def main():
    """Run the example."""
    # Create kernel
    kernel = Kernel()

    # Manually add our example module (normally done via entry points)
    module = MathModule(kernel)
    kernel.modules.append(module)

    # Start kernel
    await kernel.start()

    # Register a model provider
    kernel.register_model_provider("simple", SimpleModelProvider())

    # Use the model provider
    provider = kernel.get_model_provider("simple")
    if provider:
        response = await provider.generate("What is 2+2?")
        print(f"Model response: {response}")

    # Use the calculator tool
    tool = kernel.get_tool("calculator")
    if tool:
        result = await tool.run(operation="multiply", a=7, b=8)
        print(f"Calculator result: {result}")

    # Test event system
    results = []

    async def capture_result(event: Event):
        results.append(event.data)

    kernel.message_bus.subscribe("calculation.result", capture_result)

    # Send calculation request via event
    await kernel.message_bus.publish(
        Event(type="calculation.request", data={"operation": "add", "a": 10, "b": 20}, source="main")
    )

    # Wait for async processing
    await asyncio.sleep(0.1)

    if results:
        print(f"Event-based calculation: {results[0]}")

    # Shutdown
    await kernel.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
