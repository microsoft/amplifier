---
name: heal
description: Auto-heal unhealthy Python modules by analyzing and improving code quality
---

# /heal - Auto-heal unhealthy Python modules

Analyzes Python modules for complexity, lines of code, and type errors, then uses Claude to refactor and improve the code.

## Usage

```bash
/heal                      # Check health and heal up to 3 modules
/heal --check-only         # Only check health status, don't heal
/heal --max 5              # Heal up to 5 modules
/heal --threshold 80       # Heal modules below 80% health
/heal --yes                # Skip confirmation prompt
```

## What it does

The healing system:
1. Analyzes Python modules for complexity, LOC, and type errors
2. Identifies modules that fall below the health threshold (default: 70)
3. Uses Claude to refactor and improve the code
4. Validates improvements before committing changes
5. Creates git branches and commits for each healing operation

## Examples

Check module health without healing:
```bash
/heal --check-only
```

Heal up to 5 modules automatically:
```bash
/heal --max 5 --yes
```

Heal modules below 80% health:
```bash
/heal --threshold 80
```

## Health Score

Health score is calculated based on:
- **Complexity**: Cyclomatic complexity (penalized if > 10)
- **Lines of Code**: Module length (penalized if > 200 lines)
- **Type Errors**: Number of type errors from pyright

Score ranges from 0-100, with 100 being perfect health.

## Options

- `--max N`: Maximum number of modules to heal (default: 3)
- `--threshold N`: Health threshold percentage (default: 70)
- `--check-only`: Only display health status, don't perform healing
- `--yes`: Skip confirmation prompt, heal automatically
- `--project-root PATH`: Override project root directory

## Limitations

- **File size limit**: Modules larger than 400 lines are skipped to prevent timeouts
- **Critical files**: Files with patterns like `__init__`, `setup`, `config`, `settings`, or `test_` are skipped for safety
- When a file is skipped, you'll see: `⏭️ filename.py: File too large (692 lines, limit: 400)`

## Implementation

This command delegates to the amplifier CLI: `python -m amplifier.cli heal`