#!/bin/bash
# Amplifier deployment script for Ubuntu Linux.
# Run once to set up Amplifier on a fresh Linux machine.
#
# Usage (from the Linux machine):
#   curl -sSL https://raw.githubusercontent.com/psklarkins/amplifier/main/scripts/deploy/setup-linux.sh | bash
#
# Or run via SSH from Windows:
#   ssh claude@172.31.250.2 'bash -s' < scripts/deploy/setup-linux.sh

set -euo pipefail

AMPLIFIER_DIR="/opt/amplifier"
CLAUDE_DIR="$HOME/.claude"
GITHUB_REPO="https://github.com/psklarkins/amplifier.git"

echo "=========================================="
echo "  Amplifier Linux Setup"
echo "=========================================="
echo ""

# --- Step 1: Install uv ---
echo "[1/8] Installing uv..."
if command -v uv &>/dev/null; then
  echo "  uv already installed: $(uv --version)"
else
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Source the env so uv is available in this session
  export PATH="$HOME/.local/bin:$PATH"
  echo "  uv installed: $(uv --version)"
fi

# --- Step 2: Clone or update amplifier ---
echo "[2/8] Setting up amplifier at $AMPLIFIER_DIR..."
if [ -d "$AMPLIFIER_DIR/.git" ]; then
  echo "  Repository exists, pulling latest..."
  cd "$AMPLIFIER_DIR"
  git pull --ff-only origin main 2>/dev/null || echo "  (pull skipped — may be on a feature branch)"
else
  echo "  Cloning from GitHub..."
  sudo mkdir -p "$AMPLIFIER_DIR"
  sudo chown "$(whoami):$(id -gn)" "$AMPLIFIER_DIR"
  git clone "$GITHUB_REPO" "$AMPLIFIER_DIR"
fi
cd "$AMPLIFIER_DIR"

# --- Step 3: Install Python dependencies ---
echo "[3/8] Installing Python dependencies..."
uv sync 2>/dev/null || echo "  (no pyproject.toml or uv sync not needed)"

# --- Step 4: Deploy Linux CLAUDE.md ---
echo "[4/8] Deploying safety CLAUDE.md..."
if [ -f "$AMPLIFIER_DIR/docs/deploy/linux-CLAUDE.md" ]; then
  cp "$AMPLIFIER_DIR/docs/deploy/linux-CLAUDE.md" "$HOME/CLAUDE.md"
  echo "  Deployed to ~/CLAUDE.md"
else
  cat > "$HOME/CLAUDE.md" << 'HEREDOC'
# CLAUDE.md — Global Safety Rules (Linux)

- All files and folders MUST be created under `/opt/` only.
  Enforced by PreToolUse hook: `/opt/amplifier/scripts/guard-paths-linux.sh`.
- For full tools, agents, and workflow context: `cd /opt/amplifier && claude`.
HEREDOC
  echo "  Created ~/CLAUDE.md (inline fallback)"
fi

# --- Step 5: Make hook scripts executable ---
echo "[5/8] Setting script permissions..."
chmod +x "$AMPLIFIER_DIR/scripts/guard-paths-linux.sh" 2>/dev/null || true
chmod +x "$AMPLIFIER_DIR/.claude/hooks/session-end-index.sh" 2>/dev/null || true
chmod +x "$AMPLIFIER_DIR/scripts/deploy/sync-memory.sh" 2>/dev/null || true

# --- Step 6: Register hooks in ~/.claude/settings.json ---
echo "[6/8] Registering hooks..."
mkdir -p "$CLAUDE_DIR"

SETTINGS_FILE="$CLAUDE_DIR/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
  cp "$SETTINGS_FILE" "${SETTINGS_FILE}.bak"
  echo "  Backed up existing settings to settings.json.bak"
fi

# Merge hooks into existing settings (preserves plugins, preferences, etc.)
HOOKS_JSON=$(cat <<'HOOKEOF'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write",
        "hooks": [{"type": "command", "command": "bash /opt/amplifier/scripts/guard-paths-linux.sh"}]
      },
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "bash /opt/amplifier/scripts/guard-paths-linux.sh"}]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [{"type": "command", "command": "bash /opt/amplifier/.claude/hooks/session-end-index.sh"}]
      }
    ]
  }
}
HOOKEOF
)

if [ -f "${SETTINGS_FILE}.bak" ]; then
  # Merge hooks into existing settings
  jq -s '.[0] * .[1]' "${SETTINGS_FILE}.bak" <(echo "$HOOKS_JSON") > "$SETTINGS_FILE"
  echo "  Merged hooks into existing settings"
else
  echo "$HOOKS_JSON" > "$SETTINGS_FILE"
  echo "  Created settings with hooks"
fi

# --- Step 7: Run initial docs index ---
echo "[7/8] Running initial docs index..."
cd "$AMPLIFIER_DIR"
if [ -f "scripts/recall/extract-docs.py" ]; then
  uv run python scripts/recall/extract-docs.py --full 2>/dev/null && echo "  Docs indexed successfully" || echo "  (docs indexing skipped — may need dependencies)"
fi

# --- Step 8: Consolidate agents ---
echo "[8/8] Consolidating agents..."
# Move any scattered agents into amplifier's agent directory
AMPLIFIER_AGENTS="$AMPLIFIER_DIR/.claude/agents"
MIGRATED=0

for agent_dir in "$HOME/.claude/agents" "/opt/.claude/agents"; do
  if [ -d "$agent_dir" ] && [ "$(ls -A "$agent_dir" 2>/dev/null)" ]; then
    echo "  Found agents in $agent_dir"
    for agent_file in "$agent_dir"/*.md; do
      [ -f "$agent_file" ] || continue
      agent_name=$(basename "$agent_file")
      if [ ! -f "$AMPLIFIER_AGENTS/$agent_name" ]; then
        cp "$agent_file" "$AMPLIFIER_AGENTS/$agent_name"
        echo "    Migrated: $agent_name"
        MIGRATED=$((MIGRATED + 1))
      else
        echo "    Skipped (exists): $agent_name"
      fi
    done
  fi
done

if [ "$MIGRATED" -eq 0 ]; then
  echo "  No new agents to migrate"
fi

# --- Summary ---
echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "  Amplifier:    $AMPLIFIER_DIR"
echo "  Safety rules: ~/CLAUDE.md"
echo "  Hooks:        $SETTINGS_FILE"
echo "  Guard paths:  $AMPLIFIER_DIR/scripts/guard-paths-linux.sh"
echo "  Session hook: $AMPLIFIER_DIR/.claude/hooks/session-end-index.sh"
echo "  Python:       $(uv run python --version 2>/dev/null || echo 'not available')"
echo "  uv:           $(uv --version 2>/dev/null || echo 'not available')"
echo ""
echo "  Agents migrated: $MIGRATED"
echo ""
echo "  Next steps:"
echo "    1. cd /opt/amplifier && claude"
echo "    2. Run /recall to verify memory system works"
echo "    3. Run sync-memory.sh from Windows to sync sessions"
echo ""
