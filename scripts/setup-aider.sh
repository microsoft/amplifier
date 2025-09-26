#!/bin/bash
# Setup script for Aider integration

set -e

echo "Setting up Aider for AI-powered code regeneration..."

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please install it first."
    echo "Run: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create isolated virtual environment for Aider
echo "Creating isolated environment for Aider..."
uv venv .aider-venv --python 3.11

# Install Aider in the isolated environment
echo "Installing Aider..."
source .aider-venv/bin/activate
uv pip install aider-chat

echo ""
echo "✅ Aider setup complete!"
echo ""
echo "To use Aider directly:"
echo "  source .aider-venv/bin/activate"
echo "  aider --help"
echo ""
echo "To use the regeneration tool:"
echo "  python amplifier/tools/aider_regenerator.py --help"
echo ""
echo "Note: You'll need to set your API key:"
echo "  export ANTHROPIC_API_KEY='your-api-key'"
echo ""