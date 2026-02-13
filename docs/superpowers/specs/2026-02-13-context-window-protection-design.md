# Context Window Protection for Amplifier + Superpowers Integration

**Date:** 2026-02-13
**Status:** Draft

## Problem

Sessions break when context windows fill up and compaction fails. Root causes:

1. **Layer 1 — Fixed overhead**: ~43,000 tokens (22% of 200k window) consumed by system prompt chain before any user interaction. 14,000 tokens are design philosophy files irrelevant to most tasks.
2. **Layer 1 — Dynamic accumulation**: Brainstorming + planning accumulates 27,000-60,000 tokens in main context, but only ~8,000-12,000 is essential (user Q&A, decisions). The rest is raw tool output, redundant reads, and in-context plan generation.
3. **Layer 3 — Agent blowout**: 7 of 30 agents have no context budget awareness and can fill their own windows (content-researcher, analysis-engine, bug-hunter, security-guardian, post-task-cleanup, amplifier-cli-architect, modular-builder).

Combined: a brainstorming-to-planning session consumes 70,000-103,000 tokens (35-52%) before implementation starts, leaving insufficient room for the actual work.

## Goal

Reduce main context consumption so a full brainstorming-to-implementation session uses <40,000 tokens before implementation begins, leaving 80%+ of context for actual work. Add guardrails to prevent agent context blowout.

## Changes

### Priority 1: Reduce Fixed Overhead (~17,000 tokens saved)

**Repo: amplifier**

#### 1a. Remove design @imports from CLAUDE.md

Remove these 4 lines from the `@import` section in `amplifier/CLAUDE.md`:

```
- @ai_context/DESIGN-PHILOSOPHY.md      (~4,100 tokens)
- @ai_context/DESIGN-PRINCIPLES.md      (~2,700 tokens)
- @ai_context/design/DESIGN-FRAMEWORK.md (~5,200 tokens)
- @ai_context/design/DESIGN-VISION.md   (~2,000 tokens)
```

Files stay in the repo. Add a `Read` instruction to each of the 7 design agent files so they load the relevant context on dispatch:

Add to `.claude/agents/component-designer.md`, `.claude/agents/art-director.md`, `.claude/agents/design-system-architect.md`, `.claude/agents/layout-architect.md`, `.claude/agents/responsive-strategist.md`, `.claude/agents/voice-strategist.md`, `.claude/agents/animation-choreographer.md`:

```markdown
## Required Context
Before starting work, read these design philosophy files:
- ai_context/DESIGN-PHILOSOPHY.md
- ai_context/DESIGN-PRINCIPLES.md
- ai_context/design/DESIGN-FRAMEWORK.md
- ai_context/design/DESIGN-VISION.md
```

Also add a comment in CLAUDE.md noting where they are:

```markdown
# Design philosophy files (loaded on demand by design agents, not always):
# - ai_context/DESIGN-PHILOSOPHY.md
# - ai_context/DESIGN-PRINCIPLES.md
# - ai_context/design/DESIGN-FRAMEWORK.md
# - ai_context/design/DESIGN-VISION.md
```

#### 1b. Deduplicate AGENTS.md

Replace these two sections in AGENTS.md (which duplicate content from IMPLEMENTATION_PHILOSOPHY.md and MODULAR_DESIGN_PHILOSOPHY.md):

- `## Implementation Philosophy` (line 418 to line ~715) — ~6,000 words duplicating ai_context/IMPLEMENTATION_PHILOSOPHY.md
- `## Modular Design Philosophy` (line 716 to end) — ~900 words duplicating ai_context/MODULAR_DESIGN_PHILOSOPHY.md

Replace both with a single reference line:

```markdown
For implementation philosophy, design principles, and technical guidelines,
see @ai_context/IMPLEMENTATION_PHILOSOPHY.md (already loaded via CLAUDE.md @imports).
```

Keep AGENTS.md content that is unique (git commit guidelines, sub-agent optimization strategy, incremental processing pattern, partial failure handling, zero-BS principle, response authenticity, formatting guidelines, etc.).

#### 1c. Archive stale DISCOVERIES.md entries

