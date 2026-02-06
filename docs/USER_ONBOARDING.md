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
uv tool install git+https://github.com/microsoft/amplifier

amplifier init          # optional if you let the first run wizard configure things
amplifier run "Hello, Amplifier!"
amplifier              # enter chat mode
```

**Add recommended bundles:**

```bash
amplifier bundle add git+https://github.com/microsoft/amplifier-bundle-recipes@main
amplifier bundle add git+https://github.com/microsoft/amplifier-bundle-design-intelligence@main

# Use a bundle
amplifier bundle use recipes
amplifier bundle use design-intelligence
```

Both bundles expose agents visible via `/agents` in chat. You can invoke these from any bundle.

### For Contributors

```bash
# Clone the repos you need to work on
git clone https://github.com/microsoft/amplifier
git clone https://github.com/microsoft/amplifier-core
git clone https://github.com/microsoft/amplifier-app-cli
# ... clone other modules as needed

# Install Amplifier
uv tool install git+https://github.com/microsoft/amplifier

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

Model? [1] claude-sonnet-4-5 [2] claude-opus-4-6 [3] custom: 1
✓ Using claude-sonnet-4-5

Step 2: Bundle
Which bundle? [1] foundation [2] dev [3] full: 1
✓ Using 'foundation' bundle

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
amplifier bun<TAB>         # Completes to "bundle"
amplifier bundle u<TAB>    # Completes to "use"
amplifier bundle use <TAB> # Lists available bundles
```

---

## Quick Start Usage

### Single Prompts

```bash
# Ask anything
amplifier run "Write a Python hello world script"

# Code analysis
amplifier run "Explain what this code does" < script.py

# With specific bundle
amplifier run --bundle design-intelligence "audit the design system"
```

### Interactive Chat

```bash
# Start chat mode
amplifier

# Available slash commands:
> /help          # Show available commands
> /tools         # List available tools
> /agents        # List available agents
> /status        # Show session status
> /config        # Show current configuration
> /think         # Enable read-only plan mode
> /do            # Exit plan mode (allow modifications)
> /clear         # Clear conversation context
> /save          # Save conversation transcript

# To exit: type 'exit' or press Ctrl+C
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

Amplifier uses a bundle-based configuration system:

### Settings (Runtime Configuration)

**What**: Which bundle to use, provider credentials, model selection  
**Commands**: `amplifier provider use`, `amplifier bundle use`  
**Files**: `settings.yaml` (three-tier: local > project > user)

### Bundles (Capability Packages)

