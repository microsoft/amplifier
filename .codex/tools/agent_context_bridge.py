#!/usr/bin/env python3
"""
Agent Context Bridge - Utility for serializing conversation context and integrating agent results.

This module provides functions to:
1. Serialize conversation context for agent handoff
2. Inject context into agent invocations
3. Extract and format agent results for display
4. Utilities for context management (token counting, compression)
"""

import json
import os
import sys
import gzip
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import argparse

# Add amplifier to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class AgentContextLogger:
    """Simple logger for agent context bridge operations"""

    def __init__(self):
        self.log_dir = Path(__file__).parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"agent_context_bridge_{today}.log"

    def _write(self, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted = f"[{timestamp}] [agent_context_bridge] [{level}] {message}"
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


logger = AgentContextLogger()


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text using tiktoken if available, otherwise approximate.
    
    Args:
        text: Text to count tokens for
        model: Model name for tiktoken encoding
        
    Returns:
        Approximate token count
    """
    if TIKTOKEN_AVAILABLE:
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Failed to use tiktoken: {e}, falling back to approximation")
    
    # Simple approximation: ~4 characters per token
    return len(text) // 4


def compress_context(context_data: Dict[str, Any]) -> bytes:
    """
    Compress context data using gzip.
    
    Args:
        context_data: Dictionary to compress
        
    Returns:
        Compressed bytes
    """
    json_str = json.dumps(context_data, indent=2)
    return gzip.compress(json_str.encode('utf-8'))


def decompress_context(compressed_data: bytes) -> Dict[str, Any]:
    """
    Decompress context data from gzip.
    
    Args:
        compressed_data: Compressed bytes
        
    Returns:
        Decompressed dictionary
    """
    json_str = gzip.decompress(compressed_data).decode('utf-8')
    return json.loads(json_str)


def serialize_context(
    messages: List[Dict[str, Any]], 
    max_tokens: int = 4000,
    current_task: Optional[str] = None,
    relevant_files: Optional[List[str]] = None,
    session_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Serialize conversation context to a compact format for agent handoff.
    
    Args:
        messages: List of conversation messages
        max_tokens: Maximum tokens to include
        current_task: Current task description
        relevant_files: List of relevant file paths
        session_metadata: Additional session metadata
        
    Returns:
        Path to the saved context file
    """
    try:
        logger.info(f"Serializing context with max_tokens={max_tokens}")
        
        # Filter and truncate messages to fit within token limit
        serialized_messages = []
        total_tokens = 0
        
        # Reserve tokens for metadata
        metadata_tokens = 500
        available_tokens = max_tokens - metadata_tokens
        
        # Process messages in reverse order (most recent first)
        for msg in reversed(messages):
            msg_text = msg.get('content', '')
            msg_tokens = count_tokens(msg_text)
            
            if total_tokens + msg_tokens > available_tokens:
                # Truncate message if it would exceed limit
                remaining_tokens = available_tokens - total_tokens
                if remaining_tokens > 100:  # Minimum useful message length
                    chars_per_token = len(msg_text) // msg_tokens if msg_tokens > 0 else 4
                    max_chars = remaining_tokens * chars_per_token
                    msg_text = msg_text[:max_chars] + "..."
                    serialized_messages.insert(0, {
                        'role': msg.get('role', 'unknown'),
                        'content': msg_text,
                        'truncated': True
                    })
                    total_tokens += count_tokens(msg_text)
                break
            else:
                serialized_messages.insert(0, {
                    'role': msg.get('role', 'unknown'),
                    'content': msg_text,
                    'truncated': False
                })
                total_tokens += msg_tokens
        
        # Build context data
        context_data = {
            'messages': serialized_messages,
            'total_messages': len(messages),
            'included_messages': len(serialized_messages),
            'total_tokens': total_tokens,
            'max_tokens': max_tokens,
            'timestamp': datetime.now().isoformat(),
            'current_task': current_task,
            'relevant_files': relevant_files or [],
            'session_metadata': session_metadata or {},
            'compression': 'none'  # Will be updated if compressed
        }
        
        # Check if compression is needed
        json_size = len(json.dumps(context_data, indent=2))
        if json_size > 100000:  # Compress if over 100KB
            logger.info("Compressing large context data")
            compressed = compress_context(context_data)
            context_data = {
                'compressed': True,
                'data': compressed.hex(),
                'original_size': json_size,
                'compressed_size': len(compressed)
            }
        
        # Save to file
        context_file = Path('.codex/agent_context.json')
        context_file.parent.mkdir(exist_ok=True)
        
        with open(context_file, 'w') as f:
            json.dump(context_data, f, indent=2)
        
        logger.info(f"Saved context to {context_file} ({len(serialized_messages)} messages, {total_tokens} tokens)")
        return str(context_file)
        
    except Exception as e:
        logger.exception("Error serializing context", e)
        raise


def inject_context_to_agent(
    agent_name: str, 
    task: str, 
    context_file: str
) -> Dict[str, Any]:
    """
    Prepare context injection for agent invocation.
    
    Args:
        agent_name: Name of the agent
        task: Task description
        context_file: Path to context file
        
    Returns:
        Dictionary with injection metadata
    """
    try:
        logger.info(f"Injecting context for agent {agent_name}")
        
        if not Path(context_file).exists():
            raise FileNotFoundError(f"Context file not found: {context_file}")
        
        # Load and validate context
        with open(context_file, 'r') as f:
            context_data = json.load(f)
        
        # Generate injection metadata
        injection_data = {
            'agent_name': agent_name,
            'task': task,
            'context_file': context_file,
            'context_size': Path(context_file).stat().st_size,
            'timestamp': datetime.now().isoformat(),
            'context_hash': hashlib.md5(json.dumps(context_data, sort_keys=True).encode()).hexdigest()
        }
        
        # For Codex, this would be used to modify the command
        # The actual command modification happens in agent_backend.py
        
        logger.info(f"Prepared context injection for {agent_name}")
        return injection_data
        
    except Exception as e:
        logger.exception(f"Error injecting context for agent {agent_name}", e)
        raise


def extract_agent_result(agent_output: str, agent_name: str) -> Dict[str, Any]:
    """
    Extract and format agent result from output.
    
    Args:
        agent_output: Raw agent output string
        agent_name: Name of the agent
        
    Returns:
        Dictionary with formatted result and metadata
    """
    try:
        logger.info(f"Extracting result from agent {agent_name}")
        
        # Parse agent output (assuming JSON format from codex exec --output-format=json)
        try:
            result_data = json.loads(agent_output)
        except json.JSONDecodeError:
            # Fallback: treat as plain text
            result_data = {'output': agent_output}
        
        # Format for display
        formatted_result = f"**Agent {agent_name} Result:**\n\n"
        
        if 'success' in result_data and result_data['success']:
            formatted_result += "✅ **Success**\n\n"
            if 'result' in result_data:
                formatted_result += f"**Output:**\n{result_data['result']}\n\n"
        else:
            formatted_result += "❌ **Failed**\n\n"
            if 'error' in result_data:
                formatted_result += f"**Error:** {result_data['error']}\n\n"
        
        # Add metadata
        if 'metadata' in result_data:
            metadata = result_data['metadata']
            formatted_result += "**Metadata:**\n"
            for key, value in metadata.items():
                formatted_result += f"- {key}: {value}\n"
            formatted_result += "\n"
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = Path('.codex/agent_results')
        result_dir.mkdir(exist_ok=True)
        result_file = result_dir / f"{agent_name}_{timestamp}.md"
        
        with open(result_file, 'w') as f:
            f.write(formatted_result)
        
        logger.info(f"Saved agent result to {result_file}")
        
        return {
            'formatted_result': formatted_result,
            'result_file': str(result_file),
            'raw_data': result_data,
            'timestamp': timestamp
        }
        
    except Exception as e:
        logger.exception(f"Error extracting result from agent {agent_name}", e)
        # Return basic error result
        error_result = f"**Agent {agent_name} Error:**\n\n❌ Failed to process agent output: {str(e)}\n\n**Raw Output:**\n{agent_output}"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_dir = Path('.codex/agent_results')
        result_dir.mkdir(exist_ok=True)
        result_file = result_dir / f"{agent_name}_{timestamp}_error.md"
        
        with open(result_file, 'w') as f:
            f.write(error_result)
        
        return {
            'formatted_result': error_result,
            'result_file': str(result_file),
            'error': str(e),
            'timestamp': timestamp
        }


def cleanup_context_files():
    """Clean up old context files."""
    try:
        context_dir = Path('.codex')
        context_file = context_dir / 'agent_context.json'
        
        if context_file.exists():
            # Remove context file
            context_file.unlink()
            logger.info("Cleaned up agent context file")
        
        # Clean up old result files (keep last 10)
        result_dir = context_dir / 'agent_results'
        if result_dir.exists():
            result_files = sorted(result_dir.glob('*.md'), key=lambda f: f.stat().st_mtime, reverse=True)
            if len(result_files) > 10:
                for old_file in result_files[10:]:
                    old_file.unlink()
                    logger.info(f"Cleaned up old result file: {old_file.name}")
                    
    except Exception as e:
        logger.exception("Error during context cleanup", e)


def main():
    """CLI interface for testing the bridge functions."""
    parser = argparse.ArgumentParser(description="Agent Context Bridge Utility")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Serialize command
    serialize_parser = subparsers.add_parser('serialize', help='Serialize context')
    serialize_parser.add_argument('--messages', required=True, help='JSON file with messages')
    serialize_parser.add_argument('--max-tokens', type=int, default=4000, help='Max tokens')
    serialize_parser.add_argument('--task', help='Current task')
    serialize_parser.add_argument('--files', nargs='*', help='Relevant files')
    
    # Inject command
    inject_parser = subparsers.add_parser('inject', help='Prepare context injection')
    inject_parser.add_argument('--agent', required=True, help='Agent name')
    inject_parser.add_argument('--task', required=True, help='Task description')
    inject_parser.add_argument('--context-file', required=True, help='Context file path')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract agent result')
    extract_parser.add_argument('--agent', required=True, help='Agent name')
    extract_parser.add_argument('--output', required=True, help='Agent output')
    
    # Cleanup command
    subparsers.add_parser('cleanup', help='Clean up context files')
    
    args = parser.parse_args()
    
    if args.command == 'serialize':
        with open(args.messages, 'r') as f:
            messages = json.load(f)
        result = serialize_context(messages, args.max_tokens, args.task, args.files)
        print(f"Context serialized to: {result}")
        
    elif args.command == 'inject':
        result = inject_context_to_agent(args.agent, args.task, args.context_file)
        print(json.dumps(result, indent=2))
        
    elif args.command == 'extract':
        result = extract_agent_result(args.output, args.agent)
        print(f"Result saved to: {result['result_file']}")
        
    elif args.command == 'cleanup':
        cleanup_context_files()
        print("Context files cleaned up")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()