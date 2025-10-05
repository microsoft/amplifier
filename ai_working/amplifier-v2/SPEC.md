# Amplifier Kernel: Modular Python Design and Implementation

## Overview

The Amplifier project is reimagined as a **small, protected core** with an extensible “userland” of modules, analogous to an operating system kernel with pluggable services. The goal is to support a rich ecosystem of AI-driven tools, agents, and workflows without hard-coding policy into the core. All high-level capabilities – language model integrations, agent behaviors, tools/commands, and multi-step workflows – are implemented as **loadable modules** rather than monolithic code. This modular architecture allows rapid experimentation in userland while keeping the kernel stable and minimal. Key design goals include:

- **Fully Modular Design:** Every feature (LLM providers, agents, tools, workflows, etc.) lives in its own module, which the kernel can dynamically load or unload. The kernel provides only interfaces and a plugin registry to manage these modules.
- **Multi-Model Support:** The kernel supports multiple LLM backends concurrently. Separate modules (e.g. `amplifier-mod-llm-openai` and `amplifier-mod-llm-claude`) act as adapters for different model APIs, enabling a “dual model” setup (e.g. one hosted API and one local model) to ensure neutrality and flexible budgeting.
- **Async-First Concurrency:** The kernel is built on asynchronous Python (asyncio) to allow concurrent task execution, parallel LLM calls, and non-blocking I/O. This supports complex workflows like parallel reasoning (“ultra-think”) and simultaneous tool usage by agents.
- **Plugin Registry & Message Bus:** A lightweight plugin system lets modules register their capabilities (tools, agents, hooks, etc.) with the core at startup. The kernel exposes an **async message bus** (or capability router) for modules to communicate and coordinate tasks. Tools and agents publish requests (e.g. “invoke LLM” or “run tool X”) onto the bus, and the appropriate module handles the event – decoupling callers from specific implementations.
- **Dynamic Configuration (“Modes”):** The kernel can be configured at runtime with a declarative manifest or via a builder API to load a specific set of modules for a given purpose (a _mode_). A mode manifest lists which commands, sub-agents, hooks, and philosophy docs to enable for a workflow. This allows multiple **Amplifier configurations** (e.g. a “blog writer” mode, a “code assistant” mode) to coexist and be easily shared without affecting the core installation.
- **Independence from External Tools:** Unlike the current Amplifier, which relies on the VS Code Cloud/Claude Code SDK and its rigid directory hooks, the new kernel operates standalone in Python. This “ejects” Amplifier from the Cloud Code environment, removing external constraints. It will still integrate with IDEs or version control via modules, but these integrations are optional layers rather than prerequisites.

By adhering to these principles, the Amplifier Kernel will provide core services – identity, capability security, scheduling (task budgeting), a typed message bus, audit logging, and memory isolation – while pushing all domain-specific logic into interchangeable modules. Below we outline the repository structure and key components, followed by annotated code sketches for the core and sample modules.

## Repository Structure

Each component of the system is a separate Python package (and repository) to enable isolated development and versioning of modules. The proposed layout is:

```plaintext
amplifier-core/               # Core kernel package
└── amplifier_core/
    ├── __init__.py
    ├── kernel.py          # Core kernel class: plugin manager, bus, scheduler
    ├── plugin.py          # Plugin registry and base Module definitions
    ├── message_bus.py     # Async message bus / capability router
    ├── interfaces/        # Interface definitions for pluggable components
    │   ├── model.py       # Interface for LLM model providers
    │   ├── tool.py        # Interface for tools/commands
    │   ├── agent.py       # Interface for agents (or agent lifecycle hooks)
    │   └── workflow.py    # Interface for complex workflows (metacognitive recipes)
    ├── config.py          # Config/manifest loader and builder utilities
    └── cli.py             # (Optional) core CLI entry-point or orchestrator logic
    •••
amplifier/                    # Amplifier CLI package (user-facing CLI tool)
└── amplifier/
    ├── __init__.py
    ├── __main__.py        # Entry point to launch the CLI (e.g. `python -m amplifier`)
    └── cli.py             # CLI argument parsing, loads config, starts kernel
    •••
amplifier-mod-llm-openai/     # Module: OpenAI LLM provider
└── amplifier_mod_llm_openai/
    ├── __init__.py
    ├── openai_provider.py # Implements LLM provider interface for OpenAI API
    └── plugin.py          # Registers OpenAI provider with the kernel
    •••
amplifier-mod-llm-claude/     # Module: Claude (Anthropic) LLM provider
└── amplifier_mod_llm_claude/
    ├── __init__.py
    ├── claude_provider.py # Implements LLM provider interface for Claude API
    └── plugin.py          # Registers Claude provider with the kernel
    •••
amplifier-mod-philosophy/     # Module: Philosophy/knowledge injection
└── amplifier_mod_philosophy/
    ├── __init__.py
    ├── philosophy.py      # Loads philosophy docs and provides context injection hooks
    └── plugin.py          # Registers philosophy module (hooks) with the kernel
    •••
amplifier-mod-agent-registry/ # Module: Agent registry and management
└── amplifier_mod_agent_registry/
    ├── __init__.py
    ├── registry.py        # Defines available agent roles and lifecycle hooks
    └── plugin.py          # Registers agent types and hooks with the kernel
    •••
amplifier-mod-tool-ultra_think/   # Module: "Ultra-Think" multi-step reasoning tool
└── amplifier_mod_tool_ultra_think/
    ├── __init__.py
    ├── ultra_think.py     # Implements the UltraThink multi-step reasoning workflow
    └── plugin.py          # Registers ultra-think tool with the kernel
    •••
amplifier-mod-tool-blog_generator/ # Module: Blog post generation tool
└── amplifier_mod_tool_blog_generator/
    ├── __init__.py
    ├── blog_generator.py  # Implements a blog post generation workflow
    └── plugin.py          # Registers blog generator tool with the kernel
    •••
```