**What**: Which tools/hooks/agents are available, system instructions  
**Format**: Markdown with YAML frontmatter (`.md` files)  
**Composition**: Bundles can include other bundles  
**Learn more**: [Bundle Guide](https://github.com/microsoft/amplifier-foundation/blob/main/docs/BUNDLE_GUIDE.md)

**How they work together**:
- Settings say: "Use the 'foundation' bundle with Anthropic as the provider"
- Bundles define: "The 'foundation' bundle includes filesystem tools, web search, and 5 agents"

In other words: **Settings choose which bundle and provider to use. Bundles define what capabilities are available.**

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

### 2. Bundle (Which Capabilities)

```bash
# Switch bundle
amplifier bundle use foundation    # Minimal footprint
amplifier bundle use dev           # Development tools
amplifier bundle use recipes       # Multi-step workflows

# Check current
amplifier bundle current

# List available
amplifier bundle list
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

## Understanding Bundles

Bundles are **capability packages** that define what's available:

| Bundle         | Purpose                    | Tools                    | Agents                                                           | Use When           |
| -------------- | -------------------------- | ------------------------ | ---------------------------------------------------------------- | ------------------ |
| **foundation** | Bare minimum               | filesystem, bash         | None                                                             | Lightweight checks |
| **dev**        | Full development           | base + web, search, task | zen-architect, bug-hunter, modular-builder, explorer, researcher | Daily building     |
| **recipes**    | Multi-step workflows       | base + task              | Recipe execution agents                                          | Complex workflows  |
| **full**       | Demo of nearly all modules | Almost everything        | Broad showcase (great for exploration)                           | Feature tours      |

**Bundles define WHAT you can do.**
**Providers define WHERE the AI comes from.**

They're independent - you can use the `dev` bundle with any provider (Anthropic/OpenAI/Azure/etc).

---

## Agent Delegation

Amplifier includes specialized agents for specific tasks:

### Available Agents (in dev bundle)

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
$ amplifier bundle use dev --project
$ amplifier provider use azure --project
$ git add .amplifier/settings.yaml
$ git commit -m "Configure project defaults"

# Team member gets it
$ git clone .../team-project
$ amplifier bundle current
Bundle: dev (from project)
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
amplifier bundle current      # Which bundle
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
# Session details
amplifier session show <session-id>

# Session logs are written to:
# ~/.amplifier/projects/<project-slug>/sessions/<session-id>/events.jsonl
```

For visual log inspection, see [amplifier-log-viewer](https://github.com/microsoft/amplifier-app-log-viewer).

### Clean Reinstall (Recovery)

If `amplifier update` leaves things in a broken state, or you encounter persistent issues that configuration changes don't fix, this procedure reliably restores a working installation.

**Step 1: Clear Amplifier data directory**

```bash
# Option A: Full reset (recommended - cleanest)
rm -rf ~/.amplifier

# Option B: Preserve session history (keeps transcripts)
cd ~/.amplifier
ls  # See what's there
rm -rf bundles bundles.lock keys.env settings.yaml
# Keep: projects/ (session transcripts)
```

> **Note**: Files like `settings.yaml`, `keys.env`, and `bundles.lock` CAN be preserved, but they may be the source of issues. We recommend clearing them for a clean slate. Use your discretion based on how much you've customized.

**Step 2: Clean UV cache and uninstall**

```bash
# Make sure you're not in an active virtual environment
deactivate 2>/dev/null || true

# Clear UV's cache
uv cache clean

# Uninstall Amplifier
uv tool uninstall amplifier

# Verify it's gone
which amplifier
# Should return nothing or "amplifier not found"
```

**Step 3: Reinstall fresh**

```bash
uv tool install git+https://github.com/microsoft/amplifier
```

**Step 4: Reconfigure and test**

```bash
# Run first-time setup
amplifier init

# Smoke test
amplifier
# Type "Hi" and verify you get a response
# Type "exit" to quit
```

**When to use this**:
- After `amplifier update` breaks functionality
- When module resolution fails unexpectedly
- Persistent errors that don't resolve with config changes
- "Stale state" issues where cached modules conflict

**What Option A (full reset) clears**:
- API keys (`keys.env`) - you'll re-enter during `init`
- Settings (`settings.yaml`) - you'll reconfigure
- Installed bundles (`bundles/`, `bundles.lock`)
- Session history (`projects/`) - conversation transcripts

**What Option B preserves**:
- Session history in `~/.amplifier/projects/` - your conversation transcripts

---

## Quick Command Reference

### Configuration Commands

```bash
# Provider
amplifier provider use <name> [--scope]
amplifier provider current
amplifier provider list

# Bundle
amplifier bundle use <name> [--scope]
amplifier bundle current
amplifier bundle list

# Module
amplifier module add <name> [--scope]
amplifier module remove <name> [--scope]
amplifier module current

# Source
amplifier source add <id> <uri> [--scope]
amplifier source remove <id> [--scope]
amplifier source list

# Notifications (requires notify bundle)
amplifier notify status                   # Show current settings
amplifier notify desktop --enable         # Enable desktop notifications
amplifier notify ntfy --enable --topic X  # Enable push via ntfy.sh
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
--bundle=name    # Modify specific bundle
```

---

## Quick Reference

### Command Pattern

All Amplifier commands follow this pattern:

```
amplifier <noun> <verb> [identifier] [--scope]

Nouns: provider | bundle | module | source
Verbs: use | add | remove | list | show | current | reset | create
Scopes: --local | --project | --global | --bundle=name
```

### Configuration Scopes

| Scope       | Flag             | Where Stored                     | Who It Affects          |
| ----------- | ---------------- | -------------------------------- | ----------------------- |
| **Local**   | `--local`        | `.amplifier/settings.local.yaml` | Just you (gitignored)   |
| **Project** | `--project`      | `.amplifier/settings.yaml`       | Whole team (committed)  |
| **Global**  | `--global`       | `~/.amplifier/settings.yaml`     | All your projects       |
| **Bundle**  | `--bundle=name`  | Bundle file                      | That bundle definition  |

When no scope specified, commands prompt interactively.

---

## Next Steps

1. **Explore bundles**: Try `foundation`, `dev`, and `full` to see differences
2. **Try agents**: Delegate tasks to specialized agents
3. **Add bundles**: Install shareable capability packages
4. **Build scenario tools**: Create sophisticated multi-stage CLI tools
5. **Create custom bundle**: For your specific needs
6. **Read philosophy docs**: Understand the design principles

### Essential Reading

- **[Bundle Guide](https://github.com/microsoft/amplifier-foundation/blob/main/docs/BUNDLE_GUIDE.md)** - Creating and using bundles
- [SCENARIO_TOOLS_GUIDE.md](SCENARIO_TOOLS_GUIDE.md) - Building sophisticated CLI tools
- **[Agent Authoring](https://github.com/microsoft/amplifier-foundation/blob/main/docs/AGENT_AUTHORING.md)** - Create custom agents
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
