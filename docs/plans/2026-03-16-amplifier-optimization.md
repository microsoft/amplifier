# Amplifier Optimization Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all critical, high, and medium optimization issues found in the Amplifier project scan.

**Architecture:** Three phases — Critical fixes (data accuracy), High-impact improvements (agent quality + design doc wiring), Medium cleanup (dead code + stale docs). Each phase is independently committable.

**Tech Stack:** Markdown files, YAML config — no code compilation needed.

---

## Phase 1: Critical Fixes (accuracy & broken references)

### Task 1: Fix agent count and broken references across CLAUDE.md, llms.txt, AGENTS.md

**Agent:** modular-builder

**Files:**
- Modify: `CLAUDE.md`
- Modify: `llms.txt`
- Modify: `AGENTS.md`

- [ ] **Step 1: Count actual agents**

Run: `grep -c "^  " config/routing-matrix.yaml` in the agents section to get the exact count. Cross-reference with `ls .claude/agents/ | wc -l`.

- [ ] **Step 2: Fix CLAUDE.md**

Find the line that says "36 specialized agents" and update to the correct count. The line is in the project description near the top.

- [ ] **Step 3: Fix llms.txt**

Find any reference to agent count ("30+" or "36") and update to match.

- [ ] **Step 4: Fix AGENTS.md reference to AGENTS_CATALOG.md**

Line ~51 says "Always check `.claude/AGENTS_CATALOG.md` before starting." Verify this file exists. If it does, confirm it's useful. If it's just a thin reference table, update the instruction to: "Check `.claude/AGENTS_CATALOG.md` for the full agent registry. For model/effort assignments, see `config/routing-matrix.yaml`."

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md llms.txt AGENTS.md
git commit -m "fix: correct agent count and AGENTS_CATALOG reference"
```

---

### Task 2: Fix content-researcher routing in routing-matrix.yaml

**Agent:** modular-builder

**Files:**
- Modify: `config/routing-matrix.yaml`

- [ ] **Step 1: Change content-researcher role**

In `config/routing-matrix.yaml`, find:
```yaml
  content-researcher: research
