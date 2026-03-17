# AI Assistant Guidance

This file provides guidance to AI assistants when working with code in this repository.

---

## 💎 CRITICAL: Respect User Time - Test Before Presenting

**The user's time is their most valuable resource.** When you present work as "ready" or "done", you must have:

1. **Tested it yourself thoroughly** - Don't make the user your QA
2. **Fixed obvious issues** - Syntax errors, import problems, broken logic
3. **Verified it actually works** - Run tests, check structure, validate logic
4. **Only then present it** - "This is ready for your review" means YOU'VE already validated it

**User's role:** Strategic decisions, design approval, business context, stakeholder judgment
**Your role:** Implementation, testing, debugging, fixing issues before engaging user

**Anti-pattern**: "I've implemented X, can you test it and let me know if it works?"
**Correct pattern**: "I've implemented and tested X. Tests pass, structure verified, logic validated. Ready for your review. Here is how you can verify."

**Remember**: Every time you ask the user to debug something you could have caught, you're wasting their time on non-stakeholder work. Be thorough BEFORE engaging them.

---

## Git Workflow

**PR-first policy**: All work goes through feature branches + PRs. Never push to main. Never merge without user confirmation. Full details: `/docs search git workflow`.

**Commit footer**: Always append the Amplifier co-author tag (see `docs/guides/git-workflow.md`).

**Remote layout**: `origin` = Gitea (primary), `github` = GitHub (read-only backup, auto-synced).

**Gitea operations:** `mcp__gitea__*` MCP tools (primary) → `tea` CLI (fallback) → NEVER `gh` CLI for Gitea (`gh` talks to GitHub, not Gitea). MCP tools support parallel calls and work natively in subagents.

---

## Sub-Agent Optimization Strategy

**Cost-effective model selection:** The session runs on Opus, but most tasks don't need Opus-level reasoning. Use the routing matrix to dispatch at the right tier:

| Task type | Model | Dispatch as |
|-----------|-------|-------------|
| File searches, context gathering, cleanup | haiku | Subagent (always) |
| Implementation, review, research | sonnet | Subagent (always) |
| Architecture, security, complex debugging | opus | Inline or subagent |
| Quick 1-2 line edits, config changes | opus (inline) | Inline (cheaper than subagent overhead) |

**Rule of thumb:** If the routing matrix says haiku or sonnet for the agent's role, dispatch as a subagent — don't run it inline on Opus. The quality is the same and the cost is lower. Only use Opus inline for tasks that genuinely need deep reasoning.

Always check `.claude/AGENTS_CATALOG.md` before starting. Proactively delegate to specialized agents. Propose new agents when a task lacks a specialist — agent creation is cheap and pays off immediately.

## Subagent Resilience Protocol

Subagents launched via the Task tool have their own context windows that can fill up during execution. When this happens, agents either stop abruptly with partial results or shift into "summary mode" instead of completing actual work. This protocol prevents both failure modes.

### Turn Budgets (Elastic)

Turn budgets are **elastic** — defined as `{min, default, max}` per role in `config/routing-matrix.yaml` (always-loaded via @import). The orchestrator picks within the range using effort steering:

`resolved_effort = min(session_effort, max(role_effort, task_signals))`

- `low` → `min` turns | `medium` → `default` | `high` → `max` | `max` → `max` + auto-resume (3 cycles)

Tuned for **Opus 4.6 with 1M context**. Prefer generous budgets over tiny task decomposition.

### Read-Only Research Constraint

Research and scout subagents (context gathering, codebase exploration, documentation lookup) must be **read-only**. Include this instruction in their prompts:

> **READ-ONLY MODE: You are a research agent. Use ONLY Read, Glob, Grep, LS, and search tools. Do NOT use Edit, Write, Bash, or any tool that modifies files or executes commands. Your job is to gather and return information, not to make changes.**

This applies to:
- Context scouts dispatched by `/brainstorm` and `/create-plan`
- `agentic-search` agents doing pre-implementation reconnaissance
- Any `general-purpose` agent with `model="haiku"` used for information gathering

Implementation agents (`modular-builder`, `bug-hunter`, etc.) are exempt — they need write access.

### Resume Protocol

When an agent returns, the orchestrator evaluates completeness and resumes if needed:

1. **Dispatch** the agent with `max_turns=N`
2. **Receive** the result and `agent_id`
3. **Evaluate** completeness:
   - **Complete**: Files written, conclusions stated, explicit "done" markers → use the result
   - **Incomplete**: Trailing "I'll now...", partial lists, no conclusion, mid-sentence stops → resume
