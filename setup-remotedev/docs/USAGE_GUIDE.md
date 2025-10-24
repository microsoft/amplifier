# Usage Guide: Managing Multiple GitHub Codespaces

This guide covers daily workflows for managing multiple concurrent Codespaces.

## Overview

Once you have Codespaces set up for multiple projects, you'll need efficient ways to:
- See all your active Codespaces at a glance
- Quickly connect to the right one
- Clean up unused Codespaces to manage costs

This guide shows you how using the `gh` CLI.

## Prerequisites

Install and authenticate the GitHub CLI:

```bash
# Install gh CLI
# macOS
brew install gh

# Ubuntu/Debian
sudo apt install gh

# Windows
winget install --id GitHub.cli

# Authenticate
gh auth login
```

Follow the prompts to authenticate with your GitHub account.

## Essential Commands

### List All Codespaces

See all your active Codespaces:

```bash
gh codespace list
```

**Output:**
```
NAME                            REPOSITORY           BRANCH    STATE       CREATED
amplifier-main-abc123          user/amplifier       main      Available   2h ago
myproject-dev-def456           user/myproject       dev       Available   1d ago
experiment-feature-ghi789      user/experiment      feature   Available   3h ago
```

**Useful flags:**
```bash
# Show more details
gh codespace list --json name,repository,state,createdAt

# Filter by repository
gh codespace list --repo user/amplifier

# Include stopped Codespaces
gh codespace list --all
```

### Connect to a Codespace

Open a Codespace in VS Code:

```bash
# Interactive selection
gh codespace code

# Direct connection by name
gh codespace code --codespace amplifier-main-abc123

# Or use short form with repo
gh codespace code --repo user/amplifier
```

**Tips:**
- Use tab completion: `gh codespace code --codespace <TAB>`
- Set up aliases for frequently used Codespaces (see below)

### View Codespace Details

Get detailed information about a Codespace:

```bash
# Show details
gh codespace view --codespace amplifier-main-abc123

# Show logs (build and runtime)
gh codespace logs --codespace amplifier-main-abc123
```

### Stop a Codespace

Stop a running Codespace to save costs:

```bash
# Stop (can restart later)
gh codespace stop --codespace amplifier-main-abc123
```

**Note:** Codespaces auto-stop after 30 minutes of inactivity by default.

### Delete a Codespace

Permanently delete a Codespace:

```bash
# Delete with confirmation
gh codespace delete --codespace amplifier-main-abc123

# Delete without confirmation
gh codespace delete --codespace amplifier-main-abc123 --force

# Delete all stopped Codespaces
gh codespace list --json name,state | \
  jq -r '.[] | select(.state=="Shutdown") | .name' | \
  xargs -I {} gh codespace delete --codespace {} --force
```

**Warning:** Deletion is permanent. Any uncommitted changes are lost.

### Port Forwarding

Forward ports from your Codespace to your local machine:

```bash
# List forwarded ports
gh codespace ports --codespace amplifier-main-abc123

# Forward a specific port
gh codespace ports forward 8000:8000 --codespace amplifier-main-abc123

# Stop forwarding
gh codespace ports stop 8000 --codespace amplifier-main-abc123
```

### SSH into a Codespace

Direct SSH access for debugging:

```bash
# SSH into Codespace
gh codespace ssh --codespace amplifier-main-abc123

# Run a command without interactive shell
gh codespace ssh --codespace amplifier-main-abc123 -- ls -la

# Copy files to/from Codespace
gh codespace cp local-file.txt remote:~/path/
gh codespace cp remote:~/path/file.txt ./local-file.txt
```

## Workflow Patterns

### Morning Routine: Check Active Codespaces

Start your day by seeing what's running:

```bash
# List all Codespaces
gh codespace list

# Connect to the one you need
gh codespace code --codespace <name>
```

### Multi-Project Work: Quick Switching

Use aliases to switch between projects quickly:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias cs-amplifier='gh codespace code --repo username/amplifier'
alias cs-project='gh codespace code --repo username/myproject'
alias cs-experiment='gh codespace code --repo username/experiment'

# Then just type:
cs-amplifier  # Instantly connects
```

### End of Day: Stop Unused Codespaces

Save costs by stopping Codespaces you're done with:

```bash
# Stop specific Codespace
gh codespace stop --codespace amplifier-main-abc123

# Or let auto-stop handle it (default 30 minutes idle)
```

### Weekly Cleanup: Delete Old Codespaces

Clean up Codespaces you no longer need:

```bash
# List all Codespaces with age
gh codespace list --json name,repository,createdAt

# Delete old ones
gh codespace delete --codespace <name>
```

## Advanced Techniques

### Bulk Operations

Operate on multiple Codespaces at once:

```bash
# Stop all running Codespaces
gh codespace list --json name,state | \
  jq -r '.[] | select(.state=="Available") | .name' | \
  xargs -I {} gh codespace stop --codespace {}

# Delete all Codespaces for a specific repo
gh codespace list --repo user/myproject --json name | \
  jq -r '.[].name' | \
  xargs -I {} gh codespace delete --codespace {} --force
