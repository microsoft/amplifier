---
name: agent-name
description: When to use this agent and what it does
tools: [Read, Grep, Glob, Bash]
model: inherit
---
```

### Field Descriptions

- **`name`**: Short identifier for the agent (lowercase with hyphens)
- **`description`**: Clear description of when to use the agent and its capabilities. This field drives automatic agent selection in Codex.
- **`tools`**: Array of allowed Codex tools. Common tools include:
  - `Read`: Read file contents
  - `Grep`: Search for patterns in files
  - `Glob`: List files matching patterns
  - `Bash`: Execute shell commands
  - `Write`: Create or overwrite files
  - `Edit`: Modify existing files
- **`model`**: Model to use ("inherit" uses the profile default)

**Note**: Unlike Claude Code agents, there is no "Additional Instructions" section. All agent behavior is defined in the description and methodology content below the frontmatter.

## Available Agents

### Architecture & Design
- **zen-architect**: Designs software architecture with minimal complexity focus
- **database-architect**: Designs database schemas and data architectures
- **api-contract-designer**: Designs API contracts and interfaces

### Implementation
- **modular-builder**: Implements code using modular, testable patterns
- **integration-specialist**: Handles system integration and API connections

### Quality & Testing
- **bug-hunter**: Investigates and fixes software bugs
- **test-coverage**: Analyzes and improves test coverage
- **security-guardian**: Identifies and fixes security vulnerabilities

### Analysis
- **analysis-engine**: Performs deep code and system analysis
- **pattern-emergence**: Identifies patterns in code and data
- **insight-synthesizer**: Synthesizes insights from complex information

### Knowledge
- **concept-extractor**: Extracts key concepts from documentation
- **knowledge-archaeologist**: Uncovers hidden knowledge in codebases
- **content-researcher**: Researches and synthesizes information

### Specialized
- **amplifier-cli-architect**: Designs CLI tools following project patterns
- **performance-optimizer**: Optimizes code and system performance
- **visualization-architect**: Designs data visualization solutions

## Using Agents with Codex

### Automatic Agent Selection

Codex can automatically select the most appropriate agent based on your task description:

```bash
# Codex auto-selects based on task description
codex exec "Find and fix the authentication bug"
# Likely routes to bug-hunter agent

codex exec "Design the caching layer architecture"
# Likely routes to zen-architect agent
```

### Manual Agent Selection

For precise control, explicitly specify which agent to use:

```bash
# Explicitly specify agent
codex exec --agent bug-hunter "Investigate the memory leak"

codex exec --agent zen-architect "Review this module for complexity"
```

### Agent with Context File

Use agent definitions directly as context:

```bash
# Use agent definition as context
codex exec --context-file=.codex/agents/bug-hunter.md "Debug the API timeout"
```

## Agent Invocation Patterns

### From Command Line

Invoke agents directly for common development tasks:

```bash
# Bug investigation
codex exec "The user authentication is failing intermittently"

# Architecture design
codex exec --agent zen-architect "Design the caching layer for the API"

# Test coverage analysis
codex exec --agent test-coverage "Analyze test coverage for the payment module"
```

### From Backend Abstraction

Use the programmatic API for agent spawning:

```python
from amplifier import spawn_agent

# Spawn agent programmatically
result = spawn_agent(
    agent_name="bug-hunter",
    task="Find the root cause of the database connection timeout"
)
print(result['result'])
```

### From Codex Wrapper

Use the wrapper script for seamless integration:

```bash
# Using amplify-codex.sh wrapper
./amplify-codex.sh
# Then in Codex session, agents are available automatically
```

## Key Differences from Claude Code

| Aspect | Claude Code | Codex |
|--------|-------------|-------|
| Agent Invocation | Task tool (automatic) | Natural language or --agent flag |
| Tool References | Task, TodoWrite, WebFetch | Read, Grep, Glob, Bash, Write |
| Additional Instructions | Large boilerplate section | Not needed |
| Agent Selection | Automatic via description | Automatic or manual |
| Spawning Syntax | `Task(agent_name, task)` | `codex exec --agent <name> "<task>"` |
| Configuration | settings.json | config.toml |

## Agent Development

### Creating New Agents

1. Start with the standard template structure
2. Define clear purpose and triggers in the description field
3. Specify minimal tool set needed for the agent's tasks
4. Write focused methodology without Claude-specific references
5. Test with: `codex exec --agent <name> "<test-task>"`

### Converting from Claude Code

1. Use the `tools/convert_agents.py` script for automated conversion
2. Review the converted agent for accuracy
3. Test with Codex to ensure functionality
4. Adjust description for better auto-selection if needed

## Agent Methodology

Converted agents preserve the core methodology from their Claude Code versions:

- **Operating Modes**: ANALYZE, ARCHITECT, REVIEW modes still apply
- **Decision Frameworks**: Structured decision-making processes remain intact
- **Philosophy References**: Links to `@ai_context/IMPLEMENTATION_PHILOSOPHY.md` are preserved
- **Collaboration**: Agents can delegate to each other via natural language descriptions

## Tools Available to Agents

Codex provides these tools for agent use:

- **Read**: Read file contents
- **Write**: Create or overwrite files
- **Edit**: Modify existing files
- **Grep**: Search for patterns in files
- **Glob**: List files matching patterns
- **Bash**: Execute shell commands

**Note**: Codex does not include Task, TodoWrite, WebFetch, or WebSearch tools available in Claude Code.

## Troubleshooting

### Agent not found
- Verify agent file exists in `.codex/agents/`
- Check filename matches agent name in frontmatter
- Ensure YAML frontmatter is valid

### Agent not being selected automatically
- Review description field for clarity
- Make description more specific to task type
- Use manual selection with `--agent` flag

### Agent fails to execute
- Check tool permissions in `.codex/config.toml`
- Verify agent has necessary tools in frontmatter
- Review Codex logs for error details

## Best Practices

- Use descriptive agent names (lowercase-with-hyphens)
- Write clear, specific descriptions for auto-selection
- Minimize tool set to what's actually needed
- Test agents with various task descriptions
- Keep agent methodology focused and actionable
- Avoid Claude-specific references in custom agents

## Examples

### Example 1: Bug Investigation
```bash
# Automatic selection
codex exec "The user authentication is failing intermittently"

# Manual selection
codex exec --agent bug-hunter "Investigate auth failures"
```

### Example 2: Architecture Design
```bash
codex exec --agent zen-architect "Design a caching layer for the API"
```

### Example 3: Test Coverage Analysis
```bash
codex exec --agent test-coverage "Analyze test coverage for the payment module"
```

## Integration with Backend Abstraction

The `amplifier/core/agent_backend.py` module provides unified access to agents across backends. The `CodexAgentBackend` class handles Codex agent execution:

```python
from amplifier.core.agent_backend import CodexAgentBackend

backend = CodexAgentBackend()
result = backend.spawn_agent("bug-hunter", "Investigate memory leak")