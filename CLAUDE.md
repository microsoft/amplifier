# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

This project uses a shared context file (`AGENTS.md`) for common project guidelines. Please refer to it for information on build commands, code style, and design philosophy.

This file is reserved for Claude Code-specific instructions.

# import the following files (using the `@` syntax):

- @AGENTS.md
- @DISCOVERIES.md
- @ai_context/IMPLEMENTATION_PHILOSOPHY.md
- @ai_context/MODULAR_DESIGN_PHILOSOPHY.md
- @ai_context/DESIGN-PHILOSOPHY.md
- @ai_context/DESIGN-PRINCIPLES.md
- @ai_context/design/DESIGN-FRAMEWORK.md
- @ai_context/design/DESIGN-VISION.md

# Claude Code-Specific Operating Principles

## Task Planning with TodoWrite

- VERY IMPORTANT: Always think through a plan for every ask, and if it is more than a simple request, break it down and use TodoWrite tool to manage a todo list. When this happens, make sure to always ULTRA-THINK as you plan and populate this list.
- VERY IMPORTANT: Always consider if there is an agent available that can help with any given sub-task. Use the Task tool to delegate specific tasks to these agents. Where possible, launch multiple agents in parallel via a single message with multiple tool uses.

## Plan Mode Usage

When user has not provided enough clarity to CONFIDENTLY proceed, ask clarifying questions. Consider suggesting 'Plan Mode' for complex tasks:

<example>
User: "I want to create a new memory system."
Assistant: "Did you have a specific design or set of requirements in mind? Please consider switching to 'Plan Mode' until we are done planning (shift+tab to cycle through modes)."
</example>

Use ExitPlanMode tool when you have finished planning and there are no further clarifying questions you need answered from the user.

## Claude Code SDK Integration

For building code-based utilities that wrap sub-agent capabilities:
- See docs in `ai_context/claude_code/CLAUDE_CODE_SDK.md`
- See examples in `ai_context/git_collector/CLAUDE_CODE_SDK_PYTHON.md`

These enable creating "recipes" for dependable workflow execution that orchestrate Claude Code sub-agents for subtasks, using code where more structure is beneficial.
