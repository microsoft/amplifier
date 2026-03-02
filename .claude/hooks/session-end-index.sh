#!/bin/bash
# Auto-index Claude Code sessions into recall FTS5 on session end.
# Extracts last 3 days of sessions to markdown, then updates FTS5 index.
# Runs as a SessionEnd hook — keep it fast (timeout 30s).

AMPLIFIER_DIR="C:/claude/amplifier"
cd "$AMPLIFIER_DIR" || exit 0

# Extract recent sessions (last 3 days covers any session that just ended)
uv run python scripts/recall/extract-sessions.py --days 3 2>/dev/null

# Log completion
mkdir -p tmp
echo "$(date -Iseconds) recall-index: done" >> tmp/recall-index.log
