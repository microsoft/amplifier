# Amplifier Installation Transition Guide

## What Changed

The Amplifier installation process has been simplified and unified. The new `amplifier claude` command replaces the need for separate wrapper scripts and provides a cleaner installation experience.

## New Installation Process

### 1. Install Amplifier

```bash
# Clone the repository (if not already done)
git clone https://github.com/your-org/amplifier ~/dev/amplifier
cd ~/dev/amplifier

# Install all dependencies and global command
make install
```

This will:
- Set up the Python virtual environment
- Install all Python dependencies
- Install the Claude CLI globally via npm
- Create the global `amplifier` command in `~/bin`

### 2. Add ~/bin to PATH (if needed)

If `~/bin` is not in your PATH, add it to your shell configuration:

```bash
# For bash
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# For zsh
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## Usage

### Primary Method: Using `amplifier claude`

```bash
# Start Claude in current directory
amplifier claude

# Start Claude in a specific project
amplifier claude ~/my-project

# Pass options to Claude
amplifier claude . --model sonnet
```

### Backward Compatibility

For convenience, the old syntax still works:

```bash
# These still work (automatically route to claude command)
amplifier ~/my-project
amplifier . --model sonnet
```

## Features

The `amplifier claude` command provides:
- **Automatic project detection**: Knows whether you're working on Amplifier itself or an external project
- **External mode**: Automatically prevents modifications to Amplifier when working on other projects
- **Full agent support**: All 20+ Amplifier agents are available in any project
- **Clean integration**: No complex wrapper scripts needed

## Other Amplifier Commands

```bash
# Check your environment
amplifier doctor

# Run smoke tests
amplifier smoke

# Extract knowledge from documents
amplifier extract ~/documents

# Synthesize insights
amplifier synthesize

# View events
amplifier events tail
amplifier events summary

# Show version
amplifier --version

# Get help
amplifier --help
```

## Migration from Old Installation

If you have the old installation with `amplifier-anywhere.sh`:

1. **Clean up old files**:
   ```bash
   rm -f ~/bin/amplifier-unified
   rm -f ~/bin/amplifier-cli
   ```

2. **Reinstall**:
   ```bash
   cd ~/dev/amplifier
   make install-global
   ```

## Troubleshooting

### Claude CLI not found

If you see "Claude CLI not found", install it:

```bash
npm install -g @anthropic-ai/claude-code
```

### Permission denied

If you get permission errors, ensure the files are executable:

```bash
chmod +x ~/dev/amplifier/amplifier-anywhere.sh
```

### PATH issues

Verify ~/bin is in your PATH:

```bash
echo $PATH | grep "$HOME/bin"
```

If not, add it as shown above.

## Technical Details

### What happens under the hood

1. `amplifier claude` is a Python Click command
2. It detects if you're in the Amplifier project or an external project
3. It sets appropriate environment variables for external mode
4. It calls `amplifier-anywhere.sh` with the right configuration
5. The shell script activates the virtual environment and launches Claude

### File locations

- **Global command**: `~/bin/amplifier` (symlink to `.venv/bin/amplifier`)
- **Python CLI**: `~/dev/amplifier/amplifier/cli.py`
- **Claude launcher**: `~/dev/amplifier/amplifier/claude_launcher.py`
- **Shell script**: `~/dev/amplifier/amplifier-anywhere.sh` (still used internally)

## Benefits of the New System

1. **Single entry point**: One `amplifier` command for everything
2. **No wrapper scripts**: Direct Python CLI execution
3. **Better error handling**: Python provides clearer error messages
4. **Easier maintenance**: All logic in Python, shell script only for environment setup
5. **Consistent interface**: All commands follow the same pattern