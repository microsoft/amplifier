#!/usr/bin/env bash
# drift-detector.sh — Observer: detects uncommitted work and stale branches at session start
#
# Triggered by: SessionStart hook
# Input: JSON on stdin from Claude Code hooks API (consumed but not used)
# Writes to: /tmp/amplifier-observations.jsonl

set -euo pipefail

# Require jq for safe JSON output
if ! command -v jq &>/dev/null; then exit 0; fi

# Consume stdin (hooks always pipe JSON, even if we don't need it)
cat > /dev/null

OBS_FILE="/tmp/amplifier-observations.jsonl"
. "$(dirname "$0")/../lib/platform.sh" 2>/dev/null || true
REPO_ROOT="${AMPLIFIER_HOME:?AMPLIFIER_HOME not set}"

cd "$REPO_ROOT" 2>/dev/null || exit 0

TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")

# Check uncommitted changes
DIRTY_COUNT=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [[ "$DIRTY_COUNT" -gt 0 ]]; then
    jq -n -c \
        --arg ts "$TS" \
        --arg observer "drift-detector" \
        --arg severity "info" \
        --arg message "Uncommitted changes: ${DIRTY_COUNT} files" \
        --arg branch "$BRANCH" \
        --argjson dirty "$DIRTY_COUNT" \
        '{ts: $ts, observer: $observer, severity: $severity, message: $message, context: {dirty_count: $dirty, branch: $branch}}' \
        >> "$OBS_FILE"
fi

# Check for branches with gone upstream
GONE_BRANCHES=$(git branch -vv 2>/dev/null | grep ': gone]' | awk '{print $1}' | tr '\n' ',' | sed 's/,$//' || true)
if [[ -n "$GONE_BRANCHES" ]]; then
    jq -n -c \
        --arg ts "$TS" \
        --arg observer "drift-detector" \
        --arg severity "warn" \
        --arg message "Stale branches (remote deleted): ${GONE_BRANCHES}" \
        --arg branches "$GONE_BRANCHES" \
        '{ts: $ts, observer: $observer, severity: $severity, message: $message, context: {branches: $branches}}' \
        >> "$OBS_FILE"
fi

# Check if current branch is behind remote
BEHIND=$(git rev-list --count HEAD..@{upstream} 2>/dev/null || echo "0")
if [[ "$BEHIND" -gt 0 ]]; then
    jq -n -c \
        --arg ts "$TS" \
        --arg observer "drift-detector" \
        --arg severity "warn" \
        --arg message "Branch ${BRANCH} is ${BEHIND} commits behind remote" \
        --arg branch "$BRANCH" \
        --argjson behind "$BEHIND" \
        '{ts: $ts, observer: $observer, severity: $severity, message: $message, context: {branch: $branch, behind: $behind}}' \
        >> "$OBS_FILE"
fi
