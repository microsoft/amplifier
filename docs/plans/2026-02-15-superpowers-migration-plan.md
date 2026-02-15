# Superpowers-to-Amplifier Migration Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev (once migrated) or dispatch Amplifier agents via Task tool to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate all 14 Superpowers workflow skills into native Amplifier commands with integrated agent dispatch, eliminating the superpowers plugin dependency.

**Architecture:** Each superpowers skill is read, transformed (frontmatter adapted, agent dispatch added, cross-references updated, plugin paths removed), and written as a `.claude/commands/<name>.md` file. Existing thin stubs are enriched with full methodology. Infrastructure references (CLAUDE.md, AGENTS.md) are updated last.

**Tech Stack:** Markdown command files, Claude Code plugin system, Amplifier agent ecosystem

---

## Cross-Reference Mapping

Use this mapping when replacing cross-references in all tasks:

| Old Reference | New Reference |
|---|---|
| `superpowers:brainstorming` | `/brainstorm` |
| `superpowers:writing-plans` | `/create-plan` |
| `superpowers:executing-plans` | `/execute-plan` |
| `superpowers:subagent-driven-development` | `/subagent-dev` |
| `superpowers:dispatching-parallel-agents` | `/parallel-agents` |
| `superpowers:systematic-debugging` | `/debug` |
| `superpowers:test-driven-development` | `/tdd` |
| `superpowers:using-git-worktrees` | `/worktree` |
| `superpowers:finishing-a-development-branch` | `/finish-branch` |
| `superpowers:requesting-code-review` | `/request-review` |
| `superpowers:receiving-code-review` | `/receive-review` |
| `superpowers:verification-before-completion` | `/verify` |
| `superpowers:writing-skills` | `/write-skill` |
| `superpowers:using-superpowers` | (removed — embedded in CLAUDE.md) |

---

## Chunk 1: Core Pipeline (Tasks 1-5)

This chunk migrates the essential brainstorming → planning → execution pipeline. These commands form the backbone of Amplifier's development workflow.

### Task 1: Migrate brainstorming → /brainstorm

**Agent:** modular-builder

**Files:**
- Source: `C:\Users\Administrator.ERGOLAB\.claude\plugins\cache\superpowers-marketplace\superpowers\4.3.0\skills\brainstorming\SKILL.md`
- Create: `.claude\commands\brainstorm.md`

- [ ] **Step 1: Read source skill**
Read the source file and understand its structure, sections, and methodology.

- [ ] **Step 2: Write the Amplifier command**
Create `.claude\commands\brainstorm.md` with these transformations:

**Frontmatter:**
```yaml
---
description: Explores user intent, requirements and design before implementation. Recommended starting point for most creative work.
category: planning-workflow
allowed-tools: Bash, Read, Grep, Task, Glob
---
```

**Content transformations:**
- Preserve all methodology content (workflow steps, checklists, examples, anti-patterns)
- Replace context scout dispatch with native Amplifier agent dispatch using `haiku` model
- Replace `${CLAUDE_PLUGIN_ROOT}` references (visual-companion.md, AMPLIFIER-AGENTS.md, MEMORY-WORKFLOW.md) with `.claude/` paths or remove if obsolete
- Replace recall.js/learn.js references with episodic memory (`mcp__plugin_episodic-memory_episodic-memory__search`)
- Update cross-references:
  - `superpowers:writing-plans` → `/create-plan`
  - `superpowers:using-git-worktrees` → `/worktree`
  - `superpowers:subagent-driven-development` → `/subagent-dev`
  - `superpowers:dispatching-parallel-agents` → `/parallel-agents`
  - `superpowers:finishing-a-development-branch` → `/finish-branch`
- Add native agent references from AGENTS_CATALOG.md:
  - Context scout: dispatch `general-purpose` agent with `haiku` model
  - Spec writing: dispatch `general-purpose` agent with `sonnet` model
  - References to: zen-architect, modular-builder, bug-hunter, test-coverage
- Remove `semantic_tags` and `recommended_model` from frontmatter
- Update "Invoke superpowers:X" instructions to "Use /command-name"

- [ ] **Step 3: Verify the command**
Run these checks:
```bash
# No superpowers references
grep -c "superpowers:" .claude/commands/brainstorm.md
# Expected: 0

# No plugin root references
grep -c "CLAUDE_PLUGIN_ROOT" .claude/commands/brainstorm.md
# Expected: 0

# No recall.js references
grep -c "recall.js" .claude/commands/brainstorm.md
# Expected: 0

# Agent references are valid (spot check)
grep "agent\|Agent:" .claude/commands/brainstorm.md
# Expected: references to known agents from AGENTS_CATALOG.md
```

