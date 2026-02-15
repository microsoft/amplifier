# Superpowers to Amplifier Migration Design Specification

**Date:** 2026-02-15
**Status:** Design Phase
**Author:** Amplifier Team

## Executive Summary

Migrate all 14 Superpowers workflow skills into native Amplifier commands (`.claude/commands/`), enriching each with native Amplifier agent dispatch. Remove the superpowers plugin dependency entirely. Result: one unified command system where every workflow natively uses Amplifier's 30 specialized agents.

---

## Problem Statement

Three integration pain points with current Superpowers/Amplifier setup:

### 1. Fork Maintenance Burden
We maintain a fork of obra/superpowers, merging upstream changes causes conflicts every release. This creates ongoing maintenance overhead and risks diverging from upstream improvements.

### 2. Redundancy and User Confusion
- 14 superpowers skills + 13 amplifier commands = 27 total commands
- Unclear when to use which (e.g., `/create-plan` vs `superpowers:writing-plans`)
- Two overlapping systems for the same purpose
- Inconsistent invocation patterns

### 3. Incomplete Integration
Only 4 of 14 superpowers skills dispatch Amplifier agents; the remaining 10 are disconnected from our 30-agent system. This means:
- Most workflows don't leverage our specialized agents
- Agent expertise is underutilized
- Duplicate effort (skills duplicate what agents could do)

---

## Goal

Create a **unified, native command system** where:
- All 14 superpowers workflows are available as `/command-name` Amplifier commands
- Every command that benefits from agent dispatch references specific Amplifier agent names
- No external plugin dependencies
- No fork to maintain
- One clear, consistent user experience

---

## Architecture

### Migration Approach

Each superpowers skill becomes an Amplifier command in `.claude/commands/<name>.md`:

| Component | Transformation |
|-----------|----------------|
| **Methodology content** | Preserved verbatim (workflow steps, checklists, discipline) |
| **Agent dispatch** | Added natively using Amplifier AGENTS_CATALOG.md |
| **Cross-references** | Updated (`superpowers:skill-name` → `/command-name`) |
| **Plugin paths** | Removed (`${CLAUDE_PLUGIN_ROOT}` references eliminated) |
| **Memory system** | Replaced (recall.js/learn.js → episodic memory or removed) |
| **YAML frontmatter** | Adapted to Amplifier format |

### Key Design Principles

1. **No external agent mapping files** — Commands reference agents directly from AGENTS_CATALOG.md
2. **Preserve methodology integrity** — The workflow discipline stays intact
3. **Native integration** — All references point to Amplifier resources
4. **Self-contained** — No dependencies on external plugin infrastructure

---

## Migration Map

| Superpowers Skill | Lines | Target Command | Action |
|---|---|---|---|
| `brainstorming` | 168 | `/brainstorm.md` | NEW — full methodology + native agent dispatch |
| `writing-plans` | 227 | `/create-plan.md` | ENRICH existing 15-line stub with full methodology |
| `executing-plans` | 84 | `/execute-plan.md` | ENRICH existing 23-line stub with full methodology |
| `subagent-driven-development` | 347 | `/subagent-dev.md` | NEW — agent dispatch workflow |
| `dispatching-parallel-agents` | 173 | `/parallel-agents.md` | NEW — parallel specialist dispatch |
| `systematic-debugging` | 296 | `/debug.md` | NEW — root cause discipline |
| `test-driven-development` | 371 | `/tdd.md` | NEW — TDD methodology |
| `using-git-worktrees` | 218 | `/worktree.md` | NEW — worktree best practices |
| `finishing-a-development-branch` | 200 | `/finish-branch.md` | NEW — branch cleanup workflow |
| `requesting-code-review` | 105 | `/request-review.md` | NEW (consolidate with existing review commands) |
| `receiving-code-review` | 213 | `/receive-review.md` | NEW — review feedback handling |
| `verification-before-completion` | 139 | `/verify.md` | NEW — proof before claims |
| `writing-skills` | 655 | `/write-skill.md` | NEW — skill authoring TDD |
| `using-superpowers` | 101 | (none) | EMBED in CLAUDE.md — meta instructions become project config |

**Total:** 14 skills → 13 new commands + 1 embedded config

---

## Migration Phases

### Phase 1: Core Pipeline (Priority 1)
**Goal:** Enable the brainstorming → planning → execution chain