Each `amplifier-mod-*` repository is a plugin that can be developed and versioned independently, interfacing with the core via well-defined contracts. This separation follows the vision of keeping the kernel tiny and pushing all policy and functionality to userland modules. Next, we detail the core kernel implementation, followed by examples of module implementations.

## Amplifier Core Implementation (`amplifier-core`)

The Amplifier core is responsible for managing plugins, routing messages between components, and enforcing any global policies (e.g. scheduling, permission checks) without embedding specific tool logic. It provides: a **plugin registry system** for modules to register themselves; an **async message bus** for communication; and abstract **interfaces (contracts)** that modules must implement (for model providers, tools, agents, etc.). The core may also include a minimal CLI or runtime orchestrator to initialize modules and handle high-level input/output.

### Plugin Registry and Module Loading

The kernel exposes a plugin registration interface that modules use to load their capabilities. Each plugin module defines a `Plugin` class (subclass of a base `AmplifierModule`) with a `register()` method. On startup, the kernel (or a CLI script) discovers and instantiates each `Plugin`, calling its `register()` to let the module attach its functionality. This design allows adding new tools or models by simply installing a module – no core code changes needed.

```python
# amplifier_core/plugin.py
from abc import ABC, abstractmethod

class AmplifierModule(ABC):
    """Base class that all plugin modules must subclass."""
    @abstractmethod
    async def register(self, kernel: "AmplifierKernel") -> None:
        """Register this module's capabilities with the kernel."""
        pass
```

The kernel will provide a method to load modules either programmatically or via config. For example, using Python’s import mechanisms or entry points:

```python
# amplifier_core/kernel.py (excerpt)
import importlib
from .plugin import AmplifierModule

class AmplifierKernel:
    def __init__(self):
        self.bus = MessageBus()
        self.model_providers = {}   # e.g. {'openai': provider_instance, ...}
        self.tools = {}            # e.g. {'ultra_think': tool_instance, ...}
        self.agents = {}           # active agent instances or definitions
        # (Additional core components like scheduling, identity, etc. can be added here)

    async def register_module(self, module: AmplifierModule) -> None:
        """Load a single module (plugin) into the kernel."""
        await module.register(self)  # module populates kernel with its capabilities
        # (We might keep track of loaded modules if needed for later reference)

    async def load_modules_by_name(self, module_names: list[str]) -> None:
        """Dynamically import and register a list of modules given their package names."""
        for name in module_names:
            mod = importlib.import_module(name)
            plugin_class = getattr(mod, "Plugin", None)
            if plugin_class is None:
                raise ImportError(f"No Plugin class found in module {name}")
            plugin_instance = plugin_class()
            await self.register_module(plugin_instance)
```

In practice, the CLI or a builder will call `load_modules_by_name()` with the list of desired modules (from a manifest or config). Each module’s `Plugin.register()` method will then hook its features into the kernel (examples given in sample modules below).

### Async Message Bus and Capability Routing

The **message bus** is the communication backbone of the kernel. It allows different modules and agents to communicate via events and commands, without hard dependencies on each other. The bus supports **publish/subscribe** for events (e.g. “tool invoked”, “LLM response ready”, “agent started”) and ensures handlers run asynchronously so multiple tasks can proceed concurrently. The bus also enables the kernel to mediate access (implementing capability-based security if needed) – for example, an agent might emit a `RunTool` event that the kernel routes to the appropriate tool plugin if the agent has permission.

```python
# amplifier_core/message_bus.py
import asyncio
from collections import defaultdict
from typing import Callable, Any

class Event:
    """Generic event object for message bus communication."""
    def __init__(self, type: str, data: dict[str, Any] = None, source: str = ""):
        self.type = type
        self.data = data or {}
        self.source = source  # originator (e.g. agent or tool name)

class MessageBus:
    def __init__(self):
        # Map event type -> list of handler coroutines (callbacks)
        self._subscribers: dict[str, list[Callable[[Event], Any]]] = defaultdict(list)
        self.loop = asyncio.get_event_loop()

    def subscribe(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        """Subscribe a handler coroutine to a specific event type."""
        self._subscribers[event_type].append(handler)

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers, running handlers concurrently."""
        handlers = self._subscribers.get(event.type, [])
        for handler in handlers:
            # Schedule each handler (don't await immediately to allow concurrent execution)
            self.loop.create_task(handler(event))
        # Optionally, could gather tasks if we need to ensure completion:
        # await asyncio.gather(*(handler(event) for handler in handlers))
```

