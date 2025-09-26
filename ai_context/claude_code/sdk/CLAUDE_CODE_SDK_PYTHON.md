# Python

> Build custom AI agents with the Claude Code Python SDK

## Prerequisites

- Python 3.10+
- `claude-code-sdk` from PyPI
- Node.js 18+
- `@anthropic-ai/claude-code` from NPM

<Note>
  To view the Python SDK source code, see the [`claude-code-sdk`](https://github.com/anthropics/claude-code-sdk-python) repo.
</Note>

<Tip>
  For interactive development, use [IPython](https://ipython.org/): `pip install ipython`
</Tip>

## Installation

Install `claude-code-sdk` from PyPI and `@anthropic-ai/claude-code` from NPM:

```bash
pip install claude-code-sdk
npm install -g @anthropic-ai/claude-code  # Required dependency
```

(Optional) Install IPython for interactive development:

```bash
pip install ipython
```

## Quick start

Create your first agent:

```python
# legal-agent.py
import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

async def main():
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="You are a legal assistant. Identify risks and suggest improvements.",
            max_turns=2
        )
    ) as client:
        # Send the query
        await client.query(
            "Review this contract clause for potential issues: 'The party agrees to unlimited liability...'"
        )

        # Stream the response
        async for message in client.receive_response():
            if hasattr(message, 'content'):
                # Print streaming content as it arrives
                for block in message.content:
                    if hasattr(block, 'text'):
                        print(block.text, end='', flush=True)

if __name__ == "__main__":
    asyncio.run(main())
```

Save the code above as `legal-agent.py`, then run:

```bash
python legal-agent.py
```

For [IPython](https://ipython.org/)/Jupyter notebooks, you can run the code directly in a cell:

```python
await main()
```

<Note>
  The Python examples on this page use `asyncio`, but you can also use `anyio`.
</Note>

## Basic usage

The Python SDK provides two primary interfaces:

### 1. The `ClaudeSDKClient` class (recommended)

Best for streaming responses, multi-turn conversations, and interactive applications:

```python
import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

async def main():
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="You are a performance engineer",
            allowed_tools=["Bash", "Read", "WebSearch"],
            max_turns=5
        )
    ) as client:
        await client.query("Analyze system performance")

        # Stream responses
        async for message in client.receive_response():
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'text'):
                        print(block.text, end='', flush=True)

# Run as script
asyncio.run(main())

# Or in IPython/Jupyter: await main()
```

### 2. The `query` function

For simple, one-shot queries:

```python
from claude_code_sdk import query, ClaudeCodeOptions

async for message in query(
    prompt="Analyze system performance",
    options=ClaudeCodeOptions(system_prompt="You are a performance engineer")
):
    if type(message).__name__ == "ResultMessage":
        print(message.result)
```

## Configuration options

The Python SDK accepts all arguments supported by the [command line](/en/docs/claude-code/cli-reference) through the `ClaudeCodeOptions` class.

### ClaudeCodeOptions parameters

```python
from claude_code_sdk import ClaudeCodeOptions

options = ClaudeCodeOptions(
    # Core configuration
    system_prompt="You are a helpful assistant",
    append_system_prompt="Additional system instructions",
    max_turns=5,
    model="claude-3-5-sonnet-20241022",
    max_thinking_tokens=8000,

    # Tool management
    allowed_tools=["Bash", "Read", "Write"],
    disallowed_tools=["WebSearch"],

    # Session management
    continue_conversation=False,
    resume="session-uuid",

    # Environment
    cwd="/path/to/working/directory",
    add_dirs=["/additional/context/dir"],
    settings="/path/to/settings.json",

    # Permissions
    permission_mode="acceptEdits",  # "default", "acceptEdits", "plan", "bypassPermissions"
    permission_prompt_tool_name="mcp__approval_tool",

    # MCP integration
    mcp_servers={
        "my_server": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-example"],
            "env": {"API_KEY": "your-key"}
        }
    },

    # Advanced
    extra_args={"--verbose": None, "--custom-flag": "value"}
)
```

#### Parameter details

- **`system_prompt`**: `str | None` - Custom system prompt defining the agent's role
- **`append_system_prompt`**: `str | None` - Additional text appended to system prompt
- **`max_turns`**: `int | None` - Maximum conversation turns (unlimited if None)
- **`model`**: `str | None` - Specific Claude model to use
- **`max_thinking_tokens`**: `int` - Maximum tokens for Claude's thinking process (default: 8000)
- **`allowed_tools`**: `list[str]` - Tools specifically allowed for use
- **`disallowed_tools`**: `list[str]` - Tools that should not be used
- **`continue_conversation`**: `bool` - Continue most recent conversation (default: False)
- **`resume`**: `str | None` - Session UUID to resume specific conversation
- **`cwd`**: `str | Path | None` - Working directory for the session
- **`add_dirs`**: `list[str | Path]` - Additional directories to include in context
- **`settings`**: `str | None` - Path to settings file or settings JSON string
- **`permission_mode`**: `str | None` - Permission handling mode
- **`permission_prompt_tool_name`**: `str | None` - Custom permission prompt tool name
- **`mcp_servers`**: `dict | str | Path` - MCP server configurations
- **`extra_args`**: `dict[str, str | None]` - Pass arbitrary CLI flags to underlying Claude Code CLI

#### Permission modes

- **`"default"`**: CLI prompts for dangerous tools (default behavior)
- **`"acceptEdits"`**: Automatically accept file edits without prompting
- **`"plan"`**: Plan Mode - analyze without making changes
- **`"bypassPermissions"`**: Allow all tools without prompting (use with caution)

### Advanced configuration example

```python
import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

async def advanced_agent():
    """Example showcasing advanced configuration options"""

    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            # Custom working directory and additional context
            cwd="/project/root",
            add_dirs=["/shared/libs", "/common/utils"],

            # Model and thinking configuration
            model="claude-3-5-sonnet-20241022",
            max_thinking_tokens=12000,

            # Advanced tool control
            allowed_tools=["Read", "Write", "Bash", "Grep"],
            disallowed_tools=["WebSearch", "Bash(rm*)"],

            # Custom settings and CLI args
            settings='{"editor": "vim", "theme": "dark"}',
            extra_args={
                "--verbose": None,
                "--timeout": "300"
            }
        )
    ) as client:
        await client.query("Analyze the codebase structure")

        async for message in client.receive_response():
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'text'):
                        print(block.text, end='', flush=True)

asyncio.run(advanced_agent())
```

## Structured messages and image inputs

The SDK supports passing structured messages and image inputs:

```python
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

async with ClaudeSDKClient() as client:
    # Text message
    await client.query("Analyze this code for security issues")

    # Message with image reference (image will be read by Claude's Read tool)
    await client.query("Explain what's shown in screenshot.png")

    # Multiple messages in sequence
    messages = [
        "First, analyze the architecture diagram in diagram.png",
        "Now suggest improvements based on the diagram",
        "Finally, generate implementation code"
    ]

    for msg in messages:
        await client.query(msg)
        async for response in client.receive_response():
            # Process each response
            pass

# The SDK handles image files through Claude's built-in Read tool
# Supported formats: PNG, JPG, PDF, and other common formats
```

## Multi-turn conversations

### Method 1: Using ClaudeSDKClient for persistent conversations

```python
import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, query

# Method 1: Using ClaudeSDKClient for persistent conversations
async def multi_turn_conversation():
    async with ClaudeSDKClient() as client:
        # First query
        await client.query("Let's refactor the payment module")
        async for msg in client.receive_response():
            # Process first response
            pass

        # Continue in same session
        await client.query("Now add comprehensive error handling")
        async for msg in client.receive_response():
            # Process continuation
            pass

        # The conversation context is maintained throughout

# Method 2: Using query function with session management
async def resume_session():
    # Continue most recent conversation
    async for message in query(
        prompt="Now refactor this for better performance",
        options=ClaudeCodeOptions(continue_conversation=True)
    ):
        if type(message).__name__ == "ResultMessage":
            print(message.result)

    # Resume specific session
    async for message in query(
        prompt="Update the tests",
        options=ClaudeCodeOptions(
            resume="550e8400-e29b-41d4-a716-446655440000",
            max_turns=3
        )
    ):
        if type(message).__name__ == "ResultMessage":
            print(message.result)

# Run the examples
asyncio.run(multi_turn_conversation())
```

## Custom system prompts

System prompts define your agent's role, expertise, and behavior:

```python
import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

async def specialized_agents():
    # SRE incident response agent with streaming
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="You are an SRE expert. Diagnose issues systematically and provide actionable solutions.",
            max_turns=3
        )
    ) as sre_agent:
        await sre_agent.query("API is down, investigate")

        # Stream the diagnostic process
        async for message in sre_agent.receive_response():
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'text'):
                        print(block.text, end='', flush=True)

    # Legal review agent with custom prompt
    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            append_system_prompt="Always include comprehensive error handling and unit tests.",
            max_turns=2
        )
    ) as dev_agent:
        await dev_agent.query("Refactor this function")

        # Collect full response
        full_response = []
        async for message in dev_agent.receive_response():
            if type(message).__name__ == "ResultMessage":
                print(message.result)

asyncio.run(specialized_agents())
```

## Custom tools via MCP

The Model Context Protocol (MCP) lets you give your agents custom tools and capabilities:

```python
import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

async def mcp_enabled_agent():
    # Legal agent with document access and streaming
    # Note: Configure your MCP servers as needed
    mcp_servers = {
        # Example configuration - uncomment and configure as needed:
        # "docusign": {
        #     "command": "npx",
        #     "args": ["-y", "@modelcontextprotocol/server-docusign"],
        #     "env": {"API_KEY": "your-key"}
        # }
    }

    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            mcp_servers=mcp_servers,
            allowed_tools=["mcp__docusign", "mcp__compliance_db"],
            system_prompt="You are a corporate lawyer specializing in contract review.",
            max_turns=4
        )
    ) as client:
        await client.query("Review this contract for compliance risks")

        # Monitor tool usage and responses
        async for message in client.receive_response():
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'type'):
                        if block.type == 'tool_use':
                            print(f"\n[Using tool: {block.name}]\n")
                        elif hasattr(block, 'text'):
                            print(block.text, end='', flush=True)
                    elif hasattr(block, 'text'):
                        print(block.text, end='', flush=True)

            if type(message).__name__ == "ResultMessage":
                print(f"\n\nReview complete. Total cost: ${message.total_cost_usd:.4f}")

asyncio.run(mcp_enabled_agent())
```

## Custom permission prompt tool

Implement custom permission handling for tool calls:

```python
import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

async def use_permission_prompt():
    """Example using custom permission prompt tool"""

    # MCP server configuration
    mcp_servers = {
        # Example configuration - uncomment and configure as needed:
        # "security": {
        #     "command": "npx",
        #     "args": ["-y", "@modelcontextprotocol/server-security"],
        #     "env": {"API_KEY": "your-key"}
        # }
    }

    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            permission_prompt_tool_name="mcp__security__approval_prompt",  # Changed from permission_prompt_tool
            mcp_servers=mcp_servers,
            allowed_tools=["Read", "Grep"],
            disallowed_tools=["Bash(rm*)", "Write"],
            system_prompt="You are a security auditor"
        )
    ) as client:
        await client.query("Analyze and fix the security issues")

        # Monitor tool usage and permissions
        async for message in client.receive_response():
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'type'):  # Added check for 'type' attribute
                        if block.type == 'tool_use':
                            print(f"[Tool: {block.name}] ", end='')
                    if hasattr(block, 'text'):
                        print(block.text, end='', flush=True)

            # Check for permission denials in error messages
            if type(message).__name__ == "ErrorMessage":
                if hasattr(message, 'error') and "Permission denied" in str(message.error):
                    print(f"\n⚠️ Permission denied: {message.error}")

# Example MCP server implementation (Python)
# This would be in your MCP server code
async def approval_prompt(tool_name: str, input: dict, tool_use_id: str = None):
    """Custom permission prompt handler"""
    # Your custom logic here
    if "allow" in str(input):
        return json.dumps({
            "behavior": "allow",
            "updatedInput": input
        })
    else:
        return json.dumps({
            "behavior": "deny",
            "message": f"Permission denied for {tool_name}"
        })

asyncio.run(use_permission_prompt())
```

## Output formats

### Text output with streaming

```python
# Default text output with streaming
async with ClaudeSDKClient() as client:
    await client.query("Explain file src/components/Header.tsx")

    # Stream text as it arrives
    async for message in client.receive_response():
        if hasattr(message, 'content'):
            for block in message.content:
                if hasattr(block, 'text'):
                    print(block.text, end='', flush=True)
                    # Output streams in real-time: This is a React component showing...
```

### JSON output with metadata

```python
# Collect all messages with metadata
async with ClaudeSDKClient() as client:
    await client.query("How does the data layer work?")

    messages = []
    result_data = None

    async for message in client.receive_messages():
        messages.append(message)

        # Capture result message with metadata
        if type(message).__name__ == "ResultMessage":
            result_data = {
                "result": message.result,
                "cost": message.total_cost_usd,
                "duration": message.duration_ms,
                "num_turns": message.num_turns,
                "session_id": message.session_id
            }
            break

    print(result_data)
```

## Input formats

```python
import asyncio
from claude_code_sdk import ClaudeSDKClient

async def process_inputs():
    async with ClaudeSDKClient() as client:
        # Text input
        await client.query("Explain this code")
        async for message in client.receive_response():
            # Process streaming response
            pass

        # Image input (Claude will use Read tool automatically)
        await client.query("What's in this diagram? screenshot.png")
        async for message in client.receive_response():
            # Process image analysis
            pass

        # Multiple inputs with mixed content
        inputs = [
            "Analyze the architecture in diagram.png",
            "Compare it with best practices",
            "Generate improved version"
        ]

        for prompt in inputs:
            await client.query(prompt)
            async for message in client.receive_response():
                # Process each response
                pass

asyncio.run(process_inputs())
```

## Agent integration examples

### SRE incident response agent

```python
import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

async def investigate_incident(incident_description: str, severity: str = "medium"):
    """Automated incident response agent with real-time streaming"""

    # MCP server configuration for monitoring tools
    mcp_servers = {
        # Example configuration - uncomment and configure as needed:
        # "datadog": {
        #     "command": "npx",
        #     "args": ["-y", "@modelcontextprotocol/server-datadog"],
        #     "env": {"API_KEY": "your-datadog-key", "APP_KEY": "your-app-key"}
        # }
    }

    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="You are an SRE expert. Diagnose issues systematically and provide actionable solutions.",
            max_turns=6,
            allowed_tools=["Bash", "Read", "WebSearch", "mcp__datadog"],
            mcp_servers=mcp_servers
        )
    ) as client:
        # Send the incident details
        prompt = f"Incident: {incident_description} (Severity: {severity})"
        print(f"🚨 Investigating: {prompt}\n")
        await client.query(prompt)

        # Stream the investigation process
        investigation_log = []
        async for message in client.receive_response():
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'type'):
                        if block.type == 'tool_use':
                            print(f"[{block.name}] ", end='')
                    if hasattr(block, 'text'):
                        text = block.text
                        print(text, end='', flush=True)
                        investigation_log.append(text)

            # Capture final result
            if type(message).__name__ == "ResultMessage":
                return {
                    'analysis': ''.join(investigation_log),
                    'cost': message.total_cost_usd,
                    'duration_ms': message.duration_ms
                }

# Usage
result = await investigate_incident("Payment API returning 500 errors", "high")
print(f"\n\nInvestigation complete. Cost: ${result['cost']:.4f}")
```

### Automated security review

```python
import subprocess
import asyncio
import json
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

async def audit_pr(pr_number: int):
    """Security audit agent for pull requests with streaming feedback"""
    # Get PR diff
    pr_diff = subprocess.check_output(
        ["gh", "pr", "diff", str(pr_number)],
        text=True
    )

    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="You are a security engineer. Review this PR for vulnerabilities, insecure patterns, and compliance issues.",
            max_turns=3,
            allowed_tools=["Read", "Grep", "WebSearch"]
        )
    ) as client:
        print(f"🔍 Auditing PR #{pr_number}\n")
        await client.query(pr_diff)

        findings = []
        async for message in client.receive_response():
            if hasattr(message, 'content'):
                for block in message.content:
                    if hasattr(block, 'text'):
                        # Stream findings as they're discovered
                        print(block.text, end='', flush=True)
                        findings.append(block.text)

            if type(message).__name__ == "ResultMessage":
                return {
                    'pr_number': pr_number,
                    'findings': ''.join(findings),
                    'metadata': {
                        'cost': message.total_cost_usd,
                        'duration': message.duration_ms,
                        'severity': 'high' if 'vulnerability' in ''.join(findings).lower() else 'medium'
                    }
                }

# Usage
report = await audit_pr(123)
print(f"\n\nAudit complete. Severity: {report['metadata']['severity']}")
print(json.dumps(report, indent=2))
```

### Multi-turn legal assistant

```python
import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

async def legal_review():
    """Legal document review with persistent session and streaming"""

    async with ClaudeSDKClient(
        options=ClaudeCodeOptions(
            system_prompt="You are a corporate lawyer. Provide detailed legal analysis.",
            max_turns=2
        )
    ) as client:
        # Multi-step review in same session
        steps = [
            "Review contract.pdf for liability clauses",
            "Check compliance with GDPR requirements",
            "Generate executive summary of risks"
        ]

        review_results = []

        for step in steps:
            print(f"\n📋 {step}\n")
            await client.query(step)

            step_result = []
            async for message in client.receive_response():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            text = block.text
                            print(text, end='', flush=True)
                            step_result.append(text)

                if type(message).__name__ == "ResultMessage":
                    review_results.append({
                        'step': step,
                        'analysis': ''.join(step_result),
                        'cost': message.total_cost_usd
                    })

        # Summary
        total_cost = sum(r['cost'] for r in review_results)
        print(f"\n\n✅ Legal review complete. Total cost: ${total_cost:.4f}")
        return review_results

# Usage
results = await legal_review()
```

## Python-specific best practices

### Key patterns

```python
import asyncio
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

# Always use context managers
async with ClaudeSDKClient() as client:
    await client.query("Analyze this code")
    async for msg in client.receive_response():
        # Process streaming messages
        pass

# Run multiple agents concurrently
async with ClaudeSDKClient() as reviewer, ClaudeSDKClient() as tester:
    await asyncio.gather(
        reviewer.query("Review main.py"),
        tester.query("Write tests for main.py")
    )

# Error handling
from claude_code_sdk import CLINotFoundError, ProcessError

try:
    async with ClaudeSDKClient() as client:
        # Your code here
        pass
except CLINotFoundError:
    print("Install CLI: npm install -g @anthropic-ai/claude-code")
except ProcessError as e:
    print(f"Process error: {e}")

# Collect full response with metadata
async def get_response(client, prompt):
    await client.query(prompt)
    text = []
    async for msg in client.receive_response():
        if hasattr(msg, 'content'):
            for block in msg.content:
                if hasattr(block, 'text'):
                    text.append(block.text)
        if type(msg).__name__ == "ResultMessage":
            return {'text': ''.join(text), 'cost': msg.total_cost_usd}
```

### IPython/Jupyter tips

```python
# In Jupyter, use await directly in cells
client = ClaudeSDKClient()
await client.connect()
await client.query("Analyze data.csv")
async for msg in client.receive_response():
    print(msg)
await client.disconnect()

# Create reusable helper functions
async def stream_print(client, prompt):
    await client.query(prompt)
    async for msg in client.receive_response():
        if hasattr(msg, 'content'):
            for block in msg.content:
                if hasattr(block, 'text'):
                    print(block.text, end='', flush=True)
```

## Related resources

- [CLI usage and controls](/en/docs/claude-code/cli-reference) - Complete CLI documentation
- [GitHub Actions integration](/en/docs/claude-code/github-actions) - Automate your GitHub workflow with Claude
- [Common workflows](/en/docs/claude-code/common-workflows) - Step-by-step guides for common use cases
