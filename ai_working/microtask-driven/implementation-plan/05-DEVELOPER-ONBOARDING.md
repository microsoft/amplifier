# Developer Onboarding Guide

## Welcome to the Amplifier CLI Tool Builder Project!

This guide will get you up and running with the development environment and provide you with everything you need to start building.

## Prerequisites

### Required Software

- **Python 3.10+**
  ```bash
  python --version  # Should show 3.10 or higher
  ```

- **Node.js 18+**
  ```bash
  node --version  # Should show v18 or higher
  ```

- **Git**
  ```bash
  git --version
  ```

- **UV (Python package manager)**
  ```bash
  # Install if not present
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### API Requirements

- **Anthropic API Key**: Get from [Anthropic Console](https://console.anthropic.com/)
  ```bash
  export ANTHROPIC_API_KEY="your-api-key-here"
  ```

## Quick Start (5 Minutes)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd amplifier-tool-builder

# Install dependencies
uv sync
npm install -g @anthropic-ai/claude-code

# Verify Claude CLI installation
which claude  # Should show path to claude binary
```

### 2. Run First Test

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run test microtask
python -m amplifier_tool_builder.test_setup

# Expected output:
# ✅ Claude Code SDK: Working
# ✅ Microtask execution: Success (took 4.2 seconds)
# ✅ Setup complete! You're ready to build.
```

### 3. Try the CLI

```bash
# See available commands
amplifier-tool-builder --help

# Create your first tool (dry run)
amplifier-tool-builder create "test-tool" \
  --description "A simple test tool" \
  --dry-run
```

## Understanding the Project

### Core Concepts

#### 1. **Microtask Architecture**
Every AI operation is broken into 5-10 second focused tasks:
```python
# Instead of: "Build me a complete tool"
# We do:
# - "Identify the core problem" (5 seconds)
# - "Design the architecture" (8 seconds)
# - "Generate module X" (6 seconds)
# - "Verify quality" (5 seconds)
```

#### 2. **Code for Structure, AI for Intelligence**
- **Code handles**: Flow control, state, I/O, errors
- **AI handles**: Analysis, generation, decisions, creativity

#### 3. **Incremental Persistence**
Save after EVERY operation - never lose work:
```python
result = process(item)
save(result)  # Immediately!
```

#### 4. **Progressive Specialization**
```
Level 0: Simple code solutions (instant)
Level 1: General AI (broad capability)
Level 2: Specialized AI (domain expert)
Level 3: Metacognitive (self-improving)
```

### Project Structure

```
amplifier-tool-builder/
├── amplifier_tool_builder/        # Main package
│   ├── cli.py                    # CLI entry point
│   ├── orchestrator.py           # Main workflow orchestration
│   ├── session.py                # Session management & recovery
│   ├── agents/                   # Microtask agents
│   │   ├── base.py              # Base agent class
│   │   ├── requirements.py      # Requirements analysis
│   │   ├── architecture.py      # Architecture design
│   │   ├── generation.py        # Code generation
│   │   └── verification.py      # Quality verification
│   ├── stages/                   # Pipeline stages
│   │   ├── requirements.py      # Stage 1
│   │   ├── architecture.py      # Stage 2
│   │   ├── generation.py        # Stage 3
│   │   └── verification.py      # Stage 4
│   ├── patterns/                 # Reusable patterns
│   │   └── library.py           # Pattern templates
│   └── metacognitive/            # Self-improvement
│       └── analyzer.py          # Failure analysis
├── tests/                        # Test suite
├── docs/                         # Documentation
└── Makefile                      # Common commands
```

## Development Workflow

### 1. Understanding the Task

Before coding, understand what you're building:
```bash
# Read the background
cat docs/01-BACKGROUND-CONTEXT.md

# Review the architecture
cat docs/02-TECHNICAL-ARCHITECTURE.md

# Check the patterns
cat docs/04-MICROTASK-PATTERNS.md
```

### 2. Setting Up Your Branch

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
# ... edit files ...

# Run tests frequently
make test

# Check code quality
make check
```

### 3. Testing Your Changes

```bash
# Run specific test
pytest tests/test_agents.py::test_requirements_analyzer

# Run with coverage
pytest --cov=amplifier_tool_builder

# Run integration tests
make test-integration
```

### 4. Using the Makefile

```bash
make help          # Show all commands
make test          # Run tests
make check         # Lint and format
make run           # Run the CLI
make clean         # Clean artifacts
```

## Implementing a New Agent

### Step 1: Create the Agent Class

```python
# amplifier_tool_builder/agents/your_agent.py
from .base import MicrotaskAgent

class YourAgent(MicrotaskAgent):
    """Describe what this agent does"""

    def __init__(self):
        super().__init__(task_type="your_task", timeout=10)

    def _get_system_prompt(self) -> str:
        return "You are an expert at X. You do Y."

    def _build_prompt(self, input_data: Dict) -> str:
        return f"""
        Analyze this data:
        {json.dumps(input_data, indent=2)}

        Return: specific expected output
        """

    def _parse_response(self, response: str) -> Dict:
        # Parse the response into structured data
        return {"result": response}
```

### Step 2: Add to Stage

```python
# amplifier_tool_builder/stages/your_stage.py
from ..agents.your_agent import YourAgent

class YourStage(Stage):
    def __init__(self):
        self.agent = YourAgent()

    async def execute(self, spec, context):
        result = await self.agent.execute({
            "data": spec.data
        })

        # Save immediately!
        self.save_progress(result)

        return result
```

