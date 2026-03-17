# Unified Frontend Design Skill

**Date:** 2026-03-17
**Status:** Implementing
**Branch:** feat/web-code-antipatterns

## Problem

Amplifier has 7 separate design agents + a `/designer` router + a plugin-based `/frontend-design` skill, but none carry anti-slop awareness or per-project design context. Meanwhile, the Impeccable Style package has 19 excellent design skills with AI fingerprint detection, but exists as a separate installation with no Amplifier integration.

## Goal

Create a single unified `/frontend-design` command that:
1. Absorbs the best of Impeccable's anti-slop engine (AI Slop Test, DO/DON'T guidelines, reference docs)
2. Integrates with Amplifier's design philosophy (Nine Dimensions, Five Pillars)
3. Provides 14 modes covering creation, refinement, evaluation, and aesthetic control
4. Uses a per-project `.impeccable.md` file for persistent design context
5. Dispatches to the right model tier per mode (haiku for audit, sonnet for implementation, opus for overdrive)

## Changes

### New Files
| File | Purpose |
|------|---------|
| `.claude/commands/frontend-design.md` | Unified command — mode parser, context protocol, 14 mode procedures |
| `.claude/skills/frontend-design/SKILL.md` | Core principles — AI Slop Test, DO/DON'T, dimensions checklist |
| `.claude/skills/frontend-design/reference/typography.md` | Typography + font pairings (merged) |
| `.claude/skills/frontend-design/reference/color-and-contrast.md` | Color + token strategy (merged) |
| `.claude/skills/frontend-design/reference/spatial-design.md` | Spatial design (from Impeccable) |
| `.claude/skills/frontend-design/reference/motion-design.md` | Motion design (from Impeccable) |
| `.claude/skills/frontend-design/reference/interaction-design.md` | Interaction patterns (from Impeccable) |
| `.claude/skills/frontend-design/reference/responsive-design.md` | Responsive strategy (from Impeccable) |
| `.claude/skills/frontend-design/reference/ux-writing.md` | UX writing (from Impeccable) |

### Modified Files
| File | Change |
|------|--------|
| `CLAUDE.md` | Add `/frontend-design` to command table |

### Modes
build (default), teach, polish, audit, critique, harden, animate, typeset, colorize, arrange, bolder, quieter, distill, overdrive

### Dropped (from Impeccable)
extract, normalize, delight, onboard, optimize, clarify, adapt — overlap with existing Amplifier agents or too niche

## Impact
- Existing design agents untouched — still available for direct dispatch
- `/designer` command stays — alternative path for non-frontend work
- New recommended path for all frontend work: `/frontend-design`

## Agent Allocation
| Phase | Agent | Model |
|-------|-------|-------|
| Reference docs | modular-builder | sonnet |
| Core SKILL.md | modular-builder | sonnet |
| Command file | modular-builder | opus |
| Doc updates | modular-builder | sonnet |
| Quality review | code-quality-reviewer | sonnet |

## Test Plan
- [ ] `/frontend-design` with no args → enters build mode, asks what to create
- [ ] `/frontend-design teach` → runs context gathering dialogue
- [ ] `/frontend-design audit` → produces read-only quality report
- [ ] `/frontend-design polish ComponentName` → applies polish to target
- [ ] `/frontend-design harden` → checks production resilience
- [ ] Context protocol works: finds .impeccable.md when present
- [ ] Context protocol works: prompts teach mode when .impeccable.md missing
- [ ] Reference docs are loadable by subagents (no broken paths)

## Source Attribution
Based on Impeccable Style Universal (Apache 2.0) by https://impeccable.style
