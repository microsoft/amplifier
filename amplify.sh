#!/bin/bash

# Amplifier Docker Wrapper Script
# Usage: ./amplify.sh /path/to/your/project [data-dir]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[Amplifier]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[Amplifier]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[Amplifier]${NC} $1"
}

print_error() {
    echo -e "${RED}[Amplifier]${NC} $1"
}

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Parse arguments
if [ $# -eq 0 ]; then
    print_error "Usage: $0 /path/to/your/project [data-dir]"
    print_error "Example: $0 ~/my-project"
    print_error "Example: $0 ~/my-project ~/amplifier-data"
    exit 1
fi

TARGET_PROJECT="$1"
DATA_DIR="${2:-$(pwd)/amplifier-data}"

# Validate target project directory
if [ ! -d "$TARGET_PROJECT" ]; then
    print_error "Target project directory does not exist: $TARGET_PROJECT"
    exit 1
fi

# Convert to absolute paths
TARGET_PROJECT=$(realpath "$TARGET_PROJECT")
DATA_DIR=$(realpath "$DATA_DIR")

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

print_status "Target Project: $TARGET_PROJECT"
print_status "Data Directory: $DATA_DIR"

# Build Docker image if it doesn't exist
IMAGE_NAME="amplifier:latest"
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    print_status "Building Amplifier Docker image..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"
    print_success "Docker image built successfully"
else
    print_status "Using existing Docker image: $IMAGE_NAME"
fi

# Prepare environment variables for Claude Code configuration
ENV_ARGS=()

# Critical API keys that Claude Code needs
API_KEYS=("ANTHROPIC_API_KEY" "AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY" "AWS_DEFAULT_REGION" "AWS_REGION")

HAS_ANTHROPIC_KEY=false
HAS_AWS_KEYS=false

for key in "${API_KEYS[@]}"; do
    value="${!key}"
    if [ ! -z "$value" ]; then
        ENV_ARGS+=("-e" "$key=$value")
        print_status "✓ Forwarding $key"

        if [ "$key" = "ANTHROPIC_API_KEY" ]; then
            HAS_ANTHROPIC_KEY=true
        fi
        if [ "$key" = "AWS_ACCESS_KEY_ID" ]; then
            HAS_AWS_KEYS=true
        fi
    fi
done

# Validate API key configuration
if [ "$HAS_ANTHROPIC_KEY" = false ] && [ "$HAS_AWS_KEYS" = false ]; then
    print_error "❌ No valid API configuration found!"
    print_error ""
    print_error "Claude Code requires one of the following:"
    print_error "  1. ANTHROPIC_API_KEY environment variable"
    print_error "  2. AWS credentials (AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY)"
    print_error ""
    print_error "Set the appropriate environment variable and try again."
    exit 1
fi

if [ "$HAS_ANTHROPIC_KEY" = true ]; then
    print_success "🔑 Anthropic API key detected - will use direct API"
elif [ "$HAS_AWS_KEYS" = true ]; then
    print_success "🔑 AWS credentials detected - will use Bedrock"
fi

# Simple validation: test if Docker can mount the project directory
print_status "Testing Docker mount accessibility..."
if docker run --rm -v "$TARGET_PROJECT:/test" alpine:latest test -d /test >/dev/null 2>&1; then
    print_success "Docker mount test successful"
else
    print_warning "Docker may not be able to access project directory: $TARGET_PROJECT"
    print_warning "If container fails to start:"
    print_warning "  - For Docker Desktop: Enable file sharing for this drive in Settings"
    print_warning "  - For WSL: Ensure path is accessible from within WSL"
    print_warning "  - Check path exists and has proper permissions"
fi

# Run the Docker container with Claude Code pre-configured
print_status "🚀 Starting Amplifier Docker container..."
print_status "📁 Project: $TARGET_PROJECT → /workspace"
print_status "💾 Data: $DATA_DIR → /app/amplifier-data"

if [ "$HAS_ANTHROPIC_KEY" = true ]; then
    print_status "🔗 API: Anthropic Direct API"
elif [ "$HAS_AWS_KEYS" = true ]; then
    print_status "🔗 API: AWS Bedrock"
fi

print_warning "⚠️  IMPORTANT: When Claude starts, send this first message:"
echo -e "${YELLOW}===========================================${NC}"
echo -e "${NC}I'm working in /workspace which contains my project files.${NC}"
echo -e "${NC}Please cd to /workspace and work there.${NC}"
echo -e "${NC}Do NOT update any issues or PRs in the Amplifier repo.${NC}"
echo -e "${YELLOW}===========================================${NC}"
echo ""
print_status "Press Ctrl+C to exit when done"

CONTAINER_NAME="amplifier-$(basename "$TARGET_PROJECT")-$$"

# Docker run with complete environment configuration
print_status "Executing: docker run with $(echo "${ENV_ARGS[@]}" | grep -o ' -e ' | wc -l) environment variables"

docker run -it --rm \
    "${ENV_ARGS[@]}" \
    -e "TARGET_DIR=/workspace" \
    -e "AMPLIFIER_DATA_DIR=/app/amplifier-data" \
    -v "$TARGET_PROJECT:/workspace" \
    -v "$DATA_DIR:/app/amplifier-data" \
    --name "$CONTAINER_NAME" \
    "$IMAGE_NAME"

if [ $? -eq 0 ]; then
    print_success "✅ Amplifier session completed successfully"
else
    print_error "❌ Failed to run Amplifier container"
    print_error "Check that Docker is running and the image exists"
    exit 1
fi