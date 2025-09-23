# Claude Code SDK Toolkit

A comprehensive Python toolkit for building CLI tools and applications with the Claude Code SDK. Simplifies creating "mini-instances" of Claude Code for focused microtasks.

## Quick Start: Building a New Tool

**Start with the quickstart template:**

```bash
# Copy template to create your tool
cp amplifier/ccsdk_toolkit/templates/tool_template.py ai_working/your_tool.py

# Template includes ALL defensive patterns:
# ✓ Recursive file discovery (**/*.ext)
# ✓ Input validation and error handling
# ✓ Progress visibility and logging
# ✓ Resume capability
# ✓ Defensive LLM parsing
# ✓ Cloud sync aware I/O

Remove or modify sections as needed.

```

The template includes patterns proven through learnings from real failures. See `templates/README.md` for details.

## Features

- **🚀 Simple Async Wrapper** - Clean async/await patterns with automatic retry logic
- **⚙️ Configuration Management** - Type-safe configuration with Pydantic models
- **💾 Session Persistence** - Save and resume conversations across sessions
- **📊 Structured Logging** - JSON, plaintext, or rich console output with full tracking
- **🛠️ CLI Builder** - Generate new CLI tools from templates in seconds
- **🔄 Re-entrant Sessions** - Continue previous conversations seamlessly
- **🌊 Natural Completion** - Operations run to completion without artificial time limits
- **🎯 Agent Support** - Load and use specialized agents from files or inline

## Installation

```bash
# Install Python package
pip install claude-code-sdk

# Install Claude CLI (required)
npm install -g @anthropic-ai/claude-code

# Or if using the amplifier project
uv add claude-code-sdk
```

## Quick Start

**New Tool?** Start with the production-ready template: `amplifier/ccsdk_toolkit/templates/tool_template.py` ([see guide](templates/README.md))

### Basic Usage

```python
import asyncio
from amplifier.ccsdk_toolkit import ClaudeSession, SessionOptions

async def main():
    # Create session with options
    options = SessionOptions(
        system_prompt="You are a helpful code assistant",
        max_turns=1,
        # Operations run to natural completion
    )

    async with ClaudeSession(options) as session:
        response = await session.query("Write a Python hello world")

        if response.success:
            print(response.content)
        else:
            print(f"Error: {response.error}")

asyncio.run(main())
```

### With Retry Logic

```python
from amplifier.ccsdk_toolkit import query_with_retry

response = await query_with_retry(
    prompt="Analyze this code",
    max_retries=3,
)
```

## Core Modules

### 1. Core (`ccsdk_toolkit.core`)

The foundation module providing Claude Code SDK integration:

```python
from amplifier.ccsdk_toolkit import (
    ClaudeSession,      # Main session class
    SessionOptions,     # Configuration options
    check_claude_cli,   # Verify CLI installation
    query_with_retry,   # Retry logic wrapper
)

# Check CLI availability
if check_claude_cli():
    print("Claude CLI is available")
```

### 2. Configuration (`ccsdk_toolkit.config`)

Type-safe configuration management:

```python
from amplifier.ccsdk_toolkit import (
    ToolkitConfig,
    AgentDefinition,
    ToolPermissions,
)

# Define agent configuration
agent = AgentDefinition(
    name="code-reviewer",
    system_prompt="You are an expert code reviewer",
    tool_permissions=ToolPermissions(
        allowed=["Read", "Grep", "Glob"],
        disallowed=["Write", "Execute"]
    )
)

# Save/load configurations
config = ToolkitConfig(agents=[agent])
config.save("config.yaml")
loaded = ToolkitConfig.load("config.yaml")
```

### 3. Session Management (`ccsdk_toolkit.sessions`)

Persist and resume conversations:

```python
from amplifier.ccsdk_toolkit import SessionManager

# Create manager
manager = SessionManager()

# Create new session
session = manager.create_session(
    name="code-analysis",
    tags=["analysis", "python"]
)

# Add messages
session.add_message("user", "Analyze this function")
session.add_message("assistant", "Here's my analysis...")

# Save session
manager.save_session(session)

# Resume later
resumed = manager.load_session(session.metadata.session_id)
```

### 4. Logging (`ccsdk_toolkit.logger`)

Comprehensive structured logging:

```python
from amplifier.ccsdk_toolkit import (
    ToolkitLogger,
    LogLevel,
    LogFormat,
    create_logger,
)

# Create logger with different formats
logger = create_logger(
    name="my_tool",
    level=LogLevel.DEBUG,
    format=LogFormat.JSON,  # or PLAIN, RICH
    output_file=Path("tool.log")
)

# Log at different levels
logger.info("Starting process", task="analysis")
logger.error("Failed", error=Exception("operation failed"))

# Track queries
logger.log_query(prompt="Analyze code", response="...")

# Track sessions
logger.log_session_start(session_id, config)
logger.log_session_end(session_id, duration_ms, cost)
```

