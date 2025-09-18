# Amplifier Microtask - Phase 1 Implementation

A minimal demonstration of microtask-driven AI operations using the Amplifier pattern.

## Overview

This is a working implementation of the core concepts:
- **Microtask execution** via Claude Code SDK
- **Session persistence** with full recovery support
- **Pipeline orchestration** with incremental saves
- **CLI interface** for user interaction

## Installation

```bash
# Install dependencies
cd amplifier_microtask
uv sync

# Install Claude Code SDK (if not already installed)
npm install -g @anthropic-ai/claude-code

# Set API key
export ANTHROPIC_API_KEY="your-api-key"
```

## Quick Start

### 1. Initialize Workspace

```bash
python -m amplifier_microtask.cli init
```

This creates a workspace and example task file.

### 2. Run Example Pipeline

```bash
# Run the built-in example
python -m amplifier_microtask.cli example

# Or run with a task file
python -m amplifier_microtask.cli run examples/simple_task.json
```

### 3. Check Status

```bash
# List all sessions
python -m amplifier_microtask.cli list

# Check specific session
python -m amplifier_microtask.cli status <session-id>
```

### 4. Resume After Interruption

```bash
# If pipeline was interrupted
python -m amplifier_microtask.cli resume <session-id>
```

## Project Structure

```
amplifier_microtask/
├── storage.py      # Atomic file operations
├── session.py      # Session state management
├── agent.py        # Claude SDK integration
├── orchestrator.py # Pipeline execution
└── cli.py         # Command-line interface
```

## Key Features

- **120-second default timeout** for complex AI operations
- **Incremental saves** after every microtask
- **Full recovery** from any interruption
- **JSON task files** for pipeline definition
- **Working code only** - no stubs or placeholders

## Example Task File

```json
{
  "name": "My Pipeline",
  "tasks": [
    {
      "id": "task1",
      "prompt": "Your prompt with {context_variable}",
      "context_keys": ["context_variable"],
      "save_key": "result1",
      "required": true,
      "timeout": 120
    }
  ],
  "initial_data": {
    "context_variable": "value"
  }
}
```

## Philosophy

This implementation follows:
- **Ruthless simplicity** - minimal abstractions
- **Modular design** - clear boundaries
- **Recovery first** - designed for interruption
- **Working code** - everything actually executes

## Next Steps

This Phase 1 foundation can be extended with:
- Multiple pipeline stages
- Parallel task execution
- More sophisticated agents
- Pattern library
- Metacognitive analysis

But first, we have a working system that demonstrates the core concepts!