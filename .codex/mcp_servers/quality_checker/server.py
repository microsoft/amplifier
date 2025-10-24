import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..base import AmplifierMCPServer

# Import base utilities
from ..base import error_response
from ..base import success_response


class QualityCheckerServer(AmplifierMCPServer):
    """MCP server for code quality checking and validation"""

    def __init__(self):
        # Initialize FastMCP
        mcp = FastMCP("amplifier-quality")

        # Initialize base server
        super().__init__("quality_checker", mcp)

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools"""

        @self.mcp.tool()
        async def check_code_quality(
            file_paths: list[str], tool_name: str | None = None, cwd: str | None = None
        ) -> dict[str, Any]:
            """Run quality checks after code changes (replaces PostToolUse hook)

            Args:
                file_paths: List of file paths that were modified
                tool_name: Name of the tool that made the changes (optional)
                cwd: Current working directory (optional)

            Returns:
                Structured results with pass/fail status and issue details
            """
            try:
                self.logger.info(f"Running code quality check for {len(file_paths)} files")
                self.logger.json_preview("file_paths", file_paths)

                # Determine starting directory
                start_dir = Path(cwd) if cwd else None
                if not start_dir and file_paths:
                    # Use directory of first file
                    start_dir = Path(file_paths[0]).parent

                if not start_dir:
                    start_dir = Path.cwd()

                # Find project root
                project_root = find_project_root(start_dir)
                if not project_root:
                    return error_response("Could not find project root (.git, Makefile, or pyproject.toml)")

                self.logger.info(f"Project root: {project_root}")

                # Check for Makefile with check target
                makefile_path = project_root / "Makefile"
                if not makefile_path.exists() or not make_target_exists(makefile_path, "check"):
                    return error_response(
                        "No Makefile with 'check' target found",
                        {"makefile_exists": makefile_path.exists(), "project_root": str(project_root)},
                    )

                # Setup worktree environment
                setup_worktree_env(project_root)

                # Run make check
                self.logger.info("Running 'make check'")
                result = await asyncio.create_subprocess_exec(
                    "make",
                    "check",
                    cwd=str(project_root),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=dict(os.environ, VIRTUAL_ENV=""),  # Unset VIRTUAL_ENV for uv
                )

                stdout, stderr = await result.communicate()
                output = stdout.decode() + stderr.decode()

                # Parse output
                parsed = parse_make_output(output)

                self.logger.info(f"Make check completed with return code: {result.returncode}")

                return success_response(
                    {
                        "passed": result.returncode == 0,
                        "return_code": result.returncode,
                        "output": output,
                        "parsed": parsed,
                        "project_root": str(project_root),
                    },
                    {"tool_name": tool_name, "files_checked": len(file_paths)},
                )

            except Exception as e:
                self.logger.exception("check_code_quality failed", e)
                return error_response(f"Quality check failed: {str(e)}")

        @self.mcp.tool()
        async def run_specific_checks(
            check_type: str, file_paths: list[str] | None = None, args: list[str] | None = None
        ) -> dict[str, Any]:
            """Run specific quality tools on demand

            Args:
                check_type: Type of check ("lint", "format", "type", "test")
                file_paths: Specific files to check (optional)
                args: Additional arguments for the tool (optional)

            Returns:
                Structured results with issue locations and severity
            """
            try:
                self.logger.info(f"Running specific check: {check_type}")

                # Map check types to commands
                command_map = {
                    "lint": ["ruff", "check"],
                    "format": ["ruff", "format", "--check"],
                    "type": ["pyright"],
                    "test": ["pytest"],
                }

                if check_type not in command_map:
                    return error_response(
                        f"Unknown check type: {check_type}", {"supported_types": list(command_map.keys())}
                    )

                # Build command
                cmd = ["uv", "run"] + command_map[check_type]
                if args:
                    cmd.extend(args)
                if file_paths:
                    cmd.extend(file_paths)

                self.logger.info(f"Running command: {' '.join(cmd)}")

                # Run command
                result = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await result.communicate()
                output = stdout.decode() + stderr.decode()

                # Parse output based on tool
                parsed = parse_tool_output(check_type, output)

                self.logger.info(f"{check_type} check completed with return code: {result.returncode}")

                return success_response(
                    {
                        "passed": result.returncode == 0,
                        "return_code": result.returncode,
                        "output": output,
                        "parsed": parsed,
                        "check_type": check_type,
                    }
                )

            except Exception as e:
                self.logger.exception(f"run_specific_checks ({check_type}) failed", e)
                return error_response(f"Specific check failed: {str(e)}")

        @self.mcp.tool()
        async def validate_environment() -> dict[str, Any]:
            """Check if development environment is properly set up

            Returns:
                Environment status report
            """
            try:
                self.logger.info("Validating development environment")

                status = {}

                # Check for virtual environment
                venv_exists = Path(".venv").exists()
                status["virtual_env_exists"] = venv_exists

                # Check uv availability
                try:
                    result = await asyncio.create_subprocess_exec(
                        "uv", "--version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                    )
                    await result.communicate()
                    status["uv_available"] = result.returncode == 0
                except FileNotFoundError:
                    status["uv_available"] = False

                # Check Makefile
                makefile_exists = Path("Makefile").exists()
                status["makefile_exists"] = makefile_exists

                # Check make availability
                try:
                    result = await asyncio.create_subprocess_exec(
                        "make", "--version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                    )
                    await result.communicate()
                    status["make_available"] = result.returncode == 0
                except FileNotFoundError:
                    status["make_available"] = False

                # Check key dependencies if venv exists
                if venv_exists:
                    try:
                        result = await asyncio.create_subprocess_exec(
                            "uv",
                            "run",
                            "python",
                            "-c",
                            "import ruff, pyright, pytest",
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        await result.communicate()
                        status["key_deps_installed"] = result.returncode == 0
                    except Exception:
                        status["key_deps_installed"] = False
                else:
                    status["key_deps_installed"] = None  # Cannot check without venv

                # Overall status
                critical_checks = [
                    status.get("virtual_env_exists", False),
                    status.get("uv_available", False),
                    status.get("makefile_exists", False),
                    status.get("make_available", False),
                ]
                status["environment_ready"] = all(critical_checks)

                self.logger.info(
                    f"Environment validation complete: {'ready' if status['environment_ready'] else 'not ready'}"
                )

                return success_response(status)

            except Exception as e:
                self.logger.exception("validate_environment failed", e)
                return error_response(f"Environment validation failed: {str(e)}")


def find_project_root(start_dir: Path) -> Path | None:
    """Walk up directory tree to find project root"""
    current = start_dir
    while current != current.parent:
        if (current / ".git").exists() or (current / "Makefile").exists() or (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return None


def make_target_exists(makefile_path: Path, target: str) -> bool:
    """Check if Makefile has specific target"""
    try:
        result = subprocess.run(["make", "-C", str(makefile_path.parent), "-n", target], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def parse_make_output(output: str) -> dict[str, Any]:
    """Parse make check output for structured results"""
    lines = output.split("\n")

    parsed = {"errors": [], "warnings": [], "summary": "", "has_failures": False}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for common error patterns
        if "error" in line.lower() or "failed" in line.lower():
            parsed["errors"].append(line)
            parsed["has_failures"] = True
        elif "warning" in line.lower():
            parsed["warnings"].append(line)
        elif "passed" in line.lower() or "success" in line.lower():
            parsed["summary"] += line + "\n"

    # If no specific parsing, include raw output summary
    if not parsed["summary"]:
        parsed["summary"] = output[-500:]  # Last 500 chars

    return parsed


def parse_tool_output(check_type: str, output: str) -> dict[str, Any]:
    """Parse tool-specific output"""
    parsed = {"issues": [], "summary": ""}

    lines = output.split("\n")

    if check_type == "lint":
        # Parse ruff output
        for line in lines:
            if ":" in line and ".py:" in line:
                # filename:line:col: code message
                parsed["issues"].append(
                    {"type": "lint", "line": line, "severity": "error" if "E" in line else "warning"}
                )

    elif check_type == "type":
        # Parse pyright output
        for line in lines:
            if "error" in line.lower():
                parsed["issues"].append({"type": "type", "line": line, "severity": "error"})

    elif check_type == "test":
        # Parse pytest output
        for line in lines:
            if "FAILED" in line or "ERROR" in line:
                parsed["issues"].append({"type": "test", "line": line, "severity": "error"})

    parsed["summary"] = f"Found {len(parsed['issues'])} issues"

    return parsed


def setup_worktree_env(project_dir: Path):
    """Handle git worktree virtual environment setup"""
    # Check if we're in a worktree
    git_dir = project_dir / ".git"
    if git_dir.is_file():
        # This is a worktree, unset VIRTUAL_ENV to let uv detect local .venv
        os.environ.pop("VIRTUAL_ENV", None)


# Create and run server
if __name__ == "__main__":
    server = QualityCheckerServer()
    server.run()
