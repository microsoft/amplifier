#!/usr/bin/env bash
# build-watcher.sh — Observer: detects build/test failures from Bash tool output
#
# Triggered by: PostToolUse(Bash) hook
# Input: JSON on stdin from Claude Code hooks API
#   { tool_name, tool_input: { command }, tool_response: ... }
# Writes to: /tmp/amplifier-observations.jsonl

set -euo pipefail

OBS_FILE="/tmp/amplifier-observations.jsonl"

# Read hook input from stdin
INPUT=$(cat)

# Extract command and full response text
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null) || true
RESPONSE=$(echo "$INPUT" | jq -r '.tool_response | if type == "string" then . elif type == "object" then tostring else empty end' 2>/dev/null) || true

# Skip if no response to analyze
if [[ -z "$RESPONSE" ]]; then
    exit 0
fi

# Detect exit code from response text (Claude Code includes "Exit code N" in output)
EXIT_CODE=""
if echo "$RESPONSE" | grep -qoiE "Exit code [1-9][0-9]*"; then
    EXIT_CODE=$(echo "$RESPONSE" | grep -oiE "Exit code [0-9]+" | head -1 | grep -oE "[0-9]+" | tail -1)
fi

# Also check for error patterns even without explicit exit code
HAS_ERRORS=false
if echo "$RESPONSE" | grep -qiE "FAILED.*tests?|pytest.*failed|npm ERR|build failed|compilation error|error TS[0-9]"; then
    HAS_ERRORS=true
fi

# No failure signals — exit silently
if [[ -z "$EXIT_CODE" && "$HAS_ERRORS" == "false" ]]; then
    exit 0
fi

# Determine severity
SEVERITY="info"
MESSAGE="Command may have issues"

if [[ -n "$EXIT_CODE" ]]; then
    MESSAGE="Command failed with exit code ${EXIT_CODE}"
    SEVERITY="warn"
fi

if [[ "$HAS_ERRORS" == "true" ]]; then
    SEVERITY="error"
    MESSAGE="Build/test failure detected${EXIT_CODE:+ (exit code ${EXIT_CODE})}"
fi

# Extract first meaningful error line
ERROR_LINE=$(echo "$RESPONSE" | grep -iE "error|FAIL|exception" | head -1 | cut -c1-200 || true)

# Write observation using jq for safe JSON
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
jq -n -c \
    --arg ts "$TS" \
    --arg observer "build-watcher" \
    --arg severity "$SEVERITY" \
    --arg message "$MESSAGE" \
    --arg command "${COMMAND:-unknown}" \
    --arg error_line "${ERROR_LINE:-}" \
    '{ts: $ts, observer: $observer, severity: $severity, message: $message, context: {command: $command, error_line: $error_line}}' \
    >> "$OBS_FILE"

# Push notification for errors
if [[ "$SEVERITY" == "error" && -n "${NTFY_TOPIC:-}" ]]; then
    bash "$(dirname "$0")/../notify.sh" "Build Failure" "$MESSAGE" 4 2>/dev/null || true
fi