- [ ] **Step 4: Commit**
```bash
git add .claude/commands/brainstorm.md
git commit -m "feat: migrate brainstorming to native /brainstorm command

Transforms superpowers brainstorming skill into Amplifier command with:
- Native agent dispatch for context scout and spec writing
- Episodic memory integration replacing recall.js
- Updated cross-references to native commands
- Preserved full methodology and workflow discipline

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

### Task 2: Enrich /create-plan with full methodology

**Agent:** modular-builder

**Files:**
- Source: `C:\Users\Administrator.ERGOLAB\.claude\plugins\cache\superpowers-marketplace\superpowers\4.3.0\skills\writing-plans\SKILL.md`
- Modify: `.claude\commands\create-plan.md`

- [ ] **Step 1: Read source skill**
Read the source file (227 lines) to extract the complete planning methodology.

- [ ] **Step 2: Replace stub content with full methodology**
Replace the existing 15-line stub in `.claude\commands\create-plan.md` with enriched content:

**Frontmatter:**
```yaml
---
description: Create comprehensive implementation plans with Amplifier agent allocation and TDD structure
category: planning-workflow
allowed-tools: Bash, Read, Grep, Task, Glob, Edit, Write
---
```

**Content to preserve from source:**
- Overview section (planning discipline)
- Scope Check section
- File Structure section
- Amplifier Agent Assignment section (with references to AGENTS_CATALOG.md)
- Bite-Sized Task Granularity section
- Plan Document Header template
- Context-Efficient Plan Generation section
- Task Structure template
- Review Tasks section
- Plan Review Loop section
- Execution Handoff section

**Content transformations:**
- Replace `${CLAUDE_PLUGIN_ROOT}/AMPLIFIER-AGENTS.md` with `.claude/AGENTS_CATALOG.md`
- Replace recall.js references with episodic memory
- Update cross-references:
  - `superpowers:subagent-driven-development` → `/subagent-dev`
  - `superpowers:executing-plans` → `/execute-plan`
  - `superpowers:brainstorming` → `/brainstorm`
- Add references to specific Amplifier agents:
  - modular-builder (implementation tasks)
  - test-coverage (review tasks)
  - bug-hunter (fix/debug tasks)
  - security-guardian (security tasks)
  - zen-architect (REVIEW mode for code quality)
  - post-task-cleanup (final hygiene)
- Remove subagent dispatch code using `${CLAUDE_PLUGIN_ROOT}` paths
- Update plan document header to use `/subagent-dev` or `/execute-plan`

- [ ] **Step 3: Verify the command**
```bash
# No superpowers references
grep -c "superpowers:" .claude/commands/create-plan.md
# Expected: 0

# No plugin root references
grep -c "CLAUDE_PLUGIN_ROOT" .claude/commands/create-plan.md
# Expected: 0

# Agent catalog reference is correct
grep "AGENTS_CATALOG.md" .claude/commands/create-plan.md
# Expected: at least one match to .claude/AGENTS_CATALOG.md

# Agent references present
grep -E "modular-builder|test-coverage|bug-hunter|zen-architect" .claude/commands/create-plan.md
# Expected: multiple matches
```

- [ ] **Step 4: Commit**
```bash
git add .claude/commands/create-plan.md
git commit -m "feat: enrich /create-plan with full planning methodology

Expands stub with complete content from superpowers writing-plans:
- Amplifier agent assignment per task
- TDD structure with bite-sized steps
- Context-efficient plan generation
- Plan review loop with quality gates
- Native cross-references to Amplifier commands

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

### Task 3: Enrich /execute-plan with full methodology

**Agent:** modular-builder

**Files:**
- Source: `C:\Users\Administrator.ERGOLAB\.claude\plugins\cache\superpowers-marketplace\superpowers\4.3.0\skills\executing-plans\SKILL.md`
- Modify: `.claude\commands\execute-plan.md`

- [ ] **Step 1: Read source skill**
Read the source file (84 lines) to extract the execution methodology.

- [ ] **Step 2: Replace stub content with full methodology**
Replace the existing 23-line stub in `.claude\commands\execute-plan.md` with enriched content:

**Frontmatter:**
```yaml
---
description: Execute implementation plans in batches with review checkpoints
category: planning-workflow
allowed-tools: Bash, Read, Grep, Edit, Write, Task, TaskCreate, TaskUpdate, TaskList
---
```

**Content to preserve from source:**
- Overview section
- The Process (5 steps)
- When to Stop and Ask for Help section
- When to Revisit Earlier Steps section
- Remember section
- Integration section

**Content transformations:**
- Update cross-references:
  - `superpowers:using-git-worktrees` → `/worktree`
  - `superpowers:writing-plans` → `/create-plan`
  - `superpowers:finishing-a-development-branch` → `/finish-branch`
- Add references to TaskCreate, TaskUpdate, TaskList tools for batch tracking
- Remove "Announce at start" directive (already in core instructions)
- Update integration section to reference native commands

- [ ] **Step 3: Verify the command**
```bash
# No superpowers references
grep -c "superpowers:" .claude/commands/execute-plan.md
# Expected: 0

# Cross-references updated
grep -E "/create-plan|/worktree|/finish-branch" .claude/commands/execute-plan.md
# Expected: multiple matches

# Task tool references
grep -E "TaskCreate|TaskUpdate|TaskList" .claude/commands/execute-plan.md
# Expected: multiple matches
```

