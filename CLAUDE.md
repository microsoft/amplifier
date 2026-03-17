# CLAUDE.md — Amplifier

Amplifier is a self-improving AI development platform with 36 specialized agents, 35 slash commands, effort steering, and AutoContext-powered quality evaluation.

## Identity and Environment

- Workspace root: Linux: `/opt/amplifier/` | Windows: `C:\claude\amplifier\`
- Platform: Ubuntu Linux (primary), Windows Server 2025 (secondary)
- Safety rules: Linux: `scripts/guard-paths-linux.sh` | Windows: `C:\claude\CLAUDE.md`
- Python: UV-managed (3.13), Node.js v24
- Platform switching: `bash scripts/setup-platform-config.sh --force` or `/platform setup`

### Linux Configuration (172.31.250.2)

| Component | Path / Detail |
|-----------|--------------|
| Amplifier | `/opt/amplifier` |
| AutoContext | `/opt/autocontext/autocontext` (global MCP via `~/.claude.json`) |
| uv | `/home/claude/.local/bin/uv` (source `~/.local/bin/env` for shell) |
| Global MCP | `~/.claude.json`: autocontext, gitea, chrome-devtools, obsidian, cipher |
| Project MCP | `.mcp.json`: playwright, context7, deepwiki, repomix, autocontext |
| Claude Code | v2.1.76+, `/usr/local/bin/claude` |
| Gitea tools | `/usr/local/bin/gitea-mcp`, `/usr/local/bin/tea` |
| Chrome | Headless via Xvfb on DISPLAY=:2 |

**Key difference from Windows:** Global MCP servers registered via `claude mcp add -s user` (writes to `~/.claude.json`), not `~/.claude/mcp.json`. Use absolute paths for `uv` since `~/.local/bin` is not in default PATH.

## @imports

- @AGENTS.md
- @config/routing-matrix.yaml

Philosophy and design files are on-demand (not always-loaded). Retrieve via `/docs search`:
- `ai_context/IMPLEMENTATION_PHILOSOPHY.md`, `ai_context/MODULAR_DESIGN_PHILOSOPHY.md`
- `ai_context/DESIGN-PHILOSOPHY.md`, `ai_context/DESIGN-PRINCIPLES.md`
- `ai_context/design/DESIGN-FRAMEWORK.md`, `ai_context/design/DESIGN-VISION.md`

## Operating Principles

1. **Plan before implementing.** Use TodoWrite for any task with more than one step. Ultra-think when populating the list. Start new work with `/brainstorm`, debug with `/debug`, build test-first with `/tdd`.

2. **Delegate to the right model, not the biggest.** When routing-matrix says haiku or sonnet, dispatch as a subagent — cheaper without sacrificing quality. Only use Opus inline for deep reasoning. See `AGENTS.md` Sub-Agent Optimization Strategy for the dispatch table.

3. **Effort steering is automatic.** The routing matrix defines effort tiers (low/medium/high) and elastic turn ranges per role. When dispatching agents, pick turns from the range based on task complexity. The user's `/effort` setting is the ceiling. See `AGENTS.md` Turn Budgets for the resolution formula.

4. **Parallel execution is the default.** Sequential tool use requires justification. Never read files one at a time when they can be read in parallel. Send ONE message with MULTIPLE tool calls.

5. **Ask when uncertain.** If the goal is ambiguous, ask clarifying questions before writing any code. Prefer multiple-choice questions when possible.

## Memory and Documentation Tools

Before asking the user for context, run a `/recall` or `/docs search` query to check if the answer is already documented.

| Tool | How to invoke | What it retrieves |
|------|--------------|-------------------|
| `/recall <query>` | Temporal: `/recall yesterday`; Topic: `/recall FuseCP exchange`; Graph: `/recall graph last week` | Native JSONL session files indexed in `~/.claude/recall-index.sqlite` (FTS5, auto-updated on session end) |
| `/docs search <terms>` | `/docs search code style`; `/docs search WinRM` | BM25 full-text search across all repos' docs, keyed by doc registry |
| Doc registry | Auto-loaded at session start | Maps doc categories to file paths across all projects |
| Episodic memory | MCP plugin `mcp__plugin_episodic-memory_episodic-memory__search` | Semantic and keyword search across indexed past sessions |

**Priority:** Use `/recall` for session history lookups. Episodic memory (MCP plugin) remains available as a fallback but `/recall` is faster and more comprehensive.

## Self-Improvement Flywheel

Commands run → `/self-eval` scores (with effort metadata) → AutoContext accumulates patterns → `/self-improve` proposes instruction edits → CLAUDE.md/AGENTS.md evolve → better outputs → higher scores. See `AGENTS.md` AutoContext Quality Gates for practical guidance.

## LLM-Friendly Documentation (llms.txt)

Each project provides two files at the repo root for LLM consumption:

- **`llms.txt`** — Hand-maintained navigation index. Use as a table of contents when orienting a new session.
- **`llms-full.txt`** — Auto-generated concatenation of all key docs. Share with Gemini/OpenCode for full project context in a single file.

Regenerate: `bash scripts/generate-llms.sh`. Update `llms.txt` manually when doc structure changes. Never hand-edit `llms-full.txt`. To add/remove docs, edit the `FILES` array in `scripts/generate-llms.sh`.

## Amplifier Commands

Amplifier provides native commands in `.claude/commands/` invoked via `/command-name`. Available commands are listed in the system prompt's skills section. Before starting work, check if an applicable command exists.

| Command | Purpose |
|---------|---------|
| `/brainstorm` | Start new work — explore intent, design, route to execution |
| `/create-plan` | Structured implementation plan with agent assignments |
| `/subagent-dev` | Execute plan tasks via specialized agents with two-stage review |
| `/debug` | Hypothesis-driven root cause analysis |
| `/tdd` | Test-driven development (red-green-refactor) |
| `/verify` | Evidence-based verification before claiming done |
| `/evaluate` | Score output against quality rubrics (AutoContext) |
| `/frontend-design` | Build, refine, and evaluate frontend with anti-slop design (14 modes) |
| `/improve` | Iteratively refine output until threshold met |
| `/self-eval` | Evaluate Amplifier command quality for self-improvement |
| `/self-improve` | Propose evidence-based updates to CLAUDE.md/AGENTS.md |

All commands listed in system prompt skills section. Check before starting work.

**FuseCP-specific commands** (run in `C:\claude\fusecp-enterprise` session, NOT in Amplifier):

| Command | Purpose |
|---------|---------|
| `/fix-bugs` | Autonomous bug-fixing pipeline — fetch, triage, investigate, fix, deploy |
| `/test-verified` | Backend-Verified E2E auto-fix — run suite, classify failures, apply patterns, dispatch agents |

These commands reference FuseCP project structure (`ARCHITECTURE.md`), bugfix scripts, and E2E test infrastructure. They are part of the Amplifier command catalog but execute against FuseCP code.

## Compact Instructions

When context is compressed (automatic or via `/compact`), preserve in priority order:

1. **Architecture decisions** — NEVER summarize; keep exact rationale and constraints
2. **Modified files** — paths and key changes (not full diffs, just what changed and why)
3. **Verification status** — which tests/checks passed or failed, exact commands used
4. **Open TODOs and blockers** — unfinished work, known issues, rollback notes
5. **Agent dispatch results** — which agents ran, their verdicts (PASS/FAIL), key findings
6. **Tool outputs** — can delete content, but keep pass/fail status and error messages

Delete freely: file contents already read, intermediate search results, verbose tool output, exploratory dead ends that led nowhere.
