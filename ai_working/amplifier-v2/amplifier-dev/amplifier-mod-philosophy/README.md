# Amplifier Philosophy Module

Philosophy injection and guidance system for the Amplifier framework.

## 🎯 Purpose

This module automatically injects guiding principles, best practices, and philosophical frameworks into AI interactions. It ensures consistent alignment with project philosophy across all AI-assisted operations by prepending contextual guidance to prompts.

## ✨ Features

- **📚 Automatic Philosophy Injection**: Prepends relevant guidance to all AI prompts
- **🔄 Dynamic Document Loading**: Discovers and loads all philosophy documents
- **🎯 Event-Driven**: Integrates seamlessly via message bus events
- **📝 Extensible**: Add new philosophy documents without code changes
- **🛡️ Fault Tolerant**: Continues operation even if documents are missing
- **⚡ Lightweight**: Minimal performance overhead

## 📦 Installation

```bash
# Install from GitHub
pip install git+https://github.com/microsoft/amplifier-mod-philosophy.git
```

For development:
```bash
git clone https://github.com/microsoft/amplifier-mod-philosophy.git
cd amplifier-mod-philosophy
pip install -e .
```

## 🚀 Usage

### Automatic Integration

Once installed, the module automatically registers with the Amplifier kernel and enhances all prompts:

```python
from amplifier_core import Kernel

# Start kernel - philosophy module auto-loads
kernel = Kernel()
await kernel.start()

# All prompts are now automatically enhanced with philosophy
# No additional configuration needed!
```

### Direct Usage

```python
from amplifier_mod_philosophy import PhilosophyModule
from pathlib import Path

# Create philosophy module
philosophy = PhilosophyModule(docs_dir=Path("custom/docs"))

# Manually enhance a prompt
original = "Generate a function to calculate totals"
enhanced = philosophy.inject_guidance(original)

# Reload documents from disk
philosophy.reload()

# Check loaded documents
docs = philosophy.get_documents()
print(f"Loaded {len(docs)} philosophy documents")
```

### Adding Philosophy Documents

Add markdown files to the `docs/` directory:

```markdown
# docs/testing_philosophy.md

## Testing Principles

- Test behavior, not implementation
- Focus on contract validation
- Prefer integration tests over unit tests
- Test the happy path and edge cases
```

The module automatically discovers and includes all `.md` files.

## 📚 Included Philosophy

### Core Principles (simplicity.md)
- **Radical Simplicity**: Start simple, stay simple
- **YAGNI**: You Aren't Gonna Need It
- **Clear Over Clever**: Readable code wins
- **Composition**: Small pieces working together

### Best Practices (best_practices.md)
- **Self-Contained Modules**: Independent, regeneratable bricks
- **Clear Contracts**: Well-defined interfaces
- **Error Handling**: Graceful degradation
- **Documentation**: Code as specification

## 🔌 Module Interface

### PhilosophyModule Class

```python
class PhilosophyModule:
    def __init__(self, docs_dir: Path = None):
        """Initialize with philosophy documents directory."""

    def inject_guidance(self, prompt: str) -> str:
        """Enhance prompt with philosophy context."""

    def reload(self):
        """Reload documents from disk."""

    def get_documents(self) -> dict:
        """Get loaded philosophy documents."""
```

### Plugin Registration

```python
def register(kernel):
    """Automatically called by Amplifier kernel.

    Subscribes to:
    - prompt:before_send events

    Modifies:
    - Prepends philosophy guidance to prompts
    """
```

## 🏗️ Architecture

```
PhilosophyModule
├── Document Loader
│   └── Discovers .md files
├── Guidance Injector
│   └── Prepends to prompts
├── Event Handler
│   └── Subscribes to message bus
└── Plugin Interface
    └── Kernel registration
```

## 📊 How It Works

1. **Document Discovery**: Scans `docs/` directory for `.md` files
2. **Content Loading**: Reads and stores philosophy documents in memory
3. **Event Subscription**: Listens for `prompt:before_send` events
4. **Prompt Enhancement**: Prepends guidance as `<philosophy-guidance>` section
5. **Transparent Operation**: Original prompt functionality preserved

## ⚙️ Configuration

### Document Structure

```
amplifier-mod-philosophy/
├── docs/
│   ├── simplicity.md         # Core simplicity principles
│   ├── best_practices.md     # Development practices
│   ├── testing.md            # Testing philosophy
│   └── [your_philosophy].md  # Add your own!
```

### Event Flow

```
Original Prompt → prompt:before_send → Philosophy Injection → Enhanced Prompt → AI
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Test contract validation
pytest tests/test_contract.py

# Test plugin integration
pytest tests/test_plugin.py

# With coverage
pytest --cov=src tests/
```

## 💡 Use Cases

- **Consistent AI Behavior**: Ensure all AI interactions follow project philosophy
- **Best Practice Enforcement**: Automatically include coding standards
- **Team Alignment**: Share philosophy across all developers
- **Quality Assurance**: Inject testing and documentation requirements
- **Domain Guidance**: Add domain-specific principles

## 🤝 Contributing

Contributions welcome! Ideas for enhancement:
- Philosophy templates for different domains
- Conditional injection based on context
- Philosophy validation and linting
- Multi-language philosophy documents
- Philosophy versioning system

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **Amplifier Core**: [microsoft/amplifier-core](https://github.com/microsoft/amplifier-core)
- **Main CLI**: [microsoft/amplifier](https://github.com/microsoft/amplifier)