#!/bin/bash
# Shared platform detection for Amplifier scripts.
# Source this file: . "$(dirname "$0")/../lib/platform.sh"
# Or from tests: . "$REPO_ROOT/scripts/lib/platform.sh"

# If AMPLIFIER_HOME is already set, respect it
if [ -n "$AMPLIFIER_HOME" ]; then
    return 0 2>/dev/null || true
fi

# Auto-detect based on which path exists
if [ -d "/opt/amplifier" ]; then
    export AMPLIFIER_HOME="/opt/amplifier"
elif [ -d "/c/claude/amplifier" ]; then
    export AMPLIFIER_HOME="/c/claude/amplifier"
elif [ -d "C:/claude/amplifier" ]; then
    export AMPLIFIER_HOME="C:/claude/amplifier"
else
    # Fallback: derive from script location if sourced from within the repo
    _script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -f "$_script_dir/../../CLAUDE.md" ]; then
        export AMPLIFIER_HOME="$(cd "$_script_dir/../.." && pwd)"
    else
        echo "WARNING: Cannot detect AMPLIFIER_HOME. Set it manually." >&2
    fi
    unset _script_dir
fi

# Also export platform identifier
case "$(uname -s)" in
    Linux*)  export AMPLIFIER_PLATFORM="linux" ;;
    MINGW*|MSYS*|CYGWIN*) export AMPLIFIER_PLATFORM="windows" ;;
    Darwin*) export AMPLIFIER_PLATFORM="macos" ;;
    *)       export AMPLIFIER_PLATFORM="unknown" ;;
esac