DISCOVERIES.md has 5 entries. Archive these 3 (pre-2025, no longer actionable):
- "DevContainer Setup: Using Official Features Instead of Custom Scripts (2025-10-22)"
- "pnpm Global Bin Directory Not Configured (2025-10-23)"
- "OneDrive/Cloud Sync File I/O Errors (2025-01-21)"

Move them to `DISCOVERIES-archive.md` (new file).

Keep these 2 (still actively relevant):
- "Tool Generation Pattern Failures (2025-01-23)" — enforces recursive glob, minimum input validation
- "LLM Response Handling and Defensive Utilities (2025-01-19)" — parse_llm_json, retry_with_feedback patterns

### Priority 2: Delegate In-Context Work (~18,000-45,000 tokens saved)

**Repo: superpowers (fork)**

**Prerequisite:** Pull `origin/main` to include:
- `449100e` — Subagent reliability: `subagent_type: "general"` pattern, "DO NOT PLAN / EXECUTE IMMEDIATELY" in implementer prompt, commit verification with `git log -1`
- `bd65f4e` — Unified skill indexing and UI signal support for OpenCode

#### 2a. Context Scout Subagent (brainstorming session start)

Replace the current sequential 6-step context gathering in `skills/brainstorming/SKILL.md` with a single subagent dispatch:

**Current pattern** (accumulates ~5,500-13,000 tokens of raw output):
```
1. git status, git log, file reads
2. episodic memory search
3. recall decisions, recall glossary
4. read AMPLIFIER-AGENTS.md
```

**New pattern** (receives ~500 token summary):
```
Dispatch a general-purpose subagent to gather project context:

Task(subagent_type="general-purpose", description="Gather session context", prompt="
  Gather project context for a brainstorming session about [topic]:
  1. Run git status and git log -5 --oneline
  2. Search episodic memory for conversations about [topic]
  3. Run: node [recall.js path] knowledge_base.decisions
  4. Run: node [recall.js path] knowledge_base.glossary
  5. Check for existing specs in docs/superpowers/specs/

  Return a structured summary (max 500 words):
  - Project state: branch, uncommitted changes, recent work
  - Related past decisions: any ADRs or patterns relevant to [topic]
  - Suggested agents: which Amplifier agents are likely needed
  - Existing specs: any related design docs already written
")
```

The main context receives the summary, not the raw tool outputs.

**Where in SKILL.md:** Replace the "Session Start" section (currently titled `## Session Start` with steps 1-3). Keep the section heading. Replace the numbered steps with: (1) determine topic from user message, (2) dispatch context scout subagent with the pattern above, (3) present the summary to user and proceed to design phase.

#### 2b. Delegate writing-plans to Subagent

Replace in-context plan generation in `skills/writing-plans/SKILL.md` with subagent dispatch:

**Current pattern** (accumulates ~12,000-31,000 tokens):
- Reads spec document in-context
- Reads AMPLIFIER-AGENTS.md again
- Calls recall.js again (3rd time)
- Generates full plan with code snippets in-context
- Runs review loop in-context

**New pattern** (receives ~300 token summary):
```
After design is validated and spec is written to disk:

Task(subagent_type="zen-architect", description="Create implementation plan", prompt="
  Read the spec at [spec path].
  Read the agent mapping at [AMPLIFIER-AGENTS.md path].

  Create an implementation plan following this template:
  [insert writing-plans task template]

  For each task:
  - Assign Agent: field based on task type and agent mapping
  - Include complete file paths (Create/Modify/Test)
  - Include full step-by-step implementation instructions
  - Assign review level (1/2/3) based on complexity and security sensitivity

  Write the plan to [output path].
  Return: file path + task count + summary of what each task covers (max 200 words).
")
```

Main context only receives the summary. Full plan lives on disk, read by subagent-driven-development when executing.

**Where in SKILL.md:** The current writing-plans skill has a section where the orchestrator generates the plan content in-context (reads spec, maps agents, writes tasks). Replace this generation block with the subagent dispatch above. Keep the skill's intro (reading the spec path from brainstorming handoff) and outro (execution path recommendation). The subagent does the heavy generation work.

