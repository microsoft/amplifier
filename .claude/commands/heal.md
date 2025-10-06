---
allowed-tools: Bash(python .claude/slash_commands/heal.py:*)
description: Check or heal unhealthy Python modules using the auto-healer
argument-hint: [--check-only] [--max N] [--threshold N] [--yes]
---

# /heal — Auto-heal unhealthy Python modules

This command shells out to `.claude/slash_commands/heal.py`, which delegates to the amplifier CLI heal command. See `@.claude/slash_commands/heal.md` for detailed usage examples.

!`python .claude/slash_commands/heal.py $ARGUMENTS`