- [ ] **Step 4: Commit**
```bash
git add .claude/commands/execute-plan.md
git commit -m "feat: enrich /execute-plan with full execution methodology

Expands stub with complete content from superpowers executing-plans:
- Batch execution with review checkpoints
- Blocker handling guidance
- Task tool integration for progress tracking
- Native cross-references to Amplifier commands

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

### Task 4: Migrate subagent-driven-development → /subagent-dev

**Agent:** modular-builder

**Files:**
- Source: `C:\Users\Administrator.ERGOLAB\.claude\plugins\cache\superpowers-marketplace\superpowers\4.3.0\skills\subagent-driven-development\SKILL.md`
- Create: `.claude\commands\subagent-dev.md`

- [ ] **Step 1: Read source skill**
Read the source file (347 lines) — largest of the core pipeline skills.

- [ ] **Step 2: Write the Amplifier command**
Create `.claude\commands\subagent-dev.md` with these transformations:

**Frontmatter:**
```yaml
---
description: Execute plans by dispatching specialized Amplifier agents per task with two-stage review
category: planning-workflow
allowed-tools: Bash, Read, Grep, Task, TaskCreate, TaskUpdate, TaskList
---
```

**Content transformations:**
- Preserve all methodology (When to Use flowchart, Amplifier Agent Dispatch, Review Levels, The Process flowchart, Dispatch Announcements, Model Selection, Handling Implementer Status, Example Workflow)
- Replace `${CLAUDE_PLUGIN_ROOT}/AMPLIFIER-AGENTS.md` with `.claude/AGENTS_CATALOG.md`
- Replace `${CLAUDE_PLUGIN_ROOT}/MODEL-PROVIDERS.md` with `.claude/agents/` (or note model mappings inline)
- Update cross-references:
  - `superpowers:writing-plans` → `/create-plan`
  - `superpowers:executing-plans` → `/execute-plan`
  - `superpowers:using-git-worktrees` → `/worktree`
  - `superpowers:finishing-a-development-branch` → `/finish-branch`
  - `superpowers:requesting-code-review` → `/request-review`
  - `superpowers:test-driven-development` → `/tdd`
- Native agent references are already present (modular-builder, test-coverage, zen-architect, security-guardian, post-task-cleanup, bug-hunter, database-architect, etc.)
- Remove `${CLAUDE_PLUGIN_ROOT}` paths to prompt templates (embed inline or reference .claude/agents/)
- Replace recall.js/memorize.js references with episodic memory or note-taking tools
- Remove `semantic_tags` and `recommended_model` from frontmatter

- [ ] **Step 3: Verify the command**
```bash
# No superpowers references
grep -c "superpowers:" .claude/commands/subagent-dev.md
# Expected: 0

# No plugin root references
grep -c "CLAUDE_PLUGIN_ROOT" .claude/commands/subagent-dev.md
# Expected: 0

# AGENTS_CATALOG.md referenced
grep "AGENTS_CATALOG.md" .claude/commands/subagent-dev.md
# Expected: at least one match

# Agent names present
grep -E "modular-builder|test-coverage|zen-architect|bug-hunter" .claude/commands/subagent-dev.md
# Expected: many matches
```

- [ ] **Step 4: Commit**
```bash
git add .claude/commands/subagent-dev.md
git commit -m "feat: migrate subagent-driven-development to /subagent-dev

Transforms superpowers subagent workflow into Amplifier command:
- Native agent dispatch per task with Agent: field
- Three-tier review levels (self/spec/full)
- Model selection guidance (haiku/sonnet/opus)
- Implementer status handling (DONE/BLOCKED/NEEDS_CONTEXT)
- Updated cross-references to native commands

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

### Task 5: Migrate dispatching-parallel-agents → /parallel-agents

**Agent:** modular-builder

**Files:**
- Source: `C:\Users\Administrator.ERGOLAB\.claude\plugins\cache\superpowers-marketplace\superpowers\4.3.0\skills\dispatching-parallel-agents\SKILL.md`
- Create: `.claude\commands\parallel-agents.md`

- [ ] **Step 1: Read source skill**
Read the source file (173 lines) to understand parallel dispatch patterns.

- [ ] **Step 2: Write the Amplifier command**
Create `.claude\commands\parallel-agents.md` with these transformations:

**Frontmatter:**
```yaml
---
description: Dispatch multiple Amplifier specialists in parallel for independent analysis or implementation tasks
category: planning-workflow
allowed-tools: Task, Read, Grep, Bash
---
```

**Content transformations:**
- Preserve all methodology (when to use parallel dispatch, coordination patterns, result synthesis)
- Update to reference AGENTS_CATALOG.md for agent selection
- Add specific Amplifier agents for parallel dispatch scenarios:
  - Multiple specialists for analysis (content-researcher, analysis-engine, concept-extractor)
  - Multiple reviewers (test-coverage, security-guardian, zen-architect)
  - Multiple builders for independent modules (modular-builder with different scopes)
- Update cross-references:
  - `superpowers:brainstorming` → `/brainstorm`
  - `superpowers:systematic-debugging` → `/debug`
  - `superpowers:subagent-driven-development` → `/subagent-dev`
- Remove `${CLAUDE_PLUGIN_ROOT}` references
- Remove `semantic_tags` and `recommended_model`

- [ ] **Step 3: Verify the command**
```bash
# No superpowers references
grep -c "superpowers:" .claude/commands/parallel-agents.md
# Expected: 0

# No plugin root references
grep -c "CLAUDE_PLUGIN_ROOT" .claude/commands/parallel-agents.md
# Expected: 0

# Agent references present
grep -E "content-researcher|analysis-engine|modular-builder" .claude/commands/parallel-agents.md
# Expected: multiple matches
```

