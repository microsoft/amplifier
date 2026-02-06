#!/bin/bash

# Enhanced Claude Code Status Line Script
# =========================================
# This script creates a custom status line for Claude Code that displays:
# - Current directory (green)
# - Git branch and status (yellow when dirty, cyan when clean)
# - Model name (color-coded by cost tier: red=high, green=medium, blue=low)
# - Session cost in USD
# - Session duration
#
# To use this status line:
# 1. Run `/statusline` in Claude Code to let it customize this for your environment
# 2. Or manually configure by adding to your ~/.claude/settings.json:
#    {
#      "statusLine": {
#        "type": "command",
#        "command": "bash /path/to/this/script.sh"
#      }
#    }
#
# Note: This script was developed on WSL/Linux. The /statusline command will
# adapt it for your specific OS and environment.

# Read JSON input from Claude Code (sent via stdin)
input=$(cat)

# Function to safely extract JSON values without requiring jq
# This makes the script more portable across different environments
extract_json() {
    local key="$1"
    local default="$2"
    # First try with quotes (for string values)
    local value=$(echo "$input" | grep -o "\"$key\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | sed "s/.*: *\"\([^\"]*\)\".*/\1/" | head -1)
    # If empty, try without quotes (for numeric values)
    if [ -z "$value" ]; then
        value=$(echo "$input" | grep -o "\"$key\"[[:space:]]*:[[:space:]]*[^,}]*" | sed "s/.*: *\([^,}]*\).*/\1/" | tr -d ' ' | head -1)
    fi
    echo "${value:-$default}"
}

# Extract session information from JSON
current_dir=$(extract_json "current_dir" "")
if [ -z "$current_dir" ]; then
    current_dir=$(extract_json "cwd" "$(pwd)")
fi

model_name=$(extract_json "display_name" "Unknown")
model_id=$(extract_json "id" "")
total_cost=$(extract_json "total_cost_usd" "0")
total_duration=$(extract_json "total_duration_ms" "0")

# Change to directory for git operations
cd "$current_dir" 2>/dev/null || cd "$(pwd)"

# Format directory path (replace home directory with ~)
display_dir=$(echo "$current_dir" | sed "s|^$HOME|~|")

# Determine model color based on cost tier
# Opus models = Red (high cost)
# Sonnet models = Green (medium cost)  
# Haiku models = Blue (low cost)
case "$model_id" in
    *opus*)
        model_color="31"  # Red
        ;;
    *sonnet*)
        model_color="32"  # Green
        ;;
    *haiku*)
        model_color="34"  # Blue
        ;;
    *)
        # Fallback: check model name if ID doesn't match
        case "$model_name" in
            *Opus*|*opus*)
                model_color="31"  # Red
                ;;
            *Sonnet*|*sonnet*)
                model_color="32"  # Green
                ;;
            *Haiku*|*haiku*)
                model_color="34"  # Blue
                ;;
            *)
                model_color="37"  # White/default
                ;;
        esac
        ;;
esac

# Get git information if in a git repository
git_info=""
git_formatted=""
if git rev-parse --is-inside-work-tree &>/dev/null; then
    # Get current branch name (or commit hash if detached)
    branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || git describe --tags --exact-match 2>/dev/null || git rev-parse --short HEAD 2>/dev/null)
    
    if [ -n "$branch" ]; then
        # Check for uncommitted changes (both staged and unstaged)
        if ! git diff-index --quiet HEAD -- 2>/dev/null || ! git diff --quiet 2>/dev/null; then
            dirty_indicator="*"
            git_color="33"  # Yellow for uncommitted changes
        else
            dirty_indicator=""
            git_color="36"  # Cyan for clean working tree
        fi
        
        # Get remote name if it exists
        remote=$(git remote | head -n1 2>/dev/null)
        
        # Format git info with branch, dirty indicator, and remote
        if [ -n "$remote" ]; then
            git_info="(${branch}${dirty_indicator} → ${remote})"
        else
            git_info="(${branch}${dirty_indicator})"
        fi
        
        # Apply color formatting
        git_formatted="\033[${git_color}m${git_info}\033[0m"
    fi
fi

# Format cost display (show in dollars with 2 decimal places)
cost_display=""
if [ "$total_cost" != "0" ] && [ "$total_cost" != "null" ]; then
    # Use awk for floating point formatting (more portable than bc)
    cost_formatted=$(echo "$total_cost" | awk '{printf "%.2f", $1}')
    if [ -n "$cost_formatted" ] && [ "$cost_formatted" != "0.00" ]; then
        cost_display=" 💰\$${cost_formatted}"
    fi
fi

# Format session duration (convert milliseconds to human-readable format)
duration_display=""
if [ "$total_duration" != "0" ] && [ "$total_duration" != "null" ] && [ "$total_duration" != "" ]; then
    # Convert milliseconds to seconds
    duration_secs=$(echo "$total_duration" | awk '{printf "%d", $1/1000}')
    if [ "$duration_secs" -gt 59 ]; then
        # Convert to minutes
        duration_mins=$(echo "$duration_secs" | awk '{printf "%d", $1/60}')
        if [ "$duration_mins" -gt 0 ]; then
            if [ "$duration_mins" -gt 59 ]; then
                # Show hours and minutes for long sessions
                duration_hours=$(echo "$duration_mins" | awk '{printf "%d", $1/60}')
                duration_remain_mins=$(echo "$duration_mins" | awk '{printf "%d", $1%60}')
                duration_display=" ⏱${duration_hours}h${duration_remain_mins}m"
            else
                # Just show minutes
                duration_display=" ⏱${duration_mins}m"
            fi
        fi
    fi
fi

# Build and output the status line
# Format: [green]directory[/green] [yellow/cyan](git info)[/color] [cost-colored]Model Name[/color] 💰$X.XX ⏱Xm
if [ -n "$git_formatted" ]; then
    # With git information
    printf "\033[32m%s\033[0m %b \033[%sm%s\033[0m%s%s" \
        "$display_dir" \
        "$git_formatted" \
        "$model_color" \
        "$model_name" \
        "$cost_display" \
        "$duration_display"
else
    # Without git information
    printf "\033[32m%s\033[0m \033[%sm%s\033[0m%s%s" \
        "$display_dir" \
        "$model_color" \
        "$model_name" \
        "$cost_display" \
        "$duration_display"
fi