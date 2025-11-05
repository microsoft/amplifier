#!/bin/bash

# Codex Shortcuts - Quick commands for common Codex workflows
# Source this file in your shell or via amplify-codex.sh for convenient access
#
# Usage: source .codex/tools/codex_shortcuts.sh

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper: Check Codex availability and configuration
codex-shortcuts-check() {
    local silent="${1:-false}"

    # Check for codex CLI
    if ! command -v codex &> /dev/null; then
        if [ "$silent" != "true" ]; then
            echo -e "${RED}Error: Codex CLI not found. Install from https://github.com/xai-org/codex${NC}" >&2
        fi
        return 1
    fi

    # Check for config.toml
    if [ ! -f ".codex/config.toml" ]; then
        if [ "$silent" != "true" ]; then
            echo -e "${RED}Error: .codex/config.toml not found. Ensure you're in the project directory.${NC}" >&2
        fi
        return 1
    fi

    return 0
}

# Quick session initialization
codex-init() {
    local context="${1:-Starting development session}"

    codex-shortcuts-check || return 1

    echo -e "${BLUE}Initializing Codex session...${NC}"
    uv run python .codex/tools/session_init.py "$context" || {
        echo -e "${RED}Session initialization failed${NC}" >&2
        return 1
    }
}

# Run quality checks on files
codex-check() {
    codex-shortcuts-check || return 1

    if [ $# -eq 0 ]; then
        # No arguments - run on all Python files
        echo -e "${BLUE}Running quality checks on all Python files...${NC}"
        make check || {
            echo -e "${RED}Quality checks failed${NC}" >&2
            return 1
        }
    else
        # Run on specific files
        echo -e "${BLUE}Running quality checks on specified files...${NC}"
        for file in "$@"; do
            if [ -f "$file" ]; then
                echo "Checking: $file"
                uv run ruff check "$file" || echo -e "${YELLOW}Ruff check failed for $file${NC}"
                uv run pyright "$file" || echo -e "${YELLOW}Pyright check failed for $file${NC}"
            else
                echo -e "${YELLOW}Warning: File not found: $file${NC}"
            fi
        done
    fi
}

# Save current transcript
codex-save() {
    codex-shortcuts-check || return 1

    echo -e "${BLUE}Saving current transcript...${NC}"
    uv run python -c "
from amplifier.core.backend import BackendFactory
backend = BackendFactory.create(backend_type='codex')
result = backend.export_transcript()
print(f'Transcript saved: {result}')
" || {
        echo -e "${RED}Failed to save transcript${NC}" >&2
        return 1
    }
}

# Task management shortcuts
codex-task-add() {
    codex-shortcuts-check || return 1

    local title="${1:-Untitled Task}"
    local description="${2:-}"
    local priority="${3:-medium}"

    echo -e "${BLUE}Creating task: $title${NC}"

    # Use MCP tool via codex CLI
    codex tool amplifier_tasks.create_task \
        --args "{\"title\": \"$title\", \"description\": \"$description\", \"priority\": \"$priority\"}" 2>&1 || {
        echo -e "${RED}Failed to create task via MCP. Ensure amplifier_tasks server is active.${NC}" >&2
        return 1
    }
}

