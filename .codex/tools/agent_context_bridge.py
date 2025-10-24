#!/usr/bin/env python3
"""
Agent Context Bridge - Utilities for serializing conversation context and integrating agent results.

This module provides functionality to:
- Serialize conversation context for agent handoff
- Inject context into agent invocations
- Extract and format agent results
- Manage context files and cleanup
"""

import json
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class ContextBridgeLogger:
    """Logger for agent context bridge operations"""

    def __init__(self):
        self.script_name = "agent_context_bridge"
        self.log_dir = Path(__file__).parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"{self.script_name}_{today}.log"

    def _write(self, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted = f"[{timestamp}] [{self.script_name}] [{level}] {message}"
        print(formatted, file=sys.stderr)
        try:
            with open(self.log_file, "a") as f:
                f.write(formatted + "\n")
        except Exception as e:
            print(f"Failed to write to log file: {e}", file=sys.stderr)

    def info(self, message: str):
        self._write("INFO", message)

    def debug(self, message: str):
        self._write("DEBUG", message)

    def error(self, message: str):
        self._write("ERROR", message)

    def warning(self, message: str):
        self._write("WARN", message)

    def exception(self, message: str, exc=None):
        import traceback
        if exc:
            self.error(f"{message}: {exc}")
            self.error(f"Traceback:\n{traceback.format_exc()}")
        else:
            self.error(message)
            self.error(f"Traceback:\n{traceback.format_exc()}")


logger = ContextBridgeLogger()


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text. Uses simple approximation since tiktoken may not be available.
    Rough estimate: ~4 characters per token for English text.
    """
    if not text:
        return 0
    # More accurate estimate: count words and adjust for punctuation
    words = len(text.split())
    # Add tokens for punctuation and subword units
    punctuation_tokens = len([c for c in text if c in '.,!?;:()[]{}"\'-'])
    return max(1, int(words * 1.3 + punctuation_tokens * 0.5))


def compress_context(messages: List[Dict[str, Any]], max_tokens: int) -> Tuple[List[Dict[str, Any]], int]:
    """
    Compress conversation messages to fit within token limit.

    Prioritizes recent messages and truncates older ones if needed.
    """
    if not messages:
        return [], 0

    compressed = []
    total_tokens = 0

    # Process messages in reverse order (most recent first)
    for msg in reversed(messages):
        content = msg.get("content", "")
        if not content:
            continue

        msg_tokens = estimate_tokens(content)

        # If this message alone exceeds limit, truncate it
        if msg_tokens > max_tokens and compressed:
            # Keep at least the first 100 chars
            truncated_content = content[:400] + "..." if len(content) > 400 else content
            truncated_tokens = estimate_tokens(truncated_content)
            compressed.insert(0, {**msg, "content": truncated_content})
            total_tokens += truncated_tokens
            break

        # Check if adding this message would exceed limit
        if total_tokens + msg_tokens > max_tokens:
            if not compressed:
                # If no messages yet, truncate this one
                truncated_content = content[:max_tokens * 4] + "..." if len(content) > max_tokens * 4 else content
                truncated_tokens = estimate_tokens(truncated_content)
                compressed.insert(0, {**msg, "content": truncated_content})
                total_tokens = truncated_tokens
            break

        # Add message
        compressed.insert(0, msg)
        total_tokens += msg_tokens

    logger.debug(f"Compressed {len(messages)} messages to {len(compressed)} with {total_tokens} tokens")
    return compressed, total_tokens


def serialize_context(
    messages: List[Dict[str, Any]],
    max_tokens: int = 4000,
    current_task: Optional[str] = None,
    relevant_files: Optional[List[str]] = None,
    session_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Serialize conversation context to a file for agent handoff.

    Args:
        messages: List of conversation messages
        max_tokens: Maximum token count for context
        current_task: Current task description
        relevant_files: List of relevant file paths
        session_metadata: Additional session metadata

    Returns:
        Path to the serialized context file
    """
    try:
        logger.info(f"Serializing context with {len(messages)} messages, max_tokens={max_tokens}")

        # Compress messages to fit token limit
        compressed_messages, actual_tokens = compress_context(messages, max_tokens)

        # Build context data
        context_data = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "current_task": current_task or "",
            "messages": compressed_messages,
            "relevant_files": relevant_files or [],
            "session_metadata": session_metadata or {},
            "token_count": actual_tokens,
            "compression_applied": len(compressed_messages) < len(messages)
        }

        # Create context directory
        context_dir = Path(".codex/agent_context")
        context_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        context_file = context_dir / f"context_{timestamp}.json"

        # Write context file
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(context_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Serialized context to {context_file} ({actual_tokens} tokens)")
        return str(context_file)

    except Exception as e:
        logger.exception("Failed to serialize context", e)
        raise


def inject_context_to_agent(agent_name: str, task: str, context_file: str) -> Dict[str, Any]:
    """
    Prepare context injection data for agent invocation.

    Args:
        agent_name: Name of the agent
        task: Task description
        context_file: Path to context file

    Returns:
        Dictionary with injection metadata
    """
    try:
        logger.info(f"Injecting context for agent {agent_name}")

        # Read context file to get metadata
        with open(context_file, 'r', encoding='utf-8') as f:
            context_data = json.load(f)

        # Calculate hash for integrity checking
        with open(context_file, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()[:16]

        injection_data = {
            "agent_name": agent_name,
            "task": task,
            "context_file": context_file,
            "context_size": context_data.get("token_count", 0),
            "context_hash": file_hash,
            "message_count": len(context_data.get("messages", [])),
            "timestamp": datetime.now().isoformat()
        }

        logger.debug(f"Context injection prepared: {injection_data}")
        return injection_data

    except Exception as e:
        logger.exception(f"Failed to inject context for agent {agent_name}", e)
        raise


def extract_agent_result(agent_output: str, agent_name: str) -> Dict[str, Any]:
    """
    Extract and format agent execution result.

    Args:
        agent_output: Raw output from agent execution
        agent_name: Name of the agent

    Returns:
        Dictionary with formatted result and metadata
    """
    try:
        logger.info(f"Extracting result for agent {agent_name}")

        # Try to parse as JSON first
        try:
            parsed_output = json.loads(agent_output.strip())
            formatted_result = parsed_output.get("result", agent_output)
            metadata = parsed_output.get("metadata", {})
        except json.JSONDecodeError:
            # Treat as plain text
            formatted_result = agent_output.strip()
            metadata = {}

        # Create result directory
        result_dir = Path(".codex/agent_results")
        result_dir.mkdir(parents=True, exist_ok=True)

        # Generate result filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = result_dir / f"{agent_name}_{timestamp}.md"

        # Format result content
        result_content = f"""# Agent Result: {agent_name}
**Timestamp:** {datetime.now().isoformat()}
**Task:** {metadata.get('task', 'Unknown')}

## Result
{formatted_result}

## Metadata
- **Agent:** {agent_name}
- **Execution Time:** {metadata.get('execution_time', 'Unknown')}
- **Success:** {metadata.get('success', 'Unknown')}
- **Context Used:** {metadata.get('context_used', False)}
"""

        # Write result file
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(result_content)

        logger.info(f"Extracted agent result to {result_file}")

        return {
            "formatted_result": formatted_result,
            "result_file": str(result_file),
            "metadata": metadata,
            "agent_name": agent_name,
            "timestamp": timestamp
        }

    except Exception as e:
        logger.exception(f"Failed to extract agent result for {agent_name}", e)
        # Return basic result on failure
        return {
            "formatted_result": agent_output.strip(),
            "result_file": None,
            "metadata": {},
            "agent_name": agent_name,
            "error": str(e)
        }


def cleanup_context_files(max_age_hours: int = 24, max_files: int = 50):
    """
    Clean up old context files to prevent disk space issues.

    Args:
        max_age_hours: Delete files older than this many hours
        max_files: Keep at most this many files
    """
    try:
        context_dir = Path(".codex/agent_context")
        if not context_dir.exists():
            return

        # Get all context files
        context_files = list(context_dir.glob("context_*.json"))
        if not context_files:
            return

        # Sort by modification time (newest first)
        context_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Delete old files
        deleted_count = 0
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)

        for file_path in context_files[max_files:]:
            # Also delete if too old
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                deleted_count += 1
                logger.debug(f"Deleted old context file: {file_path.name}")

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old context files")

    except Exception as e:
        logger.exception("Failed to cleanup context files", e)


# Initialize cleanup on import
cleanup_context_files()