#### 2c. Delegate Spec Writing + Review Loop

Replace the in-context write-spec + review cycle in `skills/brainstorming/SKILL.md`:

**Current pattern** (accumulates ~4,000-9,000 tokens):
- Write spec to file in main context
- Dispatch spec reviewer (returns to main context)
- Fix issues in main context
- Re-dispatch reviewer
- Loop up to 5 times

**New pattern** (receives ~200 token confirmation):
```
After design is validated through user Q&A:

Task(subagent_type="contract-spec-author", description="Write and validate spec", prompt="
  Write a design spec from this validated design:

  [paste the validated design text from the conversation]

  Save to: [spec path]

  After writing, self-review against this checklist:
  - All requirements from the design are captured
  - Agent allocation table is included
  - File paths are concrete
  - No ambiguous language
  - Acceptance criteria are testable

  Fix any issues found. Return: file path + review status (pass/fail) + any concerns.
")
```

**Where in SKILL.md:** Replace the "After the Design" → "Documentation" subsection in brainstorming. Currently it instructs the orchestrator to write the spec file and then dispatch a reviewer in a loop. Replace with the single subagent dispatch above. Keep the git commit step after the subagent returns success.

### Priority 3: Agent Context Budget Guardrails

**Repo: amplifier**

#### 3a. Universal Context Budget Block

Add to all 30 agent definitions in `amplifier/.claude/agents/`:

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

Append to each file:

```markdown
## Context Budget

- **File reads**: Max 15 per invocation. If you need more, summarize findings so far and return with a note on what remains.
- **Output**: Return summaries with file:line references, not full file reproductions. Target max 300 lines of output.
- **Stop condition**: After reading 10 files without clear progress toward your deliverable, STOP and return what you have with a note on what's blocking you.
- **No re-planning**: If you receive a plan, execute it. Do not spend tokens creating a new plan.
```

#### 3b. HIGH RISK Agent-Specific Limits

Additional guardrails for the 7 high-risk agents, added to their specific files:

| Agent | Additional Constraint |
|-------|----------------------|
| `content-researcher` | Scan headers of max 20 files. Deep-read max 5. Return key quotes with file:line, not full docs. |
| `analysis-engine` | TRIAGE: scan max 30 doc headers. DEEP: max 3 full reads. SYNTHESIS: max 5 sources. |
| `bug-hunter` | Max 10 file reads before forming hypothesis. Max 3 hypothesis cycles, then return findings. |
| `security-guardian` | Require explicit scope from caller (file list or endpoint list). No unbounded codebase scans. |
| `post-task-cleanup` | If changeset >15 files, summary-level review. Deep-review max 10 files. |
| `amplifier-cli-architect` | Lazy-load references. Read DEVELOPER_GUIDE only upfront, others on demand. |
| `modular-builder` | (Already has guardrails.) Add: return file paths + diffs for files >200 lines, not full contents. |

#### 3c. Prompt Template Output Discipline

Add to `skills/subagent-driven-development/implementer-prompt.md` (after existing "DO NOT PLAN" block):

```markdown
## Output Discipline

When reporting back:
- List files created/modified with paths
- Summarize what changed (not full file contents)
- Include test results (pass/fail counts)
- Include git commit hash
- Keep total report under 200 lines
```

Add similar block to `spec-reviewer-prompt.md`:

```markdown
## Output Discipline

When reporting back:
- State pass/fail clearly
- List specific issues with file:line references
- Do not reproduce full file contents in the review
- Keep total report under 100 lines
```

## Impact Summary

| Layer | Before | After | Savings |
|-------|--------|-------|---------|
| Fixed overhead | ~43,000 tokens (22%) | ~26,000 tokens (13%) | ~17,000 tokens |
| Dynamic (brainstorm+plan) | ~27,000-60,000 tokens | ~9,000-15,000 tokens | ~18,000-45,000 tokens |
| Agent guardrails | Unbounded | Capped at 15 file reads, 300 lines output | Prevents blowout |
| **Total session to implementation** | **70,000-103,000 tokens (35-52%)** | **~25,000-40,000 tokens (13-20%)** | **~45,000-63,000 tokens** |

