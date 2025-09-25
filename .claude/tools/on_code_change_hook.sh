#!/usr/bin/env bash

# Claude Code make check hook script
# Intelligently finds and runs 'make check' from the appropriate directory
# Handles virtual environment issues in git worktrees

# Ensure proper environment for make to find /bin/sh
export PATH="/bin:/usr/bin:$PATH"
export SHELL="/bin/bash"

# Expected JSON input format from stdin:
# {
#   "session_id": "abc123",
#   "transcript_path": "/path/to/transcript.jsonl",
#   "cwd": "/path/to/project/subdir",
#   "hook_event_name": "PostToolUse",
#   "tool_name": "Write",
#   "tool_input": {
#     "file_path": "/path/to/file.txt",
#     "content": "..."
#   },
#   "tool_response": {
#     "filePath": "/path/to/file.txt",
#     "success": true
#   }
# }

set -euo pipefail

# Read JSON from stdin
JSON_INPUT=$(cat)

# Debug: Log the JSON input to a file (comment out in production)
# echo "DEBUG: JSON received at $(date):" >> /tmp/make-check-debug.log
# echo "$JSON_INPUT" >> /tmp/make-check-debug.log

# Parse fields from JSON (using simple grep/sed for portability)
CWD=$(echo "$JSON_INPUT" | grep -o '"cwd"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"cwd"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo "")
TOOL_NAME=$(echo "$JSON_INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo "")

# Check if tool operation was successful
SUCCESS=$(echo "$JSON_INPUT" | grep -o '"success"[[:space:]]*:[[:space:]]*[^,}]*' | sed 's/.*"success"[[:space:]]*:[[:space:]]*\([^,}]*\).*/\1/' || echo "")

# Extract file_path from tool_input if available
FILE_PATH=$(echo "$JSON_INPUT" | grep -o '"tool_input"[[:space:]]*:[[:space:]]*{[^}]*}' | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || true)

# If tool operation failed, exit early
if [[ "${SUCCESS:-}" == "false" ]]; then
    echo "Skipping 'make check' - tool operation failed"
    exit 0
fi

# Log what tool was used
if [[ -n "${TOOL_NAME:-}" ]]; then
    echo "Post-hook for $TOOL_NAME tool"
fi

# Check if we're editing a file in the claude project dir
# CLAUDE_PROJECT_DIR is provided by Claude Code and points to the project root
if [[ -n "${FILE_PATH:-}" ]] && [[ -n "${CLAUDE_PROJECT_DIR:-}" ]] && [[ "$FILE_PATH" == "$CLAUDE_PROJECT_DIR"/* ]]; then
    # Editing a file in the claude project dir project - always run from project root
    START_DIR="$CLAUDE_PROJECT_DIR"
    echo "Detected edit in project - will run checks from: $CLAUDE_PROJECT_DIR"
else
    # Determine the starting directory for non-claude project dir files
    # Priority: 1) Directory of edited file, 2) CWD, 3) Current directory
    START_DIR=""
    if [[ -n "${FILE_PATH:-}" ]]; then
        # Use directory of the edited file
        FILE_DIR=$(dirname "$FILE_PATH" 2>/dev/null || echo "")
        if [[ -n "$FILE_DIR" ]] && [[ -d "$FILE_DIR" ]]; then
            START_DIR="$FILE_DIR"
            echo "Using directory of edited file: $FILE_DIR"
        fi
    fi
    
    if [[ -z "$START_DIR" ]] && [[ -n "${CWD:-}" ]]; then
        START_DIR="$CWD"
    elif [[ -z "$START_DIR" ]]; then
        START_DIR=$(pwd)
    fi
fi

# Function to find project root (looks for .git or Makefile going up the tree)
find_project_root() {
    local dir="$1"
    while [[ "$dir" != "/" ]]; do
        if [[ -f "$dir/Makefile" ]] || [[ -d "$dir/.git" ]]; then
            echo "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    return 1
}

# Function to check if make target exists
make_target_exists() {
    local dir="$1"
    local target="$2"
    if [[ -f "$dir/Makefile" ]]; then
        # Check if target exists in Makefile
        make -C "$dir" -n "$target" &>/dev/null
        return $?
    fi
    return 1
}

# Function to setup proper environment for worktree
setup_worktree_env() {
    local project_dir="$1"
    
    # Check if we have a local .venv in this project directory
    if [[ -d "$project_dir/.venv" ]]; then
        # Temporarily unset VIRTUAL_ENV to avoid conflicts
        unset VIRTUAL_ENV
        
        # If we're in a worktree, make sure we use its local .venv
        echo "Using worktree's local .venv: $project_dir/.venv"
        
        # Let uv handle the environment detection
        # uv will automatically use the .venv in the project directory
        return 0
    fi
    
    # If no local .venv exists, keep existing environment
    return 0
}

# Start from the determined directory
cd "$START_DIR"

# Find the project root first
PROJECT_ROOT=$(find_project_root "$START_DIR")

if [[ -z "$PROJECT_ROOT" ]]; then
    echo "Error: No project root found (no .git or Makefile)"
    exit 1
fi

# Set up proper environment for the project (handles worktrees)
setup_worktree_env "$PROJECT_ROOT"

# Check if there's a local Makefile with 'check' target in START_DIR
if [[ "$START_DIR" != "$PROJECT_ROOT" ]] && make_target_exists "." "check"; then
    echo "Running 'make check' in directory: $START_DIR"
    make check
elif make_target_exists "$PROJECT_ROOT" "check"; then
    echo "Running 'make check' from project root: $PROJECT_ROOT"
    cd "$PROJECT_ROOT"
    make check
else
    # Find the project root (may fail, that's OK)
    PROJECT_ROOT=$(find_project_root "$START_DIR" || echo "")
    
    if [[ -n "$PROJECT_ROOT" ]] && make_target_exists "$PROJECT_ROOT" "check"; then
        echo "Running 'make check' from project root: $PROJECT_ROOT"
        cd "$PROJECT_ROOT"
        make check
    else
        echo "Info: No Makefile with 'check' target found - skipping make check"
        exit 0  # Exit successfully to avoid error messages
    fi
fi