```
Verify this is already `research`. If it's `scout`, change it to `research`.

The scout report said it was mapped to scout — verify and fix.

- [ ] **Step 2: Verify no other mis-routed agents**

Scan the agents section for any agent that does research/reasoning work but is mapped to `scout` (haiku). Candidates to check:
- `concept-extractor` (currently scout) — OK, it extracts/summarizes, haiku is fine
- `amplifier-expert` (currently fast) — OK, quick reference lookups
- `handoff-gemini` (currently fast) — OK, lightweight coordination

- [ ] **Step 3: Commit**

```bash
git add config/routing-matrix.yaml
git commit -m "fix: route content-researcher to research/sonnet tier"
```

---

## Phase 2: High-Impact Improvements

### Task 3: Add Synthesis Guard to all agents missing it

**Agent:** modular-builder

**Files:**
- Modify: All `.claude/agents/*.md` files that lack a Context Budget section

- [ ] **Step 1: Identify agents missing the guard**

Run: `grep -rL "Context Budget\|Synthesis guard\|synthesis guard" .claude/agents/*.md`

This lists agent files that do NOT contain the required section.

- [ ] **Step 2: Add Context Budget section to each**

For every agent file missing it, append before the closing content (or after the last section):

```markdown
## Context Budget

- **Synthesis guard**: When nearing your turn limit, STOP tool calls and produce your final output with whatever findings you have. Partial results with clear structure are MORE valuable than exhausting all turns on research with no summary. Always reserve at least 2 turns for writing your response.

- **File reads**: Max 15 per invocation. If you need more, summarize findings so far and return with a note on what remains.
- **Output**: Return summaries with file:line references, not full file reproductions. Target max 300 lines of output.
- **Stop condition**: After reading 10 files without clear progress toward your deliverable, STOP and return what you have with a note on what's blocking you.
- **No re-planning**: If you receive a plan, execute it. Do not spend tokens creating a new plan.
```

Skip agents that already have this section (component-designer has it).

- [ ] **Step 3: Verify count**

Run: `grep -rL "Synthesis guard" .claude/agents/*.md` — should return 0 files.

- [ ] **Step 4: Commit**

```bash
git add .claude/agents/
git commit -m "feat: add Synthesis Guard to all agents per AGENTS.md mandate"
```

---

### Task 4: Wire design docs into all 7 design agents

**Agent:** modular-builder

**Files:**
- Modify: `.claude/agents/design-system-architect.md`
- Modify: `.claude/agents/animation-choreographer.md`
- Modify: `.claude/agents/layout-architect.md`
- Modify: `.claude/agents/responsive-strategist.md`
- Modify: `.claude/agents/art-director.md`
- Modify: `.claude/agents/voice-strategist.md`

(component-designer already has these references — skip it.)

- [ ] **Step 1: Add design doc references to each agent**

For each of the 6 agents above, find the "Required Context" or equivalent section. If none exists, add one before the Context Budget section. Add:

```markdown
## Required Context

Before starting work, consult these design reference docs where relevant:
- `ai_context/design/UX-REVIEW-CHECKLIST.md` — Prioritized UX quality checklist (use during review)
- `ai_context/design/FONT-PAIRINGS.md` — 20 curated font pairings by mood/use case
- `ai_context/design/COLOR-STRATEGY.md` — Semantic color tokens, dark mode, accessible color pairs
```

Adapt the list per agent — voice-strategist only needs UX checklist (forms/feedback section), not font pairings. art-director needs all three. layout-architect needs UX checklist (layout section) and color strategy.

- [ ] **Step 2: Verify references**

Run: `grep -rl "UX-REVIEW-CHECKLIST" .claude/agents/` — should return 7 agents (all design agents).

- [ ] **Step 3: Commit**

```bash
git add .claude/agents/
git commit -m "feat: wire design reference docs into all design agents"
```

---

### Task 5: Archive stale cowork docs

**Agent:** post-task-cleanup

**Files:**
- Move: `docs/archive/COWORK.md` → verify already in archive
- Move: `docs/archive/HANDOFF.md` → verify already in archive
- Move: `docs/archive/DISCOVERIES.md` → verify already in archive
- Modify: Any files that reference these docs — remove or update references

- [ ] **Step 1: Verify cowork docs are in archive**

```bash
ls docs/archive/
```

If COWORK.md, HANDOFF.md, DISCOVERIES.md are already in `docs/archive/`, just verify no active files reference them.

- [ ] **Step 2: Search for references to stale docs**

```bash
grep -r "COWORK\|HANDOFF\|DISCOVERIES" --include="*.md" . | grep -v "docs/archive" | grep -v ".git"
```

For each reference found: if it's a working cross-reference, update it to point to `docs/archive/`. If it's a stale instruction ("check HANDOFF.md"), remove it.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: clean stale cowork doc references"
```

---

## Phase 3: Medium Cleanup

### Task 6: Remove dead scripts superseded by MCP tools

**Agent:** post-task-cleanup

**Files:**
- Check: `scripts/gitea/gitea-create-pr.sh`
- Check: `scripts/gitea/gitea-merge-pr.sh`
- Check: `scripts/observers/build-watcher.sh`
- Check: `scripts/observers/drift-detector.sh`

- [ ] **Step 1: Verify scripts are unreferenced**

For each file, search for references:
```bash
grep -r "gitea-create-pr\|gitea-merge-pr\|build-watcher\|drift-detector" --include="*.md" --include="*.yaml" --include="*.sh" . | grep -v ".git"
```

- [ ] **Step 2: Remove confirmed dead scripts**

Only remove scripts that have ZERO references. If any script is referenced, leave it and add a comment noting it may be superseded by MCP tools.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove dead scripts superseded by Gitea MCP and hooks"
```

---

### Task 7: Final verification and cleanup

**Agent:** post-task-cleanup

- [ ] **Step 1: Run consistency checks**

Verify:
- Agent count in CLAUDE.md matches `ls .claude/agents/ | wc -l`
- All agents have Synthesis Guard: `grep -rL "Synthesis guard" .claude/agents/*.md` returns 0
- All design agents reference UX checklist: `grep -rl "UX-REVIEW-CHECKLIST" .claude/agents/` returns 7
- routing-matrix.yaml content-researcher is `research` not `scout`
- No references to COWORK.md/HANDOFF.md outside docs/archive/

- [ ] **Step 2: Run git status and verify clean state**

```bash
git status
git log --oneline -7
```

Should show 5-6 clean commits from this plan.

- [ ] **Step 3: Report summary**

List all changes made, files modified, and verification results.

---

## Summary

| Phase | Tasks | Files Modified | Commits |
|-------|-------|---------------|---------|
| 1: Critical | 2 | CLAUDE.md, llms.txt, AGENTS.md, routing-matrix.yaml | 2 |
| 2: High | 3 | ~40 agent files + docs references | 3 |
| 3: Medium | 2 | ~4 script files + final verification | 1-2 |
| **Total** | **7** | **~50 files** | **6-7** |
