#!/usr/bin/env bash
# hooks/stop-failure.sh — StopFailure hook for Amplifier
# Fires when Claude Code session ends due to API error (rate limit, auth, network).
# Stdin: JSON with error details
# Logs to CLAUDE_PLUGIN_DATA/failures.jsonl
# Sets rate-limit flag for session-start.sh to consume

PLUGIN_DATA="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugin-data/amplifier-core}"
mkdir -p "$PLUGIN_DATA"

# Read stdin
INPUT=$(cat)

# Parse with jq if available, fall back to grep
if command -v jq >/dev/null 2>&1; then
    ERROR_TYPE=$(echo "$INPUT" | jq -r '.error_type // "unknown"' 2>/dev/null)
    MESSAGE=$(echo "$INPUT" | jq -r '.message // ""' 2>/dev/null)
    SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // ""' 2>/dev/null)
else
    ERROR_TYPE=$(echo "$INPUT" | grep -oP '"error_type"\s*:\s*"\K[^"]+' 2>/dev/null || echo "unknown")
    MESSAGE=$(echo "$INPUT" | grep -oP '"message"\s*:\s*"\K[^"]+' 2>/dev/null || echo "")
    SESSION_ID=$(echo "$INPUT" | grep -oP '"session_id"\s*:\s*"\K[^"]+' 2>/dev/null || echo "")
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S")

# Log to failures.jsonl
echo "{\"timestamp\":\"$TIMESTAMP\",\"error_type\":\"$ERROR_TYPE\",\"message\":\"$MESSAGE\",\"session_id\":\"$SESSION_ID\"}" \
    >> "$PLUGIN_DATA/failures.jsonl" 2>/dev/null

# Set rate-limit flag if applicable
if [ "$ERROR_TYPE" = "rate_limit" ]; then
    cat > "$PLUGIN_DATA/rate-limit-flag.json" 2>/dev/null <<FLAGEOF
{"flagged_at":"$TIMESTAMP","suggest_effort":"low","reason":"rate_limit_on_stop"}
FLAGEOF
fi

exit 0
