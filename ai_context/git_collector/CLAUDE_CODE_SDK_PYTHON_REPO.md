# anthropics/claude-code-sdk-python/blob/main

[git-collector-data]

**URL:** https://github.com/anthropics/claude-code-sdk-python/blob/main/  
**Date:** 10/9/2025, 3:55:28 AM  
**Files:** 16  

=== File: README.md ===
# Claude Agent SDK for Python

Python SDK for Claude Agent. See the [Claude Agent SDK documentation](https://docs.anthropic.com/en/docs/claude-code/sdk/sdk-python) for more information.

## Installation

```bash
pip install claude-agent-sdk
```

**Prerequisites:**
- Python 3.10+
- Node.js
- Claude Code 2.0.0+: `npm install -g @anthropic-ai/claude-code`

## Quick Start

```python
import anyio
from claude_agent_sdk import query

async def main():
    async for message in query(prompt="What is 2 + 2?"):
        print(message)

anyio.run(main)
```

## Basic Usage: query()

`query()` is an async function for querying Claude Code. It returns an `AsyncIterator` of response messages. See [src/claude_agent_sdk/query.py](src/claude_agent_sdk/query.py).

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

# Simple query
async for message in query(prompt="Hello Claude"):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                print(block.text)

# With options
options = ClaudeAgentOptions(
    system_prompt="You are a helpful assistant",
    max_turns=1
)

async for message in query(prompt="Tell me a joke", options=options):
    print(message)
```

### Using Tools

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode='acceptEdits'  # auto-accept file edits
)

async for message in query(
    prompt="Create a hello.py file",
    options=options
):
    # Process tool use and results
    pass
```

### Working Directory

```python
from pathlib import Path

options = ClaudeAgentOptions(
    cwd="/path/to/project"  # or Path("/path/to/project")
)
```

## ClaudeSDKClient

`ClaudeSDKClient` supports bidirectional, interactive conversations with Claude
Code. See [src/claude_agent_sdk/client.py](src/claude_agent_sdk/client.py).

Unlike `query()`, `ClaudeSDKClient` additionally enables **custom tools** and **hooks**, both of which can be defined as Python functions.

### Custom Tools (as In-Process SDK MCP Servers)

A **custom tool** is a Python function that you can offer to Claude, for Claude to invoke as needed.

Custom tools are implemented in-process MCP servers that run directly within your Python application, eliminating the need for separate processes that regular MCP servers require.

For an end-to-end example, see [MCP Calculator](examples/mcp_calculator.py).

#### Creating a Simple Tool

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions, ClaudeSDKClient

# Define a tool using the @tool decorator
@tool("greet", "Greet a user", {"name": str})
async def greet_user(args):
    return {
        "content": [
            {"type": "text", "text": f"Hello, {args['name']}!"}
        ]
    }

# Create an SDK MCP server
server = create_sdk_mcp_server(
    name="my-tools",
    version="1.0.0",
    tools=[greet_user]
)

# Use it with Claude
options = ClaudeAgentOptions(
    mcp_servers={"tools": server},
    allowed_tools=["mcp__tools__greet"]
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("Greet Alice")

    # Extract and print response
    async for msg in client.receive_response():
        print(msg)
```

#### Benefits Over External MCP Servers

- **No subprocess management** - Runs in the same process as your application
- **Better performance** - No IPC overhead for tool calls
- **Simpler deployment** - Single Python process instead of multiple
- **Easier debugging** - All code runs in the same process
- **Type safety** - Direct Python function calls with type hints

#### Migration from External Servers

```python
# BEFORE: External MCP server (separate process)
options = ClaudeAgentOptions(
    mcp_servers={
        "calculator": {
            "type": "stdio",
            "command": "python",
            "args": ["-m", "calculator_server"]
        }
    }
)

# AFTER: SDK MCP server (in-process)
from my_tools import add, subtract  # Your tool functions

calculator = create_sdk_mcp_server(
    name="calculator",
    tools=[add, subtract]
)

options = ClaudeAgentOptions(
    mcp_servers={"calculator": calculator}
)
```

#### Mixed Server Support

You can use both SDK and external MCP servers together:

```python
options = ClaudeAgentOptions(
    mcp_servers={
        "internal": sdk_server,      # In-process SDK server
        "external": {                # External subprocess server
            "type": "stdio",
            "command": "external-server"
        }
    }
)
```

### Hooks

A **hook** is a Python function that the Claude Code *application* (*not* Claude) invokes at specific points of the Claude agent loop. Hooks can provide deterministic processing and automated feedback for Claude. Read more in [Claude Code Hooks Reference](https://docs.anthropic.com/en/docs/claude-code/hooks).

For more examples, see examples/hooks.py.

#### Example

```python
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher

async def check_bash_command(input_data, tool_use_id, context):
    tool_name = input_data["tool_name"]
    tool_input = input_data["tool_input"]
    if tool_name != "Bash":
        return {}
    command = tool_input.get("command", "")
    block_patterns = ["foo.sh"]
    for pattern in block_patterns:
        if pattern in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Command contains invalid pattern: {pattern}",
                }
            }
    return {}

options = ClaudeAgentOptions(
    allowed_tools=["Bash"],
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="Bash", hooks=[check_bash_command]),
        ],
    }
)

async with ClaudeSDKClient(options=options) as client:
    # Test 1: Command with forbidden pattern (will be blocked)
    await client.query("Run the bash command: ./foo.sh --help")
    async for msg in client.receive_response():
        print(msg)

    print("\n" + "=" * 50 + "\n")

    # Test 2: Safe command that should work
    await client.query("Run the bash command: echo 'Hello from hooks example!'")
    async for msg in client.receive_response():
        print(msg)
```


## Types

See [src/claude_agent_sdk/types.py](src/claude_agent_sdk/types.py) for complete type definitions:
- `ClaudeAgentOptions` - Configuration options
- `AssistantMessage`, `UserMessage`, `SystemMessage`, `ResultMessage` - Message types
- `TextBlock`, `ToolUseBlock`, `ToolResultBlock` - Content blocks

## Error Handling

```python
from claude_agent_sdk import (
    ClaudeSDKError,      # Base error
    CLINotFoundError,    # Claude Code not installed
    CLIConnectionError,  # Connection issues
    ProcessError,        # Process failed
    CLIJSONDecodeError,  # JSON parsing issues
)

try:
    async for message in query(prompt="Hello"):
        pass
except CLINotFoundError:
    print("Please install Claude Code")
except ProcessError as e:
    print(f"Process failed with exit code: {e.exit_code}")
except CLIJSONDecodeError as e:
    print(f"Failed to parse response: {e}")
