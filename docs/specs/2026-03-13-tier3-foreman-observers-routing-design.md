# Tier 3: Routing Matrix + Observers + Foreman

**Date:** 2026-03-13
**Status:** Validated Design
**Author:** Amplifier Design Session

---

## Problem

Amplifier currently uses hardcoded model selections in agent dispatches, has no background monitoring capability, and loses agent context between dispatches. These three patterns address each gap.

## Goal

Implement three complementary patterns in phases:

- **Phase 1: Routing Matrix** — single source of truth for model-to-role mapping
- **Phase 2: Observers** — hook-based background monitoring agents
- **Phase 3: Foreman** — persistent sub-assistant fleet management

---

## Phase 1: Routing Matrix — Transparent Reference

### Design

A YAML config file (`config/routing-matrix.yaml`) serves as the single source of truth for model assignments. The orchestrator reads it behind the scenes. Agent dispatches still show explicit model names (e.g., `model="sonnet"`) — no UX change.

```yaml
roles:
  scout:
    model: haiku
    description: "Quick lookups, context gathering, file searches"
  research:
    model: sonnet
    description: "Codebase exploration, documentation analysis"
  implement:
    model: sonnet
    description: "Code writing, file creation, editing"
  architect:
    model: opus
    description: "System design, complex analysis, deep reasoning"
  review:
    model: sonnet
    description: "Code review, test coverage, security checks"

agents:
  agentic-search: scout
  bug-hunter: architect
  modular-builder: implement
  zen-architect: architect
  code-quality-reviewer: review
  test-coverage: review
  security-guardian: review
  post-task-cleanup: scout
  performance-optimizer: architect
```

### Key Principles

- **Visible UX unchanged** — model names still shown in dispatches
- **One file to update** when switching models globally
- **New agents get a role**, matrix resolves the model

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `config/routing-matrix.yaml` | NEW | The matrix config — single source of truth |
| `AGENTS.md` | MODIFIED | Add reference table linking agents to roles |

---

## Phase 2: Observers — Background Monitoring Agents

### Design

Hook-based observers using Claude Code hooks (shell scripts triggered by events). No polling, no background agents burning context.

### Observer Scripts (`scripts/observers/`)

| Observer | Trigger | What it does |
|----------|---------|--------------|
| `build-watcher.sh` | PostToolUse(Bash) | Detects build/test failures, writes to `/tmp/amplifier-observations.jsonl` |
| `drift-detector.sh` | SessionStart | Compares git status against last session, flags uncommitted work/stale branches |
| `cost-tracker.sh` | PostToolUse(*) | Counts tool calls by type per session, writes summary on SessionEnd |

### Observation Format

```jsonl
{"ts":"2026-03-13T14:22:00Z","observer":"build-watcher","severity":"warn","message":"pytest exit code 1: 2 failures in tests/test_auth.py","context":{"command":"uv run pytest","exit_code":1}}
```

### Hook Registration (`.claude/settings.json`)

```json
{
  "hooks": {
    "PostToolUse": [
      { "matcher": "Bash", "command": "bash scripts/observers/build-watcher.sh" }
    ],
    "SessionEnd": [
      { "command": "bash scripts/observers/session-summary.sh" }
    ]
  }
}
```

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `scripts/observers/build-watcher.sh` | NEW | Detects build/test failures from Bash tool output |
| `scripts/observers/drift-detector.sh` | NEW | Git drift detection on session start |
| `scripts/observers/cost-tracker.sh` | NEW | Tool call counting and session cost summary |
| `.claude/settings.json` | MODIFIED | Hook registration for observer triggers |

---

## Phase 3: Foreman — Persistent Sub-Assistant Fleet

### Design

A `/foreman` command that manages persistent sub-assistants with state across multiple dispatches. Uses file-based session context and the existing Task tool.

### Fleet Manifest (`.foreman/fleet.yaml`)

```yaml
project: "feature/dns-editor"
created: 2026-03-13
assistants:
  api-agent:
    role: implement
    scope: "src/FuseCP.EnterpriseServer/Controllers/DnsController.cs"
    agent_type: modular-builder
    model: sonnet
    status: idle
    last_dispatch: "2026-03-13T14:00:00Z"
    context_file: sessions/api-agent.md
  ui-agent:
    role: implement
    scope: "src/FuseCP.Portal/Pages/Dns/"
    agent_type: modular-builder
    model: sonnet
    status: idle
    context_file: sessions/ui-agent.md
```

### Session Context Files (`.foreman/sessions/*.md`)

Markdown files that accumulate state between dispatches — completed items, in-progress work, key decisions. Each named sub-assistant has its own session file. Updated after every dispatch cycle.

### `/foreman` Command

```
/foreman start <spec>     — create fleet from spec's agent allocation
/foreman status           — show fleet state
/foreman dispatch <name>  — dispatch one sub-assistant with accumulated context
/foreman dispatch all     — dispatch all idle in parallel
/foreman stop             — archive fleet, clean up
```

### Dispatch Flow

1. Read `fleet.yaml` for agent config (type, model, scope)
2. Read `sessions/<name>.md` for accumulated context (prior completions, decisions)
3. Dispatch via Task tool with context injected into the agent prompt
4. Agent works, returns results
5. Update session file with new completions and decisions
6. Update `fleet.yaml` status back to `idle`

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `.claude/commands/foreman.md` | NEW | The `/foreman` command implementation |
| `.foreman/` directory | NEW (gitignored) | Runtime fleet state — fleet.yaml + sessions/ |

---

## Impact

- No breaking changes to existing workflows
- All three phases are independent — each delivers value alone
- Routing matrix is referenced by observers (cost-tracker uses roles) and foreman (model resolution)

---

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Phase 1: Routing Matrix | zen-architect | YAML schema, role definitions |
| Phase 1: Routing Matrix | modular-builder | Create config file, sync script |
| Phase 1: Routing Matrix | spec-reviewer | Verify matrix covers all agents |
| Phase 2: Observers | zen-architect | Observer architecture, hook registration |
| Phase 2: Observers | modular-builder | Shell scripts, JSONL format, settings.json |
| Phase 2: Observers | test-coverage | Verify hooks fire correctly |
| Phase 3: Foreman | module-intent-architect | `/foreman` command spec |
| Phase 3: Foreman | modular-builder | Command, fleet.yaml, session management |
| Phase 3: Foreman | modular-builder | Wire to `/create-plan` agent allocation |
| Phase 3: Foreman | post-task-cleanup | Final hygiene |

---

## Test Plan

- **Phase 1:** Verify YAML parses correctly; all agents in `AGENTS_CATALOG.md` have a role mapping
- **Phase 2:** Manually trigger hooks, verify JSONL output format, verify ntfy integration
- **Phase 3:** Run `/foreman start` with a test spec, dispatch agents, verify session files update

---

## Self-Review Checklist

- [x] All requirements captured from validated design
- [x] File paths concrete and unambiguous
- [x] No ambiguous language — every section specifies exact files and actions
- [x] Three phases are independent and additive
- [x] Routing matrix covers all named agents from the existing catalog
- [x] Observer hook registration matches `.claude/settings.json` schema
- [x] Foreman dispatch flow is step-by-step with no gaps
- [x] Agent allocation table covers all phases