- [ ] **Step 4: Commit**
```bash
git add .claude/commands/parallel-agents.md
git commit -m "feat: migrate dispatching-parallel-agents to /parallel-agents

Transforms superpowers parallel dispatch into Amplifier command:
- Parallel specialist dispatch for independent tasks
- Result synthesis patterns
- Amplifier agent references from AGENTS_CATALOG.md
- Updated cross-references to native commands

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

### Task 6: Review Chunk 1 (Core Pipeline)

**Agent:** zen-architect

**Mode:** REVIEW

**Scope:** Review Tasks 1-5 command files for:
- Methodology preservation (no loss of workflow discipline)
- Agent references valid (all agents exist in AGENTS_CATALOG.md)
- Cross-references correct (all use /command-name format)
- No superpowers references remain
- No plugin root paths remain
- Frontmatter follows Amplifier format
- Commands are loadable and well-structured

**Output:** Review findings with file:line references
**Action:** If issues found, assign modular-builder to fix, then re-review

---

## Chunk 2: Development Discipline (Tasks 7-9)

This chunk migrates independent methodology skills that enhance code quality: systematic debugging, test-driven development, and verification before completion.

### Task 7: Migrate systematic-debugging → /debug

**Agent:** modular-builder

**Files:**
- Source: `C:\Users\Administrator.ERGOLAB\.claude\plugins\cache\superpowers-marketplace\superpowers\4.3.0\skills\systematic-debugging\SKILL.md`
- Create: `.claude\commands\debug.md`

- [ ] **Step 1: Read source skill**
Read the source file (296 lines) — comprehensive debugging methodology.

- [ ] **Step 2: Write the Amplifier command**
Create `.claude\commands\debug.md` with these transformations:

**Frontmatter:**
```yaml
---
description: Systematic debugging with hypothesis-driven root cause analysis. Use before proposing fixes.
category: development-discipline
allowed-tools: Bash, Read, Grep, Edit, Task
---
```

**Content transformations:**
- Preserve all methodology (The Iron Law, Four Phases, Red Flags, Common Rationalizations, Quick Reference, Supporting Techniques)
- Add native Amplifier agent dispatch:
  - Phase 1: Dispatch bug-hunter for root cause investigation
  - Phase 4: Reference test-coverage for creating failing test case
- Update cross-references:
  - `superpowers:test-driven-development` → `/tdd`
  - `superpowers:verification-before-completion` → `/verify`
- Remove references to `${CLAUDE_PLUGIN_ROOT}` if present
- Remove `semantic_tags` and `recommended_model`
- Note: This skill has supporting technique references (root-cause-tracing.md, defense-in-depth.md, condition-based-waiting.md) — these may not exist in Amplifier, so either embed the concepts or remove the references

- [ ] **Step 3: Verify the command**
```bash
# No superpowers references
grep -c "superpowers:" .claude/commands/debug.md
# Expected: 0

# Agent references added
grep -E "bug-hunter|test-coverage" .claude/commands/debug.md
# Expected: multiple matches

# Cross-references updated
grep -E "/tdd|/verify" .claude/commands/debug.md
# Expected: multiple matches
```

- [ ] **Step 4: Commit**
```bash
git add .claude/commands/debug.md
git commit -m "feat: migrate systematic-debugging to native /debug command

Transforms superpowers debugging discipline into Amplifier command:
- Four-phase root cause protocol
- Native bug-hunter agent dispatch
- Hypothesis-driven methodology preserved
- Updated cross-references to /tdd and /verify

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

### Task 8: Migrate test-driven-development → /tdd

**Agent:** modular-builder

**Files:**
- Source: `C:\Users\Administrator.ERGOLAB\.claude\plugins\cache\superpowers-marketplace\superpowers\4.3.0\skills\test-driven-development\SKILL.md`
- Create: `.claude\commands\tdd.md`

- [ ] **Step 1: Read source skill**
Read the source file (371 lines) — largest discipline skill.

- [ ] **Step 2: Write the Amplifier command**
Create `.claude\commands\tdd.md` with these transformations:

**Frontmatter:**
```yaml
---
description: Test-driven development methodology with red-green-refactor cycle
category: development-discipline
allowed-tools: Bash, Read, Grep, Edit, Task
---
```

**Content transformations:**
- Preserve all methodology (Red-Green-Refactor cycle, test design, anti-patterns, when to skip TDD)
- Add native Amplifier agent dispatch:
  - test-coverage agent for test case design
  - modular-builder for implementation
- Update cross-references:
  - `superpowers:systematic-debugging` → `/debug`
  - `superpowers:verification-before-completion` → `/verify`
  - `superpowers:writing-plans` → `/create-plan` (if referenced)
- Remove `${CLAUDE_PLUGIN_ROOT}` references
- Remove `semantic_tags` and `recommended_model`

- [ ] **Step 3: Verify the command**
```bash
# No superpowers references
grep -c "superpowers:" .claude/commands/tdd.md
# Expected: 0

# Agent references added
grep -E "test-coverage|modular-builder" .claude/commands/tdd.md
# Expected: multiple matches

# Cross-references updated
grep -E "/debug|/verify" .claude/commands/tdd.md
# Expected: at least one match
```

- [ ] **Step 4: Commit**
```bash
git add .claude/commands/tdd.md
git commit -m "feat: migrate test-driven-development to native /tdd command

Transforms superpowers TDD methodology into Amplifier command:
- Red-green-refactor cycle discipline
- Native test-coverage and modular-builder dispatch
- Test design patterns and anti-patterns
- Updated cross-references to native commands

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

### Task 9: Migrate verification-before-completion → /verify

**Agent:** modular-builder

**Files:**
- Source: `C:\Users\Administrator.ERGOLAB\.claude\plugins\cache\superpowers-marketplace\superpowers\4.3.0\skills\verification-before-completion\SKILL.md`
- Create: `.claude\commands\verify.md`

- [ ] **Step 1: Read source skill**
Read the source file (139 lines) — shortest discipline skill.

- [ ] **Step 2: Write the Amplifier command**
Create `.claude\commands\verify.md` with these transformations:

**Frontmatter:**
```yaml
---
description: Verification before completion. Evidence before claims, always. Use before claiming work is complete.
category: development-discipline
allowed-tools: Bash, Read, Grep
---
```

**Content transformations:**
- Preserve all methodology (The Iron Law, The Gate Function, Common Failures, Red Flags, Rationalization Prevention, Key Patterns, Why This Matters, When To Apply, The Bottom Line)
- Add native Amplifier agent dispatch:
  - Reference test-coverage agent for verification steps
- No major cross-references to update (this skill is mostly self-contained)
- Remove `semantic_tags` and `recommended_model`

- [ ] **Step 3: Verify the command**
```bash
# No superpowers references
grep -c "superpowers:" .claude/commands/verify.md
# Expected: 0

