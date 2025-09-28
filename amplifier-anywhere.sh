#!/bin/bash

# Amplifier Universal Script
# Use Amplifier's power on any project directory
# 
# Usage:
#   amplifier [project-dir] [claude-options]
#   amplifier --help
#   amplifier --version

set -e  # Exit on any error

# Help function
show_help() {
    cat << EOF
Amplifier Universal Access Script

USAGE:
    amplifier [PROJECT_DIR] [CLAUDE_OPTIONS...]
    amplifier --help
    amplifier --version

EXAMPLES:
    amplifier                           # Use current directory
    amplifier ~/dev/my-project          # Use specific directory
    amplifier . --model sonnet          # Pass options to Claude
    amplifier ~/app --print "Fix bugs"  # Non-interactive mode

DESCRIPTION:
    Starts Claude with Amplifier's specialized agents and tools,
    configured to work on projects in any directory.
    
    All of Amplifier's 20+ agents become available:
    - zen-architect (design with simplicity)
    - bug-hunter (systematic debugging)  
    - security-guardian (security analysis)
    - And many more...

FIRST MESSAGE TEMPLATE:
    I'm working in [YOUR_PROJECT_PATH] which doesn't have Amplifier files.
    Please cd to that directory and work there.
    Do NOT update any issues or PRs in the Amplifier repo.

EOF
}

# Handle help and version flags
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    show_help
    exit 0
fi

if [[ "$1" == "--version" ]]; then
    echo "Amplifier Universal Access (part of Amplifier toolkit)"
    exit 0
fi

# Auto-detect Amplifier directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$SCRIPT_DIR" == */bin ]]; then
    # Global installation - find amplifier directory
    AMPLIFIER_DIR="$(dirname "$SCRIPT_DIR")/dev/amplifier"
    if [[ ! -d "$AMPLIFIER_DIR" ]]; then
        # Fallback - common locations
        for candidate in "$HOME/dev/amplifier" "$HOME/amplifier" "$HOME/repos/amplifier"; do
            if [[ -d "$candidate" ]]; then
                AMPLIFIER_DIR="$candidate"
                break
            fi
        done
    fi
else
    # Local installation
    AMPLIFIER_DIR="$SCRIPT_DIR"
fi

# Validate Amplifier directory
if [[ ! -d "$AMPLIFIER_DIR" ]]; then
    echo "❌ Cannot find Amplifier installation directory"
    echo "   Looked for: $AMPLIFIER_DIR"
    echo "   Please ensure Amplifier is properly installed"
    exit 1
fi

if [[ ! -f "$AMPLIFIER_DIR/.venv/bin/activate" ]]; then
    echo "❌ Amplifier virtual environment not found at: $AMPLIFIER_DIR/.venv"
    echo "   Run 'make install' in the Amplifier directory first"
    exit 1
fi

# Parse arguments - use ORIGINAL_PWD if set (from global wrapper), otherwise current pwd
DEFAULT_DIR="${ORIGINAL_PWD:-$(pwd)}"
PROJECT_DIR="${1:-$DEFAULT_DIR}"

# Check if first arg is a Claude flag (starts with --)
if [[ "$1" == --* ]] && [[ "$1" != "--help" ]] && [[ "$1" != "-h" ]] && [[ "$1" != "--version" ]]; then
    # First argument is a Claude option, use default directory
    PROJECT_DIR="$DEFAULT_DIR"
    CLAUDE_ARGS="$@"
else
    # First argument might be a directory
    if [[ -n "$1" ]]; then
        shift || true  # Remove first argument, ignore error if no args
    fi
    CLAUDE_ARGS="$@"
fi

# Validate project directory
if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "❌ Directory '$PROJECT_DIR' does not exist"
    exit 1
fi

# Convert to absolute path
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

echo "🚀 Starting Amplifier for project: $PROJECT_DIR"
echo "📁 Amplifier location: $AMPLIFIER_DIR"

# Set up pnpm paths
export PNPM_HOME="$HOME/.local/share/pnpm"
export PATH="$PNPM_HOME:$PATH"

# Check Claude availability
if ! command -v claude >/dev/null 2>&1; then
    echo "❌ Claude CLI not found. Please ensure it's installed and in PATH."
    echo "   Run 'make install' in Amplifier directory to install it."
    exit 1
fi

# Activate amplifier's virtual environment
echo "🔄 Activating Amplifier environment..."
source "$AMPLIFIER_DIR/.venv/bin/activate"

# Create necessary directories in amplifier
mkdir -p "$AMPLIFIER_DIR/.claude-trace"
mkdir -p "$AMPLIFIER_DIR/.data"

echo "✅ Environment activated"
echo "🐍 Python: $(which python)"
echo "🤖 Claude: $(which claude)"
echo "📂 Project: $PROJECT_DIR"
echo ""
echo "💡 First message template:"
echo "   I'm working in $PROJECT_DIR which doesn't have Amplifier files."
echo "   Please cd to that directory and work there."
echo "   Do NOT update any issues or PRs in the Amplifier repo."
echo ""

# Start Claude with both directories
cd "$AMPLIFIER_DIR"
exec claude --add-dir "$PROJECT_DIR" $CLAUDE_ARGS
