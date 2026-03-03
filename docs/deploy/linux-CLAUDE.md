# CLAUDE.md — Global Safety Rules (Linux)

- All files and folders MUST be created under `/opt/` only.
  Enforced by PreToolUse hook: `/opt/amplifier/scripts/guard-paths-linux.sh`.
- For full tools, agents, and workflow context: `cd /opt/amplifier && claude`.
