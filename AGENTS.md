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

## Git Commit Message Guidelines

When creating git commit messages, always insert the following at the end of your commit message:

```
🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>
```

---

## PR-First Policy (CRITICAL)

**All completed work MUST go through a Pull Request. Never commit directly to main/master.**

### Rules

1. **Start on a feature branch** — Before any implementation work, create or verify you're on a feature branch (`feature/<name>`, `fix/<name>`, etc.). Never start work on main.
2. **End with a PR** — When work is complete, push the branch and create a PR via `gh pr create`. This is the default, not an option to choose.
3. **Never push to main** — Direct pushes to main are prohibited. If you find yourself on main with uncommitted work, create a branch first.
4. **Never merge without user confirmation** — Present the PR URL and wait for the user to approve the merge.

### Enforcement Points

- `/subagent-dev` has a **Branch Gate** that blocks execution on main
- `/finish-branch` defaults to creating a PR (no menu of options)
- `/brainstorm` → `/create-plan` → `/worktree` flow ensures a feature branch exists before implementation

### Recovery (if work accidentally lands on main)

```bash
# Create feature branch at current HEAD
git branch feature/<name>
# Reset main to before your changes
git reset --hard <pre-work-commit>
# Push the feature branch
git push -u origin feature/<name>
# Create PR
gh pr create --base main --head feature/<name>
```

This recovery works but is error-prone. Prevention (starting on a feature branch) is always preferred.

---

## Git Workflow — Gitea-First (Two-Stage)

**PRIMARY remote**: Gitea at https://gitea.ergonet.pl:3001/ (HTTPS, port 3001)
**BACKUP remote**: GitHub at https://github.com/psklarkins/ (push mirror, auto-syncs on commit)

### Remote Layout (all locally cloned repos)
- `origin` → Gitea (primary, all day-to-day pushes go here)
- `github` → GitHub (backup, never push manually — Gitea mirrors automatically)

### Daily Workflow
1. Work and commit locally as usual
2. Push to `origin` (Gitea): `git push origin feature/my-feature`
3. Open PR on Gitea: https://gitea.ergonet.pl:3001/admin/{repo}/pulls
4. Merge PR on Gitea — push mirror triggers GitHub backup automatically
5. Never push directly to `main`/`master`/`develop` — branch protection enforced

### Branch Protection Rules (all 19 repos)
- Direct push to default branch is BLOCKED
- PR is required to merge
- 0 approvals required (solo dev)
- Status checks: disabled (no CI configured on Gitea yet)

### GitHub Actions
- GitHub Actions runner at C:\actions-runner\ still runs CI on GitHub
- When Gitea push mirror syncs, GitHub Actions fires on the mirrored commits
- This provides CI coverage without needing Gitea Actions

---

## Sub-Agent Optimization Strategy

Always check `.claude/AGENTS_CATALOG.md` before starting. Proactively delegate to specialized agents. Propose new agents when a task lacks a specialist — agent creation is cheap and pays off immediately.

## Subagent Resilience Protocol

Subagents launched via the Task tool have their own context windows that can fill up during execution. When this happens, agents either stop abruptly with partial results or shift into "summary mode" instead of completing actual work. This protocol prevents both failure modes.

### Turn Budgets

Every Task dispatch must include a `max_turns` parameter. Use these starting values:

| Agent Role | max_turns | Examples |
|------------|-----------|----------|
| Quick tasks | 5-8 | Haiku scouts, context gathering, file searches |
| Research / exploration | 8-10 | Codebase exploration, documentation lookup |
| Review | 10-12 | test-coverage, security-guardian, code review |
| Analysis | 12-15 | zen-architect, bug-hunter, design analysis |
| Implementation | 15-20 | modular-builder, file creation and editing |
| Deep diagnostics | 20-25 | vmware-infrastructure (log correlation, KB lookup, command generation) |

These values are tuned through observation. If an agent consistently needs resume cycles, increase its budget. If it finishes well under budget, decrease it.

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

Right-size tasks before dispatch to prevent context exhaustion upstream:

| Dimension | Guideline |
|-----------|-----------|
| Files to read | 3-5 per agent |
| Files to modify | 1-3 per agent |
| Objectives | 1 per agent — single clear deliverable |
| Output scope | One component, module, or focused concern |

**Decompose large tasks:**
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

- Install dependencies: `make install` (uses uv)
- Add new dependencies: `uv add package-name` (in the specific project directory)
- Add development dependencies: `uv add --dev package-name`
- Run all checks: `make check` (runs lint, format, type check)
- Run all tests: `make test` or `make pytest`
- Run a single test: `uv run pytest tests/path/to/test_file.py::TestClass::test_function -v`
- Upgrade dependency lock: `make lock-upgrade`

## Dependency Management

- **ALWAYS use `uv`** for Python dependency management in this project
- To add dependencies: `cd` to the specific project directory and run `uv add <package>`
- This ensures proper dependency resolution and updates both `pyproject.toml` and `uv.lock`
- Never manually edit `pyproject.toml` dependencies - always use `uv add`

## Red Flags

If you catch yourself thinking any of the following, stop and apply the reality check before proceeding.

| If you're thinking... | Reality check |
|-----------------------|---------------|
| "This is simple, I'll just implement it directly" | Run /brainstorm first. Simplicity is confirmed after analysis, not assumed before it. |
| "I already know the codebase well enough" | Dispatch agentic-search anyway. Memory of past sessions is lossy. |
| "I'll write tests after the implementation" | /tdd exists for a reason. Tests first is not optional for non-trivial features. |
| "I'll skip the worktree, it's a small change" | Branch first always. Main is protected; there is no "small enough to skip". |
| "I can review my own code" | Two-stage review catches category errors that self-review misses. |
| "The user seems in a hurry, I'll skip brainstorming" | Rushing causes design mistakes that cost 10x the time saved. |
| "This refactor is obvious, no plan needed" | /create-plan takes 2 minutes. The blast radius of "obvious" refactors is routinely underestimated. |
| "I'll just fix this one file" | Check blast radius with grep first. Changes propagate in ways that are not always visible from one file. |
| "I tested it mentally, it should work" | /verify requires evidence, not claims. Mental testing has a well-documented failure rate. |
| "I'll clean up later" | Run /post-task-cleanup now. "Later" accumulates and becomes never. |