## Files Changed

### amplifier repo

| File | Change |
|------|--------|
| `CLAUDE.md` | Remove 4 design @imports, add comment noting location |
| `AGENTS.md` | Replace duplicated sections with reference to IMPLEMENTATION_PHILOSOPHY.md |
| `DISCOVERIES.md` | Remove stale entries |
| `DISCOVERIES-archive.md` (new) | Archived entries |
| `.claude/agents/*.md` (30 files) | Add universal context budget block |
| `.claude/agents/{component-designer,art-director,design-system-architect,layout-architect,responsive-strategist,voice-strategist,animation-choreographer}.md` (7 files) | Add "Required Context" section to read design philosophy files |
| `.claude/agents/content-researcher.md` | Add specific file read limits |
| `.claude/agents/analysis-engine.md` | Add mode-specific limits |
| `.claude/agents/bug-hunter.md` | Add hypothesis cycle limit |
| `.claude/agents/security-guardian.md` | Add scope requirement |
| `.claude/agents/post-task-cleanup.md` | Add changeset size check |
| `.claude/agents/amplifier-cli-architect.md` | Add lazy-load instruction |
| `.claude/agents/modular-builder.md` | Add output size limit |

### superpowers repo

| File | Change |
|------|--------|
| `skills/brainstorming/SKILL.md` | Context scout subagent, delegate spec writing |
| `skills/writing-plans/SKILL.md` | Delegate plan generation to subagent |
| `skills/subagent-driven-development/implementer-prompt.md` | Add output discipline block |
| `skills/subagent-driven-development/spec-reviewer-prompt.md` | Add output discipline block |

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Architecture | zen-architect | Review delegation patterns for skill rewrites |
| P1: amplifier edits | modular-builder | CLAUDE.md, AGENTS.md, DISCOVERIES.md changes |
| P2: skill rewrites | modular-builder | brainstorming + writing-plans skill changes |
| P3: agent guardrails | modular-builder | 30 agent files + prompt templates |
| Review | test-coverage | Verify skills dispatch correctly after changes |
| Cleanup | post-task-cleanup | Final hygiene pass |

## Test Plan

### Verification of token savings (Priority 1)
After P1 edits, count words in the @import chain by running:
```bash
wc -w amplifier/CLAUDE.md amplifier/AGENTS.md amplifier/DISCOVERIES.md amplifier/ai_context/IMPLEMENTATION_PHILOSOPHY.md amplifier/ai_context/MODULAR_DESIGN_PHILOSOPHY.md
```
Target: total words should drop by ~12,000+ compared to baseline of ~21,200 words.

### Verification of delegation (Priority 2)
Run a brainstorming session on a test topic. Confirm:
1. Session start dispatches a single subagent (not 6+ inline tool calls)
2. The subagent returns a summary <500 words (not raw tool output)
3. After design validation, spec writing dispatches a subagent (not inline writes)
4. writing-plans dispatches a subagent (not inline plan generation)
5. Main conversation stays responsive throughout (no compaction warnings)

### Verification of agent guardrails (Priority 3)
Dispatch `content-researcher` on a directory with 30+ files. Confirm:
1. It reads max 20 file headers, max 5 full files
2. Output is under 300 lines
3. It stops and returns partial results rather than reading everything

### Verification of design agent context
Dispatch `component-designer` for a UI task. Confirm:
1. It reads the design philosophy files from its "Required Context" section
2. Design quality is not degraded by removing @imports

## What We Don't Change

- Core superpowers discipline (TDD, verification, red flags)
- The dispatch mechanism itself (Task tool + subagent_type)
- Model selection mapping (haiku/sonnet/opus)
- Review level system (Level 1/2/3)
- Memory workflow triggers (recall/memorize)
- Plugin structure or metadata

## Execution Path

Medium task (2 repos, ~35 files, 3 priority tiers). Recommended:

1. Pull superpowers `origin/main` to get `449100e`
2. Write plan with `superpowers:writing-plans`
3. Execute with `superpowers:subagent-driven-development`
4. P1 and P3 (amplifier repo) can run in parallel
5. P2 (superpowers repo) can run in parallel with P1/P3
