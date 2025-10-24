#!/usr/bin/env python3
"""
Agent Context Bridge - Serialize conversation context for agent handoff.

Enables passing conversation context to agents spawned via 'codex exec' and
integrating their results back into the main session.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class AgentContextBridge:
    """Manages context serialization and agent result integration"""

    def __init__(self, project_root: Path | None = None):
        """Initialize the bridge

        Args:
            project_root: Project root directory (default: current directory)
        """
        self.project_root = project_root or Path.cwd()
        self.context_dir = self.project_root / ".codex"
        self.context_dir.mkdir(exist_ok=True)

        self.context_file = self.context_dir / "agent_context.json"
        self.results_dir = self.context_dir / "agent_results"
        self.results_dir.mkdir(exist_ok=True)

    def serialize_context(
        self,
        messages: list[dict[str, Any]],
        task: str,
        max_tokens: int = 4000,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """Serialize conversation context for agent handoff

        Args:
            messages: Conversation messages with role and content
            task: Current task description
            max_tokens: Maximum tokens to include in context
            metadata: Additional metadata to pass to agent

        Returns:
            Path to serialized context file
        """
        # Filter and compress messages to fit token budget
        compressed = self._compress_messages(messages, max_tokens)

        # Build context payload
        context = {
            "task": task,
            "messages": compressed,
            "metadata": metadata or {},
            "serialized_at": datetime.now().isoformat(),
            "message_count": len(messages),
            "compressed_count": len(compressed),
            "estimated_tokens": self._estimate_tokens(compressed),
        }

        # Save to file
        with open(self.context_file, "w") as f:
            json.dump(context, f, indent=2)

        return self.context_file

    def inject_context_to_agent(
        self,
        agent_name: str,
        task: str,
        messages: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Prepare context for agent invocation

        Args:
            agent_name: Name of agent to invoke
            task: Task for the agent
            messages: Conversation messages (optional)
            metadata: Additional metadata (optional)

        Returns:
            Dictionary with agent invocation details
        """
        context_path = None

        if messages:
            # Serialize context
            context_path = self.serialize_context(messages=messages, task=task, metadata=metadata)

        return {
            "agent_name": agent_name,
            "task": task,
            "context_file": str(context_path) if context_path else None,
            "timestamp": datetime.now().isoformat(),
        }

    def extract_agent_result(self, agent_output: str, agent_name: str) -> dict[str, Any]:
        """Extract and format agent result

        Args:
            agent_output: Raw output from agent execution
            agent_name: Name of the agent

        Returns:
            Formatted result dictionary
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.results_dir / f"{agent_name}_{timestamp}.md"

        # Save raw output
        with open(result_file, "w") as f:
            f.write(f"# Agent Result: {agent_name}\n\n")
            f.write(f"**Timestamp:** {datetime.now().isoformat()}\n\n")
            f.write("## Output\n\n")
            f.write(agent_output)

        # Parse output for structured data if possible
        result = {
            "agent_name": agent_name,
            "output": agent_output,
            "result_file": str(result_file),
            "timestamp": datetime.now().isoformat(),
            "success": "error" not in agent_output.lower(),  # Simple heuristic
        }

        return result

    def get_context_summary(self) -> dict[str, Any] | None:
        """Get summary of current context

        Returns:
            Context summary or None if no context exists
        """
        if not self.context_file.exists():
            return None

        with open(self.context_file) as f:
            context = json.load(f)

        return {
            "task": context.get("task", "Unknown"),
            "message_count": context.get("message_count", 0),
            "compressed_count": context.get("compressed_count", 0),
            "estimated_tokens": context.get("estimated_tokens", 0),
            "serialized_at": context.get("serialized_at", "Unknown"),
        }

    def cleanup(self):
        """Clean up context files"""
        if self.context_file.exists():
            self.context_file.unlink()

    def _compress_messages(self, messages: list[dict[str, Any]], max_tokens: int) -> list[dict[str, Any]]:
        """Compress messages to fit token budget

        Strategy:
        1. Keep most recent messages
        2. Summarize older messages
        3. Truncate if needed

        Args:
            messages: Original messages
            max_tokens: Maximum token budget

        Returns:
            Compressed message list
        """
        if not messages:
            return []

        # Simple compression: take most recent messages that fit budget
        compressed = []
        current_tokens = 0

        for msg in reversed(messages):
            msg_tokens = self._estimate_tokens([msg])

            if current_tokens + msg_tokens > max_tokens:
                # If we haven't included any messages yet, truncate this one
                if not compressed:
                    truncated = self._truncate_message(msg, max_tokens)
                    compressed.insert(0, truncated)
                break

            compressed.insert(0, msg)
            current_tokens += msg_tokens

        return compressed

    def _truncate_message(self, message: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        """Truncate a single message to fit token budget

        Args:
            message: Message to truncate
            max_tokens: Maximum tokens

        Returns:
            Truncated message
        """
        content = message.get("content", "")

        # Rough estimate: 4 chars per token
        max_chars = max_tokens * 4

        if len(content) <= max_chars:
            return message

        truncated = content[:max_chars] + "\n\n[...truncated...]"

        return {**message, "content": truncated}

    def _estimate_tokens(self, messages: list[dict[str, Any]]) -> int:
        """Estimate token count for messages

        Simple heuristic: ~4 characters per token

        Args:
            messages: Messages to estimate

        Returns:
            Estimated token count
        """
        total_chars = sum(len(str(msg.get("content", ""))) for msg in messages)

        return total_chars // 4


# CLI interface
def main():
    """CLI for testing context bridge"""
    import sys

    bridge = AgentContextBridge()

    if len(sys.argv) < 2:
        print("Usage: agent_context_bridge.py <command>")
        print("Commands:")
        print("  summary    - Show current context summary")
        print("  cleanup    - Clean up context files")
        sys.exit(1)

    command = sys.argv[1]

    if command == "summary":
        summary = bridge.get_context_summary()
        if summary:
            print(json.dumps(summary, indent=2))
        else:
            print("No context found")

    elif command == "cleanup":
        bridge.cleanup()
        print("Context cleaned up")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
