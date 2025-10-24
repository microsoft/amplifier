# Migration Guide: Claude Code ↔ Codex

## Introduction

This guide provides comprehensive instructions for migrating between Claude Code and Codex backends in the Amplifier project. The Amplifier project supports dual backends, allowing seamless switching between Claude Code's VS Code-integrated experience and Codex's standalone CLI approach.

### Purpose

This guide helps users:
- Migrate from Claude Code to Codex (or vice versa)
- Set up dual-backend configurations
- Troubleshoot common migration issues
- Understand the architectural differences between backends

### When to Migrate

**Migrate to Codex when you:**
- Prefer a standalone CLI over VS Code integration
- Need more granular control over sessions and tools
- Want to use Codex-specific features like profiles and MCP servers
- Work in environments where VS Code isn't available

**Migrate to Claude Code when you:**
- Prefer VS Code's integrated development experience
- Need automatic hooks for quality checks and notifications
- Want slash commands for quick workflow execution
- Require desktop notifications and TodoWrite integration

### Migration Philosophy

Both backends share core Amplifier modules (memory system, extraction, search), ensuring feature parity for essential functionality. Migration focuses on:
- Preserving your conversation history and memories
- Converting agents and workflows between formats
- Adapting to different automation models (hooks vs MCP servers)
- Maintaining environment consistency

**Key Insight**: Shared modules mean your memories, extracted knowledge, and search capabilities work identically across backends. Migration primarily involves adapting to different user interfaces and automation patterns.

## Pre-Migration Checklist

### Before Migrating

1. **Export Current Transcripts**
   ```bash
   # Export all transcripts to backup
   python tools/transcript_manager.py export --format both
   cp -r .data/transcripts backup_transcripts/
   cp -r ~/.codex/transcripts backup_codex_transcripts/
   ```

2. **Document Current Workflows**
   - List frequently used slash commands (Claude Code) or MCP tools (Codex)
   - Note custom agents and their purposes
   - Document environment variables and configuration settings

3. **Identify Custom Components**
   - List custom agents in `.claude/agents/` or `.codex/agents/`
   - Note custom commands in `.claude/commands/` or `.codex/commands/`
   - Document any custom hooks or MCP server modifications

4. **Backup Configurations**
   ```bash
   cp .claude/settings.json backup_claude_settings.json
   cp .codex/config.toml backup_codex_config.toml
   cp .env backup_env_file
   ```

5. **Note Environment Variables**
   ```bash
   env | grep AMPLIFIER > backup_env_vars.txt
   ```

6. **List Active Projects**
   - Identify projects using each backend
   - Note any project-specific configurations

### Verify Prerequisites

1. **Target CLI Installed**
   ```bash
   # For Codex migration
   codex --version
   
   # For Claude Code migration
   claude --version
   ```

2. **Virtual Environment Setup**
   ```bash
   uv run python --version
   echo $VIRTUAL_ENV
   ```

3. **Dependencies Installed**
   ```bash
   uv run python -c "import amplifier; print('Amplifier modules available')"
   ```

4. **Configuration Files Present**
   ```bash
   ls -la .claude/settings.json .codex/config.toml .env
   ```

## Migration Path 1: Claude Code → Codex

Follow these steps to migrate from Claude Code to Codex.

### Step 1: Install Codex CLI

```bash
# Follow Anthropic's installation instructions
# Typically involves downloading and installing the CLI
curl -fsSL https://install.codex.ai | sh
codex --version
```

### Step 2: Review Codex Configuration

```bash
# Check default configuration
cat .codex/config.toml

# Customize profiles as needed
# Edit .codex/config.toml to match your workflow preferences
```

### Step 3: Export Claude Code Transcripts

```bash
# Export all Claude Code transcripts
python tools/transcript_manager.py export --backend claude --format both

# Convert key transcripts to Codex format
python tools/transcript_manager.py convert <session-id> --from claude --to codex
```

### Step 4: Convert Agents

Agents are automatically converted via `tools/convert_agents.py`, but verify:

```bash
# Check converted agents
ls .codex/agents/

# Test agent conversion
python tools/convert_agents.py --verify
```

### Step 5: Set Environment Variables