Commands:
- `/brainstorm.md` — Explores user intent, requirements, design
- `/create-plan.md` — Enrich with full planning methodology
- `/execute-plan.md` — Enrich with execution discipline
- `/subagent-dev.md` — Agent dispatch workflow
- `/parallel-agents.md` — Parallel specialist dispatch

**Success criteria:** User can go from idea → design → plan → execution using native commands

---

### Phase 2: Development Discipline (Priority 2)
**Goal:** Independent methodology skills for code quality

Commands:
- `/debug.md` — Systematic debugging (hypothesis-driven)
- `/tdd.md` — Test-driven development methodology
- `/verify.md` — Verification before completion

**Success criteria:** Developers can invoke discipline workflows without external dependencies

---

### Phase 3: Git & Review Workflow (Priority 3)
**Goal:** Complete the development lifecycle support

Commands:
- `/worktree.md` — Git worktree best practices
- `/finish-branch.md` — Branch cleanup workflow
- `/request-review.md` — Code review request process
- `/receive-review.md` — Review feedback handling

**Success criteria:** Full git workflow supported natively

---

### Phase 4: Meta & Cleanup (Priority 4)
**Goal:** Meta-level capabilities and dependency removal

Tasks:
- `/write-skill.md` — Skill authoring with TDD
- Embed `using-superpowers` content in CLAUDE.md
- Remove superpowers plugin from `.claude/settings.json`
- Update all cross-references (CLAUDE.md, AGENTS.md, etc.)
- Archive superpowers fork

**Success criteria:** Zero superpowers dependencies, all references updated

---

## Transformation Details

### What Changes in Each Command

For each migrated skill, apply these transformations:

#### 1. YAML Frontmatter Adaptation
**Remove superpowers-specific fields:**
- `semantic_tags`
- `recommended_model`

**Keep/adapt Amplifier fields:**
- `name` → command name
- `description` → usage description
- `category` (optional, for organization)
- `allowed-tools` (optional, for safety)

**Before (superpowers):**
```yaml
---
name: systematic-debugging
description: Use when encountering any bug
semantic_tags: [role:debugger]
recommended_model: pro
---
```

**After (Amplifier):**
```yaml
---
description: Systematic debugging with hypothesis-driven root cause analysis
category: development-discipline
allowed-tools: Bash, Read, Grep, Edit
---
```

#### 2. Methodology Preservation
**Keep intact:**
- Workflow steps
- Checklists
- Discipline guidelines
- Best practices
- Anti-patterns
- Examples

**Example:** The systematic-debugging "Diagnostic Protocol" section stays verbatim.

#### 3. Agent Dispatch Addition
**Where the skill says:**
> "Dispatch a subagent to analyze..."

**We add:**
> "Dispatch the `bug-hunter` agent to analyze..."

**Reference AGENTS_CATALOG.md for:**
- Agent names
- Dispatch keywords
- Review agent mapping

**Example agent references:**
```markdown
## Implementation
Dispatch the `modular-builder` agent with the specification.

## Review
After implementation, dispatch `test-coverage` agent for spec compliance review,
then `zen-architect` (REVIEW mode) for code quality review.
```

#### 4. Cross-Reference Updates
**Before:**
```markdown
Use `superpowers:writing-plans` to create the implementation plan.
```

**After:**
```markdown
Use `/create-plan` to create the implementation plan.
```

**Search patterns:**
- `superpowers:skill-name` → `/command-name`
- `${CLAUDE_PLUGIN_ROOT}/skills/...` → remove or adapt

#### 5. Plugin Path Removal
**Before:**
```markdown
See examples in ${CLAUDE_PLUGIN_ROOT}/skills/examples/
```

**After:**
```markdown
See examples in `.claude/commands/` or remove if no longer applicable.
```

#### 6. Memory System Replacement
**Before:**
```markdown
Use recall.js to retrieve past context.
```

**After:**
```markdown
Use episodic memory search (`mcp__plugin_episodic-memory_episodic-memory__search`)
to retrieve past context.
```

**Or remove if unused.**

---

## What We Don't Change

These components remain **untouched**:

| Component | Location | Reason |
|-----------|----------|--------|
| 30 Amplifier agents | `.claude/agents/` | Already optimized for Amplifier |
| AGENTS_CATALOG.md | `.claude/` | Agent reference stays intact |
| Hook scripts | `.claude/tools/` | Independent infrastructure |
| Unique commands | `.claude/commands/` | No overlap with superpowers |