### 5. CLI Builder (`ccsdk_toolkit.cli`)

Generate new CLI tools from templates:

```python
from amplifier.ccsdk_toolkit import CliBuilder, CliTemplate

# Create builder
builder = CliBuilder(tools_dir=Path("./tools"))

# Create from template
tool_dir = builder.create_tool(
    name="code_analyzer",
    description="Analyze code complexity",
    template=CliTemplate.ANALYZER,
    system_prompt="You are a code complexity expert"
)

# List available templates
templates = builder.list_templates()
# ['basic', 'analyzer', 'generator', 'orchestrator']
```

## Example CLI Tools

### Idea Synthesis Tool

A multi-stage pipeline tool that demonstrates the "code for structure, AI for intelligence" pattern:

```bash
# Synthesize ideas from markdown documentation
python -m amplifier.ccsdk_toolkit.examples.idea_synthesis ai_context/

# Process with limits and custom output
python -m amplifier.ccsdk_toolkit.examples.idea_synthesis docs/ --limit 5 --output results/

# Resume interrupted synthesis
python -m amplifier.ccsdk_toolkit.examples.idea_synthesis docs/ --resume session-id

# Export as JSON for programmatic use
python -m amplifier.ccsdk_toolkit.examples.idea_synthesis docs/ --json-output
```

**Features:**

- 4-stage pipeline: Read → Summarize → Synthesize → Expand
- Incremental saves after each item processed
- Full resume capability at any stage
- Markdown and JSON output formats
- Demonstrates hybrid code/AI architecture

### Code Complexity Analyzer

A complete example tool included with the toolkit:

```bash
# First ensure Claude CLI is installed
which claude  # Should return a path

# Run from project root directory
cd /path/to/amplifier-ccsdk-sdk

# Analyze a single file
python amplifier/ccsdk_toolkit/examples/code_complexity_analyzer.py main.py

# Analyze directory recursively
python amplifier/ccsdk_toolkit/examples/code_complexity_analyzer.py src/ --recursive --pattern "*.py"

# Output as JSON
python amplifier/ccsdk_toolkit/examples/code_complexity_analyzer.py src/ --json --output results.json

# Resume previous session
python amplifier/ccsdk_toolkit/examples/code_complexity_analyzer.py src/ --resume session-id

# Example analyzing the toolkit itself
python amplifier/ccsdk_toolkit/examples/code_complexity_analyzer.py amplifier/ccsdk_toolkit/core/__init__.py

# Process large codebases in manageable chunks
python amplifier/ccsdk_toolkit/examples/code_complexity_analyzer.py src/ --recursive --pattern "*.py" --limit 5

# Process next batch of files using resume
python amplifier/ccsdk_toolkit/examples/code_complexity_analyzer.py src/ --recursive --pattern "*.py" --limit 5 --resume session-id
```

**Note:** The CLI tool can be run directly thanks to automatic sys.path adjustment when run as a script. If importing it as a module, ensure the project root is in your Python path.

**Batch Processing with --limit:** The `--limit` flag allows processing large codebases in manageable chunks. When combined with `--resume`, it intelligently processes the NEXT N files, skipping any that were already analyzed. This is perfect for:

- Testing on a small sample before processing everything
- Breaking up large analysis jobs into smaller sessions
- Managing API rate limits or timeouts
- Incrementally processing new files added to a codebase

### Creating Your Own Tool

```python
#!/usr/bin/env python3
"""My custom CCSDK tool"""

import asyncio
import click
from amplifier.ccsdk_toolkit import (
    ClaudeSession,
    SessionOptions,
    ToolkitLogger,
    LogLevel,
)

@click.command()
@click.argument("input_text")
@click.option("--verbose", is_flag=True)
def main(input_text: str, verbose: bool):
    """Process input with Claude"""
    asyncio.run(process(input_text, verbose))

async def process(input_text: str, verbose: bool):
    # Set up logging
    logger = ToolkitLogger(
        name="my_tool",
        level=LogLevel.DEBUG if verbose else LogLevel.INFO
    )

    # Configure session
    options = SessionOptions(
        system_prompt="You are a helpful assistant",
        max_turns=1
    )

    async with ClaudeSession(options) as session:
        response = await session.query(input_text)
        if response.success:
            print(response.content)

if __name__ == "__main__":
    main()
```

## Advanced Usage

### Loading Agents from Files

Create an agent definition file (`agent.yaml`):

