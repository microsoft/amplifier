FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for Claude Code)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Install Python 3.11
RUN apt-get update && apt-get install -y python3.11 python3.11-venv python3.11-dev && rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"
ENV PNPM_HOME="/root/.local/share/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

# Install Claude Code, pyright, and pnpm
ENV SHELL=/bin/bash
RUN npm install -g @anthropic-ai/claude-code pyright pnpm && \
    SHELL=/bin/bash pnpm setup && \
    echo 'export PNPM_HOME="/root/.local/share/pnpm"' >> ~/.bashrc && \
    echo 'export PATH="$PNPM_HOME:$PATH"' >> ~/.bashrc

# Pre-configure Claude Code to use environment variables
RUN mkdir -p /root/.config/claude-code

# Create working directory
WORKDIR /app

# Clone Amplifier repository
RUN git clone https://github.com/microsoft/amplifier.git /app/amplifier

# Set working directory to amplifier
WORKDIR /app/amplifier

# Initialize Python environment with uv and install dependencies
RUN uv venv --python python3.11 .venv && \
    uv sync && \
    . .venv/bin/activate && make install

# Create data directory for Amplifier and required subdirectories
RUN mkdir -p /app/amplifier-data && \
    mkdir -p /app/amplifier/.data

# Clone Amplifier to /root/amplifier where Claude Code will start
RUN git clone https://github.com/microsoft/amplifier.git /root/amplifier

# Build Amplifier in /root/amplifier
WORKDIR /root/amplifier
RUN uv venv --python python3.11 .venv && \
    uv sync && \
    . .venv/bin/activate && make install

# Create required .data directory structure
RUN mkdir -p /root/amplifier/.data/knowledge && \
    mkdir -p /root/amplifier/.data/indexes && \
    mkdir -p /root/amplifier/.data/state && \
    mkdir -p /root/amplifier/.data/memories && \
    mkdir -p /root/amplifier/.data/cache

# Create entrypoint script
RUN cat > /app/entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Default to /workspace if no target directory specified
TARGET_DIR=${TARGET_DIR:-/workspace}
AMPLIFIER_DATA_DIR=${AMPLIFIER_DATA_DIR:-/app/amplifier-data}

echo "🚀 Starting Amplifier Docker Container"
echo "📁 Target project: $TARGET_DIR"
echo "📊 Amplifier data: $AMPLIFIER_DATA_DIR"

# Validate target directory exists
if [ -d "$TARGET_DIR" ]; then
    echo "✅ Target directory found: $TARGET_DIR"
else
    echo "❌ Target directory not found: $TARGET_DIR"
    echo "💡 Make sure you mounted your project directory to $TARGET_DIR"
    exit 1
fi

# Change to Amplifier directory and activate environment
echo "🔧 Setting up Amplifier environment..."
cd /root/amplifier
source .venv/bin/activate

# Configure Amplifier data directory
echo "📂 Configuring Amplifier data directory..."
export AMPLIFIER_DATA_DIR="$AMPLIFIER_DATA_DIR"

# Check if API key is available
if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "❌ No API keys found!"
    echo "💡 Please set ANTHROPIC_API_KEY or AWS credentials in your environment"
    exit 1
fi

# Configure Claude Code based on available credentials
if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    echo "🔧 Configuring Claude Code with Anthropic API..."
    echo "🌐 Backend: ANTHROPIC DIRECT API"
    echo "🔑 Using provided ANTHROPIC_API_KEY"

    # Create Claude Code configuration with API key
    mkdir -p /root/.config/claude-code
    cat > /root/.config/claude-code/config.json << CONFIG_EOF
{
  "apiKey": "$ANTHROPIC_API_KEY",
  "model": "claude-3-5-sonnet-20241022",
  "skipSetup": true
}
CONFIG_EOF

    echo "🤖 Starting Claude Code from Amplifier directory..."
    echo "📁 Adding target directory: $TARGET_DIR"
    echo "🚀 Starting interactive Claude Code session..."
    echo ""
    echo "==============================================="
    echo "📋 FIRST MESSAGE TO SEND TO CLAUDE:"
    echo "I'm working in $TARGET_DIR which doesn't have Amplifier files."
    echo "Please cd to that directory and work there."
    echo "Do NOT update any issues or PRs in the Amplifier repo."
    echo "==============================================="
    echo ""

    # Start Claude with directory access and explicit permission mode
    claude --add-dir "$TARGET_DIR" --permission-mode acceptEdits

elif [ ! -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "🔧 Configuring Claude Code with AWS Bedrock..."
    echo "🌐 Backend: AWS BEDROCK"
    echo "🔑 Using provided AWS credentials"
    echo "⚠️  Setting CLAUDE_CODE_USE_BEDROCK=1"
    export CLAUDE_CODE_USE_BEDROCK=1

    # Create basic config for Bedrock
    mkdir -p /root/.config/claude-code
    cat > /root/.config/claude-code/config.json << CONFIG_EOF
{
  "useBedrock": true,
  "skipSetup": true
}
CONFIG_EOF

    echo "🤖 Starting Claude Code from Amplifier directory with AWS Bedrock..."
    echo "📁 Adding target directory: $TARGET_DIR"
    echo "🚀 Starting interactive Claude Code session..."
    echo ""
    echo "==============================================="
    echo "📋 FIRST MESSAGE TO SEND TO CLAUDE:"
    echo "I'm working in $TARGET_DIR which doesn't have Amplifier files."
    echo "Please cd to that directory and work there."
    echo "Do NOT update any issues or PRs in the Amplifier repo."
    echo "==============================================="
    echo ""

    # Start Claude with directory access and explicit permission mode
    claude --add-dir "$TARGET_DIR" --permission-mode acceptEdits
else
    echo "❌ No supported API configuration found!"
    exit 1
fi
EOF

RUN chmod +x /app/entrypoint.sh

# Set environment variables
ENV TARGET_DIR=/workspace
ENV AMPLIFIER_DATA_DIR=/app/amplifier-data
ENV PATH="/app/amplifier:$PATH"

# Create volumes for mounting
VOLUME ["/workspace", "/app/amplifier-data"]

# Set the working directory to Amplifier before entrypoint
WORKDIR /root/amplifier

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]