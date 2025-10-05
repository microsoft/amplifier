#!/usr/bin/env python3
"""
Prepare Amplifier modules for independent GitHub repositories.

This script updates all pyproject.toml files to use GitHub dependencies
instead of local file:// dependencies, making them ready for independent
repository deployment.
"""

import re
from pathlib import Path

def update_dependency(dep_line):
    """Convert local file:// dependency to GitHub dependency."""
    if "amplifier-core @" in dep_line and "file://" in dep_line:
        # For independent repos, use GitHub URL
        return '    "amplifier-core @ git+https://github.com/microsoft/amplifier-core.git",\n'
    return dep_line

def prepare_pyproject_for_github(file_path):
    """Update a pyproject.toml file for GitHub deployment."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    updated_lines = []
    in_dependencies = False

    for line in lines:
        if line.strip().startswith("dependencies = ["):
            in_dependencies = True
        elif in_dependencies and line.strip() == "]":
            in_dependencies = False

        if in_dependencies:
            line = update_dependency(line)

        updated_lines.append(line)

    # Write to a new file with .github suffix
    output_path = file_path.parent / f"{file_path.stem}.github{file_path.suffix}"
    with open(output_path, 'w') as f:
        f.writelines(updated_lines)

    return output_path

def create_module_readme(module_dir):
    """Create or update README for a module."""
    module_name = module_dir.name
    readme_path = module_dir / "README.md"

    # Extract human-readable name
    readable_name = module_name.replace("amplifier-mod-", "").replace("-", " ").title()
    if module_name.startswith("amplifier-mod-llm"):
        readable_name = module_name.replace("amplifier-mod-llm-", "").upper() + " LLM Provider"
    elif module_name.startswith("amplifier-mod-tool"):
        readable_name = module_name.replace("amplifier-mod-tool-", "").replace("_", " ").title() + " Tool"
    elif module_name.startswith("amplifier-mod-agent"):
        readable_name = "Agent Registry Module"
    elif module_name == "amplifier-mod-philosophy":
        readable_name = "Philosophy Module"

    content = f"""# {readable_name}

An Amplifier module providing {readable_name.lower()} functionality.

## Installation

### From GitHub (when published as independent repository)
```bash
# Install core dependency first
pip install git+https://github.com/microsoft/amplifier-core.git

# Install this module
pip install git+https://github.com/microsoft/{module_name}.git
```

### For Development
```bash
# Clone repositories
git clone https://github.com/microsoft/amplifier-core.git
git clone https://github.com/microsoft/{module_name}.git

# Install in development mode
cd amplifier-core && pip install -e . && cd ..
cd {module_name} && pip install -e . && cd ..
```

## Usage

This module is automatically discovered by the Amplifier kernel when installed.
Use it through the Amplifier CLI:

```bash
# List available modules
amplifier list-modules

# Use in a mode
amplifier run --modules {module_name.replace("-", "_")}
```

## Module Interface

This module implements the `AmplifierModule` interface and registers with the kernel
via Python entry points.

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Check code quality
ruff check .
```

## License

MIT License - See LICENSE file for details.
"""

    with open(readme_path, 'w') as f:
        f.write(content)

    return readme_path

def main():
    print("🚀 Preparing Amplifier modules for GitHub deployment")
    print("=" * 60)

    # Find all modules
    modules = list(Path.cwd().glob("amplifier*/pyproject.toml"))

    if not modules:
        print("❌ No amplifier modules found in current directory")
        return

    print(f"\n📦 Found {len(modules)} modules to prepare:")
    for module_path in modules:
        print(f"   • {module_path.parent.name}")

    print("\n" + "=" * 60)
    print("Creating GitHub-ready configurations...")
    print()

    for module_path in modules:
        module_dir = module_path.parent
        module_name = module_dir.name

        print(f"📝 {module_name}:")

        # Skip amplifier-core (it doesn't depend on itself)
        if module_name != "amplifier-core":
            # Create GitHub version of pyproject.toml
            github_path = prepare_pyproject_for_github(module_path)
            print(f"   ✓ Created {github_path.name}")

        # Create/update README if it doesn't exist or is minimal
        readme_path = module_dir / "README.md"
        if not readme_path.exists() or readme_path.stat().st_size < 500:
            created_readme = create_module_readme(module_dir)
            print(f"   ✓ Created README.md")

    print("\n" + "=" * 60)
    print("✅ Preparation complete!")
    print()
    print("Next steps:")
    print("1. Review the generated .github.toml files")
    print("2. When ready to deploy, rename .github.toml to .toml")
    print("3. Create GitHub repositories for each module")
    print("4. Push each module to its respective repository")
    print()
    print("Repository structure:")
    print("  • github.com/microsoft/amplifier-core")
    print("  • github.com/microsoft/amplifier")
    print("  • github.com/microsoft/amplifier-mod-llm-openai")
    print("  • github.com/microsoft/amplifier-mod-llm-claude")
    print("  • github.com/microsoft/amplifier-mod-tool-ultra_think")
    print("  • github.com/microsoft/amplifier-mod-tool-blog_generator")
    print("  • github.com/microsoft/amplifier-mod-philosophy")
    print("  • github.com/microsoft/amplifier-mod-agent-registry")

if __name__ == "__main__":
    main()