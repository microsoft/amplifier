# Amplifier

**AI-powered modular development assistant - currently in early preview.**

> [!CAUTION]
> This project is a research demonstrator. It is in early development and may change significantly. Using permissive AI tools on your computer requires careful attention to security considerations and careful human supervision, and even then things can still go wrong. Use it with caution, and at your own risk, we have NOT built in the safety systems yet. We are performing our _active exploration_ in the open for others to join in the conversation and exploration, not as a product or "official release".

---

## What is Amplifier?

Amplifier brings AI assistance to your command line with a modular, extensible architecture. More info to follow here shortly, for our earlier exploration that this will be racing to supercede, check out [our original version](https://github.com/microsoft/amplifier).

**This CLI is _just one_ interface**—the reference implementation. The real power is the modular platform underneath. Soon you'll see web interfaces, mobile apps, voice-driven coding, and even Amplifier-to-Amplifier collaborative experiences. The community will build custom interfaces, mixing and matching modules dynamically to craft tailored AI experiences.

---

## Quick Start - Zero to Working in 90 Seconds

### Step 1: Install UV (30 seconds)

```bash
# macOS/Linux/WSL
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 2: Run Amplifier (60 seconds)

```bash
# Try it now (auto-setup on first run)
uvx --from git+https://github.com/microsoft/amplifier@next amplifier
```

**First time? Quick setup wizard:**

<details>
<summary><b>With Anthropic Claude (recommended)</b></summary>

```
Provider? [1] Anthropic [2] OpenAI [3] Azure OpenAI [4] Ollama: 1

API key: ••••••••
  Get one: https://console.anthropic.com/settings/keys
✓ Saved

Model? [1] claude-sonnet-4-5 [2] claude-opus-4-1 [3] custom: 1
✓ Using claude-sonnet-4-5

Profile? [1] dev [2] base [3] full: 1
✓ Using 'dev' profile

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

Deployment name: gpt-5-codex
  Note: Use your Azure deployment name, not model name
✓ Configured

Profile? [1] dev [2] base [3] full: 1
✓ Using 'dev' profile

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

Model? [1] gpt-5 [2] gpt-5-mini [3] gpt-5-codex [4] o1 [5] custom: 1
✓ Using gpt-5

Profile? [1] dev [2] base [3] full: 1
✓ Using 'dev' profile

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

Profile? [1] dev [2] base [3] full: 1
✓ Using 'dev' profile

Ready! Starting chat...
>
```

</details>

**That's it!** From nothing to productive AI assistant in 90 seconds.

---

## Alternative Paths

### Quick One-Off Test (If You Have API Key)

```bash
# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Run immediately
uvx --from git+https://github.com/microsoft/amplifier@next amplifier run "Explain async/await in Python"
```

### Install for Regular Use

```bash
# Install globally
uv tool install git+https://github.com/microsoft/amplifier@next

# Configure (if you skipped auto-init)
amplifier init

# Use anywhere
amplifier run "Your prompt"
amplifier  # Start chat mode
```

---

## What Can Amplifier Do?

First of all, this is still VERY early and we have not brought _most_ of our features over from our prior version yet, so keep your expectations low and we'll get it ramped up very quickly over the next week or two. Consider this just an early sneak peek.

- **Generate code** - From simple functions to full applications
- **Debug problems** - Systematic error resolution with the bug-hunter agent
- **Design systems** - Architecture planning with the zen-architect agent
- **Research solutions** - Find patterns and best practices with the researcher agent
- **Build modules** - Use Amplifier to create new Amplifier modules (yes, really!)

**Additional features over prior version:**

- **Modular**: Swap AI providers, tools, and behaviors like LEGO bricks
- **Profile-based**: Pre-configured capability sets for different scenarios
- **Session persistence**: Pick up where you left off, even across projects
- **Extensible**: Build your own modules, interfaces, or entire custom experiences

---

## Supported AI Providers

Amplifier works with multiple AI providers:

- **Anthropic Claude** - Recommended, most tested (Sonnet 4.5, Opus models)
- **OpenAI** - Good alternative (GPT-4o, GPT-4o-mini, o1 models)
- **Azure OpenAI** - Enterprise users with Azure subscriptions (supports managed identity)
- **Ollama** - Local, free, no API key needed (llama3, codellama, etc.)

Switch providers anytime:

```bash
# Switch provider (interactive - prompts for model/config)
amplifier provider use openai

# Or explicit
amplifier provider use anthropic --model claude-opus-4-1
amplifier provider use azure-openai --deployment gpt-5-codex
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
- Use `/help` for special commands
- Use `/provider`, `/profile`, `/module` to configure
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

### Using Profiles

Profiles are pre-configured capability sets for different scenarios:

```bash
# See available profiles
amplifier profile list

# Use a specific profile
amplifier run --profile dev "Your prompt"

# Set as default
amplifier profile use dev
```

**Bundled profiles:**

- `foundation` - Absolute minimum (provider + orchestrator only)
- `base` - Essential tools (filesystem, bash, logging)
- `dev` - Full development setup (web, search, agents) - **Default & recommended**
- `production` - Production-minded exploration (persistent context, safety)
- `full` - Everything enabled

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
- **researcher** - Content research and synthesis
- **modular-builder** - Code implementation

---

## Sessions & Persistence

Every interaction is automatically saved:

```bash
# List your recent sessions (current project only)
amplifier session list

# See all sessions across all projects
amplifier session list --all-projects

# View session details
amplifier session show <session-id>

# Resume a previous session
amplifier session resume <session-id>
```

Sessions are project-scoped—when you're in `/home/user/myapp`, you see only `myapp` sessions. Change directories, see different sessions. Your work stays organized.

---

## Configuration

### Switching Providers

```bash
# Switch provider (interactive - prompts for model)
amplifier provider use openai

# Or explicit
amplifier provider use anthropic --model claude-opus-4-1

# Azure OpenAI (needs endpoint + deployment)
amplifier provider use azure-openai
  Azure endpoint: https://my-resource.openai.azure.com/
  Auth? [1] API key [2] Azure CLI: 2
  Deployment: gpt-5-codex

# Configure where to save
amplifier provider use openai --model gpt-5 --local      # Just you
amplifier provider use anthropic --model claude-opus-4-1 --project  # Team

# See what's active
amplifier provider current
```

### Switching Profiles

```bash
# Switch profile
amplifier profile use dev
amplifier profile use production
amplifier profile use test

# See what's active
amplifier profile current
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

### Creating Custom Profiles

Profiles configure your Amplifier environment with providers, tools, agents, and settings.

**→ [Profile Authoring Guide](https://github.com/microsoft/amplifier-profiles/blob/main/docs/PROFILE_AUTHORING.md)** - Complete guide to creating profiles

**Quick example**:
```yaml
---
profile:
  name: my-profile
  extends: base
tools:
  - module: tool-web
  - module: tool-search
agents:
  include: [zen-architect, researcher]
---
```

**API Reference**: [amplifier-profiles](https://github.com/microsoft/amplifier-profiles)

### Creating Custom Agents

Agents are specialized AI personas for focused tasks.

**→ [Agent Authoring Guide](https://github.com/microsoft/amplifier-profiles/blob/main/docs/AGENT_AUTHORING.md)** - Complete guide to creating agents

**Quick example**:
```yaml
---
meta:
  name: my-agent
  description: Expert in [domain]
providers:
  - module: provider-anthropic
    config: {model: claude-opus-4-1}
---
You are a specialized expert in [domain]...
```

---

## For Developers

### Building on Amplifier

**Core Libraries**:
- **[amplifier-core](https://github.com/microsoft/amplifier-core)** - Kernel mechanisms and contracts
- **[amplifier-profiles](https://github.com/microsoft/amplifier-profiles)** - Profile/agent loading and compilation
- **[amplifier-collections](https://github.com/microsoft/amplifier-collections)** - Collections system
- **[amplifier-config](https://github.com/microsoft/amplifier-config)** - Configuration management
- **[amplifier-module-resolution](https://github.com/microsoft/amplifier-module-resolution)** - Module source resolution

**Reference Implementation**:
- **[amplifier-app-cli](https://github.com/microsoft/amplifier-app-cli)** - CLI application (this implementation)

**Architecture**:
- **[Repository Rules](docs/REPOSITORY_RULES.md)** - Where docs go, what references what
- **[Module Catalog](#modules)** - Available providers, tools, hooks, orchestrators

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
- ✅ Profile-based configuration
- ✅ Agent delegation
- ✅ Session persistence
- ✅ Module loading from git sources

**What's rough around the edges:**

- ⚠️ Other providers need more testing
- ⚠️ Some error messages could be clearer
- ⚠️ Documentation is incomplete in places
- ⚠️ Installation experience will improve

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
