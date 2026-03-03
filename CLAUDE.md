# CLAUDE.md — Amplifier

Amplifier is an AI-native development platform with 30+ specialized agents and 15+ slash commands.

## Identity and Environment

- Workspace root: `C:\claude\amplifier\`
- Platform: Windows Server 2025, Git Bash shell
- Safety rules: See `C:\claude\CLAUDE.md` (path restriction, reserved names, null redirection)
- Python: UV-managed (3.13), Node.js v24

## @imports

- @AGENTS.md

Philosophy and design files are on-demand (not always-loaded). Retrieve via `/docs search`:
- `ai_context/IMPLEMENTATION_PHILOSOPHY.md`, `ai_context/MODULAR_DESIGN_PHILOSOPHY.md`
- `ai_context/DESIGN-PHILOSOPHY.md`, `ai_context/DESIGN-PRINCIPLES.md`
- `ai_context/design/DESIGN-FRAMEWORK.md`, `ai_context/design/DESIGN-VISION.md`

## Operating Principles

1. **Plan before implementing.** Use TodoWrite for any task with more than one step. Ultra-think when populating the list. Start new work with `/brainstorm`, debug with `/debug`, build test-first with `/tdd`.

2. **Delegate to subagents.** Check `.claude/AGENTS_CATALOG.md` before starting. Use the Task tool. Launch agents in parallel by sending multiple Task calls in a single message. If a needed specialist doesn't exist, stop and ask the user to create it via the `/agents` command.

3. **Parallel execution is the default.** Sequential tool use requires justification. Never read files one at a time when they can be read in parallel. Send ONE message with MULTIPLE tool calls.

4. **Ask when uncertain.** If the goal is ambiguous, ask clarifying questions before writing any code. Prefer multiple-choice questions when possible.

## Memory and Documentation Tools

Before asking the user for context, run a `/recall` or `/docs search` query to check if the answer is already documented.

| Tool | How to invoke | What it retrieves |
|------|--------------|-------------------|
| `/recall <query>` | Temporal: `/recall yesterday`; Topic: `/recall FuseCP exchange`; Graph: `/recall graph last week` | Native JSONL session files indexed in `~/.claude/recall-index.sqlite` (FTS5, auto-updated on session end) |
| `/docs search <terms>` | `/docs search code style`; `/docs search WinRM` | BM25 full-text search across all repos' docs, keyed by doc registry |
| Doc registry | Auto-loaded at session start | Maps doc categories to file paths across all projects |
| Episodic memory | MCP plugin `mcp__plugin_episodic-memory_episodic-memory__search` | Semantic and keyword search across indexed past sessions |

**Priority:** Use `/recall` for session history lookups. Episodic memory (MCP plugin) remains available as a fallback but `/recall` is faster and more comprehensive.

## LLM-Friendly Documentation (llms.txt)

Each project provides two files at the repo root for LLM consumption:

- **`llms.txt`** — Hand-maintained navigation index. Use as a table of contents when orienting a new session.
- **`llms-full.txt`** — Auto-generated concatenation of all key docs. Share with Gemini/OpenCode for full project context in a single file.

Regenerate: `bash scripts/generate-llms.sh`. Update `llms.txt` manually when doc structure changes. Never hand-edit `llms-full.txt`. To add/remove docs, edit the `FILES` array in `scripts/generate-llms.sh`.

## Context Strategy

- Subagents fork context; use them to conserve the main session's window.
- Research agents run in **read-only mode**: Glob, Grep, Read, LS only — no Edit, Write, or Bash.
- Turn budgets are defined in `AGENTS.md` (Subagent Resilience Protocol section).
- If a needed specialized agent does not exist, stop and ask the user to create it via the `/agents` command; provide a detailed description.
- Code style guidance is on-demand: `/docs search code style` retrieves `docs/guides/code-style.md`.

## Amplifier Commands

Amplifier provides native commands in `.claude/commands/` invoked via `/command-name`. Available commands are listed in the system prompt's skills section. Before starting work, check if an applicable command exists.

| Command | Purpose |
|---------|---------|
| `/brainstorm` | Start new work — explore intent, design, route to execution |
| `/debug` | Hypothesis-driven root cause analysis |
| `/tdd` | Test-driven development (red-green-refactor) |
| `/create-plan` | Structured implementation plan with agent assignments |
| `/subagent-dev` | Execute plan tasks via specialized agents with two-stage review |
| `/verify` | Evidence-based verification before claiming done |
