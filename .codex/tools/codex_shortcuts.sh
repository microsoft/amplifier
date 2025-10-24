#!/bin/bash

# Codex Shortcuts - Command shortcuts and workflow aliases for Codex integration
#
# This script provides convenient bash functions that wrap common Codex workflows,
# similar to Claude Code's slash commands. These functions call the Amplifier backend
# directly for quick operations.
#
# Usage:
#   source .codex/tools/codex_shortcuts.sh
#   codex-init "Hello world"
#   codex-task-add "Fix bug"
#   codex-agent "zen-code-architect" "Refactor this code"

# Colors for output (matching wrapper script)
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

# codex-init [context] - Quick session initialization
codex-init() {
    context="$*"
    if [ -z "$context" ]; then
        print_error "Usage: codex-init <context>"
        return 1
    fi

    print_status "Initializing session with context: $context"
    python3 << EOF
import os
os.environ['AMPLIFIER_BACKEND'] = 'codex'
os.environ['AMPLIFIER_ROOT'] = '.'
from amplifier.core.backend import get_backend
backend = get_backend()
result = backend.initialize_session(prompt="$context")
if result['success']:
    print("Session initialized successfully")
else:
    print(f"Error: {result.get('metadata', {}).get('error', 'Unknown error')}")
EOF
}

# codex-check [files...] - Run quality checks
codex-check() {
    files="$*"
    if [ -z "$files" ]; then
        print_error "Usage: codex-check <file1> [file2...]"
        return 1
    fi

    print_status "Running quality checks on: $files"
    python3 << EOF
import os
import sys
os.environ['AMPLIFIER_BACKEND'] = 'codex'
os.environ['AMPLIFIER_ROOT'] = '.'
from amplifier.core.backend import get_backend
backend = get_backend()
files_list = "$files".split()
result = backend.run_quality_checks(file_paths=files_list)
if result['success']:
    print("Quality checks passed")
else:
    print(f"Quality checks failed: {result.get('metadata', {}).get('error', 'Unknown error')}")
EOF
}

# codex-save - Save current transcript
codex-save() {
    print_status "Saving current transcript"
    python3 << EOF
import os
os.environ['AMPLIFIER_BACKEND'] = 'codex'
os.environ['AMPLIFIER_ROOT'] = '.'
from amplifier.core.backend import get_backend
backend = get_backend()
result = backend.export_transcript()
if result['success']:
    print(f"Transcript saved: {result['data'].get('path', 'Unknown path')}")
else:
    print(f"Error: {result.get('metadata', {}).get('error', 'Unknown error')}")
EOF
}

# codex-task-add [title] - Create task
codex-task-add() {
    title="$*"
    if [ -z "$title" ]; then
        print_error "Usage: codex-task-add <title> [description] [priority]"
        return 1
    fi

    print_status "Creating task: $title"
    python3 << EOF
import os
os.environ['AMPLIFIER_BACKEND'] = 'codex'
os.environ['AMPLIFIER_ROOT'] = '.'
from amplifier.core.backend import get_backend
backend = get_backend()
result = backend.manage_tasks('create', title="$title")
if result['success']:
    print("Task created successfully")
else:
    print(f"Error: {result.get('metadata', {}).get('error', 'Unknown error')}")
EOF
}

# codex-task-list - List tasks
codex-task-list() {
    filter="${1:-}"
    print_status "Listing tasks${filter:+ (filter: $filter)}"
    python3 << EOF
import os
import json
os.environ['AMPLIFIER_BACKEND'] = 'codex'
os.environ['AMPLIFIER_ROOT'] = '.'
from amplifier.core.backend import get_backend
backend = get_backend()
result = backend.manage_tasks('list', filter_status="$filter" if "$filter" else None)
if result['success']:
    tasks = result['data'].get('tasks', [])
    if tasks:
        for task in tasks[:5]:  # Show first 5
            status = task.get('status', 'unknown')
            priority = task.get('priority', 'medium')
            title = task.get('title', 'Untitled')
            print(f"• [{status}] {priority}: {title}")
        if len(tasks) > 5:
            print(f"... and {len(tasks) - 5} more tasks")
    else:
        print("No tasks found")
else:
    print(f"Error: {result.get('metadata', {}).get('error', 'Unknown error')}")
EOF
}

