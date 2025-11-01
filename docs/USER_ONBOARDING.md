---
last_updated: 2025-10-18
status: stable
audience: user
---

# User Onboarding Guide - Getting Started with Amplifier

**Welcome!** This guide takes you from installation to productive use of Amplifier's modular AI platform.

---

## Installation

### For Users

**Try without installing:**

```bash
# Run directly with uvx
uvx --from git+https://github.com/microsoft/amplifier@next amplifier run "Hello, Amplifier!"

# Start chat mode
uvx --from git+https://github.com/microsoft/amplifier@next amplifier
```

**Install globally:**

```bash
# Install as a tool
uv tool install git+https://github.com/microsoft/amplifier@next

# Then use anywhere
amplifier run "Your prompt"
amplifier  # Chat mode

# First-time setup
amplifier init
```

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
amplifier run --profile production "deploy to prod"
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
amplifier profile use production   # Production safety
amplifier profile use test         # Testing setup

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

| Profile        | Purpose          | Tools                  | Agents                    | Use When          |
| -------------- | ---------------- | ---------------------- | ------------------------- | ----------------- |
| **foundation** | Absolute minimum | None                   | None                      | Testing core      |
| **base**       | Essential tools  | filesystem, bash       | None                      | Basic work        |
| **dev**        | Development      | base + web, search     | zen-architect, bug-hunter | Daily development |
| **production** | Production       | base + web, monitoring | None                      | Deployments       |
| **test**       | Testing          | base + task            | None                      | Running tests     |
| **full**       | Everything       | All tools              | All agents                | Exploration       |

**Profiles define WHAT you can do.**
**Providers define WHERE the AI comes from.**

They're independent - you can use the `dev` profile with any provider (Anthropic/OpenAI/Azure/etc).

---

## Agent Delegation

Amplifier includes specialized agents for specific tasks:

### Available Agents (in dev profile)

| Agent               | Specialty                              | Example Use                            |
| ------------------- | -------------------------------------- | -------------------------------------- |
| **zen-architect**   | System design with ruthless simplicity | Architecture decisions, design reviews |
| **bug-hunter**      | Systematic debugging                   | Finding root causes, fixing issues     |
| **modular-builder** | Building self-contained modules        | Creating new components                |

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
$ amplifier profile use production --project
$ amplifier provider use azure --project
$ git add .amplifier/settings.yaml
$ git commit -m "Configure project defaults"

# Team member gets it
$ git clone .../team-project
$ amplifier profile current
Profile: production (from project)
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
amplifier run "prompt"           # Single interaction
amplifier                        # Interactive chat
amplifier session list           # Recent sessions
amplifier session resume <id>    # Continue session
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

| Scope | Flag | Where Stored | Who It Affects |
|-------|------|--------------|----------------|
| **Local** | `--local` | `.amplifier/settings.local.yaml` | Just you (gitignored) |
| **Project** | `--project` | `.amplifier/settings.yaml` | Whole team (committed) |
| **Global** | `--global` | `~/.amplifier/settings.yaml` | All your projects |
| **Profile** | `--profile=name` | Profile file | That profile definition |

When no scope specified, commands prompt interactively.

---

## Next Steps

1. **Explore profiles**: Try `dev`, `production`, `test` to see differences
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
