# Enforce Model Tiers in Amplifier Commands

> **For Claude:** REQUIRED: Use /subagent-dev (if subagents available) or /execute-plan to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add explicit `model` parameters to all Task dispatches across Amplifier commands, following the subagent-dev tier guide, so subagents use the correct model (haiku/sonnet/opus) instead of defaulting to Opus.

**Architecture:** Pure edit-only changes to 6 existing markdown files. No new files, no code changes. Each Task() pseudocode call gets a `model="X"` parameter based on the tier mapping in subagent-dev.md and AGENTS_CATALOG.md.

**Tech Stack:** Markdown editing only.

---

## Background

The subagent-dev command defines a model tier guide:

| Agent | Tier | Model |
|-------|------|-------|
| `modular-builder` (simple) | Fast | `haiku` |
| `modular-builder` (multi-file) | Balanced | `sonnet` |
| `bug-hunter` | Balanced | `sonnet` |
| `database-architect` | Balanced | `sonnet` |
| `test-coverage` (review) | Fast | `haiku` |
| `zen-architect` (review) | Balanced | `sonnet` |
| `security-guardian` | Deep | `opus` |
| `post-task-cleanup` | Fast | `haiku` |
| `agentic-search` (scouting) | Fast | `haiku` |
| `agentic-search` (deep investigation) | Balanced | `sonnet` |
| `integration-specialist` | Balanced | `sonnet` |
| `performance-optimizer` | Balanced | `sonnet` |
| `api-contract-designer` | Balanced | `sonnet` |
| `component-designer` | Balanced | `sonnet` |

**Current state:** 9 of 15 Task dispatches omit the `model` parameter, causing all subagents to inherit the parent model (Opus). This wastes cost on tasks that haiku or sonnet can handle.

---

## Task 1: Add model to brainstorm.md agentic-search dispatch

**Agent:** modular-builder

**Files:**
- Modify: `.claude/commands/brainstorm.md:59`

- [ ] **Step 1: Add model="haiku" to the agentic-search Task call**

The agentic-search dispatch at line 59 is for code exploration before designing — a scouting task. Per the tier guide, scouting uses haiku.

Change line 59 from:
```
Task(subagent_type="agentic-search", max_turns=12, description="Explore [topic] in codebase", prompt="
```
To:
```
Task(subagent_type="agentic-search", model="haiku", max_turns=12, description="Explore [topic] in codebase", prompt="
```

- [ ] **Step 2: Verify the edit**

