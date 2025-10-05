"""Blog Generator Tool Plugin

Registers the BlogGeneratorTool with the Amplifier kernel.
"""

from amplifier_core import AmplifierModule
from amplifier_core import Kernel
from .blog_generator import BlogGeneratorTool


class Plugin(AmplifierModule):
    """Blog Generator Plugin

    Registers the blog_generator tool in the kernel, making it available
    for invocation by name through the kernel's tool registry.
    """

    def __init__(self, kernel):
        """Initialize the blog generator plugin."""
        super().__init__(kernel)
        self.name = "blog_generator"
        self.tool = None

    async def initialize(self):
        """Initialize and register the blog generator tool."""
        self.tool = BlogGeneratorTool(self.kernel)
        self.kernel.register_tool(self.tool.name, self.tool)

    async def shutdown(self):
        """Clean up resources."""
        # No cleanup needed for this module
        pass

    async def register(self, kernel: Kernel) -> None:
        """Register the BlogGenerator tool in the kernel.

        Args:
            kernel: The Amplifier kernel instance

        The tool will be available as 'blog_generator' after registration.
        Example usage:
            await kernel.tools["blog_generator"].run("AI in Education")
        """
        tool = BlogGeneratorTool(kernel)
        kernel.register_tool(tool.name, tool)