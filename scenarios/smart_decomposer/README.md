# Smart Decomposer CLI Tool

An intelligent task decomposition and orchestration tool that breaks down high-level goals into actionable tasks and coordinates their execution using specialized AI agents.

## Overview

The Smart Decomposer provides a command-line interface for:
- **Decomposing** complex goals into hierarchical task structures
- **Assigning** specialized agents to tasks based on their capabilities
- **Executing** tasks with intelligent orchestration and dependency management
- **Tracking** project status and progress

## Installation

This tool is part of the amplifier project and uses the planner modules.

```bash
# Run from the amplifier root directory
make smart-decomposer ARGS="--help"
```

## Usage

### 1. Decompose a Goal

Break down a high-level goal into specific tasks:

```bash
# Basic usage
python -m scenarios.smart_decomposer decompose --goal "Build a REST API with authentication"

# With custom project ID and name
python -m scenarios.smart_decomposer decompose \
  --goal "Build a REST API with authentication" \
  --project-id "api-project" \
  --project-name "API Development" \
  --max-depth 3
```

### 2. Assign Agents

Assign specialized agents to tasks based on their requirements:

```bash
# Use default agent pool
python -m scenarios.smart_decomposer assign --project-id "api-project"

# Specify custom agents
python -m scenarios.smart_decomposer assign \
  --project-id "api-project" \
  --agents "zen-code-architect,modular-builder,test-coverage"
```

### 3. Execute Tasks

Execute the project with intelligent orchestration:

```bash
# Normal execution
python -m scenarios.smart_decomposer execute --project-id "api-project"

# With custom parallelism
python -m scenarios.smart_decomposer execute \
  --project-id "api-project" \
  --max-parallel 10

# Dry run to see what would be executed
python -m scenarios.smart_decomposer execute \
  --project-id "api-project" \
  --dry-run
```

### 4. Check Status

View the current status of a project:

```bash
# Basic status
python -m scenarios.smart_decomposer status --project-id "api-project"

# Detailed status with task samples
python -m scenarios.smart_decomposer status --project-id "api-project" --verbose
```

## Available Agents

The tool can assign the following specialized agents:

- **zen-code-architect**: Architecture and design tasks
- **modular-builder**: Implementation and construction tasks
- **bug-hunter**: Debugging and issue resolution
- **test-coverage**: Testing and validation tasks
- **refactor-architect**: Code refactoring and optimization
- **integration-specialist**: System integration tasks

## Project Storage

Projects are stored locally in:
```
~/.amplifier/smart_decomposer/projects/{project-id}.json
```

## Command Reference

### Global Options

- `-v, --verbose`: Show detailed output

### Commands

#### decompose
- `--goal GOAL`: The goal to decompose (required)
- `--project-id PROJECT_ID`: Custom project ID (auto-generated if not provided)
- `--project-name PROJECT_NAME`: Human-readable project name
- `--max-depth MAX_DEPTH`: Maximum decomposition depth (default: 3)

#### assign
- `--project-id PROJECT_ID`: Project to assign agents to (required)
- `--agents AGENTS`: Comma-separated list of available agents

#### execute
- `--project-id PROJECT_ID`: Project to execute (required)
- `--max-parallel N`: Maximum parallel task execution (default: 5)
- `--dry-run`: Simulate execution without running
- `--force`: Execute even with unassigned tasks

#### status
- `--project-id PROJECT_ID`: Project to check status for (required)

## Workflow Example

Complete workflow for a project:

```bash
# Step 1: Decompose the goal
python -m scenarios.smart_decomposer decompose \
  --goal "Build a user management system with authentication" \
  --project-id "user-system"

# Step 2: Assign agents to tasks
python -m scenarios.smart_decomposer assign --project-id "user-system"

# Step 3: Check the plan
python -m scenarios.smart_decomposer status --project-id "user-system" --verbose

# Step 4: Execute the project
python -m scenarios.smart_decomposer execute --project-id "user-system"

# Step 5: Check final status
python -m scenarios.smart_decomposer status --project-id "user-system"
```

## Integration

This tool integrates with the amplifier planner modules:
- `amplifier.planner.decomposer`: Task decomposition logic
- `amplifier.planner.agent_mapper`: Agent assignment logic
- `amplifier.planner.orchestrator`: Execution orchestration