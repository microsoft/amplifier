#!/usr/bin/env python3
"""
Runs git-collector → falls back to npx automatically (with --yes) →
shows guidance only if everything fails.
"""

import os
import subprocess
import sys
from shutil import which
from textwrap import dedent

OUTPUT_DIR = "ai_context/git_collector"


# Debug function - can be removed or commented out when fixed
def print_debug_info():
    print("===== DEBUG INFO =====")
    print(f"PATH: {os.environ.get('PATH', '')}")
    npx_location = which("npx")
    print(f"NPX location: {npx_location}")
    print("======================")


def guidance() -> str:
    return dedent(
        """\
        ❌  git-collector could not be run.

        Fixes:
          • Global install ……  npm i -g git-collector
          • Or rely on npx (no install).

        Then re-run:  make ai-context-files
        """
    )


def run(cmd: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    """Run a command, optionally capturing its output."""
    print("→", " ".join(cmd))
    return subprocess.run(
        cmd,
        text=True,
        capture_output=capture,
    )


def main() -> None:
    root = sys.argv[1] if len(sys.argv) > 1 else OUTPUT_DIR

    # Uncomment to see debug info when needed
    # print_debug_info()

    # Preferred runners in order
    runners: list[list[str]] = []
    git_collecto_path = which("git-collector")
    if git_collecto_path:
        runners.append([git_collecto_path])
    pnpm_path = which("pnpm")
    if pnpm_path:
        try:
            # Check if git-collector is available via pnpm by running a simple list command
            # Redirect output to avoid cluttering the console
            result = subprocess.run(
                [pnpm_path, "list", "git-collector"],
                capture_output=True,
                text=True,
                check=False,
            )

            # If git-collector is in the output, it's installed via pnpm
            if "git-collector" in result.stdout and "ERR" not in result.stdout:
                runners.append([pnpm_path, "exec", "git-collector"])
        except Exception:
            # If any error occurs during check, move to next option
            pass

    # For npx, we need to try multiple approaches
    # First, check if npx is in the PATH
    npx_path = which("npx")
    if npx_path:
        # Use the full path to npx if we can find it
        runners.append([npx_path, "--yes", "git-collector"])
    else:
        # Fallback to just the command name as a last resort
        runners.append(["npx", "--yes", "git-collector"])

    if not runners:
        sys.exit(guidance())

    last_result = None
    for r in runners:
        # Capture output for git-collector / pnpm, but stream for npx (shows progress)
        is_npx = "npx" in r[0].lower() if isinstance(r[0], str) else False
        is_git_collector = "git-collector" in r[0].lower() if isinstance(r[0], str) else False
        capture = not (is_npx or is_git_collector)

        print(f"Executing command: {' '.join(r + [root, '--update'])}")
        try:
            last_result = run(r + [root, "--update"], capture=capture)
        except Exception as e:
            print(f"Error executing command: {e}")
            continue
        if last_result.returncode == 0:
            return  # success 🎉
        if r[:2] == ["pnpm", "exec"]:
            print("pnpm run not supported — falling back to npx …")

    # All attempts failed → print stderr (if any) and guidance
    if last_result and last_result.stderr:
        print(last_result.stderr.strip(), file=sys.stderr)
    sys.exit(guidance())


if __name__ == "__main__":
    main()
