#!/bin/bash

# Codex Shortcuts - Quick commands for common Codex workflows
# Source this file in your shell or via amplify-codex.sh for convenient access
#
# Usage: source .codex/tools/codex_shortcuts.sh

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Quick session initialization
codex-init() {
    local context="${1:-Starting development session}"
    echo -e "${BLUE}Initializing Codex session...${NC}"
    uv run python .codex/tools/session_init.py "$context"
}

# Run quality checks on files
codex-check() {
    if [ $# -eq 0 ]; then
        # No arguments - run on all Python files
        echo -e "${BLUE}Running quality checks on all Python files...${NC}"
        make check
    else
        # Run on specific files
        echo -e "${BLUE}Running quality checks on specified files...${NC}"
        for file in "$@"; do
            if [ -f "$file" ]; then
                echo "Checking: $file"
                uv run ruff check "$file"
                uv run pyright "$file"
            else
                echo -e "${YELLOW}Warning: File not found: $file${NC}"
            fi
        done
    fi
}

# Save current transcript
codex-save() {
    echo -e "${BLUE}Saving current transcript...${NC}"
    uv run python -c "
from amplifier.core.backend import BackendFactory
backend = BackendFactory.create(backend_type='codex')
result = backend.export_transcript()
print(f'Transcript saved: {result}')
"
}

# Task management shortcuts
codex-task-add() {
    local title="${1:-Untitled Task}"
    local description="${2:-}"
    local priority="${3:-medium}"
    
    echo -e "${BLUE}Creating task: $title${NC}"
    uv run python -c "
import asyncio
import json
from pathlib import Path

async def create_task():
    # Simple task creation without MCP overhead
    tasks_file = Path('.codex/tasks/session_tasks.json')
    
    if not tasks_file.exists():
        data = {'tasks': [], 'metadata': {}}
    else:
        with open(tasks_file) as f:
            data = json.load(f)
    
    from datetime import datetime
    import uuid
    
    task = {
        'id': str(uuid.uuid4()),
        'title': '$title',
        'description': '$description',
        'priority': '$priority',
        'status': 'pending',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'completed_at': None
    }
    
    data['tasks'].append(task)
    
    with open(tasks_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f\"Task created: {task['id']}\")
    return task

asyncio.run(create_task())
"
}

# List tasks
codex-task-list() {
    local filter="${1:-}"
    
    echo -e "${BLUE}Tasks:${NC}"
    uv run python -c "
import json
from pathlib import Path

tasks_file = Path('.codex/tasks/session_tasks.json')

if not tasks_file.exists():
    print('No tasks found')
else:
    with open(tasks_file) as f:
        data = json.load(f)
    
    tasks = data.get('tasks', [])
    
    if '$filter':
        tasks = [t for t in tasks if t['status'] == '$filter']
    
    if not tasks:
        print('No tasks found')
    else:
        for task in tasks:
            status_emoji = {'pending': '⏳', 'in_progress': '🔄', 'completed': '✅', 'cancelled': '❌'}.get(task['status'], '❓')
            priority_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(task['priority'], '⚪')
            print(f\"{status_emoji} {priority_emoji} [{task['status']}] {task['title']} (ID: {task['id'][:8]})\")
"
}

# Web search shortcut
codex-search() {
    local query="$*"
    
    if [ -z "$query" ]; then
        echo -e "${YELLOW}Usage: codex-search <query>${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Searching for: $query${NC}"
    # This would call the web research MCP server
    # For now, just a placeholder
    echo "Web search functionality requires active Codex session with MCP servers"
}

# Spawn agent shortcut
codex-agent() {
    local agent_name="${1:-}"
    local task="${2:-}"
    
    if [ -z "$agent_name" ]; then
        echo -e "${YELLOW}Usage: codex-agent <agent-name> <task>${NC}"
        echo "Available agents: zen-architect, bug-hunter, test-coverage, etc."
        return 1
    fi
    
    if [ -z "$task" ]; then
        echo -e "${YELLOW}Please specify a task for the agent${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Spawning agent: $agent_name${NC}"
    echo -e "${BLUE}Task: $task${NC}"
    
    codex exec "$agent_name" --prompt "$task"
}

# Show session status
codex-status() {
    echo -e "${BLUE}=== Codex Session Status ===${NC}"
    echo ""
    
    # Git info
    if git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${GREEN}Git:${NC}"
        echo "  Branch: $(git branch --show-current)"
        echo "  Status: $(git status --short | wc -l) files modified"
        echo ""
    fi
    
    # Tasks
    if [ -f ".codex/tasks/session_tasks.json" ]; then
        local pending_count=$(uv run python -c "import json; data = json.load(open('.codex/tasks/session_tasks.json')); print(len([t for t in data.get('tasks', []) if t['status'] == 'pending']))")
        local in_progress_count=$(uv run python -c "import json; data = json.load(open('.codex/tasks/session_tasks.json')); print(len([t for t in data.get('tasks', []) if t['status'] == 'in_progress']))")
        local completed_count=$(uv run python -c "import json; data = json.load(open('.codex/tasks/session_tasks.json')); print(len([t for t in data.get('tasks', []) if t['status'] == 'completed']))")
        
        echo -e "${GREEN}Tasks:${NC}"
        echo "  Pending: $pending_count"
        echo "  In Progress: $in_progress_count"
        echo "  Completed: $completed_count"
        echo ""
    fi
    
    # Memory system
    if [ -d "amplifier_data/memory" ]; then
        local memory_count=$(find amplifier_data/memory -name "*.jsonl" -exec wc -l {} \; 2>/dev/null | awk '{sum += $1} END {print sum}')
        echo -e "${GREEN}Memory System:${NC}"
        echo "  Stored memories: ${memory_count:-0}"
        echo ""
    fi
    
    # Recent logs
    if [ -f ".codex/logs/session_init.log" ]; then
        echo -e "${GREEN}Recent Activity:${NC}"
        echo "  Last session init: $(ls -lh .codex/logs/session_init.log | awk '{print $6, $7, $8}')"
    fi
    
    if [ -f ".codex/logs/auto_saves.log" ]; then
        local last_save=$(tail -n 1 .codex/logs/auto_saves.log | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}' || echo "Never")
        echo "  Last auto-save: $last_save"
    fi
}

# Show help
codex-help() {
    echo -e "${GREEN}=== Codex Shortcuts ===${NC}"
    echo ""
    echo -e "${BLUE}Session Management:${NC}"
    echo "  codex-init [context]           - Initialize session with context"
    echo "  codex-save                     - Save current transcript"
    echo "  codex-status                   - Show session status"
    echo ""
    echo -e "${BLUE}Quality & Testing:${NC}"
    echo "  codex-check [files...]         - Run quality checks (default: all files)"
    echo ""
    echo -e "${BLUE}Task Management:${NC}"
    echo "  codex-task-add <title> [desc] [priority]  - Create new task"
    echo "  codex-task-list [status]                  - List tasks (pending/in_progress/completed)"
    echo ""
    echo -e "${BLUE}Research:${NC}"
    echo "  codex-search <query>           - Search the web (requires active session)"
    echo ""
    echo -e "${BLUE}Agents:${NC}"
    echo "  codex-agent <name> <task>      - Spawn an agent for a specific task"
    echo ""
    echo -e "${BLUE}Help:${NC}"
    echo "  codex-help                     - Show this help message"
    echo ""
}

# Bash completion for common functions
if [ -n "$BASH_VERSION" ]; then
    _codex_agent_completion() {
        local agents="zen-architect bug-hunter test-coverage modular-builder integration-specialist performance-optimizer api-contract-designer"
        COMPREPLY=($(compgen -W "$agents" -- "${COMP_WORDS[1]}"))
    }
    
    complete -F _codex_agent_completion codex-agent
    
    _codex_task_list_completion() {
        local statuses="pending in_progress completed cancelled"
        COMPREPLY=($(compgen -W "$statuses" -- "${COMP_WORDS[1]}"))
    }
    
    complete -F _codex_task_list_completion codex-task-list
fi

# Print help on source
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    # Script is being executed, not sourced
    codex-help
else
    # Script is being sourced
    echo -e "${GREEN}Codex shortcuts loaded!${NC} Type ${BLUE}codex-help${NC} for available commands."
fi