```yaml
name: code-reviewer
description: Expert code review agent
system_prompt: |
  You are an expert code reviewer focused on:
  - Security vulnerabilities
  - Performance issues
  - Best practices
tool_permissions:
  allowed:
    - Read
    - Grep
    - Glob
  disallowed:
    - Write
    - Execute
```

Load and use:

```python
from amplifier.ccsdk_toolkit import AgentDefinition, ClaudeSession

agent = AgentDefinition.from_file("agent.yaml")

options = SessionOptions(
    system_prompt=agent.system_prompt,
    # Use other agent settings
)

async with ClaudeSession(options) as session:
    response = await session.query("Review main.py")
```

### Parallel Processing

Process multiple items concurrently:

```python
import asyncio

async def process_file(file_path: Path):
    async with ClaudeSession(options) as session:
        return await session.query(f"Analyze {file_path}")

# Process files in parallel
files = Path("src").glob("*.py")
results = await asyncio.gather(
    *[process_file(f) for f in files]
)
```

### Custom MCP Servers

Integrate with Model Context Protocol servers:

```python
from amplifier.ccsdk_toolkit import MCPServerConfig

mcp_config = MCPServerConfig(
    name="custom-tools",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-example"],
    env={"API_KEY": "your-key"}
)

config = ToolkitConfig(mcp_servers=[mcp_config])
```

## Architecture

The toolkit follows a modular "bricks and studs" design:

```
amplifier/ccsdk_toolkit/
├── core/           # Core SDK wrapper (the foundation brick)
├── config/         # Configuration management (settings brick)
├── sessions/       # Session persistence (state brick)
├── logger/         # Structured logging (monitoring brick)
├── cli/            # CLI tool builder (generation brick)
└── examples/       # Example CLI tools (implementation examples)
```

Each module is:

- **Self-contained** - Can be used independently
- **Well-defined interfaces** - Clear contracts between modules
- **Regeneratable** - Can be rebuilt without affecting others
- **Following ruthless simplicity** - Minimal abstractions

## Configuration

### Environment Variables

```bash
# Set API key
export ANTHROPIC_API_KEY="your-key"

# Use alternative providers
export CLAUDE_CODE_USE_BEDROCK=1  # Amazon Bedrock
export CLAUDE_CODE_USE_VERTEX=1   # Google Vertex AI
```

### Toolkit Configuration

```python
from amplifier.ccsdk_toolkit import EnvironmentConfig

env_config = EnvironmentConfig(
    working_directory=Path("/project"),
    session_directory=Path("~/.ccsdk/sessions"),
    log_directory=Path("~/.ccsdk/logs"),
    debug=True
)
```

## Error Handling

The toolkit provides clear error messages and recovery:

```python
from amplifier.ccsdk_toolkit import SDKNotAvailableError

try:
    async with ClaudeSession(options) as session:
        response = await session.query("...")
except SDKNotAvailableError as e:
    print(f"SDK not available: {e}")
    print("Install with: npm install -g @anthropic-ai/claude-code")
except Exception as e:
    logger.error("Unexpected error", error=e)
```

## Known Issues & Solutions

### Long-Running Operations

The toolkit trusts operations to complete naturally. Use streaming for visibility:

```python
# Enable streaming to see progress
options = SessionOptions(stream_output=True)
```

### Claude CLI Not Found

The SDK requires the Claude CLI to be installed globally:

```bash
# Check if installed
which claude

# Install if missing
npm install -g @anthropic-ai/claude-code

# Or with bun
bun install -g @anthropic-ai/claude-code
```

### Session Not Found

When resuming sessions, ensure the session ID exists:

```python
session = manager.load_session(session_id)
if not session:
    print(f"Session {session_id} not found")
    # Create new session instead
```

## Philosophy

This toolkit embodies:

- **Ruthless Simplicity** - Every abstraction must justify its existence
- **Modular Design** - Self-contained bricks with clear interfaces
- **Pragmatic Defaults** - Sensible defaults that work for most cases
- **Progressive Enhancement** - Start simple, add complexity only when needed
- **Clear Error Messages** - When things fail, tell users exactly what to do

See [IMPLEMENTATION_PHILOSOPHY.md](../../ai_context/IMPLEMENTATION_PHILOSOPHY.md) for detailed principles.

## Contributing

Contributions are welcome! Please follow the modular design philosophy and ensure all code passes:

```bash
make check  # Format, lint, and type-check
make test   # Run tests
```

## License

[Project License]

## Support

For issues or questions:

- GitHub Issues: [Project Issues]
- Documentation: See `/ai_context/claude_code/` for SDK details

---

Built with the Claude Code SDK and a commitment to ruthless simplicity.
