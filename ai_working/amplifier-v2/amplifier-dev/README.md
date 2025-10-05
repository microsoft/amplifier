# Amplifier Development Repository

This is the development repository for the Amplifier project - a modular AI augmentation framework that amplifies human capabilities through composable tools and intelligent agents.

## 🎯 Purpose

This repository (`amplifier-dev`) contains all Amplifier modules in a monorepo structure for development purposes. Each module will become its own GitHub repository when published, following the modular philosophy of self-contained, regeneratable components.

## 📦 Future GitHub Repositories

When published, each module will become an independent repository under the Microsoft organization:

| Module | Future Repository | Description |
|--------|------------------|-------------|
| **amplifier** | `microsoft/amplifier` | Main CLI and orchestration framework |
| **amplifier-core** | `microsoft/amplifier-core` | Core contracts and interfaces |
| **amplifier-mod-agent-registry** | `microsoft/amplifier-mod-agent-registry` | Agent discovery and management |
| **amplifier-mod-llm-claude** | `microsoft/amplifier-mod-llm-claude` | Claude LLM provider |
| **amplifier-mod-llm-openai** | `microsoft/amplifier-mod-llm-openai` | OpenAI LLM provider |
| **amplifier-mod-philosophy** | `microsoft/amplifier-mod-philosophy` | Philosophy extraction and application |
| **amplifier-mod-tool-blog_generator** | `microsoft/amplifier-mod-tool-blog_generator` | Blog content generation tool |
| **amplifier-mod-tool-ultra_think** | `microsoft/amplifier-mod-tool-ultra_think` | Deep reasoning and analysis tool |

## 🚀 Development Setup

### Prerequisites

- Python 3.11 or higher
- uv (recommended) or pip
- Git

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/microsoft/amplifier-dev.git
   cd amplifier-dev
   ```

2. **Install all modules in development mode:**
   ```bash
   python install_all.py
   ```

   This will install all modules with editable links, allowing you to develop across modules seamlessly.

3. **Verify installation:**
   ```bash
   amplifier --version
   amplifier list-tools
   ```

### Development Workflow

#### Working on a Single Module

```bash
cd amplifier-mod-llm-claude
# Make your changes
pytest tests/  # Run tests
```

#### Creating a New Module

1. Create a new directory: `amplifier-mod-[type]-[name]`
2. Follow the module structure:
   ```
   amplifier-mod-[type]-[name]/
   ├── README.md
   ├── pyproject.toml
   ├── src/
   │   └── amplifier_mod_[type]_[name]/
   │       ├── __init__.py
   │       └── [implementation files]
   └── tests/
       └── test_[module].py
   ```

3. Register the module in `amplifier-mod-agent-registry` if it's a tool or agent

#### Running Tests

```bash
# Test all modules
python -m pytest

# Test specific module
cd amplifier-core
python -m pytest tests/

# Test with coverage
python -m pytest --cov=src tests/
```

#### Preparing for GitHub Publishing

When ready to publish modules as separate repositories:

```bash
python prepare_for_github.py
```

This script will:
- Update all cross-module dependencies to use GitHub URLs
- Prepare each module for standalone repository publication
- Generate migration instructions

## 📖 Documentation

- **User Documentation**: See [amplifier/README.md](amplifier/README.md)
- **Developer Guide**: See [amplifier/DEVELOPMENT.md](amplifier/DEVELOPMENT.md)
- **Architecture**: See individual module READMEs for component details
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md) (coming soon)

## 🏗️ Architecture

Amplifier follows a modular, brick-and-stud architecture:

- **Bricks**: Self-contained modules with single responsibilities
- **Studs**: Public contracts (interfaces) that modules connect through
- **Regeneratable**: Any module can be rebuilt from its specification without breaking others
- **Parallel Development**: Modules can be developed and tested independently

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) (coming soon) for details on:
- Code style and standards
- Testing requirements
- Pull request process
- Module development guidelines

## 📝 License

This project is licensed under the MIT License - see individual module LICENSE files for details.

## 🔗 Links

- **Production Repository**: [microsoft/amplifier](https://github.com/microsoft/amplifier) (future)
- **Documentation**: [amplifier.microsoft.com](https://amplifier.microsoft.com) (future)
- **Issues**: [GitHub Issues](https://github.com/microsoft/amplifier-dev/issues)

## 🧑‍💻 Development Team

Maintained by the Microsoft Amplifier team. For questions or support, please open an issue.

---

**Note**: This is the development repository. For production use, install from the individual module repositories once published.