# Agent reference (if added)
grep "test-coverage" .claude/commands/verify.md
# Expected: 0-1 matches (optional)

# Methodology preserved
grep -E "The Iron Law|The Gate Function|Evidence before claims" .claude/commands/verify.md
# Expected: multiple matches
```

- [ ] **Step 4: Commit**
```bash
git add .claude/commands/verify.md
git commit -m "feat: migrate verification-before-completion to native /verify command

Transforms superpowers verification discipline into Amplifier command:
- Evidence-before-claims gate function
- Common failure patterns and red flags
- Rationalization prevention guide
- Preserved complete methodology

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

### Task 10: Review Chunk 2 (Development Discipline)

**Agent:** zen-architect

**Mode:** REVIEW

**Scope:** Review Tasks 7-9 command files for:
- Methodology preservation (debugging, TDD, verification disciplines intact)
- Agent references valid (bug-hunter, test-coverage, modular-builder)
- No superpowers references remain
- Frontmatter follows Amplifier format
- Commands are loadable and well-structured

**Output:** Review findings with file:line references
**Action:** If issues found, assign modular-builder to fix, then re-review

---

## Chunk 3: Git & Review Workflow (Tasks 11-14)

This chunk migrates the git workflow and code review process skills that complete the development lifecycle support.

### Task 11: Migrate using-git-worktrees → /worktree

**Agent:** modular-builder

**Files:**
- Source: `C:\Users\Administrator.ERGOLAB\.claude\plugins\cache\superpowers-marketplace\superpowers\4.3.0\skills\using-git-worktrees\SKILL.md`
- Create: `.claude\commands\worktree.md`

- [ ] **Step 1: Read source skill**
Read the source file (218 lines) to extract worktree best practices.

- [ ] **Step 2: Write the Amplifier command**
Create `.claude\commands\worktree.md` with these transformations:

**Frontmatter:**
```yaml
---
description: Git worktree best practices for isolated development workspaces
category: version-control-git
allowed-tools: Bash, Read, Grep
---
```

**Content transformations:**
- Preserve all methodology (when to use worktrees, setup, cleanup, best practices)
- No agent dispatch needed (pure git workflow)
- Update cross-references:
  - `superpowers:brainstorming` → `/brainstorm` (if referenced)
  - `superpowers:writing-plans` → `/create-plan` (if referenced)
  - `superpowers:finishing-a-development-branch` → `/finish-branch` (if referenced)
- Remove `${CLAUDE_PLUGIN_ROOT}` references
- Remove `semantic_tags` and `recommended_model`

- [ ] **Step 3: Verify the command**
```bash
# No superpowers references
grep -c "superpowers:" .claude/commands/worktree.md
# Expected: 0

# Git worktree commands preserved
grep -E "git worktree add|git worktree list|git worktree remove" .claude/commands/worktree.md
# Expected: multiple matches
```

- [ ] **Step 4: Commit**
```bash
git add .claude/commands/worktree.md
git commit -m "feat: migrate using-git-worktrees to native /worktree command

Transforms superpowers worktree guide into Amplifier command:
- Git worktree setup and cleanup procedures
- Isolated workspace best practices
- Updated cross-references to native commands

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

### Task 12: Migrate finishing-a-development-branch → /finish-branch

**Agent:** modular-builder

**Files:**
- Source: `C:\Users\Administrator.ERGOLAB\.claude\plugins\cache\superpowers-marketplace\superpowers\4.3.0\skills\finishing-a-development-branch\SKILL.md`
- Create: `.claude\commands\finish-branch.md`

- [ ] **Step 1: Read source skill**
Read the source file (200 lines) to extract branch completion workflow.

- [ ] **Step 2: Write the Amplifier command**
Create `.claude\commands\finish-branch.md` with these transformations:

**Frontmatter:**
```yaml
---
description: Complete development branch with cleanup, verification, and merge/PR workflow
category: version-control-git
allowed-tools: Bash, Read, Grep, Task
---
```

**Content transformations:**
- Preserve all methodology (completion checklist, cleanup steps, merge vs PR decision)
- Add native Amplifier agent dispatch:
  - post-task-cleanup agent for final hygiene pass
  - test-coverage for pre-merge verification (if not already in methodology)
- Update cross-references:
  - `superpowers:verification-before-completion` → `/verify`
  - `superpowers:requesting-code-review` → `/request-review` (if referenced)
  - `superpowers:using-git-worktrees` → `/worktree` (if referenced)
- Remove `${CLAUDE_PLUGIN_ROOT}` references
- Remove `semantic_tags` and `recommended_model`

- [ ] **Step 3: Verify the command**
```bash
# No superpowers references
grep -c "superpowers:" .claude/commands/finish-branch.md
# Expected: 0

# Agent reference
grep "post-task-cleanup" .claude/commands/finish-branch.md
# Expected: at least one match

