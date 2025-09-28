---
description: Launch Aider with Amplifier presets for targeted regeneration
argument-hint: [files ...] [--options]
allowed-tools: Bash
---

Start an Aider session using the Amplifier CLI wrapper. Arguments are passed directly to the CLI.

Execute: !`python -m amplifier.cli aider $ARGUMENTS 2>&1`

Use this command to open Aider against specific files or with additional flags (for example, `--zen` or `-m "refactor this"`).

Examples:
- `/aider mymodule.py --zen -m "Simplify this module"`
- `/aider --mode chat -m "How should I structure this feature?"`
- `/aider file1.py file2.py -m "Add error handling"`
