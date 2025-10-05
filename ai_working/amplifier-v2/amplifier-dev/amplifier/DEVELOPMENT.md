# Amplifier Development Guide

This guide is for developers who want to contribute to Amplifier or create custom modules.

## 🏗️ Architecture Overview

Amplifier follows a modular, brick-and-stud architecture inspired by LEGO building blocks:

### Core Concepts

- **Bricks**: Self-contained modules with single, clear responsibilities
- **Studs**: Public contracts (interfaces) that modules connect through
- **Regeneratable**: Any module can be rebuilt from its specification without breaking others
- **Isolated**: Each module contains all its code, tests, and documentation

### System Architecture

```
amplifier (CLI)
    ├── amplifier-core (Kernel)
    │   ├── Module Loader
    │   ├── Registry Interface
    │   └── Base Contracts
    │
    ├── LLM Modules
    │   ├── amplifier-mod-llm-claude
    │   └── amplifier-mod-llm-openai
    │
    ├── Tool Modules
    │   ├── amplifier-mod-tool-blog_generator
    │   └── amplifier-mod-tool-ultra_think
    │
    └── System Modules
        ├── amplifier-mod-agent-registry
        └── amplifier-mod-philosophy
```

## 🚀 Development Setup

### Prerequisites

- Python 3.11+
- Git
- uv (recommended) or pip

### Setting Up the Development Environment

1. **Clone the development repository:**
   ```bash
   git clone https://github.com/microsoft/amplifier-dev.git
   cd amplifier-dev
   ```

2. **Install all modules in development mode:**
   ```bash
   python install_all.py
   ```

   This creates editable installs allowing you to modify any module and see changes immediately.

3. **Verify your setup:**
   ```bash
   amplifier --version
   amplifier list-modules
   ```

## 📦 Creating a New Module

### Module Types

Amplifier supports several module types:

- **llm**: Language model providers (`amplifier-mod-llm-*`)
- **tool**: Standalone tools and utilities (`amplifier-mod-tool-*`)
- **agent**: Intelligent agents with complex behaviors (`amplifier-mod-agent-*`)
- **system**: System-level functionality (`amplifier-mod-*`)

### Module Structure

Every module follows this standard structure:

```
amplifier-mod-[type]-[name]/
├── README.md                 # Module documentation
├── pyproject.toml           # Package configuration
├── LICENSE                  # License file
├── src/
│   └── amplifier_mod_[type]_[name]/
│       ├── __init__.py      # Public interface (__all__)
│       ├── core.py          # Main implementation
│       ├── models.py        # Data models (if needed)
│       └── utils.py         # Internal utilities
├── tests/
│   ├── __init__.py
│   ├── test_core.py         # Unit tests
│   └── fixtures/            # Test data
└── examples/                # Usage examples (optional)
    ├── basic_usage.py
    └── README.md
```

### Step-by-Step Module Creation

#### 1. Create the Module Directory

```bash
cd amplifier-dev
mkdir amplifier-mod-tool-mytool
cd amplifier-mod-tool-mytool
```

#### 2. Create pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "amplifier-mod-tool-mytool"
version = "0.1.0"
description = "My custom tool for Amplifier"
authors = [{name = "Your Name", email = "your.email@example.com"}]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "amplifier-core @ git+https://github.com/microsoft/amplifier-core.git",
]

[project.entry-points."amplifier.modules"]
mytool = "amplifier_mod_tool_mytool:MyToolModule"
```

#### 3. Create the Module Implementation

```python
# src/amplifier_mod_tool_mytool/__init__.py
"""MyTool module for Amplifier."""

from .core import MyToolModule

__all__ = ['MyToolModule']
```

```python
# src/amplifier_mod_tool_mytool/core.py
"""Core implementation of MyTool."""

from amplifier_core import Module, Tool
from typing import Any, Dict

class MyToolModule(Module):
    """My custom tool module."""

    @property
    def name(self) -> str:
        return "mytool"

    @property
    def version(self) -> str:
        return "0.1.0"

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the module with configuration."""
        self.config = config

    def get_tools(self) -> list[Tool]:
        """Return the tools provided by this module."""
        return [MyTool()]

class MyTool(Tool):
    """The actual tool implementation."""

    @property
    def name(self) -> str:
        return "mytool"

    @property
    def description(self) -> str:
        return "Does something useful"

    async def execute(self, *args, **kwargs) -> Any:
        """Execute the tool's main functionality."""
        # Your tool logic here
        return {"result": "success"}
```

#### 4. Write Tests

```python
# tests/test_core.py
"""Tests for MyTool module."""

import pytest
from amplifier_mod_tool_mytool import MyToolModule

def test_module_initialization():
    """Test module can be initialized."""
    module = MyToolModule()
    assert module.name == "mytool"
    assert module.version == "0.1.0"

def test_tool_execution():
    """Test tool executes correctly."""
    module = MyToolModule()
    module.initialize({})
    tools = module.get_tools()
    assert len(tools) == 1

    tool = tools[0]
    result = tool.execute()
    assert result["result"] == "success"
```

#### 5. Create Documentation

```markdown
# amplifier-mod-tool-mytool

A custom tool module for Amplifier that [describe what it does].

## Installation

```bash
pip install git+https://github.com/microsoft/amplifier-mod-tool-mytool.git
```

## Usage

[Usage examples]

## Development

