"""
Backend abstraction for agent spawning operations.

This module provides a unified interface for spawning sub-agents across different
AI backends (Claude Code and Codex), abstracting away the differences between
Claude Code's Task tool and Codex's `codex exec` command.
"""

import abc
import asyncio
import inspect
import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# Import agent context bridge utilities
from amplifier.codex_tools import create_combined_context_file
from amplifier.codex_tools import extract_agent_result
from amplifier.codex_tools import serialize_context

# Optional Claude SDK symbols are defined lazily so tests can patch them
ClaudeSDKClient = None
ClaudeCodeOptions = None

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
    allowed_tools: list[str]
    max_turns: int = 10
    model: str | None = None


def _resolve_workspace_path(
    project_root: Path,
    workspace_dir: str,
    *subdirs: str,
    prefer_non_empty: bool = False,
) -> Path:
    """Resolve workspace-relative path, searching parent/home fallbacks when available.

    Args:
        project_root: Current working directory for the project
        workspace_dir: Hidden workspace directory name (e.g., ".claude")
        *subdirs: Nested subdirectories inside the workspace dir
        prefer_non_empty: When True, prefer directories that already contain files
    """
    subpath = Path(*subdirs) if subdirs else Path()
    search_roots = [project_root, project_root.parent]

    # Include home directory for user-level agents if workspace dir is hidden (e.g., ".claude")
    if workspace_dir.startswith("."):
        search_roots.append(Path.home())

    fallback: Path | None = None

    for root in search_roots:
        candidate = root / workspace_dir / subpath
        if candidate.exists():
            if not prefer_non_empty:
                return candidate
            if candidate.is_dir() and any(candidate.glob("*")):
                return candidate
            if fallback is None:
                fallback = candidate

    # Default to project root even if it doesn't exist yet
    return fallback or (project_root / workspace_dir / subpath)


