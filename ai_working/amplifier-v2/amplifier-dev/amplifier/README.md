# Amplifier

A modular AI augmentation framework that amplifies human capabilities through composable tools and intelligent agents.

## 🎯 What is Amplifier?

Amplifier is a powerful command-line interface that brings together AI models, specialized tools, and intelligent agents to augment your cognitive abilities. Whether you're writing, coding, analyzing, or creating, Amplifier provides the right AI-powered tools to amplify your work.

## ✨ Features

- **🧩 Modular Architecture**: Install only the tools and capabilities you need
- **🤖 Multiple AI Providers**: Support for Claude, OpenAI, and more
- **🛠️ Specialized Tools**: Blog writing, deep analysis, philosophy extraction, and growing toolkit
- **🎭 Multiple Modes**: Switch between development, writing, and custom workflows
- **🔌 Extensible**: Easy to add new modules and capabilities
- **⚡ Fast & Lightweight**: Minimal core with on-demand module loading

## 📦 Installation

### Quick Install
```bash
# Install the core CLI
pip install git+https://github.com/microsoft/amplifier.git
```

### Install with Modules
```bash
# Install with Claude LLM support
pip install git+https://github.com/microsoft/amplifier.git
pip install git+https://github.com/microsoft/amplifier-mod-llm-claude.git

# Install with writing tools
pip install git+https://github.com/microsoft/amplifier-mod-tool-blog_generator.git

# Install with deep thinking capabilities
pip install git+https://github.com/microsoft/amplifier-mod-tool-ultra_think.git
```

## Usage

### Interactive Mode

Start an interactive session:

```bash
amplifier
# or
amplifier interactive --mode development
```

### Initialize a Mode

```bash
# Use a built-in mode
amplifier init --mode development

# Create a custom mode
amplifier init --name mymode --modules amplifier_mod_llm_openai amplifier_mod_tool_ultra_think

# Extend an existing mode
amplifier init --name extended --from-mode development --modules amplifier_mod_tool_blog_generator
```

### Run Commands

```bash
# Run with a specific mode
amplifier run development

# Run a specific tool
amplifier run blog_generator "AI in Education"

# Run with additional modules
amplifier run ultra_think "quantum computing" --modules amplifier_mod_llm_claude
```

### List Available Options

```bash
# List available modes
amplifier list-modes
amplifier list-modes --verbose

# List available modules
amplifier list-modules
```

## 🎮 Commands

### Core Commands
- `amplifier` - Start interactive mode
- `amplifier init` - Initialize a mode or configuration
- `amplifier run [tool] [args]` - Run a specific tool
- `amplifier list-modules` - Show available modules
- `amplifier list-modes` - Show available modes
- `amplifier list-tools` - Show available tools
- `amplifier interactive` - Enter interactive shell mode

### Examples
```bash
# Generate a blog post
amplifier run blog_generator "The Future of AI"

# Deep analysis with ultra thinking
amplifier run ultra_think "quantum computing applications"

# Interactive development mode
amplifier interactive --mode development

# Create custom mode
amplifier init --name research --modules amplifier_mod_tool_ultra_think amplifier_mod_philosophy
```

## ⚙️ Configuration

Amplifier stores configuration in `~/.amplifier/`:

```
~/.amplifier/
├── config.yaml          # User preferences
├── modes/               # Mode configurations
│   ├── default.yaml
│   ├── development.yaml
│   └── writing.yaml
├── plugins/             # Plugin settings
└── data/                # Application data
```

## 🎭 Built-in Modes

- **default** - Basic functionality for general use
- **development** - Enhanced mode for software development
- **writing** - Optimized for content creation and writing
- **research** - Deep analysis and research capabilities (with ultra_think)

## 🔧 Available Modules

### LLM Providers
- `amplifier-mod-llm-claude` - Anthropic Claude integration
- `amplifier-mod-llm-openai` - OpenAI GPT integration

### Tools
- `amplifier-mod-tool-blog_generator` - AI-powered blog writing
- `amplifier-mod-tool-ultra_think` - Deep reasoning and analysis
- `amplifier-mod-philosophy` - Philosophy extraction and application

### System
- `amplifier-mod-agent-registry` - Agent discovery and management

## 🚀 Development

For developers who want to contribute or create custom modules, see our [Development Guide](DEVELOPMENT.md).

### Quick Start for Developers
```bash
# Clone the development repository
git clone https://github.com/microsoft/amplifier-dev.git
cd amplifier-dev

# Install all modules in development mode
python install_all.py

# Start developing!
```

## 📚 Documentation

- [User Guide](https://amplifier.microsoft.com/docs/user-guide) (coming soon)
- [Module Creation Guide](DEVELOPMENT.md)
- [API Reference](https://amplifier.microsoft.com/api) (coming soon)

## 🤝 Contributing

We welcome contributions! Please see our development repository at [microsoft/amplifier-dev](https://github.com/microsoft/amplifier-dev) for:
- Contributing guidelines
- Development setup
- Module creation templates
- Testing requirements

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **Development Repo**: [microsoft/amplifier-dev](https://github.com/microsoft/amplifier-dev)
- **Issues**: [GitHub Issues](https://github.com/microsoft/amplifier/issues)
- **Discussions**: [GitHub Discussions](https://github.com/microsoft/amplifier/discussions)

---

*Amplifier - Amplifying human intelligence through modular AI augmentation*