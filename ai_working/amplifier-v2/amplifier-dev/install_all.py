#!/usr/bin/env python3
"""
Install all Amplifier modules for development.
Run from the amplifier-dev directory.

Automatically discovers and installs all amplifier* modules:
- amplifier-core is installed first (foundation)
- amplifier is installed last (depends on others)
- All other modules installed in between
"""

import subprocess
import sys
from pathlib import Path

# ANSI color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

def run_command(cmd, cwd=None):
    """Run a command and return success status."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"{RED}Error running: {cmd}{NC}")
            print(result.stderr)
            return False
        return True
    except Exception as e:
        print(f"{RED}Exception running command: {e}{NC}")
        return False

def discover_modules():
    """Discover all amplifier modules in the current directory."""
    modules = []

    # Find all directories starting with "amplifier" that contain pyproject.toml
    for path in Path.cwd().iterdir():
        if path.is_dir() and path.name.startswith("amplifier"):
            pyproject = path / "pyproject.toml"
            if pyproject.exists():
                modules.append(path.name)

    # Sort with special rules:
    # 1. amplifier-core first
    # 2. amplifier last
    # 3. Everything else alphabetically in between
    core_modules = []
    main_module = []
    other_modules = []

    for module in modules:
        if module == "amplifier-core":
            core_modules.append(module)
        elif module == "amplifier":
            main_module.append(module)
        else:
            other_modules.append(module)

    # Sort the middle modules alphabetically for consistency
    other_modules.sort()

    return core_modules + other_modules + main_module

def get_module_description(module_dir):
    """Extract a simple description from the module name."""
    name = module_dir.replace("amplifier-", "").replace("-", " ")

    # Special cases for better descriptions
    descriptions = {
        "amplifier-core": "Core kernel",
        "amplifier": "Main CLI",
        "amplifier-mod-llm-openai": "OpenAI provider",
        "amplifier-mod-llm-claude": "Claude provider",
        "amplifier-mod-tool-ultra_think": "UltraThink tool",
        "amplifier-mod-tool-blog_generator": "Blog Generator tool",
        "amplifier-mod-philosophy": "Philosophy module",
        "amplifier-mod-agent-registry": "Agent Registry",
    }

    return descriptions.get(module_dir, name.title())

def main():
    print(f"🚀 Installing Amplifier Development Environment")
    print("=" * 50)

    # Check we're in the right directory
    if not Path("amplifier-core").exists() or not Path("amplifier").exists():
        print(f"{RED}❌ Error: This script must be run from an amplifier-dev directory{NC}")
        print(f"   Current directory: {Path.cwd()}")
        sys.exit(1)

    # Discover modules automatically
    modules = discover_modules()

    if not modules:
        print(f"{RED}❌ No amplifier modules found in current directory{NC}")
        sys.exit(1)

    print(f"\n📦 Found {len(modules)} modules to install:")
    for module in modules:
        print(f"   • {module}")

    failed = []

    for i, module_dir in enumerate(modules, 1):
        description = get_module_description(module_dir)
        print(f"\n{YELLOW}Step {i}/{len(modules)}: Installing {description}{NC}")
        print("-" * 40)

        if not Path(module_dir).exists():
            print(f"{RED}❌ Directory not found: {module_dir}{NC}")
            failed.append(module_dir)
            continue

        # Install with uv in editable mode
        if not run_command(f"uv pip install -e .", cwd=module_dir):
            failed.append(module_dir)
            print(f"{RED}❌ Failed to install {module_dir}{NC}")
        else:
            print(f"{GREEN}✓ {description} installed{NC}")

    # Summary
    print("\n" + "=" * 50)
    if failed:
        print(f"{RED}⚠️  Installation completed with errors:{NC}")
        for module in failed:
            print(f"  - {module}")
        print(f"\nYou may need to manually fix these modules.")
        sys.exit(1)
    else:
        print(f"{GREEN}✅ Installation complete!{NC}")

    print("""
You can now use the Amplifier CLI:
  amplifier --help              # Show help
  amplifier list-modes          # List available modes
  amplifier run demo            # Load demo mode
  amplifier interactive -m demo # Interactive mode

Remember to set your API keys:
  export OPENAI_API_KEY='your-key'
  export ANTHROPIC_API_KEY='your-key'
""")

if __name__ == "__main__":
    main()