### Step 3: Write Tests

```python
# tests/test_your_agent.py
import pytest
from amplifier_tool_builder.agents.your_agent import YourAgent

@pytest.mark.asyncio
async def test_your_agent():
    agent = YourAgent()
    result = await agent.execute({"test": "data"})

    assert result["success"]
    assert "expected_field" in result
```

## Debugging Tips

### 1. Enable Verbose Logging

```python
# In your code
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via CLI
amplifier-tool-builder create "tool" --verbose
```

### 2. Check Session State

```bash
# View session files
ls -la .amplifier/sessions/

# Inspect session state
cat .amplifier/sessions/your-session-id.json | jq .
```

### 3. Test Individual Agents

```python
# Quick test script
import asyncio
from amplifier_tool_builder.agents.requirements import ProblemIdentifier

async def test():
    agent = ProblemIdentifier()
    result = await agent.execute({
        "description": "Test tool description"
    })
    print(result)

asyncio.run(test())
```

### 4. Monitor Microtask Timing

```python
import time

start = time.time()
result = await agent.execute(data)
duration = time.time() - start

if duration > 10:
    logger.warning(f"Microtask took {duration}s - too long!")
```

## Common Issues & Solutions

### Issue: Claude Code SDK Timeout

**Symptom**: "Claude Code SDK timeout - likely running outside Claude Code environment"

**Solution**:
```bash
# Verify CLI is installed
which claude

# Test CLI directly
echo "test" | claude --output-format json

# Increase timeout if needed
# In code: timeout=120 instead of timeout=10
```

### Issue: Session Recovery Fails

**Symptom**: "Session not found" error

**Solution**:
```bash
# Check session exists
ls .amplifier/sessions/

# Create new session
amplifier-tool-builder create "tool" --new-session
```

### Issue: Microtask Takes Too Long

**Symptom**: Tasks exceed 10 second limit

**Solution**:
```python
# Break into smaller tasks
# Instead of:
await analyze_entire_codebase()

# Do:
await analyze_module(module1)
await analyze_module(module2)
# etc.
```

## Best Practices Checklist

### ✅ Every Microtask
- [ ] Has focused, single purpose
- [ ] Completes in 5-10 seconds
- [ ] Has clear system prompt
- [ ] Returns structured data
- [ ] Handles timeouts gracefully

### ✅ Every Stage
- [ ] Saves after each operation
- [ ] Can resume from any point
- [ ] Validates inputs
- [ ] Provides clear errors
- [ ] Documents its purpose

### ✅ Every Agent
- [ ] Extends MicrotaskAgent base
- [ ] Has comprehensive tests
- [ ] Documents expected I/O
- [ ] Provides fallback on failure
- [ ] Logs important operations

## Getting Help

### Documentation
- Background: `docs/01-BACKGROUND-CONTEXT.md`
- Architecture: `docs/02-TECHNICAL-ARCHITECTURE.md`
- Roadmap: `docs/03-IMPLEMENTATION-ROADMAP.md`
- Patterns: `docs/04-MICROTASK-PATTERNS.md`

### Code Examples
- Pattern library: `amplifier_tool_builder/patterns/`
- Test examples: `tests/`
- CLI usage: `amplifier_tool_builder/cli.py`

### Team Communication
- Daily standup notes: `docs/daily-updates/`
- Questions: Create issue in repo
- Discussions: Team chat channel

## Your First Contribution

### Suggested Starter Tasks

1. **Add a new pattern to the library**
   - File: `amplifier_tool_builder/patterns/library.py`
   - Add your pattern with documentation
   - Include usage example

2. **Improve error messages**
   - Find unclear error messages
   - Make them more helpful
   - Add recovery suggestions

3. **Write missing tests**
   - Check coverage: `pytest --cov`
   - Add tests for uncovered code
   - Focus on edge cases

4. **Enhance documentation**
   - Add examples
   - Clarify confusing sections
   - Fix typos

## Next Steps

1. **Today**:
   - Set up environment ✓
   - Run first test ✓
   - Read architecture doc

2. **Tomorrow**:
   - Pick a starter task
   - Create feature branch
   - Make first contribution

3. **This Week**:
   - Understand all stages
   - Run full pipeline
   - Build familiarity with patterns

## Remember

- **Save early, save often** - Never lose work
- **5-10 second rule** - Keep microtasks focused
- **Test everything** - Catch issues early
- **Ask questions** - We're here to help
- **Document learnings** - Help the next developer

Welcome to the team! Let's build something amazing together.

## Quick Reference Card

```python
# Essential Imports
from amplifier_tool_builder.agents.base import MicrotaskAgent
from amplifier_tool_builder.session import Session
from amplifier_tool_builder.orchestrator import ToolBuilderOrchestrator
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

# Create a microtask
async def run_microtask():
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="You are an expert",
            max_turns=1,
            timeout=10
        )
    ) as client:
        await client.query("Your prompt")
        # Process response

# Save immediately
def save_progress(data):
    with open("checkpoint.json", "w") as f:
        json.dump(data, f)

# Load session
session = Session.load("session-id")
# or
session = Session.new("tool-name")

# Run the tool builder
orchestrator = ToolBuilderOrchestrator(session)
tool = await orchestrator.build_tool(specification)
```

Happy coding! 🚀