4. **Resume** using the Task tool's `resume` parameter with the returned agent ID, and prompt: "Continue your work. You were stopped due to turn limits. Focus on completing the remaining items."
5. **Limit** to 3 resume cycles maximum, then escalate to the user

The agent does not need to know about this pattern. It gets stopped, gets resumed with full prior context via the Task tool's built-in resume capability, and continues. Each resume gets a fresh output budget.

### Synthesis Guard (All Agents)

Every custom agent in `.claude/agents/` includes a **Synthesis guard** rule in its Context Budget section:

> When nearing your turn limit, STOP tool calls and produce your final output with whatever findings you have. Partial results with clear structure are MORE valuable than exhausting all turns on research with no summary. Always reserve at least 2 turns for writing your response.

This prevents the failure mode where an agent uses all turns on tool calls (Glob, Grep, Read) and returns with no text output — the orchestrator gets an empty result and must fall back to manual investigation. The guard ensures agents always produce structured findings, even if incomplete.

**When creating new agents**, always include this rule in the Context Budget section.

### Task Decomposition Guidelines

Right-size tasks before dispatch. With 1M context, agents can handle larger scope — prefer fewer, meatier tasks over many tiny ones:

| Dimension | Guideline |
|-----------|-----------|
| Files to read | 5-15 per agent |
| Files to modify | 1-5 per agent |
| Objectives | 1-2 per agent — clear deliverables |
| Output scope | One feature or focused concern |

**When to decompose** (still worth splitting):
- "Implement the authentication system" → 4 agents: token generation, middleware, login endpoint, session storage
- "Review all changed files" → 2 agents by concern: "review auth changes", "review API changes"

**Indivisible tasks** (single large file, atomic refactor): Accept them with generous `max_turns` and rely on the resume protocol.

**Where these rules apply:**
- All Task dispatches from the main conversation
- Amplifier commands that dispatch agents: `/create-plan`, `/subagent-dev`, `/parallel-agents`
- Any skill or workflow that creates Task calls with agent delegation

## Session Persistence (Memory Flush)

Auto-save progress at these triggers — don't wait for session end:

**After every commit:** Update session context with what was built, key decisions made, and what's next.

**After every plan decision:** When the user picks an approach (scope mode, architecture choice, tech stack), record it immediately. Mid-session crashes should not lose decisions.

**On exit signals:** When the user says "that's all", "done for today", "heading out", "closing", or any message implying departure (gratitude-only "thanks"/"ty", time references "tomorrow"/"later"/"next week", ambiguous closers with no follow-up question) — immediately:
1. Commit any uncommitted work (ask first)
2. Save key decisions and progress to memory
3. Note unfinished work and next steps

**Catch-all — context pressure:** When context usage is high and compression is imminent, persist all unsaved decisions before compression occurs. Don't wait for a signal that may never come.

## Batch Processing Patterns

For batch/pipeline systems: save after each item (not at end), continue on failure (don't stop the batch), track failure reasons, support selective retry, use fixed filenames that overwrite. Details in `/fix-bugs` and `/test-verified` command files.

## AutoContext Quality Gates

After significant work: `/evaluate implementation` (score < 80 → `/improve`). After brainstorm/planning: `/self-eval`. Weekly: `/self-improve` for instruction updates. Before recurring problems: `autocontext_skill_discover(query="...")` for learned strategies. Knowledge bridge: AutoContext → `.claude/skills/` → `/recall`.

## Decision Tracking

Decisions in `ai_working/decisions/`. Consult before proposing major changes. Create new records for architectural choices or reversals (format: `ai_working/decisions/README.md`). Decisions CAN change — with full understanding of why they were originally made.

## Configuration Management: Single Source of Truth

Every setting has ONE authoritative location. Hierarchy: `pyproject.toml` → `ruff.toml` → `.vscode/settings.json` → `config/routing-matrix.yaml`. Python deps via `uv` only. Duplication acceptable only for: performance-critical paths, pre-dependency build scripts, emergency fallbacks.

## Always-Loaded File Budgets

Always-loaded files: CLAUDE.md (<150 lines), AGENTS.md (<250 lines), routing-matrix.yaml (<120 lines). If exceeded, run `/self-improve prune` or move context-specific content to command files. Test: "Does every session need this?" If no → put it in the command file.

## Interactive Question Format

When asking the user to make a decision (in `/brainstorm`, `/create-plan`, `/design-interface`, or any interactive command):

1. **One issue per question** — never batch multiple decisions
2. **Lead with your recommendation**: "We recommend B: [one-line reason]"
3. **Present 2-3 lettered options**: A) ... B) ... C) ...
4. **Include "do nothing" when reasonable** — sometimes the best action is no action
5. **Keep options to one sentence** — the user should be able to pick in under 5 seconds
6. **Map reasoning to context** — connect your recommendation to project constraints or stated preferences

