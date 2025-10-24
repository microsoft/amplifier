#!/usr/bin/env python3
"""
Unified CLI launcher for Amplifier supporting both Claude Code and Codex backends.

This script provides a convenient entry point for starting either Claude Code or Codex
with proper configuration and environment setup. It uses the existing backend abstraction
for validation and delegates to the appropriate CLI tools.

Usage examples:
    ./amplify.py                    # Start with default backend
    ./amplify.py --backend codex    # Start with Codex
    ./amplify.py --list-backends    # List available backends
    ./amplify.py --info codex       # Show Codex backend info
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

try:
    from amplifier import __version__
    from amplifier.core.backend import BackendNotAvailableError
    from amplifier.core.config import detect_backend
    from amplifier.core.config import get_backend_config
    from amplifier.core.config import get_backend_info
    from amplifier.core.config import is_backend_available
except ImportError as e:
    print(f"Error: Could not import amplifier modules: {e}")
    print("Make sure you're in the amplifier project directory and dependencies are installed.")
    print("Run: make install")
    sys.exit(1)

# ANSI color codes for output
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


def print_status(message: str) -> None:
    """Print a status message with blue [Amplifier] prefix."""
    print(f"{BLUE}[Amplifier]{NC} {message}")


def print_success(message: str) -> None:
    """Print a success message with green [Amplifier] prefix."""
    print(f"{GREEN}[Amplifier]{NC} {message}")


def print_warning(message: str) -> None:
    """Print a warning message with yellow [Amplifier] prefix."""
    print(f"{YELLOW}[Amplifier]{NC} {message}")


def print_error(message: str) -> None:
    """Print an error message with red [Amplifier] prefix."""
    print(f"{RED}[Amplifier]{NC} {message}")


def validate_backend(backend: str) -> bool:
    """
    Validate that the specified backend is available.

    Args:
        backend: Backend name ('claude' or 'codex')

    Returns:
        True if backend is available, False otherwise
    """
    if not is_backend_available(backend):
        print_error(f"Backend '{backend}' is not available.")

        # Provide helpful error messages
        if backend == "claude":
            print_error("Make sure Claude Code is installed and accessible.")
            print_error("Install from: https://docs.anthropic.com/claude/docs/desktop-user-guide")
        elif backend == "codex":
            print_error("Make sure Codex CLI is installed and accessible.")
            print_error("Install from: https://www.anthropic.com/codex")
            print_error("Also ensure .codex/ directory exists with config.toml")

        return False

    return True


def launch_claude_code(args: list[str]) -> int:
    """
    Launch Claude Code with the provided arguments.

    Args:
        args: Arguments to pass to Claude Code

    Returns:
        Exit code from Claude Code
    """
    # Set environment for Claude Code
    os.environ["AMPLIFIER_BACKEND"] = "claude"

    print_status("Starting Claude Code...")

    # Build command
    cmd = ["claude"] + args

    try:
        # Launch Claude Code
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print_error("Claude CLI not found. Make sure it's installed and in PATH.")
        print_error("Install from: https://docs.anthropic.com/claude/docs/desktop-user-guide")
        return 1
    except Exception as e:
        print_error(f"Failed to launch Claude Code: {e}")
        return 1


def launch_codex(args: list[str], profile: str) -> int:
    """
    Launch Codex with the provided arguments and profile.

    Args:
        args: Arguments to pass to Codex
        profile: Codex profile to use

    Returns:
        Exit code from Codex
    """
    # Set environment for Codex
    os.environ["AMPLIFIER_BACKEND"] = "codex"
    os.environ["CODEX_PROFILE"] = profile

    # Check if amplify-codex.sh wrapper exists (preferred method)
    wrapper_path = Path("./amplify-codex.sh")
    if wrapper_path.exists() and wrapper_path.is_file():
        print_status(f"Starting Codex with Amplifier wrapper (profile: {profile})...")
        cmd = ["./amplify-codex.sh", "--profile", profile] + args
        method = "wrapper script"
    else:
        print_status(f"Starting Codex directly (profile: {profile})...")
        print_warning("amplify-codex.sh wrapper not found, using direct launch")
        cmd = ["codex", "--profile", profile, "--config", ".codex/config.toml"] + args
        method = "direct launch"

    try:
        # Launch Codex
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            print_success(f"Codex session completed successfully ({method})")
        else:
            print_error(f"Codex session exited with code {result.returncode} ({method})")
        return result.returncode
    except FileNotFoundError:
        print_error("Codex CLI not found. Make sure it's installed and in PATH.")
        print_error("Install from: https://www.anthropic.com/codex")
        return 1
    except Exception as e:
        print_error(f"Failed to launch Codex: {e}")
        return 1


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Unified CLI launcher for Amplifier backends",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./amplify.py                    # Start with default backend
  ./amplify.py --backend codex    # Start with Codex
  ./amplify.py --list-backends    # List available backends
  ./amplify.py --info codex       # Show Codex backend info
        """,
    )

    parser.add_argument("--backend", "-b", choices=["claude", "codex"], help="Backend to use (default: from config)")

    parser.add_argument(
        "--profile",
        "-p",
        choices=["development", "ci", "review"],
        default="development",
        help="Codex profile to use (default: development)",
    )

    parser.add_argument("--config", type=str, help="Path to configuration file (default: .env)")

    parser.add_argument("--list-backends", action="store_true", help="List available backends and exit")

    parser.add_argument(
        "--info", nargs="?", const="CURRENT", help="Show info for specified backend, or current if omitted"
    )

    parser.add_argument("--version", "-v", action="store_true", help="Show version information and exit")

    # Pass through remaining arguments to the backend CLI
    parser.add_argument("args", nargs="*", help="Arguments to pass through to the backend CLI")

    return parser.parse_args()


