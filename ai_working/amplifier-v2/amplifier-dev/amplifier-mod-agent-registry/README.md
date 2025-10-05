# Amplifier Agent Registry Module

Centralized agent and sub-agent management system for the Amplifier framework.

## 🎯 Purpose

The Agent Registry provides a sophisticated system for creating, managing, and coordinating specialized AI agents within Amplifier. It enables task delegation to purpose-built agents while managing lifecycle, concurrency, and resource allocation.

## ✨ Features

- **🤖 Specialized Agents**: Pre-built agents for analysis, coding, research, and review
- **🔄 Lifecycle Management**: Automatic agent creation, tracking, and disposal
- **⚡ Concurrency Control**: Configurable limits to prevent resource exhaustion
- **📊 Event Integration**: Full integration with kernel message bus
- **🔌 Extensible**: Easy registration of custom agent types
- **🛡️ Resource Protection**: Automatic capacity monitoring and warnings

## 📦 Installation

```bash
# Install from GitHub
pip install git+https://github.com/microsoft/amplifier-mod-agent-registry.git
```

For development:
```bash
git clone https://github.com/microsoft/amplifier-mod-agent-registry.git
cd amplifier-mod-agent-registry
pip install -e .
```

## 🚀 Usage

### With Amplifier Framework

```python
from amplifier_core import Kernel

# Start kernel - registry auto-loads
kernel = Kernel()
await kernel.start()

# Access the registry
registry = kernel.agent_registry

# Create specialized agents
analysis_agent = registry.create_agent("analysis")
result = await analysis_agent.handle_task("Analyze the requirements for a chat application")

# Clean up when done
registry.dispose_agent(analysis_agent.id)
```

### Direct Usage

```python
from amplifier_mod_agent_registry import AgentRegistry

# Create registry
registry = AgentRegistry(kernel)  # Optional kernel for model access

# Create different agent types
agents = {
    "analyzer": registry.create_agent("analysis"),
    "coder": registry.create_agent("coding"),
    "researcher": registry.create_agent("research"),
    "reviewer": registry.create_agent("review")
}

# Use agents for tasks
analysis = await agents["analyzer"].handle_task("Break down the problem")
code = await agents["coder"].handle_task("Implement the solution")
review = await agents["reviewer"].handle_task(f"Review this code: {code}")

# List available types
types = registry.list_agent_types()
print(f"Available agents: {types}")
```

## 🤖 Built-in Agent Types

### AnalysisAgent
Breaks down complex requests into components:
- Main objectives identification
- Requirements extraction
- Subtask decomposition
- Challenge identification
- Approach recommendations

```python
agent = registry.create_agent("analysis")
result = await agent.handle_task("Design a microservices architecture")
```

### CodingAgent
Generates production-ready code:
- Clean, documented implementations
- Error handling included
- Type hints and docstrings
- Best practices applied

```python
agent = registry.create_agent("coding")
code = await agent.handle_task("Create a REST API endpoint for user authentication")
```

### ResearchAgent
Conducts comprehensive research:
- Background and context gathering
- Key facts and data collection
- Multiple perspective analysis
- Resource compilation

```python
agent = registry.create_agent("research")
research = await agent.handle_task("Current state of quantum computing")
```

### ReviewAgent
Provides thorough reviews:
- Overall quality assessment
- Strengths and weaknesses
- Issue identification
- Enhancement suggestions

```python
agent = registry.create_agent("review")
review = await agent.handle_task("Review the system architecture document")
```

## ⚙️ Configuration

### Concurrency Limits

```python
# Set maximum concurrent agents (default: 5)
registry.max_concurrent_agents = 10

# Check current usage
active = len(registry.active_agents)
capacity = (active / registry.max_concurrent_agents) * 100
print(f"Agent capacity: {capacity}%")
```

### Custom Agent Types

```python
from amplifier_mod_agent_registry import BaseAgent

class TranslationAgent(BaseAgent):
    """Custom agent for language translation."""

    async def handle_task(self, task: str) -> str:
        # Use kernel's model provider if available
        if self.kernel and self.kernel.model_providers:
            provider = self.kernel.model_providers.get("default")
            return await provider.generate(
                f"Translate to Spanish: {task}",
                system="You are a professional translator"
            )
        return f"Translation of: {task}"

# Register custom type
registry.register_agent_type("translator", TranslationAgent)

# Use it
translator = registry.create_agent("translator")
spanish = await translator.handle_task("Hello, world!")
```

## 📊 Event System

The registry publishes these events:

| Event | Description | Data |
|-------|-------------|------|
| `agent:start` | Agent created | `{agent_id, type}` |
| `agent:finish` | Agent disposed | `{agent_id, type}` |
| `agent:error` | Agent error occurred | `{agent_id, error}` |
| `agent:limit_check` | Capacity check | `{active, max}` |
| `system:warning` | Capacity warning (>80%) | `{message}` |

## 🔌 Module Interface

```python
class AgentRegistry:
    def create_agent(self, agent_type: str) -> BaseAgent:
        """Create a new agent of specified type."""

    def dispose_agent(self, agent_id: str) -> None:
        """Dispose of an agent and free resources."""

    def list_agent_types(self) -> list[str]:
        """List all available agent types."""

    def register_agent_type(self, name: str, agent_class: type):
        """Register a custom agent type."""

    def get_active_agents(self) -> dict:
        """Get all currently active agents."""
```

## 🏗️ Architecture

```
AgentRegistry
├── Agent Factory
│   ├── Built-in types
│   └── Custom types
├── Lifecycle Manager
│   ├── Creation tracking
│   ├── Disposal handling
│   └── Resource limits
├── Event Publisher
│   └── Kernel integration
└── Agent Types
    ├── AnalysisAgent
    ├── CodingAgent
    ├── ResearchAgent
    └── ReviewAgent
```

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Test specific agent type
pytest tests/test_analysis_agent.py

# Test with coverage
pytest --cov=src tests/
```

## 💡 Use Cases

- **Task Delegation**: Distribute work to specialized agents
- **Parallel Processing**: Multiple agents working simultaneously
- **Quality Assurance**: Review agents checking work
- **Research Automation**: Automated information gathering
- **Code Generation**: Automated implementation from specs

## 🤝 Contributing

Contributions welcome! Ideas for enhancement:
- Additional specialized agent types
- Agent collaboration protocols
- Performance metrics per agent
- Agent skill evolution
- Inter-agent communication

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Links

- **Amplifier Core**: [microsoft/amplifier-core](https://github.com/microsoft/amplifier-core)
- **Main CLI**: [microsoft/amplifier](https://github.com/microsoft/amplifier)