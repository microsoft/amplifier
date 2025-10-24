# Setup Guide: Adding GitHub Codespaces to Your Project

This guide shows you how to copy the devcontainer template to any project and create your first Codespace.

## Prerequisites

Before starting, ensure you have:

- **GitHub account** with Codespaces access ([check access](https://github.com/features/codespaces))
- **Project repository** on GitHub (public or private)
- **VS Code** installed locally (recommended for best experience)
- **GitHub Codespaces extension** for VS Code

### Install VS Code Extension

1. Open VS Code
2. Press `Ctrl/Cmd+Shift+X` to open Extensions
3. Search for "GitHub Codespaces"
4. Click "Install"

## Step 1: Copy Template to Your Project

Navigate to your project repository and copy the devcontainer configuration:

```bash
# From the amplifier directory
cd /path/to/your/project

# Copy the devcontainer template
cp -r /path/to/amplifier/setup-remotedev/.devcontainer .

# Verify files copied
ls -la .devcontainer/
```

You should see:
```
.devcontainer/
├── devcontainer.json
├── post-create.sh
├── POST_SETUP_README.md
└── README.md
```

### Customize the Template (Optional)

The template works out-of-the-box, but you can customize it for your project:

**Edit `.devcontainer/devcontainer.json`:**

```json
{
  "name": "your-project-name",  // Change this to your project name
  "image": "mcr.microsoft.com/devcontainers/python:1-3.11-bookworm",

  // Adjust resources if needed
  "hostRequirements": {
    "cpus": 2,      // More CPUs for faster builds
    "memory": "8gb", // More memory for large projects
    "storage": "32gb"
  },

  // Add project-specific tools
  "features": {
    // These are already included:
    "ghcr.io/jungaretti/features/make:1": {},
    "ghcr.io/anthropics/devcontainer-features/claude-code:1": {},

    // Add more as needed:
    // "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  }
}
```

**Edit `.devcontainer/post-create.sh`:**

Add project-specific setup commands:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Existing setup...

# Add your project-specific setup
echo "🔧  Installing project dependencies..."
make install  # or npm install, pip install, etc.
```

## Step 2: Commit and Push

Commit the devcontainer configuration to your repository:

```bash
git add .devcontainer/
git commit -m "Add GitHub Codespaces devcontainer configuration

- Claude Code pre-configured
- Ready for cloud development
- Based on amplifier setup-remotedev template"

git push origin main
```

## Step 3: Create Your First Codespace

You can create a Codespace from GitHub or VS Code. VS Code is recommended for better performance.

### Option A: Create from VS Code (Recommended)

1. **Open Command Palette:** `F1` or `Ctrl/Cmd+Shift+P`

2. **Type:** `Codespaces: Create New Codespace`

3. **Select your repository** from the list

4. **Choose branch:** Usually `main` or `master`

5. **Select machine type:**
   - `2-core (8 GB RAM)` - Good for most projects
   - `4-core (16 GB RAM)` - Better for large projects
   - `8-core (32 GB RAM)` - Heavy compilation or large datasets

6. **Wait for creation:** Takes 2-5 minutes on first build

7. **Codespace opens:** Ready to use with Claude Code installed

### Option B: Create from GitHub

1. **Go to your repository** on GitHub

2. **Click the green "Code" button**

3. **Click "Codespaces" tab**

4. **Click "Create codespace on main"**

5. **Choose machine type**

6. **Wait for creation:** Browser-based editor opens

7. **Connect with VS Code:** Click the menu (three dots) → "Open in VS Code"

## Step 4: Verify Setup

Once your Codespace is running, verify everything is ready:

### Check Claude Code

```bash
# Verify Claude Code is installed
claude --version

# Should show version like: Claude Code v2.x.x
```

### Check Post-Create Logs

```bash
# View setup logs to verify everything installed
cat /tmp/devcontainer-post-create.log
```

You should see:
```
✅  Post-create tasks complete
📋 Development Environment Ready:
  • Python: 3.11.x
  • Claude CLI: 2.x.x
  • Git: 2.x.x
  • Make: 4.x
```

### Start Claude Code

```bash
# Launch Claude Code
claude

# You should see the Claude Code interface
```

## Step 5: Test Your Workflow

Try a simple task to verify everything works:

```bash
# Start Claude Code session
claude

# Ask Claude to help with your project
# Example: "Show me the structure of this project"
```

**Success indicators:**
- ✅ Claude Code responds
- ✅ Can read project files
- ✅ Can execute commands
- ✅ Changes persist when you disconnect and reconnect

## Troubleshooting

### Claude Code Not Found

If `claude --version` fails:

```bash
# Check the post-create log for errors
cat /tmp/devcontainer-post-create.log

# Manually run the post-create script
./.devcontainer/post-create.sh
```

### Codespace Won't Start

**Check build logs:**
1. In GitHub: Repository → Codespaces → Click the failed Codespace → View logs
2. Look for errors in the build output

**Common issues:**
- Invalid JSON in `devcontainer.json` - Validate with a JSON linter
- Missing features - Check feature names at [devcontainers/features](https://github.com/devcontainers/features)
- Resource limits - Try a larger machine type

### Can't Connect to Codespace

**From VS Code:**
1. Open Command Palette: `F1`
2. Type: `Codespaces: Connect to Codespace`
3. Select your Codespace from the list

**From GitHub:**
1. Repository → Code → Codespaces tab
2. Click the three dots next to your Codespace
3. Click "Open in VS Code"

### Post-Create Script Fails

```bash
# View the error
cat /tmp/devcontainer-post-create.log

# Common fixes:
# 1. Make script executable
chmod +x .devcontainer/post-create.sh

# 2. Fix line endings (if edited on Windows)
dos2unix .devcontainer/post-create.sh

# 3. Re-run manually
./.devcontainer/post-create.sh
```

## Next Steps

**You now have a working Codespace!**

**To create more Codespaces:**
- Repeat Step 3 for other projects
- Each project gets its own isolated environment
- See [USAGE_GUIDE.md](USAGE_GUIDE.md) for managing multiple Codespaces

**To optimize your workflow:**
- Read [WORKFLOW_PATTERNS.md](WORKFLOW_PATTERNS.md) for multi-project patterns
- Configure [dotfiles](https://docs.github.com/en/codespaces/customizing-your-codespace/personalizing-github-codespaces-for-your-account#dotfiles) for personal preferences

**For advanced customization:**
- Review [.devcontainer/README.md](../.devcontainer/README.md) for template details
- Explore [devcontainer features](https://containers.dev/features) for additional tools

## Quick Reference

```bash
# Check Claude Code installed
claude --version

# View setup logs
cat /tmp/devcontainer-post-create.log

# Start Claude Code
claude

# Check Codespace status (from local machine)
gh codespace list

# Connect to Codespace (from local machine)
gh codespace code --codespace <name>
```

---

**Need help?** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more solutions.

**Ready to manage multiple Codespaces?** See [USAGE_GUIDE.md](USAGE_GUIDE.md).