Modules can subscribe to relevant events during their `register()` phase. For example, a philosophy injection module might subscribe to a `"prompt:before_send"` event to modify prompts before an LLM call, or an agent could subscribe to `"tool:result"` events to consume tool outputs. The bus design above simply schedules all handlers and does not await them in sequence, ensuring **concurrent execution** when multiple components react to an event. Handlers themselves are `async` functions and can use `await` internally for I/O or model calls, allowing deep concurrency across the system.

**Scheduling and concurrency:** Complex workflows can be orchestrated by publishing events for sub-tasks and letting multiple LLM calls or tools run in parallel. The kernel could include a scheduler or budgeting system to manage how many tasks run at once or to track token usage per agent (for cost control), but initially we rely on asyncio’s cooperative scheduling. The kernel’s `MessageBus` can be extended to enforce limits (e.g. only N concurrent LLM calls) or priorities as needed.

**Capability routing:** The message bus can act as a **capability router** by exposing specific event types or channels only to authorized modules. For example, an agent might get a capability object to call a tool (which under the hood publishes a `tool:invoke` event); if the agent is not granted that capability, it cannot publish on that channel. This aligns with a capability-secure design where the kernel controls access without hard-coding policy into each agent. In the initial implementation, we assume all loaded modules are trusted, but the architecture allows adding permission checks later (for instance, the kernel could wrap certain sensitive operations in guard conditions).

### Interface Contracts for Models, Tools, and Agents

To ensure **contract-first design**, we define abstract base classes for each kind of pluggable component. These interfaces specify the methods and async signatures that modules must implement. By coding against interfaces, the core and agents can remain agnostic to the specific implementations (e.g. which LLM API is used, or what a particular tool does), enhancing modularity. Key interfaces include:

```python
# amplifier_core/interfaces/model.py
from abc import ABC, abstractmethod

class BaseModelProvider(ABC):
    """Interface for language model provider modules (e.g. OpenAI, Claude)."""
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a completion or response from the model given a prompt."""
        ...

# amplifier_core/interfaces/tool.py
class BaseTool(ABC):
    """Interface for tool/command modules that perform a discrete action."""
    name: str  # human-readable name or identifier for the tool
    @abstractmethod
    async def run(self, **kwargs) -> Any:
        """Execute the tool's action asynchronously and return the result."""
        ...

# amplifier_core/interfaces/agent.py
class BaseAgent(ABC):
    """Interface for agents (autonomous task handlers) if needed."""
    @abstractmethod
    async def handle_task(self, task: Any) -> Any:
        """Receive a task (e.g. a user query or goal) and process it (possibly using tools)."""
        ...

# amplifier_core/interfaces/workflow.py
class BaseWorkflow(ABC):
    """Interface for multi-step workflows or recipes (could also be represented as Tools)."""
    @abstractmethod
    async def run(self, **kwargs) -> Any:
        """Execute the workflow, potentially invoking sub-tools or sub-agents."""
        ...
```

**LLM Providers:** Modules implementing `BaseModelProvider` (like OpenAI or Claude adapters) will expose an async `generate` method that the kernel or agents call to get LLM outputs. This could be extended with streaming support or other endpoints (embedding, etc.), but `generate` covers the basic chat/completion functionality. The kernel might keep a registry `kernel.model_providers` mapping names to provider instances, allowing an agent or tool to select a model (e.g., `kernel.model_providers["openai"].generate(...)`).

**Tools/Commands:** Tools are atomic capabilities that perform actions – such as executing a code analysis, generating text, or performing file I/O. Each tool has a unique `name` and implements an async `run`. Tools can internally call LLM providers, interact with the file system, or even invoke other tools. The kernel will register tools in a dictionary (`kernel.tools`) so that an agent can invoke them by name. In the current Amplifier, many **commands and sub-agent behaviors** (like `ultra-think`, blog post generation, commit, etc.) can be modeled as tools in this sense.

**Agents and Hooks:** Agents are higher-level orchestrators (for example, an agent managing a multi-turn conversation or supervising a workflow). In the new design, an agent could simply be a special kind of tool or workflow – one that continuously reads user input, plans actions, invokes other tools, and produces output. We might not need a complex Agent class initially; instead, an “agent” can be composed from tools and workflows. However, we allow for an `BaseAgent` interface if needed to encapsulate agent-specific logic (like maintaining state or goals).

Additionally, **lifecycle hooks** (like events for agent start/stop, or pre/post tool execution) are supported via the message bus. Modules can subscribe to events such as `"agent:start"` or `"tool:completed"` to implement cross-cutting concerns (logging, monitoring, memory updates). For example, an agent registry module might log each agent’s actions, or a memory module could listen for conversation updates to save context. The kernel’s role is to emit these events at appropriate times (e.g. when an agent is instantiated or a tool returns a result). This flexible hook system avoids hard-coded behavior and allows modules to inject behavior (for instance, a **philosophy module** could use a hook to prepend guidelines to prompts before each LLM call, as described below).

### Core Orchestrator and CLI

The core library can be used programmatically (e.g., in a Python script or REPL) or via a CLI entry point for end-users. We provide a minimal CLI in the `amplifier` package that uses the core to load modules and execute tasks or interactive sessions. The CLI might support commands such as `amp init` (to initialize a project or mode), `amp run <mode>` (to execute a one-off workflow), or an interactive shell for on-the-fly queries.