Read `.claude/commands/brainstorm.md` lines 55-65 to confirm model parameter is present.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/brainstorm.md
git commit -m "fix: add model=haiku to brainstorm agentic-search dispatch"
```

---

## Task 2: Add model to create-plan.md agentic-search dispatch

**Agent:** modular-builder

**Files:**
- Modify: `.claude/commands/create-plan.md:20`

- [ ] **Step 1: Add model="haiku" to the agentic-search Task call**

The agentic-search dispatch at line 20 is for understanding architecture before planning — a scouting task. Per the tier guide, scouting uses haiku.

Change line 20 from:
```
   Task(subagent_type="agentic-search", max_turns=12, description="Understand [area] before planning", prompt="
```
To:
```
   Task(subagent_type="agentic-search", model="haiku", max_turns=12, description="Understand [area] before planning", prompt="
```

- [ ] **Step 2: Verify the edit**

Read `.claude/commands/create-plan.md` lines 18-25 to confirm model parameter is present.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/create-plan.md
git commit -m "fix: add model=haiku to create-plan agentic-search dispatch"
```

---

## Task 3: Add models to fix-bugs.md Task dispatches

**Agent:** modular-builder

**Files:**
- Modify: `.claude/commands/fix-bugs.md:152` (agentic-search)
- Modify: `.claude/commands/fix-bugs.md:272` (bug-hunter)

- [ ] **Step 1: Add model="sonnet" to the agentic-search Task call (line 152)**

The agentic-search in fix-bugs is a DEEP investigation task (3-phase methodology, max_turns=20, root cause analysis with synthesis). This is NOT simple scouting — it needs reasoning. Per the tier guide, deep investigation uses sonnet.

Change line 152 from:
```
Task(subagent_type="agentic-search", max_turns=20, description="Investigate bug #{id}: {title}", prompt="
```
To:
```
Task(subagent_type="agentic-search", model="sonnet", max_turns=20, description="Investigate bug #{id}: {title}", prompt="
```

- [ ] **Step 2: Add model="sonnet" to the bug-hunter Task call (line 272)**

Per the tier guide, `bug-hunter` → `sonnet` (needs reasoning about root causes).

Change line 272 from:
```
Task(subagent_type="bug-hunter", max_turns=20, description="Fix bug #{id}: {title}", prompt="
```
To:
```
Task(subagent_type="bug-hunter", model="sonnet", max_turns=20, description="Fix bug #{id}: {title}", prompt="
```

- [ ] **Step 3: Verify both edits**

Read `.claude/commands/fix-bugs.md` lines 150-155 and 270-275 to confirm both model parameters are present.

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/fix-bugs.md
git commit -m "fix: add model=sonnet to fix-bugs agentic-search and bug-hunter dispatches"
```

---

## Task 4: Add models to parallel-agents.md example dispatches

**Agent:** modular-builder

**Files:**
- Modify: `.claude/commands/parallel-agents.md:86-88`

- [ ] **Step 1: Add model parameters to all three example Task calls**

These are example dispatches showing the parallel pattern. They should model best practice by including explicit model assignments.

Change lines 86-88 from:
```
Task(subagent_type="bug-hunter", max_turns=12, description="Fix auth test failures", prompt="...")
Task(subagent_type="integration-specialist", max_turns=12, description="Fix payment API", prompt="...")
Task(subagent_type="performance-optimizer", max_turns=12, description="Fix search latency", prompt="...")
```
To:
```
Task(subagent_type="bug-hunter", model="sonnet", max_turns=12, description="Fix auth test failures", prompt="...")
Task(subagent_type="integration-specialist", model="sonnet", max_turns=12, description="Fix payment API", prompt="...")
Task(subagent_type="performance-optimizer", model="sonnet", max_turns=12, description="Fix search latency", prompt="...")
```

- [ ] **Step 2: Verify the edits**

Read `.claude/commands/parallel-agents.md` lines 84-90 to confirm all three model parameters are present.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/parallel-agents.md
git commit -m "fix: add model=sonnet to parallel-agents example dispatches"
```

---

## Task 5: Add models to subagent-dev.md template dispatches

**Agent:** modular-builder

**Files:**
- Modify: `.claude/commands/subagent-dev.md:42` (generic dispatch example)
- Modify: `.claude/commands/subagent-dev.md:49-51` (review agent templates)

- [ ] **Step 1: Add model to the generic dispatch example (line 42)**

The generic example should show best practice. Since the model depends on the agent type, add a placeholder comment.

Change line 42 from:
```
2. **Dispatch using Task tool with `subagent_type` set to the Agent: field value.** Example: if the plan says `Agent: modular-builder`, call `Task(subagent_type="modular-builder", max_turns=15, description="Implement Task N: ...", prompt="...")`
```
To:
```
2. **Dispatch using Task tool with `subagent_type` set to the Agent: field value.** Example: if the plan says `Agent: modular-builder`, call `Task(subagent_type="modular-builder", model="haiku", max_turns=15, description="Implement Task N: ...", prompt="...")` — set `model` per the Model Selection table below.
```

- [ ] **Step 2: Add models to review agent templates (lines 49-51)**

Change lines 49-51 from:
```
- Spec compliance review → `Task(subagent_type="test-coverage", ...)`
- Code quality review → `Task(subagent_type="zen-architect", ...)` in REVIEW mode
- Security-sensitive tasks → add `Task(subagent_type="security-guardian", ...)` as third reviewer
```
To:
```
- Spec compliance review → `Task(subagent_type="test-coverage", model="haiku", ...)`
- Code quality review → `Task(subagent_type="zen-architect", model="sonnet", ...)` in REVIEW mode
- Security-sensitive tasks → add `Task(subagent_type="security-guardian", model="opus", ...)` as third reviewer
```

- [ ] **Step 3: Verify the edits**

Read `.claude/commands/subagent-dev.md` lines 40-55 to confirm all model parameters are present.

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/subagent-dev.md
git commit -m "fix: add explicit model params to subagent-dev dispatch templates"
```

---

## Task 6: Expand Model Tier Mapping in AGENTS_CATALOG.md

**Agent:** modular-builder

**Files:**
- Modify: `.claude/AGENTS_CATALOG.md:78-89`

- [ ] **Step 1: Expand the Model Tier Mapping table to cover all commonly dispatched agents**

Currently the table only covers 7 agents. Add entries for `agentic-search`, `integration-specialist`, `performance-optimizer`, `api-contract-designer`, and `component-designer`.

Replace lines 78-89:
```markdown
## Model Tier Mapping

| Agent | Tier | Claude | Gemini |
|-------|------|--------|--------|
| `modular-builder` (simple) | Fast | `haiku` | Flash |
| `modular-builder` (multi-file) | Balanced | `sonnet` | Pro |
| `bug-hunter` | Balanced | `sonnet` | Pro |
| `database-architect` | Balanced | `sonnet` | Pro |
| `test-coverage` (review) | Fast | `haiku` | Flash |
| `zen-architect` (review) | Balanced | `sonnet` | Pro |
| `security-guardian` | Deep | `opus` | Pro |
| `post-task-cleanup` | Fast | `haiku` | Flash |
```

With:
```markdown
## Model Tier Mapping

| Agent | Tier | Claude | Gemini |
|-------|------|--------|--------|
| `agentic-search` (scouting) | Fast | `haiku` | Flash |
| `agentic-search` (deep investigation) | Balanced | `sonnet` | Pro |
| `modular-builder` (simple, 1-2 files) | Fast | `haiku` | Flash |
| `modular-builder` (multi-file) | Balanced | `sonnet` | Pro |
| `bug-hunter` | Balanced | `sonnet` | Pro |
| `database-architect` | Balanced | `sonnet` | Pro |
| `api-contract-designer` | Balanced | `sonnet` | Pro |
| `integration-specialist` | Balanced | `sonnet` | Pro |
| `performance-optimizer` | Balanced | `sonnet` | Pro |
| `component-designer` | Balanced | `sonnet` | Pro |
| `test-coverage` (review) | Fast | `haiku` | Flash |
| `zen-architect` (review) | Balanced | `sonnet` | Pro |
| `security-guardian` | Deep | `opus` | Pro |
| `post-task-cleanup` | Fast | `haiku` | Flash |
```

- [ ] **Step 2: Verify the expanded table**

Read `.claude/AGENTS_CATALOG.md` lines 78-95 to confirm the expanded table is correct.

- [ ] **Step 3: Commit**

```bash
git add .claude/AGENTS_CATALOG.md
git commit -m "docs: expand Model Tier Mapping to cover all commonly dispatched agents"
```

---

## Task 7: Final verification

**Agent:** post-task-cleanup

- [ ] **Step 1: Grep for all Task( calls without model parameter**

Search all `.claude/commands/*.md` files for `Task(` calls that still lack a `model=` parameter. Any remaining occurrences should be:
- Resume calls (don't need model — they inherit from original dispatch)
- The `ultrathink-task.md` reference (not a real dispatch)

```bash
grep -n 'Task(' .claude/commands/*.md | grep -v 'model=' | grep -v 'resume=' | grep -v 'ultrathink'
```

- [ ] **Step 2: Verify all probe models work**

Dispatch a quick haiku probe to confirm model routing still works after edits:
```
Task(subagent_type="general-purpose", model="haiku", max_turns=2, prompt="Report your model identity in one line.")
```

- [ ] **Step 3: Squash commits and create final commit**

```bash
git log --oneline -7
```

Review all commits are correct, then present summary to user.
