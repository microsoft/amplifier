#!/bin/bash
# Auto-index Claude Code sessions and docs into FTS5 on session end.
# Runs as a Stop hook — keep it fast (timeout 30s).

# Auto-detect amplifier directory (cross-platform)
if [ -d "C:/claude/amplifier" ]; then
  AMPLIFIER_DIR="C:/claude/amplifier"
elif [ -d "/opt/amplifier" ]; then
  AMPLIFIER_DIR="/opt/amplifier"
else
  exit 0
fi
cd "$AMPLIFIER_DIR" || exit 0

# Index sessions, docs, and regenerate registry in one Python process
uv run python scripts/recall/index-all.py 2>/dev/null

# Log completion
mkdir -p tmp
echo "$(date -Iseconds) recall-index: sessions+docs done" >> tmp/recall-index.log
