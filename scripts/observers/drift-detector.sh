#!/usr/bin/env bash
# drift-detector.sh — Observer: detects uncommitted work and stale branches at session start
#
# Triggered by: SessionStart
# Writes to: /tmp/amplifier-observations.jsonl
#
# Checks for: uncommitted changes, stale branches, diverged remotes

set -euo pipefail

OBS_FILE="/tmp/amplifier-observations.jsonl"
REPO_ROOT="${REPO_ROOT:-C:/claude/amplifier}"
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")

cd "$REPO_ROOT" 2>/dev/null || exit 0

# Check uncommitted changes
DIRTY_COUNT=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [[ "$DIRTY_COUNT" -gt 0 ]]; then
    printf '{"ts":"%s","observer":"drift-detector","severity":"info","message":"Uncommitted changes: %s files","context":{"dirty_count":%s,"branch":"%s"}}\n' \
        "$TS" "$DIRTY_COUNT" "$DIRTY_COUNT" "$(git branch --show-current 2>/dev/null)" >> "$OBS_FILE"
fi

# Check for branches with gone upstream
GONE_BRANCHES=$(git branch -vv 2>/dev/null | grep ': gone]' | awk '{print $1}' | tr '\n' ',' | sed 's/,$//')
if [[ -n "$GONE_BRANCHES" ]]; then
    printf '{"ts":"%s","observer":"drift-detector","severity":"warn","message":"Stale branches (remote deleted): %s","context":{"branches":"%s"}}\n' \
        "$TS" "$GONE_BRANCHES" "$GONE_BRANCHES" >> "$OBS_FILE"
fi

# Check if current branch is behind remote
BEHIND=$(git rev-list --count HEAD..@{upstream} 2>/dev/null || echo "0")
if [[ "$BEHIND" -gt 0 ]]; then
    BRANCH=$(git branch --show-current 2>/dev/null)
    printf '{"ts":"%s","observer":"drift-detector","severity":"warn","message":"Branch %s is %s commits behind remote","context":{"branch":"%s","behind":%s}}\n' \
        "$TS" "$BRANCH" "$BEHIND" "$BRANCH" "$BEHIND" >> "$OBS_FILE"
fi
