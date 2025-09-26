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

# Prepare environment variables
ENV_ARGS=()

# Forward API keys if they exist
if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    ENV_ARGS+=("-e" "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY")
    print_status "Forwarding ANTHROPIC_API_KEY"
fi

if [ ! -z "$AWS_ACCESS_KEY_ID" ]; then
    ENV_ARGS+=("-e" "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID")
    print_status "Forwarding AWS_ACCESS_KEY_ID"
fi

if [ ! -z "$AWS_SECRET_ACCESS_KEY" ]; then
    ENV_ARGS+=("-e" "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY")
    print_status "Forwarding AWS_SECRET_ACCESS_KEY"
fi

if [ ! -z "$AWS_DEFAULT_REGION" ]; then
    ENV_ARGS+=("-e" "AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION")
    print_status "Forwarding AWS_DEFAULT_REGION"
fi

if [ ! -z "$AWS_REGION" ]; then
    ENV_ARGS+=("-e" "AWS_REGION=$AWS_REGION")
    print_status "Forwarding AWS_REGION"
fi

# Check if we have any API keys
if [ ${#ENV_ARGS[@]} -eq 0 ]; then
    print_warning "No API keys detected in environment."
    print_warning "Make sure to set ANTHROPIC_API_KEY or AWS credentials before running."
fi

# Run the Docker container
print_status "Starting Amplifier container..."
print_status "Press Ctrl+C to exit when done"

docker run -it --rm \
    "${ENV_ARGS[@]}" \
    -e "TARGET_DIR=/workspace" \
    -e "AMPLIFIER_DATA_DIR=/app/amplifier-data" \
    -v "$TARGET_PROJECT:/workspace" \
    -v "$DATA_DIR:/app/amplifier-data" \
    --name "amplifier-$(basename "$TARGET_PROJECT")-$$" \
    "$IMAGE_NAME"

print_success "Amplifier session completed"