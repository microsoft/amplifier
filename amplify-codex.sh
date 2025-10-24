#!/bin/bash

# Amplifier Codex Wrapper - Starts Codex CLI with MCP servers and session management
# 
# This script provides a seamless integration between Codex CLI and the Amplifier
# memory system. It handles session initialization, MCP server orchestration, and
# cleanup automatically.
#
# Usage examples:
#   ./amplify-codex.sh                    # Start with default profile
#   ./amplify-codex.sh --profile review   # Use review profile
#   ./amplify-codex.sh --no-init          # Skip initialization
#   ./amplify-codex.sh --help             # Show help

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[Amplifier-Codex]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[Amplifier-Codex]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[Amplifier-Codex]${NC} $1"
}

print_error() {
    echo -e "${RED}[Amplifier-Codex]${NC} $1"
}

# Default values
PROFILE="development"
SKIP_INIT=false
SKIP_CLEANUP=false
SHOW_HELP=false

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        --no-init)
            SKIP_INIT=true
            shift
            ;;
        --no-cleanup)
            SKIP_CLEANUP=true
            shift
            ;;
        --help)
            SHOW_HELP=true
            shift
            ;;
        *)
            # Pass through to Codex
            break
            ;;
    esac
done

# Show help if requested
if [ "$SHOW_HELP" = true ]; then
    echo "Amplifier Codex Wrapper"
    echo ""
    echo "Usage: $0 [options] [codex-options]"
    echo ""
    echo "Options:"
    echo "  --profile <name>    Select Codex profile (development, ci, review) [default: development]"
    echo "  --no-init           Skip pre-session initialization"
    echo "  --no-cleanup        Skip post-session cleanup"
    echo "  --help              Show this help message"
    echo ""
    echo "All other arguments are passed through to Codex CLI."
    echo ""
    echo "Environment Variables:"
    echo "  CODEX_PROFILE       Override default profile"
    echo "  MEMORY_SYSTEM_ENABLED  Enable/disable memory system [default: true]"
    exit 0
fi

# Environment Setup
export AMPLIFIER_BACKEND=codex
export AMPLIFIER_ROOT="$(pwd)"
export MEMORY_SYSTEM_ENABLED="${MEMORY_SYSTEM_ENABLED:-true}"

# Prerequisites Validation
print_status "Validating prerequisites..."

if ! command -v codex &> /dev/null; then
    print_error "Codex CLI is not installed."
    print_error "Install Codex CLI from: https://github.com/xai-org/grok-1"
    exit 1
fi

if [ ! -d ".codex" ]; then
    print_error "Project structure incomplete: .codex/ directory not found."
    print_error "Ensure you're in the correct project directory."
    exit 1
fi

if [ ! -d ".venv" ]; then
    print_error "Virtual environment not found: .venv/ directory missing."
    print_error "Run 'make install' or 'uv sync' to set up the environment."
    exit 1
fi

if ! command -v uv &> /dev/null; then
    print_error "uv is not installed."
    print_error "Install uv from: https://github.com/astral-sh/uv"
    exit 1
fi

print_success "Prerequisites validated"

# Configuration Detection
print_status "Detecting configuration..."

if [ ! -f ".codex/config.toml" ]; then
    print_error ".codex/config.toml not found."
    print_error "Ensure Codex configuration is properly set up."
    exit 1
fi

# Allow profile override via environment
if [ -n "$CODEX_PROFILE" ]; then
    PROFILE="$CODEX_PROFILE"
fi

print_status "Using profile: $PROFILE"

# Check if profile exists in config (basic validation)
if ! grep -q "\[profiles\.$PROFILE\]" .codex/config.toml; then
    print_warning "Profile '$PROFILE' not found in config.toml, using default behavior"
fi

# Pre-Session Initialization
if [ "$SKIP_INIT" = false ]; then
    print_status "Running pre-session initialization..."
    
    # Create logs directory if it doesn't exist
    mkdir -p .codex/logs
    
    # Run initialization script
    if uv run python .codex/tools/session_init.py 2>&1 | tee .codex/logs/session_init.log; then
        # Extract summary from output (assuming it prints something like "Loaded X memories")
        SUMMARY=$(tail -n 1 .codex/logs/session_init.log | grep -o "Loaded [0-9]* memories" || echo "Initialization completed")
        print_success "$SUMMARY"
    else
        print_warning "Pre-session initialization failed, continuing anyway"
        print_warning "Check .codex/logs/session_init.log for details"
    fi
else
    print_status "Skipping pre-session initialization (--no-init)"
fi

# User Guidance Display
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${BLUE}Amplifier Codex Session Started${NC}                               ${BLUE}║${NC}"
echo -e "${BLUE}╠════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}MCP Tools Available:${NC}                                          ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}• initialize_session${NC} - Load context from memory system        ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}• check_code_quality${NC} - Run quality checks after changes       ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}• save_current_transcript${NC} - Export session transcript         ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}• finalize_session${NC} - Save memories before ending              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}                                                                ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${YELLOW}Recommended Workflow:${NC}                                         ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${YELLOW}1. Start:${NC} Use initialize_session to load context              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${YELLOW}2. Work:${NC} Edit code, run tools                                 ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${YELLOW}3. Check:${NC} Use check_code_quality after changes                ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${YELLOW}4. End:${NC} Use finalize_session to save learnings                ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}                                                                ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${YELLOW}Press Ctrl+C to exit${NC}                                          ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Codex Execution
print_status "Starting Codex CLI..."

# Build Codex command
CODEX_CMD=("codex" "--profile" "$PROFILE")

# Add config if not default location (assuming .codex/config.toml is not default)
CODEX_CMD+=("--config" ".codex/config.toml")

# Pass through remaining arguments
CODEX_CMD+=("$@")

print_status "Executing: ${CODEX_CMD[*]}"

# Trap SIGINT to ensure cleanup runs
cleanup_needed=true
trap 'cleanup_needed=true' SIGINT

# Run Codex
"${CODEX_CMD[@]}"
CODEX_EXIT_CODE=$?

# Post-Session Cleanup
if [ "$SKIP_CLEANUP" = false ] && [ "$cleanup_needed" = true ]; then
    print_status "Running post-session cleanup..."
    
    # Create logs directory if it doesn't exist
    mkdir -p .codex/logs
    
    # Run cleanup script
    if uv run python .codex/tools/session_cleanup.py 2>&1 | tee .codex/logs/session_cleanup.log; then
        # Extract summary from output
        SUMMARY=$(tail -n 1 .codex/logs/session_cleanup.log | grep -o "Extracted [0-9]* memories" || echo "Cleanup completed")
        print_success "$SUMMARY"
    else
        print_warning "Post-session cleanup failed"
        print_warning "Check .codex/logs/session_cleanup.log for details"
    fi
else
    if [ "$SKIP_CLEANUP" = true ]; then
        print_status "Skipping post-session cleanup (--no-cleanup)"
    fi
fi

# Exit Handling
if [ $CODEX_EXIT_CODE -eq 0 ]; then
    print_success "Session completed successfully"
else
    print_warning "Codex exited with code $CODEX_EXIT_CODE"
fi

exit $CODEX_EXIT_CODE