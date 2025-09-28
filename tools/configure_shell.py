#!/usr/bin/env python
"""Configure shell environment for Amplifier global installation."""

import os
import sys
from pathlib import Path


def get_shell_config_files():
    """Get the appropriate shell configuration files based on the system."""
    home = Path.home()
    config_files = []

    # Check for zsh
    if os.environ.get("SHELL", "").endswith("zsh") or (home / ".zshrc").exists():
        config_files.append(home / ".zshrc")

    # Check for bash
    # On macOS, prefer .bash_profile; on Linux, prefer .bashrc
    if sys.platform == "darwin":
        if (home / ".bash_profile").exists():
            config_files.append(home / ".bash_profile")
        elif (home / ".bashrc").exists():
            config_files.append(home / ".bashrc")
    else:
        if (home / ".bashrc").exists():
            config_files.append(home / ".bashrc")
        elif (home / ".bash_profile").exists():
            config_files.append(home / ".bash_profile")

    # Always update .profile as a fallback for some systems
    if (home / ".profile").exists():
        config_files.append(home / ".profile")

    return config_files


def add_path_to_config(config_file: Path, path_to_add: str):
    """Add a PATH export to a shell configuration file if not already present."""
    export_line = 'export PATH="$HOME/bin:$PATH"'
    pnpm_line = 'export PNPM_HOME="$HOME/.local/share/pnpm"'
    pnpm_path_line = 'export PATH="$PNPM_HOME:$PATH"'

    # Read existing content
    if config_file.exists():
        content = config_file.read_text()
    else:
        content = ""

    modified = False
    lines_to_add = []

    # Check and add ~/bin to PATH
    if "$HOME/bin" not in content and "~/bin" not in content:
        lines_to_add.append(f"\n# Added by Amplifier installer\n{export_line}")
        modified = True

    # Check and add pnpm configuration
    if "PNPM_HOME" not in content:
        lines_to_add.append(f"{pnpm_line}\n{pnpm_path_line}")
        modified = True

    if modified:
        # Append to file
        with config_file.open("a") as f:
            if lines_to_add:
                f.write("\n".join(lines_to_add) + "\n")
        print(f"   ✅ Updated {config_file}")
    else:
        print(f"   ✓ {config_file} already configured")


def main():
    """Configure shell environment for Amplifier."""
    config_files = get_shell_config_files()

    if not config_files:
        print("   ⚠️  No shell configuration files found.")
        print("   Please manually add ~/bin to your PATH.")
        return

    for config_file in config_files:
        add_path_to_config(config_file, "$HOME/bin")

    # Check if ~/bin is already in current PATH
    current_path = os.environ.get("PATH", "")
    home_bin = os.path.expanduser("~/bin")

    if home_bin not in current_path:
        print("\n   ⚠️  ~/bin is not in your current PATH.")
        print("   The changes will take effect after you reload your shell configuration.")


if __name__ == "__main__":
    main()