# Cross-references updated
grep -E "/verify|/request-review|/worktree" .claude/commands/finish-branch.md
# Expected: multiple matches
```

- [ ] **Step 4: Commit**
```bash
git add .claude/commands/finish-branch.md
git commit -m "feat: migrate finishing-a-development-branch to /finish-branch

Transforms superpowers branch completion into Amplifier command:
- Branch cleanup and verification workflow
- Native post-task-cleanup agent dispatch
- Merge vs PR decision guidance
- Updated cross-references to native commands

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

### Task 13: Migrate requesting-code-review → /request-review

**Agent:** modular-builder

**Files:**
- Source: `C:\Users\Administrator.ERGOLAB\.claude\plugins\cache\superpowers-marketplace\superpowers\4.3.0\skills\requesting-code-review\SKILL.md`
- Create: `.claude\commands\request-review.md`

**Note:** Existing `.claude\commands\review-changes.md` and `.claude\commands\review-code-at-path.md` are thin and complementary. This new command focuses on formal review request process.

- [ ] **Step 1: Read source skill**
Read the source file (105 lines) — shortest git workflow skill.

- [ ] **Step 2: Write the Amplifier command**
Create `.claude\commands\request-review.md` with these transformations:

**Frontmatter:**
```yaml
---
description: Formal code review request process with self-review checklist
category: version-control-git
allowed-tools: Bash, Read, Grep, Task
---
```

**Content transformations:**
- Preserve all methodology (self-review checklist, PR template, review request process)
- Add native Amplifier agent dispatch:
  - zen-architect (REVIEW mode) for self-review before requesting human review
- Update cross-references:
  - `superpowers:verification-before-completion` → `/verify` (if referenced)
  - `superpowers:finishing-a-development-branch` → `/finish-branch` (if referenced)
  - `superpowers:receiving-code-review` → `/receive-review`
- Remove `${CLAUDE_PLUGIN_ROOT}` references
- Remove `semantic_tags` and `recommended_model`

- [ ] **Step 3: Verify the command**
```bash
# No superpowers references
grep -c "superpowers:" .claude/commands/request-review.md
# Expected: 0

# Agent reference
grep "zen-architect" .claude/commands/request-review.md
# Expected: at least one match

# Cross-references updated
grep -E "/verify|/finish-branch|/receive-review" .claude/commands/request-review.md
# Expected: at least one match
```

- [ ] **Step 4: Commit**
```bash
git add .claude/commands/request-review.md
git commit -m "feat: migrate requesting-code-review to /request-review

Transforms superpowers review request into Amplifier command:
- Formal review request process
- Self-review checklist with zen-architect
- PR template guidance
- Updated cross-references to native commands

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

### Task 14: Migrate receiving-code-review → /receive-review

**Agent:** modular-builder

**Files:**
- Source: `C:\Users\Administrator.ERGOLAB\.claude\plugins\cache\superpowers-marketplace\superpowers\4.3.0\skills\receiving-code-review\SKILL.md`
- Create: `.claude\commands\receive-review.md`

- [ ] **Step 1: Read source skill**
Read the source file (213 lines) to extract review feedback handling methodology.

- [ ] **Step 2: Write the Amplifier command**
Create `.claude\commands\receive-review.md` with these transformations:

**Frontmatter:**
```yaml
---
description: Handle code review feedback with systematic approach to addressing comments
category: version-control-git
allowed-tools: Bash, Read, Grep, Edit, Task
---
```

**Content transformations:**
- Preserve all methodology (feedback categorization, response patterns, addressing comments systematically)
- Add native Amplifier agent dispatch:
  - modular-builder for implementing review feedback fixes
  - test-coverage for verifying fixes don't break tests
- Update cross-references:
  - `superpowers:requesting-code-review` → `/request-review` (if referenced)
  - `superpowers:verification-before-completion` → `/verify` (if referenced)
  - `superpowers:systematic-debugging` → `/debug` (if referenced)
- Remove `${CLAUDE_PLUGIN_ROOT}` references
- Remove `semantic_tags` and `recommended_model`

- [ ] **Step 3: Verify the command**
```bash
# No superpowers references
grep -c "superpowers:" .claude/commands/receive-review.md
# Expected: 0

# Agent references
grep -E "modular-builder|test-coverage" .claude/commands/receive-review.md
# Expected: multiple matches

# Cross-references updated
grep -E "/request-review|/verify|/debug" .claude/commands/receive-review.md
# Expected: at least one match
```

- [ ] **Step 4: Commit**
```bash
git add .claude/commands/receive-review.md
git commit -m "feat: migrate receiving-code-review to /receive-review

Transforms superpowers review feedback handling into Amplifier command:
- Systematic feedback categorization
- Response patterns and resolution workflow
- Native modular-builder and test-coverage dispatch
- Updated cross-references to native commands

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

### Task 15: Review Chunk 3 (Git & Review Workflow)

**Agent:** zen-architect

**Mode:** REVIEW

**Scope:** Review Tasks 11-14 command files for:
- Methodology preservation (worktree, branch completion, review workflows intact)
- Agent references valid (post-task-cleanup, zen-architect, modular-builder, test-coverage)
- No superpowers references remain
- Frontmatter follows Amplifier format
- Commands are loadable and well-structured

**Output:** Review findings with file:line references
**Action:** If issues found, assign modular-builder to fix, then re-review

---

## Chunk 4: Meta & Cleanup (Tasks 16-20)

This chunk migrates the meta-level skill authoring command and performs complete cleanup of superpowers dependencies from the codebase.

