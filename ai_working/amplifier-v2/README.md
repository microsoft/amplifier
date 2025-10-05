# Amplifier v2 Architecture

Amplifier v2 is a modular AI amplification system built with a plugin architecture that allows for flexible composition of LLM providers, tools, and workflows.

## Overview

The Amplifier v2 system is organized as a collection of modular components that work together to provide a powerful AI-assisted development environment. Each module follows the "bricks and studs" philosophy, where modules are self-contained units with clear interfaces.

## Architecture

```
amplifier-v2/
├── amplifier-core/           # Core kernel providing plugin infrastructure
├── amplifier/                # User-facing CLI and orchestration
├── amplifier-mod-llm-*/      # LLM provider modules (Claude, OpenAI, etc.)
├── amplifier-mod-tool-*/     # Tool modules (UltraThink, BlogGenerator, etc.)
├── amplifier-mod-philosophy/ # Philosophy injection for AI guidance
└── amplifier-mod-agent-*/    # Agent registry and management
```

## Modules

### Core Components

- **amplifier-core** (v0.1.0): Core kernel providing the plugin infrastructure, message passing, and base abstractions for the entire system.

- **amplifier** (v0.1.0): User-facing CLI tool that orchestrates modules and provides the primary interface for users.

### LLM Providers

- **amplifier-mod-llm-claude** (v0.1.0): Claude LLM provider module supporting Anthropic's Claude models.

- **amplifier-mod-llm-openai** (v0.1.0): OpenAI LLM provider module supporting GPT models.

### Tools and Workflows

- **amplifier-mod-tool-ultra_think** (v0.1.0): Multi-step reasoning and deep analysis workflow tool.

- **amplifier-mod-tool-blog_generator** (v0.1.0): Blog content generation workflow with structured multi-step creation.

### System Modules

- **amplifier-mod-philosophy** (v0.1.0): Automatically injects guiding principles and philosophy into AI prompts to maintain consistency.

- **amplifier-mod-agent-registry** (v0.1.0): Manages specialized sub-agents and their coordination.

## Installation

### Prerequisites

- Python 3.11 or higher
- uv (Python package manager)

### Quick Start

1. Clone the dev repository (contains all sub-repos for development):

```bash
git clone <repository-url>
cd amplifier-v2-dev-repo
```

2. Install the core system:

```bash
cd repos/amplifier-core
uv venv
uv pip install -e .
```

3. Install the main CLI:

```bash
cd ../amplifier
uv pip install -e .
```

4. Install desired modules:

```bash
# Install LLM providers
cd ../amplifier-mod-llm-claude
uv pip install -e .

cd ../amplifier-mod-llm-openai
uv pip install -e .

# Install tools
cd ../amplifier-mod-tool-ultra_think
uv pip install -e .
```

## Development

### Project Standards

All modules follow consistent configuration and tooling:

- **Python Version**: 3.11+
- **Package Manager**: uv
- **Formatter**: ruff
- **Type Checker**: pyright
- **Test Framework**: pytest with asyncio support
- **Build System**: hatchling

### Development Setup

1. Install development dependencies:

```bash
uv pip install -e ".[dev]"
```

2. Run checks:

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type check
pyright

# Run tests
pytest
```

### Configuration Files

Each module includes:

- `pyproject.toml`: Package configuration and tool settings
- `ruff.toml`: Code formatting and linting rules
- `README.md`: Module-specific documentation

## Module Development

### Creating a New Module

1. Follow the naming convention:

   - LLM providers: `amplifier-mod-llm-<provider>`
   - Tools: `amplifier-mod-tool-<toolname>`
   - System modules: `amplifier-mod-<function>`

2. Use the standard `pyproject.toml` template with:

   - Consistent metadata fields
   - Standard dev dependencies
   - Unified tool configurations

3. Implement the plugin interface from `amplifier-core`

4. Register via entry points in `pyproject.toml`

### Module Interface

All modules interact through the `amplifier-core` plugin system:

```python
from amplifier_core import Plugin, Message

class MyPlugin(Plugin):
    async def initialize(self):
        """Initialize the plugin"""

    async def process(self, message: Message):
        """Process incoming messages"""
```

## Philosophy

The system follows key design principles:

1. **Modular Design**: Each module is a self-contained "brick" with clear interfaces
2. **Regeneratable**: Modules can be rebuilt from specifications without breaking connections
3. **Simple Contracts**: Clear, minimal interfaces between modules
4. **Progressive Enhancement**: Start simple, add complexity only as needed

See `IMPLEMENTATION_PHILOSOPHY.md` and `MODULAR_DESIGN_PHILOSOPHY.md` for detailed guidance.

## Contributing

When contributing:

1. Follow the existing module patterns
2. Maintain consistent configuration across modules
3. Write clear module documentation
4. Include comprehensive tests
5. Ensure all checks pass (`ruff`, `pyright`, `pytest`)

## License

MIT License - See individual module directories for specific licensing information.

## Support

For issues, questions, or contributions, please refer to the main project repository.