**Unique commands preserved:**
- `designer.md` — UI/UX design (no superpowers equivalent)
- `ultrathink-task.md` — Deep thinking (Amplifier-specific)
- `modular-build.md` — Modular building (Amplifier pattern)
- `commit.md` — Git commit workflow
- `prime.md` — Session initialization
- `psmux.md` — Terminal multiplexer control
- `transcripts.md` — Transcript management
- `test-webapp-ui.md` — UI testing

---

## Existing Commands Resolution

### Review Commands Consolidation

| Command | Lines | Decision | Rationale |
|---|---|---|---|
| `/review-changes.md` | 23 | KEEP | Quick diff review, different scope |
| `/review-code-at-path.md` | 19 | KEEP | Targeted review, complementary |
| `/request-review.md` | — | ADD | Formal review request (from superpowers) |
| `/receive-review.md` | — | ADD | Review feedback handling (from superpowers) |

**No conflicts:** Existing review commands are thin and complementary to the more methodical formal review workflows.

---

## Infrastructure Changes

### 1. Remove Superpowers Plugin
**File:** `.claude/settings.json` (or equivalent)

**Action:** Unregister the superpowers marketplace plugin

**Before:**
```json
{
  "plugins": [
    "superpowers-marketplace"
  ]
}
```

**After:**
```json
{
  "plugins": []
}
```

### 2. Update CLAUDE.md
**File:** `C:\claude\amplifier\CLAUDE.md`

**Changes:**
- Remove references to superpowers skills
- Add guidance about Amplifier commands
- Embed `using-superpowers` meta instructions as project config

### 3. Update AGENTS.md
**File:** `C:\claude\amplifier\AGENTS.md`

**Changes:**
- Remove superpowers cross-references
- Update examples to use `/command-name` syntax

### 4. Verify Session-Start Hook
**File:** `.claude/tools/hook_session_start.py`

**Action:** Verify it doesn't reference superpowers (already independent)

---

## Agent Allocation

### Implementation Phase
**Agent:** `modular-builder`
**Responsibility:** Port each skill to Amplifier command format
**Task size:** 1 skill → 1 command per dispatch
**Dispatch pattern:** Sequential (one skill at a time per phase)

### Testing Phase
**Agent:** `test-coverage`
**Responsibility:** Verify each command loads and dispatches correctly
**Task size:** 1 command per dispatch
**Dispatch pattern:** After each implementation

### Code Review Phase
**Agent:** `zen-architect` (REVIEW mode)
**Responsibility:** Review migrated commands for quality, completeness, philosophy alignment
**Task size:** Phase-level review (5-6 commands per batch)
**Dispatch pattern:** After each phase completes

### Cleanup Phase
**Agent:** `post-task-cleanup`
**Responsibility:** Remove superpowers dependency, clean dead references
**Task size:** Full codebase scan
**Dispatch pattern:** After Phase 4 implementation

---

## Test Plan

### Per-Command Verification (After Each Migration)

Test each command individually:

```bash
# Invoke the command
/command-name

# Verify:
# 1. Command loads without errors
# 2. Help text displays correctly
# 3. Methodology content is complete (compare with original skill)
# 4. Agent references are valid (check against AGENTS_CATALOG.md)
# 5. Cross-references point to valid Amplifier commands
```

**Checklist:**
- [ ] Command loads without errors
- [ ] Methodology content matches original skill
- [ ] Agent names exist in AGENTS_CATALOG.md
- [ ] Cross-references use `/command-name` format
- [ ] No `superpowers:` references remain
- [ ] No `${CLAUDE_PLUGIN_ROOT}` references remain
- [ ] No recall.js/learn.js references (or replaced with episodic memory)

### End-to-End Workflow Test (After Phase 1)

Test the complete pipeline:

```bash
# 1. Brainstorm a feature
/brainstorm "Add user authentication"
# Expected: Produces design with Agent Allocation section

# 2. Create implementation plan
/create-plan
# Expected: Produces plan with Agent: fields for each task

# 3. Execute with subagent workflow
/subagent-dev
# Expected: Dispatches agents per plan (modular-builder, test-coverage, etc.)

# 4. Verify before completion
/verify
# Expected: Checks implementation against spec, tests pass, etc.
```

**Success criteria:** Full pipeline executes without superpowers dependencies

### Integration Test (After Each Phase)

For each phase, verify:
- All commands in the phase load correctly
- Commands can invoke each other (cross-references work)
- Agent dispatch succeeds (no missing agent errors)
- No superpowers references in command outputs

### Cleanup Verification (After Phase 4)

