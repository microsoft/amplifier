# Claude Code v2.1.74-2.1.80 Improvements — Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Leverage 7 new Claude Code features to enforce agent constraints, improve resilience, and enable cross-session intelligence.

**Architecture:** Staged rollout — each stage is independently deployable and testable. Stages 1-2 are mechanical (script-driven frontmatter updates). Stages 3-5 are hook/state infrastructure. Stages 6-7 are observability and experimental.

**Tech Stack:** Python (scripts), Bash (hooks), YAML (frontmatter), JSON (hook registration)

**Scope Mode:** HOLD SCOPE — all 7 features, no more, no less.

---

## Stage 1: Agent Frontmatter Enhancement [TRACER]

**Feature:** Claude Code 2.1.78+ natively enforces `effort`, `maxTurns`, and `disallowedTools` fields in agent frontmatter. This replaces prompt-based "READ-ONLY MODE" instructions with actual engine-level enforcement.

**Why:** Currently, the read-only constraint on scout/research agents is advisory text in the prompt. A misbehaving or confused agent can still call Edit or Write. Native frontmatter enforcement removes this failure mode entirely.

**Agent:** `amplifier-core:modular-builder` (implement role)

**Files to create:**
- `scripts/sync-agent-frontmatter.py`

**Files to modify:**
- All 36 `.md` files in `~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/agents/`

**Role → frontmatter mapping** (derived from `config/routing-matrix.yaml`):

| Role | effort | maxTurns | disallowedTools |
|------|--------|----------|-----------------|
| scout | low | 12 | [Edit, Write, Bash, NotebookEdit] |
| research | medium | 15 | [Edit, Write, Bash, NotebookEdit] |
| implement | medium | 25 | — |
| architect | high | 20 | — |
| review | medium | 15 | — |
| security | high | 15 | — |
| fast | low | 10 | — |

**Agent → role mapping** (from routing-matrix agents section):

| Agent | Role |
|-------|------|
| agentic-search | scout |
| concept-extractor | scout |
| zen-architect | architect |
| module-intent-architect | architect |
| design-system-architect | architect |
| modular-builder | implement |
| bug-hunter | implement |
| integration-specialist | implement |
| api-contract-designer | implement |
| database-architect | implement |
| contract-spec-author | implement |
| component-designer | implement |
| art-director | implement |
| animation-choreographer | implement |
| layout-architect | implement |
| responsive-strategist | implement |
| graph-builder | implement |
| visualization-architect | implement |
| subagent-architect | implement |
| amplifier-cli-architect | implement |
| test-coverage | review |
| spec-reviewer | review |
| code-quality-reviewer | review |
| security-guardian | security |
| content-researcher | research |
| analysis-engine | research |
| insight-synthesizer | research |
| knowledge-archaeologist | research |
| pattern-emergence | research |
| performance-optimizer | research |
| vmware-infrastructure | research |
| ambiguity-guardian | research |
| post-task-cleanup | fast |
| amplifier-expert | fast |
| handoff-gemini | fast |
| voice-strategist | fast |

### Task 1.1 [TRACER]: Write sync-agent-frontmatter.py