**Anti-pattern**: Open-ended "what do you think?" or "should we X?" without options.
**Anti-pattern**: Batching 5 decisions into one message and asking "thoughts?"

---

## URL Fetch Routing

When fetching content from URLs, pick the optimal tool by platform. Don't blindly use WebFetch — it fails on social platforms and authenticated services.

| Platform | First choice | Fallback |
|----------|-------------|----------|
| GitHub repos/PRs/issues | `gh` CLI via Bash | WebFetch |
| Gitea repos/PRs/issues | Gitea MCP tools (`mcp__gitea__*`) | WebFetch |
| Twitter/X (single post) | WebFetch | Playwright navigate |
| General articles/blogs | WebFetch | Playwright for JS-heavy SPAs |
| Authenticated services (Jira, Confluence, Google Docs) | Specialized MCP tool if available | Ask user to paste content |
| npm/PyPI packages | WebFetch on registry page | `context7` MCP for docs |
| GitHub raw files | WebFetch on raw.githubusercontent.com | `gh api` via Bash |
| **All other URLs** | WebFetch | Playwright navigate (for JS-heavy/paywalled) |

**Rules:**
- Never try >2 tools on the same URL — 2 failures → tell user what was tried, what failed, suggest they paste content
- Never use WebFetch as first choice for social platforms (always fails)
- For GitHub, prefer `gh` CLI — it handles auth and rate limits
- For Gitea, ALWAYS use MCP tools — never `gh` CLI (talks to GitHub, not Gitea)

**Amplifier repos live on Gitea, not GitHub.** When working with Amplifier, FuseCP, or any `admin/*` or `claude/*` repo, ALWAYS use Gitea MCP tools — never `gh` CLI. The GitHub rows above apply only to external/public GitHub repos.

---

## Response Authenticity Guidelines

**CRITICAL**: Professional, authentic communication. No sycophancy.

**NEVER**: "You're absolutely right!", "Brilliant idea!", "Excellent point!", "I completely agree!"
**INSTEAD**: Analyze merit, point out trade-offs, provide honest assessment, disagree constructively, focus on the code.

You're a professional tool, not a cheerleader. Users value honest, direct feedback over empty agreement.

## Zero-BS Principle: No Unnecessary Stubs or Placeholders

**CRITICAL**: Build working code. Every function must work or not exist. Every file must be complete or not created.

**NEVER write** `raise NotImplementedError`, `TODO` comments without code, `pass` as placeholder, mock/dummy functions, `return {} # stub`, or `...` as implementation — unless it's a legitimate pattern (ABC `@abstractmethod`, Click `@group()`, protocol stubs, empty `__init__.py`).

**When requirements are vague**: Ask for details, reduce scope, implement only what works.
**When facing external deps**: Use file-based storage, local processing, simplest working version.
**YAGNI**: Don't create unused parameters, don't build for hypothetical futures.

**The test**: "Does this code DO something useful right now?" If no — implement it fully or remove it.

## Verification-First Completion

**Never claim work is complete without citing specific verification evidence.** Every completion claim MUST include at least one of: test results with pass/fail counts, command output with exit codes, or specific file/line references showing the change works.

Phrases that express confidence without evidence are banned — including but not limited to: "should be fine", "probably passes", "I think it's fixed", "seems correct", "theoretically correct", "I fixed it, you try", "that should do it", "everything looks good". The test: does your claim contain verifiable evidence, or just an opinion?

## Build/Test/Lint Commands

- Install dependencies: `uv sync`
- Add new dependencies: `uv add package-name` (in the specific project directory)
- Add development dependencies: `uv add --dev package-name`
- Run all checks: `uv run ruff check . && uv run ruff format --check .`
- Run all tests: `uv run pytest`
- Run a single test: `uv run pytest tests/path/to/test_file.py::TestClass::test_function -v`
- Upgrade dependency lock: `uv lock --upgrade`

## Dependency Management

- **ALWAYS use `uv`** for Python dependency management in this project
- To add dependencies: `cd` to the specific project directory and run `uv add <package>`
- This ensures proper dependency resolution and updates both `pyproject.toml` and `uv.lock`
- Never manually edit `pyproject.toml` dependencies - always use `uv add`

## Red Flags

Metacognitive checklist for common reasoning traps. Full table: `/docs search red flags`.

