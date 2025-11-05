#!/usr/bin/env python3
"""
Example script demonstrating CCSDK Toolkit usage.

This shows how to:
1. Use the core ClaudeSession for queries
2. Manage configuration with AgentConfig
3. Persist sessions with SessionManager
4. Use structured logging
5. Create CLI tools with CliBuilder
"""

import asyncio
from pathlib import Path

from amplifier.ccsdk_toolkit import AgentConfig  # Config
from amplifier.ccsdk_toolkit import ClaudeSession  # Core
from amplifier.ccsdk_toolkit import CliBuilder  # CLI
from amplifier.ccsdk_toolkit import ConfigLoader
from amplifier.ccsdk_toolkit import LogFormat
from amplifier.ccsdk_toolkit import LogLevel
from amplifier.ccsdk_toolkit import SDKNotAvailableError
from amplifier.ccsdk_toolkit import SessionManager  # Sessions
from amplifier.ccsdk_toolkit import SessionOptions
from amplifier.ccsdk_toolkit import ToolkitLogger  # Logger


async def basic_session_example():
    """Example 1: Basic session usage."""
    print("\n=== Example 1: Basic Session ===")

    try:
        # Create session with options
        options = SessionOptions(system_prompt="You are a helpful code assistant", max_turns=1)

        async with ClaudeSession(options) as session:
            response = await session.query("Write a Python hello world function")

            if response.success:
                print(f"Response:\n{response.content}")
            else:
                print(f"Error: {response.error}")

    except SDKNotAvailableError as e:
        print(f"SDK not available: {e}")


async def config_example():
    """Example 2: Configuration management."""
    print("\n=== Example 2: Configuration ===")

    # Create agent configuration
    agent_config = AgentConfig(
        name="code-reviewer",
        system_prompt="You are an expert code reviewer",
        allowed_tools=["read", "grep"],
        disallowed_tools=["write", "execute"],
        context_files=["README.md"],
        max_turns=3,
    )

    # Save configuration
    config_path = Path("/tmp/agent_config.json")
    ConfigLoader.save_config(agent_config, config_path)
    print(f"Saved config to {config_path}")

    # Load configuration
    loaded_config = ConfigLoader.load_agent_config(config_path)
    print(f"Loaded config: {loaded_config.name}")


async def session_persistence_example():
    """Example 3: Session persistence."""
    print("\n=== Example 3: Session Persistence ===")

    # Create session manager
    manager = SessionManager(session_dir=Path("/tmp/ccsdk_sessions"))

    # Create new session
    session_state = manager.create_session(name="example-session", tags=["demo", "test"])

    # Add messages
    session_state.add_message("user", "What is Python?")
    session_state.add_message("assistant", "Python is a programming language...")

    # Save session
    saved_path = manager.save_session(session_state)
    print(f"Saved session to {saved_path}")

    # Load session
    loaded = manager.load_session(session_state.metadata.session_id)
    if loaded:
        print(f"Loaded session: {loaded.metadata.name}")
        print(f"Messages: {len(loaded.messages)}")

    # List recent sessions
    recent = manager.list_sessions(days_back=1)
    print(f"Recent sessions: {len(recent)}")


def logging_example():
    """Example 4: Structured logging."""
    print("\n=== Example 4: Structured Logging ===")

    # Create logger with proper parameters
    logger = ToolkitLogger(name="example", level=LogLevel.DEBUG, format=LogFormat.PLAIN)

    # Log at different levels
    logger.debug("Debug message", component="test")
    logger.info("Processing started", items=100)
    logger.warning("Low memory", available_mb=500)
    logger.error("Failed to process", error=Exception("Operation failed"))

    # Stream progress
    logger.stream_progress("Analyzing main.py", progress=0.5)

    # Log tool use
    logger.log_tool_use("Read", {"file": "data.csv"}, result="Success")


def cli_builder_example():
    """Example 5: CLI tool creation."""
    print("\n=== Example 5: CLI Builder ===")

    # Create builder
    builder = CliBuilder(tools_dir=Path("/tmp/ccsdk_tools"))

    # List available templates
    templates = builder.list_templates()
    print(f"Available templates: {templates}")

    # Create a basic tool
    tool_path = builder.create_template(name="my_analyzer", description="Analyze code files", template_type="analyzer")
    print(f"Created tool: {tool_path}")

    # Get template description
    desc = builder.get_template_description("analyzer")
    print(f"Template description: {desc}")


async def integrated_example():
    """Example 6: Integrated usage with all components."""
    print("\n=== Example 6: Integrated Usage ===")

    # Set up logger
    logger = ToolkitLogger(name="integrated", level=LogLevel.INFO, format=LogFormat.PLAIN)

    # Load configuration
    config = AgentConfig(name="assistant", system_prompt="You are a helpful assistant", max_turns=1)

    # Create session manager
    manager = SessionManager()

    # Create new session
    session_state = manager.create_session(name="integrated-demo")
    logger.info("Created session", session_id=session_state.metadata.session_id)

    try:
        # Use Claude session
        options = SessionOptions(system_prompt=config.system_prompt, max_turns=config.max_turns)

        async with ClaudeSession(options) as claude:
            # Query Claude
            prompt = "What is the capital of France?"
            logger.info("Sending query", prompt=prompt)

            response = await claude.query(prompt)

            if response.success:
                # Add to session history
                session_state.add_message("user", prompt)
                session_state.add_message("assistant", response.content)

                # Save session
                manager.save_session(session_state)
                logger.info("Session saved", messages=len(session_state.messages))

                print(f"Q: {prompt}")
                print(f"A: {response.content}")
            else:
                logger.error("Query failed", error=Exception(response.error if response.error else "Unknown error"))

    except SDKNotAvailableError as e:
        logger.error("SDK not available", error=e)


async def main():
    """Run all examples."""
    print("CCSDK Toolkit Examples")
    print("=" * 50)

    # Run examples
    await basic_session_example()
    await config_example()
    await session_persistence_example()
    logging_example()
    cli_builder_example()
    await integrated_example()

    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
