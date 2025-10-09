#!/bin/bash

# Amplifier Claude Startup Script
# This script ensures all environment variables and paths are set correctly

echo "🚀 Starting Claude with Amplifier environment..."

# Set up pnpm paths
export PNPM_HOME="$HOME/.local/share/pnpm"
export PATH="$PNPM_HOME:$PATH"

# Activate virtual environment
source .venv/bin/activate

# Create necessary directories if they don't exist
mkdir -p .claude-trace
mkdir -p .data

echo "✅ Environment activated"
echo "📁 Working directory: $(pwd)"
echo "🐍 Python: $(which python)"
echo "🤖 Claude: $(which claude)"
echo ""

# Start Claude
claude "$@"