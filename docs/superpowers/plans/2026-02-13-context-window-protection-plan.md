# Context Window Protection Implementation Plan

> **For Claude:** REQUIRED: Use superpowers:subagent-driven-development to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce pre-implementation context consumption from 35-52% to 13-20% of the 200k token window, and add guardrails to prevent agent context blowout.

**Architecture:** Three independent priority tiers across two repos (amplifier + superpowers). P1 reduces fixed system prompt overhead. P2 delegates in-context work to subagents. P3 adds context budget guardrails to agent definitions. All tiers are independent and can execute in parallel.

**Tech Stack:** Markdown files only — no code changes. Agent definitions (.md), skill files (.md), project config (.md).

**Spec:** `docs/superpowers/specs/2026-02-13-context-window-protection-design.md`

**Note on subagent_type:** Per commit `449100e`, the established pattern is `subagent_type: "general-purpose"` with role instructions in the prompt (not specialized agent types like `zen-architect` or `contract-spec-author`). This plan follows that pattern. The spec's subagent_type references are illustrative of the role, not the literal parameter value.

**Task independence:** Tasks 1-3 (amplifier repo P1), Tasks 4-7 (superpowers repo P2), and Tasks 8-10 (amplifier repo P3) are independent tiers. Tasks within each tier are sequential.

---

## Chunk 0: Prerequisites

### Task 0: Pull superpowers origin/main

**Agent:** modular-builder

**Files:** None (git operation)

- [ ] **Step 1: Pull latest superpowers**

```bash
cd /c/claude/superpowers
git pull origin main
```

Expected: Fast-forward to include `449100e` (subagent reliability) and `bd65f4e` (skill indexing).

- [ ] **Step 2: Verify**

```bash
git log --oneline -3
```

Expected: `449100e` appears in the log.

---

## Chunk 1: Priority 1 — Reduce Fixed Overhead (amplifier repo)

### Task 1: Remove design @imports from CLAUDE.md

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\amplifier\CLAUDE.md:9-18`

- [ ] **Step 1: Edit the @import section**

In `CLAUDE.md`, replace lines 9-18:

```markdown
# import the following files (using the `@` syntax):

- @AGENTS.md
- @DISCOVERIES.md
- @ai_context/IMPLEMENTATION_PHILOSOPHY.md
- @ai_context/MODULAR_DESIGN_PHILOSOPHY.md
- @ai_context/DESIGN-PHILOSOPHY.md
- @ai_context/DESIGN-PRINCIPLES.md
- @ai_context/design/DESIGN-FRAMEWORK.md
- @ai_context/design/DESIGN-VISION.md
```

With:

```markdown
# import the following files (using the `@` syntax):

- @AGENTS.md
- @DISCOVERIES.md
- @ai_context/IMPLEMENTATION_PHILOSOPHY.md
- @ai_context/MODULAR_DESIGN_PHILOSOPHY.md

# Design philosophy files — NOT always-loaded. Design agents read these on demand:
# - ai_context/DESIGN-PHILOSOPHY.md
# - ai_context/DESIGN-PRINCIPLES.md
# - ai_context/design/DESIGN-FRAMEWORK.md
# - ai_context/design/DESIGN-VISION.md
```

- [ ] **Step 2: Verify the change**

Run: `grep -n "@ai_context/DESIGN" C:\claude\amplifier\CLAUDE.md`
Expected: Only comment lines (starting with `#`), no active `- @` imports for design files.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "perf: remove design philosophy @imports from always-loaded context

Design files (DESIGN-PHILOSOPHY, DESIGN-PRINCIPLES, DESIGN-FRAMEWORK,
DESIGN-VISION) are now loaded on demand by design agents only.
Saves ~14,000 tokens per session for non-design tasks."
```

---

### Task 2: Deduplicate AGENTS.md

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\amplifier\AGENTS.md:418-757`

- [ ] **Step 1: Read current duplicated sections**

