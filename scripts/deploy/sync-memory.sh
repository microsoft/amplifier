#!/bin/bash
# Sync recall sessions and auto-memory between Windows and Ubuntu.
# Run from Windows (Git Bash) to bidirectionally sync with the Ubuntu VM.
#
# What syncs:
#   - Recall sessions (~/.claude/recall-sessions/*.md) — extracted markdown, portable
#   - Auto-memory (~/.claude/projects/*/memory/) — markdown files, portable
#
# What stays per-machine:
#   - recall-index.sqlite (FTS5, sessions are machine-local)
#   - docs-index.sqlite (each machine indexes its own repos)
#   - docs-registry.md (derived from docs index)
#
# Usage:
#   bash scripts/deploy/sync-memory.sh [REMOTE_HOST]

set -euo pipefail

REMOTE="${1:-claude@172.31.250.2}"
CLAUDE_DIR="$HOME/.claude"

echo "=== Memory Sync: $(hostname) <-> $REMOTE ==="
echo ""

# --- Recall sessions (bidirectional) ---
echo "[1/4] Push recall sessions → remote..."
mkdir -p "$CLAUDE_DIR/recall-sessions/"
ssh "$REMOTE" "mkdir -p ~/.claude/recall-sessions/" 2>/dev/null || true
rsync -avz "$CLAUDE_DIR/recall-sessions/" "$REMOTE:~/.claude/recall-sessions/" 2>/dev/null || echo "  (no recall sessions to push)"

echo "[2/4] Pull recall sessions ← remote..."
rsync -avz "$REMOTE:~/.claude/recall-sessions/" "$CLAUDE_DIR/recall-sessions/" 2>/dev/null || echo "  (no recall sessions to pull)"

# --- Auto-memory (bidirectional, update-only to avoid overwrites) ---
echo "[3/4] Push auto-memory → remote..."
if ls "$CLAUDE_DIR"/projects/*/memory/ >/dev/null 2>&1; then
  for memdir in "$CLAUDE_DIR"/projects/*/memory/; do
    # Extract the project key (e.g., C--claude-amplifier)
    project_key=$(basename "$(dirname "$memdir")")
    rsync -avzu "$memdir" "$REMOTE:~/.claude/projects/$project_key/memory/" 2>/dev/null || true
  done
else
  echo "  (no auto-memory directories found)"
fi

echo "[4/4] Pull auto-memory ← remote..."
# Get list of remote project memory dirs
remote_projects=$(ssh "$REMOTE" 'ls -d ~/.claude/projects/*/memory/ 2>/dev/null | while read d; do basename "$(dirname "$d")"; done' 2>/dev/null || true)
if [ -n "$remote_projects" ]; then
  for project_key in $remote_projects; do
    mkdir -p "$CLAUDE_DIR/projects/$project_key/memory/"
    rsync -avzu "$REMOTE:~/.claude/projects/$project_key/memory/" "$CLAUDE_DIR/projects/$project_key/memory/" 2>/dev/null || true
  done
else
  echo "  (no remote auto-memory to pull)"
fi

echo ""
echo "=== Sync complete ==="

# Show counts
local_sessions=$(ls "$CLAUDE_DIR/recall-sessions/"*.md 2>/dev/null | wc -l)
echo "Local recall sessions: $local_sessions"

local_memory=$(find "$CLAUDE_DIR/projects/" -path "*/memory/*.md" 2>/dev/null | wc -l)
echo "Local auto-memory files: $local_memory"
