#!/usr/bin/env bash
# build-watcher.sh — Observer: detects build/test failures from Bash tool output
#
# Triggered by: PostToolUse(Bash)
# Writes to: /tmp/amplifier-observations.jsonl
#
# Reads the tool input/output from environment variables set by Claude Code hooks.
# Looks for exit codes > 0 and common failure patterns.

set -euo pipefail

OBS_FILE="/tmp/amplifier-observations.jsonl"
TOOL_OUTPUT="${TOOL_OUTPUT:-}"
EXIT_CODE="${EXIT_CODE:-0}"
TOOL_INPUT="${TOOL_INPUT:-}"

# Only act on non-zero exit codes
if [[ "$EXIT_CODE" == "0" ]]; then
    exit 0
fi

# Detect build/test failure patterns
SEVERITY="info"
MESSAGE="Command failed with exit code ${EXIT_CODE}"

if echo "$TOOL_OUTPUT" | grep -qiE "FAIL|error|exception|traceback|SyntaxError|TypeError|ImportError"; then
    SEVERITY="warn"
fi

if echo "$TOOL_OUTPUT" | grep -qiE "FAILED.*tests?|pytest.*failed|npm ERR|build failed|compilation error"; then
    SEVERITY="error"
    MESSAGE="Build/test failure detected (exit code ${EXIT_CODE})"
fi

# Extract first meaningful error line
ERROR_LINE=$(echo "$TOOL_OUTPUT" | grep -iE "error|FAIL|exception" | head -1 | cut -c1-200)

# Write observation
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
printf '{"ts":"%s","observer":"build-watcher","severity":"%s","message":"%s","context":{"exit_code":%s,"error_line":"%s"}}\n' \
    "$TS" "$SEVERITY" "$MESSAGE" "$EXIT_CODE" "${ERROR_LINE//\"/\\\"}" >> "$OBS_FILE"

# Push notification for errors
if [[ "$SEVERITY" == "error" && -n "${NTFY_TOPIC:-}" ]]; then
    bash "$(dirname "$0")/../notify.sh" "Build Failure" "$MESSAGE" 4 2>/dev/null || true
fi
