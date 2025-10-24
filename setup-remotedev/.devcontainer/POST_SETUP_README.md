# Welcome to Your Codespace!

Your GitHub Codespace is ready for development with Claude Code.

## What Just Happened

The devcontainer automatically configured your environment:

- ✅ Installed Claude Code CLI
- ✅ Configured Git for easy pushing
- ✅ Set up Python, Node.js, and essential tools
- ✅ Prepared development environment

## Quick Verification

Check that everything installed correctly:

```bash
# Verify Claude Code
claude --version

# View setup logs (if something seems wrong)
cat /tmp/devcontainer-post-create.log
```

## Getting Started

### Start Claude Code

```bash
# Launch Claude Code
claude

# Claude will help you with:
# - Understanding the codebase
# - Writing code
# - Running tests
# - Debugging issues
```

### Your Development Tools

**Languages & Runtimes:**
- Python 3.11 (with `uv` package manager)
- Node.js (LTS) with npm and pnpm

**Development Tools:**
- Claude Code CLI
- GitHub CLI (`gh`)
- Git (pre-configured)
- Make
- Vim

**Check versions:**
```bash
python3 --version
node --version
gh --version
git --version
```

## Common Next Steps

### Install Project Dependencies

```bash
# Python projects
uv pip install -r requirements.txt

# Node.js projects
npm install
# or
pnpm install

# Projects with Makefile
make install
```

### Run Tests

```bash
# Python
pytest

# Node.js
npm test

# Or use your project's test command
make test
```

### Start Development Server

```bash
# Check your project's README for specific commands
# Common patterns:
npm run dev
python manage.py runserver
make serve
```

## Codespace Tips

### Reconnecting Later

This Codespace persists in the cloud. To reconnect:

**From VS Code:**
1. Open Command Palette: `F1`
2. Type: `Codespaces: Connect to Codespace`
3. Select this Codespace

**From Terminal:**
```bash
gh codespace code --codespace <name>
```

### Work Continues When Disconnected

Close your laptop during a commute? No problem!

Long-running tasks (tests, builds) continue in the cloud. Reconnect later and they'll be done.

**Use tmux for persistent sessions:**
```bash
# Start a session
tmux new -s work

# Run long task
npm run test:all

# Detach: Ctrl+B, then D
# Close laptop, task continues

# Later: Reconnect
tmux attach -s work
```

### Auto-Stop

Codespaces auto-stop after 30 minutes of inactivity to save costs. Restart is quick (< 1 minute).

### Managing Multiple Codespaces

Working on multiple projects? See these guides:

- [Usage Guide](../docs/USAGE_GUIDE.md) - Daily Codespace management
- [Workflow Patterns](../docs/WORKFLOW_PATTERNS.md) - Multi-project patterns

## Customizing Your Codespace

### Personal Settings (Dotfiles)

Sync your shell config, aliases, and preferences:

1. Create a `dotfiles` repository
2. Add `.bashrc`, `.zshrc`, `.gitconfig`, etc.
3. Enable in GitHub Settings → Codespaces → Dotfiles

Every new Codespace gets your personal config automatically.

### VS Code Settings Sync

Sync your editor settings and extensions:

1. In VS Code: Settings Sync → Enable
2. Sign in with GitHub
3. Select what to sync

Now all Codespaces share your VS Code configuration.

### Project-Specific Setup

Customize this Codespace's configuration:

**Edit `.devcontainer/devcontainer.json`:**
- Add VS Code extensions
- Configure resources (CPU, RAM)
- Add development tools

**Edit `.devcontainer/post-create.sh`:**
- Add project setup commands
- Install project dependencies
- Configure services

See [.devcontainer/README.md](.devcontainer/README.md) for details.

## Troubleshooting

### Claude Code Not Working

```bash
# Check installation
claude --version

# View setup logs
cat /tmp/devcontainer-post-create.log

# Re-run setup if needed
./.devcontainer/post-create.sh
```

### Tools Missing

```bash
# Check what's available
which python3 node npm git gh

# View post-create log for errors
cat /tmp/devcontainer-post-create.log
```

### Performance Issues

Try a larger machine type:
1. Delete this Codespace
2. Create new one with 4-core or 8-core machine

### More Help

See the comprehensive troubleshooting guide:
[../docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)

## Resources

**Setup and Usage:**
- [Setup Guide](../docs/SETUP_GUIDE.md) - Copy template to projects
- [Usage Guide](../docs/USAGE_GUIDE.md) - Daily Codespace commands
- [Workflow Patterns](../docs/WORKFLOW_PATTERNS.md) - Multi-project development

**Official Documentation:**
- [GitHub Codespaces](https://docs.github.com/en/codespaces)
- [Devcontainer Spec](https://containers.dev/)
- [Claude Code](https://claude.ai/claude-code)

## Ready to Code!

Your Codespace is fully configured. Start with:

```bash
# Launch Claude Code
claude

# Ask Claude to help you get oriented:
# "Show me the structure of this project"
# "Help me understand the codebase"
# "What should I work on first?"
```

Happy coding! 🚀