def _extract_agent_metadata(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter (with flexible formatting) and body prompt."""
    stripped = content.lstrip()
    if not stripped:
        return {}, ""

    frontmatter_text = ""
    body_text = ""

    if stripped.startswith("---"):
        parts = stripped.split("---", 2)
        if len(parts) < 3:
            raise ValueError("Agent definition frontmatter is incomplete")
        frontmatter_text = parts[1]
        body_text = parts[2]
    else:
        parts = stripped.split("---", 1)
        if len(parts) == 2:
            frontmatter_text = parts[0]
            body_text = parts[1]
        else:
            # Treat entire file as YAML metadata if separator missing
            frontmatter_text = stripped
            body_text = ""

    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in agent definition: {exc}") from exc

    return frontmatter, body_text.strip()


def _parse_tools_field(frontmatter: dict[str, Any]) -> list[str]:
    """Normalize allowed tools declarations from multiple schema variants."""
    tools_value = frontmatter.get("tools") or frontmatter.get("allowed_tools") or frontmatter.get("allowed_tools_csv")

    if isinstance(tools_value, list):
        return [str(tool).strip() for tool in tools_value if str(tool).strip()]

    if isinstance(tools_value, str):
        cleaned = tools_value.strip().strip("[]")
        return [tool.strip() for tool in cleaned.split(",") if tool.strip()]

    return []


class AgentBackend(abc.ABC):
    """Abstract base class for agent spawning backends."""

    @abc.abstractmethod
    def spawn_agent(self, agent_name: str, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
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
    def list_available_agents(self) -> list[str]:
        """List names of available agent definitions."""
        pass

    @abc.abstractmethod
    def get_agent_definition(self, agent_name: str) -> str | None:
        """Get the raw agent definition content."""
        pass

    @abc.abstractmethod
    def validate_agent_exists(self, agent_name: str) -> bool:
        """Check if an agent definition exists."""
        pass


class ClaudeCodeAgentBackend(AgentBackend):
    """Agent backend for Claude Code using the SDK."""

    def __init__(self):
        self.project_root = Path.cwd()
        self.agents_dir = _resolve_workspace_path(self.project_root, ".claude", "agents", prefer_non_empty=True)
        self._sdk_client = None
        self._sdk_options = None

    def _ensure_sdk_available(self):
        """Ensure Claude Code SDK is available."""
        global ClaudeSDKClient, ClaudeCodeOptions

        if ClaudeSDKClient is not None and ClaudeCodeOptions is not None:
            return ClaudeSDKClient, ClaudeCodeOptions

        try:
            from claude_code_sdk import ClaudeCodeOptions as ImportedOptions
            from claude_code_sdk import ClaudeSDKClient as ImportedClient

            ClaudeSDKClient = ImportedClient
            ClaudeCodeOptions = ImportedOptions
            return ClaudeSDKClient, ClaudeCodeOptions
        except ImportError as e:
            raise AgentBackendError(f"Claude Code SDK not available: {e}")

    def _get_sdk_client(self):
        """Get or create SDK client."""
        if self._sdk_client is None:
            sdk_client_cls, sdk_options_cls = self._ensure_sdk_available()

            # Create options with Task tool enabled
            self._sdk_options = sdk_options_cls(allowed_tools=["Task", "Read", "Write", "Bash", "Grep", "Glob"])  # type: ignore[call-arg]

            self._sdk_client = sdk_client_cls(options=self._sdk_options)

        return self._sdk_client

    def spawn_agent(self, agent_name: str, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Spawn agent using Claude Code SDK Task tool."""
        import time

        start_time = time.time()

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
                context_str = json.dumps(context, separators=(", ", ": "))
                full_task += f"\n\nAdditional context:\n{context_str}"

            # Execute via SDK
            result = asyncio.run(self._execute_agent_task(client, full_task))

            execution_time = time.time() - start_time

            # Log analytics
            self._log_agent_execution(
                agent_name=agent_name,
                task=task,
                duration_seconds=execution_time,
                success=True,
                result_summary=result[:500] if result else None,  # Truncate for summary
                context_tokens=None,  # Claude SDK doesn't provide this
            )

            return {
                "success": True,
                "result": result,
                "metadata": {"backend": "claude", "agent_name": agent_name, "task_length": len(task)},
            }

        except AgentNotFoundError:
            raise
        except AgentTimeoutError:
            raise
        except Exception as e:
            execution_time = time.time() - start_time

            # Log failed execution
            self._log_agent_execution(
                agent_name=agent_name,
                task=task,
                duration_seconds=execution_time,
                success=False,
                error_message=str(e),
            )

            logger.error(f"Error spawning Claude Code agent {agent_name}: {e}")
            raise AgentSpawnError(f"Failed to spawn agent {agent_name}: {e}")

    def _log_agent_execution(
        self,
        agent_name: str,
        task: str,
        duration_seconds: float,
        success: bool,
        result_summary: str | None = None,
        context_tokens: int | None = None,
        error_message: str | None = None,
    ):
        """Log agent execution to analytics MCP server if available."""
        analytics_flag = os.getenv("AMPLIFIER_ENABLE_AGENT_ANALYTICS", "").strip().lower()
        if analytics_flag not in {"1", "true", "yes"}:
            return

        try:
            # Try to invoke the agent analytics MCP server
            import subprocess
            import sys

            # Escape single quotes in strings for shell safety
            safe_task = task.replace("'", "'\"'\"'")
            safe_result = result_summary.replace("'", "'\"'\"'") if result_summary else ""
            safe_error = error_message.replace("'", "'\"'\"'") if error_message else ""

            # Build the Python command
            python_cmd = f"""
import sys
sys.path.insert(0, '.')
from .codex.mcp_servers.agent_analytics.server import AgentAnalyticsServer
import asyncio

async def log_execution():
    server = AgentAnalyticsServer(None)  # MCP instance not needed for direct logging
    return await server.log_agent_execution(
        agent_name='{agent_name}',
        task='{safe_task}',
        duration_seconds={duration_seconds},
        success={str(success).lower()},
        result_summary={"None" if result_summary is None else f"'{safe_result}'"},
        context_tokens={context_tokens if context_tokens else "None"},
        error_message={"None" if error_message is None else f"'{safe_error}'"}
    )

result = asyncio.run(log_execution())
print('LOGGED' if result else 'FAILED')
"""

            cmd = [sys.executable, "-c", python_cmd]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and "LOGGED" in result.stdout:
                logger.debug(f"Successfully logged agent execution for {agent_name}")
            else:
                logger.debug(f"Failed to log agent execution: {result.stderr}")

        except Exception as e:
            logger.debug(f"Could not log agent execution to analytics: {e}")

    async def _execute_agent_task(self, client, task: str) -> str:
        """Execute agent task with timeout."""
        try:
            async with asyncio.timeout(300):  # 5 minute timeout
                # This is a simplified implementation - actual SDK usage would depend
                # on the specific ClaudeSDKClient API
                result = client.query(task)
                response = await result if inspect.isawaitable(result) else result
                return response.get("content", "")
        except TimeoutError:
            raise AgentTimeoutError("Agent execution timed out after 5 minutes")

    def _load_agent_definition(self, agent_name: str) -> AgentDefinition | None:
        """Load and parse agent definition."""
        agent_file = self.agents_dir / f"{agent_name}.md"
        if not agent_file.exists():
            return None

        try:
            content = agent_file.read_text()
            frontmatter, system_prompt_body = _extract_agent_metadata(content)

            system_prompt_text = frontmatter.get("system_prompt") or system_prompt_body

            return AgentDefinition(
                name=frontmatter.get("name", agent_name),
                description=frontmatter.get("description", ""),
                system_prompt=system_prompt_text,
                allowed_tools=_parse_tools_field(frontmatter),
                max_turns=frontmatter.get("max_turns", 10),
                model=frontmatter.get("model"),
            )
        except Exception as e:
            logger.error(f"Error parsing agent definition {agent_name}: {e}")
            return None

    def list_available_agents(self) -> list[str]:
        """List available Claude Code agents."""
        if not self.agents_dir.exists():
            return []

        agents = []
        for file_path in self.agents_dir.glob("*.md"):
            agents.append(file_path.stem)

        return sorted(agents)

    def get_agent_definition(self, agent_name: str) -> str | None:
        """Get raw agent definition content."""
        agent_file = self.agents_dir / f"{agent_name}.md"
        if agent_file.exists():
            return agent_file.read_text()
        return None

    def validate_agent_exists(self, agent_name: str) -> bool:
        """Check if Claude Code agent exists."""
        agent_file = self.agents_dir / f"{agent_name}.md"
        return agent_file.exists()

    def is_available(self) -> bool:
        """Return True if the Claude Code SDK is importable."""

        try:
            self._ensure_sdk_available()
            return True
        except AgentBackendError:
            return False


class CodexAgentBackend(AgentBackend):
    """Agent backend for Codex using subprocess."""

    def __init__(self):
        self.project_root = Path.cwd()
        self.agents_dir = _resolve_workspace_path(self.project_root, ".codex", "agents", prefer_non_empty=True)
        self.codex_cli = os.getenv("CODEX_CLI_PATH", "codex")
        self.profile = os.getenv("CODEX_PROFILE", "development")
        self.context_temp_dir = _resolve_workspace_path(self.project_root, ".codex", "agent_contexts")
        self.context_temp_dir.mkdir(parents=True, exist_ok=True)

    def spawn_agent(self, agent_name: str, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Spawn agent using Codex CLI."""
        import time

        start_time = time.time()

        serialized_context_file: Path | None = None
        combined_context_file: Path | None = None
        preserve_serialized = False
        preserve_combined = False
        keep_on_error = bool(os.getenv("CODEX_KEEP_CONTEXT_FILES_ON_ERROR"))
        try:
            logger.info(f"Spawning Codex agent: {agent_name}")

            if not self.validate_agent_exists(agent_name):
                raise AgentNotFoundError(f"Agent '{agent_name}' not found")

            cli_path = shutil.which(self.codex_cli)
            if cli_path is None:
                explicit_path = Path(self.codex_cli)
                if explicit_path.exists():
                    cli_path = str(explicit_path)

            if cli_path is None:
                raise AgentSpawnError(
                    "Codex CLI not found. Install the Codex CLI or set CODEX_CLI_PATH to the executable."
                )

            agent_definition = self._load_agent_definition_content(agent_name)
            context_payload, serialized_context_file = self._prepare_context_payload(task, context)

            combined_context_file = self._create_combined_context_file(
                agent_name=agent_name,
                agent_definition=agent_definition,
                task=task,
                context_payload=context_payload,
            )

            cmd = [cli_path, "exec", f"--context-file={combined_context_file}", task, "--agent", agent_name]
            logger.debug(f"Running command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=os.getcwd(),
            )

            execution_time = time.time() - start_time

            processed_result = self._process_codex_result(
                result=result,
                agent_name=agent_name,
                task=task,
                combined_context_file=combined_context_file,
                context_payload=context_payload,
            )

            # Log successful execution
            self._log_agent_execution(
                agent_name=agent_name,
                task=task,
                duration_seconds=execution_time,
                success=True,
                result_summary=processed_result.get("result", "")[:500] if processed_result.get("result") else None,
                context_tokens=context_payload.get("metadata", {}).get("token_count") if context_payload else None,
            )

            return processed_result

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            preserve_serialized = bool(serialized_context_file)
            preserve_combined = bool(combined_context_file)
            logger.warning(f"Agent {agent_name} timed out, preserving context files for debugging")
            if combined_context_file:
                logger.warning("Combined context preserved at: %s", combined_context_file)
            if serialized_context_file:
                logger.warning("Serialized context preserved at: %s", serialized_context_file)

            # Log timeout execution
            self._log_agent_execution(
                agent_name=agent_name,
                task=task,
                duration_seconds=execution_time,
                success=False,
                error_message="Execution timed out after 5 minutes",
            )

            raise AgentTimeoutError("Agent execution timed out after 5 minutes")
        except AgentNotFoundError:
            raise
        except Exception as e:
            execution_time = time.time() - start_time

            if keep_on_error:
                if combined_context_file:
                    preserve_combined = True
                    logger.warning(
                        "CODEX_KEEP_CONTEXT_FILES_ON_ERROR set; preserving combined context file at %s",
                        combined_context_file,
                    )
                if serialized_context_file:
                    preserve_serialized = True
                    logger.warning(
                        "CODEX_KEEP_CONTEXT_FILES_ON_ERROR set; preserving serialized context file at %s",
                        serialized_context_file,
                    )

            # Log failed execution
            self._log_agent_execution(
                agent_name=agent_name,
                task=task,
                duration_seconds=execution_time,
                success=False,
                error_message=str(e),
            )

            logger.error(f"Error spawning Codex agent {agent_name}: {e}")
            raise AgentSpawnError(f"Failed to spawn agent {agent_name}: {e}")
        finally:
            if not preserve_serialized:
                self._cleanup_temp_file(serialized_context_file)
            if not preserve_combined:
                self._cleanup_temp_file(combined_context_file)

    def spawn_agent_with_context(
        self, agent_name: str, task: str, messages: list[dict[str, Any]], context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Spawn agent with full conversation context.

        Args:
            agent_name: Name of the agent to spawn
            task: Task description for the agent
            messages: Full conversation messages for context
            context: Additional context metadata

        Returns:
            Dict with keys: success (bool), result (str), metadata (Dict)
        """
        logger.info(f"Spawning Codex agent with conversation context: {agent_name}")

        extended_context: dict[str, Any] = dict(context or {})
        extended_context["messages"] = messages

        return self.spawn_agent(agent_name=agent_name, task=task, context=extended_context)

    def _load_agent_definition_content(self, agent_name: str) -> str:
        agent_file = self.agents_dir / f"{agent_name}.md"
        if not agent_file.exists():
            raise AgentNotFoundError(f"Agent '{agent_name}' not found")
        return agent_file.read_text()

    def _prepare_context_payload(
        self, task: str, context: dict[str, Any] | None
    ) -> tuple[dict[str, Any] | None, Path | None]:
        if not context:
            return None, None

        messages = context.get("messages", [])
        try:
            if messages:
                serialized_path = serialize_context(
                    messages=messages,
                    max_tokens=4000,
                    current_task=task,
                    relevant_files=context.get("relevant_files"),
                    session_metadata=context.get("session_metadata"),
                )
                payload = self._load_json_file(serialized_path)
                payload.setdefault("metadata", {}).setdefault("extras", context)
                return payload, serialized_path

            logger.debug("No messages found in context; embedding raw context payload")
            return context, None
        except Exception as exc:
            logger.warning(f"Failed to serialize context: {exc}; embedding raw context")
            return context, None

    def _create_combined_context_file(
        self,
        agent_name: str,
        agent_definition: str,
        task: str,
        context_payload: dict[str, Any] | None,
    ) -> Path:
        combined_path = create_combined_context_file(
            agent_definition=agent_definition,
            task=task,
            context_data=context_payload,
            agent_name=agent_name,
        )
        logger.debug(f"Created combined context file: {combined_path}")
        return combined_path

    def _process_codex_result(
        self,
        result: subprocess.CompletedProcess[str],
        agent_name: str,
        task: str,
        combined_context_file: Path,
        context_payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        success = result.returncode == 0
        output = result.stdout.strip()
        if context_payload is not None:
            try:
                context_bytes = len(json.dumps(context_payload).encode("utf-8"))
            except (TypeError, ValueError) as exc:
                logger.warning(f"Failed to serialize context payload for metrics: {exc}")
                context_bytes = 0
        else:
            context_bytes = 0
        context_file_name = combined_context_file.name

        if success:
            try:
                extracted = extract_agent_result(output, agent_name)
                return {
                    "success": True,
                    "result": extracted.get("formatted_result", output),
                    "metadata": {
                        "backend": "codex",
                        "agent_name": agent_name,
                        "task_length": len(task),
                        "return_code": result.returncode,
                        "result_file": extracted.get("result_file"),
                        "context_bridge_used": True,
                        "invocation": "context-file",
                        "context_payload_bytes": context_bytes,
                        "context_file_name": context_file_name,
                        "profile": self.profile,
                    },
                }
            except Exception as exc:
                logger.warning(f"Failed to extract agent result with bridge: {exc}; using raw output")

        if success:
            return {
                "success": True,
                "result": output,
                "metadata": {
                    "backend": "codex",
                    "agent_name": agent_name,
                    "task_length": len(task),
                    "return_code": result.returncode,
                    "context_bridge_used": False,
                    "invocation": "context-file",
                    "context_payload_bytes": context_bytes,
                    "context_file_name": context_file_name,
                    "profile": self.profile,
                },
            }

        error_msg = result.stderr.strip() or output or "Unknown error"
        raise AgentSpawnError(f"Codex agent failed: {error_msg}")

    def _cleanup_temp_file(self, path: Path | None) -> None:
        if not path:
            return

        try:
            Path(path).unlink(missing_ok=True)
            logger.debug(f"Cleaned up temporary file: {path}")
        except Exception as exc:
            logger.warning(f"Failed to cleanup temporary file {path}: {exc}")

    @staticmethod
    def _load_json_file(path: Path) -> dict[str, Any]:
        try:
            with open(path) as handle:
                return json.load(handle)
        except Exception as exc:
            logger.warning(f"Failed to read serialized context from {path}: {exc}")
            return {}

    def list_available_agents(self) -> list[str]:
        """List available Codex agents."""
        if not self.agents_dir.exists():
            return []

        agents = []
        for file_path in self.agents_dir.glob("*.md"):
            agents.append(file_path.stem)

        return sorted(agents)

    def get_agent_definition(self, agent_name: str) -> str | None:
        """Get raw agent definition content."""
        agent_file = self.agents_dir / f"{agent_name}.md"
        if agent_file.exists():
            return agent_file.read_text()
        return None

    def validate_agent_exists(self, agent_name: str) -> bool:
        """Check if Codex agent exists."""
        agent_file = self.agents_dir / f"{agent_name}.md"
        return agent_file.exists()

    def is_available(self) -> bool:
        """Return True if the Codex CLI executable can be located."""

        cli_path = shutil.which(self.codex_cli)
        if cli_path:
            return True

        explicit_path = Path(self.codex_cli)
        return explicit_path.exists()

    def _log_agent_execution(
        self,
        agent_name: str,
        task: str,
        duration_seconds: float,
        success: bool,
        result_summary: str | None = None,
        context_tokens: int | None = None,
        error_message: str | None = None,
    ):
        """Log agent execution to analytics MCP server if available."""
        analytics_flag = os.getenv("AMPLIFIER_ENABLE_AGENT_ANALYTICS", "").strip().lower()
        if analytics_flag not in {"1", "true", "yes"}:
            return

        try:
            # Try to invoke the agent analytics MCP server
            import subprocess
            import sys

            # Escape single quotes in strings for shell safety
            safe_task = task.replace("'", "'\"'\"'")
            safe_result = result_summary.replace("'", "'\"'\"'") if result_summary else ""
            safe_error = error_message.replace("'", "'\"'\"'") if error_message else ""

            # Build the Python command
            python_cmd = f"""
import sys
sys.path.insert(0, '.')
from .codex.mcp_servers.agent_analytics.server import AgentAnalyticsServer
import asyncio

async def log_execution():
    server = AgentAnalyticsServer(None)  # MCP instance not needed for direct logging
    return await server.log_agent_execution(
        agent_name='{agent_name}',
        task='{safe_task}',
        duration_seconds={duration_seconds},
        success={str(success).lower()},
        result_summary={"None" if result_summary is None else f"'{safe_result}'"},
        context_tokens={context_tokens if context_tokens else "None"},
        error_message={"None" if error_message is None else f"'{safe_error}'"}
    )

result = asyncio.run(log_execution())
print('LOGGED' if result else 'FAILED')
"""

            cmd = [sys.executable, "-c", python_cmd]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and "LOGGED" in result.stdout:
                logger.debug(f"Successfully logged agent execution for {agent_name}")
            else:
                logger.debug(f"Failed to log agent execution: {result.stderr}")

        except Exception as e:
            logger.debug(f"Could not log agent execution to analytics: {e}")


class AgentBackendFactory:
    """Factory for creating agent backends."""

    @staticmethod
    def create_agent_backend(backend_type: str | None = None) -> AgentBackend:
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
        if backend_type == "codex":
            backend = CodexAgentBackend()
            if not backend.list_available_agents():
                logger.warning("No Codex agents found - backend may not be properly configured")
            return backend
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
        frontmatter, body = _extract_agent_metadata(content)

        system_prompt_text = frontmatter.get("system_prompt") or body

        return AgentDefinition(
            name=frontmatter.get("name", "unnamed"),
            description=frontmatter.get("description", ""),
            system_prompt=system_prompt_text,
            allowed_tools=_parse_tools_field(frontmatter),
            max_turns=frontmatter.get("max_turns", 10),
            model=frontmatter.get("model"),
        )

    except Exception as e:
        raise ValueError(f"Failed to parse agent definition: {e}")


def spawn_agent(agent_name: str, task: str, backend: str | None = None) -> dict[str, Any]:
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
        return {"success": False, "result": "", "metadata": {"error": str(e), "error_type": type(e).__name__}}


# Global convenience instance
_agent_backend = None


def get_agent_backend() -> AgentBackend:
    """Get the global agent backend instance."""
    global _agent_backend
    if _agent_backend is None:
        _agent_backend = AgentBackendFactory.get_agent_backend()
    return _agent_backend
