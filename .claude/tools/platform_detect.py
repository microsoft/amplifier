"""
Platform detection for multi-machine Amplifier deployment.

Detects whether we're running on:
  - Windows Claude Code machine (C:/claude/)
  - Windows Gemini/OpenCode machine (C:/Przemek/)
  - Linux machine (/opt/amplifier/)

Exports path constants that all hooks use instead of hardcoded paths.

Detection priority (highest to lowest):
  1. CLAUDECODE=1 env var  — set by .bash_profile for Claude Code sessions
  2. OPENCODE=1 env var    — set as User env var for OpenCode sessions
  3. Directory presence    — fallback for environments without env vars set
"""

import os
import sys

_claudecode_env = os.environ.get("CLAUDECODE") == "1"
_opencode_env = os.environ.get("OPENCODE") == "1"
_is_linux = sys.platform.startswith("linux")

if _claudecode_env:
    IS_CLAUDE_CODE = True
    IS_OPENCODE = False
    IS_LINUX = False
elif _opencode_env:
    IS_CLAUDE_CODE = False
    IS_OPENCODE = True
    IS_LINUX = False
elif _is_linux:
    IS_CLAUDE_CODE = os.path.isdir("/opt/amplifier")
    IS_OPENCODE = False
    IS_LINUX = True
else:
    # Windows fallback: check for Gemini first, as its root is unique
    IS_OPENCODE = os.path.isdir("C:/Przemek")
    IS_CLAUDE_CODE = os.path.isdir("C:/claude/amplifier") and not IS_OPENCODE
    IS_LINUX = False

if IS_LINUX and os.path.isdir("/opt/amplifier"):
    AMPLIFIER_ROOT = "/opt"
    SUPERPOWERS_FALLBACK = ""
elif IS_CLAUDE_CODE and not IS_LINUX:
    AMPLIFIER_ROOT = "C:/claude"
    SUPERPOWERS_FALLBACK = "C:/claude/superpowers"
elif IS_OPENCODE:
    AMPLIFIER_ROOT = "C:/Przemek"
    SUPERPOWERS_FALLBACK = "C:/Przemek/superpowers"
else:
    AMPLIFIER_ROOT = os.path.expanduser("~")
    SUPERPOWERS_FALLBACK = ""


if __name__ == "__main__":
    print(f"IS_CLAUDE_CODE={IS_CLAUDE_CODE}")
    print(f"IS_OPENCODE={IS_OPENCODE}")
    print(f"IS_LINUX={IS_LINUX}")
    print(f"AMPLIFIER_ROOT={AMPLIFIER_ROOT}")
    print(f"SUPERPOWERS_FALLBACK={SUPERPOWERS_FALLBACK}")
