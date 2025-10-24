"""
Shared base classes and utilities for MCP servers.
Provides logging, common initialization, and error handling for all MCP servers.
"""

import json
import os
import sys
import traceback
from collections.abc import Awaitable
from collections.abc import Callable
from datetime import date
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any


class MCPLogger:
    """Simple logger that writes to file with structured output for MCP servers"""

    def __init__(self, server_name: str):
        """Initialize logger for a specific MCP server"""
        self.server_name = server_name

        # Create logs directory
        self.log_dir = Path(__file__).parent.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)

        # Create log file with today's date
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"{server_name}_{today}.log"

        # Log initialization
        self.info(f"Logger initialized for {server_name}")

    def _format_message(self, level: str, message: str) -> str:
        """Format a log message with timestamp and level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return f"[{timestamp}] [{self.server_name}] [{level}] {message}"

    def _write(self, level: str, message: str):
        """Write to log file"""
        formatted = self._format_message(level, message)

        # Write to file
        try:
            with open(self.log_file, "a") as f:
                f.write(formatted + "\n")
        except Exception as e:
            # If file writing fails, write to stderr as fallback
            print(f"Failed to write to log file: {e}", file=sys.stderr)
            print(formatted, file=sys.stderr)

    def info(self, message: str):
        """Log info level message"""
        self._write("INFO", message)

    def debug(self, message: str):
        """Log debug level message"""
        self._write("DEBUG", message)

    def error(self, message: str):
        """Log error level message"""
        self._write("ERROR", message)

    def warning(self, message: str):
        """Log warning level message"""
        self._write("WARN", message)

    def json_preview(self, label: str, data: Any, max_length: int = 500):
        """Log a preview of JSON data"""
        try:
            json_str = json.dumps(data, default=str)
            if len(json_str) > max_length:
                json_str = json_str[:max_length] + "..."
            self.debug(f"{label}: {json_str}")
        except Exception as e:
            self.error(f"Failed to serialize {label}: {e}")

    def structure_preview(self, label: str, data: dict):
        """Log structure of a dict without full content"""
        structure = {}
        for key, value in data.items():
            if isinstance(value, list):
                structure[key] = f"list[{len(value)}]"
            elif isinstance(value, dict):
                structure[key] = (
                    f"dict[{list(value.keys())[:3]}...]" if len(value.keys()) > 3 else f"dict[{list(value.keys())}]"
                )
            elif isinstance(value, str):
                structure[key] = f"str[{len(value)} chars]"
            else:
                structure[key] = type(value).__name__
        self.debug(f"{label}: {json.dumps(structure)}")

    def exception(self, message: str, exc: Exception | None = None):
        """Log exception with traceback"""
        if exc:
            self.error(f"{message}: {exc}")
            self.error(f"Traceback:\n{traceback.format_exc()}")
        else:
            self.error(message)
            self.error(f"Traceback:\n{traceback.format_exc()}")

    def cleanup_old_logs(self, days_to_keep: int = 7):
        """Clean up log files older than specified days"""
        try:
            today = datetime.now().date()
            cutoff = today - timedelta(days=days_to_keep)

            for log_file in self.log_dir.glob(f"{self.server_name}_*.log"):
                # Parse date from filename
                try:
                    date_str = log_file.stem.split("_")[-1]
                    # Parse date components manually to avoid strptime timezone warning
                    year = int(date_str[0:4])
                    month = int(date_str[4:6])
                    day = int(date_str[6:8])
                    file_date = date(year, month, day)
                    if file_date < cutoff:
                        log_file.unlink()
                        self.info(f"Deleted old log file: {log_file.name}")
                except (ValueError, IndexError):
                    # Skip files that don't match expected pattern
                    continue
        except Exception as e:
            self.warning(f"Failed to cleanup old logs: {e}")


def get_project_root(start_path: Path | None = None) -> Path | None:
    """Find project root by looking for .git, pyproject.toml, or Makefile"""
    if start_path is None:
        start_path = Path.cwd()

    current = start_path
    while current != current.parent:
        # Check for common project root indicators
        if (current / ".git").exists() or (current / "pyproject.toml").exists() or (current / "Makefile").exists():
            return current
        current = current.parent

    return None


def setup_amplifier_path(project_root: Path | None = None) -> bool:
    """Add amplifier to Python path for imports"""
    try:
        if project_root is None:
            project_root = get_project_root()

        if project_root:
            amplifier_path = project_root / "amplifier"
            if amplifier_path.exists():
                sys.path.insert(0, str(project_root))
                return True

        return False
    except Exception:
        return False


def check_memory_system_enabled() -> bool:
    """Read MEMORY_SYSTEM_ENABLED environment variable"""
    return os.getenv("MEMORY_SYSTEM_ENABLED", "false").lower() in ["true", "1", "yes"]


def safe_import(module_path: str, fallback: Any = None) -> Any:
    """Safely import amplifier modules with fallback"""
    try:
        __import__(module_path)
        return sys.modules[module_path]
    except ImportError:
        return fallback


def success_response(data: Any, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build successful tool response with metadata"""
    response = {"success": True, "data": data}
    if metadata:
        response["metadata"] = metadata
    return response


