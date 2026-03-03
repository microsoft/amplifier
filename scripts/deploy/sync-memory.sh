#!/bin/bash
# Sync recall sessions and auto-memory between Windows and Ubuntu.
# Run from either machine to bidirectionally sync with the other.
#
# Uses scp (universally available) instead of rsync (not in Git Bash).
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
REMOTE_HOME=$(ssh "$REMOTE" 'echo $HOME' 2>/dev/null)
CLAUDE_DIR="$HOME/.claude"

echo "=== Memory Sync: $(hostname) <-> $REMOTE ==="
echo ""

# --- Recall sessions (bidirectional) ---
echo "[1/4] Push recall sessions → remote..."
mkdir -p "$CLAUDE_DIR/recall-sessions/"
ssh "$REMOTE" "mkdir -p ~/.claude/recall-sessions/" 2>/dev/null || true
LOCAL_COUNT=$(ls "$CLAUDE_DIR/recall-sessions/"*.md 2>/dev/null | wc -l)
if [ "$LOCAL_COUNT" -gt 0 ]; then
  scp -q "$CLAUDE_DIR/recall-sessions/"*.md "$REMOTE:$REMOTE_HOME/.claude/recall-sessions/" 2>/dev/null
  echo "  Pushed $LOCAL_COUNT session files"
else
  echo "  (no local recall sessions)"
fi

echo "[2/4] Pull recall sessions ← remote..."
REMOTE_FILES=$(ssh "$REMOTE" 'ls ~/.claude/recall-sessions/*.md 2>/dev/null' || true)
if [ -n "$REMOTE_FILES" ]; then
  scp -q "$REMOTE:$REMOTE_HOME/.claude/recall-sessions/"*.md "$CLAUDE_DIR/recall-sessions/" 2>/dev/null
  PULLED=$(echo "$REMOTE_FILES" | wc -l)
  echo "  Pulled $PULLED session files"
else
  echo "  (no remote recall sessions)"
fi

# --- Auto-memory (bidirectional) ---
echo "[3/4] Push auto-memory → remote..."
PUSHED_MEM=0
if ls "$CLAUDE_DIR"/projects/*/memory/ >/dev/null 2>&1; then
  for memdir in "$CLAUDE_DIR"/projects/*/memory/; do
    project_key=$(basename "$(dirname "$memdir")")
    # Only push if there are .md files
    if ls "$memdir"*.md >/dev/null 2>&1; then
      ssh "$REMOTE" "mkdir -p ~/.claude/projects/$project_key/memory/" 2>/dev/null || true
      scp -q "$memdir"*.md "$REMOTE:$REMOTE_HOME/.claude/projects/$project_key/memory/" 2>/dev/null || true
      PUSHED_MEM=$((PUSHED_MEM + 1))
    fi
  done
  echo "  Pushed $PUSHED_MEM project memory dirs"
else
  echo "  (no auto-memory directories found)"
fi

echo "[4/4] Pull auto-memory ← remote..."
remote_projects=$(ssh "$REMOTE" 'ls -d ~/.claude/projects/*/memory/ 2>/dev/null | while read d; do basename "$(dirname "$d")"; done' 2>/dev/null || true)
PULLED_MEM=0
if [ -n "$remote_projects" ]; then
  for project_key in $remote_projects; do
    mkdir -p "$CLAUDE_DIR/projects/$project_key/memory/"
    REMOTE_MD=$(ssh "$REMOTE" "ls ~/.claude/projects/$project_key/memory/*.md 2>/dev/null" || true)
    if [ -n "$REMOTE_MD" ]; then
      scp -q "$REMOTE:$REMOTE_HOME/.claude/projects/$project_key/memory/"*.md "$CLAUDE_DIR/projects/$project_key/memory/" 2>/dev/null || true
      PULLED_MEM=$((PULLED_MEM + 1))
    fi
  done
  echo "  Pulled $PULLED_MEM project memory dirs"
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
