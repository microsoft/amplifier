# Claude Code Platform Architecture

This directory contains the core configuration and extensions that transform Claude Code from a coding assistant into a complete development platform.

## 📁 Directory Structure

```
.claude/
├── agents/            # AI agents that assist with various tasks
├── commands/          # Custom commands that extend Claude Code
├── tools/             # Shell scripts for automation and notifications
├── docs/              # Deep-dive documentation
├── settings.json      # Claude Code configuration
└── README.md          # This file
```

## 🏗️ Architecture Overview

### AI Agents

The `agents/` directory contains the AI agents that assist with various tasks within Claude Code.

- Each `.md` file defines a specific agent and its capabilities.
- The agents can be composed together to handle more complex tasks.
- Agents can also share data and context with each other.

### Custom Commands

The `commands/` directory contains markdown files that define custom workflows:

- Each `.md` file becomes a slash command in Claude Code
- Commands can orchestrate complex multi-step processes
- They encode best practices and methodologies
- Key commands include `/transcripts` for restoring conversation history after compaction

### Automation Tools

The `tools/` directory contains scripts that integrate with Claude Code:

- `notify.sh` - Cross-platform desktop notifications
- `make-check.sh` - Intelligent quality check runner
- `subagent-logger.py` - Logs interactions with sub-agents
- `hook_precompact.py` - Exports conversation transcripts before compaction
- `transcript_manager.py` - CLI tool for managing conversation transcripts
- Triggered by hooks defined in `settings.json`

### Configuration

`settings.json` defines:

- **Hooks**: Automated actions after specific events
- **Permissions**: Allowed commands and operations
- **MCP Servers**: Extended capabilities

## 🔧 How It Works

### Event Flow

1. You make a code change in Claude Code
2. PostToolUse hook triggers `make-check.sh`
3. Quality checks run automatically
4. Notification hook triggers `notify.sh`
5. You get desktop notification of results
6. If sub-agents were used, `subagent-logger.py` logs their interactions to `.data/subagents-logs`
7. Before conversation compaction, PreCompact hook triggers `hook_precompact.py`
8. Full transcript is exported to `.data/transcripts/` preserving your entire conversation

### Command Execution

1. You type `/command-name` in Claude Code
2. Claude reads the command definition
3. Executes the defined process
4. Can spawn sub-agents for complex tasks
5. Returns results in structured format

### Philosophy Integration

1. `/prime` command loads philosophy documents
2. These guide all subsequent AI interactions
3. Ensures consistent coding style and decisions
4. Philosophy becomes executable through commands

## 🚀 Extending the Platform

### Adding AI Agents

Options:

- [Preferred]: Create via Claude Code:
  - Use the `/agents` command to define the agent's capabilities.
  - Provide the definition for the agent's behavior and context.
  - Let Claude Code perform its own optimization to improve the agent's performance.
- [Alternative]: Create manually:
  - Define the agent in a new `.md` file within `agents/`.
  - Include all necessary context and dependencies.
  - Must follow the existing agent structure and guidelines.

### Adding New Commands

Create a new file in `commands/`:

```markdown
## Usage

`/your-command <args>`

## Context

- What this command does
- When to use it

## Process

1. Step one
2. Step two
3. Step three

## Output Format

- What the user sees
- How results are structured
```

### Adding Automation

Edit `settings.json`:

```json
{
  "hooks": {
    "YourEvent": [
      {
        "matcher": "pattern",
        "hooks": [
          {
            "type": "command",
            "command": "your-script.sh"
          }
        ]
      }
    ]
  }
}
```

### Adding Tools

1. Create script in `tools/`
2. Make it executable: `chmod +x tools/your-tool.sh`
3. Add to hooks or commands as needed

## 🎯 Design Principles

1. **Minimal Intrusion**: Stay in `.claude/` to not interfere with user's project
2. **Cross-Platform**: Everything works on Mac, Linux, Windows, WSL
3. **Fail Gracefully**: Scripts handle errors without breaking workflow
4. **User Control**: Easy to modify or disable any feature
5. **Team Friendly**: Configurations are shareable via Git

## 📚 Learn More

- [Command Reference](../.ai/docs/commands.md)
- [Automation Guide](../.ai/docs/automation.md)
- [Notifications Setup](../.ai/docs/notifications.md)
