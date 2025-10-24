# Troubleshooting Guide

Common issues and solutions when working with GitHub Codespaces.

## Table of Contents

- [Codespace Creation Issues](#codespace-creation-issues)
- [Connection Problems](#connection-problems)
- [Claude Code Issues](#claude-code-issues)
- [Performance Problems](#performance-problems)
- [Git and Authentication](#git-and-authentication)
- [Port Forwarding Issues](#port-forwarding-issues)
- [Cost and Billing](#cost-and-billing)
- [General Tips](#general-tips)

---

## Codespace Creation Issues

### Codespace Won't Start

**Symptoms:**
- Stuck on "Creating codespace..."
- Build fails with errors
- Container won't start

**Diagnosis:**
```bash
# View build logs from GitHub
# Repository → Code → Codespaces → Click failed Codespace → View logs

# Or check logs via CLI
gh codespace logs --codespace <name>
```

**Common Causes and Fixes:**

**1. Invalid devcontainer.json**
```bash
# Validate JSON syntax
cat .devcontainer/devcontainer.json | jq .

# Common issues:
# - Missing comma
# - Trailing comma in last item
# - Unescaped quotes
```

**Fix:**
```json
// Bad
{
  "name": "project"
  "image": "python:3.11"  // Missing comma
}

// Good
{
  "name": "project",
  "image": "python:3.11"
}
```

**2. Invalid Feature References**
```bash
# Check feature names exist
# See: https://github.com/devcontainers/features
```

**Fix:**
```json
// Bad
"features": {
  "ghcr.io/devcontainers/features/python:1": {}  // Wrong path
}

// Good (check actual feature catalog)
"features": {
  "ghcr.io/devcontainers/features/python:1": {}
}
```

**3. Resource Limits Exceeded**

**Fix:** Try larger machine type:
- From VS Code: Delete and recreate with larger machine
- From GitHub: Settings when creating Codespace

---

### Build Takes Too Long

**Symptoms:**
- Codespace creation takes 10+ minutes
- Every start is slow

**Solutions:**

**1. Use Prebuilds** (Recommended)
```bash
# In your repository:
# Settings → Codespaces → Set up prebuild
# Select branch (usually main)
# Prebuilds run on every push
```

**Benefits:**
- Codespace starts in < 1 minute
- Dependencies pre-installed
- Trade-off: Uses build minutes

**2. Optimize post-create.sh**
```bash
# Bad: Install everything
pip install -r requirements.txt  # 100+ packages, 5 minutes

# Good: Only essentials in post-create
pip install -r requirements-dev.txt  # 10 packages, 30 seconds
# User installs project deps with: make install
```

**3. Cache Dependencies**
```json
// In devcontainer.json
"mounts": [
  "source=uv-cache,target=/workspaces/.cache/uv,type=volume"
]
```

---

## Connection Problems

### Can't Connect to Codespace

**Symptoms:**
- "Failed to connect" error
- Timeout when opening
- VS Code won't connect

**Solutions:**

**1. Check Codespace State**
```bash
gh codespace list

# Look for state:
# - "Available" = running, should connect
# - "Shutdown" = stopped, will auto-start
# - "Starting" = wait a moment
```

**2. Restart Codespace**
```bash
# Stop
gh codespace stop --codespace <name>

# Start
gh codespace code --codespace <name>
```

**3. Check VS Code Extension**
```bash
# Update GitHub Codespaces extension
# VS Code → Extensions → Update all
```

**4. Re-authenticate gh CLI**
```bash
gh auth logout
gh auth login
# Ensure "codespace" scope is included
```

---

### Disconnects Frequently

**Symptoms:**
- Loses connection every few minutes
- "Reconnecting..." frequently

**Solutions:**

**1. Network Issues**
- Switch to more stable network
- Disable VPN if causing issues
- Try different VS Code window

**2. Use SSH Connection**
```bash
# More stable than web protocol
gh codespace ssh --codespace <name>
```

**3. Check Codespace Region**
```bash
# Use region closest to you
# Set in: GitHub Settings → Codespaces → Default region
```

---

## Claude Code Issues

### Claude Command Not Found

**Symptoms:**
```bash
$ claude --version
bash: claude: command not found
```

**Solutions:**

**1. Check Post-Create Log**
```bash
cat /tmp/devcontainer-post-create.log

# Look for errors during Claude Code installation
```

**2. Verify Feature Installed**
```bash
# Check devcontainer.json includes:
"ghcr.io/anthropics/devcontainer-features/claude-code:1": {}
```

**3. Manual Installation**
```bash
# If post-create failed, run manually
./.devcontainer/post-create.sh

# Or install directly
npm install -g @anthropic-ai/claude-code
```

**4. Rebuild Codespace**
```bash
# From VS Code: Command Palette (F1)
# → "Codespaces: Rebuild Container"

# Or delete and recreate
gh codespace delete --codespace <name>
# Then create new from repository
```

---

### Claude Code Not Responding

**Symptoms:**
- Claude starts but doesn't respond
- Hangs on first prompt
- Error messages

**Solutions:**

**1. Check API Key**
```bash
# Claude Code needs API key configured
# Follow prompts on first run to set up
```

**2. Network/Firewall Issues**
```bash
# Test connectivity
curl https://api.anthropic.com/v1/health

# If fails, check firewall rules
```

**3. Restart Claude Code**
```bash
# Exit and restart
# Ctrl+D to exit
claude
```

---

## Performance Problems

### Codespace is Slow

**Symptoms:**
- Laggy typing
- Slow file operations
- Commands take forever

**Solutions:**

**1. Upgrade Machine Type**
```bash
# Check current machine
gh codespace view --codespace <name> | grep "Machine type"

# Upgrade to larger machine:
# Delete current Codespace
gh codespace delete --codespace <name>

# Create with larger machine
# From VS Code: Select 4-core or 8-core when creating
```

**2. Check Resource Usage**
```bash
# In Codespace
top
df -h
free -h

# Look for:
# - High CPU usage
# - Low disk space
# - Memory exhausted
```

**3. Clean Up Disk Space**
```bash
# Remove build artifacts
make clean

# Clean package caches
# Python
rm -rf ~/.cache/pip

# Node
npm cache clean --force

# Docker
docker system prune -a
```

**4. Use Local VS Code**

Browser-based VS Code is slower. Use local VS Code instead:
```bash
# Connect with local VS Code
gh codespace code --codespace <name>
```

---

### File Sync Issues

**Symptoms:**
- Local changes not appearing in Codespace
- Codespace changes not syncing

**Solution:**

This shouldn't happen - Codespaces don't sync with local files. They're independent environments. If you're seeing this:

```bash
# You might be confusing Codespace with:
# - Remote SSH
# - Dev Containers (local Docker)

# Codespace files only exist in cloud
# No sync with local machine
```

---

## Git and Authentication

### Git Push Fails

**Symptoms:**
```bash
$ git push
fatal: Authentication failed
```

**Solutions:**

**1. Check Git Config**
```bash
git config --global user.name
git config --global user.email

# If empty, set them:
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

**2. Re-authenticate**
```bash
# GitHub CLI handles auth
gh auth login

# Or use Git credential helper
git config --global credential.helper store
```

**3. Use SSH Instead of HTTPS**
```bash
# Change remote URL
git remote set-url origin git@github.com:user/repo.git
```

---

### Can't Clone Private Repos

**Symptoms:**
- Permission denied cloning repos
- "Repository not found"

**Solution:**
```bash
# Ensure gh CLI has correct scopes
gh auth refresh --scopes repo,read:org

# Test access
gh repo view user/private-repo
```

---

## Port Forwarding Issues

### Ports Not Forwarding

**Symptoms:**
- Can't access web app on forwarded port
- "Connection refused"

**Solutions:**

**1. Check Port is Listening**
```bash
# In Codespace
netstat -tuln | grep <port>

# Or
lsof -i :<port>

# If nothing, app isn't running
```

**2. Configure Port Forwarding**
```bash
# List forwarded ports
gh codespace ports --codespace <name>

# Forward manually
gh codespace ports forward <local>:<remote> --codespace <name>

# Example: Forward 8000 to local 8000
gh codespace ports forward 8000:8000 --codespace <name>
```

**3. Check Port Visibility**

In VS Code: Ports tab → Right-click port → Change Port Visibility
- Private: Only you can access
- Public: Anyone with URL can access

**4. Bind to 0.0.0.0**
```bash
# App must bind to 0.0.0.0, not localhost
# Bad
python -m http.server 8000  # Binds to 127.0.0.1

# Good
python -m http.server 8000 --bind 0.0.0.0
```

---

## Cost and Billing

### Unexpected High Costs

**Symptoms:**
- Bill higher than expected
- Many hours billed

**Diagnosis:**
```bash
# Check active Codespaces
gh codespace list

# Look for old Codespaces still running
# Check "Created" dates
```

**Solutions:**

**1. Stop Unused Codespaces**
```bash
# Stop all
gh codespace list --json name,state | \
  jq -r '.[] | select(.state=="Available") | .name' | \
  xargs -I {} gh codespace stop --codespace {}
```

**2. Delete Old Codespaces**
```bash
# Delete stopped Codespaces
gh codespace list --json name,state | \
  jq -r '.[] | select(.state=="Shutdown") | .name' | \
  xargs -I {} gh codespace delete --codespace {} --force
```

**3. Set Auto-Stop Timeout**
```bash
# In GitHub Settings → Codespaces
# Set "Default idle timeout" to 30 minutes
```

**4. Use Smaller Machines**

Costs by machine type (per hour):
- 2-core: ~$0.18/hour
- 4-core: ~$0.36/hour
- 8-core: ~$0.72/hour

Use smallest machine that meets needs.

---

### Free Tier Exhausted

**Symptoms:**
- "You've used your included Codespaces hours"
- Can't create new Codespaces

**Solutions:**

**1. Check Usage**
```bash
# View current month usage
gh api /user/codespaces/billing
```

**2. Wait for Reset**
- Free tier resets monthly
- Billing cycle: 1st of month

**3. Upgrade Plan**
- GitHub Pro: 180 core-hours/month
- Team: More hours included

**4. Optimize Usage**
- Stop Codespaces when not using
- Use 2-core machines
- Delete completed work

---

## General Tips

### Debugging Strategy

**When something doesn't work:**

1. **Check logs first**
   ```bash
   cat /tmp/devcontainer-post-create.log
   gh codespace logs --codespace <name>
   ```

2. **Verify state**
   ```bash
   gh codespace list
   gh codespace view --codespace <name>
   ```

3. **Test basics**
   ```bash
   # Can execute commands?
   gh codespace ssh --codespace <name> -- ls

   # Network working?
   gh codespace ssh --codespace <name> -- ping -c 1 google.com
   ```

4. **Rebuild if needed**
   ```bash
   # From VS Code: Rebuild Container
   # Or: Delete and recreate
   ```

---

### Getting Help

**Before asking for help:**

1. **Gather information**
   ```bash
   gh codespace view --codespace <name> > codespace-info.txt
   gh codespace logs --codespace <name> > codespace-logs.txt
   ```

2. **Check official docs**
   - [GitHub Codespaces Docs](https://docs.github.com/en/codespaces)
   - [Devcontainer Spec](https://containers.dev/)

3. **Search existing issues**
   - [GitHub Community](https://github.com/orgs/community/discussions)
   - [Codespaces Issues](https://github.com/github/feedback/discussions/categories/codespaces-feedback)

**When asking for help, include:**
- What you're trying to do
- What happened instead
- Error messages (full text)
- Logs (from commands above)
- Steps to reproduce

---

## Quick Reference

```bash
# Diagnosis commands
gh codespace list                              # Check all Codespaces
gh codespace view --codespace <name>           # Check specific one
gh codespace logs --codespace <name>           # View logs
cat /tmp/devcontainer-post-create.log         # Post-create log

# Common fixes
gh codespace stop --codespace <name>           # Restart
gh codespace delete --codespace <name>         # Recreate
gh auth login                                  # Re-auth
gh codespace ssh --codespace <name>            # Direct access

# In Codespace
claude --version                               # Check Claude
git status                                     # Check git
df -h                                          # Check disk
free -h                                        # Check memory
```

---

**Still stuck?** See [USAGE_GUIDE.md](USAGE_GUIDE.md) or [SETUP_GUIDE.md](SETUP_GUIDE.md) for more context.
