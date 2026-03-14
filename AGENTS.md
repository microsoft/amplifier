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

**Gitea operations**: Use Gitea MCP tools (`mcp__gitea__*`) for all Gitea operations — PRs, issues, labels, milestones, reviews. MCP tools support parallel calls and work natively in subagents. Fallback: `tea` CLI when MCP is unavailable. Quick ref: `/docs search git workflow`.

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

Turn budgets are **elastic** — each role defines a range `{min, default, max}` in `config/routing-matrix.yaml`. The orchestrator picks within the range based on task complexity and the current `/effort` setting.

| Role | Effort | Turns (min/default/max) | Examples |
|------|--------|------------------------|----------|
| scout | low | 8 / 12 / 20 | Haiku scouts, context gathering, file searches |
| research | medium | 10 / 15 / 25 | Codebase exploration, documentation lookup |
| review | medium | 10 / 15 / 25 | test-coverage, security-guardian, code review |
| architect | high | 15 / 20 / 35 | zen-architect, design analysis |
| implement | medium | 15 / 25 / 40 | modular-builder, file creation and editing |
| security | high | 12 / 15 / 25 | security-guardian (audits, vulnerability assessment) |
| fast | low | 5 / 10 / 15 | post-task-cleanup, copy editing |

**Effort resolution (three layers):**
1. **Session `/effort`** — user sets ceiling (low/medium/high/max)
2. **Role effort** — default from routing-matrix (above table)
3. **Task signals** — orchestrator adjusts based on file count, keywords, retry state

`resolved_effort = min(session_effort, max(role_effort, task_signals))`

**Effort → turns mapping:**
- `low` → use `min` turns
- `medium` → use `default` turns
- `high` → use `max` turns
- `max` → use `max` turns + auto-resume up to 3 cycles (effectively unlimited)

These values are tuned for **Opus 4.6 with 1M context**. With large context windows, prefer giving agents more room over decomposing into tiny tasks. If an agent consistently needs resume cycles, increase its budget. If it finishes well under budget, decrease it.

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

## Incremental Processing Pattern

When building batch processing systems:

- Save results after each item, not at intervals or completion
- Use fixed filenames that overwrite, not timestamps
- Enable interruption without losing processed items
- Support incremental updates without reprocessing existing ones

## Partial Failure Handling Pattern

When appropriate for long-running batch processes with multiple sub-processors:

- Continue on failure — don't stop the entire batch for individual processor failures
- Save partial results — better than nothing
- Track failure reasons — distinguish "legitimately empty" from "extraction failed"
- Support selective retry — re-run only failed processors, not entire items
- Report comprehensively — show success rates per processor and items needing attention

## Decision Tracking System

Decisions are documented in `ai_working/decisions/`. Consult before proposing major changes or questioning existing patterns. Create new records for architectural choices, approach selection, pattern adoption, or reversals. Format: see `ai_working/decisions/README.md`.

Decisions CAN change, but should change with full understanding of why they were originally made.

## Configuration Management: Single Source of Truth

Every configuration setting should have exactly ONE authoritative location. All other uses reference or derive from that single source.

**Hierarchy**: `pyproject.toml` (primary) → `ruff.toml` (ruff-specific) → `.vscode/settings.json` (IDE) → `Makefile` (commands).

**Key locations**: Python deps in `pyproject.toml` only (via uv). Code exclusions in `[tool.pyright]`. Formatting in `ruff.toml`.

**When duplication is acceptable**: Performance-critical paths, build scripts that must work before dependencies are installed, emergency fallbacks.

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

