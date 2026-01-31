# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

```bash
make install                    # Install dependencies (uses uv)
make check                      # Run lint, format, type check
make test                       # Run all tests
uv run pytest tests/path/to/test.py::TestClass::test_name -v  # Single test
uv add package-name             # Add dependency (run in project directory)
uv add --dev package-name       # Add dev dependency
```

## Shared Context

This project uses `AGENTS.md` as the primary source for:
- Build/test/lint commands
- Code style and formatting guidelines
- Implementation philosophy and design principles
- Sub-agent optimization strategy

**Always consult `AGENTS.md` for detailed guidance.** The sections below are Claude Code-specific instructions that supplement (not duplicate) that file.

## Recommended Context Files

When working on this project, consider reading these files for deeper context:
- `AGENTS.md` - Core development guidelines and philosophy
- `DISCOVERIES.md` - Non-obvious problems and solutions discovered during development
- `ai_context/IMPLEMENTATION_PHILOSOPHY.md` - Detailed implementation approach
- `ai_context/MODULAR_DESIGN_PHILOSOPHY.md` - Brick-and-stud modular patterns
- `ai_context/DESIGN-PHILOSOPHY.md` - High-level design thinking
- `ai_context/DESIGN-PRINCIPLES.md` - Core design principles

## Agent and Command Discovery

- **Available agents**: `.claude/agents/` - Specialized sub-agents for various tasks
- **Slash commands**: `.claude/commands/` - User-invocable commands like `/commit`, `/prime`
- **Agent catalog summary**: See `AGENTS.md` section "Available Specialized Agents"

## Claude Code Operating Principles

### Planning and Task Management

- **Break down complex requests**: For non-trivial tasks, decompose into smaller steps and use the todo/task tracking tools
- **Ask clarifying questions**: If the user hasn't provided enough clarity to confidently proceed, ask before implementing
- **Use Plan Mode for uncertainty**: When requirements are unclear, suggest switching to Plan Mode (shift+tab to cycle modes)

### Parallel Execution Strategy

**Always ask: "What can I do in parallel here?"** Send ONE message with MULTIPLE tool calls when tasks don't depend on each other.

**Parallelize when tasks:**
- Don't depend on each other's output
- Perform similar operations on different targets
- Can be delegated to different agents
- Gather independent information

**Anti-pattern:**
```
"Let me read the first file" → [Read file1.py]
"Now let me read the second file" → [Read file2.py]
```

**Correct pattern:**
```
"I'll examine these files" → [Single message: Read file1.py, Read file2.py, Read file3.py]
```

### Sub-Agent Delegation

- **Delegate everything possible** to specialized sub-agents
- **Each sub-agent** only returns the parts of their context that are needed, conserving context
- **Use sub-agents for**: Analysis tasks, parallel exploration, complex multi-step work, specialized expertise
- **When struggling**: Propose a new specialized agent - agent creation is cheap

### Context Window Management

- **Limited context requires strategic compaction** - Details get summarized and lost over long sessions
- **Two key solutions**:
  1. Use memory system for critical persistent information
  2. Use sub-agents to fork context and conserve space
- **Be selective** about what's truly critical to persist

## Document Reference Protocol

When working with documents that contain references:

1. **Always check for references/citations** at the end of documents
2. **Re-read source materials** when implementing referenced concepts
3. **Understand the backstory/context** before applying ideas
4. **Track which articles informed which decisions** for learning

This ensures we build on the full depth of ideas, not just their summaries.
