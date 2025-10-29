# Codex Custom Prompts

This directory contains Codex custom prompts that extend functionality with reusable task templates. These prompts are the Codex equivalent of Claude Code's custom commands (stored in `.claude/commands/`).

## Purpose

Custom prompts provide:
- **Reusable Templates**: Pre-configured workflows for common complex tasks
- **Agent Orchestration**: Coordinated multi-agent workflows with clear patterns
- **Tool Integration**: Structured use of Codex tools (Read, Write, Edit, Grep, Glob, Bash)
- **Automatic Loading**: Prompts are loaded automatically and accessible via `/prompts:` menu in Codex TUI

## Prompt Structure

Each prompt is a Markdown file with YAML frontmatter:

```yaml
---
name: prompt-identifier
description: Clear description for menu display and automatic selection
arguments:
  - name: argument_name
    description: What this argument represents
    required: true
model: inherit  # or specify a model
tools: [Read, Write, Edit, Grep, Glob, Bash]
---

# Prompt content in Markdown
Use {argument_name} placeholders for arguments
```

### Frontmatter Fields

- **name**: Lowercase identifier with hyphens (e.g., `ultrathink-task`)
- **description**: Clear, concise description shown in prompt selection menu
- **arguments**: Array of argument definitions:
  - `name`: Argument identifier
  - `description`: What the argument represents
  - `required`: Boolean flag
- **model**: Model to use (`inherit` for profile default, or specify model name)
- **tools**: Array of Codex tools the prompt can use

### Content Section

- Written in Markdown
- Uses `{argument_name}` placeholders for dynamic values
- Should be clear, focused, and avoid backend-specific references
- Can include detailed instructions, examples, and guidance

## Available Prompts

### ultrathink-task

**Description**: Orchestrate specialized agents for complex tasks requiring deep reasoning, architecture design, implementation, and validation cycles

**Arguments**:
- `task_description` (required): Detailed description of the complex task to be accomplished

**Tools**: Read, Write, Edit, Grep, Glob, Bash

**Key Features**:
- Multi-agent coordination and orchestration
- Sequential and parallel delegation patterns
- Validation cycles between architecture, implementation, and review
- Integration with amplifier CLI tools via Makefile
- Proactive contextualization for tool opportunities
- Comprehensive task tracking and reasoning

**When to Use**:
- Complex feature implementation requiring multiple phases
- Architecture design followed by implementation and review
- Bug investigation requiring analysis, fix, and validation
- Tasks benefiting from specialized agent expertise
- Large-scale refactoring with validation steps
- Projects requiring amplifier CLI tool integration

**Source**: Converted from `.claude/commands/ultrathink-task.md`

## Usage Instructions

### Primary Method: Command Line with Context File (Always Works)

The most reliable way to use custom prompts works with all Codex versions:

```bash
# Direct context file usage (recommended)
codex exec --context-file=.codex/prompts/ultrathink-task.md "Implement JWT authentication"

# With full path
codex exec --context-file=/path/to/project/.codex/prompts/ultrathink-task.md "<task>"

# In scripts
#!/bin/bash
TASK="Refactor the API layer to use async/await patterns"
codex exec --context-file=.codex/prompts/ultrathink-task.md "$TASK"
```

### Alternative: Interactive TUI (Version-Dependent)

**Note**: The `/prompts:` menu and `--prompt` flag require Codex CLI support for prompt registries. If these don't work in your Codex version, use the `--context-file` method above.

1. Launch Codex:
   ```bash
   codex
   # or
   ./amplify-codex.sh
   ```

2. Invoke prompt menu (if supported):
   ```
   /prompts:
   ```

3. Select `ultrathink-task` from the menu

4. Provide the task description when prompted

## Creating New Custom Prompts

### 1. Start with Template

Create a new `.md` file in this directory:

