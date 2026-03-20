#!/usr/bin/env bash
# hooks/post-compact.sh — PostCompact hook for Amplifier
# Fires after Claude Code context compaction.
# Stdin: JSON with {tokens_before, tokens_after, ratio}
# Updates STATE.md with compaction notice and current git state.

# Read stdin (compaction details)
INPUT=$(cat)

# Parse with jq if available
if command -v jq >/dev/null 2>&1; then
    TOKENS_BEFORE=$(echo "$INPUT" | jq -r '.tokens_before // "?"' 2>/dev/null)
    TOKENS_AFTER=$(echo "$INPUT" | jq -r '.tokens_after // "?"' 2>/dev/null)
    RATIO=$(echo "$INPUT" | jq -r '.ratio // "?"' 2>/dev/null)
else
    TOKENS_BEFORE="?"
    TOKENS_AFTER="?"
    RATIO="?"
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S")

# Capture git state
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
RECENT_COMMITS=$(git log --oneline -5 2>/dev/null || echo "(not a git repo)")
DIFF_STAT=$(git diff --stat 2>/dev/null || echo "(no uncommitted changes)")

# Find STATE.md
STATE_FILE=""
if [ -f "$PWD/STATE.md" ]; then
    STATE_FILE="$PWD/STATE.md"
else
    TOPLEVEL=$(git rev-parse --show-toplevel 2>/dev/null)
    if [ -n "$TOPLEVEL" ] && [ -f "$TOPLEVEL/STATE.md" ]; then
        STATE_FILE="$TOPLEVEL/STATE.md"
    elif [ -n "$TOPLEVEL" ]; then
        STATE_FILE="$TOPLEVEL/STATE.md"
    fi
fi

# Build compaction block
COMPACT_BLOCK="## Context Compacted — $TIMESTAMP

**Branch:** $BRANCH
**Compaction ratio:** $RATIO (tokens reduced from $TOKENS_BEFORE → $TOKENS_AFTER)

### Recent Commits (at compaction time)
$RECENT_COMMITS

### Uncommitted Changes (at compaction time)
$DIFF_STAT

---
"

if [ -n "$STATE_FILE" ] && [ -f "$STATE_FILE" ]; then
    # Prepend compaction block to existing STATE.md
    EXISTING=$(cat "$STATE_FILE")
    printf '%s\n\n%s' "$COMPACT_BLOCK" "$EXISTING" > "$STATE_FILE"
elif [ -n "$STATE_FILE" ]; then
    # Create minimal STATE.md
    printf '# Project State\n\n%s' "$COMPACT_BLOCK" > "$STATE_FILE"
fi

exit 0
