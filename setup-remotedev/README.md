# Remote Development Setup for GitHub Codespaces

**Run multiple projects simultaneously in persistent cloud environments**

This directory contains a reusable devcontainer template and management tools for setting up GitHub Codespaces that persist even when you disconnect.

## What This Is

A ready-to-use GitHub Codespaces configuration that you can copy to any project repository. Each project gets its own isolated cloud environment with Claude Code pre-installed.

**Key Features:**
- ✅ Runs in the cloud - continues when you disconnect
- ✅ Claude Code pre-configured and ready to use
- ✅ Work on multiple projects simultaneously
- ✅ Reconnect from any device and continue where you left off
- ✅ Simple CLI scripts to manage multiple Codespaces

## Why Use This

**Problem:** Running multiple development projects locally exhausts your machine's resources. Work stops when you close your laptop.

**Solution:** Each project runs in its own GitHub Codespace. Codespaces persist in the cloud, so work continues even during your commute. Reconnect from anywhere to pick up exactly where you left off.

## What's Included

```
setup-remotedev/
├── .devcontainer/           # Reusable template - copy to any project
│   ├── devcontainer.json    # Minimal, production-ready config
│   ├── post-create.sh       # Automatic Claude Code setup
│   ├── POST_SETUP_README.md # Post-creation instructions
│   └── README.md            # Template documentation
└── docs/                    # Detailed guides
    ├── SETUP_GUIDE.md       # Copy template to a project
    ├── USAGE_GUIDE.md       # Manage multiple Codespaces
    ├── WORKFLOW_PATTERNS.md # Multi-project workflows
    └── TROUBLESHOOTING.md   # Common issues and solutions
```

## Quick Start

### For Your First Project

1. **Copy the template** to your project repository:
   ```bash
   cp -r setup-remotedev/.devcontainer /path/to/your/project/
   ```

2. **Create a Codespace** from GitHub or VS Code

3. **Start coding** - Claude Code is ready to use

See [SETUP_GUIDE.md](docs/SETUP_GUIDE.md) for detailed instructions.

### Managing Multiple Codespaces

Once you have several Codespaces running:

```bash
# List all active Codespaces
gh codespace list

# Connect to a specific one
gh codespace code --codespace <name>

# Delete unused ones
gh codespace delete --codespace <name>
```

See [USAGE_GUIDE.md](docs/USAGE_GUIDE.md) for complete management guide.

## Documentation

**Getting Started:**
- [Setup Guide](docs/SETUP_GUIDE.md) - Copy template and create first Codespace
- [Usage Guide](docs/USAGE_GUIDE.md) - Manage multiple Codespaces effectively

**Advanced:**
- [Workflow Patterns](docs/WORKFLOW_PATTERNS.md) - Multi-project development patterns
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

**Template Details:**
- [Template README](.devcontainer/README.md) - Devcontainer configuration details

## Prerequisites

- GitHub account with Codespaces access
- `gh` CLI installed locally (for management scripts)
- VS Code with GitHub Codespaces extension (recommended)

## Use Cases

**Parallel Feature Development:**
Work on multiple features in isolation. Each Codespace is independent - no context switching overhead.

**Multi-Project Work:**
Maintain separate Codespaces for different projects. Switch between them instantly without local setup.

**Location Independence:**
Start work at the office, continue on your commute (work persists in cloud), finish at home from any device.

**Team Collaboration:**
Share consistent development environments. Every team member gets the same setup automatically.

## Philosophy

This setup follows amplifier's core principles:

**Ruthless Simplicity:**
- Minimal devcontainer config - only essentials
- Simple scripts wrapping `gh` CLI
- No complex orchestration needed

**Modular Design:**
- Each Codespace is a self-contained "brick"
- Clear interfaces (copy template, manage with gh CLI)
- Template is reusable across any project

## Next Steps

1. **Read the setup guide:** [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)
2. **Copy template to your first project**
3. **Create your first Codespace**
4. **Explore workflow patterns:** [docs/WORKFLOW_PATTERNS.md](docs/WORKFLOW_PATTERNS.md)

## Related Resources

**Amplifier's Existing Devcontainer:**
- `.devcontainer/` - Amplifier's production devcontainer setup
- `.devcontainer/OPTIMIZING_FOR_CODESPACES.md` - Optimization tips

**GitHub Documentation:**
- [GitHub Codespaces Docs](https://docs.github.com/en/codespaces)
- [Devcontainer Spec](https://containers.dev/)

---

**Questions?** See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) or check the [usage guide](docs/USAGE_GUIDE.md).
