# Amplifier

**AI-powered modular development assistant - currently in early preview.**

> [!CAUTION]
> This project is a research demonstrator. It is in early development and may change significantly. Using permissive AI tools on your computer requires careful attention to security considerations and careful human supervision, and even then things can still go wrong. Use it with caution, and at your own risk, we have NOT built in the safety systems yet. We are performing our _active exploration_ in the open for others to join in the conversation and exploration, not as a product or "official release".

> [!NOTE]
> **Looking for the earlier Claude Code-based version?** The previous version of Amplifier, built on top of Claude Code, has been moved to the [`amplifier-claude`](https://github.com/microsoft/amplifier/tree/amplifier-claude) branch.

---

## What is Amplifier?

Amplifier brings AI assistance to your command line with a modular, extensible architecture.

**This CLI is _just one_ interface**—the reference implementation. The real power is the modular platform underneath. Soon you'll see web interfaces, mobile apps, voice-driven coding, and even Amplifier-to-Amplifier collaborative experiences. The community will build custom interfaces, mixing and matching modules dynamically to craft tailored AI experiences.

---

## Quick Start - Zero to Working in 90 Seconds

> [!IMPORTANT]
> Amplifier is currently developed and tested on macOS, Linux, and Windows Subsystem for Linux (WSL). Native Windows shells have known issues—use WSL unless you're actively contributing Windows fixes.

### Step 1: Install UV (30 seconds)

```bash
# macOS/Linux/WSL
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 2: Install Amplifier (30 seconds)

```bash
uv tool install git+https://github.com/microsoft/amplifier
```

### Step 3: Run Amplifier (30 seconds)

```bash
# First-time wizard (auto-detects missing config)
amplifier init

# Ask a question
amplifier run "Explain async/await in Python"

# Start chat mode
amplifier
```

### Step 4: Add bundles (optional)

```bash
# Add additional capability bundles
amplifier bundle add git+https://github.com/microsoft/amplifier-bundle-recipes@main
amplifier bundle add git+https://github.com/microsoft/amplifier-bundle-design-intelligence@main

# Use a bundle
amplifier bundle use recipes
```

Bundles ship focused agents you can invoke by name. Use `/agents` in chat to see available agents like `recipes:recipe-author` or `design-intelligence:component-designer`.

**First time? Quick setup wizard:**

<details>
<summary><b>With Anthropic Claude (recommended)</b></summary>

```
Provider? [1] Anthropic [2] OpenAI [3] Azure OpenAI [4] Ollama: 1

API key: ••••••••
  Get one: https://console.anthropic.com/settings/keys
✓ Saved

Model? [1] claude-sonnet-4-5 [2] claude-opus-4-6 [3] custom: 1
✓ Using claude-sonnet-4-5

Ready! Starting chat...

Ready! Starting chat...
>
```

</details>

<details>
<summary><b>With Azure OpenAI (enterprise)</b></summary>

```
Provider? [1] Anthropic [2] OpenAI [3] Azure OpenAI [4] Ollama: 3

Azure endpoint: https://my-resource.openai.azure.com/
✓ Saved

Authentication? [1] API key [2] Azure CLI (az login): 2
✓ Using DefaultAzureCredential
  (Works with 'az login' locally or managed identity in Azure)

Deployment name: gpt-5.2
  Note: Use your Azure deployment name, not model name
✓ Configured

Ready! Starting chat...
>
```

</details>

<details>
<summary><b>With OpenAI</b></summary>

```
Provider? [1] Anthropic [2] OpenAI [3] Azure OpenAI [4] Ollama: 2

API key: ••••••••
  Get one: https://platform.openai.com/api-keys
✓ Saved

Model? [1] gpt-5.2 [2] gpt-5.1-codex [3] gpt-5.2-pro [4] custom: 1
✓ Using gpt-5.2

Ready! Starting chat...
>
```

</details>

<details>
<summary><b>With Ollama (local, free)</b></summary>

```
Provider? [1] Anthropic [2] OpenAI [3] Azure OpenAI [4] Ollama: 4

Model? [1] llama3 [2] codellama [3] mistral [4] custom: 1
✓ Using llama3

Make sure Ollama is running:
  ollama serve
  ollama pull llama3

Ready! Starting chat...
>
```

</details>

**That's it!** From nothing to productive AI assistant in 90 seconds.

## What Can Amplifier Do?

First of all, this is still VERY early and we have not brought _most_ of our features over yet, so keep your expectations low and we'll get it ramped up very quickly over the next week or two. Consider this just an early sneak peek.

- **Generate code** - From simple functions to full applications
- **Debug problems** - Systematic error resolution with the bug-hunter agent
- **Design systems** - Architecture planning with the zen-architect agent
- **Research solutions** - Find patterns and best practices with the researcher agent
- **Build modules** - Use Amplifier to create new Amplifier modules (yes, really!)

**Key features:**

- **Modular**: Swap AI providers, tools, and behaviors like LEGO bricks
- **Bundle-based**: Composable configuration packages for different scenarios
- **Session persistence**: Pick up where you left off, even across projects
- **Extensible**: Build your own modules, bundles, or entire custom experiences

**Developer Tools:**

- **[Log Viewer](https://github.com/microsoft/amplifier-app-log-viewer)**: Web-based tool for debugging sessions with real-time log streaming and interactive JSON inspection

```bash
# Install and run the log viewer while developing
uv tool install git+https://github.com/microsoft/amplifier-app-log-viewer@main
amplifier-log-viewer
```

---

## Supported AI Providers

Amplifier works with multiple AI providers:

- **Anthropic Claude** - Recommended, most tested (Sonnet 4.5, Opus 4.6, Haiku 4.5)
- **OpenAI** - Good alternative (GPT-5.2, GPT-5.2-Pro, GPT-5.1-Codex)
- **Azure OpenAI** - Enterprise users with Azure subscriptions (supports managed identity)
- **Ollama** - Local, free, no API key needed (llama3, codellama, etc.)

Switch providers anytime:

```bash
# Switch provider (interactive - prompts for model/config)
amplifier provider use openai

# Or explicit
amplifier provider use anthropic --model claude-opus-4-6
amplifier provider use azure-openai --deployment gpt-5.2
```

> **Note**: We've done most of our early testing with Anthropic Claude. Other providers are supported but may have rough edges we're actively smoothing out.

---

## Basic Usage

### Interactive Chat Mode

```bash
# Start a conversation
amplifier

# Or explicitly
amplifier run --mode chat
```

In chat mode:

- Context persists across messages
- Use `/help` to see available commands
- Use `/tools`, `/agents`, `/status`, `/config` to inspect session
- Use `/think` and `/do` to toggle plan mode
- Type `exit` or Ctrl+C to quit

### Single Commands

```bash
# Get quick answers
amplifier run "Explain async/await in Python"

# Generate code
amplifier run "Create a REST API for a todo app with FastAPI"

# Debug issues
amplifier run "Why does this code throw a TypeError: [paste code]"
```

### Using Bundles

Bundles are composable configuration packages that define tools, providers, agents, and behaviors:

```bash
# See current bundle (foundation is the default)
amplifier bundle current

# List available bundles
amplifier bundle list

# Use a specific bundle for one command
amplifier run --bundle recipes "Your prompt"

# Set as default
amplifier bundle use foundation
```

**The `foundation` bundle** is the default and includes:

- **Tools**: filesystem, bash, web, search, task delegation
- **Agents**: 14 specialized agents (zen-architect, bug-hunter, git-ops, web-research, explorer, etc.)
- **Behaviors**: logging, redaction, streaming UI, todo tracking

Most users never need to change bundles—foundation provides everything for development work.

### Working with Agents

Specialized agents for focused tasks:

```bash
# Let the AI delegate to specialized agents
amplifier run "Design a caching layer with careful consideration"
# The AI will use zen-architect when appropriate

# Or request specific agents
amplifier run "Use bug-hunter to debug this error: [paste error]"
```

**Bundled agents:**

- **zen-architect** - System design with ruthless simplicity
- **bug-hunter** - Systematic debugging
- **web-research** - Web research and content fetching
- **modular-builder** - Code implementation
- **explorer** - Breadth-first exploration of local code, docs, and other files with citation-ready summaries

---

## Sessions & Persistence

Every interaction is automatically saved:

```bash
# Resume most recent session
amplifier continue

# Resume with new prompt (single-shot mode)
amplifier continue "follow-up question"

# List your recent sessions (current project only)
amplifier session list

# See all sessions across all projects
amplifier session list --all-projects

# View session details
amplifier session show <session-id>

# Resume a specific session (interactive mode)
amplifier session resume <session-id>

# Resume specific session with new prompt
amplifier run --resume <session-id> "new question"
```

Sessions are project-scoped—when you're in `/home/user/myapp`, you see only `myapp` sessions. Change directories, see different sessions. Your work stays organized.

---

## Configuration

### Switching Providers

```bash
# Switch provider (interactive - prompts for model)
amplifier provider use openai

# Or explicit
amplifier provider use anthropic --model claude-opus-4-6

# Azure OpenAI (needs endpoint + deployment)
amplifier provider use azure-openai
  Azure endpoint: https://my-resource.openai.azure.com/
  Auth? [1] API key [2] Azure CLI: 2
  Deployment: gpt-5.2

# Configure where to save
amplifier provider use openai --model gpt-5.2 --local      # Just you
amplifier provider use anthropic --model claude-opus-4-6 --project  # Team

# See what's active
amplifier provider current
```

### Switching Bundles

```bash
# See current bundle
amplifier bundle current

# Switch bundle
amplifier bundle use foundation
amplifier bundle use recipes

# Add external bundles
amplifier bundle add git+https://github.com/microsoft/amplifier-bundle-recipes@main

# See what's active
amplifier bundle list
```

### Adding Capabilities

```bash
# Add module
amplifier module add tool-jupyter
amplifier module add tool-custom --project

# See loaded modules
amplifier module current
```

See [docs/USER_ONBOARDING.md#quick-reference](docs/USER_ONBOARDING.md#quick-reference) for complete command reference.

---

## Customizing Amplifier

### Creating Custom Bundles

Bundles configure your Amplifier environment with providers, tools, agents, and behaviors.

**→ [Bundle Authoring Guide](https://github.com/microsoft/amplifier-foundation/blob/main/docs/BUNDLE_GUIDE.md)** - Complete guide to creating bundles

### Creating Custom Agents

Agents are specialized AI personas for focused tasks.

**→ [Agent Authoring Guide](https://github.com/microsoft/amplifier-foundation/blob/main/docs/AGENT_AUTHORING.md)** - Complete guide to creating agents

---

## For Developers

### Building on Amplifier

**Core Libraries**:

- **[amplifier-core](https://github.com/microsoft/amplifier-core)** - Ultra-thin kernel (~2,600 lines) providing module protocols, session lifecycle, and hooks
- **[amplifier-foundation](https://github.com/microsoft/amplifier-foundation)** - Bundle composition library + the default `foundation` bundle

**Reference Implementation**:

- **[amplifier-app-cli](https://github.com/microsoft/amplifier-app-cli)** - CLI application (this implementation)

**Architecture**:

- **[Repository Rules](docs/REPOSITORY_RULES.md)** - Where docs go, what references what
- **[Module Catalog](docs/MODULES.md)** - Available providers, tools, hooks, orchestrators

---

## What's Next

> **Note**: Amplifier is under active development. Some documentation links are being consolidated. If you encounter issues, please report them.

---

## The Vision

**Today**: A powerful CLI for AI-assisted development.

**Tomorrow**: A platform where:

- **Multiple interfaces** coexist - CLI, web, mobile, voice, IDE plugins
- **Community modules** extend capabilities infinitely
- **Dynamic mixing** - Amplifier composes custom solutions from available modules
- **AI builds AI** - Use Amplifier to create new modules with minimal manual coding
- **Collaborative AI** - Amplifier instances work together on complex tasks

The modular foundation we're building today enables all of this. You're getting in early on something that's going to fundamentally change how we work with AI.

---

## Current State (Be Aware)

This is an **early preview release**:

- APIs are stabilizing but may change
- Some features are experimental
- Documentation is catching up with code
- We're moving fast—breaking changes happen

**What works today:**

- ✅ Core AI interactions (Anthropic Claude)
- ✅ Bundle-based configuration
- ✅ Agent delegation
- ✅ Session persistence
- ✅ Module loading from git sources

**What's rough around the edges:**

- ⚠️ Other providers need more testing
- ⚠️ Some error messages could be clearer
- ⚠️ Documentation is incomplete in places
- ⚠️ Installation experience will improve

**Having issues?** See [Troubleshooting](docs/USER_ONBOARDING.md#troubleshooting) including [Clean Reinstall](docs/USER_ONBOARDING.md#clean-reinstall-recovery) for recovery steps.

**Join us on this journey!** Fork, experiment, build modules, share feedback. This is the ground floor.

---

## Contributing

> [!NOTE]
> This project is not currently accepting external contributions, but we're actively working toward opening this up. We value community input and look forward to collaborating in the future. For now, feel free to fork and experiment!

Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit [Contributor License Agreements](https://cla.opensource.microsoft.com).

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
