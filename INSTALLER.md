# Amplifier Self-Extracting Installer

## Overview

The Amplifier self-extracting installer is a single-file solution that bundles the entire codebase and automates the setup process for new users. It eliminates the need for GitHub access, manual dependency installation, or complex setup procedures.

## Features

- **Single file distribution** - Everything in one ~624KB shell script
- **Interactive installation** - Prompts for key decisions with sensible defaults
- **Non-interactive mode** - Fully automated with `--yes` flag
- **Cross-platform support** - Works on WSL, Linux, and macOS
- **Smart prerequisites** - Only installs what's missing
- **Resume capability** - Can recover from interrupted installations
- **No GitHub required** - Complete offline installation after download

## Building the Installer

To create a new installer from the current codebase:

```bash
./tools/build_installer.sh
```

This will create `install_amplifier.sh` in the project root.

## Using the Installer

### Quick Start

Share the `install_amplifier.sh` file with users via any method (email, download link, USB drive, etc.)

Users run:
```bash
bash install_amplifier.sh
```

Or make it executable first:
```bash
chmod +x install_amplifier.sh
./install_amplifier.sh
```

### Installation Process

The installer will:

1. **Welcome & Setup** - Show version and platform detection
2. **Choose install directory** - Prompts for location (default: `./amplifier`)
3. **Check prerequisites** - Shows what's installed and what's needed
4. **Confirm installation** - Review and approve what will be installed
5. **Install components**:
   - Python 3.11+ (if needed)
   - UV package manager
   - Node.js and npm (if needed)
   - pnpm package manager
   - Claude CLI (`@anthropic-ai/claude-code`)
6. **Setup Python environment** - Run `make install`
7. **Shell configuration** - Ask permission to update PATH
8. **Launch prompt** - Ask if you want to start Claude Code now

### Interactive Prompts

During installation, you'll see prompts like:

```
📁 Where would you like to install Amplifier?
Installation path [./amplifier]:

🔍 Checking prerequisites...
  ✓ Python 3.11+ found
  ⚠ UV not found (will install)
  ✓ Node.js 20+ found

Continue with installation? [Y/n]:

🐚 Shell configuration
Update shell configuration? [Y/n]:

🚀 Ready to launch Claude Code!
Launch Claude Code now? [Y/n]:
```

Press ENTER at any prompt to accept the default (shown in brackets).

### Command Line Options

```bash
# Run in non-interactive mode (accept all defaults)
./install_amplifier.sh --yes
# or
./install_amplifier.sh -y

# Force reinstall even if already installed
./install_amplifier.sh --force

# Install without launching Claude Code
./install_amplifier.sh --no-launch

# Combine options for fully automated installation
./install_amplifier.sh --yes --no-launch

# Show help
./install_amplifier.sh --help
```

### Custom Installation Directory

The installer will prompt you for the installation directory (default: `./amplifier` in current directory).

You can also set the `AMPLIFIER_HOME` environment variable to skip the prompt:

```bash
AMPLIFIER_HOME=/opt/amplifier ./install_amplifier.sh
```

Or specify a different directory when prompted during interactive installation.

## Platform-Specific Notes

### WSL/Linux

- Uses `apt-get` for system packages (Debian/Ubuntu)
- Falls back to `yum` for Red Hat-based systems
- Requires `sudo` for system package installation

### macOS

- Installs Homebrew if not present
- Uses `brew` for system packages
- Supports both Intel and Apple Silicon

## State Management

The installer tracks progress in `.install_state` file, allowing it to:
- Skip already completed steps
- Resume from failures
- Support re-running without duplicating work

## Troubleshooting

### Installation Failed

Check the error messages - the installer provides clear feedback about what failed.

Common issues:
- **No sudo access**: Install system packages manually first
- **Network issues**: The installer retries downloads 3 times
- **Disk space**: Ensure ~500MB free space for installation

### Resume Installation

Simply run the installer again - it will skip completed steps and continue from where it failed.

### Force Reinstall

Use the `--force` flag to start fresh:
```bash
./install_amplifier.sh --force
```

### Manual Cleanup

To completely remove an installation:
```bash
rm -rf ~/amplifier
rm -rf ~/.cargo/bin/uv  # UV package manager
pnpm remove -g @anthropic-ai/claude-code  # Claude CLI
```

## Non-Interactive Mode

For automated deployments or CI/CD pipelines, use the `--yes` flag:

```bash
# Fully automated installation
./install_amplifier.sh --yes

# Automated with custom directory
AMPLIFIER_HOME=/usr/local/amplifier ./install_amplifier.sh --yes

# Automated without launching Claude
./install_amplifier.sh --yes --no-launch
```

This will:
- Install to `./amplifier` (or `$AMPLIFIER_HOME` if set)
- Accept all prerequisites
- Update shell configuration
- Skip Claude Code launch

## Technical Details

### Architecture

- **Self-extracting script**: Shell script header + embedded tar.gz archive
- **Size**: ~624KB compressed (5MB uncompressed)
- **Compression**: gzip with maximum compression
- **Transform**: Adds `amplifier/` prefix to all extracted files

### Excluded Files

The following are NOT included in the installer:
- `.git/` - Version control
- `.venv/` - Python virtual environment (recreated)
- `node_modules/` - Node packages (reinstalled)
- `__pycache__/` - Python cache files
- `.claude/` - Claude logs and cache
- Test artifacts and temporary files

### Security Considerations

- No sensitive data or credentials included
- No API keys or tokens embedded
- Clean environment created from scratch
- Dependencies installed from official sources

## Development

### Modifying the Installer

1. Edit the installer script template in `tools/build_installer.sh`
2. Update exclusions in `.tarignore` if needed
3. Rebuild: `./tools/build_installer.sh`
4. Test the new installer

### Adding Platform Support

To support additional platforms, modify the platform detection and package installation functions in the installer script template within `build_installer.sh`.

## Support

For issues or questions about the installer, please check:
1. Error messages from the installer (they're designed to be helpful)
2. The `.install_state` file for progress tracking
3. Platform-specific package manager logs

## License

The installer and Amplifier codebase are distributed under the project's license terms.

