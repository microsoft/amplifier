#!/bin/bash
# Setup Amplifier skills globally by symlinking commands and agents to ~/.claude/
# Usage: bash scripts/setup-global-skills.sh
# Safe to re-run — idempotent (skips correct symlinks, refreshes broken ones)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$HOME/.claude/backups/$(date +%Y-%m-%d)"

LINKED=0
SKIPPED=0
BACKED_UP=0

link_file() {
    local src="$1"
    local dest="$2"

    # Already a correct symlink — skip
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
        SKIPPED=$((SKIPPED + 1))
        return
    fi

    # Existing file (not a symlink, or wrong target) — back up
    if [ -e "$dest" ] || [ -L "$dest" ]; then
        mkdir -p "$BACKUP_DIR"
        local rel_dir="$(dirname "${dest#$HOME/.claude/}")"
        mkdir -p "$BACKUP_DIR/$rel_dir"
        local backup_name="$(basename "$dest")"
        mv "$dest" "$BACKUP_DIR/$rel_dir/$backup_name"
        echo "  Backed up: $dest"
        BACKED_UP=$((BACKED_UP + 1))
    fi

    # Create parent directory if needed
    mkdir -p "$(dirname "$dest")"

    ln -s "$src" "$dest"
    LINKED=$((LINKED + 1))
}

echo "=== Amplifier Global Skills Setup ==="
echo "Source: $REPO_ROOT"
echo ""

# Symlink commands (top-level .md files)
echo "Commands:"
mkdir -p "$HOME/.claude/commands"
for src in "$REPO_ROOT/.claude/commands/"*.md; do
    [ -f "$src" ] || continue
    dest="$HOME/.claude/commands/$(basename "$src")"
    link_file "$src" "$dest"
    echo "  $(basename "$src")"
done

# Symlink command subdirectories (e.g., commands/ddd/)
for dir in "$REPO_ROOT/.claude/commands/"/*/; do
    [ -d "$dir" ] || continue
    dirname_only="$(basename "$dir")"
    mkdir -p "$HOME/.claude/commands/$dirname_only"
    for src in "$dir"*.md; do
        [ -f "$src" ] || continue
        dest="$HOME/.claude/commands/$dirname_only/$(basename "$src")"
        link_file "$src" "$dest"
        echo "  $dirname_only/$(basename "$src")"
    done
done

# Symlink agents
echo ""
echo "Agents:"
mkdir -p "$HOME/.claude/agents"
for src in "$REPO_ROOT/.claude/agents/"*.md; do
    [ -f "$src" ] || continue
    dest="$HOME/.claude/agents/$(basename "$src")"
    link_file "$src" "$dest"
    echo "  $(basename "$src")"
done

echo ""
echo "=== Done ==="
echo "Linked: $LINKED | Skipped (already correct): $SKIPPED | Backed up: $BACKED_UP"
[ "$BACKED_UP" -gt 0 ] && echo "Backups at: $BACKUP_DIR"
