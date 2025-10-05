# Amplifier Claude LLM Module

Anthropic Claude language model integration for the Amplifier framework.

## 🎯 Purpose

This module provides seamless integration with Anthropic's Claude models (Opus, Sonnet, Haiku) for the Amplifier system. It enables AI-powered text generation, analysis, and reasoning capabilities through Claude's advanced language models.

## ✨ Features

- **🤖 Multiple Claude Models**: Support for Claude 3 Opus, Sonnet, and Haiku
- **⚡ Async Operations**: Full async/await support for high performance
- **📡 Streaming**: Real-time streaming responses
- **🔧 Configurable**: Temperature, max tokens, and other parameters
- **🔄 Automatic Retries**: Built-in retry logic for resilience
- **📝 System Prompts**: Support for system-level instructions

## 📦 Installation

```bash
# Install from GitHub
pip install git+https://github.com/microsoft/amplifier-mod-llm-claude.git
```

For development:
```bash
git clone https://github.com/microsoft/amplifier-mod-llm-claude.git
cd amplifier-mod-llm-claude
pip install -e .
```

## 🔑 Configuration

Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Or configure programmatically:

```python
provider = ClaudeProvider(api_key="your-api-key")
```

## 🚀 Usage

### With Amplifier Framework

When installed, the module automatically registers with Amplifier:

```python
from amplifier_core import Kernel

# Start the kernel
kernel = Kernel()
await kernel.start()

# Claude provider is automatically available
provider = kernel.get_model_provider("claude")
response = await provider.generate("Explain quantum computing in simple terms")
print(response)
```

### Standalone Usage

```python
from amplifier_mod_llm_claude import ClaudeProvider

# Create provider instance
provider = ClaudeProvider(model="claude-3-opus-20240229")

# Generate response
response = await provider.generate(
    prompt="Write a haiku about programming",
    system="You are a creative poet who loves technology"
)
print(response)

# Configure with parameters
response = await provider.generate(
    prompt="Analyze this code",
    max_tokens=2000,
    temperature=0.7
)
```

## 🤖 Supported Models

| Model | ID | Description |
|-------|-----|-------------|
| **Claude 3 Opus** | `claude-3-opus-20240229` | Most capable, best for complex tasks |
| **Claude 3.5 Sonnet** | `claude-3-5-sonnet-20241022` | Balanced performance and speed |
| **Claude 3 Haiku** | `claude-3-haiku-20240307` | Fast and efficient for simple tasks |

## ⚙️ Advanced Configuration

```python
provider = ClaudeProvider(
    model="claude-3-5-sonnet-20241022",
    api_key="your-key",  # Optional if env var is set
    max_retries=3,
    timeout=30
)
```

## 🔌 Module Interface

This module implements the Amplifier `BaseModelProvider` interface:

```python
class ClaudeProvider(BaseModelProvider):
    async def generate(prompt: str, system: str = None, **kwargs) -> str
    def get_config() -> dict
```

## 📊 Performance Considerations

- **Rate Limits**: Respects Anthropic's rate limits automatically
- **Context Window**: Up to 200K tokens (model dependent)
- **Response Time**: Varies by model (Haiku < Sonnet < Opus)
- **Concurrency**: Supports multiple concurrent requests

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## 🤝 Contributing

Contributions welcome! Please ensure:
- Tests pass
- Code follows the project style
- Documentation is updated

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **Amplifier Core**: [microsoft/amplifier-core](https://github.com/microsoft/amplifier-core)
- **Main CLI**: [microsoft/amplifier](https://github.com/microsoft/amplifier)
- **Anthropic API**: [anthropic.com](https://anthropic.com)