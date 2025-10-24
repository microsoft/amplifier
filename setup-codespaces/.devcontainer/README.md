# Devcontainer Template

GitHub Codespaces configuration with Claude Code pre-installed.

## What's Included

**Tools:**
- Python 3.11 + Node.js LTS
- Claude Code CLI
- GitHub CLI (`gh`)
- Make, Git, Vim

**Resources:**
- 2 CPU cores, 8GB RAM, 32GB storage
- Auto-stops after 30 minutes idle

**Configuration:**
- Git auto-push enabled
- Post-creation status report

## Quick Customization

### Change Container Name
Edit `devcontainer.json`:
```json
{
  "name": "your-project-name"
}
```

### Adjust Resources
```json
{
  "hostRequirements": {
    "cpus": 4,
    "memory": "16gb",
    "storage": "64gb"
  }
}
```

### Add Tools
Browse [available features](https://github.com/devcontainers/features) and add to `features` section.

### Add VS Code Extensions
Add to `customizations.vscode.extensions` array in `devcontainer.json`.

### Project-Specific Setup
Edit `post-create.sh` to add commands (e.g., `make install`).

## Documentation

- [Devcontainer Specification](https://containers.dev/)
- [GitHub Codespaces Docs](https://docs.github.com/en/codespaces)
- [Available Features](https://github.com/devcontainers/features)

**Detailed guides:** Available in `docs-archive/` if you need comprehensive documentation.