**Dynamic Mode Loading:** One important CLI function is to apply a **mode manifest** – a declarative config that specifies which modules (tools, agents, philosophies, etc.) to load for a given use-case. This could be a YAML/JSON file or a section in a config. The CLI will parse the manifest and instruct the kernel to load the listed modules. For example: if `blog-mode.yaml` lists the OpenAI provider, the blog generator tool, and a writing philosophy doc, the CLI will load those modules into the kernel instance. This satisfies the requirement for quickly switching between multiple Amplifier configurations (“modes”) without manual reconfiguration.

Below is a conceptual snippet of how the CLI might initialize the kernel with modules based on a mode name or manifest:

```python
# amplifier/cli.py (simplified illustration)
import argparse, asyncio, importlib
from amplifier_core.kernel import AmplifierKernel
from amplifier_core import config  # utilities to load manifest

def main():
    parser = argparse.ArgumentParser(description="Amplifier CLI")
    parser.add_argument("--mode", help="Name of the mode (configuration) to load")
    parser.add_argument("--run", help="Optional command or tool to run in this mode")
    args = parser.parse_args()
    mode = args.mode or "default"

    async def _run():
        kernel = AmplifierKernel()
        # Load module list from a manifest (could be a YAML file named after the mode)
        module_names = config.load_mode_manifest(mode)  # e.g. returns ["amplifier_mod_llm_openai", "amplifier_mod_tool_blog_generator", ...]
        await kernel.load_modules_by_name(module_names)
        if args.run:
            # If a specific tool/command is requested, invoke it and print result
            result = await kernel.tools[args.run].run()
            print(result)
        else:
            # Otherwise enter an interactive loop (not fully implemented here)
            print(f"Interactive mode '{mode}' activated. Type a query or command:")
            # Pseudocode: read user input, dispatch to an agent or tool, etc.
    # Run the async setup
    asyncio.run(_run())
```

In practice, the CLI would handle more (like interactive conversations with an agent, printing outputs nicely, error handling, etc.), but the above demonstrates using a manifest to compose the kernel instance. **Declarative configuration** could also be achieved via a fluent builder API. For instance, a `KernelBuilder` class could allow chaining method calls to add modules or set parameters, then produce a configured `AmplifierKernel`. For initial simplicity, manifest files are straightforward and align with the concept of a mode manifest that can be shared and versioned among users.

With the core kernel defined, we now illustrate how various modules implement these interfaces and register themselves to provide Amplifier’s features.

## Sample Module Implementations

Each module extends the core by providing a specific capability. We provide examples for: two LLM provider modules (`amplifier-mod-llm-openai` and `amplifier-mod-llm-claude`), a philosophy injection module, an agent registry module, and two tool/workflow modules (UltraThink and BlogGenerator). These samples demonstrate how the core interfaces are used in practice. Each module’s **`plugin.py`** file is responsible for initializing the module and registering it with the kernel on load.

### OpenAI LLM Provider Module (`amplifier-mod-llm-openai`)

**Purpose:** Enable Amplifier to call OpenAI’s GPT models via OpenAI’s API. This module implements the `BaseModelProvider` interface and registers itself so that agents or tools can invoke OpenAI completions.

**Key components:**

- `openai_provider.py`: Defines `OpenAIProvider` class with an async `generate` method calling the OpenAI API.
- `plugin.py`: Contains a `Plugin` class (subclass of `AmplifierModule`) whose `register()` method adds an OpenAIProvider instance to the kernel's model providers registry.

**Implementation highlights:** The provider stores an API key (from env or config) and model name (defaulting to `gpt-4` or another specified engine). The `generate` method uses OpenAI’s SDK (which we assume provides an asyncio-compatible client; if not, one could use `asyncio.to_thread` or an HTTP client).

```python
# amplifier_mod_llm_openai/openai_provider.py
import os, openai
from amplifier_core.interfaces.model import BaseModelProvider

class OpenAIProvider(BaseModelProvider):
    def __init__(self, model_name: str = "gpt-4", api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        openai.api_key = self.api_key  # configure global API key

    async def generate(self, prompt: str, **kwargs) -> str:
        """Call OpenAI's chat completion API to get a response."""
        # Note: openai.ChatCompletion.create is typically sync; in a real implementation,
        # we might wrap it in an executor or use an async HTTP library.
        response = await openai.ChatCompletion.acreate(  # using hypothetical async method `.acreate`
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        text = response["choices"][0]["message"]["content"]
        return text
```

The `Plugin` class in this module creates an `OpenAIProvider` and registers it under a key (e.g. `"openai"`) in the kernel’s model provider registry:

```python
# amplifier_mod_llm_openai/plugin.py
from amplifier_core.plugin import AmplifierModule
from amplifier_core.kernel import AmplifierKernel
from .openai_provider import OpenAIProvider

class Plugin(AmplifierModule):
    async def register(self, kernel: AmplifierKernel) -> None:
        """Register OpenAI model provider with the kernel."""
        provider = OpenAIProvider()  # Initialize with default model (or could load config)
        # Add to kernel's model providers so it can be used by agents/tools
        await kernel.add_model_provider("openai", provider)
```

