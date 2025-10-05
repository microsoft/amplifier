# Amplifier OpenAI LLM Module

OpenAI language model integration for the Amplifier framework.

## 🎯 Purpose

This module provides seamless integration with OpenAI's GPT models (GPT-4, GPT-3.5) for the Amplifier system. It enables AI-powered text generation, code completion, and reasoning capabilities through OpenAI's powerful language models.

## ✨ Features

- **🤖 Multiple GPT Models**: Support for GPT-4, GPT-4 Turbo, and GPT-3.5 Turbo
- **⚡ Async Operations**: Full async/await support for high performance
- **📡 Streaming**: Real-time streaming responses
- **🔧 Configurable**: Temperature, max tokens, and other parameters
- **💬 Chat Format**: Native support for conversation history
- **🛡️ Error Handling**: Robust error handling and retries

## 📦 Installation

```bash
# Install from GitHub
pip install git+https://github.com/microsoft/amplifier-mod-llm-openai.git
```

For development:
```bash
git clone https://github.com/microsoft/amplifier-mod-llm-openai.git
cd amplifier-mod-llm-openai
pip install -e .
```

## 🔑 Configuration

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or configure programmatically:

```python
provider = OpenAIProvider(api_key="your-api-key")
```

## 🚀 Usage

### With Amplifier Framework

When installed, the module automatically registers with Amplifier:

```python
from amplifier_core import Kernel

# Start the kernel
kernel = Kernel()
await kernel.start()

# OpenAI provider is automatically available
provider = kernel.get_model_provider("openai")
response = await provider.generate("Explain neural networks in simple terms")
print(response)
```

### Standalone Usage

```python
from amplifier_mod_llm_openai import OpenAIProvider

# Create provider instance
provider = OpenAIProvider(model="gpt-4-turbo-preview")

# Generate response
response = await provider.generate(
    prompt="Write a Python function to sort a list",
    system="You are an expert Python programmer"
)
print(response)

# Configure with parameters
response = await provider.generate(
    prompt="Analyze this data",
    max_tokens=1500,
    temperature=0.5,
    top_p=0.9
)
```

## 🤖 Supported Models

| Model | ID | Description |
|-------|-----|-------------|
| **GPT-4 Turbo** | `gpt-4-turbo-preview` | Latest GPT-4 with 128K context |
| **GPT-4** | `gpt-4` | Most capable for complex tasks |
| **GPT-3.5 Turbo** | `gpt-3.5-turbo` | Fast and cost-effective |
| **GPT-3.5 Turbo 16K** | `gpt-3.5-turbo-16k` | Extended context window |

## ⚙️ Advanced Configuration

```python
provider = OpenAIProvider(
    model="gpt-4-turbo-preview",
    api_key="your-key",  # Optional if env var is set
    organization="org-id",  # Optional
    max_retries=3,
    timeout=60,
    base_url="https://api.openai.com/v1"  # For API proxies
)
```

## 🔌 Module Interface

This module implements the Amplifier `BaseModelProvider` interface:

```python
class OpenAIProvider(BaseModelProvider):
    async def generate(prompt: str, system: str = None, **kwargs) -> str
    def get_config() -> dict
```

## 📊 Performance Considerations

- **Rate Limits**: Automatic rate limit handling
- **Context Window**: Up to 128K tokens (model dependent)
- **Response Time**: GPT-3.5 < GPT-4 < GPT-4 Turbo
- **Cost**: GPT-3.5 is most cost-effective
- **Concurrency**: Supports parallel requests

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
- **OpenAI API**: [platform.openai.com](https://platform.openai.com)