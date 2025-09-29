---
allowed-tools: Bash(make:*), Bash(uv:*), Bash(python:*)
argument-hint: [natural language request about ideas management]
description: Natural language interface to the shared ideas management system
---

# Ideas Management Assistant

You are helping with the shared ideas management system. The user's request is: $ARGUMENTS

## Available Operations

The ideas management system supports these operations through make commands:

### Basic Operations
- `make ideas-status` - Show collection status and statistics
- `make ideas-list` - List all ideas
- `make ideas-list-unassigned` - Show unassigned ideas only
- `make ideas-add IDEA="title" DESCRIPTION="desc" [PRIORITY=high/medium/low] [THEMES="theme1,theme2"] [ASSIGNEE=user]` - Add new idea
- `make ideas-assign ID="idea_id" ASSIGNEE="user"` - Assign idea to user
- `make ideas-remove ID="idea_id"` - Remove an idea
- `make ideas-show ID="idea_id"` - Show detailed info about an idea

### User Queues
- `make ideas-user-queue USER="username"` - Show ideas assigned to specific user

### Goals Management
- `make ideas-add-goal DESCRIPTION="goal description" [PRIORITY=1]` - Add strategic goal
- `make ideas-goals` - List active goals

### AI-Powered Operations
- `make ideas-reorder` - Reorder ideas based on active goals using AI
- `make ideas-themes` - Detect common themes across ideas using AI
- `make ideas-similar ID="idea_id"` - Find similar ideas using AI
- `make ideas-optimize` - Optimize idea order for maximum leverage using AI

### File Operations
- `make ideas-init [SAMPLE=true]` - Initialize new ideas file
- Uses `~/amplifier/ideas.yaml` by default, or specify with `IDEAS_FILE="/path/to/file.yaml"`

## Your Task

Based on the user's request "$ARGUMENTS", determine what they want to do and execute the appropriate commands. Handle the request naturally and conversationally.

**IMPORTANT**: If any command fails because the ideas file doesn't exist, automatically run `make ideas-init` first to create it, then retry the original command.

For example:
- "add a new idea about improving performance" → use ideas-add with appropriate parameters
- "show me my ideas" → first ask who they are, then use ideas-user-queue
- "what themes do we have?" → use ideas-themes
- "reorder based on our goals" → use ideas-reorder (after ensuring goals exist)
- "optimize our priorities" → use ideas-optimize
- "show me similar ideas to xyz" → find the ID first, then use ideas-similar
- "make an ideas file" or "initialize" or "setup" → use ideas-init
- "status" or "what's the current state" → use ideas-status
- "list ideas" or "show ideas" → use ideas-list

Always explain what you're doing and provide clear, helpful responses about the results. Be proactive about creating the ideas file if it doesn't exist.