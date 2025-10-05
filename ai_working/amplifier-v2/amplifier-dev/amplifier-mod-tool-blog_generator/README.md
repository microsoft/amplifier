# Amplifier Blog Generator Tool

AI-powered blog content generation tool for the Amplifier framework.

## 🎯 Purpose

This module provides an intelligent blog writing tool that generates high-quality, structured blog posts on any topic. It leverages AI through a metacognitive recipe - a multi-step workflow that coordinates draft generation and refinement to produce polished content.

## ✨ Features

- **📝 Two-Phase Generation**: Draft creation followed by intelligent refinement
- **🎨 Structured Content**: Well-organized posts with introduction, body, and conclusion
- **🤖 Model Agnostic**: Works with any configured LLM provider (Claude, OpenAI, etc.)
- **📊 Progress Tracking**: Optional event publishing for workflow visibility
- **🎯 Simple Interface**: Single command generates complete blog post
- **🔧 Extensible**: Easy to add more refinement steps or specialized processing

## 📦 Installation

```bash
# Install from GitHub
pip install git+https://github.com/microsoft/amplifier-mod-tool-blog_generator.git
```

For development:
```bash
git clone https://github.com/microsoft/amplifier-mod-tool-blog_generator.git
cd amplifier-mod-tool-blog_generator
pip install -e .
```

## 🚀 Usage

### With Amplifier CLI

```bash
# Generate a blog post
amplifier run blog_generator "The Future of Artificial Intelligence"

# From an outline
amplifier run blog_generator "Climate Change: 1. Causes 2. Effects 3. Solutions"
```

### With Amplifier Framework

```python
from amplifier_core import Kernel

# Start the kernel
kernel = Kernel()
await kernel.start()

# Get the blog generator tool
blog_tool = kernel.get_tool("blog_generator")

# Generate a blog post
result = await blog_tool.run("The Impact of Remote Work on Society")
print(result)
```

### Standalone Usage

```python
from amplifier_mod_tool_blog_generator import BlogGeneratorTool

# Create generator with a model provider
generator = BlogGeneratorTool(model_provider)

# Generate blog post
blog = await generator.run("Quantum Computing Explained")
print(blog)
```

## 🔄 Workflow Process

The blog generator implements a metacognitive recipe with two phases:

### Phase 1: Draft Generation
- Takes topic or outline as input
- Generates initial blog post with structure
- Focuses on content coverage and organization

### Phase 2: Refinement
- Reviews and improves the draft
- Enhances clarity and engagement
- Strengthens introduction and conclusion
- Polishes transitions between sections

## 📊 Events

The module publishes progress events when a message bus is available:

| Event | Description |
|-------|-------------|
| `tool:blog_generator:draft_complete` | Fired after draft generation |
| `tool:blog_generator:complete` | Fired after refinement |

## 🔌 Module Interface

This module implements the Amplifier `BaseTool` interface:

```python
class BlogGeneratorTool(BaseTool):
    @property
    def name(self) -> str:
        return "blog_generator"

    @property
    def description(self) -> str:
        return "Generate polished blog posts from topics or outlines"

    async def run(topic_or_outline: str) -> str:
        # Two-phase generation process
```

## 🎯 Extension Opportunities

This tool can be extended with additional capabilities:

- **Multiple Refinement Passes**: Add more specialized improvement steps
- **Section Specialists**: Different agents for introduction, body, conclusion
- **Style Checking**: Grammar and readability analysis
- **SEO Optimization**: Keyword integration and meta descriptions
- **Fact Checking**: Integration with research tools
- **Template System**: Pre-defined structures for different blog types
- **Multi-language**: Support for content in various languages

## 🏗️ Architecture

```
BlogGeneratorTool
├── Draft Generation
│   └── Initial content creation
├── Refinement Phase
│   └── Quality improvement
└── Event Publishing
    └── Progress notifications
```

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## 💡 Design Philosophy

This module embodies the Amplifier principle of **workflow orchestration**: complex multi-step processes packaged as simple, accessible tools. Users invoke a single command, and multiple coordinated LLM calls occur behind the scenes, demonstrating how sophisticated AI workflows can be made accessible to non-technical users.

## 🤝 Contributing

Contributions welcome! Please:
- Follow the modular design philosophy
- Include tests for new features
- Update documentation
- Maintain the simple interface

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **Amplifier Core**: [microsoft/amplifier-core](https://github.com/microsoft/amplifier-core)
- **Main CLI**: [microsoft/amplifier](https://github.com/microsoft/amplifier)