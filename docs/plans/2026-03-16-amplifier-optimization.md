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

- [x] **Step 1: Count actual agents** *(Done 2026-03-16: 36 agents, 35 commands)*

Run: `grep -c "^  " config/routing-matrix.yaml` in the agents section to get the exact count. Cross-reference with `ls .claude/agents/ | wc -l`.

- [x] **Step 2: Fix CLAUDE.md** *(Done: 31→35 commands)*

Find the line that says "36 specialized agents" and update to the correct count. The line is in the project description near the top.

- [x] **Step 3: Fix llms.txt** *(Done: "30+ agents, 19 commands" → "36 agents, 35 commands")*

Find any reference to agent count ("30+" or "36") and update to match.

- [x] **Step 4: Fix AGENTS.md reference to AGENTS_CATALOG.md** *(Verified 2026-03-16: file exists, 133 lines, valid catalog. Reference is correct — no change needed.)*

- [x] **Step 5: Commit** *(Done: PR #40)*

```bash
git add CLAUDE.md llms.txt AGENTS.md
git commit -m "fix: correct agent count and AGENTS_CATALOG reference"
```

---

### Task 2: ~~Fix content-researcher routing~~ — SKIPPED (false positive)

> **Verified 2026-03-16:** Already `content-researcher: research` in routing-matrix.yaml:97. Scout report was incorrect.

---

## Phase 2: High-Impact Improvements

### Task 3: ~~Add Synthesis Guard to all agents~~ — SKIPPED (false positive)

> **Verified 2026-03-16:** All 36 agents already have Context Budget sections with Synthesis Guard. `grep -rl "Context Budget" .claude/agents/*.md | wc -l` = 36. Scout searched for exact heading text "Synthesis Guard" instead of checking content within Context Budget sections.

---

### Task 4: Wire design docs into all 7 design agents — DONE (PR #40)

**Agent:** modular-builder

**Files:**
- Modify: `.claude/agents/design-system-architect.md`
- Modify: `.claude/agents/animation-choreographer.md`
- Modify: `.claude/agents/layout-architect.md`
- Modify: `.claude/agents/responsive-strategist.md`
- Modify: `.claude/agents/art-director.md`
- Modify: `.claude/agents/voice-strategist.md`

(component-designer already has these references — skip it.)

- [x] **Step 1: Add design doc references to each agent**

For each of the 6 agents above, find the "Required Context" or equivalent section. If none exists, add one before the Context Budget section. Add:

```markdown
## Required Context

Before starting work, consult these design reference docs where relevant:
- `ai_context/design/UX-REVIEW-CHECKLIST.md` — Prioritized UX quality checklist (use during review)
- `ai_context/design/FONT-PAIRINGS.md` — 20 curated font pairings by mood/use case
- `ai_context/design/COLOR-STRATEGY.md` — Semantic color tokens, dark mode, accessible color pairs
```

Adapt the list per agent — voice-strategist only needs UX checklist (forms/feedback section), not font pairings. art-director needs all three. layout-architect needs UX checklist (layout section) and color strategy.

- [x] **Step 2: Verify references** *(Done: `grep -rl "UX-REVIEW-CHECKLIST" .claude/agents/` returns 7)*

- [x] **Step 3: Commit** *(Done: PR #40)*

---

### Task 5: ~~Archive stale cowork docs~~ — SKIPPED (already done)

> **Verified 2026-03-16:** COWORK.md, HANDOFF.md, DISCOVERIES.md already in `docs/archive/`. References in other files are historical context in old plans/specs — not orphaned. `/handoff` command legitimately uses HANDOFF.md as its working file.

---

## Phase 3: Medium Cleanup

### Task 6: ~~Remove dead scripts~~ — SKIPPED (false positive)

> **Verified 2026-03-16:** Observer scripts (`build-watcher.sh`, `drift-detector.sh`) are active hooks registered in `.claude/settings.json`. Gitea scripts (`gitea-create-pr.sh`, `gitea-merge-pr.sh`) are CLI fallbacks when MCP is unavailable. None are dead code.

---

### Task 7: Final verification — DONE (PR #40)

All checks passed:
- [x] Agent count: 36 (CLAUDE.md matches `ls .claude/agents/*.md | wc -l`)
- [x] Command count: 35 (CLAUDE.md matches `ls .claude/commands/*.md | wc -l`)
- [x] Synthesis Guard: all 36 agents have Context Budget sections
- [x] Design doc coverage: 7/7 design agents reference UX-REVIEW-CHECKLIST
- [x] content-researcher: `research` in routing-matrix.yaml
- [x] Cowork docs: properly archived in `docs/archive/`

---

## Summary

| Phase | Tasks | Status | Notes |
|-------|-------|--------|-------|
| 1: Critical | Task 1: Fix counts | DONE (PR #40) | CLAUDE.md + llms.txt updated |
| 1: Critical | Task 2: Fix routing | SKIPPED | False positive — already correct |
| 2: High | Task 3: Synthesis Guard | SKIPPED | False positive — all agents have it |
| 2: High | Task 4: Wire design docs | DONE (PR #40) | 6 agents updated, 7/7 coverage |
| 2: High | Task 5: Archive cowork | SKIPPED | Already archived |
| 3: Medium | Task 6: Remove dead scripts | SKIPPED | Not dead — active hooks |
| 3: Medium | Task 7: Verification | DONE | All checks pass |

**Executed:** 3 of 7 tasks. **Skipped:** 4 tasks (false positives from scout scan).
**Lesson:** Always verify scout findings before acting — 57% false positive rate in this scan.