### Task 16: Migrate writing-skills → /write-skill

**Agent:** modular-builder

**Files:**
- Source: `C:\Users\Administrator.ERGOLAB\.claude\plugins\cache\superpowers-marketplace\superpowers\4.3.0\skills\writing-skills\SKILL.md`
- Create: `.claude\commands\write-skill.md`

- [ ] **Step 1: Read source skill**
Read the source file (655 lines) — largest skill in the collection.

- [ ] **Step 2: Write the Amplifier command**
Create `.claude\commands\write-skill.md` with these transformations:

**Frontmatter:**
```yaml
---
description: Skill authoring with TDD methodology for creating new Amplifier commands
category: meta
allowed-tools: Bash, Read, Grep, Edit, Write, Task
---
```

**Content transformations:**
- Preserve all methodology (skill design, TDD for skills, testing, examples, anti-patterns)
- Update to target `.claude/commands/<name>.md` instead of plugin skill format
- Update frontmatter format to Amplifier format (remove semantic_tags, recommended_model)
- Add native Amplifier agent dispatch:
  - modular-builder for skill implementation
  - test-coverage for skill testing
- Update cross-references:
  - `superpowers:test-driven-development` → `/tdd` (if referenced)
  - `superpowers:verification-before-completion` → `/verify` (if referenced)
  - `superpowers:using-superpowers` → embedded in CLAUDE.md (note this change)
- Replace `${CLAUDE_PLUGIN_ROOT}/skills/` paths with `.claude/commands/`
- Remove recall.js/learn.js references
- Remove `semantic_tags` and `recommended_model` from example frontmatter

- [ ] **Step 3: Verify the command**
```bash
# No superpowers references
grep -c "superpowers:" .claude/commands/write-skill.md
# Expected: 0

# No plugin root references
grep -c "CLAUDE_PLUGIN_ROOT" .claude/commands/write-skill.md
# Expected: 0

# Agent references added
grep -E "modular-builder|test-coverage" .claude/commands/write-skill.md
# Expected: multiple matches

# Amplifier command paths
grep ".claude/commands/" .claude/commands/write-skill.md
# Expected: multiple matches
```

- [ ] **Step 4: Commit**
```bash
git add .claude/commands/write-skill.md
git commit -m "feat: migrate writing-skills to native /write-skill command

Transforms superpowers skill authoring into Amplifier command:
- Complete TDD methodology for command authoring
- Targets .claude/commands/ format
- Native modular-builder and test-coverage dispatch
- Amplifier frontmatter format examples
- Updated cross-references to native commands

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

### Task 17: Update CLAUDE.md (embed using-superpowers content)

**Agent:** modular-builder

**Files:**
- Source: `C:\Users\Administrator.ERGOLAB\.claude\plugins\cache\superpowers-marketplace\superpowers\4.3.0\skills\using-superpowers\SKILL.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Read source skill**
Read the using-superpowers skill (101 lines) to extract meta-level instructions.

- [ ] **Step 2: Identify content to embed**
Determine which sections from using-superpowers should become project-level guidance in CLAUDE.md. Likely candidates:
- Skill invocation patterns → become command invocation patterns
- When to use which skill → when to use which command
- Workflow guidance → workflow guidance with native commands

- [ ] **Step 3: Update CLAUDE.md**
Modify CLAUDE.md to:
- Remove any existing superpowers skill references
- Add section on Amplifier commands (if not already present)
- Embed relevant meta-instructions from using-superpowers
- Update example workflows to use `/command-name` syntax
- Ensure all cross-references use native command names

- [ ] **Step 4: Verify changes**
```bash
# No superpowers skill references remain
grep -c "superpowers:" CLAUDE.md
# Expected: 0

# Native command references present
grep -E "/brainstorm|/create-plan|/execute-plan|/subagent-dev" CLAUDE.md
# Expected: multiple matches

# Git diff review
git diff CLAUDE.md
# Review changes manually
```

- [ ] **Step 5: Commit**
```bash
git add CLAUDE.md
git commit -m "docs: embed using-superpowers meta content in CLAUDE.md

Updates CLAUDE.md to:
- Remove superpowers skill references
- Add Amplifier command invocation guidance
- Embed workflow patterns from using-superpowers
- Reference native /command-name format throughout

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

### Task 18: Update AGENTS.md (remove superpowers cross-references)

**Agent:** modular-builder

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Scan AGENTS.md for superpowers references**
```bash
grep -n "superpowers:" AGENTS.md
# Note all line numbers with references
```

- [ ] **Step 2: Update cross-references**
Replace all `superpowers:skill-name` references with `/command-name` equivalents using the cross-reference mapping from this plan.

- [ ] **Step 3: Verify changes**
```bash
# No superpowers references remain
grep -c "superpowers:" AGENTS.md
# Expected: 0

# Native command references present
grep -E "/brainstorm|/create-plan|/debug|/tdd|/verify" AGENTS.md
# Expected: multiple matches (wherever examples are given)

# Git diff review
git diff AGENTS.md
# Review changes manually
```

- [ ] **Step 4: Commit**
```bash
git add AGENTS.md
git commit -m "docs: update AGENTS.md to reference native commands

Replaces all superpowers:skill-name cross-references with native
/command-name format. Updates examples to use Amplifier commands.

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

### Task 19: Remove superpowers plugin registration

**Agent:** modular-builder

