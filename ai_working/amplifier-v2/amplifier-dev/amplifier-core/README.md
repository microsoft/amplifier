# Amplifier Core

The foundational kernel for the Amplifier modular AI augmentation framework.

## 🎯 Purpose

Amplifier Core is the heart of the Amplifier system - a lightweight kernel that provides the essential infrastructure for loading, managing, and coordinating AI modules. It enables a plugin-based architecture where capabilities can be added or removed as self-contained modules.

## ✨ Key Features

- **🔌 Plugin Discovery**: Automatic discovery and loading via Python entry points
- **📨 Message Bus**: Async pub/sub for inter-component communication
- **📚 Registry Management**: Central registration for models, tools, and agents
- **🔄 Lifecycle Management**: Clean initialization and shutdown orchestration
- **🏗️ Minimal Core**: Ruthlessly simple design following the brick-and-stud philosophy

## 📦 Installation

```bash
# Install from GitHub
pip install git+https://github.com/microsoft/amplifier-core.git
```

For development:
```bash
# Clone and install in editable mode
git clone https://github.com/microsoft/amplifier-core.git
cd amplifier-core
pip install -e .
```

## Usage

```python
import asyncio
from amplifier_core import Kernel

async def main():
    # Create and start kernel
    kernel = Kernel()
    await kernel.start()

    # Kernel loads all discovered modules automatically
    # Modules register their providers and tools

    # Access registered components
    provider = kernel.get_model_provider("openai")
    tool = kernel.get_tool("web_search")

    # Publish events via message bus
    from amplifier_core import Event
    await kernel.message_bus.publish(Event(
        type="task.started",
        data={"task_id": "123"},
        source="my_component"
    ))

    # Shutdown cleanly
    await kernel.shutdown()

asyncio.run(main())
```

## Creating a Module

Modules are discovered via Python entry points. Create a module by:

1. Inherit from `AmplifierModule`:

```python
from amplifier_core import AmplifierModule

class MyModule(AmplifierModule):
    async def initialize(self):
        # Register providers, tools, subscriptions
        self.kernel.register_tool("my_tool", MyTool())

        # Subscribe to events
        self.kernel.message_bus.subscribe(
            "task.started",
            self.handle_task_started
        )

    async def handle_task_started(self, event):
        # Handle the event
        pass
```

2. Register via entry point in `pyproject.toml`:

```toml
[project.entry-points."amplifier.modules"]
my_module = "my_package.module:MyModule"
```

## Interfaces

### BaseModelProvider
- `async generate(prompt, system=None, **kwargs) -> str`
- `get_config() -> dict`

### BaseTool
- `name: str` - Tool identifier
- `description: str` - Human-readable description
- `async run(**kwargs) -> dict` - Execute the tool

### BaseWorkflow
- `name: str` - Workflow identifier
- `steps: list[str]` - Execution steps
- `async execute(context) -> dict` - Run the workflow

## 🏗️ Architecture

```
Kernel (Core)
├── MessageBus (async pub/sub)
├── Model Provider Registry
├── Tool Registry
├── Agent Registry
└── Module Lifecycle Manager
    └── Discovers and loads modules via entry points
```

The kernel follows a hub-and-spoke model where modules connect to the central kernel but not directly to each other. This ensures:
- Clean separation of concerns
- Easy module replacement
- Clear dependency management
- Simple testing and debugging

## 🎯 Design Principles

- **Ruthless Simplicity**: Minimal abstractions, direct implementations
- **Self-Contained Modules**: Each module is independent with its own tests and docs
- **Contract-Based**: Clear, stable interfaces between components
- **Async-First**: Built for concurrent operations
- **Regeneratable**: Modules can be rebuilt from specifications

## 🧪 Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src tests/
```

## 🔧 Development

```bash
# Format code
ruff format .

# Lint
ruff check .

# Type check
pyright
```

## 📚 Module Development

See the [Amplifier Development Guide](https://github.com/microsoft/amplifier/blob/main/DEVELOPMENT.md) for detailed instructions on creating modules.

## 🤝 Contributing

Contributions are welcome! Please:
1. Follow the design principles
2. Include tests for new functionality
3. Update documentation
4. Ensure all checks pass

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **Main CLI**: [microsoft/amplifier](https://github.com/microsoft/amplifier)
- **Documentation**: [amplifier.microsoft.com](https://amplifier.microsoft.com) (coming soon)