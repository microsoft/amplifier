# GitHub Codespaces Setup

Quick setup for GitHub Codespaces with Claude Code pre-installed.

## Quick Start

**1. Copy template to your project:**
```bash
cp -r setup-codespaces/.devcontainer /path/to/your/project/
cd /path/to/your/project
git add .devcontainer/
git commit -m "Add Codespaces support"
git push
```

**2. Create Codespace:**
```bash
# Via GitHub CLI
gh codespace create --repo your-username/your-repo

# Or via VS Code
# Press F1 → "Codespaces: Create New Codespace"
```

**3. Start working:**
```bash
# Claude Code is pre-installed
claude --version
claude
```

## What's Included

- Python 3.11 + Node.js LTS
- Claude Code CLI
- GitHub CLI (`gh`)
- Auto-stops after 30 minutes idle (saves costs)

## Managing Codespaces

```bash
# List all Codespaces
gh codespace list

# Connect to one
gh codespace code --codespace <name>

# Stop when done
gh codespace stop --codespace <name>

# Delete permanently
gh codespace delete --codespace <name>
```

## Customization

Edit `.devcontainer/devcontainer.json` to add tools or change resources.

See [.devcontainer/README.md](.devcontainer/README.md) for details.

## Learn More

- [GitHub Codespaces Docs](https://docs.github.com/en/codespaces)
- [Devcontainer Spec](https://containers.dev/)
- [Claude Code](https://claude.ai/claude-code)

---

**Detailed guides:** Available in `docs-archive/` if you need comprehensive documentation.