**Files:**
- Check: `.claude/settings.json` (or equivalent configuration file)
- Check: `C:\Users\Administrator.ERGOLAB\.claude\` global config (if applicable)

- [ ] **Step 1: Locate plugin configuration**
```bash
# Find where superpowers is registered
grep -r "superpowers" .claude/*.json
grep -r "superpowers-marketplace" .claude/*.json
cat .claude/settings.json
```

- [ ] **Step 2: Remove plugin registration**
If superpowers is registered in `.claude/settings.json` or similar:
- Remove the plugin entry from the `plugins` array
- Save the file

If no project-level registration, check global config at `C:\Users\Administrator.ERGOLAB\.claude\`

- [ ] **Step 3: Verify removal**
```bash
# No superpowers in config
grep -c "superpowers" .claude/settings.json
# Expected: 0

# Git diff review
git diff .claude/settings.json
# Review changes manually
```

- [ ] **Step 4: Commit (if changes made)**
```bash
git add .claude/settings.json
git commit -m "chore: remove superpowers plugin registration

Removes superpowers-marketplace plugin from project config.
All workflows now use native Amplifier commands.

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

**Note:** If superpowers is registered globally (not in this repo), inform the user that they need to manually remove it from their global Claude Code config.

---

### Task 20: Final verification (grep entire codebase for banned patterns)

**Agent:** modular-builder

**Files:**
- Scope: entire repository

- [ ] **Step 1: Run comprehensive verification**
```bash
cd /c/claude/amplifier

# Check for superpowers references
echo "=== Checking for superpowers: references ==="
grep -r "superpowers:" .claude/ AGENTS.md CLAUDE.md docs/ 2>/dev/null | wc -l
# Expected: 0

# Check for plugin root references
echo "=== Checking for CLAUDE_PLUGIN_ROOT references ==="
grep -r "CLAUDE_PLUGIN_ROOT" .claude/ AGENTS.md CLAUDE.md docs/ 2>/dev/null | wc -l
# Expected: 0

# Check for recall.js references
echo "=== Checking for recall.js references ==="
grep -r "recall.js" .claude/ AGENTS.md CLAUDE.md docs/ 2>/dev/null | wc -l
# Expected: 0

# Check for learn.js references
echo "=== Checking for learn.js references ==="
grep -r "learn.js" .claude/ AGENTS.md CLAUDE.md docs/ 2>/dev/null | wc -l
# Expected: 0

# Verify all new commands exist
echo "=== Verifying new commands exist ==="
ls -1 .claude/commands/brainstorm.md
ls -1 .claude/commands/create-plan.md
ls -1 .claude/commands/execute-plan.md
ls -1 .claude/commands/subagent-dev.md
ls -1 .claude/commands/parallel-agents.md
ls -1 .claude/commands/debug.md
ls -1 .claude/commands/tdd.md
ls -1 .claude/commands/verify.md
ls -1 .claude/commands/worktree.md
ls -1 .claude/commands/finish-branch.md
ls -1 .claude/commands/request-review.md
ls -1 .claude/commands/receive-review.md
ls -1 .claude/commands/write-skill.md
# Expected: all files exist

# Check command frontmatter format
echo "=== Checking command frontmatter ==="
for cmd in brainstorm create-plan execute-plan subagent-dev parallel-agents debug tdd verify worktree finish-branch request-review receive-review write-skill; do
    echo "Checking $cmd..."
    grep -E "semantic_tags|recommended_model" .claude/commands/${cmd}.md && echo "WARNING: Found old frontmatter in $cmd" || echo "  OK"
done
```

- [ ] **Step 2: Document verification results**
Create a summary of verification results:
- Total superpowers references: 0
- Total plugin root references: 0
- Total recall.js/learn.js references: 0
- All 13 commands created: yes
- No old frontmatter fields: yes

- [ ] **Step 3: Report to user**
Present verification summary and status:
```
Migration verification complete:

✅ 13 new Amplifier commands created
✅ 2 existing commands enriched (create-plan, execute-plan)
✅ 0 superpowers: references remain
✅ 0 CLAUDE_PLUGIN_ROOT references remain
✅ 0 recall.js/learn.js references remain
✅ CLAUDE.md updated with native command guidance
✅ AGENTS.md cross-references updated
✅ Plugin registration removed (or noted if global)

Migration is complete. All superpowers workflows are now native Amplifier commands.
```

**No commit needed** — this is verification only.

---

### Task 21: Review Chunk 4 (Meta & Cleanup)

**Agent:** zen-architect

**Mode:** REVIEW

**Scope:** Review Tasks 16-20 for:
- /write-skill command complete and functional
- CLAUDE.md properly updated (no superpowers references)
- AGENTS.md cross-references correct
- Plugin registration removed
- Final verification passed (all checks = 0/yes)
- Migration is complete and clean

**Output:** Review findings with file:line references
**Action:** If issues found, assign modular-builder to fix, then re-verify

---

## Migration Complete

After all chunks pass review:

1. **Announce completion**
2. **Provide user with migration summary:**
   - 13 new commands created
   - 2 existing commands enriched
   - 1 skill embedded in CLAUDE.md
   - 0 superpowers dependencies
   - One unified command system

3. **Next steps for user:**
   - Test commands by invoking them (e.g., `/brainstorm`, `/create-plan`)
   - Remove superpowers fork from maintenance rotation (archive repo)
   - Update any user documentation or training materials
   - Communicate unified command system to team

4. **Archive note:**
   - Original superpowers fork: maintain for historical reference but no longer actively synced
   - Migration design spec: `docs/plans/2026-02-15-superpowers-migration-design.md`
   - Migration implementation plan: this file
