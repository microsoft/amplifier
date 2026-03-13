#!/usr/bin/env bash
# cost-tracker.sh — Observer: session summary with observation counts
#
# Triggered by: Stop (SessionEnd) hook
# Input: JSON on stdin from Claude Code hooks API (consumed but not used)
# Reads from: /tmp/amplifier-observations.jsonl
# Writes to: /tmp/amplifier-session-cost.jsonl

set -euo pipefail

# Consume stdin
cat > /dev/null

OBS_FILE="/tmp/amplifier-observations.jsonl"
COST_FILE="/tmp/amplifier-session-cost.jsonl"
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")

# Count observations from this session
TOTAL_OBS=0
ERROR_OBS=0
WARN_OBS=0

if [[ -f "$OBS_FILE" && -s "$OBS_FILE" ]]; then
    TOTAL_OBS=$(wc -l < "$OBS_FILE" | tr -d '[:space:]')
    ERROR_OBS=$(grep -c '"severity":"error"' "$OBS_FILE" || true)
    WARN_OBS=$(grep -c '"severity":"warn"' "$OBS_FILE" || true)
fi
# Ensure numeric values (default 0 if empty)
TOTAL_OBS=${TOTAL_OBS:-0}
ERROR_OBS=${ERROR_OBS:-0}
WARN_OBS=${WARN_OBS:-0}

# Write session cost summary using jq for safe JSON
jq -n -c \
    --arg ts "$TS" \
    --arg observer "cost-tracker" \
    --arg type "session-summary" \
    --argjson total "$TOTAL_OBS" \
    --argjson errors "$ERROR_OBS" \
    --argjson warnings "$WARN_OBS" \
    '{ts: $ts, observer: $observer, type: $type, observations: {total: $total, errors: $errors, warnings: $warnings}}' \
    >> "$COST_FILE"

# Rotate observations file — keep last session only
if [[ -f "$OBS_FILE" ]]; then
    cp "$OBS_FILE" "/tmp/amplifier-observations.prev.jsonl" 2>/dev/null || true
    : > "$OBS_FILE"
fi

# Notify if session had errors
if [[ "$ERROR_OBS" -gt 0 && -n "${NTFY_TOPIC:-}" ]]; then
    bash "$(dirname "$0")/../notify.sh" "Session Summary" "Session ended with ${ERROR_OBS} error(s), ${WARN_OBS} warning(s)" 3 2>/dev/null || true
fi
