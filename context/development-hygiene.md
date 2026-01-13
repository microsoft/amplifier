# Amplifier CLI Installation Architecture & Development Hygiene

This guide explains how the Amplifier CLI installation works and the correct patterns for development work.

## How Amplifier is Installed

### Installation Flow

1. **Entry point**: `uv tool install git+https://github.com/microsoft/amplifier`
2. **Tool directory**: Creates `~/.local/share/uv/tools/amplifier/` (bin, lib, site-packages)
3. **Cache directory**: Clones `amplifier-core`, `amplifier-app-cli`, and other packages to `~/.amplifier/cache/`
4. **Editable installs**: The site-packages contain **links** pointing to the cache versions

### Runtime Behavior

When Amplifier launches:
1. Installs "well-known" providers (clone to cache → editable install)
2. Downloads bundles and modules on demand (same pattern)
3. **The actual running code is the code in `~/.amplifier/cache/`**

### Directory Structure

```
~/.local/share/uv/tools/amplifier/
├── bin/amplifier           # Entry point script
└── lib/python3.x/site-packages/
    └── amplifier_*.egg-link  # LINKS to ~/.amplifier/cache/

~/.amplifier/
├── cache/                  # Downloaded packages - THE RUNNING CODE
│   ├── amplifier-core-{hash}/
│   ├── amplifier-foundation-{hash}/
│   ├── amplifier-module-provider-anthropic-{hash}/
│   └── ...
├── registry.json           # Bundle name → source mappings
├── settings.yaml           # Global user settings
├── keys.env                # API keys
└── projects/               # Session transcripts
```

## CRITICAL: Never Delete the Cache Directly

**NEVER run:**
```bash
rm -rf ~/.amplifier/cache/   # DANGEROUS - breaks Amplifier
rm -rf ~/.amplifier/         # DANGEROUS - breaks Amplifier
```

**Why this breaks things:**
1. The CLI's site-packages contain **links** to cache files
2. Without the cache, the CLI cannot run ANY commands
3. It can't even download modules to repopulate because it needs modules to do that
4. You end up in a broken state requiring manual `uv tool install` to recover

### The Right Way: `amplifier reset`

Use the reset command to safely clear and reinstall:

```bash
# Interactive mode - choose what to preserve
amplifier reset

# Clear only cache and registry (preserves settings, keys, projects)
amplifier reset --remove cache,registry -y

# Preview what would be removed without changes
amplifier reset --dry-run

# Nuclear option - remove everything
amplifier reset --full -y
```

**How reset works safely:**
1. Cleans UV cache
2. Uninstalls amplifier via `uv tool uninstall`
3. Removes specified ~/.amplifier contents
4. **Reinstalls** from `git+https://github.com/microsoft/amplifier`
5. Launches fresh amplifier

The reinstall step is what makes this safe - it repopulates everything from scratch.

## Development Patterns

### Don't Modify ~/.amplifier/cache/ for Development

The cache is for RUNNING the installed CLI, not for development work.

**Anti-patterns:**
- Reading cache code to understand how something works (use cloned repos)
- Editing cache files to test changes (changes are invisible to git)
- Using cache paths in your work (they're ephemeral)

**Instead:**
- Clone the repo you need: `git clone https://github.com/microsoft/amplifier-module-xyz.git`
- Or add as submodule in a workspace: `git submodule add https://github.com/...`

### Project-Local Source Overrides

To test local changes without modifying the global installation:

**Create `.amplifier/settings.yaml` in your project:**

```yaml
sources:
  # Override a module to use local checkout
  amplifier-module-xyz:
    type: local
    path: ./amplifier-module-xyz
  
  # Override core for kernel development
  amplifier-core:
    type: local
    path: ./amplifier-core
```

### Settings Scope Hierarchy

| Scope | File | Precedence | Use Case |
|-------|------|------------|----------|
| Local | `.amplifier/settings.local.yaml` | Highest | Personal (gitignored) |
| Project | `.amplifier/settings.yaml` | Medium | Team-shared |
| Global | `~/.amplifier/settings.yaml` | Lowest | User defaults |

**Module Resolution Order:**
1. Environment variable: `AMPLIFIER_MODULE_<ID>=<path>`
2. Workspace convention: `.amplifier/modules/<module-id>/`
3. Project config: `.amplifier/settings.yaml` sources
4. User config: `~/.amplifier/settings.yaml` sources
5. Bundle/profile source field
6. Installed package (cache)

### Shadow Environments (Recommended for Testing)

For testing local changes in complete isolation, use **shadow environments** (available via the foundation bundle):

```python
# Create isolated environment with your local changes
shadow.create(local_sources=[
    "~/repos/amplifier-core:microsoft/amplifier-core",
    "~/repos/amplifier-module-xyz:microsoft/amplifier-module-xyz"
])

# Install and test in the shadow - uses YOUR local code
shadow.exec(shadow_id, "uv tool install git+https://github.com/microsoft/amplifier")
shadow.exec(shadow_id, "amplifier run 'test my changes'")

# Clean up
shadow.destroy(shadow_id)
```

**Why shadow environments:**
- Complete OS-level isolation (containerized)
- Your local changes are snapshotted and served via embedded Gitea
- No risk of corrupting your global installation
- Tests exactly what will happen when changes are pushed
- See `@shadow:context/shadow-instructions.md` for full documentation

### Project-Local Virtual Environments

When developing on Amplifier ecosystem repos directly:

```bash
cd amplifier-core
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/
```

**Why project-local venv:**
- Isolated from other projects and global install
- Matches CI environment
- Easy to recreate
- Changes don't affect the installed CLI

## Summary: Where Things Belong

| What | Where | Why |
|------|-------|-----|
| Code you're modifying | Cloned repo or submodule | Git-tracked, pushable |
| Local source overrides | `.amplifier/settings.yaml` | Project-scoped, explicit |
| Dev dependencies | `.venv/` in the repo | Isolated, reproducible |
| Isolated testing | Shadow environment | Complete isolation |
| Installed CLI runtime | `~/.amplifier/cache/` | Auto-managed, don't touch |
| Clearing cache | `amplifier reset` | Handles reinstall safely |
| **NEVER** | Direct `rm -rf ~/.amplifier/cache/` | Breaks CLI |
