#!/bin/bash
# Amplifier v2 Setup Script
# This installs the minimal dependencies needed to run the demo

set -e

echo "Setting up Amplifier v2 Demo Environment..."
echo "==========================================="

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install minimal dependencies for the demo
echo "Installing core dependencies..."
pip install --quiet --upgrade pip

# Install basic requirements
pip install --quiet asyncio
pip install --quiet typing_extensions
pip install --quiet click
pip install --quiet pyyaml
pip install --quiet rich

# Optional: Install real LLM libraries if you want to use them
echo ""
echo "Optional: Install LLM provider libraries?"
echo "  1) OpenAI (requires OPENAI_API_KEY)"
echo "  2) Anthropic (requires ANTHROPIC_API_KEY)"
echo "  3) Both"
echo "  4) Skip (use mock provider)"
read -p "Choose [1-4]: " choice

case $choice in
    1)
        echo "Installing OpenAI..."
        pip install --quiet openai
        ;;
    2)
        echo "Installing Anthropic..."
        pip install --quiet anthropic
        ;;
    3)
        echo "Installing both OpenAI and Anthropic..."
        pip install --quiet openai anthropic
        ;;
    *)
        echo "Skipping LLM providers (will use mock)"
        ;;
esac

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the demo:"
echo "  source .venv/bin/activate  # if not already activated"
echo "  python demo.py"
echo ""
echo "To use real LLMs, set API keys first:"
echo "  export OPENAI_API_KEY=your-key"
echo "  export ANTHROPIC_API_KEY=your-key"