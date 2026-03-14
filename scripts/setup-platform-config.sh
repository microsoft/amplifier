#!/usr/bin/env bash
# Generate platform-specific .claude/settings.json and .mcp.json from templates.
# Run after cloning or when switching platforms.
#
# Usage: bash scripts/setup-platform-config.sh [--force]
#   --force  Overwrite existing configs without prompting

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source platform detection (temporarily relax strict mode for platform.sh)
_saved_home="${AMPLIFIER_HOME:-}"
unset AMPLIFIER_HOME 2>/dev/null || true
set +u
. "$SCRIPT_DIR/lib/platform.sh"
set -u
: "${AMPLIFIER_HOME:=$_saved_home}"

FORCE=false
[[ "${1:-}" == "--force" ]] && FORCE=true

echo "Platform: $AMPLIFIER_PLATFORM"
echo "AMPLIFIER_HOME: $AMPLIFIER_HOME"

# --- Generate .claude/settings.json ---

SETTINGS_OUT="$REPO_ROOT/.claude/settings.json"
SETTINGS_TPL="$REPO_ROOT/config/platform/settings.json.template"

if [[ -f "$SETTINGS_OUT" ]] && [[ "$FORCE" != true ]]; then
    echo ""
    echo "WARNING: $SETTINGS_OUT already exists."
    read -r -p "Overwrite? [y/N] " answer
    if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
        echo "Skipping settings.json"
    else
        FORCE_SETTINGS=true
    fi
fi

if [[ ! -f "$SETTINGS_OUT" ]] || [[ "$FORCE" == true ]] || [[ "${FORCE_SETTINGS:-false}" == true ]]; then
    # Determine enabled MCP servers per platform
    ENABLED_MCP='["playwright", "context7", "deepwiki", "repomix", "gitea", "autocontext"]'

    # Use AMPLIFIER_HOME with forward slashes (Git Bash on Windows uses forward slashes)
    AMP_PATH="$AMPLIFIER_HOME"

    sed -e "s|{{AMPLIFIER_HOME}}|${AMP_PATH}|g" \
        -e "s|{{ENABLED_MCP_SERVERS}}|${ENABLED_MCP}|g" \
        "$SETTINGS_TPL" > "$SETTINGS_OUT"

    echo "Generated: $SETTINGS_OUT"
fi

# --- Copy platform-specific .mcp.json ---

MCP_OUT="$REPO_ROOT/.mcp.json"
MCP_SRC="$REPO_ROOT/config/platform/mcp.${AMPLIFIER_PLATFORM}.json"

if [[ ! -f "$MCP_SRC" ]]; then
    echo "ERROR: No MCP config for platform '$AMPLIFIER_PLATFORM': $MCP_SRC"
    exit 1
fi

if [[ -f "$MCP_OUT" ]] && [[ "$FORCE" != true ]]; then
    echo ""
    echo "WARNING: $MCP_OUT already exists."
    read -r -p "Overwrite? [y/N] " answer
    if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
        echo "Skipping .mcp.json"
        echo ""
        echo "Done."
        exit 0
    fi
fi

cp "$MCP_SRC" "$MCP_OUT"
echo "Generated: $MCP_OUT"

echo ""
echo "Done. Platform configs ready for $AMPLIFIER_PLATFORM."
