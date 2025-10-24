# Devcontainer Template Documentation

This devcontainer configuration provides a GitHub Codespaces-ready environment with Claude Code pre-installed.

## What This Template Provides

**Pre-installed Tools:**
- Python 3.11
- Node.js (LTS)
- Claude Code CLI
- GitHub CLI (`gh`)
- Make
- Git (pre-configured)
- Common development utilities

**Resource Configuration:**
- 2 CPU cores
- 8GB RAM
- 32GB storage

**Automatic Setup:**
- Git configured for auto-push
- Claude Code installed and ready
- Post-creation status report

## Files in This Template

```
.devcontainer/
├── devcontainer.json        # Container configuration
├── post-create.sh           # Automatic setup script
├── POST_SETUP_README.md     # Displayed after creation
└── README.md                # This file
```

## Customization Guide

### Changing the Container Name

**Edit `devcontainer.json`:**
```json
{
  "name": "your-project-name",  // Change this
  ...
}
```

### Adjusting Resources

**For larger projects, increase resources:**
```json
{
  "hostRequirements": {
    "cpus": 4,        // More CPUs
    "memory": "16gb", // More RAM
    "storage": "64gb" // More disk
  }
}
```

**Note:** Larger machines cost more per hour.

### Adding Development Tools

**Add to the `features` section:**

```json
{
  "features": {
    // Already included:
    "ghcr.io/jungaretti/features/make:1": {},
    "ghcr.io/jungaretti/features/vim:1": {},
    "ghcr.io/anthropics/devcontainer-features/claude-code:1": {},

    // Add additional tools:
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/aws-cli:1": {},
    "ghcr.io/devcontainers/features/terraform:1": {}
  }
}
```

