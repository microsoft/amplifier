# Doctor vs Validate Commands

## Quick Comparison

| Command | Purpose | What it Checks | When to Use |
|---------|---------|----------------|-------------|
| `amplifier doctor` | Check runtime environment | External dependencies & environment setup | Before first use or when things aren't working |
| `make validate` | Verify installation correctness | Code installation & functionality | After installation or updates |

## Detailed Breakdown

### `amplifier doctor`
Checks the **runtime environment** your system needs to run Amplifier:

**Required Components** (must pass):
- ✓ Python 3.11+ installed
- ✓ Claude CLI available  
- ✓ npm installed

**Optional Components** (nice to have):
- ◯ AMPLIFIER_HOME environment variable
- ◯ Config file
- ◯ Data directory

**Exit codes:**
- 0 = All required components OK
- 1 = Critical component missing

### `make validate` (or `python validate_installation.py`)
Verifies the **Amplifier installation** itself is correct:

**Core Installation:**
- Python version check
- `amplifier` command works
- Python CLI installed
- Unified wrapper installed

**Module Functionality:**
- Cache module imports correctly
- Event module imports correctly
- CLI module imports correctly

**Performance & Quality:**
- Cache performance test (verifies speedup)
- Lint status (code quality)

**Optional with `--full`:**
- Smoke tests (AI-driven functionality tests)

**Exit codes:**
- 0 = All validations passed
- 1 = Some validations failed

## When Each Command Shows Issues

### Doctor shows issues but validate passes:
This is normal! It means Amplifier is installed correctly but you're missing optional environment configurations. The system will work fine with defaults.

Example:
```bash
amplifier doctor
# Shows: AMPLIFIER_HOME [INFO] Not configured (using defaults)
# This is OK - just informational

make validate  
# Shows: ✅ ALL VALIDATIONS PASSED!
# Installation is perfect
```

### Validate fails but doctor passes:
This indicates the environment is ready but the installation has problems. You may need to reinstall or fix specific components.

Example:
```bash
amplifier doctor
# Shows: ✓ All required components are healthy

make validate
# Shows: ❌ Cache module import failed
# Need to fix the installation
```

## TL;DR

- **`amplifier doctor`** = "Is my computer ready to run Amplifier?"
- **`make validate`** = "Is Amplifier installed correctly?"

Both passing = Everything is perfect! 🎉
Doctor has optional warnings = Normal, system uses defaults 👍
Validate fails = Need to fix installation 🔧