Here, `AmplifierKernel.add_model_provider` is a helper that simply stores the provider in `kernel.model_providers` dict and potentially performs any setup (in this draft, we can assume it just sets `kernel.model_providers[name] = provider`). After this registration, other modules can access `kernel.model_providers["openai"]` to invoke the OpenAI model.

This modular approach means we could swap out or update the OpenAI module independently (for example, to support new parameters or models) without modifying the kernel or other modules. It also allows the system to have multiple providers loaded (e.g., OpenAI and Claude) and even use them in combination (one agent could query both models for comparison, etc.). This addresses the **dual-model** requirement from the vision, ensuring the kernel is not tied to a single AI backend.

### Claude LLM Provider Module (`amplifier-mod-llm-claude`)

**Purpose:** Similarly to OpenAI module, this provides access to Anthropic’s Claude model via their API. It implements `BaseModelProvider` and registers itself as e.g. `"claude"` in the kernel.

**Implementation highlights:** The structure is analogous to OpenAI’s. It would use Anthropic’s Python SDK or HTTP API. For brevity, we outline the key parts:

```python
# amplifier_mod_llm_claude/claude_provider.py
import os, anthropic
from amplifier_core.interfaces.model import BaseModelProvider

class ClaudeProvider(BaseModelProvider):
    def __init__(self, model: str = "claude-2", api_key: str = None):
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Client(api_key=self.api_key)  # hypothetical SDK client

    async def generate(self, prompt: str, **kwargs) -> str:
        """Call Anthropic Claude API to get a completion."""
        # Using anthropic client with async (pseudo-code; actual SDK usage may differ)
        response = await self.client.acomplete(
            prompt=anthropic.HUMAN_PROMPT + prompt + anthropic.AI_PROMPT,
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1000)
        )
        return response.completion
```

And its plugin registers the provider:

```python
# amplifier_mod_llm_claude/plugin.py
from amplifier_core.plugin import AmplifierModule
from amplifier_core.kernel import AmplifierKernel
from .claude_provider import ClaudeProvider

class Plugin(AmplifierModule):
    async def register(self, kernel: AmplifierKernel) -> None:
        """Register Claude model provider with the kernel."""
        provider = ClaudeProvider()
        await kernel.add_model_provider("claude", provider)
```

By having both OpenAI and Claude modules loaded, the Amplifier can route requests to either model. For example, a workflow might use OpenAI for one task and Claude for another, or compare outputs. The kernel could also implement **budgeting and scheduling** policies across providers – e.g., ensuring that combined usage stays within a certain token limit – since it has a unified view of all model calls (this could be built on top of the message bus or via wrappers on `add_model_provider` to track usage). These adapters validate the kernel’s neutrality: it remains **LLM-agnostic**, simply holding references to providers without special-casing their logic.

### Philosophy/Knowledge Injection Module (`amplifier-mod-philosophy`)

**Purpose:** Inject _philosophy documents_ (guiding principles, patterns, or “metacognitive recipes”) into the AI’s context. In Amplifier’s current design, there are various philosophy and strategy documents (in `.ai/docs` and similar) that agents use for guidance. This module makes such knowledge available at runtime, ensuring all agents/tools adhere to shared principles. It can also implement the notion of **context packs** or knowledge bases that are mounted for reference.

**Implementation highlights:** The module might load a set of markdown files containing philosophies or workflow recipes. During operation, it hooks into the kernel’s events to add this context. For example, before an LLM call is made, the module could prepend relevant philosophy text to the prompt. Or if an agent enters a certain mode, the module could provide a summary of guidelines. We utilize the message bus to achieve this injection cleanly, without altering the core prompt logic. The module subscribes to a `prompt:before_send` event (which the kernel or agent should emit before calling an LLM) and modifies the prompt.

```python
# amplifier_mod_philosophy/philosophy.py
import glob

class PhilosophyModule:
    def __init__(self, docs_path: str = "philosophy_docs/"):
        # Load all philosophy documents (e.g., .md files) into memory
        self.documents = []
        for fname in glob.glob(f"{docs_path}/*.md"):
            with open(fname, 'r') as f:
                self.documents.append(f.read())

    def inject_guidance(self, prompt: str) -> str:
        """Prepend or append philosophy guidance to the prompt."""
        # Simple strategy: prepend all docs content (could be more selective in practice)
        combined_docs = "\n\n".join(self.documents)
        return f"{combined_docs}\n\n{prompt}"
```

The plugin sets up the event hook using the kernel’s message bus:

```python
# amplifier_mod_philosophy/plugin.py
from amplifier_core.plugin import AmplifierModule
from amplifier_core.kernel import AmplifierKernel
from amplifier_core.message_bus import Event
from .philosophy import PhilosophyModule

class Plugin(AmplifierModule):
    async def register(self, kernel: AmplifierKernel) -> None:
        """Register philosophy injection hooks with the kernel."""
        philosophy = PhilosophyModule()  # load philosophy docs from default path
        # Define an async handler that injects philosophy into prompts
        async def on_prompt(event: Event):
            if event.type == "prompt:before_send":
                prompt_text = event.data.get("prompt")
                if prompt_text:
                    # modify the prompt in-place
                    event.data["prompt"] = philosophy.inject_guidance(prompt_text)
        # Subscribe the handler to the bus event
        kernel.bus.subscribe("prompt:before_send", on_prompt)
```