```bash
# Update environment for Codex
export AMPLIFIER_BACKEND=codex
export CODEX_PROFILE=development

# Add to .env file
echo "AMPLIFIER_BACKEND=codex" >> .env
echo "CODEX_PROFILE=development" >> .env
```

### Step 6: Test Codex Setup

```bash
# Test basic functionality
./amplify-codex.sh --help

# Test with wrapper script
./amplify-codex.sh

# Verify MCP servers start
codex --profile development
# Then in Codex: check_code_quality
```

### Step 7: Migrate Workflows

| Claude Code Hook | Codex MCP Tool | Migration Notes |
|------------------|----------------|-----------------|
| `SessionStart.py` | `initialize_session` | Call manually or use wrapper |
| `PostToolUse.py` | `check_code_quality` | Call after code changes |
| `PreCompact.py` | `save_current_transcript` | Call before ending session |
| `SessionStop.py` | `finalize_session` | Call at session end |

### Step 8: Migrate Custom Commands

| Claude Code Command | Codex Alternative | Migration Notes |
|---------------------|-------------------|-----------------|
| `/architect` | `codex> architect agent` | Use agent directly |
| `/review` | `codex> check_code_quality` | Use MCP tool |
| `/prime` | Manual context loading | Load via `initialize_session` |

### Step 9: Update Documentation

- Update project READMEs to reference Codex workflows
- Document new MCP tool usage patterns
- Update team documentation for Codex-specific features

### Step 10: Verify Migration

```bash
# Test complete workflow
./amplify-codex.sh

# Verify memories load
codex> initialize_session with prompt "Test migration"

# Verify quality checks work
codex> check_code_quality with file_paths ["test.py"]

# Verify transcript export
codex> save_current_transcript
```

## Migration Path 2: Codex → Claude Code

Follow these steps to migrate from Codex to Claude Code.

### Step 1: Install Claude Code

```bash
# Install Claude Code extension in VS Code
# Follow Anthropic's VS Code extension installation
code --install-extension anthropic.claude
```

### Step 2: Review Claude Code Configuration

```bash
# Check settings
cat .claude/settings.json

# Customize hooks and permissions as needed
# Edit .claude/settings.json for your workflow
```

### Step 3: Export Codex Transcripts

```bash
# Export all Codex transcripts
python tools/transcript_manager.py export --backend codex --format both

# Convert key transcripts to Claude format (optional)
python tools/transcript_manager.py convert <session-id> --from codex --to claude
```

### Step 4: Convert Transcripts (Optional)

```bash
# Use transcript manager for conversion
python tools/transcript_manager.py convert <session-id> --from codex --to claude
```

### Step 5: Set Environment Variables

```bash
# Update environment for Claude Code
export AMPLIFIER_BACKEND=claude

# Add to .env file
echo "AMPLIFIER_BACKEND=claude" >> .env
```

### Step 6: Test Claude Code Setup

```bash
# Test basic functionality
./amplify.py --help

# Launch Claude Code
./amplify.py

# Verify hooks work (check notifications, quality checks)
```

### Step 7: Migrate Workflows

| Codex MCP Tool | Claude Code Hook | Migration Notes |
|----------------|------------------|-----------------|
| `initialize_session` | `SessionStart.py` | Automatic on session start |
| `check_code_quality` | `PostToolUse.py` | Automatic after tool use |
| `save_current_transcript` | `PreCompact.py` | Automatic before compaction |
| `finalize_session` | `SessionStop.py` | Automatic on session end |

### Step 8: Migrate Custom Tools

| Codex MCP Server | Claude Code Alternative | Migration Notes |
|------------------|-------------------------|-----------------|
| Custom MCP tools | Custom hooks or commands | Implement as Claude Code hooks |
| Agent execution | Task tool | Use Claude Code's Task tool |

### Step 9: Update Documentation

- Update project documentation for Claude Code workflows
- Document hook-based automation patterns
- Update team guides for VS Code integration

### Step 10: Verify Migration

```bash
# Test complete workflow
./amplify.py

# Verify hooks trigger (make changes, check notifications)
# Verify slash commands work (/architect, /review)
# Verify transcript export on compaction
```

## Using Both Backends

### Dual Backend Setup

```bash
# Install both CLIs
codex --version && claude --version

# Configure environment for switching
export AMPLIFIER_BACKEND_AUTO_DETECT=true

# Or set explicitly per session
export AMPLIFIER_BACKEND=claude  # or codex
```

