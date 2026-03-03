#!/bin/bash
# Auto-index Claude Code sessions and docs into FTS5 on session end.
# Runs as a Stop hook — keep it fast (timeout 30s).

AMPLIFIER_DIR="C:/claude/amplifier"
cd "$AMPLIFIER_DIR" || exit 0

# Index recent sessions (last 3 days covers any session that just ended)
uv run python scripts/recall/extract-sessions.py --days 3 2>/dev/null

# Index recently modified docs (last 3 days)
uv run python scripts/recall/extract-docs.py --recent 3 2>/dev/null

# Regenerate doc registry for cold-start context
uv run python scripts/recall/generate-doc-registry.py 2>/dev/null

# Log completion
mkdir -p tmp
echo "$(date -Iseconds) recall-index: sessions+docs done" >> tmp/recall-index.log
