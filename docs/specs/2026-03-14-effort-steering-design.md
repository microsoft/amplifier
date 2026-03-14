# Effort Steering — Automated, Adaptive Effort Control for Amplifier

**Date:** 2026-03-14
**Status:** Approved for Phase A implementation
**Branch:** feature/effort-steering

---

## Problem

Amplifier dispatches agents with fixed `max_turns` budgets that don't match task complexity. A simple file rename gets the same 25-turn budget as a complex refactor. No reasoning effort control — all tasks get the same thinking depth regardless of complexity.

## Goal

Add three-layer effort control: session level (`/effort` switch), role level (routing-matrix), and task level (signal-based). Elastic turn budgets replace fixed numbers. Self-improvement loop via AutoContext learns optimal effort per task type over time.

---

## Phase A: Effort Tiers + Elastic Turns (implement now)

### Routing Matrix Extension

Add `effort` field and replace fixed `max_turns` with `turns: {min, default, max}` range per role:

```yaml
roles:
  scout:
    model: haiku
    effort: low
    turns: { min: 8, default: 12, max: 20 }
  research:
    model: sonnet
    effort: medium
    turns: { min: 10, default: 15, max: 25 }
  implement:
    model: sonnet
    effort: medium
    turns: { min: 15, default: 25, max: 40 }
  architect:
    model: opus
    effort: high
    turns: { min: 15, default: 20, max: 35 }
  review:
    model: sonnet
    effort: medium
    turns: { min: 10, default: 15, max: 25 }
  security:
    model: opus
    effort: high
    turns: { min: 12, default: 15, max: 25 }
  fast:
    model: haiku
    effort: low
    turns: { min: 5, default: 10, max: 15 }
```

### Three-Layer Effort Resolution

```
Session level:  /effort (user sets globally — low/medium/high/max)
Role level:     routing-matrix.yaml effort field (per agent role)
Task level:     signal-based adjustment (per dispatch)

resolved_effort = min(session_effort, max(role_effort, task_signals))
```

### /effort Mapping

| /effort | Extended thinking | Turn budget position | When |
|---------|------------------|---------------------|------|
| low | Minimal | min turns | Quick edits, config |
| medium | Standard | default turns | Normal dev work |
| high | Deep | max turns | Complex features |
| max | Maximum | max turns + auto-resume | Architecture, security |

When effort resolves to `max`: turn budget = role's max, auto-resume up to 3 cycles without asking.

### AGENTS.md Updates

Replace fixed Turn Budgets table with elastic ranges. Add effort tier column.

### CLAUDE.md Updates

Add effort steering guidance to Operating Principles.

---

## Phase B: Dynamic Effort Detection (future)

Signal-based complexity scoring:

| Signal | Score |
|--------|-------|
| File count 1 | 0 |
| File count 2–4 | +1 |
| File count 5+ | +2 |
| Keywords: security, auth, migration, refactor | +1 |
| Keywords: rename, config, typo | -1 |
| Previous BLOCKED/NEEDS_CONTEXT | +2 |
| TDD steps present | +1 |
| Multi-subsystem (3+ dirs) | +1 |

Score ≤0 → low, 1–2 → medium, ≥3 → high.

---

## Phase C: Adaptive Self-Improvement (future)

Wire `/self-eval` to record effort metadata → AutoContext accumulates patterns → effort resolver reads playbook for learned adjustments.

---

## Files Changed (Phase A only)

| File | Change |
|------|--------|
| `config/routing-matrix.yaml` | Add `effort` field, replace `max_turns` with `turns` range |
| `AGENTS.md` | Update Turn Budgets table with elastic ranges + effort tier |
| `CLAUDE.md` | Add effort steering to Operating Principles |

---

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Routing matrix | modular-builder | Add effort + elastic turns |
| Documentation | modular-builder | Update AGENTS.md + CLAUDE.md |
| Validation | spec-reviewer | Verify consistency |

---

## Test Plan

- [ ] Verify `config/routing-matrix.yaml` parses as valid YAML
- [ ] Verify `AGENTS.md` Turn Budgets table matches routing-matrix values
- [ ] Verify `CLAUDE.md` references effort steering
- [ ] Run `validate-routing-matrix.sh` — 0 errors