Read `AGENTS.md` lines 418-757 to confirm the `## Implementation Philosophy` section (line 418) and `## Modular Design Philosophy` section (line 716) exist and duplicate content from `ai_context/IMPLEMENTATION_PHILOSOPHY.md` and `ai_context/MODULAR_DESIGN_PHILOSOPHY.md`.

- [ ] **Step 2: Replace with reference**

Delete everything from line 418 (`## Implementation Philosophy`) through end of file (line 757). Replace with:

```markdown
## Implementation Philosophy

See `@ai_context/IMPLEMENTATION_PHILOSOPHY.md` for the full implementation philosophy (already loaded via CLAUDE.md @imports).

## Modular Design Philosophy

See `@ai_context/MODULAR_DESIGN_PHILOSOPHY.md` for the modular design philosophy (already loaded via CLAUDE.md @imports).
```

- [ ] **Step 3: Verify the file is valid**

Run: `wc -l AGENTS.md`
Expected: ~425 lines (down from 757). Verify no broken markdown by checking section headings: `grep "^## " AGENTS.md`

- [ ] **Step 4: Commit**

```bash
git add AGENTS.md
git commit -m "perf: deduplicate AGENTS.md by referencing @imported philosophy files

Implementation Philosophy and Modular Design Philosophy sections were
duplicated from ai_context/ files already loaded via CLAUDE.md @imports.
Replaced with references. Saves ~2,000 tokens per session."
```

---

### Task 3: Archive stale DISCOVERIES.md entries

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\amplifier\DISCOVERIES.md`
- Create: `C:\claude\amplifier\DISCOVERIES-archive.md`

- [ ] **Step 1: Create archive file**

Create `DISCOVERIES-archive.md` with header:

```markdown
# DISCOVERIES Archive

Archived entries from DISCOVERIES.md. These solved past issues that are no longer actively relevant.
See DISCOVERIES.md for current patterns.
```

Then copy these 3 entries (with full content) from DISCOVERIES.md into the archive:
- "DevContainer Setup: Using Official Features Instead of Custom Scripts (2025-10-22)" (lines 5-64)
- "pnpm Global Bin Directory Not Configured (2025-10-23)" (lines 66-124)
- "OneDrive/Cloud Sync File I/O Errors (2025-01-21)" (lines 125-198)

- [ ] **Step 2: Remove archived entries from DISCOVERIES.md**

Delete lines 5-198 from DISCOVERIES.md, keeping:
- The header (`# DISCOVERIES.md` and intro text, lines 1-4)
- "Tool Generation Pattern Failures (2025-01-23)" (currently lines 199-256)
- "LLM Response Handling and Defensive Utilities (2025-01-19)" (currently lines 257-end)

- [ ] **Step 3: Verify both files**

Run: `grep "^## " DISCOVERIES.md` — should show exactly 2 entries.
Run: `grep "^## " DISCOVERIES-archive.md` — should show exactly 3 entries.

- [ ] **Step 4: Commit**

```bash
git add DISCOVERIES.md DISCOVERIES-archive.md
git commit -m "perf: archive 3 stale DISCOVERIES entries to reduce context overhead

Moved DevContainer Setup, pnpm Global Bin, and OneDrive/Cloud Sync
entries to DISCOVERIES-archive.md. Kept Tool Generation Patterns and
LLM Response Handling (still actively relevant). Saves ~1,000 tokens."
```

---

## Chunk 2: Priority 2 — Delegate In-Context Work (superpowers repo)

### Task 4: Add context scout subagent to brainstorming

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\superpowers\skills\brainstorming\SKILL.md:14-29`

- [ ] **Step 1: Read current Session Start section**

Read `skills/brainstorming/SKILL.md` lines 14-29 to confirm the current 3-step sequential context gathering pattern.

- [ ] **Step 2: Replace Session Start section**

Replace the content of the `## Session Start` section (lines 14-29) with:

