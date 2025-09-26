# Documentation Improvement Recommendations

## 🚨 Critical Issues to Fix

### 1. Installation Process Clarity

**Current Problem**: Users following README.md will get "command not found: amplifier" after running `make install`.

**Immediate Fix Required** in README.md around line 45-56:

```markdown
2. **Run the installer**:

   ```bash
   # Install core dependencies and Claude CLI
   make install

   # IMPORTANT: Also install the global command (highly recommended!)
   make install-global
   ```

   What this installs:
   - ✅ Python dependencies and virtual environment (`make install`)
   - ✅ Claude CLI globally via pnpm (`make install`)
   - ✅ Global `amplifier` command for use anywhere (`make install-global`)

   Note: Without `make install-global`, you'll need to use `./amplifier-anywhere.sh` directly.
```

### 2. Fix Misleading Examples

**Current Problem**: Lines 84-94 and 104-113 show using `amplifier` command, but it won't exist without `make install-global`.

**Required Changes**:

1. Add a clear note after installation steps
2. Update first example to check if command exists
3. Add fallback instructions

### 3. Remove Outdated Transition Guide

The file `docs/INSTALLATION_TRANSITION.md` references `amplifier claude` which doesn't exist. Either:
- Delete this file entirely, OR
- Update it to reflect actual current state

## 📝 Documentation That Should Be Added

### 1. Create CHANGELOG.md (Root Directory)

```markdown
# Changelog

All notable changes to Amplifier will be documented in this file.

## [Unreleased]

### Added
- Unified `amplifier` CLI command replacing scattered scripts
- Automatic project detection (Amplifier vs external projects)
- Global command installation via `make install-global`
- `amplifier doctor` command for environment validation
- Better error messages with actionable fixes

### Changed
- Simplified installation to two clear steps
- Removed dependency on wrapper scripts for external projects
- Improved Claude launcher with automatic context detection

### Fixed
- PATH configuration issues with global command
- External project mode detection
- Virtual environment activation in various shells

## [0.1.0] - Previous Version
- Initial release with amplifier-anywhere.sh script
```

### 2. Add CLI Command Reference (docs/CLI_REFERENCE.md)

```markdown
# Amplifier CLI Command Reference

## Overview

The `amplifier` command is your single entry point to all Amplifier functionality.

## Installation Check

```bash
amplifier --version  # Should show: Amplifier v0.2.0
amplifier --help     # Show all available commands
```

## Core Commands

### amplifier (default)
Launch Claude with Amplifier's AI agents in any project.

**Usage:**
```bash
amplifier [PROJECT_DIR] [OPTIONS]
```

**Examples:**
```bash
amplifier                    # Current directory
amplifier ~/my-project       # Specific directory
amplifier . --debug          # Enable debug output
```

### amplifier doctor
Check your Amplifier installation and environment.

**What it checks:**
- Python version (requires 3.11+)
- Virtual environment setup
- Claude CLI installation
- PATH configuration
- Agent availability

**Usage:**
```bash
amplifier doctor
amplifier doctor --verbose  # Detailed output
```

### amplifier smoke
Run smoke tests to validate installation.

**Usage:**
```bash
amplifier smoke              # Run all tests
amplifier smoke --quick      # Quick validation only
```

## Beta Commands

These commands are under active development:

### amplifier extract [BETA]
Extract knowledge from documents.

### amplifier synthesize [BETA]
Generate insights from extracted knowledge.

### amplifier run [BETA]
Run complete knowledge pipeline.

## Getting Help

```bash
amplifier --help              # General help
amplifier COMMAND --help      # Command-specific help
amplifier doctor              # Diagnose issues
```
```

### 3. Installation Troubleshooting Guide (docs/TROUBLESHOOTING.md)

```markdown
# Amplifier Troubleshooting Guide

## Installation Issues

### "command not found: amplifier"

**Cause**: The global command wasn't installed.

**Solution**:
```bash
cd ~/dev/amplifier
make install-global
```

### "amplifier: No such file or directory"

**Cause**: ~/bin is not in your PATH.

**Solution**:
```bash
# Add to your shell config
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc  # or ~/.bashrc
source ~/.zshrc