In this implementation, whenever any part of the system is about to send a prompt to a model, it should publish a `prompt:before_send` event with the prompt text in `event.data`. The philosophy module’s handler will catch that and augment the prompt with the loaded philosophy content. This way, all model queries automatically include the team’s accumulated wisdom, best practices, or debugging strategies, without each agent/tool needing to manually load those docs. This mechanism realizes the **metacognitive recipes** concept – structured guidance that shapes AI behavior – by treating those recipe documents as just another input injected at runtime. The kernel itself **does not interpret the content** of philosophy docs or enforce their usage; it merely provides the hook mechanism for this module to plug in the context. The philosophy docs can be updated or extended independently (with versioning and tags for scope as noted in the vision), and different modes might load different sets of docs via this module (for instance, a “zen” mode could load an additional Zen guide file, etc.).

### Agent Registry Module (`amplifier-mod-agent-registry`)

**Purpose:** Manage registration and lifecycle of **sub-agents** – specialized agents that handle specific tasks or domains. In Amplifier’s current system there are many agent definitions (e.g. “analysis-engine”, “bug-hunter”, “integration-specialist”, etc. as seen in the `.claude/agents` directory). The agent registry module provides a way to declare these roles and instantiate agents on demand, without hardcoding them in the kernel. It can also implement any global agent-related hooks (like logging agent activity, or enforcing that only a certain number of agents run in parallel to reduce cognitive load).

**Implementation highlights:** The module might define multiple agent classes (subclasses of `BaseAgent` or simply encapsulating an LLM with a specific prompt prefix). Each agent could be associated with a name and capabilities. The registry can expose a method to create an agent by name. On registration, it could inform the kernel of available agent types, or pre-instantiate some if needed. For simplicity, we illustrate it with a couple of dummy agent classes and a create method.

```python
# amplifier_mod_agent_registry/registry.py
from amplifier_core.interfaces.agent import BaseAgent

class AnalysisAgent(BaseAgent):
    async def handle_task(self, task):
        # A simple implementation: use an LLM to analyze the task description
        prompt = f"Analyze the following request and break it down:\n{task}"
        # Assume kernel or model provider is accessible via global or passed context
        return await kernel.model_providers["openai"].generate(prompt)

class CodingAgent(BaseAgent):
    async def handle_task(self, task):
        prompt = f"Implement the following feature:\n{task}\nProvide code solution."
        return await kernel.model_providers["openai"].generate(prompt)

class AgentRegistry:
    def __init__(self):
        self.agent_classes = {
            "analysis": AnalysisAgent,
            "coding": CodingAgent,
            # ... register other agent types
        }
    def create_agent(self, agent_type: str, **kwargs) -> BaseAgent:
        """Instantiate an agent of the given type (if registered)."""
        cls = self.agent_classes.get(agent_type)
        if not cls:
            raise ValueError(f"No such agent type: {agent_type}")
        agent = cls(**kwargs)
        # (Optionally, do any initialization like injecting kernel reference if needed)
        return agent
```

The plugin uses this registry to possibly add agents to the kernel’s management. Exactly how the kernel handles agents can vary: it might keep a pool or just create as needed. Here we’ll simply attach the registry to the kernel for others to use, and perhaps subscribe to agent lifecycle events for logging.

```python
# amplifier_mod_agent_registry/plugin.py
from amplifier_core.plugin import AmplifierModule
from amplifier_core.kernel import AmplifierKernel
from .registry import AgentRegistry

class Plugin(AmplifierModule):
    async def register(self, kernel: AmplifierKernel) -> None:
        """Register agent types and hooks with the kernel."""
        registry = AgentRegistry()
        kernel.agent_registry = registry  # Attach registry to kernel for global access

        # Example: subscribe to an event when a new agent is started
        async def on_agent_start(event):
            if event.type == "agent:start":
                agent_type = event.data.get("type")
                kernel.bus.publish(Event("log", {"message": f"Agent started: {agent_type}"}))
        kernel.bus.subscribe("agent:start", on_agent_start)
```

With this module, whenever an agent is needed, another part of the system (like a workflow or the CLI) can call `kernel.agent_registry.create_agent("analysis")` to get a new agent instance. The agent can then be given a task or goal to handle. For example, a workflow might spin up an “analysis” agent to process a complex request. This design cleanly separates the definition of agent roles from the kernel. New agent types can be added by contributing new classes and updating the registry map, all within this module’s scope.

Moreover, the registry can enforce limits or track agent usage: e.g. if too many agents are active, it could queue requests (addressing the concern that running 10 agents at once is taxing). It can also house the **shared logic for agent lifecycle** (like broadcasting `agent:start` and `agent:finish` events that other modules or the kernel might listen to for audit or cleanup). This satisfies the need for clear modular architecture for sub-agents and hooks, by making agent management a dedicated module.

### UltraThink Workflow Tool Module (`amplifier-mod-tool-ultra_think`)

**Purpose:** Implement the **“ultra-think”** workflow – a multi-step reasoning process used in Amplifier to deeply analyze or brainstorm a problem. This was mentioned as a key workflow that many agents rely on. We implement it as a tool (or workflow) module so that it can be invoked as a single command but internally perform complex actions (potentially involving multiple LLM calls in parallel, followed by a synthesis).