**Browse available features:** [devcontainers/features](https://github.com/devcontainers/features)

### Adding VS Code Extensions

**Edit the `customizations.vscode.extensions` array:**

```json
{
  "customizations": {
    "vscode": {
      "extensions": [
        // Already included:
        "anthropic.claude-code",
        "GitHub.copilot",

        // Add your favorites:
        "ms-python.black-formatter",
        "esbenp.prettier-vscode",
        "dbaeumer.vscode-eslint"
      ]
    }
  }
}
```

### Project-Specific Setup

**Edit `post-create.sh` to add setup commands:**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Existing setup...
echo "🔧  Configuring Git..."
git config --global push.autoSetupRemote true

# Add your project setup:
echo "📦  Installing project dependencies..."
make install  # or npm install, pip install, etc.

echo "🗄️  Setting up database..."
make db-setup  # if needed

echo "✅  Project setup complete!"
```

### Customizing the Base Image

**Change the base image in `devcontainer.json`:**

```json
{
  // Default: Python 3.11
  "image": "mcr.microsoft.com/devcontainers/python:1-3.11-bookworm",

  // Or use different base:
  // "image": "mcr.microsoft.com/devcontainers/javascript-node:1-18-bookworm",
  // "image": "mcr.microsoft.com/devcontainers/rust:1-bullseye",
  // "image": "mcr.microsoft.com/devcontainers/go:1-1.21-bookworm"
}
```

**Browse base images:** [devcontainers/images](https://github.com/devcontainers/images)

### Port Forwarding

**Forward ports automatically:**

```json
{
  "forwardPorts": [3000, 8000, 8080],

  "portsAttributes": {
    "3000": {
      "label": "Frontend",
      "onAutoForward": "notify"
    },
    "8000": {
      "label": "API",
      "onAutoForward": "openBrowser"
    }
  }
}
```

### Environment Variables

**Set environment variables:**

```json
{
  "containerEnv": {
    "MY_VAR": "value",
    "NODE_ENV": "development",
    "PYTHONUNBUFFERED": "1"
  }
}
```

**Or use a `.env` file:**

```json
{
  "runArgs": ["--env-file", "${localWorkspaceFolder}/.env"]
}
```

## Advanced Customization

### Using a Dockerfile

**Instead of a pre-built image, use a custom Dockerfile:**

```json
{
  // Remove "image" line, add:
  "build": {
    "dockerfile": "Dockerfile",
    "context": ".",
    "args": {
      "VARIANT": "3.11"
    }
  }
}
```

**Create `.devcontainer/Dockerfile`:**
```dockerfile
FROM mcr.microsoft.com/devcontainers/python:1-${VARIANT}-bookworm

# Custom setup
RUN apt-get update && apt-get install -y \
    your-custom-package \
    && rm -rf /var/lib/apt/lists/*
```

### Docker Compose

**For multi-container setups:**

```json
{
  "dockerComposeFile": "docker-compose.yml",
  "service": "app",
  "workspaceFolder": "/workspace"
}
```

### Lifecycle Scripts

```json
{
  "onCreateCommand": "echo 'Container created'",
  "updateContentCommand": "pip install -r requirements.txt",
  "postCreateCommand": "./.devcontainer/post-create.sh",
  "postStartCommand": "echo 'Container started'"
}
```

**Script timing:**
- `onCreateCommand`: Runs once when container is created
- `updateContentCommand`: Runs when container is recreated
- `postCreateCommand`: Runs after creation (our setup script)
- `postStartCommand`: Runs every time container starts

## Template Philosophy

This template follows the **ruthless simplicity** principle:

**What's included:**
- ✅ Essential tools (Claude Code, Git, basic CLI tools)
- ✅ Reasonable defaults (2-core, 8GB RAM)
- ✅ Automatic setup (Git config, status report)

**What's NOT included:**
- ❌ Heavy frameworks (install per-project)
- ❌ Large language runtimes (add if needed)
- ❌ Database servers (use Docker Compose if needed)
- ❌ Complex orchestration (keep it simple)

**Why:** Start minimal. Add only what your project needs. Easy to extend, hard to remove.

## Testing Your Configuration

**Before committing changes:**

1. **Validate JSON syntax:**
   ```bash
   cat .devcontainer/devcontainer.json | jq .
   ```

2. **Test locally with Dev Containers:**
   - Install VS Code Dev Containers extension
   - Open repository in container
   - Verify everything works

3. **Test in Codespace:**
   - Create a test Codespace
   - Check post-create log: `cat /tmp/devcontainer-post-create.log`
   - Verify tools: `claude --version`, `gh --version`
   - Delete test Codespace when done

## Troubleshooting

### Build Fails

**Check logs:**
```bash
# View build logs from GitHub
# Repository → Code → Codespaces → Failed build → View logs
```

**Common issues:**
- Invalid JSON in `devcontainer.json`
- Unknown feature references
- Script errors in `post-create.sh`

### Tools Not Available

**After Codespace creation:**
```bash
# Check post-create log
cat /tmp/devcontainer-post-create.log

# Re-run if needed
./.devcontainer/post-create.sh
```

### Slow Build Times

**Use prebuilds:**
- Repository Settings → Codespaces → Set up prebuild
- Builds run automatically on push
- Codespaces start much faster

## Best Practices

**1. Keep It Simple**
- Start with this minimal template
- Add only what you need
- Remove what you don't use

**2. Test Before Sharing**
- Create test Codespace
- Verify all tools work
- Check logs for errors

**3. Document Changes**
- Comment your customizations
- Explain why you added features
- Update POST_SETUP_README.md

**4. Version Control**
- Commit .devcontainer/ to Git
- Team gets same environment
- Changes are tracked

**5. Security**
- Don't commit secrets to devcontainer.json
- Use GitHub Secrets for sensitive values
- Be cautious with public repositories

## Resources

**Official Documentation:**
- [Devcontainer Specification](https://containers.dev/)
- [GitHub Codespaces Docs](https://docs.github.com/en/codespaces)
- [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers)

**Features and Images:**
- [Browse Features](https://github.com/devcontainers/features)
- [Browse Images](https://github.com/devcontainers/images)
- [Anthropic Claude Code Feature](https://github.com/anthropics/devcontainer-features)

**Related Guides:**
- [../docs/SETUP_GUIDE.md](../docs/SETUP_GUIDE.md) - Using this template
- [../docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md) - Common issues

---

**Questions?** Check the [setup guide](../docs/SETUP_GUIDE.md) or [troubleshooting guide](../docs/TROUBLESHOOTING.md).