def list_backends() -> None:
    """List available backends and their status."""
    from amplifier.core.backend import BackendFactory

    print_status("Available backends:")
    print()

    backends = BackendFactory.get_available_backends()
    if not backends:
        print_error("No backends available!")
        print_error("Install Claude Code or Codex CLI to get started.")
        return

    for backend_name in ["claude", "codex"]:
        status = "✓ Available" if backend_name in backends else "✗ Not available"
        color = GREEN if backend_name in backends else RED

        if backend_name == "claude":
            description = "Claude Code (VS Code extension)"
        else:
            description = "Codex CLI (standalone)"

        print(f"  {color}{backend_name}{NC} - {description}")
        print(f"    Status: {status}")

        if backend_name not in backends:
            if backend_name == "claude":
                print("    Install: https://docs.anthropic.com/claude/docs/desktop-user-guide")
            else:
                print("    Install: https://www.anthropic.com/codex")
        print()

    # Show current configuration
    try:
        config = get_backend_config()
        current = config.amplifier_backend
        print_status(f"Current configuration: {current}")
        if current not in backends:
            print_warning(f"Configured backend '{current}' is not available")
    except Exception as e:
        print_warning(f"Could not determine current configuration: {e}")


def show_backend_info(backend: str) -> None:
    """Show detailed information for a specific backend."""
    try:
        info = get_backend_info(backend)

        print_status(f"Backend Information: {backend}")
        print()

        # Basic info
        print(f"Available: {'Yes' if info.get('available', False) else 'No'}")

        if info.get("available"):
            print(f"CLI Path: {info.get('cli_path', 'Not found')}")
            print(f"Version: {info.get('version', 'Unknown')}")

            # Backend-specific info
            if backend == "claude":
                config_dir = Path(".claude")
                print(f"Config Directory: {config_dir} ({'Exists' if config_dir.exists() else 'Missing'})")
            elif backend == "codex":
                config_file = Path(".codex/config.toml")
                wrapper_script = Path("./amplify-codex.sh")
                print(f"Config File: {config_file} ({'Exists' if config_file.exists() else 'Missing'})")
                print(f"Wrapper Script: {wrapper_script} ({'Exists' if wrapper_script.exists() else 'Missing'})")
                print(f"Profile: {os.environ.get('CODEX_PROFILE', 'development (default)')}")

        # Additional metadata
        if "metadata" in info:
            print()
            print("Additional Info:")
            for key, value in info["metadata"].items():
                print(f"  {key}: {value}")

    except Exception as e:
        print_error(f"Failed to get backend info for '{backend}': {e}")


def show_version() -> None:
    """Show version information."""
    print(f"Amplifier v{__version__}")
    print(f"Python {sys.version.split()[0]}")

    try:
        import platform

        print(f"Platform: {platform.platform()}")
    except:
        pass

    try:
        config = get_backend_config()
        print(f"Configured Backend: {config.amplifier_backend}")
    except:
        print("Configured Backend: Unknown")


def main() -> int:
    """Main entry point."""
    try:
        args = parse_args()

        # Handle special commands that exit early
        if args.list_backends:
            list_backends()
            return 0

        if args.info is not None:
            if args.info in {"claude", "codex"}:
                show_backend_info(args.info)
                return 0
            if args.info == "CURRENT":
                # Determine effective backend using precedence
                config = get_backend_config()
                backend = args.backend
                if not backend:
                    backend = config.amplifier_backend
                    if not backend and config.amplifier_backend_auto_detect:
                        try:
                            backend = detect_backend()
                            if backend:
                                print_status(f"Auto-detected backend: {backend}")
                            else:
                                backend = "claude"  # Default fallback
                                print_warning("Could not auto-detect backend, using default: claude")
                        except Exception as e:
                            print_warning(f"Auto-detection failed: {e}, using default: claude")
                            backend = "claude"
                    elif not backend:
                        backend = "claude"  # Default fallback
                show_backend_info(backend)
                return 0
            print_error(f"Invalid backend '{args.info}'. Must be 'claude' or 'codex'.")
            return 1

        if args.version:
            show_version()
            return 0

        # Load configuration
        if args.config:
            os.environ["ENV_FILE"] = args.config

        try:
            config = get_backend_config()
        except Exception as e:
            print_error(f"Failed to load configuration: {e}")
            return 1

        # Determine backend
        backend = args.backend
        if not backend:
            backend = config.amplifier_backend
            if not backend and config.amplifier_backend_auto_detect:
                try:
                    backend = detect_backend()
                    if backend:
                        print_status(f"Auto-detected backend: {backend}")
                    else:
                        backend = "claude"  # Default fallback
                        print_warning("Could not auto-detect backend, using default: claude")
                except Exception as e:
                    print_warning(f"Auto-detection failed: {e}, using default: claude")
                    backend = "claude"
            elif not backend:
                backend = "claude"  # Default fallback

        print_status(f"Using backend: {backend}")

        # Validate backend availability
        if not validate_backend(backend):
            print_error("Backend validation failed. Use --list-backends to see available options.")
            return 1

        # Launch the appropriate backend
        if backend == "claude":
            exit_code = launch_claude_code(args.args)
        elif backend == "codex":
            exit_code = launch_codex(args.args, args.profile)
        else:
            print_error(f"Unknown backend: {backend}")
            return 1

        # Report final status
        if exit_code == 0:
            print_success("Session completed successfully")
        else:
            print_error(f"Session exited with code {exit_code}")

        return exit_code

    except KeyboardInterrupt:
        print_warning("Interrupted by user")
        return 130  # Standard interrupt exit code
    except BackendNotAvailableError as e:
        print_error(f"Backend error: {e}")
        return 1
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        return e.returncode
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback

        if os.environ.get("DEBUG"):
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