```

### Custom Scripts

Create helper scripts for common tasks:

**`~/bin/cs-list`** - Pretty list of Codespaces:
```bash
#!/usr/bin/env bash
gh codespace list --json name,repository,state,createdAt | \
  jq -r '.[] | "\(.name) | \(.repository) | \(.state)"' | \
  column -t -s '|'
```

**`~/bin/cs-connect`** - Interactive Codespace selector:
```bash
#!/usr/bin/env bash
CODESPACE=$(gh codespace list --json name | jq -r '.[].name' | fzf)
if [ -n "$CODESPACE" ]; then
  gh codespace code --codespace "$CODESPACE"
fi
```

**`~/bin/cs-cleanup`** - Delete old stopped Codespaces:
```bash
#!/usr/bin/env bash
echo "Finding stopped Codespaces older than 7 days..."
gh codespace list --json name,state,createdAt | \
  jq -r --arg cutoff "$(date -d '7 days ago' -I)" \
    '.[] | select(.state=="Shutdown" and .createdAt < $cutoff) | .name' | \
  while read -r name; do
    echo "Deleting: $name"
    gh codespace delete --codespace "$name" --force
  done
```

Make scripts executable:
```bash
chmod +x ~/bin/cs-*
```

### Monitoring Costs

Track Codespaces usage to manage costs:

```bash
# View billing usage (requires org admin)
gh api /user/codespaces/billing

# List Codespaces with machine types
gh codespace list --json name,machine,billableOwner
```

**Cost management tips:**
- Use smallest machine type that meets your needs
- Stop Codespaces when not actively using (auto-stop helps)
- Delete Codespaces for completed work
- Set up prebuilds to reduce startup time (but increase build costs)

### VS Code Settings Sync

Sync your VS Code settings across all Codespaces:

1. In VS Code: Settings Sync → Enable
2. Sign in with GitHub account
3. Select settings to sync:
   - ✅ Settings
   - ✅ Keyboard Shortcuts
   - ✅ Extensions
   - ✅ UI State

Now all your Codespaces share the same VS Code configuration.

### Dotfiles Integration

Apply your personal shell configuration to all Codespaces:

1. Create a dotfiles repository (e.g., `username/dotfiles`)
2. Add your configs: `.bashrc`, `.zshrc`, `.gitconfig`, etc.
3. In GitHub Settings:
   - Codespaces → Enable "Automatically install dotfiles"
   - Select your dotfiles repository

Every new Codespace automatically applies your dotfiles.

## Troubleshooting

### Can't Connect to Codespace

**Symptom:** `gh codespace code` fails or times out

**Solutions:**
```bash
# Check Codespace state
gh codespace list

# If Shutdown, restart it
gh codespace code --codespace <name>  # Auto-starts

# If stuck Starting, view logs
gh codespace logs --codespace <name>

# If logs show errors, delete and recreate
gh codespace delete --codespace <name>
# Then create new one from repository
```

### Codespace Name Unknown

**Symptom:** Don't remember Codespace name

**Solution:**
```bash
# List all with repository names
gh codespace list

# Or connect by repository instead
gh codespace code --repo user/amplifier
```

### Authentication Issues

**Symptom:** `gh` commands fail with auth errors

**Solution:**
```bash
# Re-authenticate
gh auth logout
gh auth login

# Check auth status
gh auth status

# Ensure Codespaces scope included
# Should show: ✓ codespace
```

### Too Many Codespaces

**Symptom:** Hit account limits or confused by many Codespaces

**Solution:**
```bash
# Delete all stopped Codespaces
gh codespace list --json name,state | \
  jq -r '.[] | select(.state=="Shutdown") | .name' | \
  xargs -I {} gh codespace delete --codespace {} --force

# Keep only recent ones (last 3 days)
# Use cleanup script from Advanced Techniques section
```

## Quick Reference

```bash
# Essential commands
gh codespace list                              # List all
gh codespace code                              # Connect (interactive)
gh codespace code --codespace <name>           # Connect directly
gh codespace stop --codespace <name>           # Stop
gh codespace delete --codespace <name>         # Delete

# Useful queries
gh codespace list --repo <repo>                # Filter by repo
gh codespace list --json name,state,createdAt  # JSON output
gh codespace view --codespace <name>           # Details
gh codespace logs --codespace <name>           # View logs

# Bulk operations
gh codespace list --json name | jq -r '.[].name'  # All names
# Then pipe to xargs for bulk operations
```

## Next Steps

**Master your workflow:**
- Read [WORKFLOW_PATTERNS.md](WORKFLOW_PATTERNS.md) for multi-project patterns
- Set up aliases and scripts for common operations
- Configure dotfiles for consistent environment

**Optimize costs:**
- Stop Codespaces when done for the day
- Delete old Codespaces weekly
- Use appropriate machine sizes

**Get help:**
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Check [GitHub Docs](https://docs.github.com/en/codespaces) for official documentation

---

**Quick help:** `gh codespace --help` or `gh codespace <command> --help`
