"""
Platform detection for dual-machine Amplifier deployment.

Detects whether we're running on the Claude Code machine (C:/claude/)
or the Gemini/OpenCode machine (C:/Przemek/) and exports path constants
that all hooks use instead of hardcoded paths.

Detection priority (highest to lowest):
  1. CLAUDECODE=1 env var  — set by .bash_profile for Claude Code sessions
  2. OPENCODE=1 env var    — set as User env var for OpenCode sessions
  3. Directory presence    — fallback for environments without env vars set
"""

import os

_claudecode_env = os.environ.get("CLAUDECODE") == "1"
_opencode_env = os.environ.get("OPENCODE") == "1"

if _claudecode_env:
    IS_CLAUDE_CODE = True
    IS_OPENCODE = False
elif _opencode_env:
    IS_CLAUDE_CODE = False
    IS_OPENCODE = True
else:
    # Check for Gemini first, as its root is unique to that machine
    IS_OPENCODE = os.path.isdir("C:/Przemek")
    IS_CLAUDE_CODE = os.path.isdir("C:/claude/amplifier") and not IS_OPENCODE

if IS_CLAUDE_CODE:
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
    print(f"AMPLIFIER_ROOT={AMPLIFIER_ROOT}")
    print(f"SUPERPOWERS_FALLBACK={SUPERPOWERS_FALLBACK}")