def error_response(error: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build error response with details"""
    response = {"success": False, "error": error}
    if details:
        response["details"] = details
    return response


def metadata_response(metadata: dict[str, Any]) -> dict[str, Any]:
    """Build metadata-only response"""
    return {"success": True, "metadata": metadata}


class AmplifierMCPServer:
    """Base class for MCP servers with common initialization and error handling"""

    def __init__(self, server_name: str, fastmcp_instance):
        """Initialize base server with common setup"""
        self.server_name = server_name
        self.mcp = fastmcp_instance
        self.logger = MCPLogger(server_name)

        # Common initialization
        self.project_root = get_project_root()
        self.amplifier_available = setup_amplifier_path(self.project_root)
        self.memory_enabled = check_memory_system_enabled()

        # Log initialization status
        self.logger.info(f"Project root: {self.project_root}")
        self.logger.info(f"Amplifier available: {self.amplifier_available}")
        self.logger.info(f"Memory system enabled: {self.memory_enabled}")

        # Register common tools
        self._register_health_check()

    def _register_health_check(self):
        """Register the common health check tool"""

        @self.mcp.tool()
        async def health_check() -> dict[str, Any]:
            """Check server health and module availability"""
            try:
                status = {
                    "server": self.server_name,
                    "project_root": str(self.project_root) if self.project_root else None,
                    "amplifier_available": self.amplifier_available,
                    "memory_enabled": self.memory_enabled,
                    "timestamp": datetime.now().isoformat(),
                }

                # Test basic imports if amplifier is available
                if self.amplifier_available:
                    try:
                        from amplifier.memory import MemoryStore

                        status["memory_store_import"] = True
                    except ImportError:
                        status["memory_store_import"] = False

                    try:
                        from amplifier.search import MemorySearcher

                        status["memory_searcher_import"] = True
                    except ImportError:
                        status["memory_searcher_import"] = False

                self.logger.info("Health check completed successfully")
                return success_response(status, {"checked_at": datetime.now().isoformat()})

            except Exception as e:
                self.logger.exception("Health check failed", e)
                return error_response("Health check failed", {"error": str(e)})

    def tool_error_handler(self, tool_func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """Decorator to wrap tool functions with error handling"""

        async def wrapper(*args, **kwargs):
            try:
                self.logger.cleanup_old_logs()  # Clean up logs on each tool call
                result = await tool_func(*args, **kwargs)
                return result
            except Exception as e:
                self.logger.exception(f"Tool {tool_func.__name__} failed", e)
                return error_response(
                    f"Tool execution failed: {str(e)}", {"tool": tool_func.__name__, "error_type": type(e).__name__}
                )

        # Preserve function metadata for FastMCP
        wrapper.__name__ = tool_func.__name__
        wrapper.__doc__ = tool_func.__doc__
        return wrapper

    def run(self):
        """Run the MCP server (to be called by subclasses)"""
        self.logger.info(f"Starting {self.server_name} MCP server")
        self.mcp.run()
