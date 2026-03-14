#!/bin/bash
# Auto-index Claude Code sessions and docs into FTS5 on session end.
# Runs as a Stop hook — keep it fast (timeout 30s).

AMPLIFIER_DIR="${AMPLIFIER_HOME:-/opt/amplifier}"
cd "$AMPLIFIER_DIR" || exit 0

# Index sessions, docs, and regenerate registry in one Python process
uv run python scripts/recall/index-all.py 2>/dev/null

# Log completion
mkdir -p tmp
echo "$(date -Iseconds) recall-index: sessions+docs done" >> tmp/recall-index.log