### Workflow Recommendations

**For Development Work:**
- Use Claude Code for integrated VS Code experience
- Switch to Codex for headless/CI scenarios

**For Review Work:**
- Use Codex for structured MCP tool workflows
- Use Claude Code for quick slash commands

**For Team Collaboration:**
- Standardize on one backend per project
- Use transcript sharing for cross-backend visibility

### Transcript Sharing

```bash
# List transcripts from both backends
python tools/transcript_manager.py list --backend auto

# Search across backends
python tools/transcript_manager.py search "architecture decision"

# Restore conversation lineage across backends
python tools/transcript_manager.py restore
```

## Common Migration Issues

### Transcripts Not Converting

**Cause**: Format differences between backends
**Solution**: Use transcript manager conversion
```bash
python tools/transcript_manager.py convert <session-id> --from claude --to codex
```
**Workaround**: Manually copy transcript content

### Agents Not Working

**Cause**: Agent format differences (Task tool vs codex exec)
**Solution**: Re-run agent conversion
```bash
python tools/convert_agents.py --force
```
**Workaround**: Manually adapt agent definitions

### Memory System Not Loading

**Cause**: Environment variable not set
**Solution**: Check MEMORY_SYSTEM_ENABLED
```bash
echo $MEMORY_SYSTEM_ENABLED
export MEMORY_SYSTEM_ENABLED=true
```
**Workaround**: Restart session with proper environment

### Quality Checks Not Running

**Cause**: Makefile missing or incorrect
**Solution**: Verify Makefile has 'check' target
```bash
make check
```
**Workaround**: Run checks manually: `uv run ruff check && uv run pyright`

### Environment Variables Not Recognized

**Cause**: .env file not loaded or syntax error
**Solution**: Check .env file syntax
```bash
python -c "import dotenv; dotenv.load_dotenv(); print('Env loaded')"
```
**Workaround**: Export variables manually in shell

## Rollback Procedures

### Quick Rollback

```bash
# Restore environment variables
source backup_env_vars.txt

# Restore configuration files
cp backup_claude_settings.json .claude/settings.json
cp backup_codex_config.toml .codex/config.toml

# Restart with original backend
./amplify.py  # or ./amplify-codex.sh
```

### Full Rollback with Backup Restoration

```bash
# Restore transcripts
cp -r backup_transcripts/ .data/
cp -r backup_codex_transcripts/ ~/.codex/

# Restore configurations
cp backup_env_file .env

# Clear any new configurations
rm -f .codex/config.toml.new
rm -f .claude/settings.json.new

# Restart services
# (No services to restart, just relaunch CLI)
```

## Post-Migration Checklist

### Verify Everything Works

- [ ] Backend launches successfully
- [ ] Memory system loads memories
- [ ] Quality checks run and pass
- [ ] Transcript export works
- [ ] Agents execute correctly
- [ ] Custom workflows function
- [ ] Environment variables are respected

### Optimize New Setup

- [ ] Tune backend-specific configurations
- [ ] Set up preferred profiles/workflows
- [ ] Train team on new patterns
- [ ] Update CI/CD pipelines if needed
- [ ] Document any custom adaptations

## Team Migration

### Gradual Migration Approach

1. **Pilot Phase**: One developer migrates and documents issues
2. **Team Training**: Train team on new backend patterns
3. **Parallel Usage**: Allow both backends during transition
4. **Full Migration**: Complete migration with rollback plan

### Communication Plan

- Announce migration timeline and reasons
- Provide training sessions on new workflows
- Share migration guide and troubleshooting tips
- Set up support channels for migration issues
- Celebrate successful migration

## Reference

- [Backend Comparison Guide](BACKEND_COMPARISON.md) - Detailed feature comparison
- [Codex Integration Guide](CODEX_INTEGRATION.md) - Comprehensive Codex documentation
- [.claude/README.md](../.claude/README.md) - Claude Code integration details
- [.codex/README.md](../.codex/README.md) - Codex integration details
- [Transcript Manager](../tools/transcript_manager.py) - Cross-backend transcript tools
- Troubleshooting sections in [.codex/README.md](../.codex/README.md#troubleshooting)