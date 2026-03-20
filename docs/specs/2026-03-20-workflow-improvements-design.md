# Workflow Improvements & Self-Improvement Visibility — Design Spec

**Date:** 2026-03-20
**Status:** Ready for /create-plan

## Problem

The Amplifier self-improvement flywheel (commands → eval → improve → CLAUDE.md evolves) generates data but has no visibility layer. Review history, failure logs, agent dispatch stats, and eval scores are scattered across JSONL files with no aggregation or trending. Additionally, 4 manual workflow steps waste time on every session.

## Goal

Add a self-improvement dashboard (HTML + CLI) and automate 4 friction points discovered during the 2026-03-20 development session (6 PRs, 7 stages).

## Part 1: Self-Improvement Dashboard

### Data Sources (already exist)

| Source | Path | Format | What it captures |
|--------|------|--------|-----------------|
| Review history | `${CLAUDE_PLUGIN_DATA}/reviews/history.jsonl` | JSONL | Engine, verdict, finding counts per review |
| Failure log | `${CLAUDE_PLUGIN_DATA}/failures.jsonl` | JSONL | API errors, rate limits, session context |
| Rate limit flags | `${CLAUDE_PLUGIN_DATA}/rate-limit-flag.json` | JSON | Rate limit events |
| Eval history | `${CLAUDE_PLUGIN_DATA}/eval-history.jsonl` | JSONL | AutoContext eval scores (when channels land) |
| Monitor alerts | `${CLAUDE_PLUGIN_DATA}/monitor-alerts.jsonl` | JSONL | AutoContext alerts (when channels land) |
| Git log | `git log` | Native | Commits, PRs, frequency |

### CLI View: Enhance /retro

Add a "Metrics" section to the existing `/retro` command output:

```
AMPLIFIER METRICS (last 7 days)
═══════════════════════════════
Reviews:    12 total | 10 PASS | 2 FAIL (83% pass rate)
  By engine: sonnet: 6 | codex: 4 | gemini: 2
  Findings:  3 P1 | 8 P2 | 15 P3
Failures:   1 rate_limit | 0 auth | 0 network
Sessions:   ~18 (from git log frequency)
Commits:    34 across 6 PRs
Lines:      +2,847 / -412
```

Read from JSONL files, aggregate by time window (24h, 7d, 14d, 30d — matching existing /retro windows).

### HTML Dashboard: amplifier.ergonet.pl/en/dashboard.html

A new page on the docs site with live-generated charts:

**Sections:**
1. **Review Health** — pass/fail rate over time, by engine, finding severity distribution
2. **Agent Activity** — which agents dispatched most, success/fail/blocked counts
3. **Rate Limit Proximity** — timeline of usage percentage (from statusline data if logged)
4. **Failure Log** — recent API errors with timestamps and types
5. **Improvement Score** — self-eval trends over time (placeholder until AutoContext channels land)
6. **Session Velocity** — commits/day, PRs/day, lines changed

**Generation:** Add `dashboard` page to docs manifest. Python script reads JSONL files and generates data for the HTML template. Can regenerate on demand or via cron.

## Part 2: Automation Fixes

### Fix A: Auto-sync plugin marketplace (post-commit hook)

Create `hooks/post-commit-sync.sh`:
- Triggered after every git commit in the amplifier repo
- Copies changed `.md` files from `commands/` and `agents/` to plugin marketplace
- Copies changed `.sh` files from `hooks/` to plugin hooks directory
- Only syncs files that actually changed (git diff --name-only HEAD~1)

Register in `.claude/settings.json` or as a git hook.

### Fix B: Auto-run frontmatter sync on routing-matrix changes

Add to post-commit hook:
- If `config/routing-matrix.yaml` is in the changed files list
- Auto-run `uv run python scripts/sync-agent-frontmatter.py --commands`
- Log what changed

### Fix C: Git workflow — prevent merge conflicts

Add to CLAUDE.md or AGENTS.md:
- Rule: Always `git pull origin main` before creating a feature branch
- Rule: Use `merge` (not squash) for single-commit PRs to avoid duplicate commits
- Rule: For multi-commit PRs, squash is fine

### Fix D: Review history reporter

Create `scripts/review-report.py`:
- Reads `${CLAUDE_PLUGIN_DATA}/reviews/history.jsonl`
- Outputs formatted table with filtering by time window, engine, verdict
- Used by both `/retro` enhancement and dashboard generation

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Research | agentic-search | Read existing /retro command, understand JSONL schemas |
| Dashboard HTML | modular-builder | Create dashboard page template + manifest entry |
| Report script | modular-builder | Build review-report.py aggregation |
| /retro enhancement | modular-builder | Add metrics section to retro command |
| Post-commit hook | modular-builder | Auto-sync plugin + frontmatter |
| Docs integration | modular-builder | Add dashboard to docs generation pipeline |
| Cleanup | post-task-cleanup | Final hygiene pass |

## Files Changed

| File | Action |
|------|--------|
| `scripts/review-report.py` | Create |
| `hooks/post-commit-sync.sh` | Create |
| `commands/retro.md` | Modify (add metrics section) |
| `prompts/dashboard.md` (amplifier-docs) | Create |
| `manifest.json` (amplifier-docs) | Modify (add dashboard page) |
| `CLAUDE.md` or `AGENTS.md` | Modify (add git workflow rules) |

## Estimated Effort

| Part | Tasks | Time |
|------|-------|------|
| Part 1 CLI (/retro + report script) | 3 | ~30 min |
| Part 1 Dashboard (HTML page) | 3 | ~45 min |
| Part 2 Fixes (A-D) | 4 | ~30 min |
| **Total** | **10 tasks** | **~2 hours** |

## Success Criteria

- `/retro 7d` shows review metrics section with real data
- `amplifier.ergonet.pl/en/dashboard.html` renders with charts
- Committing a command file auto-deploys to plugin marketplace
- Changing routing-matrix.yaml auto-syncs agent frontmatter
- No merge conflicts from normal PR workflow