# List tasks
codex-task-list() {
    codex-shortcuts-check || return 1

    local filter="${1:-}"

    echo -e "${BLUE}Tasks:${NC}"

    # Use MCP tool via codex CLI
    if [ -n "$filter" ]; then
        codex tool amplifier_tasks.list_tasks --args "{\"filter_status\": \"$filter\"}" 2>&1 || {
            echo -e "${RED}Failed to list tasks via MCP. Ensure amplifier_tasks server is active.${NC}" >&2
            return 1
        }
    else
        codex tool amplifier_tasks.list_tasks 2>&1 || {
            echo -e "${RED}Failed to list tasks via MCP. Ensure amplifier_tasks server is active.${NC}" >&2
            return 1
        }
    fi
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

# Agent analytics shortcuts
codex-analytics-stats() {
    codex-shortcuts-check || return 1

    echo -e "${BLUE}Getting agent execution statistics...${NC}"
    codex tool amplifier_agent_analytics.get_agent_stats 2>&1 || {
        echo -e "${RED}Failed to get analytics stats. Ensure amplifier_agent_analytics server is active.${NC}" >&2
        return 1
    }
}

codex-analytics-recommendations() {
    local task="${1:-}"

    if [ -z "$task" ]; then
        echo -e "${YELLOW}Usage: codex-analytics-recommendations <task-description>${NC}"
        return 1
    fi

    codex-shortcuts-check || return 1

    echo -e "${BLUE}Getting agent recommendations for: $task${NC}"
    codex tool amplifier_agent_analytics.get_agent_recommendations --args "{\"current_task\": \"$task\"}" 2>&1 || {
        echo -e "${RED}Failed to get recommendations. Ensure amplifier_agent_analytics server is active.${NC}" >&2
        return 1
    }
}

codex-analytics-report() {
    local format="${1:-markdown}"

    codex-shortcuts-check || return 1

    echo -e "${BLUE}Generating agent analytics report...${NC}"
    codex tool amplifier_agent_analytics.export_agent_report --args "{\"format\": \"$format\"}" 2>&1 || {
        echo -e "${RED}Failed to generate report. Ensure amplifier_agent_analytics server is active.${NC}" >&2
        return 1
    }
}

# Memory management shortcuts
codex-memory-suggest() {
    local context="${1:-current work}"
    local limit="${2:-5}"

    codex-shortcuts-check || return 1

    echo -e "${BLUE}Suggesting relevant memories for: $context${NC}"
    codex tool amplifier_memory_enhanced.suggest_relevant_memories --args "{\"current_context\": \"$context\", \"limit\": $limit}" 2>&1 || {
        echo -e "${RED}Failed to get memory suggestions. Ensure amplifier_memory_enhanced server is active.${NC}" >&2
        return 1
    }
}

codex-memory-tag() {
    local memory_id="${1:-}"
    local tags="${2:-}"

    if [ -z "$memory_id" ] || [ -z "$tags" ]; then
        echo -e "${YELLOW}Usage: codex-memory-tag <memory-id> <tags>${NC}"
        echo "Example: codex-memory-tag mem_123 'important,bugfix'"
        return 1
    fi

    codex-shortcuts-check || return 1

    echo -e "${BLUE}Tagging memory $memory_id with: $tags${NC}"
    # Convert comma-separated tags to JSON array
    local tag_array=$(echo "$tags" | sed 's/,/","/g' | sed 's/^/["/' | sed 's/$/"]/')
    codex tool amplifier_memory_enhanced.tag_memory --args "{\"memory_id\": \"$memory_id\", \"tags\": $tag_array}" 2>&1 || {
        echo -e "${RED}Failed to tag memory. Ensure amplifier_memory_enhanced server is active.${NC}" >&2
        return 1
    }
}

codex-memory-related() {
    local memory_id="${1:-}"

    if [ -z "$memory_id" ]; then
        echo -e "${YELLOW}Usage: codex-memory-related <memory-id>${NC}"
        return 1
    fi

    codex-shortcuts-check || return 1

    echo -e "${BLUE}Finding memories related to: $memory_id${NC}"
    codex tool amplifier_memory_enhanced.find_related_memories --args "{\"memory_id\": \"$memory_id\"}" 2>&1 || {
        echo -e "${RED}Failed to find related memories. Ensure amplifier_memory_enhanced server is active.${NC}" >&2
        return 1
    }
}

codex-memory-score() {
    local memory_id="${1:-}"

    if [ -z "$memory_id" ]; then
        echo -e "${YELLOW}Usage: codex-memory-score <memory-id>${NC}"
        return 1
    fi

    codex-shortcuts-check || return 1

    echo -e "${BLUE}Scoring quality of memory: $memory_id${NC}"
    codex tool amplifier_memory_enhanced.score_memory_quality --args "{\"memory_id\": \"$memory_id\"}" 2>&1 || {
        echo -e "${RED}Failed to score memory. Ensure amplifier_memory_enhanced server is active.${NC}" >&2
        return 1
    }
}

codex-memory-cleanup() {
    local threshold="${1:-0.3}"

    codex-shortcuts-check || return 1

    echo -e "${BLUE}Cleaning up memories with quality threshold: $threshold${NC}"
    codex tool amplifier_memory_enhanced.cleanup_memories --args "{\"quality_threshold\": $threshold}" 2>&1 || {
        echo -e "${RED}Failed to cleanup memories. Ensure amplifier_memory_enhanced server is active.${NC}" >&2
        return 1
    }
}

codex-memory-insights() {
    codex-shortcuts-check || return 1

    echo -e "${BLUE}Getting memory system insights...${NC}"
    codex tool amplifier_memory_enhanced.get_memory_insights 2>&1 || {
        echo -e "${RED}Failed to get memory insights. Ensure amplifier_memory_enhanced server is active.${NC}" >&2
        return 1
    }
}

# Hooks management shortcuts
codex-hooks-list() {
    codex-shortcuts-check || return 1

    echo -e "${BLUE}Listing active hooks...${NC}"
    codex tool amplifier_hooks.list_active_hooks 2>&1 || {
        echo -e "${RED}Failed to list hooks. Ensure amplifier_hooks server is active.${NC}" >&2
        return 1
    }
}

codex-hooks-trigger() {
    local hook_id="${1:-}"

    if [ -z "$hook_id" ]; then
        echo -e "${YELLOW}Usage: codex-hooks-trigger <hook-id>${NC}"
        return 1
    fi

    codex-shortcuts-check || return 1

    echo -e "${BLUE}Triggering hook: $hook_id${NC}"
    codex tool amplifier_hooks.trigger_hook_manually --args "{\"hook_id\": \"$hook_id\"}" 2>&1 || {
        echo -e "${RED}Failed to trigger hook. Ensure amplifier_hooks server is active.${NC}" >&2
        return 1
    }
}

codex-hooks-watch() {
    local enable="${1:-true}"
    local patterns="${2:-*.py,*.js,*.ts}"
    local interval="${3:-5}"

    codex-shortcuts-check || return 1

    if [ "$enable" = "true" ]; then
        echo -e "${BLUE}Enabling file watching with patterns: $patterns${NC}"
        # Convert comma-separated patterns to JSON array
        local pattern_array=$(echo "$patterns" | sed 's/,/","/g' | sed 's/^/["/' | sed 's/$/"]/')
        codex tool amplifier_hooks.enable_watch_mode --args "{\"file_patterns\": $pattern_array, \"check_interval\": $interval}" 2>&1 || {
            echo -e "${RED}Failed to enable file watching. Ensure amplifier_hooks server is active.${NC}" >&2
            return 1
        }
    else
        echo -e "${BLUE}Disabling file watching...${NC}"
        codex tool amplifier_hooks.disable_watch_mode 2>&1 || {
            echo -e "${RED}Failed to disable file watching. Ensure amplifier_hooks server is active.${NC}" >&2
            return 1
        }
    fi
}

codex-hooks-history() {
    codex-shortcuts-check || return 1

    echo -e "${BLUE}Getting hook execution history...${NC}"
    codex tool amplifier_hooks.get_hook_history 2>&1 || {
        echo -e "${RED}Failed to get hook history. Ensure amplifier_hooks server is active.${NC}" >&2
        return 1
    }
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
    echo -e "${BLUE}Agent Analytics:${NC}"
    echo "  codex-analytics-stats                      - Get agent execution statistics"
    echo "  codex-analytics-recommendations <task>     - Get agent recommendations for a task"
    echo "  codex-analytics-report [format]            - Export analytics report (markdown/json)"
    echo ""
    echo -e "${BLUE}Memory Management:${NC}"
    echo "  codex-memory-suggest [context] [limit]     - Suggest relevant memories"
    echo "  codex-memory-tag <id> <tags>               - Tag a memory (comma-separated)"
    echo "  codex-memory-related <id> [limit]          - Find related memories"
    echo "  codex-memory-score <id>                    - Score memory quality"
    echo "  codex-memory-cleanup [thresh]              - Cleanup low-quality memories"
    echo "  codex-memory-insights                      - Get memory system insights"
    echo ""
    echo -e "${BLUE}Hooks Management:${NC}"
    echo "  codex-hooks-list                           - List active hooks"
    echo "  codex-hooks-trigger <id>                   - Trigger a hook manually"
    echo "  codex-hooks-watch [true/false] [patterns] [interval] - Enable/disable file watching"
    echo "  codex-hooks-history [limit]                - Get hook execution history"
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