# Verify
which amplifier  # Should show: ~/bin/amplifier
```

### "Claude CLI not found"

**Cause**: The Claude CLI isn't installed globally.

**Solution**:
```bash
npm install -g @anthropic-ai/claude-code

# Or with pnpm
pnpm add -g @anthropic-ai/claude-code
```

### "Cannot find Amplifier installation"

**Cause**: Amplifier isn't in expected location.

**Solution**:
The global command looks for Amplifier in:
- `~/dev/amplifier`
- `~/amplifier`
- `~/repos/amplifier`
- `~/code/amplifier`

Either move Amplifier to one of these locations or create a symlink:
```bash
ln -s /your/actual/amplifier/path ~/dev/amplifier
```

## Runtime Issues

### "Failed to activate virtual environment"

**Cause**: Virtual environment is missing or corrupted.

**Solution**:
```bash
cd ~/dev/amplifier
rm -rf .venv
make install
make install-global
```

### Agents not available

**Cause**: Not running from Amplifier environment.

**Solution**:
Ensure you're using the global `amplifier` command, not running `claude` directly.

## Quick Diagnostic

Run this command to check everything:
```bash
amplifier doctor
```

This will verify:
- ✅ Python version
- ✅ Virtual environment
- ✅ Claude CLI installation
- ✅ PATH configuration
- ✅ Agent availability
```

## 🎯 Quick Wins (Do These First)

### 1. Update README.md Installation Section

**Line 45-56**, add clear two-step process with explicit global install instruction.

### 2. Add Installation Verification Step

After installation steps in README.md, add:

```markdown
3. **Verify installation**:

   ```bash
   # Check the global command is available
   which amplifier
   # Should show: /home/youruser/bin/amplifier

   # Test it works
   amplifier --version
   # Should show: Amplifier v0.2.0

   # If not found, ensure ~/bin is in your PATH
   echo $PATH | grep "$HOME/bin"
   ```
```

### 3. Fix Help Text for Incomplete Commands

In `amplifier/cli.py`, mark beta commands clearly:

```python
@cli.command()
def extract():
    """[BETA] Extract knowledge from documents.

    Note: This command is under active development and may change."""
```

### 4. Add Success Message to Installation

In Makefile `install-global` target, add final success message:

```makefile
@echo "✅ Global 'amplifier' command installed successfully!"
@echo ""
@echo "Next steps:"
@echo "  1. Ensure ~/bin is in your PATH"
@echo "  2. Run 'amplifier --version' to verify"
@echo "  3. Run 'amplifier doctor' to check your environment"
@echo "  4. Run 'amplifier' to launch Claude with AI agents!"
```

## 📊 Documentation Quality Metrics

### Current State:
- ❌ Installation confusion (missing global install step)
- ❌ Outdated transition guide
- ❌ No changelog
- ❌ No CLI reference
- ⚠️ Incomplete command help text
- ⚠️ Missing troubleshooting guide
- ✅ Good README structure
- ✅ Agent documentation exists

### Target State:
- ✅ Clear two-step installation
- ✅ Up-to-date documentation
- ✅ Comprehensive changelog
- ✅ Complete CLI reference
- ✅ Clear beta/stable indicators
- ✅ Detailed troubleshooting
- ✅ User journey tested
- ✅ All examples verified working

## Next Steps

1. **Immediate** (Today):
   - Fix README.md installation section
   - Add verification step
   - Update or remove transition guide

2. **Short-term** (This Week):
   - Create CHANGELOG.md
   - Add CLI reference document
   - Mark beta commands clearly

3. **Medium-term** (Next Sprint):
   - Complete troubleshooting guide
   - Add developer documentation
   - Create video tutorials

This documentation improvement will significantly reduce user confusion and support requests while making Amplifier more professional and approachable.