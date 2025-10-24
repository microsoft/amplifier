#!/bin/bash

# Codex Shortcuts - Quick commands for common Codex workflows
#
# This script provides bash functions that wrap common MCP tool invocations
# for the Codex CLI integration with Amplifier. These shortcuts provide a
# convenient way to perform frequent operations without typing full commands.
#
# Usage:
#   source .codex/tools/codex_shortcuts.sh  # Load shortcuts
#   codex-init "project context"            # Quick initialization
#   codex-check file1.py file2.py           # Quality checks
#   codex-task-add "Implement feature X"   # Create task
#   codex-help                              # Show available shortcuts

# Colors for output (matching amplify-codex.sh)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[Codex-Shortcut]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[Codex-Shortcut]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[Codex-Shortcut]${NC} $1"
}

print_error() {
    echo -e "${RED}[Codex-Shortcut]${NC} $1"
}

# Helper function to check if Codex is available
_check_codex() {
    if ! command -v codex &> /dev/null; then
        print_error "Codex CLI is not available. Please ensure Codex is installed and in PATH."
        return 1
    fi
    return 0
}

# Helper function to execute Codex tool
_codex_exec() {
    local tool_name="$1"
    local params="$2"
    
    if ! _check_codex; then
        return 1
    fi
    
    print_status "Executing: codex exec $tool_name $params"
    codex exec "$tool_name" "$params"
}

# codex-init [context] - Quick session initialization
codex-init() {
    local context="${1:-}"
    
    if [ -z "$context" ]; then
        print_warning "No context provided, using default initialization"
        _codex_exec "initialize_session" "{}"
    else
        _codex_exec "initialize_session" "{\"context\": \"$context\"}"
    fi
}

# codex-check [files...] - Run quality checks
codex-check() {
    local files="$*"
    
    if [ -z "$files" ]; then
        print_warning "No files specified, checking all modified files"
        _codex_exec "check_code_quality" "{}"
    else
        # Convert space-separated files to JSON array
        local file_array="["
        for file in $files; do
            file_array+="\"$file\","
        done
        file_array="${file_array%,}]"  # Remove trailing comma and close array
        
        _codex_exec "check_code_quality" "{\"file_paths\": $file_array}"
    fi
}

# codex-save - Save current transcript
codex-save() {
    _codex_exec "save_current_transcript" "{}"
}

# codex-task-add [title] - Create task
codex-task-add() {
    local title="$*"
    
    if [ -z "$title" ]; then
        print_error "Task title is required"
        echo "Usage: codex-task-add <title> [description]"
        return 1
    fi
    
    _codex_exec "create_task" "{\"title\": \"$title\"}"
}

# codex-task-list - List tasks
codex-task-list() {
    local filter="${1:-}"
    
    if [ -z "$filter" ]; then
        _codex_exec "list_tasks" "{}"
    else
        _codex_exec "list_tasks" "{\"filter_status\": \"$filter\"}"
    fi
}

# codex-search [query] - Web search
codex-search() {
    local query="$*"
    
    if [ -z "$query" ]; then
        print_error "Search query is required"
        echo "Usage: codex-search <query>"
        return 1
    fi
    
    _codex_exec "search_web" "{\"query\": \"$query\", \"num_results\": 5}"
}

# codex-agent [agent-name] [task] - Spawn agent
codex-agent() {
    local agent_name="$1"
    local task="$2"
    
    if [ -z "$agent_name" ] || [ -z "$task" ]; then
        print_error "Agent name and task are required"
        echo "Usage: codex-agent <agent-name> <task>"
        return 1
    fi
    
    _codex_exec "spawn_agent" "{\"agent_name\": \"$agent_name\", \"task\": \"$task\"}"
}

# codex-status - Show session status
codex-status() {
    print_status "Codex Session Status"
    echo "Profile: ${CODEX_PROFILE:-development}"
    echo "Backend: ${AMPLIFIER_BACKEND:-codex}"
    echo "Memory System: ${MEMORY_SYSTEM_ENABLED:-true}"
    
    # Try to get MCP server status
    if _check_codex; then
        print_success "Codex CLI available"
    else
        print_error "Codex CLI not available"
    fi
    
    # Check if we're in a project directory
    if [ -d ".codex" ] && [ -d ".venv" ]; then
        print_success "Project environment ready"
    else
        print_warning "Project environment incomplete"
    fi
}

# codex-help - Show available shortcuts
codex-help() {
    echo "Codex Shortcuts - Quick commands for common workflows"
    echo ""
    echo "Available shortcuts:"
    echo "  codex-init [context]     - Initialize session with optional context"
    echo "  codex-check [files...]   - Run quality checks on files"
    echo "  codex-save               - Save current transcript"
    echo "  codex-task-add <title>   - Create a new task"
    echo "  codex-task-list [filter] - List tasks (optional status filter)"
    echo "  codex-search <query>     - Search the web"
    echo "  codex-agent <name> <task>- Spawn an agent with a task"
    echo "  codex-status             - Show session status"
    echo "  codex-help               - Show this help message"
    echo ""
    echo "Examples:"
    echo "  codex-init \"Working on authentication\""
    echo "  codex-check src/*.py"
    echo "  codex-task-add \"Fix login bug\""
    echo "  codex-task-list pending"
    echo "  codex-search \"python async best practices\""
    echo "  codex-agent code-review \"Review the new feature\""
    echo ""
    echo "Note: These shortcuts require an active Codex session to work."
}

# Bash completion function
_codex_completion() {
    local cur prev words cword
    _init_completion || return
    
    case $prev in
        codex-agent)
            # Complete agent names (common ones, could be extended)
            COMPREPLY=( $(compgen -W "code-review bug-hunter test-writer refactor-architect" -- "$cur") )
            ;;
        codex-task-list)
            # Complete status filters
            COMPREPLY=( $(compgen -W "pending in-progress completed all" -- "$cur") )
            ;;
        codex-init|codex-check|codex-task-add|codex-search)
            # File completion for relevant commands
            _filedir
            ;;
        *)
            # Default to no completion
            ;;
    esac
}

# Enable completion for all codex-* functions
complete -F _codex_completion codex-init
complete -F _codex_completion codex-check
complete -F _codex_completion codex-save
complete -F _codex_completion codex-task-add
complete -F _codex_completion codex-task-list
complete -F _codex_completion codex-search
complete -F _codex_completion codex-agent
complete -F _codex_completion codex-status
complete -F _codex_completion codex-help

print_success "Codex shortcuts loaded. Type 'codex-help' for usage information."