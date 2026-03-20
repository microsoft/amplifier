#!/usr/bin/env bash
# hooks/post-commit-sync.sh — Auto-sync repo files to plugin marketplace after commit
# Copies changed commands, agents, and hooks to the installed plugin directory.
# Only syncs files that actually changed in the last commit.

PLUGIN_DIR="$HOME/.claude/plugins/marketplaces/amplifier-marketplace/amplifier-core"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

if [ -z "$REPO_ROOT" ] || [ ! -d "$PLUGIN_DIR" ]; then
    exit 0
fi

# Get files changed in last commit
CHANGED=$(git diff --name-only HEAD~1 HEAD 2>/dev/null)
if [ -z "$CHANGED" ]; then
    exit 0
fi

SYNCED=0

# Sync commands
echo "$CHANGED" | grep '^commands/.*\.md$' | while read -r f; do
    if [ -f "$REPO_ROOT/$f" ]; then
        cp "$REPO_ROOT/$f" "$PLUGIN_DIR/$f" 2>/dev/null && SYNCED=$((SYNCED+1))
    fi
done

# Sync hooks
echo "$CHANGED" | grep '^hooks/' | while read -r f; do
    if [ -f "$REPO_ROOT/$f" ]; then
        mkdir -p "$PLUGIN_DIR/hooks"
        cp "$REPO_ROOT/$f" "$PLUGIN_DIR/$f" 2>/dev/null && SYNCED=$((SYNCED+1))
    fi
done

# Fix B: Auto-run frontmatter sync if routing-matrix changed
if echo "$CHANGED" | grep -q 'config/routing-matrix.yaml'; then
    if command -v uv >/dev/null 2>&1 && [ -f "$REPO_ROOT/scripts/sync-agent-frontmatter.py" ]; then
        echo "Amplifier: routing-matrix changed — syncing agent/command frontmatter..."
        cd "$REPO_ROOT" && uv run python scripts/sync-agent-frontmatter.py --commands 2>/dev/null
    fi
fi

exit 0
