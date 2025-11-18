---
last_updated: 2025-11-18
status: stable
audience: user
---

# User Onboarding Guide - Getting Started with Amplifier

**Welcome!** This guide takes you from installation to productive use of Amplifier's modular AI platform.

---

## Installation

### For Users

> [!IMPORTANT]
> Amplifier runs best on macOS, Linux, and Windows Subsystem for Linux (WSL). Native Windows shells have unresolved issues—use WSL unless you're contributing Windows compatibility fixes.

**Install UV (if you haven't already):**

```bash
# macOS/Linux/WSL
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Install Amplifier CLI:**

```bash
uv tool install git+https://github.com/microsoft/amplifier@next

amplifier init          # optional if you let the first run wizard configure things
amplifier run "Hello, Amplifier!"
amplifier              # enter chat mode
```

**Add recommended collections:**

```bash
amplifier collection add git+https://github.com/microsoft/amplifier-collection-toolkit@main
amplifier collection add git+https://github.com/microsoft/amplifier-collection-design-intelligence@main

# Explore their profiles or agents
amplifier profile use toolkit-dev
amplifier profile use designer
```

Both collections expose agents visible via `/agents` in chat and are the ones prefixed with `toolkit:` or `design-intelligence:`. You can invoke these from any profile.

### For Contributors (workspace)

```bash
# Clone development workspace
git clone --recursive https://github.com/microsoft/amplifier-dev
cd amplifier-dev

# Install for development
./scripts/install-dev.sh

# First-time setup
amplifier init
```

---

## First-Time Setup

```bash
$ amplifier init

Welcome to Amplifier!

Step 1: Provider
Which provider? [1] Anthropic [2] OpenAI [3] Azure OpenAI [4] Ollama: 1

API key: ••••••••
  Get one: https://console.anthropic.com/settings/keys
✓ Saved to ~/.amplifier/keys.env

Model? [1] claude-sonnet-4-5 [2] claude-opus-4-1 [3] custom: 1
✓ Using claude-sonnet-4-5

Step 2: Profile
Which profile? [1] dev [2] base [3] full: 1
✓ Using 'dev' profile

Ready! Try: amplifier run "Hello world"
```

**Note:** Azure OpenAI has additional setup (endpoint, deployment name, auth method). See examples in [amplifier/README.md](../amplifier/README.md#quick-start).

**That's it!** You're configured and ready to use Amplifier.

---

## Environment Variables

Amplifier detects environment variables and uses them as defaults during configuration. If set, you can simply press Enter to confirm instead of typing values.

### Supported Variables

| Provider         | Variable                       | Purpose                             |
| ---------------- | ------------------------------ | ----------------------------------- |
| **Anthropic**    | `ANTHROPIC_API_KEY`            | API key                             |
| **OpenAI**       | `OPENAI_API_KEY`               | API key                             |
| **Azure OpenAI** | `AZURE_OPENAI_ENDPOINT`        | Azure endpoint URL                  |
|                  | `AZURE_OPENAI_DEPLOYMENT`      | Deployment name                     |
|                  | `AZURE_OPENAI_API_KEY`         | API key (if using key auth)         |
|                  | `AZURE_USE_DEFAULT_CREDENTIAL` | Use Azure CLI auth (`true`/`false`) |
| **Ollama**       | `OLLAMA_HOST`                  | Ollama server URL                   |

### Quick Setup with Environment Variables

```bash
# Set your environment
export ANTHROPIC_API_KEY="your-key"

# Run init - detected values shown, just press Enter
amplifier init
```

The wizard shows detected values and lets you confirm or override them.

---

## Shell Completion (Optional)

Enable tab completion in one command. Amplifier will automatically modify your shell configuration.

```bash
amplifier --install-completion
```

**What this does**:

1. Detects your current shell (bash, zsh, or fish)
2. **Adds completion line to your shell config file**:
   - Bash → appends to `~/.bashrc`
   - Zsh → appends to `~/.zshrc`
   - Fish → creates `~/.config/fish/completions/amplifier.fish`
3. Safe to run multiple times (checks if already installed)
4. Shows manual instructions if custom setup detected

**Activate completion**:

```bash
# In your current terminal
source ~/.bashrc  # or ~/.zshrc

# Or just open a new terminal
```

**Tab completion then works everywhere**:

```bash
amplifier pro<TAB>         # Completes to "profile"
amplifier profile u<TAB>   # Completes to "use"
amplifier profile use <TAB> # Lists available profiles
```

---

## Quick Start Usage

### Single Prompts

```bash
# Ask anything
amplifier run "Write a Python hello world script"

# Code analysis
amplifier run "Explain what this code does" < script.py

# With specific profile
amplifier run --profile designer "audit the design system"
```

### Interactive Chat

```bash
# Start chat mode
amplifier

# Available slash commands:
> /help          # Show commands
> /tools         # List available tools
> /agents        # List available agents
> /profile       # Show active profile
> /provider      # Show active provider
> /exit          # Quit
```

### Session Management

```bash
# List recent sessions
amplifier session list

# Resume a session
amplifier session resume <session-id>

# Show session details
amplifier session show <session-id>
```

---

## Configuration Basics

Amplifier uses two complementary systems:

### Settings (Runtime Configuration)

**What**: Which profile to use, provider credentials, model selection  
**Commands**: `amplifier provider use`, `amplifier profile use`  
**Files**: `settings.yaml` (three-tier: local > project > user)  
**Learn more**: [Configuration Management](https://github.com/microsoft/amplifier-config)

### Profiles (Capability Presets)

**What**: Which tools/hooks/agents are available, system instructions  
**Format**: YAML frontmatter + markdown (`.md` files)  
**Inheritance**: Profiles can extend other profiles  
**Learn more**: [Profile Authoring](https://github.com/microsoft/amplifier-profiles)

**How they work together**:
- Settings say: "Use the 'dev' profile with Anthropic as the provider"
- Profiles define: "The 'dev' profile includes filesystem tools, web search, and 5 agents"

In other words: **Settings choose which profile and provider to use. Profiles define what capabilities are available.**

---

Amplifier has 4 configuration dimensions:

### 1. Provider (Which AI Service)

```bash
# Switch provider
amplifier provider use openai

# Interactive: asks where to configure
# Or explicit:
amplifier provider use openai --local      # Just you
amplifier provider use azure --project     # Team
amplifier provider use anthropic --global  # All projects

# Check current
amplifier provider current
```

### 2. Profile (Which Capabilities)

```bash
# Switch profile
amplifier profile use dev          # Development tools
amplifier profile use base         # Essential CLI helpers
amplifier profile use test         # Testing setup
amplifier profile use foundation   # Minimal footprint

# Check current
amplifier profile current

# List available
amplifier profile list
```

### 3. Module (Add Capabilities)

```bash
# Add module
amplifier module add tool-jupyter
amplifier module add tool-custom --project

# Remove module
amplifier module remove tool-jupyter

# See loaded modules
amplifier module current
```

### 4. Source (Where Modules Come From)

```bash
# Override source for local development
amplifier source add tool-bash ~/dev/tool-bash --local

# Remove override
amplifier source remove tool-bash --local

# Check overrides
amplifier source list
```

---

## Understanding Profiles

Profiles are pre-configured **capability sets** that define what's available:

| Profile        | Purpose                    | Tools                    | Agents                                                           | Use When           |
| -------------- | -------------------------- | ------------------------ | ---------------------------------------------------------------- | ------------------ |
| **foundation** | Bare minimum               | None                     | None                                                             | Lightweight checks |
| **base**       | Essential CLI helpers      | filesystem, bash         | None                                                             | Everyday basics    |
| **dev**        | Full development           | base + web, search, task | zen-architect, bug-hunter, modular-builder, explorer, researcher | Daily building     |
| **test**       | Focused testing workflows  | base + task              | None                                                             | Running suites     |
| **full**       | Demo of nearly all modules | Almost everything        | Broad showcase (great for exploration)                           | Feature tours      |

**Profiles define WHAT you can do.**
**Providers define WHERE the AI comes from.**

They're independent - you can use the `dev` profile with any provider (Anthropic/OpenAI/Azure/etc).

---

## Agent Delegation

Amplifier includes specialized agents for specific tasks:

### Available Agents (in dev profile)

| Agent               | Specialty                                         | Example Use                                 |
| ------------------- | ------------------------------------------------- | ------------------------------------------- |
| **zen-architect**   | System design with ruthless simplicity            | Architecture decisions, design reviews      |
| **bug-hunter**      | Systematic debugging                              | Finding root causes, fixing issues          |
| **modular-builder** | Building self-contained modules                   | Creating new components                     |
| **researcher**      | Curated research and synthesis of external info   | Summarising docs, comparing approaches      |
| **explorer**        | Breadth-first exploration of local files & assets | Mapping code ownership, surfacing key files |

### Using Agents

```bash
# In interactive mode
amplifier

> Delegate to zen-architect: Design a caching system
> Use bug-hunter to find issues in src/main.py
> Ask modular-builder to create a validation module
```

Agents work in specialized sub-sessions with focused capabilities.

---

## Usage Examples

### Try Different Providers

```bash
# Try OpenAI temporarily
$ amplifier run --provider openai "write a poem"

# Switch permanently for this project
$ amplifier provider use openai --local
$ amplifier run "write another poem"
[Uses OpenAI from now on]

# Switch back
$ amplifier provider use anthropic --local
```

### Add Community Modules

```bash
# Discover and add module
$ amplifier module add tool-jupyter
Source: git+https://github.com/jupyter-amplifier/tool-jupyter
Configure now? [y/n]: y
API key: ••••
✓ Added

# Use in session
$ amplifier run "analyze this dataset"
```

### Project Team Configuration

```bash
# Configure for team
$ cd ~/team-project
$ amplifier profile use dev --project
$ amplifier provider use azure --project
$ git add .amplifier/settings.yaml
$ git commit -m "Configure project defaults"

# Team member gets it
$ git clone .../team-project
$ amplifier profile current
Profile: dev (from project)
Provider: Azure (from project)
```

### Local Development

```bash
# Override module source
$ amplifier source add tool-bash ~/dev/tool-bash --local
✓ Using local version

# Test changes
$ amplifier run "test bash functionality"

# Remove override when done
$ amplifier source remove tool-bash --local
```

---

## Troubleshooting

### See What's Active

```bash
# Check all configuration
amplifier provider current    # Which AI service
amplifier profile current     # Which profile
amplifier module current      # Which modules loaded
amplifier source list         # Which source overrides
```

### Configuration Not Working

```bash
# Check settings files
cat .amplifier/settings.yaml
cat .amplifier/settings.local.yaml
cat ~/.amplifier/settings.yaml

# Look for override conflicts
amplifier provider current
# Shows resolution chain
```

### Module Not Found

```bash
# Check where it's coming from
amplifier source show tool-custom

# Install if needed
uv pip install amplifier-module-tool-custom

# Or add source
amplifier source add tool-custom git+https://github.com/...
```

### Logs and Debugging

```bash
# Watch activity
amplifier logs

# Filter for specific events
amplifier logs --filter "error"
amplifier logs --filter "tool:"

# Session details
amplifier session show <session-id>
```

---

## Quick Command Reference

### Configuration Commands

```bash
# Provider
amplifier provider use <name> [--scope]
amplifier provider current
amplifier provider list

# Profile
amplifier profile use <name> [--scope]
amplifier profile current
amplifier profile list

# Module
amplifier module add <name> [--scope]
amplifier module remove <name> [--scope]
amplifier module current

# Source
amplifier source add <id> <uri> [--scope]
amplifier source remove <id> [--scope]
amplifier source list
```

### Session Commands

```bash
# New sessions
amplifier run "prompt"                    # Single-shot (auto-persists, shows session ID)
amplifier                                 # Interactive chat (auto-generates session ID)

# Resume sessions
amplifier continue                        # Resume most recent (interactive)
amplifier continue "new prompt"           # Resume most recent (single-shot with context)
amplifier run --resume <id> "prompt"      # Resume specific session (single-shot)

# Session management
amplifier session list                    # List recent sessions
amplifier session resume <id>             # Resume specific session (interactive)
amplifier session delete <id>             # Delete session
amplifier session cleanup                 # Clean up old sessions
```

### Scope Flags

```bash
--local          # Just you in this project
--project        # Whole team (committed)
--global         # All your projects
--profile=name   # Modify specific profile
```

---

## Quick Reference

### Command Pattern

All Amplifier commands follow this pattern:

```
amplifier <noun> <verb> [identifier] [--scope]

Nouns: provider | profile | module | source
Verbs: use | add | remove | list | show | current | reset | create
Scopes: --local | --project | --global | --profile=name
```

### Configuration Scopes

| Scope       | Flag             | Where Stored                     | Who It Affects          |
| ----------- | ---------------- | -------------------------------- | ----------------------- |
| **Local**   | `--local`        | `.amplifier/settings.local.yaml` | Just you (gitignored)   |
| **Project** | `--project`      | `.amplifier/settings.yaml`       | Whole team (committed)  |
| **Global**  | `--global`       | `~/.amplifier/settings.yaml`     | All your projects       |
| **Profile** | `--profile=name` | Profile file                     | That profile definition |

When no scope specified, commands prompt interactively.

---

## Next Steps

1. **Explore profiles**: Try `dev`, `base`, `test`, and `full` to see differences
2. **Try agents**: Delegate tasks to specialized agents
3. **Explore collections**: Install shareable expertise bundles
4. **Build scenario tools**: Create sophisticated multi-stage CLI tools
5. **Create custom profile**: For your specific needs
6. **Read philosophy docs**: Understand the design principles

### Essential Reading

- **[Collections User Guide](https://github.com/microsoft/amplifier-collections/blob/main/docs/USER_GUIDE.md)** - Using collections
- **[Collection Authoring](https://github.com/microsoft/amplifier-collections/blob/main/docs/AUTHORING.md)** - Creating collections
- [SCENARIO_TOOLS_GUIDE.md](SCENARIO_TOOLS_GUIDE.md) - Building sophisticated CLI tools
- **[Profile Authoring](https://github.com/microsoft/amplifier-profiles/blob/main/docs/PROFILE_AUTHORING.md)** - Create custom profiles
- **[Agent Authoring](https://github.com/microsoft/amplifier-profiles/blob/main/docs/AGENT_AUTHORING.md)** - Create custom agents
- **[Profile System Design](https://github.com/microsoft/amplifier-profiles/blob/main/docs/DESIGN.md)** - Profile system architecture
- **[Module Resolution](https://github.com/microsoft/amplifier-module-resolution/blob/main/docs/USER_GUIDE.md)** - Module source management
- [TOOLKIT_GUIDE.md](TOOLKIT_GUIDE.md) - Toolkit utilities for building tools
- [context/KERNEL_PHILOSOPHY.md](context/KERNEL_PHILOSOPHY.md) - Core design principles

---

Welcome to Amplifier! Start with simple tasks, explore the capabilities, and gradually customize your environment. The modular architecture is designed for experimentation - try things, see what works, adjust as needed.

Happy building!

## Using @Mentions in Chat

Reference files directly in your messages using @mention syntax:

```
amplifier run "Explain the kernel design in @docs/AMPLIFIER_AS_LINUX_KERNEL.md"
```

The file content loads automatically while your @mention stays as a reference marker.

**Learn more**: See [MENTION_PROCESSING.md](MENTION_PROCESSING.md) for complete guide.