- [ ] Create `scripts/sync-agent-frontmatter.py` in the Amplifier repo root
- [ ] Script reads `config/routing-matrix.yaml` to build role → {effort, turns, disallowedTools} map
- [ ] Script reads `config/routing-matrix.yaml` agents section to build agent-name → role map
- [ ] For each `.md` file in the agents directory:
  - [ ] Parse YAML frontmatter between `---` delimiters
  - [ ] Look up agent name in role map (default to `implement` if not found)
  - [ ] Add/update `effort` field from role mapping
  - [ ] Add/update `maxTurns` field from role `turns.default`
  - [ ] For scout/research roles: add `disallowedTools: [Edit, Write, Bash, NotebookEdit]`
  - [ ] For other roles: remove `disallowedTools` if present (don't leave stale values)
  - [ ] Write back preserving all non-frontmatter content exactly
- [ ] Script prints a change report: `agent-name: effort=X, maxTurns=Y [+disallowedTools]` or `(no change)`
- [ ] Script accepts `--dry-run` flag to preview changes without writing
- [ ] Script accepts `--agents-dir` flag to override default path

**Script signature:**
```python
# scripts/sync-agent-frontmatter.py
# Usage: python scripts/sync-agent-frontmatter.py [--dry-run] [--agents-dir PATH]
# Default agents-dir: ~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/agents/
```

**Verification:**
```bash
# Dry run first
python scripts/sync-agent-frontmatter.py --dry-run
# Apply
python scripts/sync-agent-frontmatter.py
# Spot check: agentic-search should have disallowedTools; zen-architect should not
head -10 ~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/agents/agentic-search.md
head -10 ~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/agents/zen-architect.md
```

### Task 1.2: Run sync and commit agent files

- [ ] Run `python scripts/sync-agent-frontmatter.py` and verify all 36 agents updated
- [ ] Confirm scout/research agents have `disallowedTools`
- [ ] Confirm implement/architect/review/security/fast agents do NOT have `disallowedTools`
- [ ] Commit both the script and the updated agent files

**Commit message:**
```
feat: add effort/maxTurns/disallowedTools to agent frontmatter via sync script

Implements Stage 1 of CC v2.1.78 improvements. Native engine enforcement
replaces prompt-based READ-ONLY MODE instructions for scout/research agents.
All 36 agents updated with effort and maxTurns from routing-matrix.yaml.
```

---

## Stage 2: Command Effort Frontmatter

**Feature:** Claude Code 2.1.74+ reads an `effort` field from command frontmatter and auto-sets the session effort level when that command is invoked. No more manual `/effort high` before `/brainstorm`.

**Why:** Users forget to set effort before intensive commands. Auto-setting from frontmatter ensures `/brainstorm` always runs at high effort, `/prime` always runs at low effort, without requiring user action.

**Agent:** `amplifier-core:modular-builder` (implement role)

**Files to modify:**
- All 41 `.md` files in `~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/commands/`

**Command → effort mapping:**

| effort: high | effort: medium | effort: low |
|-------------|----------------|-------------|
| brainstorm | evaluate | guard |
| create-plan | self-eval | platform |
| debug | self-improve | prime |
| design-interface | tdd | recall |
| second-opinion | verify | docs |
| frontend-design | subagent-dev | commit |
| solve | parallel-agents | retro |
| worktree | browser-audit | techdebt |
| — | review-changes | transcripts |
| — | receive-review | — |
| — | request-review | — |
| — | optimize-skill | — |
| — | write-skill | — |
| — | finish-branch | — |
| — | modular-build | — |
| — | improve | — |
| — | foreman | — |
| — | vmware | — |
| — | exchange | — |
| — | handoff | — |
| — | test-browser | — |
| — | test-webapp-ui | — |
| — | visual | — |

### Task 2.1: Extend sync script for commands

- [ ] Add a `sync_commands()` function to `scripts/sync-agent-frontmatter.py` (or create `scripts/sync-command-effort.py` if cleaner)
- [ ] Encode the high/medium/low command lists in the script as a dict
- [ ] For each `.md` file in commands directory:
  - [ ] Parse frontmatter
  - [ ] Look up command name in effort map (default to `medium` if not listed)
  - [ ] Add/update `effort` field
  - [ ] Write back preserving content
- [ ] Print change report per command

**Script invocation:**
```bash
python scripts/sync-agent-frontmatter.py --commands
# or
python scripts/sync-command-effort.py [--dry-run]
```

**Verification:**
```bash
# brainstorm should be high
head -5 ~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/commands/brainstorm.md
# prime should be low
head -5 ~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/commands/prime.md
# evaluate should be medium
head -5 ~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/commands/evaluate.md
```

### Task 2.2: Run command sync and commit

- [ ] Run command sync, verify 41 commands updated
- [ ] Confirm `effort: high` on brainstorm, debug, design-interface, create-plan, second-opinion
- [ ] Confirm `effort: low` on prime, recall, commit, retro, techdebt
- [ ] Commit updated command files

**Commit message:**
```
feat: add effort field to all 41 command frontmatter definitions

Implements Stage 2 of CC v2.1.74 improvements. Commands now auto-set session
effort on invocation — high-effort commands (brainstorm, debug, design-interface)
no longer require manual /effort high before use.
```

---

## Stage 3: Plugin Persistent State (CLAUDE_PLUGIN_DATA)

**Feature:** Claude Code 2.1.76+ provides `${CLAUDE_PLUGIN_DATA}` — a per-plugin persistent directory that survives session restarts. Guard's freeze state and second-opinion's session history should use this instead of `/tmp` or ad-hoc paths.

**Why:** Currently `/guard freeze` state is in-memory only (lost on session end). Second-opinion uses `/tmp` for diff files which are ephemeral. CLAUDE_PLUGIN_DATA gives us a proper, isolated, cross-session state store.

**Agent:** `amplifier-core:modular-builder` (implement role)

**Files to modify:**
- `~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/commands/guard.md`
- `~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/commands/second-opinion.md`

### Task 3.1: Update guard.md for persistent freeze state

- [ ] Read `commands/guard.md` in full
- [ ] Find the "Setting the freeze boundary" section
- [ ] Add a step to persist freeze state: write the canonicalized freeze path to `${CLAUDE_PLUGIN_DATA}/guard-freeze-dir.txt`
- [ ] Add a session-start recovery step: on `/guard` invocation, check if `${CLAUDE_PLUGIN_DATA}/guard-freeze-dir.txt` exists and offer to restore previous freeze boundary
- [ ] On `/guard off` or `/unfreeze`: delete `${CLAUDE_PLUGIN_DATA}/guard-freeze-dir.txt`
- [ ] Ensure the instructions make clear `${CLAUDE_PLUGIN_DATA}` is the plugin's isolated state dir (not a shared path)

**State file behavior:**
```
# Written on /guard freeze <path>
${CLAUDE_PLUGIN_DATA}/guard-freeze-dir.txt → "/absolute/canonicalized/path/"

# On session start / /guard invocation, check for this file
# If exists: "Previous freeze boundary found: <path>. Restore? [y/n]"

# Deleted on /guard off
```

### Task 3.2: Update second-opinion.md for persistent session history

- [ ] Read `commands/second-opinion.md` in full
- [ ] Find all `/tmp/second-opinion-diff-XXXXXX.txt` mktemp calls
- [ ] Replace with `${CLAUDE_PLUGIN_DATA}/second-opinion-sessions/<timestamp>-diff.txt`
- [ ] Add a session log: after each review, append a summary line to `${CLAUDE_PLUGIN_DATA}/second-opinion-sessions/history.jsonl`
- [ ] Each history entry: `{"timestamp": "...", "branch": "...", "verdict": "PASS/FAIL/CONCERNS", "finding_count": N}`
- [ ] Add optional `/second-opinion --history` mode that reads and displays history.jsonl
- [ ] For future telemetry, add a note: `${CLAUDE_PLUGIN_DATA}/telemetry/` reserved for automated instrumentation

**Verification:**
```bash
# After running /guard freeze /some/dir in a session
cat "${CLAUDE_PLUGIN_DATA}/guard-freeze-dir.txt"
# After running /second-opinion
ls "${CLAUDE_PLUGIN_DATA}/second-opinion-sessions/"
```

### Task 3.3: Commit Stage 3 changes

**Commit message:**
```
feat: migrate guard and second-opinion state to CLAUDE_PLUGIN_DATA

Implements Stage 3 of CC v2.1.76 improvements. Guard freeze state now
persists across sessions. Second-opinion builds a reviewable history log.
Both use the isolated CLAUDE_PLUGIN_DATA directory for clean state separation.
```

---

## Stage 4: StopFailure Hook

**Feature:** Claude Code 2.1.77+ fires a `StopFailure` hook when the session ends due to an API error (rate limit, auth failure, network timeout). This feeds into the Failure Classification system.

**Why:** Currently, rate limit hits are silent — the session just stops. With StopFailure, we can log the error type, maintain a failure history, and auto-downshift effort on the next session if rate limiting is the cause.

**Agent:** `amplifier-core:modular-builder` (implement role)

**Files to create:**
- `~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/hooks/stop-failure.sh`
- Update: `~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/hooks/hooks.json`

### Task 4.1: Create stop-failure.sh

- [ ] Create `hooks/stop-failure.sh` in the amplifier-core plugin directory
- [ ] Script reads JSON from stdin (Claude Code passes error details as JSON)
- [ ] Parse fields: `error_type` (rate_limit / auth_failure / network_error / unknown), `message`, `session_id`
- [ ] Log entry to `${CLAUDE_PLUGIN_DATA}/failures.jsonl`:
  ```json
  {"timestamp": "2026-03-20T14:30:00Z", "error_type": "rate_limit", "message": "...", "session_id": "..."}
  ```
- [ ] If `error_type == "rate_limit"`:
  - [ ] Write flag file: `${CLAUDE_PLUGIN_DATA}/rate-limit-flag.json` with timestamp and suggested effort downshift
  - [ ] Content: `{"flagged_at": "...", "suggest_effort": "low", "reason": "rate_limit_on_stop"}`
- [ ] Script must be defensive: use `jq` if available, fall back to grep/sed for parsing
- [ ] Script exits 0 always (hook failures should not block session end)

**Script skeleton:**
```bash
#!/usr/bin/env bash
# hooks/stop-failure.sh — StopFailure hook for Amplifier
# Fires when Claude Code session ends due to API error.
# Stdin: JSON with error details (error_type, message, session_id)
set -euo pipefail

PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugin-data/amplifier-core}"
mkdir -p "$PLUGIN_DATA"

# ... parse stdin JSON, log, set rate-limit flag if needed
exit 0
```

### Task 4.2: Register StopFailure hook in hooks.json

- [ ] Read current `hooks/hooks.json` (or create if missing)
- [ ] Add StopFailure entry alongside any existing hooks:
  ```json
  {
    "hooks": [
      {
        "event": "StopFailure",
        "command": "bash ${CLAUDE_SKILL_DIR}/hooks/stop-failure.sh"
      }
    ]
  }
  ```
- [ ] Verify JSON is valid with `jq . hooks/hooks.json`

### Task 4.3: Update session-start.sh to consume rate-limit flag

- [ ] Read `hooks/session-start.sh` in full
- [ ] After platform detection section, add:
  ```bash
  # Check for rate-limit flag from previous session
  RATE_LIMIT_FLAG="${CLAUDE_PLUGIN_DATA}/rate-limit-flag.json"
  if [[ -f "$RATE_LIMIT_FLAG" ]]; then
    FLAGGED_AT=$(jq -r '.flagged_at' "$RATE_LIMIT_FLAG" 2>/dev/null || echo "unknown")
    echo "⚠️  Rate limit hit at $FLAGGED_AT. Starting with effort=low. Use /effort to override."
    rm -f "$RATE_LIMIT_FLAG"
  fi
  ```
- [ ] Flag is consumed (deleted) on read — not a sticky setting

**Verification:**
```bash
# Manually test by piping fake JSON
echo '{"error_type":"rate_limit","message":"429 Too Many Requests","session_id":"test-123"}' \
  | bash hooks/stop-failure.sh
# Check output
cat "${CLAUDE_PLUGIN_DATA}/failures.jsonl"
cat "${CLAUDE_PLUGIN_DATA}/rate-limit-flag.json"
```

### Task 4.4: Commit Stage 4

**Commit message:**
```
feat: add StopFailure hook for API error logging and rate-limit awareness

Implements Stage 4 of CC v2.1.77 improvements. Failure events now logged to
CLAUDE_PLUGIN_DATA/failures.jsonl. Rate limit hits set a flag that causes
session-start.sh to auto-downshift effort on the next session start.
```

---

## Stage 5: PostCompact Hook

**Feature:** Claude Code 2.1.79+ fires a `PostCompact` hook after automatic context compaction. We use this to auto-update STATE.md so the compressed context captures current project state.

**Why:** After compaction, the new context window starts without project state unless STATE.md was current. Currently, STATE.md is updated manually or on explicit session-end signals. PostCompact makes this automatic and reliable.

**Agent:** `amplifier-core:modular-builder` (implement role)

**Files to create:**
- `~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/hooks/post-compact.sh`
- Update: `~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/hooks/hooks.json`

### Task 5.1: Create post-compact.sh

- [ ] Create `hooks/post-compact.sh` in the amplifier-core plugin directory
- [ ] Script reads compact event JSON from stdin (fields: `tokens_before`, `tokens_after`, `ratio`)
- [ ] Captures current git state:
  ```bash
  RECENT_COMMITS=$(git log --oneline -5 2>/dev/null || echo "(not a git repo)")
  DIFF_STAT=$(git diff --stat 2>/dev/null || echo "(no uncommitted changes)")
  BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
  ```
- [ ] Finds STATE.md: check `$PWD/STATE.md`, then `$(git rev-parse --show-toplevel)/STATE.md`
- [ ] If STATE.md exists: prepend a compaction notice block:
  ```markdown
  ## Context Compacted — 2026-03-20T14:30:00Z

  **Branch:** feature/my-feature
  **Compaction ratio:** 0.18 (tokens reduced from 45000 → 8100)

  ### Recent Commits (at compaction time)
  abc1234 feat: add X
  def5678 fix: correct Y

  ### Uncommitted Changes (at compaction time)
  src/foo.py | 3 ++-
  ```
- [ ] If STATE.md does not exist: create a minimal one with just the compaction block
- [ ] Script exits 0 always

**Script skeleton:**
```bash
#!/usr/bin/env bash
# hooks/post-compact.sh — PostCompact hook for Amplifier
# Fires after Claude Code context compaction.
# Stdin: JSON with {tokens_before, tokens_after, ratio}
set -euo pipefail
# ... capture git state, update STATE.md
exit 0
```

### Task 5.2: Register PostCompact hook in hooks.json

- [ ] Add PostCompact entry to the hooks array in `hooks/hooks.json`:
  ```json
  {
    "event": "PostCompact",
    "command": "bash ${CLAUDE_SKILL_DIR}/hooks/post-compact.sh"
  }
  ```
- [ ] Final `hooks.json` should have both StopFailure and PostCompact registered
- [ ] Verify valid JSON: `jq . hooks/hooks.json`

**Verification:**
```bash
# Manually test
echo '{"tokens_before":45000,"tokens_after":8100,"ratio":0.18}' \
  | bash hooks/post-compact.sh
# Check STATE.md was updated
head -20 STATE.md
```

### Task 5.3: Commit Stage 5

**Commit message:**
```
feat: add PostCompact hook to auto-update STATE.md after context compression

Implements Stage 5 of CC v2.1.79 improvements. STATE.md now auto-captures
git state (branch, recent commits, diff stat) when context compaction fires,
ensuring compressed sessions have accurate recovery context.
```

---

## Stage 6: Rate Limit Awareness in Statusline

**Feature:** Claude Code 2.1.80 exposes a `rate_limits` field in the session statusline. When usage exceeds 80%, the statusline should warn the user and suggest effort downshift.

**Why:** Users currently have no visibility into rate limit proximity until they hit a wall. A statusline indicator gives early warning, allowing proactive effort reduction before StopFailure occurs.

**Agent:** `amplifier-core:amplifier-expert` (fast role — this is a config task)

**Files to create/modify:**
- `~/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core/config/statusline.json` (create if missing)
- Or update existing statusline config in `~/.claude/settings.json`

### Task 6.1: Research statusline config format

- [ ] Read `~/.claude/settings.json` to understand current statusline config
- [ ] Check Claude Code 2.1.80 changelog or docs for `rate_limits` field schema
- [ ] Document the field structure: `rate_limits.used_percentage`, `rate_limits.reset_at`, etc.

### Task 6.2: Implement rate limit statusline indicator

- [ ] If `rate_limits.used_percentage` is available in statusline config expressions:
  - [ ] Add a conditional indicator: when `rate_limits.used_percentage > 80`, show `⚡ {used}% — consider /effort low`
  - [ ] When `> 95%`: show `🔴 {used}% — rate limit imminent`
  - [ ] When `<= 80%`: show nothing (no noise when safe)
- [ ] If statusline config does not support expressions yet (still preview): document the intended config in a comment file at `config/statusline-planned.json` with a TODO note for when the feature stabilizes
- [ ] In either case, add a note in AGENTS.md (Rate Limit Awareness section) referencing the StopFailure hook as the fallback

**Planned statusline config (when feature is stable):**
```json
{
  "statusline": {
    "segments": [
      {
        "condition": "rate_limits.used_percentage > 95",
        "text": "🔴 {rate_limits.used_percentage}% — rate limit imminent",
        "color": "red"
      },
      {
        "condition": "rate_limits.used_percentage > 80",
        "text": "⚡ {rate_limits.used_percentage}% — consider /effort low",
        "color": "yellow"
      }
    ]
  }
}
```

### Task 6.3: Commit Stage 6

**Commit message:**
```
feat: add rate limit statusline config for CC v2.1.80 rate_limits field

Implements Stage 6. Statusline shows warning at >80% rate limit usage and
critical indicator at >95%. Falls back to StopFailure hook logging if the
statusline expression feature is not yet stable.
```

---

## Stage 7: MCP Channels for AutoContext (Experimental)

**Feature:** Claude Code 2.1.80 adds `--channels` support for MCP servers, enabling servers to push messages into the active session. AutoContext can use this to push eval results, improvement suggestions, and monitoring alerts in real time.

**Status:** Research preview — `--channels` flag behavior may change. Implement with explicit opt-in and feature flag.

**Agent:** `amplifier-core:zen-architect` (architect role — design decision required)

**Files to modify:**
- `.mcp.json` in Amplifier repo (add channels to autocontext server config)
- Create: `hooks/mcp-channel-handler.sh` (processes incoming AutoContext messages)
- Create: `config/autocontext-channels.json` (channel subscription config)

### Task 7.1: Research --channels format and AutoContext compatibility

- [ ] Read current `.mcp.json` to understand autocontext server config
- [ ] Review Claude Code 2.1.80 `--channels` documentation (WebFetch or /docs)
- [ ] Review AutoContext MCP server capabilities via `mcp__autocontext__autocontext_capabilities`
- [ ] Document: does AutoContext currently support outbound push? What event types?
- [ ] Identify which AutoContext tools could benefit from push: `autocontext_evaluate_output`, `autocontext_list_monitor_alerts_tool`, `autocontext_get_feedback`

### Task 7.2: Update .mcp.json to enable channels for autocontext

- [ ] Read current `.mcp.json`
- [ ] Add `--channels` flag to the autocontext server args (behind a feature-flag comment)
- [ ] Add channel subscription config: which event types to receive
- [ ] Proposed subscription events:
  - `eval.score` — when `/evaluate` runs, push the score into session
  - `monitor.alert` — when a monitor fires, push alert to session
  - `improvement.suggestion` — periodic improvement hints from distillation

**Config addition:**
```json
{
  "autocontext": {
    "args": ["--channels", "eval.score,monitor.alert,improvement.suggestion"],
    "note": "EXPERIMENTAL: --channels requires CC 2.1.80+. Remove args if causing issues."
  }
}
```

### Task 7.3: Create mcp-channel-handler.sh

- [ ] Create `hooks/mcp-channel-handler.sh`
- [ ] Script reads channel message JSON from stdin: `{"channel": "eval.score", "payload": {...}}`
- [ ] Dispatch by channel type:
  - `eval.score`: log to `${CLAUDE_PLUGIN_DATA}/eval-history.jsonl`, echo score to terminal
  - `monitor.alert`: log to `${CLAUDE_PLUGIN_DATA}/monitor-alerts.jsonl`, echo alert
  - `improvement.suggestion`: append to `${CLAUDE_PLUGIN_DATA}/improvement-queue.jsonl`
- [ ] Register in hooks.json as: `{"event": "MCPChannel", "server": "autocontext", "command": "bash ${CLAUDE_SKILL_DIR}/hooks/mcp-channel-handler.sh"}`

### Task 7.4: Smoke test with eval.score channel

- [ ] Run `/evaluate` command in a session with channels enabled
- [ ] Verify AutoContext pushes a score message
- [ ] Verify `${CLAUDE_PLUGIN_DATA}/eval-history.jsonl` receives the entry
- [ ] If no push received: document the gap in `ai_context/AUTOCONTEXT-CHANNELS-RESEARCH.md` as a known limitation with a follow-up task
- [ ] Either outcome is acceptable — the infrastructure is in place

### Task 7.5: Commit Stage 7

**Commit message:**
```
feat: add MCP channels infrastructure for AutoContext push notifications (experimental)

Implements Stage 7 of CC v2.1.80 improvements. AutoContext can now push eval
scores, monitor alerts, and improvement suggestions into active sessions.
Gated behind explicit --channels flag; remove from .mcp.json args to disable.
```

---

## Rollout Order and Deployment Notes

| Stage | Risk | Rollback | Deploy time |
|-------|------|----------|-------------|
| 1 | Low — additive YAML fields | Re-run script without new fields | ~10 min |
| 2 | Low — additive YAML fields | Re-run script with `effort: medium` for all | ~5 min |
| 3 | Low — changes in-memory behavior | Revert guard.md / second-opinion.md | ~15 min |
| 4 | Low — hook exits 0 always | Remove from hooks.json | ~10 min |
| 5 | Low — hook exits 0 always | Remove from hooks.json | ~10 min |
| 6 | Medium — statusline config format may differ | Remove statusline config | ~15 min |
| 7 | High — experimental feature | Remove `--channels` from .mcp.json args | ~20 min |

**Deploy stages 1-5 first** (low risk, high value). Stage 6 and 7 require testing after each.

## Verification Checklist (Full Rollout)

- [ ] Stage 1: `agentic-search.md` has `disallowedTools: [Edit, Write, Bash, NotebookEdit]`
- [ ] Stage 1: `zen-architect.md` has `effort: high` and `maxTurns: 20`, no disallowedTools
- [ ] Stage 2: `brainstorm.md` has `effort: high`
- [ ] Stage 2: `prime.md` has `effort: low`
- [ ] Stage 3: `/guard freeze /tmp/test` persists to `${CLAUDE_PLUGIN_DATA}/guard-freeze-dir.txt`
- [ ] Stage 3: `/second-opinion` writes to `${CLAUDE_PLUGIN_DATA}/second-opinion-sessions/history.jsonl`
- [ ] Stage 4: `echo '{"error_type":"rate_limit",...}' | bash hooks/stop-failure.sh` → writes failures.jsonl
- [ ] Stage 4: rate-limit-flag.json created; session-start.sh prints downshift warning
- [ ] Stage 5: `echo '{"tokens_before":45000,...}' | bash hooks/post-compact.sh` → STATE.md updated
- [ ] Stage 6: Statusline config valid JSON; indicator logic documented
- [ ] Stage 7: `.mcp.json` has channels flag; handler script exists and is wired

## Task Count Summary

| Stage | Tasks | Total items |
|-------|-------|-------------|
| Stage 1 | 2 tasks (1.1 TRACER, 1.2) | 14 checkboxes |
| Stage 2 | 2 tasks (2.1, 2.2) | 8 checkboxes |
| Stage 3 | 3 tasks (3.1, 3.2, 3.3) | 14 checkboxes |
| Stage 4 | 4 tasks (4.1–4.4) | 16 checkboxes |
| Stage 5 | 3 tasks (5.1–5.3) | 10 checkboxes |
| Stage 6 | 3 tasks (6.1–6.3) | 7 checkboxes |
| Stage 7 | 5 tasks (7.1–7.5) | 16 checkboxes |
| **Total** | **22 tasks** | **85 checkboxes** |
