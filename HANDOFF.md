# Amplifier Cowork — Task Handoff

## Dispatch Status: IDLE

> **Protocol:** Only the designated receiver should act.
> - Claude acts on: `IDLE`, `PR_READY`, `REVIEWING`, `DEPLOYING`
> - Gemini acts on: `WAITING_FOR_GEMINI`

## State Transitions

```
IDLE ──(Claude writes task)──→ WAITING_FOR_GEMINI
WAITING_FOR_GEMINI ──(Gemini starts)──→ IN_PROGRESS
IN_PROGRESS ──(Gemini pushes PR)──→ PR_READY
PR_READY ──(Claude reviews)──→ REVIEWING
REVIEWING ──(Claude merges/deploys)──→ DEPLOYING
DEPLOYING ──(Claude tests pass)──→ IDLE
```

---

## Current Task

_No active task. Claude: write a task below and set status to WAITING_FOR_GEMINI._

### Task Template (copy when dispatching)

```markdown
## Current Task

**From:** Claude → Gemini
**Branch:** feature/<name>
**Priority:** normal | urgent

### Objective
[One sentence: what to build/fix/change]

### Spec
[Inline spec or link to docs/specs/...]

### Context Loading (use your full 1M context)
Load these files completely before starting:
- [file1 — full file]
- [file2 — full file]
- [file3 — lines X-Y]

### Files YOU May Modify
- [exact/path/to/file1.ext]
- [exact/path/to/file2.ext]

### Files You Must NOT Modify
- .claude/* (always)
- CLAUDE.md (always)
- [any other protected files]

### Acceptance Criteria
- [ ] [testable criterion 1]
- [ ] [testable criterion 2]

### Agent Tier Unlocks
[List any senior-review or design-specialist agents Gemini may use for this task, or "primary + knowledge only"]
```

---

## History

| Date | Direction | Task | PR | Result |
|------|-----------|------|-----|--------|
| 2026-02-16 | Gemini → Claude | Initial cowork setup | — | Agents synced, protocol established |
