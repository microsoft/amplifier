# Amplifier UltraThink Tool

Deep multi-perspective reasoning and analysis tool for the Amplifier framework.

## 🎯 Purpose

UltraThink is a powerful analytical tool that performs deep, multi-dimensional analysis of any topic by examining it from multiple perspectives simultaneously. It leverages parallel processing to gather diverse viewpoints and synthesizes them into comprehensive, actionable insights.

## ✨ Features

- **🔄 Parallel Processing**: Concurrent analysis from multiple perspectives for 5x+ speed improvement
- **🎭 Multi-Perspective Analysis**: Philosophical, practical, critical, creative, and systems thinking angles
- **🧠 Intelligent Synthesis**: Combines diverse viewpoints into cohesive insights
- **⚙️ Customizable Perspectives**: Define your own analytical lenses
- **🛡️ Fault Tolerant**: Continues even if some perspectives fail
- **📊 Structured Output**: Organized insights, tensions, and recommendations

## 📦 Installation

```bash
# Install from GitHub
pip install git+https://github.com/microsoft/amplifier-mod-tool-ultra_think.git
```

For development:
```bash
git clone https://github.com/microsoft/amplifier-mod-tool-ultra_think.git
cd amplifier-mod-tool-ultra_think
pip install -e .
```

## 🚀 Usage

### With Amplifier CLI

```bash
# Analyze a topic
amplifier run ultra_think "The future of remote work"

# With custom output format
amplifier run ultra_think "Quantum computing applications" --format detailed
```

### With Amplifier Framework

```python
from amplifier_core import Kernel

# Start the kernel
kernel = Kernel()
await kernel.start()

# Get the UltraThink tool
ultra_think = kernel.get_tool("ultra_think")

# Run deep analysis
result = await ultra_think.run("Impact of AI on education")
print(result)
```

### With Custom Perspectives

```python
# Use custom analytical lenses
result = await ultra_think.run(
    topic="Sustainable urban development",
    perspectives=[
        "Environmental sustainability and climate resilience",
        "Economic viability and funding models",
        "Social equity and community impact",
        "Technological innovation and smart city integration",
        "Policy and governance challenges"
    ]
)
```

### Standalone Usage

```python
from amplifier_mod_tool_ultra_think import UltraThinkTool

# Create tool with model provider
tool = UltraThinkTool(model_provider)

# Perform analysis
analysis = await tool.run("The ethics of artificial general intelligence")
print(analysis)
```

## 🔄 How It Works

### 1. Perspective Generation
Generates prompts examining the topic from different angles:
- **Philosophical**: Core principles and ethical implications
- **Practical**: Real-world applications and implementation
- **Critical**: Challenges, risks, and limitations
- **Creative**: Innovative possibilities and unconventional approaches
- **Systems**: Interconnections and emergent properties

### 2. Parallel Execution
All perspectives are analyzed simultaneously using async operations:
```python
responses = await asyncio.gather(*perspective_tasks)
```

### 3. Intelligent Synthesis
Combines all perspectives into structured output:
- **Key Insights**: Major findings across perspectives
- **Common Themes**: Recurring patterns and agreements
- **Tensions**: Contradictions and trade-offs
- **Recommendations**: Actionable next steps
- **Critical Takeaways**: Most important conclusions

## ⚡ Performance Benefits

| Approach | 5 Perspectives @ 5s each | Result |
|----------|-------------------------|---------|
| Sequential | 5 × 5s = 25s | Slow |
| **Parallel (UltraThink)** | **max(5s) = ~5s** | **5x faster** |

- Scales to more perspectives without linear time increase
- Efficient API usage through concurrent requests
- Typically completes in time of slowest perspective

## 🎨 Example Output

```markdown
## Analysis: The Future of Remote Work

### Key Insights
- Remote work fundamentally reshapes urban economics
- Technology enables but culture determines success
- Hybrid models emerging as dominant paradigm

### Tensions Identified
- Flexibility vs. collaboration needs
- Global talent access vs. local community impact
- Work-life balance vs. always-on culture

### Recommendations
1. Invest in asynchronous collaboration tools
2. Develop clear remote work policies
3. Create intentional culture-building practices
```

## 🔌 Module Interface

Implements the Amplifier `BaseTool` interface:

```python
class UltraThinkTool(BaseTool):
    @property
    def name(self) -> str:
        return "ultra_think"

    @property
    def description(self) -> str:
        return "Deep multi-perspective analysis tool"

    async def run(topic: str, perspectives: list = None) -> str:
        # Parallel analysis and synthesis
```

## 🏗️ Architecture

```
UltraThinkTool
├── Perspective Generator
│   └── Creates analytical prompts
├── Parallel Executor
│   └── Concurrent LLM queries
├── Result Collector
│   └── Fault-tolerant aggregation
└── Synthesizer
    └── Intelligent combination
```

## 🧪 Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=src tests/

# Specific test
pytest tests/test_ultra_think.py -v
```

## 💡 Philosophy Alignment

This module exemplifies Amplifier's core principles:

- **Modular Design**: Self-contained brick with clear interface studs
- **Async-First**: Maximizes concurrency for optimal performance
- **Ruthless Simplicity**: Clear implementation without unnecessary complexity
- **Regeneratable**: Can be rebuilt from specification

## 🎯 Use Cases

- **Strategic Planning**: Analyze business strategies from multiple angles
- **Research**: Comprehensive literature review perspectives
- **Decision Making**: Evaluate options from diverse viewpoints
- **Problem Solving**: Understand complex problems holistically
- **Innovation**: Generate creative solutions through varied lenses

## 🤝 Contributing

Contributions welcome! Ideas for enhancement:
- Additional default perspectives
- Perspective templates for specific domains
- Visualization of perspective relationships
- Integration with research databases

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **Amplifier Core**: [microsoft/amplifier-core](https://github.com/microsoft/amplifier-core)
- **Main CLI**: [microsoft/amplifier](https://github.com/microsoft/amplifier)