# Project Planner: AI-Driven Multi-Agent Project Orchestration

**Turn complex projects into coordinated task execution across specialized AI agents.**

## The Problem

Managing complex projects with multiple interconnected tasks is challenging:

- **Manual coordination** - Breaking down projects and coordinating execution takes significant time
- **Context switching** - Jumping between different types of work (coding, documentation, testing) disrupts flow
- **Agent specialization** - Different tasks need different expertise, but coordination is manual
- **State management** - Tracking progress across multiple sessions and agents is error-prone
- **Dependency complexity** - Understanding what can be done in parallel vs. sequentially requires constant mental overhead

## The Solution

Project Planner is a persistent AI planning system that:

1. **Analyzes project complexity** - Uses AI to break down high-level goals into actionable tasks
2. **Builds dependency graphs** - Creates hierarchical task structures with proper dependency management
3. **Assigns specialized agents** - Maps tasks to the most appropriate AI agents based on capability
4. **Coordinates execution** - Orchestrates multi-agent workflows with proper sequencing
5. **Persists across sessions** - Maintains project state and progress through multiple amplifier invocations

**The result**: Complex projects execute themselves through coordinated AI agents, while you focus on high-level decisions.

## Quick Start

**Prerequisites**: Complete the [Amplifier setup instructions](../../README.md#-step-by-step-setup) first.

### Initialize Project Planning

```bash
# Initialize project with planning
make project-init PROJECT_NAME="My Web App"

# Or manually
uv run python -m scenarios.project_planner init --name "My Web App"
```

### Plan Project Tasks

```bash
# AI-driven task decomposition
make project-plan

# Or with specific goals
uv run python -m scenarios.project_planner plan --goals "Build user authentication system"
```

### Execute Coordinated Workflow

```bash
# Execute tasks with multi-agent coordination
make project-execute

# Check status and progress
make project-status
```

## Core Features

### 🧠 AI Task Decomposition
- Natural language project description → structured task hierarchy
- Intelligent dependency detection and management
- Automatic subtask generation for complex work

### 🤖 Multi-Agent Coordination
- Maps tasks to specialized agents (zen-architect, bug-hunter, test-coverage, etc.)
- Parallel execution where dependencies allow
- Context sharing between related agents

### 💾 Persistent State Management
- Project context survives across amplifier sessions
- Progress tracking with automatic checkpointing
- Resumable workflows after interruptions

### 📊 Intelligent Progress Monitoring
- Real-time dependency resolution
- Bottleneck identification and suggestions
- Completion estimation and milestone tracking

## Project Structure

```
.amplifier/
├── project.json          # Project configuration and metadata
└── sessions/
    └── planning_*.json    # Session state for resumable workflows

data/planner/projects/
└── {project_id}.json     # Task hierarchy and dependency graph
```

## Integration with Amplifier

Project Planner integrates seamlessly with amplifier's core workflow:

- **Auto-detection**: Amplifier automatically detects project context via `.amplifier/project.json`
- **Cross-session state**: Planning context persists across amplifier invocations
- **Agent coordination**: Uses amplifier's existing agent ecosystem for task execution
- **Zero configuration**: Works without setup once project is initialized

## Advanced Usage

### Custom Task Hierarchies

```python
# Define custom task breakdown
uv run python -m scenarios.project_planner plan \
  --template custom_hierarchy.json \
  --depth 4
```

### Agent Assignment Control

```python
# Control which agents handle which tasks
uv run python -m scenarios.project_planner assign \
  --task "backend-api" \
  --agent zen-architect
```

### Workflow Orchestration

```python
# Execute specific workflow patterns
uv run python -m scenarios.project_planner execute \
  --pattern parallel_branches \
  --max_agents 3
```

## Philosophy

Project Planner embodies amplifier's core principle: **"Code for structure, AI for intelligence"**

- **Structure**: Reliable task management, dependency tracking, and state persistence
- **Intelligence**: AI-driven planning, agent coordination, and adaptive execution

The result is a system that handles the mechanical complexity of project orchestration while letting AI agents focus on the creative and technical work they do best.