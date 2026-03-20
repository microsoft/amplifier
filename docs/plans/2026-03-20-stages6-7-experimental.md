# Stages 6-7: Rate Limit Statusline + MCP Channels — Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add rate limit visibility via statusline and experimental AutoContext push notifications via MCP channels.

**Architecture:** Stage 6 creates a statusline script that reads `rate_limits` from CC 2.1.80. Stage 7 adds `--channels` flag to AutoContext MCP config with a handler hook. Both are opt-in and have explicit rollback paths.

**Tech Stack:** Bash (statusline script, hook), JSON (config)

**Scope Mode:** SCOPE REDUCTION — minimum viable, clear rollback, research notes for future.

---

## Stage 6: Rate Limit Statusline

### Task 6.1 [TRACER]: Research statusline format and create script

**Agent:** modular-builder
**Review:** L1

TRIVIAL EXEMPTION: config + small bash script

Claude Code 2.1.80 exposes `rate_limits` in statusline scripts. The statusline is configured in `~/.claude/settings.json` under the `statusLine` key as a shell command that outputs text.

- [ ] **Step 1:** Read current `~/.claude/settings.json` to find existing `statusLine` config

```bash
grep -A5 'statusLine' ~/.claude/settings.json 2>/dev/null || echo "NO_STATUSLINE_CONFIG"
```

- [ ] **Step 2:** Create `scripts/statusline.sh` — a statusline script that shows rate limit warnings:

```bash
#!/usr/bin/env bash
# scripts/statusline.sh — Amplifier statusline for Claude Code
# Shows rate limit proximity warnings.
# Configured via: "statusLine": "bash /path/to/statusline.sh"
#
# CC 2.1.80+ passes rate_limits as env vars to statusline scripts:
#   RATE_LIMIT_5H_USED_PCT — 5-hour window usage percentage
#   RATE_LIMIT_7D_USED_PCT — 7-day window usage percentage

PCT_5H="${RATE_LIMIT_5H_USED_PCT:-0}"
PCT_7D="${RATE_LIMIT_7D_USED_PCT:-0}"

# Use whichever is higher
PCT="$PCT_5H"
[ "$PCT_7D" -gt "$PCT" ] 2>/dev/null && PCT="$PCT_7D"

if [ "$PCT" -gt 95 ] 2>/dev/null; then
  echo "RATE ${PCT}% IMMINENT"
elif [ "$PCT" -gt 80 ] 2>/dev/null; then
  echo "RATE ${PCT}%"
fi
# Below 80%: output nothing (clean statusline)
```

- [ ] **Step 3:** If the `rate_limits` env vars are NOT available (feature not yet stable), create a placeholder config file instead:

Create `config/statusline-planned.json`:
```json
{
  "_comment": "Planned statusline config — waiting for CC 2.1.80 rate_limits env var stabilization",
  "statusLine": "bash ${AMPLIFIER_HOME}/scripts/statusline.sh",
  "thresholds": {
    "warning": 80,
    "critical": 95
  },
  "env_vars_expected": ["RATE_LIMIT_5H_USED_PCT", "RATE_LIMIT_7D_USED_PCT"],
  "fallback": "StopFailure hook (Stage 4) logs rate limits to failures.jsonl"
}
```

- [ ] **Step 4:** Test the script with simulated values:

```bash
RATE_LIMIT_5H_USED_PCT=85 bash scripts/statusline.sh
# Expected: "RATE 85%"

RATE_LIMIT_5H_USED_PCT=97 bash scripts/statusline.sh
# Expected: "RATE 97% IMMINENT"

RATE_LIMIT_5H_USED_PCT=50 bash scripts/statusline.sh
# Expected: (empty — no output below 80%)
```

- [ ] **Step 5:** Commit

```bash
git add scripts/statusline.sh config/statusline-planned.json
git commit -m "feat: add rate limit statusline script (Stage 6)

Shows warning at >80% and critical at >95% rate limit usage.
Falls back to StopFailure hook if env vars not yet available.
Activate: add statusLine to settings.json pointing to this script."
```

**Rollback:** Remove `statusLine` from settings.json. Zero impact.

---

## Stage 7: MCP Channels for AutoContext (Experimental)

### Task 7.1: Research AutoContext channel support

**Agent:** agentic-search
**Review:** L1 (research only)

- [ ] **Step 1:** Read current `.mcp.json` to understand autocontext server config:

```bash
cat .mcp.json
```

- [ ] **Step 2:** Check AutoContext capabilities:

Call `mcp__autocontext__autocontext_capabilities` to see what the server supports. Look for any mention of channels, push notifications, or event subscriptions.

- [ ] **Step 3:** Check Claude Code `--channels` docs:

```bash
claude --help 2>&1 | grep -i channel
```

- [ ] **Step 4:** Document findings in `ai_context/AUTOCONTEXT-CHANNELS-RESEARCH.md`:

```markdown
# AutoContext MCP Channels Research

**Date:** 2026-03-20
**CC Version:** 2.1.80
**Status:** Research Preview

## Findings

### --channels flag
[Does claude CLI accept --channels? What format?]

### AutoContext push support
[Does AutoContext MCP server support outbound push? What events?]

### Integration path
[How to wire channels: .mcp.json config, hook handler, or both?]

## Conclusion
[Ready to implement / needs more work / not yet possible]

## Next Steps
[Specific actions based on findings]
```

- [ ] **Step 5:** Commit research notes

