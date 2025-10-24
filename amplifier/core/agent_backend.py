"""
Backend abstraction for agent spawning operations.

This module provides a unified interface for spawning sub-agents across different
AI backends (Claude Code and Codex), abstracting away the differences between
Claude Code's Task tool and Codex's `codex exec` command.
"""

import abc
import asyncio
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentBackendError(Exception):
    """Base exception for agent backend operations."""
    pass


class AgentNotFoundError(AgentBackendError):
    """Raised when an agent definition doesn't exist."""
    pass


class AgentSpawnError(AgentBackendError):
    """Raised when agent spawning fails."""
    pass


class AgentTimeoutError(AgentBackendError):
    """Raised when agent execution times out."""
    pass


@dataclass
class AgentDefinition:
    """Represents a parsed agent definition."""
    name: str
    description: str
    system_prompt: str
    allowed_tools: List[str]
    max_turns: int = 10
    model: Optional[str] = None


class AgentBackend(abc.ABC):
    """Abstract base class for agent spawning backends."""

    @abc.abstractmethod
    def spawn_agent(
        self,
        agent_name: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Spawn a sub-agent with the given task.

        Args:
            agent_name: Name of the agent to spawn
            task: Task description for the agent
            context: Optional context dictionary

        Returns:
            Dict with keys: success (bool), result (str), metadata (Dict)
        """
        pass

    @abc.abstractmethod
    def list_available_agents(self) -> List[str]:
        """List names of available agent definitions."""
        pass

    @abc.abstractmethod
    def get_agent_definition(self, agent_name: str) -> Optional[str]:
        """Get the raw agent definition content."""
        pass

    @abc.abstractmethod
    def validate_agent_exists(self, agent_name: str) -> bool:
        """Check if an agent definition exists."""
        pass


class ClaudeCodeAgentBackend(AgentBackend):
    """Agent backend for Claude Code using the SDK."""

    def __init__(self):
        self.agents_dir = Path(".claude/agents")
        self._sdk_client = None
        self._sdk_options = None

    def _ensure_sdk_available(self):
        """Ensure Claude Code SDK is available."""
        try:
            from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
            return ClaudeSDKClient, ClaudeCodeOptions
        except ImportError as e:
            raise AgentBackendError(f"Claude Code SDK not available: {e}")

    def _get_sdk_client(self):
        """Get or create SDK client."""
        if self._sdk_client is None:
            ClaudeSDKClient, ClaudeCodeOptions = self._ensure_sdk_available()

            # Create options with Task tool enabled
            self._sdk_options = ClaudeCodeOptions(
                allowed_tools=["Task", "Read", "Write", "Bash", "Grep", "Glob"],
                working_directory=os.getcwd()
            )

            self._sdk_client = ClaudeSDKClient(options=self._sdk_options)

        return self._sdk_client

    def spawn_agent(
        self,
        agent_name: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Spawn agent using Claude Code SDK Task tool."""
        try:
            logger.info(f"Spawning Claude Code agent: {agent_name}")

            if not self.validate_agent_exists(agent_name):
                raise AgentNotFoundError(f"Agent '{agent_name}' not found")

            # Get SDK client
            client = self._get_sdk_client()

            # Load agent definition
            definition = self._load_agent_definition(agent_name)
            if not definition:
                raise AgentNotFoundError(f"Could not load agent definition: {agent_name}")

            # Create task prompt that includes agent context
            full_task = f"Use the {agent_name} subagent to: {task}"
            if context:
                context_str = json.dumps(context, indent=2)
                full_task += f"\n\nAdditional context:\n{context_str}"

            # Execute via SDK
            result = asyncio.run(self._execute_agent_task(client, full_task))

            return {
                "success": True,
                "result": result,
                "metadata": {
                    "backend": "claude",
                    "agent_name": agent_name,
                    "task_length": len(task)
                }
            }

        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error spawning Claude Code agent {agent_name}: {e}")
            raise AgentSpawnError(f"Failed to spawn agent {agent_name}: {e}")

    async def _execute_agent_task(self, client, task: str) -> str:
        """Execute agent task with timeout."""
        try:
            async with asyncio.timeout(300):  # 5 minute timeout
                # This is a simplified implementation - actual SDK usage would depend
                # on the specific ClaudeSDKClient API
                response = await client.query(task)
                return response.get("content", "")
        except asyncio.TimeoutError:
            raise AgentTimeoutError("Agent execution timed out after 5 minutes")

    def _load_agent_definition(self, agent_name: str) -> Optional[AgentDefinition]:
        """Load and parse agent definition."""
        agent_file = self.agents_dir / f"{agent_name}.md"
        if not agent_file.exists():
            return None

        try:
            content = agent_file.read_text()

            # Parse YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    system_prompt = parts[2].strip()

                    return AgentDefinition(
                        name=frontmatter.get("name", agent_name),
                        description=frontmatter.get("description", ""),
                        system_prompt=system_prompt,
                        allowed_tools=frontmatter.get("tools", "").split(",") if frontmatter.get("tools") else [],
                        max_turns=frontmatter.get("max_turns", 10),
                        model=frontmatter.get("model")
                    )

            return None
        except Exception as e:
            logger.error(f"Error parsing agent definition {agent_name}: {e}")
            return None

    def list_available_agents(self) -> List[str]:
        """List available Claude Code agents."""
        if not self.agents_dir.exists():
            return []

        agents = []
        for file_path in self.agents_dir.glob("*.md"):
            agents.append(file_path.stem)

        return sorted(agents)

    def get_agent_definition(self, agent_name: str) -> Optional[str]:
        """Get raw agent definition content."""
        agent_file = self.agents_dir / f"{agent_name}.md"
        if agent_file.exists():
            return agent_file.read_text()
        return None

    def validate_agent_exists(self, agent_name: str) -> bool:
        """Check if Claude Code agent exists."""
        agent_file = self.agents_dir / f"{agent_name}.md"
        return agent_file.exists()


class CodexAgentBackend(AgentBackend):
    """Agent backend for Codex using subprocess."""

    def __init__(self):
        self.agents_dir = Path(".codex/agents")
        self.codex_cli = os.getenv("CODEX_CLI_PATH", "codex")
        self.profile = os.getenv("CODEX_PROFILE", "development")

    def spawn_agent(
        self,
        agent_name: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Spawn agent using Codex CLI."""
        try:
            logger.info(f"Spawning Codex agent: {agent_name}")

            if not self.validate_agent_exists(agent_name):
                raise AgentNotFoundError(f"Agent '{agent_name}' not found")

            # Build command
            agent_file = self.agents_dir / f"{agent_name}.md"
            cmd = [
                self.codex_cli,
                "exec",
                f"--context-file={agent_file}",
                f"--task={task}",
                f"--profile={self.profile}"
            ]

            # Add context if provided
            if context:
                context_json = json.dumps(context)
                cmd.extend(["--context-data", context_json])

            logger.debug(f"Running command: {' '.join(cmd)}")

            # Execute with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=os.getcwd()
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "result": result.stdout.strip(),
                    "metadata": {
                        "backend": "codex",
                        "agent_name": agent_name,
                        "task_length": len(task),
                        "return_code": result.returncode
                    }
                }
            else:
                error_msg = result.stderr.strip() or "Unknown error"
                raise AgentSpawnError(f"Codex agent failed: {error_msg}")

        except subprocess.TimeoutExpired:
            raise AgentTimeoutError("Agent execution timed out after 5 minutes")
        except AgentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error spawning Codex agent {agent_name}: {e}")
            raise AgentSpawnError(f"Failed to spawn agent {agent_name}: {e}")

    def list_available_agents(self) -> List[str]:
        """List available Codex agents."""
        if not self.agents_dir.exists():
            return []

        agents = []
        for file_path in self.agents_dir.glob("*.md"):
            agents.append(file_path.stem)

        return sorted(agents)

    def get_agent_definition(self, agent_name: str) -> Optional[str]:
        """Get raw agent definition content."""
        agent_file = self.agents_dir / f"{agent_name}.md"
        if agent_file.exists():
            return agent_file.read_text()
        return None

    def validate_agent_exists(self, agent_name: str) -> bool:
        """Check if Codex agent exists."""
        agent_file = self.agents_dir / f"{agent_name}.md"
        return agent_file.exists()


class AgentBackendFactory:
    """Factory for creating agent backends."""

    @staticmethod
    def create_agent_backend(backend_type: Optional[str] = None) -> AgentBackend:
        """
        Create an agent backend instance.

        Args:
            backend_type: "claude" or "codex", or None to use AMPLIFIER_BACKEND env var

        Returns:
            AgentBackend instance
        """
        if backend_type is None:
            backend_type = os.getenv("AMPLIFIER_BACKEND", "claude")

        backend_type = backend_type.lower()

        if backend_type == "claude":
            backend = ClaudeCodeAgentBackend()
            if not backend.list_available_agents():
                logger.warning("No Claude Code agents found - backend may not be properly configured")
            return backend
        elif backend_type == "codex":
            backend = CodexAgentBackend()
            if not backend.list_available_agents():
                logger.warning("No Codex agents found - backend may not be properly configured")
            return backend
        else:
            raise ValueError(f"Invalid backend type: {backend_type}. Must be 'claude' or 'codex'")

    @staticmethod
    def get_agent_backend() -> AgentBackend:
        """Convenience method to get the configured agent backend."""
        return AgentBackendFactory.create_agent_backend()


def parse_agent_definition(content: str) -> AgentDefinition:
    """
    Parse agent definition from markdown content.

    Args:
        content: Raw markdown content with YAML frontmatter

    Returns:
        Parsed AgentDefinition

    Raises:
        ValueError: If parsing fails
    """
    try:
        if not content.startswith("---"):
            raise ValueError("Agent definition must start with YAML frontmatter")

        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError("Invalid agent definition format")

        frontmatter = yaml.safe_load(parts[1])
        system_prompt = parts[2].strip()

        # Parse tools
        tools_str = frontmatter.get("tools", "")
        if isinstance(tools_str, str):
            allowed_tools = [t.strip() for t in tools_str.split(",") if t.strip()]
        elif isinstance(tools_str, list):
            allowed_tools = tools_str
        else:
            allowed_tools = []

        return AgentDefinition(
            name=frontmatter.get("name", "unnamed"),
            description=frontmatter.get("description", ""),
            system_prompt=system_prompt,
            allowed_tools=allowed_tools,
            max_turns=frontmatter.get("max_turns", 10),
            model=frontmatter.get("model")
        )

    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in agent definition: {e}")
    except Exception as e:
        raise ValueError(f"Failed to parse agent definition: {e}")


def spawn_agent(
    agent_name: str,
    task: str,
    backend: Optional[str] = None
) -> Dict[str, Any]:
    """
    High-level convenience function to spawn an agent.

    Args:
        agent_name: Name of the agent to spawn
        task: Task description
        backend: Backend type ("claude" or "codex"), or None for auto-detection

    Returns:
        Agent result dictionary
    """
    try:
        backend_instance = AgentBackendFactory.create_agent_backend(backend)
        return backend_instance.spawn_agent(agent_name, task)
    except Exception as e:
        logger.error(f"Error in spawn_agent convenience function: {e}")
        return {
            "success": False,
            "result": "",
            "metadata": {
                "error": str(e),
                "error_type": type(e).__name__
            }
        }


# Global convenience instance
_agent_backend = None

def get_agent_backend() -> AgentBackend:
    """Get the global agent backend instance."""
    global _agent_backend
    if _agent_backend is None:
        _agent_backend = AgentBackendFactory.get_agent_backend()
    return _agent_backend