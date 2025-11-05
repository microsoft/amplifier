import abc
import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

# Set up logging
logger = logging.getLogger(__name__)


class BackendNotAvailableError(Exception):
    """Raised when requested backend is not available."""

    pass


class BackendOperationError(Exception):
    """Raised when backend operation fails."""

    pass


class AmplifierBackend(abc.ABC):
    """Abstract base class for amplifier backends."""

    @abc.abstractmethod
    def initialize_session(self, prompt: str, context: str | None = None) -> dict[str, Any]:
        """
        Load memories at session start.

        Args:
            prompt: The initial prompt for the session.
            context: Optional additional context.

        Returns:
            Dict with success, data, and metadata.
        """
        pass

    @abc.abstractmethod
    def finalize_session(self, messages: list[dict[str, Any]], context: str | None = None) -> dict[str, Any]:
        """
        Extract and store memories at session end.

        Args:
            messages: List of conversation messages.
            context: Optional context.

        Returns:
            Dict with success, data, and metadata.
        """
        pass

    @abc.abstractmethod
    def run_quality_checks(self, file_paths: list[str], cwd: str | None = None) -> dict[str, Any]:
        """
        Run code quality checks.

        Args:
            file_paths: List of file paths to check.
            cwd: Optional working directory.

        Returns:
            Dict with success, data, and metadata.
        """
        pass

    @abc.abstractmethod
    def export_transcript(
        self, session_id: str | None = None, format: str = "standard", output_dir: str | None = None
    ) -> dict[str, Any]:
        """
        Export session transcript.

        Args:
            session_id: Optional session ID.
            format: Export format.
            output_dir: Optional output directory.

        Returns:
            Dict with success, data, and metadata.
        """
        pass

    @abc.abstractmethod
    def manage_tasks(self, action: str, **kwargs) -> dict[str, Any]:
        """
        Manage tasks.

        Args:
            action: The action to perform (create, list, update, complete, delete, export).
            **kwargs: Additional arguments for the action.

        Returns:
            Dict with success, data, and metadata.
        """
        pass

    @abc.abstractmethod
    def search_web(self, query: str, num_results: int = 5) -> dict[str, Any]:
        """
        Search the web.

        Args:
            query: Search query.
            num_results: Number of results to return.

        Returns:
            Dict with success, data, and metadata.
        """
        pass

    @abc.abstractmethod
    def fetch_url(self, url: str) -> dict[str, Any]:
        """
        Fetch content from URL.

        Args:
            url: URL to fetch.

        Returns:
            Dict with success, data, and metadata.
        """
        pass

    @abc.abstractmethod
    def spawn_agent_with_context(
        self, agent_name: str, task: str, messages: list[dict[str, Any]], context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Spawn agent with full conversation context.

        Args:
            agent_name: Name of the agent to spawn
            task: Task description
            messages: Full conversation messages
            context: Additional context metadata

        Returns:
            Dict with success, result, and metadata
        """
        pass

    @abc.abstractmethod
    def get_capabilities(self) -> dict[str, Any]:
        """Return backend capabilities."""
        pass

    @abc.abstractmethod
    def get_backend_name(self) -> str:
        """Return backend identifier."""
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available."""
        pass


class ClaudeCodeBackend(AmplifierBackend):
    """Claude Code backend implementation."""

    def get_backend_name(self) -> str:
        return "claude"

    def is_available(self) -> bool:
        # Check for .claude/ directory and Claude CLI
        claude_dir = Path(".claude")
        if not claude_dir.exists():
            return False
        try:
            subprocess.run(["claude", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def initialize_session(self, prompt: str, context: str | None = None) -> dict[str, Any]:
        try:
            memory_enabled = os.getenv("MEMORY_SYSTEM_ENABLED", "false").lower() in ["true", "1", "yes"]
            if not memory_enabled:
                return {"success": True, "data": {}, "metadata": {"memoriesLoaded": 0, "disabled": True}}

            from amplifier.memory import MemoryStore
            from amplifier.search import MemorySearcher

            store = MemoryStore()
            searcher = MemorySearcher()

            all_memories = store.get_all()
            search_results = searcher.search(prompt, all_memories, limit=5)
            recent = store.search_recent(limit=3)

            context_parts = []
            if search_results or recent:
                context_parts.append("## Relevant Context from Memory System\n")
                if search_results:
                    context_parts.append("### Relevant Memories")
                    for result in search_results[:3]:
                        content = result.memory.content
                        category = result.memory.category
                        score = result.score
                        context_parts.append(f"- **{category}** (relevance: {score:.2f}): {content}")
                seen_ids = {r.memory.id for r in search_results}
                unique_recent = [m for m in recent if m.id not in seen_ids]
                if unique_recent:
                    context_parts.append("\n### Recent Context")
                    for mem in unique_recent[:2]:
                        context_parts.append(f"- {mem.category}: {mem.content}")

            context_str = "\n".join(context_parts) if context_parts else ""
            memories_loaded = len(search_results) + len(unique_recent) if search_results else len(recent)

            return {
                "success": True,
                "data": {"additionalContext": context_str},
                "metadata": {"memoriesLoaded": memories_loaded, "source": "amplifier_memory"},
            }
        except Exception as e:
            logger.error(f"Claude initialize_session error: {e}")
            raise BackendOperationError(f"Session initialization failed: {e}")

    def finalize_session(self, messages: list[dict[str, Any]], context: str | None = None) -> dict[str, Any]:
        try:
            memory_enabled = os.getenv("MEMORY_SYSTEM_ENABLED", "false").lower() in ["true", "1", "yes"]
            if not memory_enabled:
                return {"success": True, "data": {}, "metadata": {"memoriesExtracted": 0, "disabled": True}}

            from amplifier.extraction import MemoryExtractor
            from amplifier.memory import MemoryStore

            async def extract():
                extractor = MemoryExtractor()
                store = MemoryStore()
                extracted = await extractor.extract_from_messages(messages, context)
                memories_count = 0
                if extracted and "memories" in extracted:
                    memories_list = extracted.get("memories", [])
                    store.add_memories_batch(extracted)
                    memories_count = len(memories_list)
                return memories_count

            memories_count = asyncio.run(asyncio.wait_for(extract(), timeout=60))
            return {
                "success": True,
                "data": {},
                "metadata": {"memoriesExtracted": memories_count, "source": "amplifier_extraction"},
            }
        except TimeoutError:
            logger.error("Claude finalize_session timeout")
            return {"success": False, "data": {}, "metadata": {"error": "timeout"}}
        except Exception as e:
            logger.error(f"Claude finalize_session error: {e}")
            raise BackendOperationError(f"Session finalization failed: {e}")

    def run_quality_checks(self, file_paths: list[str], cwd: str | None = None) -> dict[str, Any]:
        try:
            # Find project root
            start_dir = Path(cwd) if cwd else Path.cwd()
            project_root = None
            for dir_path in [start_dir] + list(start_dir.parents):
                if (
                    (dir_path / "Makefile").exists()
                    or (dir_path / ".git").exists()
                    or (dir_path / "pyproject.toml").exists()
                ):
                    project_root = dir_path
                    break
            if not project_root:
                return {"success": False, "data": {}, "metadata": {"error": "No project root found"}}

            # Check if Makefile has 'check' target
            makefile = project_root / "Makefile"
            if not makefile.exists():
                return {"success": False, "data": {}, "metadata": {"error": "No Makefile found"}}

            result = subprocess.run(["make", "-C", str(project_root), "-n", "check"], capture_output=True, text=True)
            if result.returncode != 0:
                return {"success": False, "data": {}, "metadata": {"error": "No 'check' target in Makefile"}}

            # Run make check
            result = subprocess.run(["make", "-C", str(project_root), "check"], capture_output=True, text=True)
            return {
                "success": result.returncode == 0,
                "data": {"output": result.stdout + result.stderr},
                "metadata": {"returncode": result.returncode},
            }
        except Exception as e:
            logger.error(f"Claude run_quality_checks error: {e}")
            raise BackendOperationError(f"Quality checks failed: {e}")

    def export_transcript(
        self, session_id: str | None = None, format: str = "standard", output_dir: str | None = None
    ) -> dict[str, Any]:
        try:
            # Use transcript_manager.py logic from hook_precompact.py
            # Simplified implementation
            storage_dir = Path(".data/transcripts")
            storage_dir.mkdir(parents=True, exist_ok=True)
            timestamp = "now"  # Placeholder
            output_filename = f"compact_{timestamp}_{session_id or 'unknown'}.txt"
            output_path = storage_dir / output_filename

            # Placeholder content
            output_path.write_text("Transcript content placeholder")

            return {
                "success": True,
                "data": {"path": str(output_path)},
                "metadata": {"format": format, "session_id": session_id},
            }
        except Exception as e:
            logger.error(f"Claude export_transcript error: {e}")
            raise BackendOperationError(f"Transcript export failed: {e}")

    def manage_tasks(self, action: str, **kwargs) -> dict[str, Any]:
        # Claude Code has built-in TodoWrite tool - feature not supported via backend API
        return {
            "success": False,
            "data": {},
            "metadata": {"unsupported": True, "native_tool": "TodoWrite", "action": action},
        }

    def search_web(self, query: str, num_results: int = 5) -> dict[str, Any]:
        # Claude Code has built-in WebSearch/WebFetch tool - feature not supported via backend API
        return {
            "success": False,
            "data": {},
            "metadata": {"unsupported": True, "native_tool": "WebSearch", "query": query, "num_results": num_results},
        }

    def fetch_url(self, url: str) -> dict[str, Any]:
        # Claude Code has built-in WebFetch tool - feature not supported via backend API
        return {
            "success": False,
            "data": {},
            "metadata": {"unsupported": True, "native_tool": "WebFetch", "url": url},
        }

    def spawn_agent_with_context(
        self, agent_name: str, task: str, messages: list[dict[str, Any]], context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Claude Code doesn't support context serialization via backend API."""
        # Return unsupported - Claude Code uses Task tool but doesn't expose context serialization
        return {
            "success": False,
            "data": {},
            "metadata": {"unsupported": True, "native_tool": "Task", "agent_name": agent_name, "task": task},
        }

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "task_management": False,  # Native TodoWrite tool, not via backend API
            "web_search": False,  # Native WebSearch tool, not via backend API
            "url_fetch": False,  # Native WebFetch tool, not via backend API
            "agent_spawning": False,  # Native Task tool, not via backend API
            "native_tools": True,  # Has native tools for these features
        }


class CodexBackend(AmplifierBackend):
    """Codex backend implementation."""

    def get_backend_name(self) -> str:
        return "codex"

    def is_available(self) -> bool:
        # Check for .codex/ directory and Codex CLI
        codex_dir = Path(".codex")
        if not codex_dir.exists():
            return False
        try:
            subprocess.run(["codex", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def initialize_session(self, prompt: str, context: str | None = None) -> dict[str, Any]:
        # Session metadata files are now separated by component to avoid conflicts:
        # - session_memory_init_metadata.json: Memory loading during session initialization
        # - session_memory_cleanup_metadata.json: Memory extraction during session finalization
        # - session_resume_metadata.json: Session resume operations
        try:
            memory_enabled = os.getenv("MEMORY_SYSTEM_ENABLED", "true").lower() in ["true", "1", "yes"]
            if not memory_enabled:
                context_file = Path(".codex/session_context.md")
                context_file.parent.mkdir(exist_ok=True)
                context_file.write_text("")
                metadata = {"memoriesLoaded": 0, "source": "disabled"}
                metadata_file = Path(".codex/session_memory_init_metadata.json")
                metadata_file.write_text(json.dumps(metadata))
                return {"success": True, "data": {"context": ""}, "metadata": metadata}

            from amplifier.memory import MemoryStore
            from amplifier.search import MemorySearcher

            store = MemoryStore()
            searcher = MemorySearcher()

            all_memories = store.get_all()
            search_results = searcher.search(prompt, all_memories, limit=5)
            recent = store.search_recent(limit=3)

            context_parts = []
            if search_results or recent:
                context_parts.append("## Relevant Context from Memory System\n")
                if search_results:
                    context_parts.append("### Relevant Memories")
                    for result in search_results[:3]:
                        content = result.memory.content
                        category = result.memory.category
                        score = result.score
                        context_parts.append(f"- **{category}** (relevance: {score:.2f}): {content}")
                seen_ids = {r.memory.id for r in search_results}
                unique_recent = [m for m in recent if m.id not in seen_ids]
                if unique_recent:
                    context_parts.append("\n### Recent Context")
                    for mem in unique_recent[:2]:
                        context_parts.append(f"- {mem.category}: {mem.content}")

            context_md = "\n".join(context_parts) if context_parts else ""
            context_file = Path(".codex/session_context.md")
            context_file.parent.mkdir(exist_ok=True)
            context_file.write_text(context_md)

            memories_loaded = len(search_results) + len(unique_recent) if search_results else len(recent)
            metadata = {
                "memoriesLoaded": memories_loaded,
                "relevantCount": len(search_results),
                "recentCount": memories_loaded - len(search_results),
                "source": "amplifier_memory",
                "contextFile": str(context_file),
            }
            metadata_file = Path(".codex/session_memory_init_metadata.json")
            metadata_file.write_text(json.dumps(metadata))

            return {
                "success": True,
                "data": {"context": context_md, "contextFile": str(context_file)},
                "metadata": metadata,
            }
        except Exception as e:
            logger.error(f"Codex initialize_session error: {e}")
            raise BackendOperationError(f"Session initialization failed: {e}")

    def finalize_session(self, messages: list[dict[str, Any]], context: str | None = None) -> dict[str, Any]:
        try:
            memory_enabled = os.getenv("MEMORY_SYSTEM_ENABLED", "true").lower() in ["true", "1", "yes"]
            if not memory_enabled:
                metadata = {"memoriesExtracted": 0, "source": "disabled"}
                metadata_file = Path(".codex/session_memory_cleanup_metadata.json")
                metadata_file.write_text(json.dumps(metadata))
                return {"success": True, "data": {}, "metadata": metadata}

            from amplifier.extraction import MemoryExtractor
            from amplifier.memory import MemoryStore

            async def extract():
                extractor = MemoryExtractor()
                store = MemoryStore()
                extracted = await extractor.extract_from_messages(messages, context)
                memories_count = 0
                if extracted and "memories" in extracted:
                    memories_list = extracted.get("memories", [])
                    store.add_memories_batch(extracted)
                    memories_count = len(memories_list)
                return memories_count

            memories_count = asyncio.run(asyncio.wait_for(extract(), timeout=60))

            # Export transcript
            transcript_path = None
            try:
                from ...codex.tools.transcript_exporter import CodexTranscriptExporter

                exporter = CodexTranscriptExporter()
                transcript_path = exporter.export_codex_transcript("session_id", Path(".codex/transcripts"))
            except Exception:
                pass

            metadata = {
                "memoriesExtracted": memories_count,
                "transcriptExported": transcript_path is not None,
                "transcriptPath": transcript_path,
                "source": "amplifier_cleanup",
            }
            metadata_file = Path(".codex/session_memory_cleanup_metadata.json")
            metadata_file.write_text(json.dumps(metadata))

            return {"success": True, "data": {"transcriptPath": transcript_path}, "metadata": metadata}
        except TimeoutError:
            logger.error("Codex finalize_session timeout")
            return {"success": False, "data": {}, "metadata": {"error": "timeout"}}
        except Exception as e:
            logger.error(f"Codex finalize_session error: {e}")
            raise BackendOperationError(f"Session finalization failed: {e}")

    def run_quality_checks(self, file_paths: list[str], cwd: str | None = None) -> dict[str, Any]:
        # Same as Claude
        return ClaudeCodeBackend().run_quality_checks(file_paths, cwd)

    def export_transcript(
        self, session_id: str | None = None, format: str = "standard", output_dir: str | None = None
    ) -> dict[str, Any]:
        try:
            from ...codex.tools.transcript_exporter import CodexTranscriptExporter

            exporter = CodexTranscriptExporter()
            output_dir = Path(output_dir) if output_dir else Path(".codex/transcripts")
            result = exporter.export_codex_transcript(session_id or "unknown", output_dir, format)
            return {
                "success": result is not None,
                "data": {"path": str(result)} if result else {},
                "metadata": {"format": format, "session_id": session_id},
            }
        except Exception as e:
            logger.error(f"Codex export_transcript error: {e}")
            raise BackendOperationError(f"Transcript export failed: {e}")

    def manage_tasks(self, action: str, **kwargs) -> dict[str, Any]:
        try:
            # Use MCP client to invoke task tracker tools via Codex CLI
            import sys

            codex_tools_path = Path(__file__).parent.parent.parent / ".codex" / "tools"
            sys.path.insert(0, str(codex_tools_path))

            try:
                from codex_mcp_client import CodexMCPClient

                client = CodexMCPClient(profile=os.getenv("CODEX_PROFILE", "development"))

                # Map action to tool name
                tool_map = {
                    "create": "create_task",
                    "list": "list_tasks",
                    "update": "update_task",
                    "complete": "complete_task",
                    "delete": "delete_task",
                    "export": "export_tasks",
                }

                tool_name = tool_map.get(action)
                if not tool_name:
                    return {"success": False, "data": {}, "metadata": {"error": f"Unknown action: {action}"}}

                # Call tool via MCP protocol
                result = client.call_tool("amplifier_tasks", tool_name, **kwargs)

                # Ensure consistent response shape
                if not isinstance(result, dict):
                    result = {"success": False, "data": {}, "metadata": {"error": "Invalid response from MCP tool"}}

                return result

            finally:
                # Remove from path
                if str(codex_tools_path) in sys.path:
                    sys.path.remove(str(codex_tools_path))

        except Exception as e:
            logger.error(f"Codex manage_tasks error: {e}")
            return {"success": False, "data": {}, "metadata": {"error": str(e)}}

    def search_web(self, query: str, num_results: int = 5) -> dict[str, Any]:
        try:
            # Use MCP client to invoke web research tools via Codex CLI
            import sys

            codex_tools_path = Path(__file__).parent.parent.parent / ".codex" / "tools"
            sys.path.insert(0, str(codex_tools_path))

            try:
                from codex_mcp_client import CodexMCPClient

                client = CodexMCPClient(profile=os.getenv("CODEX_PROFILE", "development"))
                result = client.call_tool("amplifier_web", "search_web", query=query, num_results=num_results)

                if not isinstance(result, dict):
                    result = {"success": False, "data": {}, "metadata": {"error": "Invalid response from MCP tool"}}

                return result

            finally:
                if str(codex_tools_path) in sys.path:
                    sys.path.remove(str(codex_tools_path))

        except Exception as e:
            logger.error(f"Codex search_web error: {e}")
            return {"success": False, "data": {}, "metadata": {"error": str(e)}}

    def fetch_url(self, url: str) -> dict[str, Any]:
        try:
            # Use MCP client to invoke web research tools via Codex CLI
            import sys

            codex_tools_path = Path(__file__).parent.parent.parent / ".codex" / "tools"
            sys.path.insert(0, str(codex_tools_path))

            try:
                from codex_mcp_client import CodexMCPClient

                client = CodexMCPClient(profile=os.getenv("CODEX_PROFILE", "development"))
                result = client.call_tool("amplifier_web", "fetch_url", url=url)

                if not isinstance(result, dict):
                    result = {"success": False, "data": {}, "metadata": {"error": "Invalid response from MCP tool"}}

                return result

            finally:
                if str(codex_tools_path) in sys.path:
                    sys.path.remove(str(codex_tools_path))

        except Exception as e:
            logger.error(f"Codex fetch_url error: {e}")
            return {"success": False, "data": {}, "metadata": {"error": str(e)}}

    def spawn_agent_with_context(
        self, agent_name: str, task: str, messages: list[dict[str, Any]], context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Codex delegates to agent backend with full context support."""
        try:
            from amplifier.core.agent_backend import get_agent_backend

            agent_backend = get_agent_backend()
            # Codex agent backend has spawn_agent_with_context method
            if hasattr(agent_backend, "spawn_agent_with_context"):
                return agent_backend.spawn_agent_with_context(agent_name, task, messages, context)
            # Fallback to regular spawn
            return agent_backend.spawn_agent(agent_name, task, context)
        except Exception as e:
            logger.error(f"Codex spawn_agent_with_context error: {e}")
            return {"success": False, "result": "", "metadata": {"error": str(e)}}

    def get_capabilities(self) -> dict[str, Any]:
        return {"task_management": True, "web_search": True, "url_fetch": True, "mcp_tools": True}


class BackendFactory:
    """Factory for creating backend instances."""

    @staticmethod
    def create_backend(backend_type: str | None = None) -> AmplifierBackend:
        if backend_type is None:
            backend_type = os.getenv("AMPLIFIER_BACKEND", "claude")
        if backend_type not in ["claude", "codex"]:
            raise ValueError(f"Invalid backend type: {backend_type}")
        logger.info(f"Creating backend: {backend_type}")
        if backend_type == "claude":
            backend = ClaudeCodeBackend()
        else:
            backend = CodexBackend()
        if not backend.is_available():
            raise BackendNotAvailableError(f"Backend {backend_type} is not available")
        return backend

    @staticmethod
    def get_available_backends() -> list[str]:
        available = []
        if ClaudeCodeBackend().is_available():
            available.append("claude")
        if CodexBackend().is_available():
            available.append("codex")
        return available

    @staticmethod
    def auto_detect_backend() -> str:
        if ClaudeCodeBackend().is_available():
            return "claude"
        if CodexBackend().is_available():
            return "codex"
        raise BackendNotAvailableError("No backend available")

    @staticmethod
    def get_backend_capabilities(backend_type: str) -> dict[str, Any]:
        if backend_type == "claude":
            return ClaudeCodeBackend().get_capabilities()
        if backend_type == "codex":
            return CodexBackend().get_capabilities()
        return {}


def get_backend() -> AmplifierBackend:
    """Convenience function to get backend."""
    return BackendFactory.create_backend()


def set_backend(backend_type: str):
    """Set AMPLIFIER_BACKEND environment variable."""
    os.environ["AMPLIFIER_BACKEND"] = backend_type
