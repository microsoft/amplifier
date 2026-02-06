---
last_updated: 2025-11-18
status: stable
audience: user
---

# Amplifier User Guide

Complete guide to using Amplifier for AI-assisted development.

> **Note**: Amplifier is under active development. Some features and commands may change.

---

## Installation

See [../README.md](../README.md#quick-start---zero-to-working-in-90-seconds) for complete installation guide.

**Quick summary:**

```bash
uv tool install git+https://github.com/microsoft/amplifier
amplifier init      # optional if you let the first run wizard handle setup
amplifier run "Your prompt"
```

After installing, add optional bundles to extend capabilities:

```bash
amplifier bundle add git+https://github.com/microsoft/amplifier-bundle-recipes@main
amplifier bundle add git+https://github.com/microsoft/amplifier-bundle-design-intelligence@main
```

Use `recipes` or `design-intelligence` as turnkey bundles, or call their agents directly (use `/agents` in chat to list available agents).

> [!IMPORTANT]
> Amplifier is currently tested on macOS, Linux, and Windows Subsystem for Linux (WSL). Native Windows shells have known issues—use WSL unless you're helping improve Windows support.

---

## Basic Usage

### Single Command Mode

Execute one task and exit:

```bash
# Generate code
amplifier run "Create a Python function to parse CSV files"

# Get explanations
amplifier run "Explain how async/await works in Python with examples"

# Debug errors
amplifier run "Debug this TypeError: 'NoneType' object is not subscriptable in [code snippet]"

# Code review
amplifier run "Review this code for security issues: [paste code]"
```

### Interactive Chat Mode

Start a conversation with persistent context:

```bash
# Launch chat mode
amplifier

# Or explicitly
amplifier run --mode chat
```

**Chat commands:**

- `/help` - Show available commands
- `/tools` - List available tools
- `/agents` - List available agents
- `/status` - Show session status
- `/config` - Show current configuration
- `/think` - Enable plan mode (read-only)
- `/do` - Disable plan mode (allow modifications)
- `/clear` - Clear conversation context
- `/save` - Save conversation transcript
- `exit` or `Ctrl+C` - Quit

**Example conversation:**

```
> Explain dependency injection in Python

[AI explains concept]

> Show me an example with a real-world use case

[AI provides code example]

> How would I test this?

[AI shows testing patterns]

> exit
```

---

## Configuration

### Understanding Configuration Dimensions

Amplifier has 4 configuration dimensions you can control:

1. **Provider** - Which AI service (Anthropic/OpenAI/Azure OpenAI/Ollama)
2. **Bundle** - Which capabilities (foundation/dev/recipes/full)
3. **Module** - Which specific tools/hooks/agents
4. **Source** - Where modules come from (git/local/package)

### Switching Providers

```bash
# Switch provider (interactive - prompts for model/config)
amplifier provider use openai

# Or explicit
amplifier provider use anthropic --model claude-opus-4-6
amplifier provider use openai --model gpt-5.1
amplifier provider use ollama --model llama3

# Azure OpenAI (more complex)
amplifier provider use azure-openai --deployment gpt-5.1-codex --use-azure-cli

# Configure where to save
amplifier provider use openai --model gpt-5.1 --local    # Just you
amplifier provider use anthropic --model claude-opus-4-6 --project  # Team

# See what's active
amplifier provider current

# List available
amplifier provider list
```

**Supported providers:**

- **Anthropic Claude** - Recommended, most tested (configure: model + API key)
- **OpenAI** - Good alternative (configure: model + API key)
- **Azure OpenAI** - Enterprise (configure: endpoint + deployment + auth method)
- **Ollama** - Local, free (configure: model only, no API key)

### Switching Bundles

```bash
# Switch bundle
amplifier bundle use foundation    # Minimal footprint
amplifier bundle use dev           # Development tools
amplifier bundle use recipes       # Multi-step workflows

# See what's active
amplifier bundle current

# List available
amplifier bundle list
```

**Bundled Configurations:**

| Bundle       | Purpose                    | Tools                    | Agents                                                           |
| ------------ | -------------------------- | ------------------------ | ---------------------------------------------------------------- |
| `foundation` | Bare minimum               | filesystem, bash         | None                                                             |
| `dev`        | Full development           | base + web, search, task | zen-architect, bug-hunter, modular-builder, explorer, researcher |
| `recipes`    | Multi-step workflows       | base + task              | Recipe execution agents                                          |
| `full`       | Demo of nearly all modules | Almost everything        | Broad showcase (best for exploration, not daily use)             |

### Adding Capabilities

```bash
# Add module to current bundle
amplifier module add tool-jupyter

# Add for team
amplifier module add tool-custom --project

# See loaded modules
amplifier module current
```

### Creating Custom Bundles

```bash
# Create custom bundle
amplifier bundle create my-workflow --extend foundation

# Edit bundle
# File created at: ~/.amplifier/bundles/my-workflow.md

# Use it
amplifier bundle use my-workflow
```

See [../docs/USER_ONBOARDING.md#quick-reference](../docs/USER_ONBOARDING.md#quick-reference) for complete configuration reference.

---

## Working with Agents

Agents are specialized AI sub-sessions focused on specific tasks. The dev bundle includes several agents:

### Using Agents

```bash
# Let the AI decide when to use agents
amplifier run "Design a caching layer for my API"
# The AI might use zen-architect for design

# Request specific agents
amplifier run "Use bug-hunter to debug this error: [paste stack trace]"
amplifier run "Use researcher to find best practices for async error handling"
```

### Bundled Agents

**zen-architect** - Architecture and design

- Analyzes problems before implementing
- Designs system architecture
- Reviews code for simplicity and philosophy compliance

**bug-hunter** - Debugging expert

- Systematic hypothesis-driven debugging
- Tracks down errors efficiently
- Fixes issues without adding complexity

**researcher** - Content synthesis

- Researches best practices
- Analyzes documentation
- Synthesizes information from multiple sources

**modular-builder** - Implementation specialist

- Builds code from specifications
- Creates self-contained modules
- Follows modular design principles

---

## Session Management

Sessions are automatically saved and organized by project.

### Listing Sessions

```bash
# Show sessions for current project
amplifier session list

# Show all sessions across all projects
amplifier session list --all-projects

# Show sessions for specific project
amplifier session list --project /path/to/other/project
```

### Session Details

```bash
# Show session metadata
amplifier session show <session-id>

# Show full transcript
amplifier session show <session-id> --detailed
```

### Resuming Sessions

```bash
# Resume most recent session (interactive)
amplifier continue

# Resume most recent with new prompt (single-shot)
amplifier continue "follow-up question"

# Resume specific session (interactive)
amplifier session resume <session-id>

# Resume specific session with new prompt (single-shot)
amplifier run --resume <session-id> "new question"

# Resume with different bundle
amplifier continue --bundle full
amplifier session resume <session-id> --bundle full
```

### Where Are Sessions Stored?

Sessions are stored in `~/.amplifier/projects/<project-slug>/sessions/` where the project slug is based on your current working directory.

Example: Working in `/home/user/repos/myapp` stores sessions in:
`~/.amplifier/projects/-home-user-repos-myapp/sessions/`

Each session contains:

- `transcript.jsonl` - Message history
- `events.jsonl` - All events (tool calls, approvals, etc.)
- `metadata.json` - Session info (bundle, provider, timestamps)

---

## Advanced Usage

### Per-Command Overrides

```bash
# Use different provider just once
amplifier run --provider openai "test prompt"

# Use different bundle just once
amplifier run --bundle design-intelligence "audit the design system"

# Combine overrides
amplifier run --provider openai --bundle recipes "compare models"
```

### Keeping Amplifier Up to Date

Amplifier checks for updates across all components: the CLI itself, cached modules, and installed bundles.

```bash
# Check for updates (no changes made)
amplifier update --check-only

# Update everything (prompts for confirmation)
amplifier update

# Update without confirmation prompts
amplifier update --yes
```

**What gets updated:**

- **Cached modules** - Modules pinned to mutable refs (`@main`, `@dev`)
- **Bundles** - Installed bundles pinned to mutable refs
- **Amplifier itself** - The CLI tool and core libraries

**Updating modules:**

```bash
# Refresh all cached modules
amplifier module refresh

# Refresh specific module
amplifier module refresh tool-filesystem

# Only refresh branches (not tags/SHAs)
amplifier module refresh --mutable-only

# Check what needs updating
amplifier module check-updates
```

**Updating bundles:**

```bash
# Refresh all installed bundles
amplifier bundle refresh

# Refresh specific bundle
amplifier bundle refresh foundation

# Only refresh branches (not tags/SHAs)
amplifier bundle refresh --mutable-only
```

**Notes:**

- Immutable refs (tags like `@v1.0.0`, SHAs) are never automatically updated
- Local file sources show update status but require manual `git pull`
- Use `--mutable-only` to skip pinned versions during refresh

### Module Management

```bash
# List installed modules
amplifier module list

# Filter by type
amplifier module list --type tool

# Get module information
amplifier module show loop-streaming
```

### Source Overrides (Development)

```bash
# Override module source for local development
amplifier source add tool-bash ~/dev/tool-bash --local

# See where modules come from
amplifier source show tool-bash
amplifier source list

# Remove override
amplifier source remove tool-bash --local
```

---

## Troubleshooting

### Configuration Not Working

**Q: My settings aren't taking effect**  
A: Check scope precedence. Local (`.amplifier/settings.local.yaml`) overrides project and user.

**Q: How do I see what's actually active?**  
A: Use these commands:
```bash
amplifier provider current  # Active provider
amplifier bundle current    # Active bundle
amplifier module current    # Loaded modules
```

**Q: Where are configuration files?**  
A: Three locations:
- `.amplifier/settings.local.yaml` (local, gitignored)
- `.amplifier/settings.yaml` (project, committed)
- `~/.amplifier/settings.yaml` (user-global)

### "No providers mounted"

**Cause**: Missing API key

**Solution**:

```bash
# Run init to configure
amplifier init

# Or set API key manually
export ANTHROPIC_API_KEY="your-key"
```

### "Module not found"

**Cause**: Module not installed or missing git source in bundle

**Solution**: Modules are fetched dynamically from git sources. Check your bundle includes source fields or install the module.

```bash
# Check module resolution
amplifier source show tool-filesystem

# Check bundle
amplifier bundle show dev
```

### Sessions Not Showing

**Cause**: Sessions are project-scoped

**Solution**:

```bash
# Show all sessions across projects
amplifier session list --all-projects

# Or navigate to the project directory
cd /path/to/project
amplifier session list
```

### Installation & Update Issues

If `amplifier update` leaves things in a broken state, or you encounter persistent issues that configuration changes don't fix:

**→ See [Clean Reinstall (Recovery)](USER_ONBOARDING.md#clean-reinstall-recovery)**

---

## Tips & Best Practices

1. **Be specific** - More context = better results
2. **Use chat mode** - For complex, multi-turn tasks
3. **Try agents** - Let specialized agents handle focused work
4. **Leverage sessions** - Resume complex work later
5. **Experiment with providers** - Compare Anthropic vs OpenAI for your use case
6. **Customize bundles** - Create bundles tailored to your needs

---

## What's Next

- **Configuration deep dive**: [../docs/USER_ONBOARDING.md#quick-reference](../docs/USER_ONBOARDING.md#quick-reference)
- **See available modules**: [MODULES.md](./MODULES.md)
- **Build your own**: [DEVELOPER.md](./DEVELOPER.md)
- **Understand the philosophy**: [../docs/context/KERNEL_PHILOSOPHY.md](../docs/context/KERNEL_PHILOSOPHY.md)