```

See [src/claude_agent_sdk/_errors.py](src/claude_agent_sdk/_errors.py) for all error types.

## Available Tools

See the [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code/settings#tools-available-to-claude) for a complete list of available tools.

## Examples

See [examples/quick_start.py](examples/quick_start.py) for a complete working example.

See [examples/streaming_mode.py](examples/streaming_mode.py) for comprehensive examples involving `ClaudeSDKClient`. You can even run interactive examples in IPython from [examples/streaming_mode_ipython.py](examples/streaming_mode_ipython.py).

## Migrating from Claude Code SDK

If you're upgrading from the Claude Code SDK (versions < 0.1.0), please see the [CHANGELOG.md](CHANGELOG.md#010) for details on breaking changes and new features, including:

- `ClaudeCodeOptions` → `ClaudeAgentOptions` rename
- Merged system prompt configuration
- Settings isolation and explicit control
- New programmatic subagents and session forking features

## License

MIT


=== File: examples/quick_start.py ===
#!/usr/bin/env python3
"""Quick start example for Claude Code SDK."""

import anyio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)


async def basic_example():
    """Basic example - simple question."""
    print("=== Basic Example ===")

    async for message in query(prompt="What is 2 + 2?"):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")
    print()


async def with_options_example():
    """Example with custom options."""
    print("=== With Options Example ===")

    options = ClaudeAgentOptions(
        system_prompt="You are a helpful assistant that explains things simply.",
        max_turns=1,
    )

    async for message in query(
        prompt="Explain what Python is in one sentence.", options=options
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")
    print()


async def with_tools_example():
    """Example using tools."""
    print("=== With Tools Example ===")

    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write"],
        system_prompt="You are a helpful file assistant.",
    )

    async for message in query(
        prompt="Create a file called hello.txt with 'Hello, World!' in it",
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")
        elif isinstance(message, ResultMessage) and message.total_cost_usd > 0:
            print(f"\nCost: ${message.total_cost_usd:.4f}")
    print()


async def main():
    """Run all examples."""
    await basic_example()
    await with_options_example()
    await with_tools_example()


if __name__ == "__main__":
    anyio.run(main)


=== File: examples/streaming_mode.py ===
#!/usr/bin/env python3
"""
Comprehensive examples of using ClaudeSDKClient for streaming mode.

This file demonstrates various patterns for building applications with
the ClaudeSDKClient streaming interface.

The queries are intentionally simplistic. In reality, a query can be a more
complex task that Claude SDK uses its agentic capabilities and tools (e.g. run
bash commands, edit files, search the web, fetch web content) to accomplish.

Usage:
./examples/streaming_mode.py - List the examples
./examples/streaming_mode.py all - Run all examples
./examples/streaming_mode.py basic_streaming - Run a specific example
"""

import asyncio
import contextlib
import sys

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    CLIConnectionError,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)


def display_message(msg):
    """Standardized message display function.

    - UserMessage: "User: <content>"
    - AssistantMessage: "Claude: <content>"
    - SystemMessage: ignored
    - ResultMessage: "Result ended" + cost if available
    """
    if isinstance(msg, UserMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(f"User: {block.text}")
    elif isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(f"Claude: {block.text}")
    elif isinstance(msg, SystemMessage):
        # Ignore system messages
        pass
    elif isinstance(msg, ResultMessage):
        print("Result ended")


async def example_basic_streaming():
    """Basic streaming with context manager."""
    print("=== Basic Streaming Example ===")

    async with ClaudeSDKClient() as client:
        print("User: What is 2+2?")
        await client.query("What is 2+2?")

        # Receive complete response using the helper method
        async for msg in client.receive_response():
            display_message(msg)

    print("\n")


async def example_multi_turn_conversation():
    """Multi-turn conversation using receive_response helper."""
    print("=== Multi-Turn Conversation Example ===")

    async with ClaudeSDKClient() as client:
        # First turn
        print("User: What's the capital of France?")
        await client.query("What's the capital of France?")

        # Extract and print response
        async for msg in client.receive_response():
            display_message(msg)

        # Second turn - follow-up
        print("\nUser: What's the population of that city?")
        await client.query("What's the population of that city?")

        async for msg in client.receive_response():
            display_message(msg)

    print("\n")


async def example_concurrent_responses():
    """Handle responses while sending new messages."""
    print("=== Concurrent Send/Receive Example ===")

    async with ClaudeSDKClient() as client:
        # Background task to continuously receive messages
        async def receive_messages():
            async for message in client.receive_messages():
                display_message(message)

        # Start receiving in background
        receive_task = asyncio.create_task(receive_messages())

        # Send multiple messages with delays
        questions = [
            "What is 2 + 2?",
            "What is the square root of 144?",
            "What is 10% of 80?",
        ]

        for question in questions:
            print(f"\nUser: {question}")
            await client.query(question)
            await asyncio.sleep(3)  # Wait between messages

        # Give time for final responses
        await asyncio.sleep(2)

        # Clean up
        receive_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await receive_task

    print("\n")


async def example_with_interrupt():
    """Demonstrate interrupt capability."""
    print("=== Interrupt Example ===")
    print("IMPORTANT: Interrupts require active message consumption.")

    async with ClaudeSDKClient() as client:
        # Start a long-running task
        print("\nUser: Count from 1 to 100 slowly")
        await client.query(
            "Count from 1 to 100 slowly, with a brief pause between each number"
        )

        # Create a background task to consume messages
        messages_received = []

        async def consume_messages():
            """Consume messages in the background to enable interrupt processing."""
            async for message in client.receive_response():
                messages_received.append(message)
                display_message(message)

        # Start consuming messages in the background
        consume_task = asyncio.create_task(consume_messages())

        # Wait 2 seconds then send interrupt
        await asyncio.sleep(2)
        print("\n[After 2 seconds, sending interrupt...]")
        await client.interrupt()

        # Wait for the consume task to finish processing the interrupt
        await consume_task

        # Send new instruction after interrupt
        print("\nUser: Never mind, just tell me a quick joke")
        await client.query("Never mind, just tell me a quick joke")

        # Get the joke
        async for msg in client.receive_response():
            display_message(msg)

    print("\n")


async def example_manual_message_handling():
    """Manually handle message stream for custom logic."""
    print("=== Manual Message Handling Example ===")

    async with ClaudeSDKClient() as client:
        await client.query("List 5 programming languages and their main use cases")

        # Manually process messages with custom logic
        languages_found = []

        async for message in client.receive_messages():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        text = block.text
                        print(f"Claude: {text}")
                        # Custom logic: extract language names
                        for lang in [
                            "Python",
                            "JavaScript",
                            "Java",
                            "C++",
                            "Go",
                            "Rust",
                            "Ruby",
                        ]:
                            if lang in text and lang not in languages_found:
                                languages_found.append(lang)
                                print(f"Found language: {lang}")
            elif isinstance(message, ResultMessage):
                display_message(message)
                print(f"Total languages mentioned: {len(languages_found)}")
                break

    print("\n")


async def example_with_options():
    """Use ClaudeAgentOptions to configure the client."""
    print("=== Custom Options Example ===")

    # Configure options
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write"],  # Allow file operations
        system_prompt="You are a helpful coding assistant.",
        env={
            "ANTHROPIC_MODEL": "claude-sonnet-4-5",
        },
    )

    async with ClaudeSDKClient(options=options) as client:
        print("User: Create a simple hello.txt file with a greeting message")
        await client.query("Create a simple hello.txt file with a greeting message")

        tool_uses = []
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                display_message(msg)
                for block in msg.content:
                    if hasattr(block, "name") and not isinstance(
                        block, TextBlock
                    ):  # ToolUseBlock
                        tool_uses.append(getattr(block, "name", ""))
            else:
                display_message(msg)

        if tool_uses:
            print(f"Tools used: {', '.join(tool_uses)}")

    print("\n")


async def example_async_iterable_prompt():
    """Demonstrate send_message with async iterable."""
    print("=== Async Iterable Prompt Example ===")

    async def create_message_stream():
        """Generate a stream of messages."""
        print("User: Hello! I have multiple questions.")
        yield {
            "type": "user",
            "message": {"role": "user", "content": "Hello! I have multiple questions."},
            "parent_tool_use_id": None,
            "session_id": "qa-session",
        }

        print("User: First, what's the capital of Japan?")
        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": "First, what's the capital of Japan?",
            },
            "parent_tool_use_id": None,
            "session_id": "qa-session",
        }

        print("User: Second, what's 15% of 200?")
        yield {
            "type": "user",
            "message": {"role": "user", "content": "Second, what's 15% of 200?"},
            "parent_tool_use_id": None,
            "session_id": "qa-session",
        }

    async with ClaudeSDKClient() as client:
        # Send async iterable of messages
        await client.query(create_message_stream())

        # Receive the three responses
        async for msg in client.receive_response():
            display_message(msg)
        async for msg in client.receive_response():
            display_message(msg)
        async for msg in client.receive_response():
            display_message(msg)

    print("\n")


async def example_bash_command():
    """Example showing tool use blocks when running bash commands."""
    print("=== Bash Command Example ===")

    async with ClaudeSDKClient() as client:
        print("User: Run a bash echo command")
        await client.query("Run a bash echo command that says 'Hello from bash!'")

        # Track all message types received
        message_types = []

        async for msg in client.receive_messages():
            message_types.append(type(msg).__name__)

            if isinstance(msg, UserMessage):
                # User messages can contain tool results
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"User: {block.text}")
                    elif isinstance(block, ToolResultBlock):
                        print(
                            f"Tool Result (id: {block.tool_use_id}): {block.content[:100] if block.content else 'None'}..."
                        )

            elif isinstance(msg, AssistantMessage):
                # Assistant messages can contain tool use blocks
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")
                    elif isinstance(block, ToolUseBlock):
                        print(f"Tool Use: {block.name} (id: {block.id})")
                        if block.name == "Bash":
                            command = block.input.get("command", "")
                            print(f"  Command: {command}")

            elif isinstance(msg, ResultMessage):
                print("Result ended")
                if msg.total_cost_usd:
                    print(f"Cost: ${msg.total_cost_usd:.4f}")
                break

        print(f"\nMessage types received: {', '.join(set(message_types))}")

    print("\n")


async def example_control_protocol():
    """Demonstrate server info and interrupt capabilities."""
    print("=== Control Protocol Example ===")
    print("Shows server info retrieval and interrupt capability\n")

    async with ClaudeSDKClient() as client:
        # 1. Get server initialization info
        print("1. Getting server info...")
        server_info = await client.get_server_info()

        if server_info:
            print("✓ Server info retrieved successfully!")
            print(f"  - Available commands: {len(server_info.get('commands', []))}")
            print(f"  - Output style: {server_info.get('output_style', 'unknown')}")

            # Show available output styles if present
            styles = server_info.get('available_output_styles', [])
            if styles:
                print(f"  - Available output styles: {', '.join(styles)}")

            # Show a few example commands
            commands = server_info.get('commands', [])[:5]
            if commands:
                print("  - Example commands:")
                for cmd in commands:
                    if isinstance(cmd, dict):
                        print(f"    • {cmd.get('name', 'unknown')}")
        else:
            print("✗ No server info available (may not be in streaming mode)")

        print("\n2. Testing interrupt capability...")

        # Start a long-running task
        print("User: Count from 1 to 20 slowly")
        await client.query("Count from 1 to 20 slowly, pausing between each number")

        # Start consuming messages in background to enable interrupt
        messages = []
        async def consume():
            async for msg in client.receive_response():
                messages.append(msg)
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            # Print first 50 chars to show progress
                            print(f"Claude: {block.text[:50]}...")
                            break
                if isinstance(msg, ResultMessage):
                    break

        consume_task = asyncio.create_task(consume())

        # Wait a moment then interrupt
        await asyncio.sleep(2)
        print("\n[Sending interrupt after 2 seconds...]")

        try:
            await client.interrupt()
            print("✓ Interrupt sent successfully")
        except Exception as e:
            print(f"✗ Interrupt failed: {e}")

        # Wait for task to complete
        with contextlib.suppress(asyncio.CancelledError):
            await consume_task

        # Send new query after interrupt
        print("\nUser: Just say 'Hello!'")
        await client.query("Just say 'Hello!'")

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

    print("\n")


async def example_error_handling():
    """Demonstrate proper error handling."""
    print("=== Error Handling Example ===")

    client = ClaudeSDKClient()

    try:
        await client.connect()

        # Send a message that will take time to process
        print("User: Run a bash sleep command for 60 seconds not in the background")
        await client.query("Run a bash sleep command for 60 seconds not in the background")

        # Try to receive response with a short timeout
        try:
            messages = []
            async with asyncio.timeout(10.0):
                async for msg in client.receive_response():
                    messages.append(msg)
                    if isinstance(msg, AssistantMessage):
                        for block in msg.content:
                            if isinstance(block, TextBlock):
                                print(f"Claude: {block.text[:50]}...")
                    elif isinstance(msg, ResultMessage):
                        display_message(msg)
                        break

        except asyncio.TimeoutError:
            print(
                "\nResponse timeout after 10 seconds - demonstrating graceful handling"
            )
            print(f"Received {len(messages)} messages before timeout")

    except CLIConnectionError as e:
        print(f"Connection error: {e}")

    except Exception as e:
        print(f"Unexpected error: {e}")

    finally:
        # Always disconnect
        await client.disconnect()

    print("\n")


async def main():
    """Run all examples or a specific example based on command line argument."""
    examples = {
        "basic_streaming": example_basic_streaming,
        "multi_turn_conversation": example_multi_turn_conversation,
        "concurrent_responses": example_concurrent_responses,
        "with_interrupt": example_with_interrupt,
        "manual_message_handling": example_manual_message_handling,
        "with_options": example_with_options,
        "async_iterable_prompt": example_async_iterable_prompt,
        "bash_command": example_bash_command,
        "control_protocol": example_control_protocol,
        "error_handling": example_error_handling,
    }

    if len(sys.argv) < 2:
        # List available examples
        print("Usage: python streaming_mode.py <example_name>")
        print("\nAvailable examples:")
        print("  all - Run all examples")
        for name in examples:
            print(f"  {name}")
        sys.exit(0)

    example_name = sys.argv[1]

    if example_name == "all":
        # Run all examples
        for example in examples.values():
            await example()
            print("-" * 50 + "\n")
    elif example_name in examples:
        # Run specific example
        await examples[example_name]()
    else:
        print(f"Error: Unknown example '{example_name}'")
        print("\nAvailable examples:")
        print("  all - Run all examples")
        for name in examples:
            print(f"  {name}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())


=== File: examples/streaming_mode_ipython.py ===
#!/usr/bin/env python3
"""
IPython-friendly code snippets for ClaudeSDKClient streaming mode.

These examples are designed to be copy-pasted directly into IPython.
Each example is self-contained and can be run independently.

The queries are intentionally simplistic. In reality, a query can be a more
complex task that Claude SDK uses its agentic capabilities and tools (e.g. run
bash commands, edit files, search the web, fetch web content) to accomplish.
"""

# ============================================================================
# BASIC STREAMING
# ============================================================================

from claude_agent_sdk import AssistantMessage, ClaudeSDKClient, ResultMessage, TextBlock

async with ClaudeSDKClient() as client:
    print("User: What is 2+2?")
    await client.query("What is 2+2?")

    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")


# ============================================================================
# STREAMING WITH REAL-TIME DISPLAY
# ============================================================================

import asyncio

from claude_agent_sdk import AssistantMessage, ClaudeSDKClient, TextBlock

async with ClaudeSDKClient() as client:
    async def send_and_receive(prompt):
        print(f"User: {prompt}")
        await client.query(prompt)
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

    await send_and_receive("Tell me a short joke")
    print("\n---\n")
    await send_and_receive("Now tell me a fun fact")


# ============================================================================
# PERSISTENT CLIENT FOR MULTIPLE QUESTIONS
# ============================================================================

from claude_agent_sdk import AssistantMessage, ClaudeSDKClient, TextBlock

# Create client
client = ClaudeSDKClient()
await client.connect()


# Helper to get response
async def get_response():
    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")


# Use it multiple times
print("User: What's 2+2?")
await client.query("What's 2+2?")
await get_response()

print("User: What's 10*10?")
await client.query("What's 10*10?")
await get_response()

# Don't forget to disconnect when done
await client.disconnect()


# ============================================================================
# WITH INTERRUPT CAPABILITY
# ============================================================================
# IMPORTANT: Interrupts require active message consumption. You must be
# consuming messages from the client for the interrupt to be processed.

from claude_agent_sdk import AssistantMessage, ClaudeSDKClient, TextBlock

async with ClaudeSDKClient() as client:
    print("\n--- Sending initial message ---\n")

    # Send a long-running task
    print("User: Count from 1 to 100, run bash sleep for 1 second in between")
    await client.query("Count from 1 to 100, run bash sleep for 1 second in between")

    # Create a background task to consume messages
    messages_received = []
    interrupt_sent = False

    async def consume_messages():
        async for msg in client.receive_messages():
            messages_received.append(msg)
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"Claude: {block.text}")

            # Check if we got a result after interrupt
            if isinstance(msg, ResultMessage) and interrupt_sent:
                break

    # Start consuming messages in the background
    consume_task = asyncio.create_task(consume_messages())

    # Wait a bit then send interrupt
    await asyncio.sleep(10)
    print("\n--- Sending interrupt ---\n")
    interrupt_sent = True
    await client.interrupt()

    # Wait for the consume task to finish
    await consume_task

    # Send a new message after interrupt
    print("\n--- After interrupt, sending new message ---\n")
    await client.query("Just say 'Hello! I was interrupted.'")

    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")


# ============================================================================
# ERROR HANDLING PATTERN
# ============================================================================

from claude_agent_sdk import AssistantMessage, ClaudeSDKClient, TextBlock

try:
    async with ClaudeSDKClient() as client:
        print("User: Run a bash sleep command for 60 seconds")
        await client.query("Run a bash sleep command for 60 seconds")

        # Timeout after 20 seconds
        messages = []
        async with asyncio.timeout(20.0):
            async for msg in client.receive_response():
                messages.append(msg)
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            print(f"Claude: {block.text}")

except asyncio.TimeoutError:
    print("Request timed out after 20 seconds")
except Exception as e:
    print(f"Error: {e}")


# ============================================================================
# SENDING ASYNC ITERABLE OF MESSAGES
# ============================================================================

from claude_agent_sdk import AssistantMessage, ClaudeSDKClient, TextBlock


async def message_generator():
    """Generate multiple messages as an async iterable."""
    print("User: I have two math questions.")
    yield {
        "type": "user",
        "message": {"role": "user", "content": "I have two math questions."},
        "parent_tool_use_id": None,
        "session_id": "math-session"
    }
    print("User: What is 25 * 4?")
    yield {
        "type": "user",
        "message": {"role": "user", "content": "What is 25 * 4?"},
        "parent_tool_use_id": None,
        "session_id": "math-session"
    }
    print("User: What is 100 / 5?")
    yield {
        "type": "user",
        "message": {"role": "user", "content": "What is 100 / 5?"},
        "parent_tool_use_id": None,
        "session_id": "math-session"
    }

async with ClaudeSDKClient() as client:
    # Send async iterable instead of string
    await client.query(message_generator())

    async for msg in client.receive_response():
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")


# ============================================================================
# COLLECTING ALL MESSAGES INTO A LIST
# ============================================================================

from claude_agent_sdk import AssistantMessage, ClaudeSDKClient, TextBlock

async with ClaudeSDKClient() as client:
    print("User: What are the primary colors?")
    await client.query("What are the primary colors?")

    # Collect all messages into a list
    messages = [msg async for msg in client.receive_response()]

    # Process them afterwards
    for msg in messages:
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")
        elif isinstance(msg, ResultMessage):
            print(f"Total messages: {len(messages)}")


=== File: examples/streaming_mode_trio.py ===
#!/usr/bin/env python3
"""
Example of multi-turn conversation using trio with the Claude SDK.

This demonstrates how to use the ClaudeSDKClient with trio for interactive,
stateful conversations where you can send follow-up messages based on
Claude's responses.
"""

import trio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
    UserMessage,
)


def display_message(msg):
    """Standardized message display function.

    - UserMessage: "User: <content>"
    - AssistantMessage: "Claude: <content>"
    - SystemMessage: ignored
    - ResultMessage: "Result ended" + cost if available
    """
    if isinstance(msg, UserMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(f"User: {block.text}")
    elif isinstance(msg, AssistantMessage):
        for block in msg.content:
            if isinstance(block, TextBlock):
                print(f"Claude: {block.text}")
    elif isinstance(msg, SystemMessage):
        # Ignore system messages
        pass
    elif isinstance(msg, ResultMessage):
        print("Result ended")


async def multi_turn_conversation():
    """Example of a multi-turn conversation using trio."""
    async with ClaudeSDKClient(
        options=ClaudeAgentOptions(model="claude-sonnet-4-5")
    ) as client:
        print("=== Multi-turn Conversation with Trio ===\n")

        # First turn: Simple math question
        print("User: What's 15 + 27?")
        await client.query("What's 15 + 27?")

        async for message in client.receive_response():
            display_message(message)
        print()

        # Second turn: Follow-up calculation
        print("User: Now multiply that result by 2")
        await client.query("Now multiply that result by 2")

        async for message in client.receive_response():
            display_message(message)
        print()

        # Third turn: One more operation
        print("User: Divide that by 7 and round to 2 decimal places")
        await client.query("Divide that by 7 and round to 2 decimal places")

        async for message in client.receive_response():
            display_message(message)

        print("\nConversation complete!")


if __name__ == "__main__":
    trio.run(multi_turn_conversation)


=== File: pyproject.toml ===
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "claude-agent-sdk"
version = "0.1.1"
description = "Python SDK for Claude Code"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Anthropic", email = "support@anthropic.com"},
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
]
keywords = ["claude", "ai", "sdk", "anthropic"]
dependencies = [
    "anyio>=4.0.0",
    "typing_extensions>=4.0.0; python_version<'3.11'",
    "mcp>=0.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.20.0",
    "anyio[trio]>=4.0.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]

[project.urls]
Homepage = "https://github.com/anthropics/claude-agent-sdk-python"
Documentation = "https://docs.anthropic.com/en/docs/claude-code/sdk"
Issues = "https://github.com/anthropics/claude-agent-sdk-python/issues"

[tool.hatch.build.targets.wheel]
packages = ["src/claude_agent_sdk"]

[tool.hatch.build.targets.sdist]
include = [
    "/src",
    "/tests",
    "/README.md",
    "/LICENSE",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = [
    "--import-mode=importlib",
    "-p", "asyncio",
]

[tool.pytest-asyncio]
asyncio_mode = "auto"

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.ruff]
target-version = "py310"
line-length = 88

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "N",  # pep8-naming
    "UP", # pyupgrade
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "PTH", # flake8-use-pathlib
    "SIM", # flake8-simplify
]
ignore = [
    "E501", # line too long (handled by formatter)
]

[tool.ruff.lint.isort]
known-first-party = ["claude_agent_sdk"]

=== File: tests/conftest.py ===
"""Pytest configuration for tests."""


# No async plugin needed since we're using sync tests with anyio.run()


=== File: tests/test_changelog.py ===
import re
from pathlib import Path


class TestChangelog:
    def setup_method(self):
        self.changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"

    def test_changelog_exists(self):
        assert self.changelog_path.exists(), "CHANGELOG.md file should exist"

    def test_changelog_starts_with_header(self):
        content = self.changelog_path.read_text()
        assert content.startswith("# Changelog"), (
            "Changelog should start with '# Changelog'"
        )

    def test_changelog_has_valid_version_format(self):
        content = self.changelog_path.read_text()
        lines = content.split("\n")

        version_pattern = re.compile(r"^## \d+\.\d+\.\d+(?:\s+\(\d{4}-\d{2}-\d{2}\))?$")
        versions = []

        for line in lines:
            if line.startswith("## "):
                assert version_pattern.match(line), f"Invalid version format: {line}"
                version_match = re.match(r"^## (\d+\.\d+\.\d+)", line)
                if version_match:
                    versions.append(version_match.group(1))

        assert len(versions) > 0, "Changelog should contain at least one version"

    def test_changelog_has_bullet_points(self):
        content = self.changelog_path.read_text()
        lines = content.split("\n")

        in_version_section = False
        has_bullet_points = False

        for i, line in enumerate(lines):
            if line.startswith("## "):
                if in_version_section and not has_bullet_points:
                    raise AssertionError(
                        "Previous version section should have at least one bullet point"
                    )
                in_version_section = True
                has_bullet_points = False
            elif in_version_section and line.startswith("- "):
                has_bullet_points = True
            elif in_version_section and line.strip() == "" and i == len(lines) - 1:
                # Last line check
                assert has_bullet_points, (
                    "Each version should have at least one bullet point"
                )

        # Check the last section
        if in_version_section:
            assert has_bullet_points, (
                "Last version section should have at least one bullet point"
            )

    def test_changelog_versions_in_descending_order(self):
        content = self.changelog_path.read_text()
        lines = content.split("\n")

        versions = []
        for line in lines:
            if line.startswith("## "):
                version_match = re.match(r"^## (\d+)\.(\d+)\.(\d+)", line)
                if version_match:
                    versions.append(tuple(map(int, version_match.groups())))

        for i in range(1, len(versions)):
            assert versions[i - 1] > versions[i], (
                f"Versions should be in descending order: {versions[i - 1]} should be > {versions[i]}"
            )

    def test_changelog_no_empty_bullet_points(self):
        content = self.changelog_path.read_text()
        lines = content.split("\n")

        for line in lines:
            if line.strip() == "-":
                raise AssertionError("Changelog should not have empty bullet points")


=== File: tests/test_client.py ===
"""Tests for Claude SDK client functionality."""

from unittest.mock import AsyncMock, Mock, patch

import anyio

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, query
from claude_agent_sdk.types import TextBlock


class TestQueryFunction:
    """Test the main query function."""

    def test_query_single_prompt(self):
        """Test query with a single prompt."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.client.InternalClient.process_query"
            ) as mock_process:
                # Mock the async generator
                async def mock_generator():
                    yield AssistantMessage(
                        content=[TextBlock(text="4")], model="claude-opus-4-1-20250805"
                    )

                mock_process.return_value = mock_generator()

                messages = []
                async for msg in query(prompt="What is 2+2?"):
                    messages.append(msg)

                assert len(messages) == 1
                assert isinstance(messages[0], AssistantMessage)
                assert messages[0].content[0].text == "4"

        anyio.run(_test)

    def test_query_with_options(self):
        """Test query with various options."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.client.InternalClient.process_query"
            ) as mock_process:

                async def mock_generator():
                    yield AssistantMessage(
                        content=[TextBlock(text="Hello!")],
                        model="claude-opus-4-1-20250805",
                    )

                mock_process.return_value = mock_generator()

                options = ClaudeAgentOptions(
                    allowed_tools=["Read", "Write"],
                    system_prompt="You are helpful",
                    permission_mode="acceptEdits",
                    max_turns=5,
                )

                messages = []
                async for msg in query(prompt="Hi", options=options):
                    messages.append(msg)

                # Verify process_query was called with correct prompt and options
                mock_process.assert_called_once()
                call_args = mock_process.call_args
                assert call_args[1]["prompt"] == "Hi"
                assert call_args[1]["options"] == options

        anyio.run(_test)

    def test_query_with_cwd(self):
        """Test query with custom working directory."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.client.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = AsyncMock()
                mock_transport_class.return_value = mock_transport

                # Mock the message stream
                async def mock_receive():
                    yield {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "Done"}],
                            "model": "claude-opus-4-1-20250805",
                        },
                    }
                    yield {
                        "type": "result",
                        "subtype": "success",
                        "duration_ms": 1000,
                        "duration_api_ms": 800,
                        "is_error": False,
                        "num_turns": 1,
                        "session_id": "test-session",
                        "total_cost_usd": 0.001,
                    }

                mock_transport.read_messages = mock_receive
                mock_transport.connect = AsyncMock()
                mock_transport.close = AsyncMock()
                mock_transport.end_input = AsyncMock()
                mock_transport.write = AsyncMock()
                mock_transport.is_ready = Mock(return_value=True)

                options = ClaudeAgentOptions(cwd="/custom/path")
                messages = []
                async for msg in query(prompt="test", options=options):
                    messages.append(msg)

                # Verify transport was created with correct parameters
                mock_transport_class.assert_called_once()
                call_kwargs = mock_transport_class.call_args.kwargs
                assert call_kwargs["prompt"] == "test"
                assert call_kwargs["options"].cwd == "/custom/path"

        anyio.run(_test)


=== File: tests/test_errors.py ===
"""Tests for Claude SDK error handling."""

from claude_agent_sdk import (
    ClaudeSDKError,
    CLIConnectionError,
    CLIJSONDecodeError,
    CLINotFoundError,
    ProcessError,
)


class TestErrorTypes:
    """Test error types and their properties."""

    def test_base_error(self):
        """Test base ClaudeSDKError."""
        error = ClaudeSDKError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert isinstance(error, Exception)

    def test_cli_not_found_error(self):
        """Test CLINotFoundError."""
        error = CLINotFoundError("Claude Code not found")
        assert isinstance(error, ClaudeSDKError)
        assert "Claude Code not found" in str(error)

    def test_connection_error(self):
        """Test CLIConnectionError."""
        error = CLIConnectionError("Failed to connect to CLI")
        assert isinstance(error, ClaudeSDKError)
        assert "Failed to connect to CLI" in str(error)

    def test_process_error(self):
        """Test ProcessError with exit code and stderr."""
        error = ProcessError("Process failed", exit_code=1, stderr="Command not found")
        assert error.exit_code == 1
        assert error.stderr == "Command not found"
        assert "Process failed" in str(error)
        assert "exit code: 1" in str(error)
        assert "Command not found" in str(error)

    def test_json_decode_error(self):
        """Test CLIJSONDecodeError."""
        import json

        try:
            json.loads("{invalid json}")
        except json.JSONDecodeError as e:
            error = CLIJSONDecodeError("{invalid json}", e)
            assert error.line == "{invalid json}"
            assert error.original_error == e
            assert "Failed to decode JSON" in str(error)


=== File: tests/test_integration.py ===
"""Integration tests for Claude SDK.

These tests verify end-to-end functionality with mocked CLI responses.
"""

from unittest.mock import AsyncMock, Mock, patch

import anyio
import pytest

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    CLINotFoundError,
    ResultMessage,
    query,
)
from claude_agent_sdk.types import ToolUseBlock


class TestIntegration:
    """End-to-end integration tests."""

    def test_simple_query_response(self):
        """Test a simple query with text response."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.client.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = AsyncMock()
                mock_transport_class.return_value = mock_transport

                # Mock the message stream
                async def mock_receive():
                    yield {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "2 + 2 equals 4"}],
                            "model": "claude-opus-4-1-20250805",
                        },
                    }
                    yield {
                        "type": "result",
                        "subtype": "success",
                        "duration_ms": 1000,
                        "duration_api_ms": 800,
                        "is_error": False,
                        "num_turns": 1,
                        "session_id": "test-session",
                        "total_cost_usd": 0.001,
                    }

                mock_transport.read_messages = mock_receive
                mock_transport.connect = AsyncMock()
                mock_transport.close = AsyncMock()
                mock_transport.end_input = AsyncMock()
                mock_transport.write = AsyncMock()
                mock_transport.is_ready = Mock(return_value=True)

                # Run query
                messages = []
                async for msg in query(prompt="What is 2 + 2?"):
                    messages.append(msg)

                # Verify results
                assert len(messages) == 2

                # Check assistant message
                assert isinstance(messages[0], AssistantMessage)
                assert len(messages[0].content) == 1
                assert messages[0].content[0].text == "2 + 2 equals 4"

                # Check result message
                assert isinstance(messages[1], ResultMessage)
                assert messages[1].total_cost_usd == 0.001
                assert messages[1].session_id == "test-session"

        anyio.run(_test)

    def test_query_with_tool_use(self):
        """Test query that uses tools."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.client.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = AsyncMock()
                mock_transport_class.return_value = mock_transport

                # Mock the message stream with tool use
                async def mock_receive():
                    yield {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Let me read that file for you.",
                                },
                                {
                                    "type": "tool_use",
                                    "id": "tool-123",
                                    "name": "Read",
                                    "input": {"file_path": "/test.txt"},
                                },
                            ],
                            "model": "claude-opus-4-1-20250805",
                        },
                    }
                    yield {
                        "type": "result",
                        "subtype": "success",
                        "duration_ms": 1500,
                        "duration_api_ms": 1200,
                        "is_error": False,
                        "num_turns": 1,
                        "session_id": "test-session-2",
                        "total_cost_usd": 0.002,
                    }

                mock_transport.read_messages = mock_receive
                mock_transport.connect = AsyncMock()
                mock_transport.close = AsyncMock()
                mock_transport.end_input = AsyncMock()
                mock_transport.write = AsyncMock()
                mock_transport.is_ready = Mock(return_value=True)

                # Run query with tools enabled
                messages = []
                async for msg in query(
                    prompt="Read /test.txt",
                    options=ClaudeAgentOptions(allowed_tools=["Read"]),
                ):
                    messages.append(msg)

                # Verify results
                assert len(messages) == 2

                # Check assistant message with tool use
                assert isinstance(messages[0], AssistantMessage)
                assert len(messages[0].content) == 2
                assert messages[0].content[0].text == "Let me read that file for you."
                assert isinstance(messages[0].content[1], ToolUseBlock)
                assert messages[0].content[1].name == "Read"
                assert messages[0].content[1].input["file_path"] == "/test.txt"

        anyio.run(_test)

    def test_cli_not_found(self):
        """Test handling when CLI is not found."""

        async def _test():
            with (
                patch("shutil.which", return_value=None),
                patch("pathlib.Path.exists", return_value=False),
                pytest.raises(CLINotFoundError) as exc_info,
            ):
                async for _ in query(prompt="test"):
                    pass

            assert "Claude Code not found" in str(exc_info.value)

        anyio.run(_test)

    def test_continuation_option(self):
        """Test query with continue_conversation option."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.client.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = AsyncMock()
                mock_transport_class.return_value = mock_transport

                # Mock the message stream
                async def mock_receive():
                    yield {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Continuing from previous conversation",
                                }
                            ],
                            "model": "claude-opus-4-1-20250805",
                        },
                    }

                mock_transport.read_messages = mock_receive
                mock_transport.connect = AsyncMock()
                mock_transport.close = AsyncMock()
                mock_transport.end_input = AsyncMock()
                mock_transport.write = AsyncMock()
                mock_transport.is_ready = Mock(return_value=True)

                # Run query with continuation
                messages = []
                async for msg in query(
                    prompt="Continue",
                    options=ClaudeAgentOptions(continue_conversation=True),
                ):
                    messages.append(msg)

                # Verify transport was created with continuation option
                mock_transport_class.assert_called_once()
                call_kwargs = mock_transport_class.call_args.kwargs
                assert call_kwargs["options"].continue_conversation is True

        anyio.run(_test)


=== File: tests/test_message_parser.py ===
"""Tests for message parser error handling."""

import pytest

from claude_agent_sdk._errors import MessageParseError
from claude_agent_sdk._internal.message_parser import parse_message
from claude_agent_sdk.types import (
    AssistantMessage,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)


class TestMessageParser:
    """Test message parsing with the new exception behavior."""

    def test_parse_valid_user_message(self):
        """Test parsing a valid user message."""
        data = {
            "type": "user",
            "message": {"content": [{"type": "text", "text": "Hello"}]},
        }
        message = parse_message(data)
        assert isinstance(message, UserMessage)
        assert len(message.content) == 1
        assert isinstance(message.content[0], TextBlock)
        assert message.content[0].text == "Hello"

    def test_parse_user_message_with_tool_use(self):
        """Test parsing a user message with tool_use block."""
        data = {
            "type": "user",
            "message": {
                "content": [
                    {"type": "text", "text": "Let me read this file"},
                    {
                        "type": "tool_use",
                        "id": "tool_456",
                        "name": "Read",
                        "input": {"file_path": "/example.txt"},
                    },
                ]
            },
        }
        message = parse_message(data)
        assert isinstance(message, UserMessage)
        assert len(message.content) == 2
        assert isinstance(message.content[0], TextBlock)
        assert isinstance(message.content[1], ToolUseBlock)
        assert message.content[1].id == "tool_456"
        assert message.content[1].name == "Read"
        assert message.content[1].input == {"file_path": "/example.txt"}

    def test_parse_user_message_with_tool_result(self):
        """Test parsing a user message with tool_result block."""
        data = {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "tool_789",
                        "content": "File contents here",
                    }
                ]
            },
        }
        message = parse_message(data)
        assert isinstance(message, UserMessage)
        assert len(message.content) == 1
        assert isinstance(message.content[0], ToolResultBlock)
        assert message.content[0].tool_use_id == "tool_789"
        assert message.content[0].content == "File contents here"

    def test_parse_user_message_with_tool_result_error(self):
        """Test parsing a user message with error tool_result block."""
        data = {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "tool_error",
                        "content": "File not found",
                        "is_error": True,
                    }
                ]
            },
        }
        message = parse_message(data)
        assert isinstance(message, UserMessage)
        assert len(message.content) == 1
        assert isinstance(message.content[0], ToolResultBlock)
        assert message.content[0].tool_use_id == "tool_error"
        assert message.content[0].content == "File not found"
        assert message.content[0].is_error is True

    def test_parse_user_message_with_mixed_content(self):
        """Test parsing a user message with mixed content blocks."""
        data = {
            "type": "user",
            "message": {
                "content": [
                    {"type": "text", "text": "Here's what I found:"},
                    {
                        "type": "tool_use",
                        "id": "use_1",
                        "name": "Search",
                        "input": {"query": "test"},
                    },
                    {
                        "type": "tool_result",
                        "tool_use_id": "use_1",
                        "content": "Search results",
                    },
                    {"type": "text", "text": "What do you think?"},
                ]
            },
        }
        message = parse_message(data)
        assert isinstance(message, UserMessage)
        assert len(message.content) == 4
        assert isinstance(message.content[0], TextBlock)
        assert isinstance(message.content[1], ToolUseBlock)
        assert isinstance(message.content[2], ToolResultBlock)
        assert isinstance(message.content[3], TextBlock)

    def test_parse_user_message_inside_subagent(self):
        """Test parsing a valid user message."""
        data = {
            "type": "user",
            "message": {"content": [{"type": "text", "text": "Hello"}]},
            "parent_tool_use_id": "toolu_01Xrwd5Y13sEHtzScxR77So8",
        }
        message = parse_message(data)
        assert isinstance(message, UserMessage)
        assert message.parent_tool_use_id == "toolu_01Xrwd5Y13sEHtzScxR77So8"

    def test_parse_valid_assistant_message(self):
        """Test parsing a valid assistant message."""
        data = {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "text", "text": "Hello"},
                    {
                        "type": "tool_use",
                        "id": "tool_123",
                        "name": "Read",
                        "input": {"file_path": "/test.txt"},
                    },
                ],
                "model": "claude-opus-4-1-20250805",
            },
        }
        message = parse_message(data)
        assert isinstance(message, AssistantMessage)
        assert len(message.content) == 2
        assert isinstance(message.content[0], TextBlock)
        assert isinstance(message.content[1], ToolUseBlock)

    def test_parse_assistant_message_with_thinking(self):
        """Test parsing an assistant message with thinking block."""
        data = {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "thinking",
                        "thinking": "I'm thinking about the answer...",
                        "signature": "sig-123",
                    },
                    {"type": "text", "text": "Here's my response"},
                ],
                "model": "claude-opus-4-1-20250805",
            },
        }
        message = parse_message(data)
        assert isinstance(message, AssistantMessage)
        assert len(message.content) == 2
        assert isinstance(message.content[0], ThinkingBlock)
        assert message.content[0].thinking == "I'm thinking about the answer..."
        assert message.content[0].signature == "sig-123"
        assert isinstance(message.content[1], TextBlock)
        assert message.content[1].text == "Here's my response"

    def test_parse_valid_system_message(self):
        """Test parsing a valid system message."""
        data = {"type": "system", "subtype": "start"}
        message = parse_message(data)
        assert isinstance(message, SystemMessage)
        assert message.subtype == "start"

    def test_parse_assistant_message_inside_subagent(self):
        """Test parsing a valid assistant message."""
        data = {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "text", "text": "Hello"},
                    {
                        "type": "tool_use",
                        "id": "tool_123",
                        "name": "Read",
                        "input": {"file_path": "/test.txt"},
                    },
                ],
                "model": "claude-opus-4-1-20250805",
            },
            "parent_tool_use_id": "toolu_01Xrwd5Y13sEHtzScxR77So8",
        }
        message = parse_message(data)
        assert isinstance(message, AssistantMessage)
        assert message.parent_tool_use_id == "toolu_01Xrwd5Y13sEHtzScxR77So8"

    def test_parse_valid_result_message(self):
        """Test parsing a valid result message."""
        data = {
            "type": "result",
            "subtype": "success",
            "duration_ms": 1000,
            "duration_api_ms": 500,
            "is_error": False,
            "num_turns": 2,
            "session_id": "session_123",
        }
        message = parse_message(data)
        assert isinstance(message, ResultMessage)
        assert message.subtype == "success"

    def test_parse_invalid_data_type(self):
        """Test that non-dict data raises MessageParseError."""
        with pytest.raises(MessageParseError) as exc_info:
            parse_message("not a dict")  # type: ignore
        assert "Invalid message data type" in str(exc_info.value)
        assert "expected dict, got str" in str(exc_info.value)

    def test_parse_missing_type_field(self):
        """Test that missing 'type' field raises MessageParseError."""
        with pytest.raises(MessageParseError) as exc_info:
            parse_message({"message": {"content": []}})
        assert "Message missing 'type' field" in str(exc_info.value)

    def test_parse_unknown_message_type(self):
        """Test that unknown message type raises MessageParseError."""
        with pytest.raises(MessageParseError) as exc_info:
            parse_message({"type": "unknown_type"})
        assert "Unknown message type: unknown_type" in str(exc_info.value)

    def test_parse_user_message_missing_fields(self):
        """Test that user message with missing fields raises MessageParseError."""
        with pytest.raises(MessageParseError) as exc_info:
            parse_message({"type": "user"})
        assert "Missing required field in user message" in str(exc_info.value)

    def test_parse_assistant_message_missing_fields(self):
        """Test that assistant message with missing fields raises MessageParseError."""
        with pytest.raises(MessageParseError) as exc_info:
            parse_message({"type": "assistant"})
        assert "Missing required field in assistant message" in str(exc_info.value)

    def test_parse_system_message_missing_fields(self):
        """Test that system message with missing fields raises MessageParseError."""
        with pytest.raises(MessageParseError) as exc_info:
            parse_message({"type": "system"})
        assert "Missing required field in system message" in str(exc_info.value)

    def test_parse_result_message_missing_fields(self):
        """Test that result message with missing fields raises MessageParseError."""
        with pytest.raises(MessageParseError) as exc_info:
            parse_message({"type": "result", "subtype": "success"})
        assert "Missing required field in result message" in str(exc_info.value)

    def test_message_parse_error_contains_data(self):
        """Test that MessageParseError contains the original data."""
        data = {"type": "unknown", "some": "data"}
        with pytest.raises(MessageParseError) as exc_info:
            parse_message(data)
        assert exc_info.value.data == data


=== File: tests/test_streaming_client.py ===
"""Tests for ClaudeSDKClient streaming functionality and query() with async iterables."""

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import anyio
import pytest

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    CLIConnectionError,
    ResultMessage,
    TextBlock,
    UserMessage,
    query,
)
from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport


def create_mock_transport(with_init_response=True):
    """Create a properly configured mock transport.

    Args:
        with_init_response: If True, automatically respond to initialization request
    """
    mock_transport = AsyncMock()
    mock_transport.connect = AsyncMock()
    mock_transport.close = AsyncMock()
    mock_transport.end_input = AsyncMock()
    mock_transport.write = AsyncMock()
    mock_transport.is_ready = Mock(return_value=True)

    # Track written messages to simulate control protocol responses
    written_messages = []

    async def mock_write(data):
        written_messages.append(data)

    mock_transport.write.side_effect = mock_write

    # Default read_messages to handle control protocol
    async def control_protocol_generator():
        # Wait for initialization request if needed
        if with_init_response:
            # Wait a bit for the write to happen
            await asyncio.sleep(0.01)

            # Check if initialization was requested
            for msg_str in written_messages:
                try:
                    msg = json.loads(msg_str.strip())
                    if (
                        msg.get("type") == "control_request"
                        and msg.get("request", {}).get("subtype") == "initialize"
                    ):
                        # Send initialization response
                        yield {
                            "type": "control_response",
                            "response": {
                                "request_id": msg.get("request_id"),
                                "subtype": "success",
                                "commands": [],
                                "output_style": "default",
                            },
                        }
                        break
                except (json.JSONDecodeError, KeyError, AttributeError):
                    pass

            # Keep checking for other control requests (like interrupt)
            last_check = len(written_messages)
            timeout_counter = 0
            while timeout_counter < 100:  # Avoid infinite loop
                await asyncio.sleep(0.01)
                timeout_counter += 1

                # Check for new messages
                for msg_str in written_messages[last_check:]:
                    try:
                        msg = json.loads(msg_str.strip())
                        if msg.get("type") == "control_request":
                            subtype = msg.get("request", {}).get("subtype")
                            if subtype == "interrupt":
                                # Send interrupt response
                                yield {
                                    "type": "control_response",
                                    "response": {
                                        "request_id": msg.get("request_id"),
                                        "subtype": "success",
                                    },
                                }
                                return  # End after interrupt
                    except (json.JSONDecodeError, KeyError, AttributeError):
                        pass
                last_check = len(written_messages)

        # Then end the stream
        return

    mock_transport.read_messages = control_protocol_generator
    return mock_transport


class TestClaudeSDKClientStreaming:
    """Test ClaudeSDKClient streaming functionality."""

    def test_auto_connect_with_context_manager(self):
        """Test automatic connection when using context manager."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = create_mock_transport()
                mock_transport_class.return_value = mock_transport

                async with ClaudeSDKClient() as client:
                    # Verify connect was called
                    mock_transport.connect.assert_called_once()
                    assert client._transport is mock_transport

                # Verify disconnect was called on exit
                mock_transport.close.assert_called_once()

        anyio.run(_test)

    def test_manual_connect_disconnect(self):
        """Test manual connect and disconnect."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = create_mock_transport()
                mock_transport_class.return_value = mock_transport

                client = ClaudeSDKClient()
                await client.connect()

                # Verify connect was called
                mock_transport.connect.assert_called_once()
                assert client._transport is mock_transport

                await client.disconnect()
                # Verify disconnect was called
                mock_transport.close.assert_called_once()
                assert client._transport is None

        anyio.run(_test)

    def test_connect_with_string_prompt(self):
        """Test connecting with a string prompt."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = create_mock_transport()
                mock_transport_class.return_value = mock_transport

                client = ClaudeSDKClient()
                await client.connect("Hello Claude")

                # Verify transport was created with string prompt
                call_kwargs = mock_transport_class.call_args.kwargs
                assert call_kwargs["prompt"] == "Hello Claude"

        anyio.run(_test)

    def test_connect_with_async_iterable(self):
        """Test connecting with an async iterable."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = create_mock_transport()
                mock_transport_class.return_value = mock_transport

                async def message_stream():
                    yield {"type": "user", "message": {"role": "user", "content": "Hi"}}
                    yield {
                        "type": "user",
                        "message": {"role": "user", "content": "Bye"},
                    }

                client = ClaudeSDKClient()
                stream = message_stream()
                await client.connect(stream)

                # Verify transport was created with async iterable
                call_kwargs = mock_transport_class.call_args.kwargs
                # Should be the same async iterator
                assert call_kwargs["prompt"] is stream

        anyio.run(_test)

    def test_query(self):
        """Test sending a query."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = create_mock_transport()
                mock_transport_class.return_value = mock_transport

                async with ClaudeSDKClient() as client:
                    await client.query("Test message")

                    # Verify write was called with correct format
                    # Should have at least 2 writes: init request and user message
                    assert mock_transport.write.call_count >= 2

                    # Find the user message in the write calls
                    user_msg_found = False
                    for call in mock_transport.write.call_args_list:
                        data = call[0][0]
                        try:
                            msg = json.loads(data.strip())
                            if msg.get("type") == "user":
                                assert msg["message"]["content"] == "Test message"
                                assert msg["session_id"] == "default"
                                user_msg_found = True
                                break
                        except (json.JSONDecodeError, KeyError, AttributeError):
                            pass
                    assert user_msg_found, "User message not found in write calls"

        anyio.run(_test)

    def test_send_message_with_session_id(self):
        """Test sending a message with custom session ID."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = create_mock_transport()
                mock_transport_class.return_value = mock_transport

                async with ClaudeSDKClient() as client:
                    await client.query("Test", session_id="custom-session")

                    # Find the user message with custom session ID
                    session_found = False
                    for call in mock_transport.write.call_args_list:
                        data = call[0][0]
                        try:
                            msg = json.loads(data.strip())
                            if msg.get("type") == "user":
                                assert msg["session_id"] == "custom-session"
                                session_found = True
                                break
                        except (json.JSONDecodeError, KeyError, AttributeError):
                            pass
                    assert session_found, "User message with custom session not found"

        anyio.run(_test)

    def test_send_message_not_connected(self):
        """Test sending message when not connected raises error."""

        async def _test():
            client = ClaudeSDKClient()
            with pytest.raises(CLIConnectionError, match="Not connected"):
                await client.query("Test")

        anyio.run(_test)

    def test_receive_messages(self):
        """Test receiving messages."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = create_mock_transport()
                mock_transport_class.return_value = mock_transport

                # Mock the message stream with control protocol support
                async def mock_receive():
                    # First handle initialization
                    await asyncio.sleep(0.01)
                    written = mock_transport.write.call_args_list
                    for call in written:
                        data = call[0][0]
                        try:
                            msg = json.loads(data.strip())
                            if (
                                msg.get("type") == "control_request"
                                and msg.get("request", {}).get("subtype")
                                == "initialize"
                            ):
                                yield {
                                    "type": "control_response",
                                    "response": {
                                        "request_id": msg.get("request_id"),
                                        "subtype": "success",
                                        "commands": [],
                                        "output_style": "default",
                                    },
                                }
                                break
                        except (json.JSONDecodeError, KeyError, AttributeError):
                            pass

                    # Then yield the actual messages
                    yield {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "Hello!"}],
                            "model": "claude-opus-4-1-20250805",
                        },
                    }
                    yield {
                        "type": "user",
                        "message": {"role": "user", "content": "Hi there"},
                    }

                mock_transport.read_messages = mock_receive

                async with ClaudeSDKClient() as client:
                    messages = []
                    async for msg in client.receive_messages():
                        messages.append(msg)
                        if len(messages) == 2:
                            break

                    assert len(messages) == 2
                    assert isinstance(messages[0], AssistantMessage)
                    assert isinstance(messages[0].content[0], TextBlock)
                    assert messages[0].content[0].text == "Hello!"
                    assert isinstance(messages[1], UserMessage)
                    assert messages[1].content == "Hi there"

        anyio.run(_test)

    def test_receive_response(self):
        """Test receive_response stops at ResultMessage."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = create_mock_transport()
                mock_transport_class.return_value = mock_transport

                # Mock the message stream with control protocol support
                async def mock_receive():
                    # First handle initialization
                    await asyncio.sleep(0.01)
                    written = mock_transport.write.call_args_list
                    for call in written:
                        data = call[0][0]
                        try:
                            msg = json.loads(data.strip())
                            if (
                                msg.get("type") == "control_request"
                                and msg.get("request", {}).get("subtype")
                                == "initialize"
                            ):
                                yield {
                                    "type": "control_response",
                                    "response": {
                                        "request_id": msg.get("request_id"),
                                        "subtype": "success",
                                        "commands": [],
                                        "output_style": "default",
                                    },
                                }
                                break
                        except (json.JSONDecodeError, KeyError, AttributeError):
                            pass

                    # Then yield the actual messages
                    yield {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "Answer"}],
                            "model": "claude-opus-4-1-20250805",
                        },
                    }
                    yield {
                        "type": "result",
                        "subtype": "success",
                        "duration_ms": 1000,
                        "duration_api_ms": 800,
                        "is_error": False,
                        "num_turns": 1,
                        "session_id": "test",
                        "total_cost_usd": 0.001,
                    }
                    # This should not be yielded
                    yield {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [
                                {"type": "text", "text": "Should not see this"}
                            ],
                        },
                        "model": "claude-opus-4-1-20250805",
                    }

                mock_transport.read_messages = mock_receive

                async with ClaudeSDKClient() as client:
                    messages = []
                    async for msg in client.receive_response():
                        messages.append(msg)

                    # Should only get 2 messages (assistant + result)
                    assert len(messages) == 2
                    assert isinstance(messages[0], AssistantMessage)
                    assert isinstance(messages[1], ResultMessage)

        anyio.run(_test)

    def test_interrupt(self):
        """Test interrupt functionality."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = create_mock_transport()
                mock_transport_class.return_value = mock_transport

                async with ClaudeSDKClient() as client:
                    # Interrupt is now handled via control protocol
                    await client.interrupt()
                    # Check that a control request was sent via write
                    write_calls = mock_transport.write.call_args_list
                    interrupt_found = False
                    for call in write_calls:
                        data = call[0][0]
                        try:
                            msg = json.loads(data.strip())
                            if (
                                msg.get("type") == "control_request"
                                and msg.get("request", {}).get("subtype") == "interrupt"
                            ):
                                interrupt_found = True
                                break
                        except (json.JSONDecodeError, KeyError, AttributeError):
                            pass
                    assert interrupt_found, "Interrupt control request not found"

        anyio.run(_test)

    def test_interrupt_not_connected(self):
        """Test interrupt when not connected raises error."""

        async def _test():
            client = ClaudeSDKClient()
            with pytest.raises(CLIConnectionError, match="Not connected"):
                await client.interrupt()

        anyio.run(_test)

    def test_client_with_options(self):
        """Test client initialization with options."""

        async def _test():
            options = ClaudeAgentOptions(
                cwd="/custom/path",
                allowed_tools=["Read", "Write"],
                system_prompt="Be helpful",
            )

            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = create_mock_transport()
                mock_transport_class.return_value = mock_transport

                client = ClaudeSDKClient(options=options)
                await client.connect()

                # Verify options were passed to transport
                call_kwargs = mock_transport_class.call_args.kwargs
                assert call_kwargs["options"] is options

        anyio.run(_test)

    def test_concurrent_send_receive(self):
        """Test concurrent sending and receiving messages."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = create_mock_transport()
                mock_transport_class.return_value = mock_transport

                # Mock receive to wait then yield messages with control protocol support
                async def mock_receive():
                    # First handle initialization
                    await asyncio.sleep(0.01)
                    written = mock_transport.write.call_args_list
                    for call in written:
                        if call:
                            data = call[0][0]
                            try:
                                msg = json.loads(data.strip())
                                if (
                                    msg.get("type") == "control_request"
                                    and msg.get("request", {}).get("subtype")
                                    == "initialize"
                                ):
                                    yield {
                                        "type": "control_response",
                                        "response": {
                                            "request_id": msg.get("request_id"),
                                            "subtype": "success",
                                            "commands": [],
                                            "output_style": "default",
                                        },
                                    }
                                    break
                            except (json.JSONDecodeError, KeyError, AttributeError):
                                pass

                    # Then yield the actual messages
                    await asyncio.sleep(0.1)
                    yield {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "Response 1"}],
                            "model": "claude-opus-4-1-20250805",
                        },
                    }
                    await asyncio.sleep(0.1)
                    yield {
                        "type": "result",
                        "subtype": "success",
                        "duration_ms": 1000,
                        "duration_api_ms": 800,
                        "is_error": False,
                        "num_turns": 1,
                        "session_id": "test",
                        "total_cost_usd": 0.001,
                    }

                mock_transport.read_messages = mock_receive

                async with ClaudeSDKClient() as client:
                    # Helper to get next message
                    async def get_next_message():
                        return await client.receive_response().__anext__()

                    # Start receiving in background
                    receive_task = asyncio.create_task(get_next_message())

                    # Send message while receiving
                    await client.query("Question 1")

                    # Wait for first message
                    first_msg = await receive_task
                    assert isinstance(first_msg, AssistantMessage)

        anyio.run(_test)


class TestQueryWithAsyncIterable:
    """Test query() function with async iterable inputs."""

    def test_query_with_async_iterable(self):
        """Test query with async iterable of messages."""

        async def _test():
            async def message_stream():
                yield {"type": "user", "message": {"role": "user", "content": "First"}}
                yield {"type": "user", "message": {"role": "user", "content": "Second"}}

            # Create a simple test script that validates stdin and outputs a result
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                test_script = f.name
                f.write("""#!/usr/bin/env python3
import sys
import json

# Read stdin messages
stdin_messages = []
while True:
    line = sys.stdin.readline()
    if not line:
        break

    try:
        msg = json.loads(line.strip())
        # Handle control requests
        if msg.get("type") == "control_request":
            request_id = msg.get("request_id")
            request = msg.get("request", {})

            # Send control response for initialize
            if request.get("subtype") == "initialize":
                response = {
                    "type": "control_response",
                    "response": {
                        "subtype": "success",
                        "request_id": request_id,
                        "response": {
                            "commands": [],
                            "output_style": "default"
                        }
                    }
                }
                print(json.dumps(response))
                sys.stdout.flush()
        else:
            stdin_messages.append(line.strip())
    except:
        stdin_messages.append(line.strip())

# Verify we got 2 user messages
assert len(stdin_messages) == 2
assert '"First"' in stdin_messages[0]
assert '"Second"' in stdin_messages[1]

# Output a valid result
print('{"type": "result", "subtype": "success", "duration_ms": 100, "duration_api_ms": 50, "is_error": false, "num_turns": 1, "session_id": "test", "total_cost_usd": 0.001}')
""")

            # Make script executable (Unix-style systems)
            if sys.platform != "win32":
                Path(test_script).chmod(0o755)

            try:
                # Mock _find_cli to return the test script path directly
                with patch.object(
                    SubprocessCLITransport, "_find_cli", return_value=test_script
                ):
                    # Mock _build_command to properly execute Python script
                    original_build_command = SubprocessCLITransport._build_command

                    def mock_build_command(self):
                        # Get original command
                        cmd = original_build_command(self)
                        # On Windows, we need to use python interpreter to run the script
                        if sys.platform == "win32":
                            # Replace first element with python interpreter and script
                            cmd[0:1] = [sys.executable, test_script]
                        else:
                            # On Unix, just use the script directly
                            cmd[0] = test_script
                        return cmd

                    with patch.object(
                        SubprocessCLITransport, "_build_command", mock_build_command
                    ):
                        # Run query with async iterable
                        messages = []
                        async for msg in query(prompt=message_stream()):
                            messages.append(msg)

                        # Should get the result message
                        assert len(messages) == 1
                        assert isinstance(messages[0], ResultMessage)
                        assert messages[0].subtype == "success"
            finally:
                # Clean up
                Path(test_script).unlink()

        anyio.run(_test)


class TestClaudeSDKClientEdgeCases:
    """Test edge cases and error scenarios."""

    def test_receive_messages_not_connected(self):
        """Test receiving messages when not connected."""

        async def _test():
            client = ClaudeSDKClient()
            with pytest.raises(CLIConnectionError, match="Not connected"):
                async for _ in client.receive_messages():
                    pass

        anyio.run(_test)

    def test_receive_response_not_connected(self):
        """Test receive_response when not connected."""

        async def _test():
            client = ClaudeSDKClient()
            with pytest.raises(CLIConnectionError, match="Not connected"):
                async for _ in client.receive_response():
                    pass

        anyio.run(_test)

    def test_double_connect(self):
        """Test connecting twice."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                # Create a new mock transport for each call
                mock_transport_class.side_effect = [
                    create_mock_transport(),
                    create_mock_transport(),
                ]

                client = ClaudeSDKClient()
                await client.connect()
                # Second connect should create new transport
                await client.connect()

                # Should have been called twice
                assert mock_transport_class.call_count == 2

        anyio.run(_test)

    def test_disconnect_without_connect(self):
        """Test disconnecting without connecting first."""

        async def _test():
            client = ClaudeSDKClient()
            # Should not raise error
            await client.disconnect()

        anyio.run(_test)

    def test_context_manager_with_exception(self):
        """Test context manager cleans up on exception."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = create_mock_transport()
                mock_transport_class.return_value = mock_transport

                with pytest.raises(ValueError):
                    async with ClaudeSDKClient():
                        raise ValueError("Test error")

                # Disconnect should still be called
                mock_transport.close.assert_called_once()

        anyio.run(_test)

    def test_receive_response_list_comprehension(self):
        """Test collecting messages with list comprehension as shown in examples."""

        async def _test():
            with patch(
                "claude_agent_sdk._internal.transport.subprocess_cli.SubprocessCLITransport"
            ) as mock_transport_class:
                mock_transport = create_mock_transport()
                mock_transport_class.return_value = mock_transport

                # Mock the message stream with control protocol support
                async def mock_receive():
                    # First handle initialization
                    await asyncio.sleep(0.01)
                    written = mock_transport.write.call_args_list
                    for call in written:
                        if call:
                            data = call[0][0]
                            try:
                                msg = json.loads(data.strip())
                                if (
                                    msg.get("type") == "control_request"
                                    and msg.get("request", {}).get("subtype")
                                    == "initialize"
                                ):
                                    yield {
                                        "type": "control_response",
                                        "response": {
                                            "request_id": msg.get("request_id"),
                                            "subtype": "success",
                                            "commands": [],
                                            "output_style": "default",
                                        },
                                    }
                                    break
                            except (json.JSONDecodeError, KeyError, AttributeError):
                                pass

                    # Then yield the actual messages
                    yield {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "Hello"}],
                            "model": "claude-opus-4-1-20250805",
                        },
                    }
                    yield {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "text", "text": "World"}],
                            "model": "claude-opus-4-1-20250805",
                        },
                    }
                    yield {
                        "type": "result",
                        "subtype": "success",
                        "duration_ms": 1000,
                        "duration_api_ms": 800,
                        "is_error": False,
                        "num_turns": 1,
                        "session_id": "test",
                        "total_cost_usd": 0.001,
                    }

                mock_transport.read_messages = mock_receive

                async with ClaudeSDKClient() as client:
                    # Test list comprehension pattern from docstring
                    messages = [msg async for msg in client.receive_response()]

                    assert len(messages) == 3
                    assert all(
                        isinstance(msg, AssistantMessage | ResultMessage)
                        for msg in messages
                    )
                    assert isinstance(messages[-1], ResultMessage)

        anyio.run(_test)


=== File: tests/test_subprocess_buffering.py ===
"""Tests for subprocess transport buffering edge cases."""

import json
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import anyio
import pytest

from claude_agent_sdk._errors import CLIJSONDecodeError
from claude_agent_sdk._internal.transport.subprocess_cli import (
    _DEFAULT_MAX_BUFFER_SIZE,
    SubprocessCLITransport,
)
from claude_agent_sdk.types import ClaudeAgentOptions


class MockTextReceiveStream:
    """Mock TextReceiveStream for testing."""

    def __init__(self, lines: list[str]) -> None:
        self.lines = lines
        self.index = 0

    def __aiter__(self) -> AsyncIterator[str]:
        return self

    async def __anext__(self) -> str:
        if self.index >= len(self.lines):
            raise StopAsyncIteration
        line = self.lines[self.index]
        self.index += 1
        return line


class TestSubprocessBuffering:
    """Test subprocess transport handling of buffered output."""

    def test_multiple_json_objects_on_single_line(self) -> None:
        """Test parsing when multiple JSON objects are concatenated on a single line.

        In some environments, stdout buffering can cause multiple distinct JSON
        objects to be delivered as a single line with embedded newlines.
        """

        async def _test() -> None:
            json_obj1 = {"type": "message", "id": "msg1", "content": "First message"}
            json_obj2 = {"type": "result", "id": "res1", "status": "completed"}

            buffered_line = json.dumps(json_obj1) + "\n" + json.dumps(json_obj2)

            transport = SubprocessCLITransport(
                prompt="test", options=ClaudeAgentOptions(), cli_path="/usr/bin/claude"
            )

            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock(return_value=None)
            transport._process = mock_process

            transport._stdout_stream = MockTextReceiveStream([buffered_line])  # type: ignore[assignment]
            transport._stderr_stream = MockTextReceiveStream([])  # type: ignore[assignment]

            messages: list[Any] = []
            async for msg in transport.read_messages():
                messages.append(msg)

            assert len(messages) == 2
            assert messages[0]["type"] == "message"
            assert messages[0]["id"] == "msg1"
            assert messages[0]["content"] == "First message"
            assert messages[1]["type"] == "result"
            assert messages[1]["id"] == "res1"
            assert messages[1]["status"] == "completed"

        anyio.run(_test)

    def test_json_with_embedded_newlines(self) -> None:
        """Test parsing JSON objects that contain newline characters in string values."""

        async def _test() -> None:
            json_obj1 = {"type": "message", "content": "Line 1\nLine 2\nLine 3"}
            json_obj2 = {"type": "result", "data": "Some\nMultiline\nContent"}

            buffered_line = json.dumps(json_obj1) + "\n" + json.dumps(json_obj2)

            transport = SubprocessCLITransport(
                prompt="test", options=ClaudeAgentOptions(), cli_path="/usr/bin/claude"
            )

            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock(return_value=None)
            transport._process = mock_process
            transport._stdout_stream = MockTextReceiveStream([buffered_line])
            transport._stderr_stream = MockTextReceiveStream([])

            messages: list[Any] = []
            async for msg in transport.read_messages():
                messages.append(msg)

            assert len(messages) == 2
            assert messages[0]["content"] == "Line 1\nLine 2\nLine 3"
            assert messages[1]["data"] == "Some\nMultiline\nContent"

        anyio.run(_test)

    def test_multiple_newlines_between_objects(self) -> None:
        """Test parsing with multiple newlines between JSON objects."""

        async def _test() -> None:
            json_obj1 = {"type": "message", "id": "msg1"}
            json_obj2 = {"type": "result", "id": "res1"}

            buffered_line = json.dumps(json_obj1) + "\n\n\n" + json.dumps(json_obj2)

            transport = SubprocessCLITransport(
                prompt="test", options=ClaudeAgentOptions(), cli_path="/usr/bin/claude"
            )

            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock(return_value=None)
            transport._process = mock_process
            transport._stdout_stream = MockTextReceiveStream([buffered_line])
            transport._stderr_stream = MockTextReceiveStream([])

            messages: list[Any] = []
            async for msg in transport.read_messages():
                messages.append(msg)

            assert len(messages) == 2
            assert messages[0]["id"] == "msg1"
            assert messages[1]["id"] == "res1"

        anyio.run(_test)

    def test_split_json_across_multiple_reads(self) -> None:
        """Test parsing when a single JSON object is split across multiple stream reads."""

        async def _test() -> None:
            json_obj = {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "text", "text": "x" * 1000},
                        {
                            "type": "tool_use",
                            "id": "tool_123",
                            "name": "Read",
                            "input": {"file_path": "/test.txt"},
                        },
                    ]
                },
            }

            complete_json = json.dumps(json_obj)

            part1 = complete_json[:100]
            part2 = complete_json[100:250]
            part3 = complete_json[250:]

            transport = SubprocessCLITransport(
                prompt="test", options=ClaudeAgentOptions(), cli_path="/usr/bin/claude"
            )

            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock(return_value=None)
            transport._process = mock_process
            transport._stdout_stream = MockTextReceiveStream([part1, part2, part3])
            transport._stderr_stream = MockTextReceiveStream([])

            messages: list[Any] = []
            async for msg in transport.read_messages():
                messages.append(msg)

            assert len(messages) == 1
            assert messages[0]["type"] == "assistant"
            assert len(messages[0]["message"]["content"]) == 2

        anyio.run(_test)

    def test_large_minified_json(self) -> None:
        """Test parsing a large minified JSON (simulating the reported issue)."""

        async def _test() -> None:
            large_data = {"data": [{"id": i, "value": "x" * 100} for i in range(1000)]}
            json_obj = {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "tool_use_id": "toolu_016fed1NhiaMLqnEvrj5NUaj",
                            "type": "tool_result",
                            "content": json.dumps(large_data),
                        }
                    ],
                },
            }

            complete_json = json.dumps(json_obj)

            chunk_size = 64 * 1024
            chunks = [
                complete_json[i : i + chunk_size]
                for i in range(0, len(complete_json), chunk_size)
            ]

            transport = SubprocessCLITransport(
                prompt="test", options=ClaudeAgentOptions(), cli_path="/usr/bin/claude"
            )

            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock(return_value=None)
            transport._process = mock_process
            transport._stdout_stream = MockTextReceiveStream(chunks)
            transport._stderr_stream = MockTextReceiveStream([])

            messages: list[Any] = []
            async for msg in transport.read_messages():
                messages.append(msg)

            assert len(messages) == 1
            assert messages[0]["type"] == "user"
            assert (
                messages[0]["message"]["content"][0]["tool_use_id"]
                == "toolu_016fed1NhiaMLqnEvrj5NUaj"
            )

        anyio.run(_test)

    def test_buffer_size_exceeded(self) -> None:
        """Test that exceeding buffer size raises an appropriate error."""

        async def _test() -> None:
            huge_incomplete = '{"data": "' + "x" * (_DEFAULT_MAX_BUFFER_SIZE + 1000)

            transport = SubprocessCLITransport(
                prompt="test", options=ClaudeAgentOptions(), cli_path="/usr/bin/claude"
            )

            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock(return_value=None)
            transport._process = mock_process
            transport._stdout_stream = MockTextReceiveStream([huge_incomplete])
            transport._stderr_stream = MockTextReceiveStream([])

            with pytest.raises(Exception) as exc_info:
                messages: list[Any] = []
                async for msg in transport.read_messages():
                    messages.append(msg)

            assert isinstance(exc_info.value, CLIJSONDecodeError)
            assert "exceeded maximum buffer size" in str(exc_info.value)

        anyio.run(_test)

    def test_buffer_size_option(self) -> None:
        """Test that the configurable buffer size option is respected."""

        async def _test() -> None:
            custom_limit = 512
            huge_incomplete = '{"data": "' + "x" * (custom_limit + 10)

            transport = SubprocessCLITransport(
                prompt="test",
                options=ClaudeAgentOptions(max_buffer_size=custom_limit),
                cli_path="/usr/bin/claude",
            )

            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock(return_value=None)
            transport._process = mock_process
            transport._stdout_stream = MockTextReceiveStream([huge_incomplete])
            transport._stderr_stream = MockTextReceiveStream([])

            with pytest.raises(CLIJSONDecodeError) as exc_info:
                async for _ in transport.read_messages():
                    pass

            assert f"maximum buffer size of {custom_limit} bytes" in str(exc_info.value)

        anyio.run(_test)

    def test_mixed_complete_and_split_json(self) -> None:
        """Test handling a mix of complete and split JSON messages."""

        async def _test() -> None:
            msg1 = json.dumps({"type": "system", "subtype": "start"})

            large_msg = {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "y" * 5000}]},
            }
            large_json = json.dumps(large_msg)

            msg3 = json.dumps({"type": "system", "subtype": "end"})

            lines = [
                msg1 + "\n",
                large_json[:1000],
                large_json[1000:3000],
                large_json[3000:] + "\n" + msg3,
            ]

            transport = SubprocessCLITransport(
                prompt="test", options=ClaudeAgentOptions(), cli_path="/usr/bin/claude"
            )

            mock_process = MagicMock()
            mock_process.returncode = None
            mock_process.wait = AsyncMock(return_value=None)
            transport._process = mock_process
            transport._stdout_stream = MockTextReceiveStream(lines)
            transport._stderr_stream = MockTextReceiveStream([])

            messages: list[Any] = []
            async for msg in transport.read_messages():
                messages.append(msg)

            assert len(messages) == 3
            assert messages[0]["type"] == "system"
            assert messages[0]["subtype"] == "start"
            assert messages[1]["type"] == "assistant"
            assert len(messages[1]["message"]["content"][0]["text"]) == 5000
            assert messages[2]["type"] == "system"
            assert messages[2]["subtype"] == "end"

        anyio.run(_test)


=== File: tests/test_transport.py ===
"""Tests for Claude SDK transport layer."""

import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import anyio
import pytest

from claude_agent_sdk._internal.transport.subprocess_cli import SubprocessCLITransport
from claude_agent_sdk.types import ClaudeAgentOptions


class TestSubprocessCLITransport:
    """Test subprocess transport implementation."""

    def test_find_cli_not_found(self):
        """Test CLI not found error."""
        from claude_agent_sdk._errors import CLINotFoundError

        with (
            patch("shutil.which", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
            pytest.raises(CLINotFoundError) as exc_info,
        ):
            SubprocessCLITransport(prompt="test", options=ClaudeAgentOptions())

        assert "Claude Code not found" in str(exc_info.value)

    def test_build_command_basic(self):
        """Test building basic CLI command."""
        transport = SubprocessCLITransport(
            prompt="Hello", options=ClaudeAgentOptions(), cli_path="/usr/bin/claude"
        )

        cmd = transport._build_command()
        assert cmd[0] == "/usr/bin/claude"
        assert "--output-format" in cmd
        assert "stream-json" in cmd
        assert "--print" in cmd
        assert "Hello" in cmd

    def test_cli_path_accepts_pathlib_path(self):
        """Test that cli_path accepts pathlib.Path objects."""
        from pathlib import Path

        path = Path("/usr/bin/claude")
        transport = SubprocessCLITransport(
            prompt="Hello",
            options=ClaudeAgentOptions(),
            cli_path=path,
        )

        # Path object is converted to string, compare with str(path)
        assert transport._cli_path == str(path)

    def test_build_command_with_system_prompt_string(self):
        """Test building CLI command with system prompt as string."""
        transport = SubprocessCLITransport(
            prompt="test",
            options=ClaudeAgentOptions(
                system_prompt="Be helpful",
            ),
            cli_path="/usr/bin/claude",
        )

        cmd = transport._build_command()
        assert "--system-prompt" in cmd
        assert "Be helpful" in cmd

    def test_build_command_with_system_prompt_preset(self):
        """Test building CLI command with system prompt preset."""
        transport = SubprocessCLITransport(
            prompt="test",
            options=ClaudeAgentOptions(
                system_prompt={"type": "preset", "preset": "claude_code"},
            ),
            cli_path="/usr/bin/claude",
        )

        cmd = transport._build_command()
        assert "--system-prompt" not in cmd
        assert "--append-system-prompt" not in cmd

    def test_build_command_with_system_prompt_preset_and_append(self):
        """Test building CLI command with system prompt preset and append."""
        transport = SubprocessCLITransport(
            prompt="test",
            options=ClaudeAgentOptions(
                system_prompt={
                    "type": "preset",
                    "preset": "claude_code",
                    "append": "Be concise.",
                },
            ),
            cli_path="/usr/bin/claude",
        )

        cmd = transport._build_command()
        assert "--system-prompt" not in cmd
        assert "--append-system-prompt" in cmd
        assert "Be concise." in cmd

    def test_build_command_with_options(self):
        """Test building CLI command with options."""
        transport = SubprocessCLITransport(
            prompt="test",
            options=ClaudeAgentOptions(
                allowed_tools=["Read", "Write"],
                disallowed_tools=["Bash"],
                model="claude-sonnet-4-5",
                permission_mode="acceptEdits",
                max_turns=5,
            ),
            cli_path="/usr/bin/claude",
        )

        cmd = transport._build_command()
        assert "--allowedTools" in cmd
        assert "Read,Write" in cmd
        assert "--disallowedTools" in cmd
        assert "Bash" in cmd
        assert "--model" in cmd
        assert "claude-sonnet-4-5" in cmd
        assert "--permission-mode" in cmd
        assert "acceptEdits" in cmd
        assert "--max-turns" in cmd
        assert "5" in cmd

    def test_build_command_with_add_dirs(self):
        """Test building CLI command with add_dirs option."""
        from pathlib import Path

        dir1 = "/path/to/dir1"
        dir2 = Path("/path/to/dir2")
        transport = SubprocessCLITransport(
            prompt="test",
            options=ClaudeAgentOptions(add_dirs=[dir1, dir2]),
            cli_path="/usr/bin/claude",
        )

        cmd = transport._build_command()

        # Check that both directories are in the command
        assert "--add-dir" in cmd
        add_dir_indices = [i for i, x in enumerate(cmd) if x == "--add-dir"]
        assert len(add_dir_indices) == 2

        # The directories should appear after --add-dir flags
        dirs_in_cmd = [cmd[i + 1] for i in add_dir_indices]
        assert dir1 in dirs_in_cmd
        assert str(dir2) in dirs_in_cmd

    def test_session_continuation(self):
        """Test session continuation options."""
        transport = SubprocessCLITransport(
            prompt="Continue from before",
            options=ClaudeAgentOptions(
                continue_conversation=True, resume="session-123"
            ),
            cli_path="/usr/bin/claude",
        )

        cmd = transport._build_command()
        assert "--continue" in cmd
        assert "--resume" in cmd
        assert "session-123" in cmd

    def test_connect_close(self):
        """Test connect and close lifecycle."""

        async def _test():
            with patch("anyio.open_process") as mock_exec:
                # Mock version check process
                mock_version_process = MagicMock()
                mock_version_process.stdout = MagicMock()
                mock_version_process.stdout.receive = AsyncMock(
                    return_value=b"2.0.0 (Claude Code)"
                )
                mock_version_process.terminate = MagicMock()
                mock_version_process.wait = AsyncMock()

                # Mock main process
                mock_process = MagicMock()
                mock_process.returncode = None
                mock_process.terminate = MagicMock()
                mock_process.wait = AsyncMock()
                mock_process.stdout = MagicMock()
                mock_process.stderr = MagicMock()

                # Mock stdin with aclose method
                mock_stdin = MagicMock()
                mock_stdin.aclose = AsyncMock()
                mock_process.stdin = mock_stdin

                # Return version process first, then main process
                mock_exec.side_effect = [mock_version_process, mock_process]

                transport = SubprocessCLITransport(
                    prompt="test",
                    options=ClaudeAgentOptions(),
                    cli_path="/usr/bin/claude",
                )

                await transport.connect()
                assert transport._process is not None
                assert transport.is_ready()

                await transport.close()
                mock_process.terminate.assert_called_once()

        anyio.run(_test)

    def test_read_messages(self):
        """Test reading messages from CLI output."""
        # This test is simplified to just test the transport creation
        # The full async stream handling is tested in integration tests
        transport = SubprocessCLITransport(
            prompt="test", options=ClaudeAgentOptions(), cli_path="/usr/bin/claude"
        )

        # The transport now just provides raw message reading via read_messages()
        # So we just verify the transport can be created and basic structure is correct
        assert transport._prompt == "test"
        assert transport._cli_path == "/usr/bin/claude"

    def test_connect_with_nonexistent_cwd(self):
        """Test that connect raises CLIConnectionError when cwd doesn't exist."""
        from claude_agent_sdk._errors import CLIConnectionError

        async def _test():
            transport = SubprocessCLITransport(
                prompt="test",
                options=ClaudeAgentOptions(cwd="/this/directory/does/not/exist"),
                cli_path="/usr/bin/claude",
            )

            with pytest.raises(CLIConnectionError) as exc_info:
                await transport.connect()

            assert "/this/directory/does/not/exist" in str(exc_info.value)

        anyio.run(_test)

    def test_build_command_with_settings_file(self):
        """Test building CLI command with settings as file path."""
        transport = SubprocessCLITransport(
            prompt="test",
            options=ClaudeAgentOptions(settings="/path/to/settings.json"),
            cli_path="/usr/bin/claude",
        )

        cmd = transport._build_command()
        assert "--settings" in cmd
        assert "/path/to/settings.json" in cmd

    def test_build_command_with_settings_json(self):
        """Test building CLI command with settings as JSON object."""
        settings_json = '{"permissions": {"allow": ["Bash(ls:*)"]}}'
        transport = SubprocessCLITransport(
            prompt="test",
            options=ClaudeAgentOptions(settings=settings_json),
            cli_path="/usr/bin/claude",
        )

        cmd = transport._build_command()
        assert "--settings" in cmd
        assert settings_json in cmd

    def test_build_command_with_extra_args(self):
        """Test building CLI command with extra_args for future flags."""
        transport = SubprocessCLITransport(
            prompt="test",
            options=ClaudeAgentOptions(
                extra_args={
                    "new-flag": "value",
                    "boolean-flag": None,
                    "another-option": "test-value",
                }
            ),
            cli_path="/usr/bin/claude",
        )

        cmd = transport._build_command()
        cmd_str = " ".join(cmd)

        # Check flags with values
        assert "--new-flag value" in cmd_str
        assert "--another-option test-value" in cmd_str

        # Check boolean flag (no value)
        assert "--boolean-flag" in cmd
        # Make sure boolean flag doesn't have a value after it
        boolean_idx = cmd.index("--boolean-flag")
        # Either it's the last element or the next element is another flag
        assert boolean_idx == len(cmd) - 1 or cmd[boolean_idx + 1].startswith("--")

    def test_build_command_with_mcp_servers(self):
        """Test building CLI command with mcp_servers option."""
        import json

        mcp_servers = {
            "test-server": {
                "type": "stdio",
                "command": "/path/to/server",
                "args": ["--option", "value"],
            }
        }

        transport = SubprocessCLITransport(
            prompt="test",
            options=ClaudeAgentOptions(mcp_servers=mcp_servers),
            cli_path="/usr/bin/claude",
        )

        cmd = transport._build_command()

        # Find the --mcp-config flag and its value
        assert "--mcp-config" in cmd
        mcp_idx = cmd.index("--mcp-config")
        mcp_config_value = cmd[mcp_idx + 1]

        # Parse the JSON and verify structure
        config = json.loads(mcp_config_value)
        assert "mcpServers" in config
        assert config["mcpServers"] == mcp_servers

    def test_build_command_with_mcp_servers_as_file_path(self):
        """Test building CLI command with mcp_servers as file path."""
        from pathlib import Path

        # Test with string path
        string_path = "/path/to/mcp-config.json"
        transport = SubprocessCLITransport(
            prompt="test",
            options=ClaudeAgentOptions(mcp_servers=string_path),
            cli_path="/usr/bin/claude",
        )

        cmd = transport._build_command()
        assert "--mcp-config" in cmd
        mcp_idx = cmd.index("--mcp-config")
        assert cmd[mcp_idx + 1] == string_path

        # Test with Path object
        path_obj = Path("/path/to/mcp-config.json")
        transport = SubprocessCLITransport(
            prompt="test",
            options=ClaudeAgentOptions(mcp_servers=path_obj),
            cli_path="/usr/bin/claude",
        )

        cmd = transport._build_command()
        assert "--mcp-config" in cmd
        mcp_idx = cmd.index("--mcp-config")
        # Path object gets converted to string, compare with str(path_obj)
        assert cmd[mcp_idx + 1] == str(path_obj)

    def test_build_command_with_mcp_servers_as_json_string(self):
        """Test building CLI command with mcp_servers as JSON string."""
        json_config = '{"mcpServers": {"server": {"type": "stdio", "command": "test"}}}'
        transport = SubprocessCLITransport(
            prompt="test",
            options=ClaudeAgentOptions(mcp_servers=json_config),
            cli_path="/usr/bin/claude",
        )

        cmd = transport._build_command()
        assert "--mcp-config" in cmd
        mcp_idx = cmd.index("--mcp-config")
        assert cmd[mcp_idx + 1] == json_config

    def test_env_vars_passed_to_subprocess(self):
        """Test that custom environment variables are passed to the subprocess."""

        async def _test():
            test_value = f"test-{uuid.uuid4().hex[:8]}"
            custom_env = {
                "MY_TEST_VAR": test_value,
            }

            options = ClaudeAgentOptions(env=custom_env)

            # Mock the subprocess to capture the env argument
            with patch(
                "anyio.open_process", new_callable=AsyncMock
            ) as mock_open_process:
                # Mock version check process
                mock_version_process = MagicMock()
                mock_version_process.stdout = MagicMock()
                mock_version_process.stdout.receive = AsyncMock(
                    return_value=b"2.0.0 (Claude Code)"
                )
                mock_version_process.terminate = MagicMock()
                mock_version_process.wait = AsyncMock()

                # Mock main process
                mock_process = MagicMock()
                mock_process.stdout = MagicMock()
                mock_stdin = MagicMock()
                mock_stdin.aclose = AsyncMock()  # Add async aclose method
                mock_process.stdin = mock_stdin
                mock_process.returncode = None

                # Return version process first, then main process
                mock_open_process.side_effect = [mock_version_process, mock_process]

                transport = SubprocessCLITransport(
                    prompt="test",
                    options=options,
                    cli_path="/usr/bin/claude",
                )

                await transport.connect()

                # Verify open_process was called twice (version check + main process)
                assert mock_open_process.call_count == 2

                # Check the second call (main process) for env vars
                second_call_kwargs = mock_open_process.call_args_list[1].kwargs
                assert "env" in second_call_kwargs
                env_passed = second_call_kwargs["env"]

                # Check that custom env var was passed
                assert env_passed["MY_TEST_VAR"] == test_value

                # Verify SDK identifier is present
                assert "CLAUDE_CODE_ENTRYPOINT" in env_passed
                assert env_passed["CLAUDE_CODE_ENTRYPOINT"] == "sdk-py"

                # Verify system env vars are also included with correct values
                if "PATH" in os.environ:
                    assert "PATH" in env_passed
                    assert env_passed["PATH"] == os.environ["PATH"]

        anyio.run(_test)

    def test_connect_as_different_user(self):
        """Test connect as different user."""

        async def _test():
            custom_user = "claude"
            options = ClaudeAgentOptions(user=custom_user)

            # Mock the subprocess to capture the env argument
            with patch(
                "anyio.open_process", new_callable=AsyncMock
            ) as mock_open_process:
                # Mock version check process
                mock_version_process = MagicMock()
                mock_version_process.stdout = MagicMock()
                mock_version_process.stdout.receive = AsyncMock(
                    return_value=b"2.0.0 (Claude Code)"
                )
                mock_version_process.terminate = MagicMock()
                mock_version_process.wait = AsyncMock()

                # Mock main process
                mock_process = MagicMock()
                mock_process.stdout = MagicMock()
                mock_stdin = MagicMock()
                mock_stdin.aclose = AsyncMock()  # Add async aclose method
                mock_process.stdin = mock_stdin
                mock_process.returncode = None

                # Return version process first, then main process
                mock_open_process.side_effect = [mock_version_process, mock_process]

                transport = SubprocessCLITransport(
                    prompt="test",
                    options=options,
                    cli_path="/usr/bin/claude",
                )

                await transport.connect()

                # Verify open_process was called twice (version check + main process)
                assert mock_open_process.call_count == 2

                # Check the second call (main process) for user
                second_call_kwargs = mock_open_process.call_args_list[1].kwargs
                assert "user" in second_call_kwargs
                user_passed = second_call_kwargs["user"]

                # Check that user was passed
                assert user_passed == "claude"

        anyio.run(_test)


=== File: tests/test_types.py ===
"""Tests for Claude SDK type definitions."""

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
)
from claude_agent_sdk.types import (
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)


class TestMessageTypes:
    """Test message type creation and validation."""

    def test_user_message_creation(self):
        """Test creating a UserMessage."""
        msg = UserMessage(content="Hello, Claude!")
        assert msg.content == "Hello, Claude!"

    def test_assistant_message_with_text(self):
        """Test creating an AssistantMessage with text content."""
        text_block = TextBlock(text="Hello, human!")
        msg = AssistantMessage(content=[text_block], model="claude-opus-4-1-20250805")
        assert len(msg.content) == 1
        assert msg.content[0].text == "Hello, human!"

    def test_assistant_message_with_thinking(self):
        """Test creating an AssistantMessage with thinking content."""
        thinking_block = ThinkingBlock(thinking="I'm thinking...", signature="sig-123")
        msg = AssistantMessage(
            content=[thinking_block], model="claude-opus-4-1-20250805"
        )
        assert len(msg.content) == 1
        assert msg.content[0].thinking == "I'm thinking..."
        assert msg.content[0].signature == "sig-123"

    def test_tool_use_block(self):
        """Test creating a ToolUseBlock."""
        block = ToolUseBlock(
            id="tool-123", name="Read", input={"file_path": "/test.txt"}
        )
        assert block.id == "tool-123"
        assert block.name == "Read"
        assert block.input["file_path"] == "/test.txt"

    def test_tool_result_block(self):
        """Test creating a ToolResultBlock."""
        block = ToolResultBlock(
            tool_use_id="tool-123", content="File contents here", is_error=False
        )
        assert block.tool_use_id == "tool-123"
        assert block.content == "File contents here"
        assert block.is_error is False

    def test_result_message(self):
        """Test creating a ResultMessage."""
        msg = ResultMessage(
            subtype="success",
            duration_ms=1500,
            duration_api_ms=1200,
            is_error=False,
            num_turns=1,
            session_id="session-123",
            total_cost_usd=0.01,
        )
        assert msg.subtype == "success"
        assert msg.total_cost_usd == 0.01
        assert msg.session_id == "session-123"


class TestOptions:
    """Test Options configuration."""

    def test_default_options(self):
        """Test Options with default values."""
        options = ClaudeAgentOptions()
        assert options.allowed_tools == []
        assert options.system_prompt is None
        assert options.permission_mode is None
        assert options.continue_conversation is False
        assert options.disallowed_tools == []

    def test_claude_code_options_with_tools(self):
        """Test Options with built-in tools."""
        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Write", "Edit"], disallowed_tools=["Bash"]
        )
        assert options.allowed_tools == ["Read", "Write", "Edit"]
        assert options.disallowed_tools == ["Bash"]

    def test_claude_code_options_with_permission_mode(self):
        """Test Options with permission mode."""
        options = ClaudeAgentOptions(permission_mode="bypassPermissions")
        assert options.permission_mode == "bypassPermissions"

        options_plan = ClaudeAgentOptions(permission_mode="plan")
        assert options_plan.permission_mode == "plan"

        options_default = ClaudeAgentOptions(permission_mode="default")
        assert options_default.permission_mode == "default"

        options_accept = ClaudeAgentOptions(permission_mode="acceptEdits")
        assert options_accept.permission_mode == "acceptEdits"

    def test_claude_code_options_with_system_prompt_string(self):
        """Test Options with system prompt as string."""
        options = ClaudeAgentOptions(
            system_prompt="You are a helpful assistant.",
        )
        assert options.system_prompt == "You are a helpful assistant."

    def test_claude_code_options_with_system_prompt_preset(self):
        """Test Options with system prompt preset."""
        options = ClaudeAgentOptions(
            system_prompt={"type": "preset", "preset": "claude_code"},
        )
        assert options.system_prompt == {"type": "preset", "preset": "claude_code"}

    def test_claude_code_options_with_system_prompt_preset_and_append(self):
        """Test Options with system prompt preset and append."""
        options = ClaudeAgentOptions(
            system_prompt={
                "type": "preset",
                "preset": "claude_code",
                "append": "Be concise.",
            },
        )
        assert options.system_prompt == {
            "type": "preset",
            "preset": "claude_code",
            "append": "Be concise.",
        }

    def test_claude_code_options_with_session_continuation(self):
        """Test Options with session continuation."""
        options = ClaudeAgentOptions(continue_conversation=True, resume="session-123")
        assert options.continue_conversation is True
        assert options.resume == "session-123"

    def test_claude_code_options_with_model_specification(self):
        """Test Options with model specification."""
        options = ClaudeAgentOptions(
            model="claude-sonnet-4-5", permission_prompt_tool_name="CustomTool"
        )
        assert options.model == "claude-sonnet-4-5"
        assert options.permission_prompt_tool_name == "CustomTool"