```markdown
## Session Start

Before diving into the idea, gather context by dispatching a **context scout subagent**. This runs all context gathering in a separate context window, returning only a concise summary to the main session.

1. **Determine topic** from the user's message or ask what they want to work on.
2. **Dispatch context scout:**

```
Task(subagent_type="general-purpose", model="haiku", description="Gather session context for [topic]", prompt="
  Gather project context for a brainstorming session about [topic].

  Run these steps and compile a summary:
  1. Run: git status --short && git log --oneline -5
  2. Search episodic memory for conversations about [topic] (use episodic-memory:search-conversations if available)
  3. Run: node ${CLAUDE_PLUGIN_ROOT}/../commands/recall.js knowledge_base.decisions
  4. Run: node ${CLAUDE_PLUGIN_ROOT}/../commands/recall.js knowledge_base.glossary
  5. Check for existing specs: ls docs/superpowers/specs/ (if directory exists)
  6. Read ${CLAUDE_PLUGIN_ROOT}/AMPLIFIER-AGENTS.md

  If any step fails, skip it and continue.

  Return a structured summary (MAX 500 words, this is critical):
  ## Project State
  [branch, uncommitted changes, recent commits — 2-3 lines]

  ## Related Past Decisions
  [any ADRs or patterns relevant to topic — bullet list or 'None found']

  ## Relevant Agents
  [which Amplifier agents are likely needed for this task — bullet list]

  ## Existing Specs
  [any related design docs — list or 'None found']
")
```

3. **Present summary** to user and proceed to The Process.

See `${CLAUDE_PLUGIN_ROOT}/MEMORY-WORKFLOW.md` for when to use which memory system.
```

- [ ] **Step 3: Verify no broken markdown**

Read the full file and verify frontmatter is intact, all sections flow correctly.

- [ ] **Step 4: Commit**

```bash
cd /c/claude/superpowers
git add skills/brainstorming/SKILL.md
git commit -m "perf: delegate brainstorming context gathering to scout subagent

Session start now dispatches a haiku subagent to gather git status,
episodic memory, recall decisions/glossary, and agent mapping. Returns
~500 word summary instead of dumping ~5,000-13,000 tokens of raw tool
output into the main context window."
```

---

### Task 5: Delegate spec writing + review in brainstorming

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\superpowers\skills\brainstorming\SKILL.md:85-98`

- [ ] **Step 1: Read current "After the Design" section**

Read `skills/brainstorming/SKILL.md` lines 85-98 to confirm the current documentation and spec review loop pattern.

- [ ] **Step 2: Replace Documentation and Spec Review Loop subsections**

Replace lines 87-98 (the "Documentation:" and "Spec Review Loop:" subsections) with:

```markdown
**Documentation:**
- Delegate spec writing and review to a subagent, keeping only the result in main context:

```
Task(subagent_type="general-purpose", model="sonnet", description="Write and validate design spec", prompt="
  Write a design spec document from the following validated design.

  ## Validated Design
  [paste the complete design text including Agent Allocation table]

  ## Instructions
  1. Write the spec to: docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md
  2. Include all sections: Problem, Goal, Changes, Impact, Files Changed, Agent Allocation, Test Plan
  3. Self-review against this checklist:
     - All requirements from the design are captured
     - Agent allocation table is included
     - File paths are concrete (not placeholder)
     - No ambiguous language ('should', 'could', 'might' replaced with specifics)
     - Acceptance criteria are testable
  4. Fix any issues found during self-review
  5. Commit the spec: git add <file> && git commit -m 'docs: add <topic> design spec'
  6. Return: file path, git commit hash, review status (pass/fail), any concerns (MAX 100 words)
")
```

- (User preferences for spec location override the default path)
```

- [ ] **Step 3: Verify no broken markdown**

Read the full file and verify all sections flow correctly, frontmatter intact.

- [ ] **Step 4: Commit**

```bash
cd /c/claude/superpowers
git add skills/brainstorming/SKILL.md
git commit -m "perf: delegate spec writing and review to subagent

Spec writing, self-review, and git commit now happen in a separate
context window. Main context receives only file path and status
instead of accumulating ~4,000-9,000 tokens of spec content and
review loop exchanges."
```

---

### Task 6: Delegate plan generation in writing-plans

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\superpowers\skills\writing-plans\SKILL.md`

- [ ] **Step 1: Read current writing-plans skill**

Read the full `skills/writing-plans/SKILL.md` to understand the current structure.

- [ ] **Step 2: Add delegation instruction after the header section**

After the plan document header section and before the task structure section, add a new section:

```markdown
## Context-Efficient Plan Generation

For plans with 5+ tasks, delegate the heavy generation work to a subagent to protect the main context window:

```
Task(subagent_type="general-purpose", model="sonnet", description="Generate implementation plan for [feature]", prompt="
  You are writing an implementation plan. Follow these instructions EXACTLY.

  ## Spec Document
  Read the spec at: [spec file path]

  ## Agent Mapping
  Read the agent mapping at: ${CLAUDE_PLUGIN_ROOT}/AMPLIFIER-AGENTS.md

  ## Plan Template
  [paste the full plan document header template and task structure template from this skill]

  ## Requirements
  1. Create a task for each change in the spec's 'Files Changed' section
  2. Assign Agent: field to each task based on the agent mapping
  3. Include exact file paths for all Create/Modify/Test entries
  4. Write complete code for each step (not placeholders)
  5. Include TDD steps: write failing test, verify failure, implement, verify pass, commit
  6. Add review tasks where the spec's Agent Allocation specifies reviewers
  7. Write the plan to: [output path]
  8. Commit: git add <file> && git commit -m 'docs: add <feature> implementation plan'
  9. Return: file path, git commit hash, task count, and a 200-word summary of what each task covers
")
```

For plans with <5 tasks, generate in-context as before (the overhead is acceptable).

After receiving the subagent's summary, present it to the user: "Plan complete with N tasks. [summary]. Ready to execute?"
```

- [ ] **Step 3: Verify skill file is valid**

Read the full file and verify frontmatter, all sections, and the execution handoff at the end are intact.

- [ ] **Step 4: Commit**

```bash
cd /c/claude/superpowers
git add skills/writing-plans/SKILL.md
git commit -m "perf: delegate large plan generation to subagent

Plans with 5+ tasks are now generated in a separate context window.
Main context receives file path and 200-word summary instead of
accumulating ~12,000-31,000 tokens of plan content. Small plans
(<5 tasks) still generate in-context."
```

---

### Task 7: Add output discipline to prompt templates

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\superpowers\skills\subagent-driven-development\implementer-prompt.md`
- Modify: `C:\claude\superpowers\skills\subagent-driven-development\spec-reviewer-prompt.md`

- [ ] **Step 1: Read current implementer-prompt.md**

Read the full file to find the right insertion point (after the "DO NOT PLAN" block).

- [ ] **Step 2: Add output discipline to implementer-prompt.md**

After the `## IMMEDIATE ACTION` section (which contains "DO NOT PLAN" / "EXECUTE IMMEDIATELY"), add:

```markdown
    ## Output Discipline

    When reporting back, keep your response concise to protect the caller's context:
    - List files created/modified with paths (not full contents)
    - Summarize what changed in each file (1-2 lines per file)
    - Include test results: pass/fail counts and command used
    - Include git commit hash from `git log -1 --format="%H %s"`
    - If a file is >200 lines, report the path and summary, not the full content
    - Keep total report under 200 lines
```

- [ ] **Step 3: Read current spec-reviewer-prompt.md**

Read the full file to find the right insertion point.

- [ ] **Step 4: Add output discipline to spec-reviewer-prompt.md**

Add before the `**DO:**` section:

```markdown
    ## Output Discipline

    Keep your review concise to protect the caller's context:
    - State PASS or FAIL clearly at the top
    - List specific issues with file:line references
    - Do not reproduce full file contents in the review
    - For passing reviews, keep response under 50 lines
    - For failing reviews, keep response under 100 lines
```

- [ ] **Step 5: Commit**

```bash
cd /c/claude/superpowers
git add skills/subagent-driven-development/implementer-prompt.md skills/subagent-driven-development/spec-reviewer-prompt.md
git commit -m "perf: add output discipline to implementer and reviewer prompts

Subagents now return concise summaries (200 lines max for implementers,
100 lines max for reviewers) instead of full file contents. Protects
the main context window from large agent outputs."
```

---

## Chunk 3: Priority 3 — Agent Context Budget Guardrails (amplifier repo)

### Task 8: Add universal context budget to all 30 agents

**Agent:** modular-builder

**Files:**
- Modify: All 30 files in `C:\claude\amplifier\.claude\agents\*.md`

```
ambiguity-guardian.md        amplifier-cli-architect.md   analysis-engine.md
animation-choreographer.md   api-contract-designer.md     art-director.md
bug-hunter.md                component-designer.md        concept-extractor.md
content-researcher.md        contract-spec-author.md      database-architect.md
design-system-architect.md   graph-builder.md             insight-synthesizer.md
integration-specialist.md    knowledge-archaeologist.md    layout-architect.md
modular-builder.md           module-intent-architect.md    pattern-emergence.md
performance-optimizer.md     post-task-cleanup.md          responsive-strategist.md
security-guardian.md         subagent-architect.md         test-coverage.md
visualization-architect.md   voice-strategist.md           zen-architect.md
```

- [ ] **Step 1: Append context budget block to each agent file**

Append the following block to the END of each of the 30 agent `.md` files:

```markdown

## Context Budget

- **File reads**: Max 15 per invocation. If you need more, summarize findings so far and return with a note on what remains.
- **Output**: Return summaries with file:line references, not full file reproductions. Target max 300 lines of output.
- **Stop condition**: After reading 10 files without clear progress toward your deliverable, STOP and return what you have with a note on what's blocking you.
- **No re-planning**: If you receive a plan, execute it. Do not spend tokens creating a new plan.
```

- [ ] **Step 2: Verify all 30 files were updated**

Run: `grep -l "## Context Budget" .claude/agents/*.md | wc -l`
Expected: 30

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/*.md
git commit -m "perf: add universal context budget guardrails to all 30 agents

Every agent now has file read limits (max 15), output size targets
(max 300 lines), stop conditions (10 reads without progress), and
no-replan instructions. Prevents agent context window exhaustion."
```

---

### Task 9: Add specific limits to 7 high-risk agents

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\amplifier\.claude\agents\content-researcher.md`
- Modify: `C:\claude\amplifier\.claude\agents\analysis-engine.md`
- Modify: `C:\claude\amplifier\.claude\agents\bug-hunter.md`
- Modify: `C:\claude\amplifier\.claude\agents\security-guardian.md`
- Modify: `C:\claude\amplifier\.claude\agents\post-task-cleanup.md`
- Modify: `C:\claude\amplifier\.claude\agents\amplifier-cli-architect.md`
- Modify: `C:\claude\amplifier\.claude\agents\modular-builder.md`

- [ ] **Step 1: Add specific limits to content-researcher.md**

Add after the universal Context Budget block:

```markdown

### Content Researcher Limits
- **Scan phase**: Read headers/first 5 lines of max 20 files to assess relevance
- **Deep read phase**: Full-read max 5 of the most relevant files
- **Output**: Return key quotes with file:line references, not full document reproductions
```

- [ ] **Step 2: Add specific limits to analysis-engine.md**

```markdown

### Analysis Engine Limits
- **TRIAGE mode**: Scan max 30 document headers (first 5 lines each)
- **DEEP mode**: Full-read max 3 documents
- **SYNTHESIS mode**: Combine max 5 sources
- If total file reads exceed 15, stop and return partial results with a note
```

- [ ] **Step 3: Add specific limits to bug-hunter.md**

```markdown

### Bug Hunter Limits
- **Investigation**: Max 10 file reads before forming a hypothesis
- **Hypothesis cycles**: Max 3 cycles of hypothesize-test-refine, then return findings
- **Scope**: Read error location + max 2 levels of callers/callees
```

- [ ] **Step 4: Add specific limits to security-guardian.md**

```markdown

### Security Guardian Limits
- **Scope requirement**: Caller must provide explicit scope (file list, endpoint list, or specific categories to check)
- **No unbounded scans**: Do not scan the entire codebase. If scope is not provided, ask for it before proceeding.
- **Per-scan limit**: Max 15 files per security review pass
```

- [ ] **Step 5: Add specific limits to post-task-cleanup.md**

```markdown

### Post-Task Cleanup Limits
- **Large changesets**: If >15 files touched, do summary-level review (check file names, commit messages, obvious issues)
- **Deep review**: Max 10 files for detailed philosophy compliance checking
- **Report**: Brief format when <5 issues found (skip verbose template sections)
```

- [ ] **Step 6: Add specific limits to amplifier-cli-architect.md**

```markdown

### CLI Architect Limits
- **Lazy-load references**: Do NOT pre-read all reference files. Read only DEVELOPER_GUIDE.md upfront.
- **On-demand reads**: Read other reference files (IMPLEMENTATION_PHILOSOPHY, scenarios/README, templates, examples) only when specifically needed for the current task.
```

- [ ] **Step 7: Add specific limits to modular-builder.md**

```markdown

### Modular Builder Output Limits
- **Large files**: For files >200 lines, return the file path and a summary of changes, not the full contents
- **Diffs preferred**: When modifying existing files, describe the changes as diffs or before/after snippets, not full file reproductions
```

- [ ] **Step 8: Verify all 7 files have specific limits**

Run: `grep -l "### .* Limits" .claude/agents/*.md | wc -l`
Expected: 7

- [ ] **Step 9: Commit**

```bash
git add .claude/agents/content-researcher.md .claude/agents/analysis-engine.md .claude/agents/bug-hunter.md .claude/agents/security-guardian.md .claude/agents/post-task-cleanup.md .claude/agents/amplifier-cli-architect.md .claude/agents/modular-builder.md
git commit -m "perf: add specific context limits to 7 high-risk agents

content-researcher: max 20 scan, 5 deep-read
analysis-engine: mode-specific caps (30/3/5)
bug-hunter: 10 reads before hypothesis, 3 cycles max
security-guardian: require explicit scope, no unbounded scans
post-task-cleanup: summary review for >15 file changesets
amplifier-cli-architect: lazy-load references
modular-builder: return paths+summaries for large files"
```

---

### Task 10: Add Required Context to 7 design agents

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\amplifier\.claude\agents\component-designer.md`
- Modify: `C:\claude\amplifier\.claude\agents\art-director.md`
- Modify: `C:\claude\amplifier\.claude\agents\design-system-architect.md`
- Modify: `C:\claude\amplifier\.claude\agents\layout-architect.md`
- Modify: `C:\claude\amplifier\.claude\agents\responsive-strategist.md`
- Modify: `C:\claude\amplifier\.claude\agents\voice-strategist.md`
- Modify: `C:\claude\amplifier\.claude\agents\animation-choreographer.md`

- [ ] **Step 1: Add Required Context section to each design agent**

Add BEFORE the Context Budget block in each of the 7 design agent files:

```markdown

## Required Context

Before starting work, read these design philosophy files for project design guidelines:
- `ai_context/DESIGN-PHILOSOPHY.md`
- `ai_context/DESIGN-PRINCIPLES.md`
- `ai_context/design/DESIGN-FRAMEWORK.md`
- `ai_context/design/DESIGN-VISION.md`
```

- [ ] **Step 2: Verify all 7 files have Required Context**

Run: `grep -l "## Required Context" .claude/agents/*.md | wc -l`
Expected: 7

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/component-designer.md .claude/agents/art-director.md .claude/agents/design-system-architect.md .claude/agents/layout-architect.md .claude/agents/responsive-strategist.md .claude/agents/voice-strategist.md .claude/agents/animation-choreographer.md
git commit -m "feat: add Required Context to design agents for on-demand philosophy loading

Design agents now read DESIGN-PHILOSOPHY, DESIGN-PRINCIPLES,
DESIGN-FRAMEWORK, and DESIGN-VISION on demand. These files were
removed from the always-loaded @import chain in Task 1 to save
~14,000 tokens per non-design session."
```

---

## Chunk 4: Verification

### Task 11: Verify token savings and all changes

**Agent:** test-coverage

**Scope:** Verify all priorities achieved their goals.

- [ ] **Step 1: Count words in the active @import chain**

Run:
```bash
cd /c/claude/amplifier
wc -w CLAUDE.md AGENTS.md DISCOVERIES.md ai_context/IMPLEMENTATION_PHILOSOPHY.md ai_context/MODULAR_DESIGN_PHILOSOPHY.md
```

Expected: Total should be ~9,000 words or less (down from ~21,200 baseline).

- [ ] **Step 2: Verify design files are NOT in @imports**

Run: `grep "^- @ai_context/DESIGN" CLAUDE.md`
Expected: No output (no active @imports for design files).

Run: `grep "^# - ai_context/DESIGN" CLAUDE.md`
Expected: 4 comment lines listing the design files.

- [ ] **Step 3: Verify design agents have Required Context**

Run: `grep -c "## Required Context" .claude/agents/component-designer.md .claude/agents/art-director.md .claude/agents/design-system-architect.md .claude/agents/layout-architect.md .claude/agents/responsive-strategist.md .claude/agents/voice-strategist.md .claude/agents/animation-choreographer.md`
Expected: Each file shows count of 1.

- [ ] **Step 4: Verify all 30 agents have Context Budget**

Run: `grep -l "## Context Budget" .claude/agents/*.md | wc -l`
Expected: 30

- [ ] **Step 5: Verify 7 high-risk agents have specific limits**

Run: `grep -l "### .* Limits" .claude/agents/*.md`
Expected: 7 files listed (content-researcher, analysis-engine, bug-hunter, security-guardian, post-task-cleanup, amplifier-cli-architect, modular-builder).

- [ ] **Step 6: Verify brainstorming skill has context scout pattern**

Run: `grep "context scout" /c/claude/superpowers/skills/brainstorming/SKILL.md`
Expected: Match found (confirms Task 4 applied).

Run: `grep "Gather session context" /c/claude/superpowers/skills/brainstorming/SKILL.md`
Expected: Match found (confirms subagent dispatch pattern).

- [ ] **Step 7: Verify writing-plans skill has delegation pattern**

Run: `grep "Context-Efficient Plan Generation" /c/claude/superpowers/skills/writing-plans/SKILL.md`
Expected: Match found (confirms Task 6 applied).

- [ ] **Step 8: Verify implementer/reviewer prompts have output discipline**

Run: `grep "Output Discipline" /c/claude/superpowers/skills/subagent-driven-development/implementer-prompt.md`
Expected: Match found.

Run: `grep "Output Discipline" /c/claude/superpowers/skills/subagent-driven-development/spec-reviewer-prompt.md`
Expected: Match found.

- [ ] **Step 9: Verify brainstorming spec writing is delegated**

Run: `grep "Write and validate design spec" /c/claude/superpowers/skills/brainstorming/SKILL.md`
Expected: Match found (confirms Task 5 applied).

---

### Task 12: Final cleanup

**Agent:** post-task-cleanup

**Scope:** Review all changes across both repos for hygiene.

- [ ] **Step 1: Check amplifier repo**

Run `git diff --stat HEAD~5` in amplifier repo. Verify:
- No accidental file deletions
- No broken markdown syntax
- AGENTS.md still has all unique sections (git commit guidelines, sub-agent strategy, etc.)

- [ ] **Step 2: Check superpowers repo**

Run `git diff --stat HEAD~4` in superpowers repo. Verify:
- Skill frontmatter is intact in all modified files
- No broken markdown syntax
- All existing skill sections preserved (only Session Start, Documentation, and writing-plans changed)

- [ ] **Step 3: Report**

List all commits made across both repos with their hashes and one-line summaries.
