#!/usr/bin/env bash
# cost-tracker.sh — Observer: tracks tool call counts per session
#
# Triggered by: Stop (SessionEnd)
# Reads from: /tmp/amplifier-observations.jsonl (build-watcher entries)
# Writes to: /tmp/amplifier-session-cost.jsonl
#
# Produces a session summary with tool call counts and observer activity.

set -euo pipefail

OBS_FILE="/tmp/amplifier-observations.jsonl"
COST_FILE="/tmp/amplifier-session-cost.jsonl"
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")

# Count observations from this session
TOTAL_OBS=0
ERROR_OBS=0
WARN_OBS=0

if [[ -f "$OBS_FILE" ]]; then
    TOTAL_OBS=$(wc -l < "$OBS_FILE" | tr -d ' ')
    ERROR_OBS=$(grep -c '"severity":"error"' "$OBS_FILE" 2>/dev/null || echo "0")
    WARN_OBS=$(grep -c '"severity":"warn"' "$OBS_FILE" 2>/dev/null || echo "0")
fi

# Write session cost summary
printf '{"ts":"%s","observer":"cost-tracker","type":"session-summary","observations":{"total":%s,"errors":%s,"warnings":%s}}\n' \
    "$TS" "$TOTAL_OBS" "$ERROR_OBS" "$WARN_OBS" >> "$COST_FILE"

# Rotate observations file — keep last session only
if [[ -f "$OBS_FILE" ]]; then
    cp "$OBS_FILE" "/tmp/amplifier-observations.prev.jsonl" 2>/dev/null || true
    : > "$OBS_FILE"
fi

# Notify if session had errors
if [[ "$ERROR_OBS" -gt 0 && -n "${NTFY_TOPIC:-}" ]]; then
    bash "$(dirname "$0")/../notify.sh" "Session Summary" "Session ended with ${ERROR_OBS} error(s), ${WARN_OBS} warning(s)" 3 2>/dev/null || true
fi