```bash
# 1. Check skill list
# Expected: No superpowers skills listed

# 2. Grep for superpowers references
cd /c/claude/amplifier
grep -r "superpowers:" .claude/ AGENTS.md CLAUDE.md
# Expected: No matches

# 3. Grep for plugin root references
grep -r "CLAUDE_PLUGIN_ROOT" .claude/
# Expected: No matches

# 4. Verify plugin not loaded
cat .claude/settings.json | grep superpowers
# Expected: No match
```

---

## Acceptance Criteria

### Functional Criteria
- [ ] All 14 superpowers workflows available as `/command-name` Amplifier commands
- [ ] Every command that dispatches agents references specific Amplifier agent names from AGENTS_CATALOG.md
- [ ] All cross-references use `/command-name` format (no `superpowers:` references)
- [ ] Commands load and execute without errors
- [ ] End-to-end workflow test passes (brainstorm → plan → execute → verify)

### Infrastructure Criteria
- [ ] Superpowers plugin removed from `.claude/settings.json`
- [ ] No `${CLAUDE_PLUGIN_ROOT}` references in any command
- [ ] No recall.js/learn.js references (or replaced with episodic memory)
- [ ] CLAUDE.md and AGENTS.md updated (no superpowers references)
- [ ] Session-start hook verified (no superpowers dependencies)

### Quality Criteria
- [ ] Methodology content preserved (workflow steps, checklists, examples)
- [ ] Agent dispatch added where beneficial
- [ ] Commands follow Amplifier formatting standards
- [ ] Documentation updated (CLAUDE.md reflects unified command system)

### Maintenance Criteria
- [ ] No superpowers fork to maintain
- [ ] No upstream merge conflicts
- [ ] One unified command system (27 commands → 24 commands)
- [ ] Clear user guidance (one invocation pattern: `/command-name`)

---

## Risk Assessment

### Low Risk
- **Command migration** — Straightforward markdown transformation
- **Agent reference validation** — AGENTS_CATALOG.md provides clear mapping
- **Testing** — Simple per-command verification

### Medium Risk
- **Cross-reference updates** — Must update all references consistently
- **Memory system replacement** — Episodic memory may not be 1:1 with recall.js

**Mitigation:** Grep entire codebase for references before declaring phase complete

### High Risk
- **None identified** — Migration is additive (old system works until new system is complete)

---

## Rollback Plan

If migration encounters critical issues:

1. **Keep superpowers plugin installed** — Old skills continue to work
2. **Remove new commands incrementally** — Delete `.claude/commands/<new-command>.md`
3. **Revert infrastructure changes** — Restore `.claude/settings.json`, CLAUDE.md, AGENTS.md
4. **No data loss** — Migration is file-based, reversible via git

**Safe migration:** Old and new systems can coexist during migration.

---

## Timeline Estimate

| Phase | Commands | Estimated Effort | Agent Cycles |
|-------|----------|------------------|--------------|
| Phase 1 | 5 commands | 8-10 hours | 10-12 agent dispatches |
| Phase 2 | 3 commands | 4-5 hours | 6-8 agent dispatches |
| Phase 3 | 4 commands | 5-6 hours | 8-10 agent dispatches |
| Phase 4 | 1 command + cleanup | 3-4 hours | 4-6 agent dispatches |
| **Total** | **13 commands + cleanup** | **20-25 hours** | **28-36 agent dispatches** |

**Assumptions:**
- 1-2 hours per command migration (implementation + testing)
- Phase reviews add 20% overhead
- Cleanup and verification add 15% overhead

---

## Success Metrics

### Quantitative
- **Command count:** 27 → 24 (11% reduction)
- **Dependencies:** 1 external plugin → 0
- **Maintenance burden:** Weekly merge conflicts → eliminated
- **Integration coverage:** 4/14 skills use agents → 13/13 commands use agents

### Qualitative
- **User clarity:** One command system, one invocation pattern
- **Development velocity:** No fork maintenance overhead
- **Agent utilization:** All workflows leverage specialized agents
- **Code ownership:** Full control over command implementation

---

## Post-Migration

### Documentation Updates
- [ ] Update README.md (if it references superpowers)
- [ ] Update getting-started guides
- [ ] Update command reference documentation
- [ ] Archive superpowers integration design docs

### User Communication
- [ ] Announce unified command system
- [ ] Provide migration guide (`superpowers:skill-name` → `/command-name` mapping)
- [ ] Update any training materials