```bash
git add ai_context/AUTOCONTEXT-CHANNELS-RESEARCH.md
git commit -m "docs: add AutoContext channels research notes (Stage 7)"
```

### Task 7.2: Implement channel infrastructure (if research shows it's feasible)

**Agent:** modular-builder
**Review:** L1

**Precondition:** Only proceed if Task 7.1 confirms channels are supported.

- [ ] **Step 1:** Update `.mcp.json` to add channels flag to autocontext server:

Read `.mcp.json`, add `--channels` to the autocontext server args. Add a comment noting this is experimental:

```json
{
  "mcpServers": {
    "autocontext": {
      "args": ["existing", "args", "--channels"],
      "_note": "EXPERIMENTAL: --channels requires CC 2.1.80+. Remove if causing issues."
    }
  }
}
```

- [ ] **Step 2:** Create `hooks/mcp-channel-handler.sh`:

```bash
#!/usr/bin/env bash
# hooks/mcp-channel-handler.sh — Handle incoming AutoContext channel messages
# Stdin: JSON with {"channel": "...", "payload": {...}}

PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugin-data/amplifier-core}"
mkdir -p "$PLUGIN_DATA"

INPUT=$(cat)

if command -v jq >/dev/null 2>&1; then
  CHANNEL=$(echo "$INPUT" | jq -r '.channel // "unknown"')
else
  CHANNEL=$(echo "$INPUT" | grep -oP '"channel"\s*:\s*"\K[^"]+' || echo "unknown")
fi

case "$CHANNEL" in
  eval.score)
    echo "$INPUT" >> "$PLUGIN_DATA/eval-history.jsonl"
    ;;
  monitor.alert)
    echo "$INPUT" >> "$PLUGIN_DATA/monitor-alerts.jsonl"
    ;;
  improvement.suggestion)
    echo "$INPUT" >> "$PLUGIN_DATA/improvement-queue.jsonl"
    ;;
  *)
    echo "$INPUT" >> "$PLUGIN_DATA/channel-unknown.jsonl"
    ;;
esac

exit 0
```

- [ ] **Step 3:** Register in hooks.json (add to existing array):

Add to `hooks/hooks.json`:
```json
{
  "event": "MCPChannel",
  "server": "autocontext",
  "command": "bash ${CLAUDE_SKILL_DIR}/hooks/mcp-channel-handler.sh"
}
```

- [ ] **Step 4:** Smoke test — pipe a fake channel message:

```bash
echo '{"channel":"eval.score","payload":{"score":87,"task":"test"}}' | bash hooks/mcp-channel-handler.sh
cat "${CLAUDE_PLUGIN_DATA}/eval-history.jsonl"
```

- [ ] **Step 5:** Commit

```bash
git add .mcp.json hooks/mcp-channel-handler.sh hooks/hooks.json
git commit -m "feat: add MCP channels for AutoContext push notifications (experimental)

Stage 7 of CC v2.1.80 improvements. AutoContext can push eval scores,
monitor alerts, and improvement suggestions. Gated behind --channels flag.
Rollback: remove --channels from .mcp.json autocontext args."
```

### Task 7.3: If channels NOT feasible — document gap

**Agent:** modular-builder
**Review:** L1

**Precondition:** Only if Task 7.1 shows channels are not yet supported.

- [ ] **Step 1:** Update `ai_context/AUTOCONTEXT-CHANNELS-RESEARCH.md` with specific gap:

```markdown
## Blockers
- [specific reason channels don't work yet]
- [what CC version or AutoContext version would fix it]

## Infrastructure Ready
The handler script and hooks.json registration are prepared.
When channels become available, enable by adding --channels to .mcp.json.
```

- [ ] **Step 2:** Create the handler script and hooks.json entry anyway (infrastructure-ready):

Same as Task 7.2 Steps 2-3, but WITHOUT modifying .mcp.json (no --channels flag).

- [ ] **Step 3:** Commit

```bash
git add ai_context/AUTOCONTEXT-CHANNELS-RESEARCH.md hooks/mcp-channel-handler.sh hooks/hooks.json
git commit -m "docs: document AutoContext channels gap, prepare infrastructure (Stage 7)

Channels not yet available. Handler script and hook registration ready
for when --channels support stabilizes. See AUTOCONTEXT-CHANNELS-RESEARCH.md."
```

**Rollback:** Delete `hooks/mcp-channel-handler.sh`, remove MCPChannel entry from hooks.json.

---

## Verification Checklist

- [ ] `scripts/statusline.sh` outputs warning at >80%, critical at >95%
- [ ] `scripts/statusline.sh` outputs nothing below 80%
- [ ] `config/statusline-planned.json` documents the intended config
- [ ] `ai_context/AUTOCONTEXT-CHANNELS-RESEARCH.md` has research findings
- [ ] If channels feasible: `.mcp.json` has --channels, handler works, hooks.json updated
- [ ] If channels NOT feasible: infrastructure ready but not activated, gap documented

## Task Count

| Task | What | Checkboxes |
|------|------|------------|
| 6.1 [TRACER] | Statusline script + config | 5 |
| 7.1 | Research channels | 5 |
| 7.2 (conditional) | Implement channels | 5 |
| 7.3 (conditional) | Document gap + prepare infra | 3 |
| **Total** | | **13-18** (depending on path) |

## Wave Analysis

```
Wave 0 (parallel): Task 6.1 + Task 7.1 (independent research)
Wave 1 (conditional): Task 7.2 OR Task 7.3 (based on 7.1 findings)
```