# codex-search [query] - Web search
codex-search() {
    query="$*"
    if [ -z "$query" ]; then
        print_error "Usage: codex-search <query>"
        return 1
    fi

    print_status "Searching web for: $query"
    python3 << EOF
import os
os.environ['AMPLIFIER_BACKEND'] = 'codex'
os.environ['AMPLIFIER_ROOT'] = '.'
from amplifier.core.backend import get_backend
backend = get_backend()
result = backend.search_web(query="$query", num_results=3)
if result['success']:
    results = result['data']
    if results:
        print("Search results:")
        for i, res in enumerate(results[:3], 1):
            title = res.get('title', 'No title')[:50]
            url = res.get('url', 'No URL')
            print(f"{i}. {title}")
            print(f"   {url}")
    else:
        print("No results found")
else:
    print(f"Error: {result.get('metadata', {}).get('error', 'Unknown error')}")
EOF
}

# codex-agent [agent-name] [task] - Spawn agent
codex-agent() {
    agent_name="$1"
    shift
    task="$*"
    if [ -z "$agent_name" ] || [ -z "$task" ]; then
        print_error "Usage: codex-agent <agent-name> <task>"
        return 1
    fi

    print_status "Spawning agent $agent_name with task: $task"
    python3 << EOF
import os
os.environ['AMPLIFIER_BACKEND'] = 'codex'
os.environ['AMPLIFIER_ROOT'] = '.'
from amplifier.core.agent_backend import get_agent_backend
backend = get_agent_backend()
result = backend.spawn_agent(agent_name="$agent_name", task="$task")
if result['success']:
    print("Agent completed successfully")
    print("Result:", result.get('result', 'No result')[:200])
else:
    print(f"Error: {result.get('metadata', {}).get('error', 'Unknown error')}")
EOF
}

# codex-status - Show session status
codex-status() {
    print_status "Checking Codex status"
    python3 << EOF
import os
os.environ['AMPLIFIER_BACKEND'] = 'codex'
os.environ['AMPLIFIER_ROOT'] = '.'
from amplifier.core.backend import get_backend
from amplifier.core.agent_backend import get_agent_backend
backend = get_backend()
agent_backend = get_agent_backend()
capabilities = backend.get_capabilities()
agents = agent_backend.list_available_agents()
print("Backend capabilities:")
for key, value in capabilities.items():
    print(f"  {key}: {value}")
print(f"Available agents: {', '.join(agents) if agents else 'None'}")
EOF
}

# Help function
codex-help() {
    echo "Codex Shortcuts - Quick commands for Codex workflows"
    echo ""
    echo "Available commands:"
    echo "  codex-init <context>     Initialize session with context"
    echo "  codex-check <files...>   Run quality checks on files"
    echo "  codex-save               Save current transcript"
    echo "  codex-task-add <title>   Create a new task"
    echo "  codex-task-list [filter] List tasks (optional status filter)"
    echo "  codex-search <query>     Search the web"
    echo "  codex-agent <name> <task> Spawn an agent"
    echo "  codex-status             Show backend status"
    echo "  codex-help               Show this help"
    echo ""
    echo "Examples:"
    echo "  codex-init 'Refactor the authentication module'"
    echo "  codex-check src/*.py tests/*.py"
    echo "  codex-task-add 'Fix login bug' 'The login form validation is broken'"
    echo "  codex-task-list completed"
    echo "  codex-search 'python async best practices'"
    echo "  codex-agent zen-code-architect 'Review this PR'"
}

# Bash completion setup
if [ -n "$BASH_VERSION" ]; then
    # Completion for codex-agent (agent names)
    _codex_agent_completion() {
        local agents=("zen-code-architect" "architecture-reviewer" "bug-hunter" "test-coverage" "modular-builder" "refactor-architect" "integration-specialist")
        COMPREPLY=($(compgen -W "${agents[*]}" -- "${COMP_WORDS[1]}"))
    }
    complete -F _codex_agent_completion codex-agent

    # Completion for codex-task-list (status filters)
    _codex_task_list_completion() {
        local filters=("pending" "in_progress" "completed")
        COMPREPLY=($(compgen -W "${filters[*]}" -- "${COMP_WORDS[1]}"))
    }
    complete -F _codex_task_list_completion codex-task-list

    # Completion for codex-check (files)
    _codex_check_completion() {
        COMPREPLY=($(compgen -f -- "${COMP_WORDS[COMP_CWORD]}"))
    }
    complete -F _codex_check_completion codex-check
fi

# Export functions to make them available
export -f codex-init
export -f codex-check
export -f codex-save
export -f codex-task-add
export -f codex-task-list
export -f codex-search
export -f codex-agent
export -f codex-status
export -f codex-help