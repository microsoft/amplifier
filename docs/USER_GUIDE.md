# Amplifier User Guide

Complete guide to using Amplifier for AI-assisted development.

> **Note**: Amplifier is under active development. Some features and commands may change.

---

## Installation

See [../README.md](../README.md#quick-start---zero-to-working-in-90-seconds) for complete installation guide.

**Quick summary:**

```bash
# Try without installing
uvx --from git+https://github.com/microsoft/amplifier@next amplifier

# Or install globally
uv tool install git+https://github.com/microsoft/amplifier@next
```

First-time setup happens automatically when you run Amplifier with no configuration.

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
- `/provider` - Show/change active provider
- `/profile` - Show/change active profile
- `/think` - Enable plan mode (read-only)
- `/do` - Disable plan mode (allow modifications)
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
2. **Profile** - Which profile (dev/production/test/minimal)
3. **Module** - Which capabilities (tools/hooks/agents)
4. **Source** - Where modules come from (git/local/package)

### Switching Providers

```bash
# Switch provider (interactive - prompts for model/config)
amplifier provider use openai

# Or explicit
amplifier provider use anthropic --model claude-opus-4-1
amplifier provider use openai --model gpt-4o
amplifier provider use ollama --model llama3

# Azure OpenAI (more complex)
amplifier provider use azure-openai --deployment gpt-5-codex --use-azure-cli

# Configure where to save
amplifier provider use openai --model gpt-4o --local    # Just you
amplifier provider use anthropic --model claude-opus-4-1 --project  # Team

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

### Switching Profiles (Workflows)

```bash
# Switch profile
amplifier profile use dev          # Development tools
amplifier profile use production   # Production safety
amplifier profile use test         # Testing setup
amplifier profile use base         # Minimal tools

# See what's active
amplifier profile current

# List available
amplifier profile list
```

**Bundled Profiles:**

| Profile      | Purpose          | Tools                  | Agents                    |
| ------------ | ---------------- | ---------------------- | ------------------------- |
| `foundation` | Bare minimum     | None                   | None                      |
| `base`       | Essential tools  | filesystem, bash       | None                      |
| `dev`        | Full development | base + web, search     | zen-architect, bug-hunter |
| `production` | Production-ready | base + web, monitoring | None                      |
| `test`       | Testing          | base + task            | None                      |
| `full`       | Everything       | All tools              | All agents                |

### Adding Capabilities

```bash
# Add module to current profile
amplifier module add tool-jupyter

# Add for team
amplifier module add tool-custom --project

# See loaded modules
amplifier module current
```

### Creating Custom Profiles

```bash
# Create custom profile
amplifier profile create my-workflow --extend dev

# Edit profile
# File created at: ~/.amplifier/profiles/my-workflow.md

# Use it
amplifier profile use my-workflow
```

See [../docs/USER_ONBOARDING.md#quick-reference](../docs/USER_ONBOARDING.md#quick-reference) for complete configuration reference.

---

## Working with Agents

Agents are specialized AI sub-sessions focused on specific tasks. The dev profile includes four agents:

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
# Continue where you left off
amplifier session resume <session-id>

# Resume with different profile
amplifier session resume <session-id> --profile full
```

### Where Are Sessions Stored?

Sessions are stored in `~/.amplifier/projects/<project-slug>/sessions/` where the project slug is based on your current working directory.

Example: Working in `/home/user/repos/myapp` stores sessions in:
`~/.amplifier/projects/-home-user-repos-myapp/sessions/`

Each session contains:

- `transcript.jsonl` - Message history
- `events.jsonl` - All events (tool calls, approvals, etc.)
- `metadata.json` - Session info (profile, provider, timestamps)

---

## Advanced Usage

### Per-Command Overrides

```bash
# Use different provider just once
amplifier run --provider openai "test prompt"

# Use different profile just once
amplifier --profile production "deploy task"

# Combine overrides
amplifier run --provider openai --profile test "compare models"
```

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

**Cause**: Module not installed or missing git source in profile

**Solution**: Modules are fetched dynamically from git sources. Check your profile includes source fields or install the module.

```bash
# Check module resolution
amplifier source show tool-filesystem

# Check profile
amplifier profile show dev
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

---

## Tips & Best Practices

1. **Be specific** - More context = better results
2. **Use chat mode** - For complex, multi-turn tasks
3. **Try agents** - Let specialized agents handle focused work
4. **Leverage sessions** - Resume complex work later
5. **Experiment with providers** - Compare Anthropic vs OpenAI for your use case
6. **Customize profiles** - Create profiles tailored to your needs

---

## What's Next

- **Configuration deep dive**: [../docs/USER_ONBOARDING.md#quick-reference](../docs/USER_ONBOARDING.md#quick-reference)
- **See available modules**: [MODULES.md](./MODULES.md)
- **Build your own**: [DEVELOPER.md](./DEVELOPER.md)
- **Understand the philosophy**: [../docs/context/KERNEL_PHILOSOPHY.md](../docs/context/KERNEL_PHILOSOPHY.md)