**Implementation highlights:** The UltraThink tool likely takes a question or topic, generates multiple parallel lines of thought, and then combines them. We demonstrate how an async-first design allows us to launch concurrent model calls to simulate “thinking in parallel,” then aggregate the results. The tool uses the kernel’s model providers (e.g. OpenAI) and could also leverage multiple models or an agent if desired. For simplicity, the example will use one model type for parallel brainstorming and summarization.

```python
# amplifier_mod_tool_ultra_think/ultra_think.py
import asyncio
from amplifier_core.interfaces.tool import BaseTool

class UltraThinkTool(BaseTool):
    name = "ultra_think"
    def __init__(self, kernel):
        self.kernel = kernel  # store kernel to access models or other tools

    async def run(self, topic: str) -> str:
        """
        Perform an 'ultra-think' deep analysis on the given topic.
        This spawns multiple parallel LLM queries and then synthesizes their outputs.
        """
        # Step 1: Launch parallel thoughtful prompts
        model = self.kernel.model_providers.get("openai") or next(iter(self.kernel.model_providers.values()))
        prompts = [
            f"Think deeply about '{topic}' from a philosophical perspective.",
            f"Analyze '{topic}' from a practical perspective.",
            f"Critique the concept of '{topic}' and identify potential issues."
        ]
        # Run all prompts concurrently
        results = await asyncio.gather(*(model.generate(p) for p in prompts))

        # Step 2: Synthesize the results
        combined = "\n=== THOUGHT ===\n".join(results)
        synthesis_prompt = f"Given these multiple perspectives on '{topic}', provide a concise summary and insight:\n{combined}"
        summary = await model.generate(synthesis_prompt)
        return summary
```

In this code, three prompts are sent out concurrently to the same model (for illustration – they could also go to different models for diversity). Once all results come back, they are concatenated and a follow-up prompt asks the model to summarize them. The use of `asyncio.gather` means the three initial calls happen in parallel, showcasing the **async-first architecture** benefitting complex workflows. If each call took (say) 5 seconds, running them concurrently yields a total time close to 5 seconds, rather than 15 if done sequentially. The kernel’s design supports this by not enforcing a global lock on model calls (the only limitation might be API rate limits, which could be handled by the scheduling/budgeting layer if needed).

The plugin for this module registers the UltraThinkTool so it becomes available via the kernel:

```python
# amplifier_mod_tool_ultra_think/plugin.py
from amplifier_core.plugin import AmplifierModule
from amplifier_core.kernel import AmplifierKernel
from .ultra_think import UltraThinkTool

class Plugin(AmplifierModule):
    async def register(self, kernel: AmplifierKernel) -> None:
        """Register the UltraThink tool in the kernel."""
        tool = UltraThinkTool(kernel)
        await kernel.add_tool(tool)
```

After registration, users (or agents) can invoke this tool by name. For example, if running interactively, a user might type a command that the CLI recognizes as a tool invocation: `!ultra_think "quantum computing ethics"` (depending on CLI syntax). The CLI or an agent would then call `await kernel.tools["ultra_think"].run(topic="quantum computing ethics")` and present the result. Because UltraThink is implemented as a module, it can be improved or modified independently. It could be expanded to use multiple sub-agents for each perspective, or integrate with the philosophy module to fetch relevant guiding principles, etc., all without needing kernel changes.

### Blog Generator Workflow Module (`amplifier-mod-tool-blog_generator`)

**Purpose:** Provide a workflow to turn an idea or outline into a polished blog post – a concrete example of a **metacognitive recipe** that non-developers might use (as mentioned by Amplifier’s stakeholders). This module demonstrates how a higher-level content creation task can be encapsulated as a tool that coordinates multiple steps (drafting, reviewing, refining) behind the scenes.

**Implementation highlights:** The BlogGenerator tool likely takes an input (like a short description or outline of a blog post) and produces a full article. Internally it might: prompt an LLM to create a draft, then possibly prompt the LLM (or another model or agent) to review and improve that draft (simulating a “reviewer” role), and finally return the revised draft. This shows how a tool can chain multiple LLM calls (or even use other tools, like a grammar checker if one existed). We illustrate a simple two-step version (draft, then refine):

```python
# amplifier_mod_tool_blog_generator/blog_generator.py
from amplifier_core.interfaces.tool import BaseTool

class BlogGeneratorTool(BaseTool):
    name = "blog_generator"
    def __init__(self, kernel):
        self.kernel = kernel

    async def run(self, topic_or_outline: str) -> str:
        """
        Generate a blog post based on a given topic or outline.
        """
        model = self.kernel.model_providers.get("openai") or next(iter(self.kernel.model_providers.values()))
        # Step 1: Draft the blog post
        prompt = f"Write a detailed, well-structured blog post about: {topic_or_outline}"
        draft = await model.generate(prompt, max_tokens=1024)

        # Step 2: Refine the draft (e.g., improve clarity and add a conclusion)
        refine_prompt = f"Improve the following draft to be more clear and engaging, then conclude it:\n\n{draft}"
        refined = await model.generate(refine_prompt, max_tokens=512)
        return refined
```

