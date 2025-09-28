---
description: Run the Amplifier auto-healing workflow through the CLI
argument-hint: [--check-only] [--max N] [--threshold SCORE]
allowed-tools: Bash
---

Automate healing of unhealthy modules using the Amplifier CLI.

## Current Status
!`python -m amplifier.cli heal --check-only 2>&1`

## Task
Based on the health analysis above, run the healing process with the provided arguments (or use defaults if no arguments provided).

Execute: !`python -m amplifier.cli heal $ARGUMENTS 2>&1`

Review the reported results and summarize the improvements made to each module.
