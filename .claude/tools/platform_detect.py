"""
Platform detection for dual-machine Amplifier deployment.

Detects whether we're running on the Claude Code machine (C:/claude/)
or the Gemini/OpenCode machine (C:/Przemek/) and exports path constants
that all hooks use instead of hardcoded paths.
"""

import os

# Platform detection by root folder presence
IS_CLAUDE_CODE = os.path.isdir("C:/claude/amplifier")
IS_OPENCODE = os.path.isdir("C:/Przemek") and not IS_CLAUDE_CODE

# Path constants
if IS_CLAUDE_CODE:
    AMPLIFIER_ROOT = "C:/claude"
    SUPERPOWERS_FALLBACK = "C:/claude/superpowers"
elif IS_OPENCODE:
    AMPLIFIER_ROOT = "C:/Przemek"
    SUPERPOWERS_FALLBACK = "C:/Przemek/superpowers"
else:
    # Unknown platform — use home directory fallback
    AMPLIFIER_ROOT = os.path.expanduser("~")
    SUPERPOWERS_FALLBACK = ""


if __name__ == "__main__":
    print(f"IS_CLAUDE_CODE={IS_CLAUDE_CODE}")
    print(f"IS_OPENCODE={IS_OPENCODE}")
    print(f"AMPLIFIER_ROOT={AMPLIFIER_ROOT}")
    print(f"SUPERPOWERS_FALLBACK={SUPERPOWERS_FALLBACK}")