This tool assumes the presence of at least one model provider (prefers OpenAI if available). After getting the initial draft, it asks for an improvement. In a more advanced scenario, the refining step could involve a second model or a different approach (like splitting the draft into sections and using specialized agents to critique each). But even this simple pipeline demonstrates the **workflow orchestration** capability: the user invokes one command and under the hood multiple LLM calls occur. Because the core and message bus are async, these could even be run in parallel if we wanted (though in this logical sequence they are serial). If needed, events could be published at each step (e.g., a `tool:blog_generator:step` event) to which a UI module could subscribe to show progress, or a logging module could record the draft and final output for auditing.

Registering the blog tool:

```python
# amplifier_mod_tool_blog_generator/plugin.py
from amplifier_core.plugin import AmplifierModule
from amplifier_core.kernel import AmplifierKernel
from .blog_generator import BlogGeneratorTool

class Plugin(AmplifierModule):
    async def register(self, kernel: AmplifierKernel) -> None:
        """Register the BlogGenerator tool in the kernel."""
        tool = BlogGeneratorTool(kernel)
        await kernel.add_tool(tool)
```

Once loaded, this tool can be invoked by name (e.g., `kernel.tools["blog_generator"].run("AI in Education")`). Non-technical users could employ it through a simple prompt or UI, achieving the Amplifier team’s goal of letting people leverage structured AI workflows without needing to write code or understand the implementation details.

## Putting It All Together

The above components illustrate the initial bootstrap of a **Python-based Amplifier kernel** and its ecosystem of modules. This design supports all the current Amplifier features while addressing the modularity and maintainability concerns:

- **Multiple LLM APIs:** accomplished via separate `amplifier-mod-llm-*` modules for OpenAI and Claude (and extensible to others), fulfilling the dual-adapter approach. The kernel remains model-agnostic.
- **Agents and Sub-Agents:** managed via the Agent Registry and potentially specialized tool modules. We can represent complex agent behaviors as combinations of simpler tools and workflows, all loaded through the plugin system.
- **Tools/Commands:** each Amplifier “command” (commit, plan execution, etc.) can be a module implementing the Tool interface. We showed UltraThink and BlogGenerator as examples, but similarly one could port other existing commands (like `commit`, `review-code`) into this framework. They would all register via `kernel.add_tool`, making them addressable through the bus or CLI.
- **Philosophy and Context Docs:** kept in userland and injected at runtime by a module, rather than being baked into every prompt. This preserves the **philosophy documents** as first-class, shareable artifacts that influence behavior without bloating the kernel.
- **Modes and Configuration:** the system supports mode manifests to bundle specific sets of modules and context for particular use cases. For example, a “coding assistant” mode might load coding-related agents, tools, and coding philosophy, whereas a “blog assistant” mode loads writing tools and docs. The kernel’s `load_modules_by_name` (or a future `kernel.load_mode_manifest`) provides the mechanism to realize `amp init --mode X` functionality.
- **Async Orchestration:** All interactions – from LLM calls to tool execution – are designed to be `async`, enabling concurrency. The UltraThink example specifically demonstrates parallel calls. This aligns with keeping the system efficient and able to leverage parallelism where possible (for speed or diversity of thought).
- **No External SDK Dependency:** The Python kernel does not rely on the VS Code Cloud/Claude Code SDK. We avoid its enforced structure and instead implement our own lightweight hook and context system. This makes Amplifier more flexible (editors or environments can be integrated via additional modules or simple APIs) and easier to install/use (just Python packages).
- **Audit and Replay:** While not fully implemented in the stub, the architecture allows easy insertion of logging/audit modules. For instance, one could have a module subscribe to all `tool:invoke` and `tool:result` events or wrap model providers to log prompts and responses. These logs can be saved for replay or debugging sessions, supporting the audit/replay goal of the kernel.
- **Security and Isolation:** The kernel provides a point to enforce capability-based restrictions. In this initial design, all modules have full access to the kernel’s structures (for flexibility), but the intent is to later introduce permission scopes. For example, an untrusted tool module might only be given a restricted subset of the message bus or be prevented from calling certain kernel methods. The foundations laid (the message bus and the distinct registration of capabilities) will make it feasible to add such checks without redesign.

**Repository layout and development:** Each module can be developed in isolation, as it depends only on the `amplifier-core` interfaces. This encourages community contributions – a developer can create a new tool or agent module in its own repo, and as long as it adheres to the interfaces and registration protocol, any Amplifier Kernel instance can load it. To facilitate discovery, a central **plugin registry** (e.g. using Python entry points or a simple index of known `amplifier-mod-*` packages) can be provided, but it’s not strictly required. The core’s stability is maintained by having clear contracts and tests for those contracts. Changes to the kernel or interfaces can be validated against all official modules’ test suites to ensure compatibility.

In summary, this modular Python kernel design achieves the vision of Amplifier as a tiny kernel with a rich, extensible userland. It preserves existing Amplifier capabilities (multi-agent workflows, philosophy-guided operations, complex tool chains) while making the system more maintainable and flexible. Crucially, it lays the groundwork for future enhancements like mode sharing, context pack mounting, and fine-grained security, all aligned with the **AI OS kernel** concept and the team’s strategic goals for the project.
