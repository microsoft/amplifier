# Subagents in the SDK

> Working with subagents in the Claude Code SDK

Subagents in the Claude Code SDK are specialized AIs that are orchestrated by the main agent.
Use subagents for context management and parallelization.

This guide explains how SDK applications interact with and utilize subagents that are created via markdown files.

## Overview

Subagents are created exclusively through the filesystem-based approach by placing markdown files with YAML frontmatter in designated directories. The SDK can then invoke these pre-defined subagents during execution.

## Benefits of Using Subagents

### Context Management

Subagents maintain separate context from the main agent, preventing information overload and keeping interactions focused. This isolation ensures that specialized tasks don't pollute the main conversation context with irrelevant details.

**Example**: A `research-assistant` subagent can explore dozens of files and documentation pages without cluttering the main conversation with all the intermediate search results - only returning the relevant findings.

### Parallelization

Multiple subagents can run concurrently, dramatically speeding up complex workflows.

**Example**: During a code review, you can run `style-checker`, `security-scanner`, and `test-coverage` subagents simultaneously, reducing review time from minutes to seconds.

### Specialized Instructions and Knowledge

Each subagent can have tailored system prompts with specific expertise, best practices, and constraints.

**Example**: A `database-migration` subagent can have detailed knowledge about SQL best practices, rollback strategies, and data integrity checks that would be unnecessary noise in the main agent's instructions.

### Tool Restrictions

Subagents can be limited to specific tools, reducing the risk of unintended actions.

**Example**: A `doc-reviewer` subagent might only have access to Read and Grep tools, ensuring it can analyze but never accidentally modify your documentation files.

## Creating Subagents

Subagents are defined as markdown files in specific directories:

- **Project-level**: `.claude/agents/*.md` - Available only in the current project
- **User-level**: `~/.claude/agents/*.md` - Available across all projects

### File Format

Each subagent is a markdown file with YAML frontmatter:

```markdown
---
name: code-reviewer
description: Expert code review specialist. Use for quality, security, and maintainability reviews.
tools: Read, Grep, Glob, Bash # Optional - inherits all tools if omitted
---

Your subagent's system prompt goes here. This defines the subagent's
role, capabilities, and approach to solving problems.

Include specific instructions, best practices, and any constraints
the subagent should follow.
```

### Configuration Fields

| Field         | Required | Description                                                           |
| :------------ | :------- | :-------------------------------------------------------------------- |
| `name`        | Yes      | Unique identifier using lowercase letters and hyphens                 |
| `description` | Yes      | Natural language description of when to use this subagent             |
| `tools`       | No       | Comma-separated list of allowed tools. If omitted, inherits all tools |

## How the SDK Uses Subagents

When using the Claude Code SDK, subagents defined in the filesystem are automatically available. Claude Code will:

1. **Auto-detect subagents** from `.claude/agents/` directories
2. **Invoke them automatically** based on task matching
3. **Use their specialized prompts** and tool restrictions
4. **Maintain separate context** for each subagent invocation

The SDK respects the filesystem configuration - there's no programmatic way to create subagents at runtime. All subagents must be defined as files before SDK execution.

## Example Subagents

For comprehensive examples of subagents including code reviewers, test runners, debuggers, and security auditors, see the [main Subagents guide](/en/docs/claude-code/sub-agents#example-subagents). The guide includes detailed configurations and best practices for creating effective subagents.

## SDK Integration Patterns

### Automatic Invocation

The SDK will automatically invoke appropriate subagents based on the task context. Ensure your subagent's `description` field clearly indicates when it should be used:

```markdown
---
name: performance-optimizer
description: Use PROACTIVELY when code changes might impact performance. MUST BE USED for optimization tasks.
tools: Read, Edit, Bash, Grep
---
```

### Explicit Invocation

Users can request specific subagents in their prompts:

```typescript
// When using the SDK, users can explicitly request subagents:
const result = await query({
  prompt: "Use the code-reviewer subagent to check the authentication module",
});
```

## Tool Restrictions

Subagents can have restricted tool access via the `tools` field:

- **Omit the field** - Subagent inherits all available tools (default)
- **Specify tools** - Subagent can only use listed tools

Example of a read-only analysis subagent:

```markdown
---
name: code-analyzer
description: Static code analysis and architecture review
tools: Read, Grep, Glob # No write or execute permissions
---

You are a code architecture analyst. Analyze code structure,
identify patterns, and suggest improvements without making changes.
```

## Related Documentation

- [Main Subagents Guide](/en/docs/claude-code/sub-agents) - Comprehensive subagent documentation
- [SDK Configuration Guide](/en/docs/claude-code/sdk/sdk-configuration-guide) - Overview of configuration approaches
- [Settings](/en/docs/claude-code/settings) - Configuration file reference
- [Slash Commands](/en/docs/claude-code/slash-commands) - Custom command creation
