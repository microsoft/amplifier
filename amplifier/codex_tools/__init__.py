"""Codex-specific tools and utilities for Amplifier."""

from pathlib import Path
from typing import Any

from .agent_context_bridge import AgentContextBridge

# Create singleton bridge instance
_BRIDGE = AgentContextBridge()


def serialize_context(
    messages: list[dict[str, Any]],
    max_tokens: int | None = None,
    current_task: str | None = None,
    relevant_files: list[str] | None = None,
    session_metadata: dict[str, Any] | None = None,
) -> Path:
    """
    Serialize conversation context for agent handoff.

    Args:
        messages: Conversation messages with role and content
        max_tokens: Maximum tokens to include in context (default: 4000)
        current_task: Current task description
        relevant_files: List of relevant file paths
        session_metadata: Additional session metadata

    Returns:
        Path to serialized context file
    """
    # Build task and metadata from provided arguments
    task = current_task or "No task specified"
    metadata = session_metadata or {}
    if relevant_files:
        metadata["relevant_files"] = relevant_files

    # Use provided max_tokens or default to 4000
    token_limit = max_tokens or 4000

    return _BRIDGE.serialize_context(messages=messages, task=task, max_tokens=token_limit, metadata=metadata)


def inject_context_to_agent(
    agent_name: str,
    task: str,
    context_file_or_messages: str | Path | list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Inject context to agent, accepting either a file path or messages list.

    Args:
        agent_name: Name of agent to invoke
        task: Task for the agent
        context_file_or_messages: Either a path to context file or messages list

    Returns:
        Dictionary with agent invocation details including context metadata
    """
    # If it's a file path (string or Path), return metadata with that path
    if isinstance(context_file_or_messages, str | Path):
        from datetime import datetime

        return {
            "agent_name": agent_name,
            "task": task,
            "context_file": str(context_file_or_messages),
            "timestamp": datetime.now().isoformat(),
        }

    # Otherwise treat as messages list and delegate to bridge
    return _BRIDGE.inject_context_to_agent(agent_name=agent_name, task=task, messages=context_file_or_messages)


def extract_agent_result(agent_output: str, agent_name: str) -> dict[str, Any]:
    """
    Extract and format agent result.

    Args:
        agent_output: Raw output from agent execution
        agent_name: Name of the agent

    Returns:
        Formatted result dictionary with keys: agent_name, output, result_file,
        timestamp, success, formatted_result
    """
    result = _BRIDGE.extract_agent_result(agent_output=agent_output, agent_name=agent_name)
    # Add formatted_result key for backward compatibility
    result["formatted_result"] = result["output"]
    return result


def cleanup_context_files():
    """Clean up context files created by the bridge."""
    _BRIDGE.cleanup()


def create_combined_context_file(
    agent_definition: str,
    task: str,
    context_data: dict[str, Any] | None = None,
    agent_name: str | None = None,
) -> Path:
    """Create combined markdown context file via shared bridge."""
    create_combined = getattr(_BRIDGE, "create_combined_context_file", None)
    if create_combined is None:
        msg = "AgentContextBridge missing create_combined_context_file implementation"
        raise AttributeError(msg)

    return create_combined(
        agent_definition=agent_definition,
        task=task,
        context_data=context_data,
        agent_name=agent_name,
    )


__all__ = [
    "serialize_context",
    "inject_context_to_agent",
    "extract_agent_result",
    "cleanup_context_files",
    "create_combined_context_file",
]