```yaml
---
name: my-custom-prompt
description: What this prompt does
arguments:
  - name: input_param
    description: Description of parameter
    required: true
model: inherit
tools: [Read, Write, Edit]
---

# Your prompt content here
Task: {input_param}

## Instructions
- Step 1
- Step 2
```

### 2. Define Clear Purpose

- What specific problem does this prompt solve?
- When should users choose this over direct commands?
- What workflow pattern does it implement?

### 3. Specify Minimal Tool Set

Only include tools actually needed:
- **Read**: Reading file contents
- **Write**: Creating new files
- **Edit**: Modifying existing files
- **Grep**: Searching within files
- **Glob**: Finding files by pattern
- **Bash**: Running shell commands

### 4. Write Focused Content

- Clear, actionable instructions
- Relevant examples where helpful
- Avoid backend-specific tool references (no TodoWrite, Task, WebFetch)
- Use natural language for agent delegation
- Include reasoning/validation guidance

### 5. Test with Codex

```bash
codex
/prompts:
# Select your new prompt and test with various inputs
```

## Differences from Claude Code Commands

| Aspect | Claude Code Commands | Codex Custom Prompts |
|--------|---------------------|---------------------|
| **Format** | Plain Markdown with sections | YAML frontmatter + Markdown content |
| **Invocation** | `/command-name` | `/prompts:` menu selection |
| **Arguments** | `$ARGUMENTS` variable | `{argument_name}` placeholders |
| **Tools** | Task, TodoWrite, WebFetch, WebSearch | Read, Write, Edit, Grep, Glob, Bash |
| **Agent Spawning** | `Task(agent="name", task="...")` | Natural language delegation |
| **Location** | `.claude/commands/` | `.codex/prompts/` |
| **Configuration** | Automatic discovery | Configured in `.codex/config.toml` |

## Migration from Claude Code Commands

To convert a Claude Code command:

1. **Add YAML frontmatter** with name, description, arguments, model, tools
2. **Replace `$ARGUMENTS`** with `{argument_name}` in content
3. **Remove TodoWrite references** - use task tracking in reasoning or MCP tools
4. **Update tool references** - Task → Read, TodoWrite → reasoning, WebFetch → Bash with curl
5. **Convert agent spawning** - `Task(agent, task)` → natural language delegation
6. **Test and refine** - Ensure prompt works with Codex's interaction model

Example conversion:
```markdown
# Claude Code (.claude/commands/example.md)
## Usage
/example <description>

Use TodoWrite to track tasks.
Spawn agents with Task(agent="zen-architect", task="...").

# Codex (.codex/prompts/example.md)
---
name: example
description: Example prompt
arguments:
  - name: description
    description: Task description
    required: true
model: inherit
tools: [Read, Write, Edit]
---

Task: {description}

Track tasks in your reasoning.
Delegate to agents: "I need zen-architect to analyze..."
```

## Best Practices

1. **Keep prompts focused** - One clear purpose per prompt
2. **Provide context** - Explain when and why to use the prompt
3. **Document arguments** - Clear descriptions help users understand inputs
4. **Minimize tool usage** - Only include tools actually needed
5. **Test thoroughly** - Verify with various inputs and edge cases
6. **Update documentation** - Keep this README in sync with available prompts
7. **Version control** - Commit prompts with clear commit messages
8. **Learn from examples** - Study `ultrathink-task.md` as a reference

## Related Documentation

- `.codex/README.md` - Main Codex integration documentation
- `.claude/commands/` - Source commands for conversion
- `.codex/agents/README.md` - Agent system documentation
- `TUTORIAL.md` - Usage tutorials including ultrathink-task examples

## Support

For issues with custom prompts:
1. Check YAML frontmatter syntax (validate with a YAML parser)
2. Verify argument placeholders match frontmatter definitions
3. Test prompt loading with `codex` and `/prompts:` menu
4. Review `.codex/config.toml` prompts configuration
5. Check Codex CLI logs for loading errors