[Development instructions]
```

#### 6. Register with Agent Registry

Add your module to the agent registry so it can be discovered:

```python
# In amplifier-mod-agent-registry, add to the registry
{
    "name": "mytool",
    "type": "tool",
    "module": "amplifier_mod_tool_mytool",
    "description": "Does something useful"
}
```

## 🧪 Testing

### Running Tests

```bash
# Test all modules
pytest

# Test specific module
cd amplifier-mod-tool-mytool
pytest tests/

# Test with coverage
pytest --cov=src tests/
```

### Writing Good Tests

- Test the public interface, not implementation details
- Include both success and failure cases
- Use fixtures for test data
- Test async code with pytest-asyncio
- Aim for >80% code coverage

## 📝 Module Best Practices

### Interface Design

- **Minimal Public API**: Export only what's necessary via `__all__`
- **Clear Contracts**: Document inputs, outputs, and side effects
- **Type Hints**: Use Python type hints everywhere
- **Async First**: Prefer async/await for I/O operations

### Code Organization

- **Single Responsibility**: Each module does one thing well
- **No Cross-Module Imports**: Never import from another module's internals
- **Self-Contained**: Include all necessary code within the module
- **Clear Boundaries**: Separate public interface from implementation

### Documentation

- **README.md**: Every module needs comprehensive documentation
- **Docstrings**: Document all public functions and classes
- **Examples**: Provide working examples in the examples/ directory
- **Type Information**: Include type hints in documentation

### Philosophy Alignment

Follow the core Amplifier philosophy:

- **Ruthless Simplicity**: Avoid unnecessary complexity
- **Regeneratable**: Module can be rebuilt from specification
- **Working Code**: No stubs or placeholders
- **User-Focused**: Design for the end user, not the implementation

## 🔄 Module Lifecycle

### Version Management

- Use semantic versioning (MAJOR.MINOR.PATCH)
- Update version in pyproject.toml
- Document changes in CHANGELOG.md
- Tag releases in Git

### Publishing Process

When your module is ready for production:

1. **Prepare for standalone repository:**
   ```bash
   cd amplifier-dev
   python prepare_for_github.py --module amplifier-mod-tool-mytool
   ```

2. **Create GitHub repository:**
   - Repository name: `microsoft/amplifier-mod-tool-mytool`
   - Add LICENSE file
   - Enable issues and discussions

3. **Push to GitHub:**
   ```bash
   cd amplifier-mod-tool-mytool
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/microsoft/amplifier-mod-tool-mytool.git
   git push -u origin main
   ```

4. **Create Release:**
   - Tag with version number
   - Write release notes
   - Publish release

## 🤝 Contributing

### Contribution Process

1. **Fork the repository** (amplifier-dev for development)
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** following the guidelines above
4. **Write/update tests** for your changes
5. **Run tests** to ensure everything works
6. **Commit your changes** (`git commit -m 'Add amazing feature'`)
7. **Push to your fork** (`git push origin feature/amazing-feature`)
8. **Open a Pull Request** with a clear description

### Code Review Criteria

PRs are reviewed for:

- Adherence to module architecture
- Code simplicity and clarity
- Test coverage
- Documentation completeness
- Philosophy alignment

## 📚 Resources

### Documentation

- [Amplifier Core API](https://github.com/microsoft/amplifier-core)
- [Module Examples](https://github.com/microsoft/amplifier-dev/tree/main/examples)
- [Architecture Decision Records](https://github.com/microsoft/amplifier-dev/tree/main/docs/adr)

### Community

- [GitHub Discussions](https://github.com/microsoft/amplifier/discussions)
- [Issue Tracker](https://github.com/microsoft/amplifier/issues)
- [Discord Server](https://discord.gg/amplifier) (coming soon)

### Tools & Libraries

- [Click](https://click.palletsprojects.com/) - CLI framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [pytest](https://docs.pytest.org/) - Testing framework

## 🎯 Module Ideas

Looking for module ideas? Here are some suggestions:

### Tools
- **Code Generator**: Generate boilerplate code from templates
- **Data Analyzer**: Analyze and visualize datasets
- **Documentation Generator**: Auto-generate documentation
- **Test Generator**: Create tests from code

### Agents
- **Code Reviewer**: Automated code review
- **Bug Finder**: Identify potential bugs
- **Performance Analyzer**: Find performance bottlenecks
- **Security Scanner**: Check for security issues

### LLM Providers
- **Local Models**: Support for llama.cpp, Ollama
- **Alternative Providers**: Cohere, Anthropic, etc.
- **Model Routers**: Intelligent model selection

### System Enhancements
- **Caching Layer**: Smart caching for LLM responses
- **Metrics Collector**: Usage and performance metrics
- **Plugin Manager**: Dynamic plugin loading
- **Configuration Manager**: Advanced configuration handling

## 🚧 Troubleshooting

### Common Issues

**Module not found after installation:**
- Ensure you're using editable install: `pip install -e .`
- Check entry points in pyproject.toml
- Verify module is registered in agent registry

**Import errors:**
- Check all dependencies are installed
- Verify Python version (3.11+)
- Ensure amplifier-core is installed

**Tests failing:**
- Update test fixtures
- Check for breaking changes in amplifier-core
- Verify async code is properly awaited

## 📞 Getting Help

If you need help:

1. Check this documentation
2. Look for similar issues on GitHub
3. Ask in GitHub Discussions
4. Open an issue with:
   - Clear problem description
   - Steps to reproduce
   - System information
   - Error messages/logs

---

*Happy coding! Together we're building the future of AI augmentation.*