### Continuous Improvement
- [ ] Monitor command usage patterns
- [ ] Collect user feedback on new commands
- [ ] Identify opportunities for further command consolidation
- [ ] Refine agent dispatch patterns based on usage

---

## Appendix A: Command Naming Map

| Superpowers Skill | Amplifier Command | Notes |
|---|---|---|
| `brainstorming` | `/brainstorm` | Shortened for convenience |
| `writing-plans` | `/create-plan` | Already exists, enrich |
| `executing-plans` | `/execute-plan` | Already exists, enrich |
| `subagent-driven-development` | `/subagent-dev` | Shortened, clear purpose |
| `dispatching-parallel-agents` | `/parallel-agents` | Clear, concise |
| `systematic-debugging` | `/debug` | Standard, expected name |
| `test-driven-development` | `/tdd` | Industry standard abbreviation |
| `using-git-worktrees` | `/worktree` | Git command alignment |
| `finishing-a-development-branch` | `/finish-branch` | Action-oriented |
| `requesting-code-review` | `/request-review` | Clear action |
| `receiving-code-review` | `/receive-review` | Clear action |
| `verification-before-completion` | `/verify` | Concise, clear |
| `writing-skills` | `/write-skill` | Action-oriented |
| `using-superpowers` | (embedded in CLAUDE.md) | Meta-level config |

---

## Appendix B: Agent Dispatch Examples

### Example 1: /debug Command

**Original superpowers content:**
> Dispatch a subagent to analyze the stack trace and reproduce the error.

**Amplified version:**
```markdown
## Diagnostic Phase

1. **Gather Evidence**
   - Collect error messages, stack traces, logs
   - Identify reproduction steps

2. **Analyze Root Cause**
   Dispatch the `bug-hunter` agent:
   - Task: Analyze stack trace and propose hypotheses
   - Input: Error details, relevant code files
   - Output: Ranked hypotheses with evidence

3. **Test Hypotheses**
   - Verify each hypothesis systematically
   - Dispatch `modular-builder` for fixes if needed
```

### Example 2: /create-plan Command

**Original superpowers content:**
> Create a plan that breaks down the work into implementation tasks.

**Amplified version:**
```markdown
## Plan Structure

Each task should specify:
- **Objective:** What to build
- **Agent:** Which Amplifier agent will implement it
- **Inputs:** Files, specs, dependencies
- **Outputs:** Expected deliverables
- **Review:** Which agent will verify it

Example task:
```
### Task 1: Implement User Authentication

**Agent:** `modular-builder`
**Objective:** Create JWT-based auth middleware
**Inputs:**
- specs/auth-requirements.md
- src/middleware/ (existing patterns)
**Outputs:**
- src/middleware/auth.ts
- tests/middleware/auth.test.ts
**Review:** `test-coverage` (spec compliance), then `zen-architect` (REVIEW mode)
```
```

---

## Appendix C: Superpowers Skills Line Count

Reference for migration sizing:

| Skill | Lines | Complexity |
|-------|-------|------------|
| `writing-skills` | 655 | High — comprehensive authoring guide |
| `test-driven-development` | 371 | High — full TDD methodology |
| `subagent-driven-development` | 347 | High — complex workflow |
| `systematic-debugging` | 296 | Medium — structured protocol |
| `writing-plans` | 227 | Medium — planning discipline |
| `using-git-worktrees` | 218 | Medium — git workflow |
| `receiving-code-review` | 213 | Medium — review handling |
| `finishing-a-development-branch` | 200 | Medium — cleanup workflow |
| `dispatching-parallel-agents` | 173 | Medium — parallel dispatch |
| `brainstorming` | 168 | Medium — exploratory workflow |
| `verification-before-completion` | 139 | Low — verification checklist |
| `requesting-code-review` | 105 | Low — review request |
| `using-superpowers` | 101 | Low — meta instructions |
| `executing-plans` | 84 | Low — execution discipline |

**Total:** 3,297 lines of methodology content to preserve

---

## Document History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-15 | 1.0 | Initial design specification |

---

## Review Checklist

- [ ] All 14 skills accounted for in migration map
- [ ] File paths are concrete and valid
- [ ] Agent references match AGENTS_CATALOG.md
- [ ] Phases are logically sequenced
- [ ] Test plan covers all validation scenarios
- [ ] Acceptance criteria are measurable
- [ ] Risk assessment is complete
- [ ] Rollback plan is feasible
- [ ] No ambiguous language or placeholders
