---
last_updated: 2025-10-16
status: stable
audience: developer
---

# Module Development Guide

**For developers creating or modifying Amplifier modules.**

This guide covers development workflows from quick fixes to full workspace setups. Assumes familiarity with Amplifier's modular architecture.

For technical specification, see **[Module Resolution Specification](https://github.com/microsoft/amplifier-module-resolution/blob/main/docs/SPECIFICATION.md)**.

---

## Development Workflows

### Scenario 1: Quick Fix to Single Module

**Goal:** Make a small change to one module, test it, commit.

```bash
# Clone module repo
git clone https://github.com/microsoft/amplifier-module-tool-bash
cd amplifier-module-tool-bash

# Make changes
# ... edit code ...

# Test with environment override (temporary)
export AMPLIFIER_MODULE_TOOL_BASH=$(pwd)
cd ~/your-project
amplifier run "test bash changes"

# Back in module repo
cd -
git add .
git commit -m "fix: Handle edge case"
git push origin main
```

**Override clears when terminal closes—no files modified.**

### Scenario 2: Working on Multiple Modules

**Goal:** Work across module boundaries (e.g., tool + provider).

```bash
# Set up workspace
mkdir ~/amplifier-workspace
cd ~/amplifier-workspace

# Clone modules
git clone https://github.com/microsoft/amplifier-module-tool-bash
git clone https://github.com/microsoft/amplifier-module-provider-anthropic

# Create project config
cat > .amplifier/settings.yaml << 'EOF'
sources:
  tool-bash: file://./amplifier-module-tool-bash
  provider-anthropic: file://./amplifier-module-provider-anthropic
EOF

# Work across both
amplifier run --mode chat
# Uses local versions automatically
```

### Scenario 3: Full Dev Workspace

**Goal:** Work on core + CLI + many modules simultaneously.

**Option A: Zero-Config Workspace Convention**

```bash
# Create your workspace directory
mkdir amplifier-workspace && cd amplifier-workspace

# Clone the repos you need
git clone https://github.com/microsoft/amplifier-core
git clone https://github.com/microsoft/amplifier-app-cli
git clone https://github.com/microsoft/amplifier-module-tool-bash
# ... clone other modules as needed

# Use workspace convention for auto-discovery
amplifier module dev init
# Creates .amplifier/modules/ and offers to link modules

# Check status
amplifier module dev status
```

**Option B: Manual Symlinks**

```bash
cd amplifier-workspace
mkdir -p .amplifier/modules

# Symlink modules you're working on
cd .amplifier/modules
ln -s ../../amplifier-module-tool-bash tool-bash
ln -s ../../amplifier-module-tool-filesystem tool-filesystem
cd ../..

# Auto-discovered!
amplifier module status
```

**Option C: Git Submodules (Selective Loading)**

```bash
cd amplifier-workspace/.amplifier/modules

# Add as submodules
git submodule add ../../amplifier-module-tool-bash tool-bash
git submodule add ../../amplifier-module-tool-filesystem tool-filesystem

# Temporarily use remote version (deinit)
git submodule deinit tool-bash
# Now tool-bash uses bundle/remote version

# Bring it back
git submodule update --init tool-bash
```

---

## Module Dev Commands

### Development-Focused CLI

**Pattern:** `amplifier module dev <command>`

Keeps production commands clean while providing dev tools.

```bash
# Initialize workspace
amplifier module dev init
# Creates .amplifier/modules/, offers to link existing modules

# Link module to workspace
amplifier module dev link <module-id> [<path>]
# If path omitted, offers to clone from known sources

# List workspace modules
amplifier module dev list
# Shows initialized vs uninitialized modules

# Show workspace status
amplifier module dev status
# Which modules are in workspace, which are active

# Test module
amplifier module dev test <module-id>
# Runs module's test suite
```

**Example:**

```bash
$ amplifier module dev init

Setting up module workspace in .amplifier/modules/

Found these module repos in parent directory:
  ✓ amplifier-module-tool-bash
  ✓ amplifier-module-tool-filesystem

Link them? [Y/n] y

Creating symlinks:
  tool-bash -> ../../amplifier-module-tool-bash
  tool-filesystem -> ../../amplifier-module-tool-filesystem

Workspace ready! Run 'amplifier module dev status' to verify.
```

---

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Installing UV

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Module Structure

See **[Module Structure Contract](https://github.com/microsoft/amplifier-module-resolution/blob/main/docs/SPECIFICATION.md#module-structure-contract)** for required structure.

---

## Testing Your Module

### Local Testing (No Install)

```bash
cd amplifier-module-tool-bash

# Override with env var
export AMPLIFIER_MODULE_TOOL_BASH=$(pwd)
cd ~/test-project
amplifier run "test bash tool"
```

### Unit Tests

```bash
cd amplifier-module-tool-bash
uv run pytest
uv run pytest --cov
```

### Integration Testing

```bash
# Quick test via dev command
amplifier module dev test tool-bash

# Or create test bundle
cat > test-bundle.md << 'EOF'
---
bundle:
  name: test
  version: 1.0.0

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main#subdirectory=bundles/anchors/bundle.md

tools:
  - module: tool-bash
    source: file:///path/to/your/module

providers:
  - module: provider-mock
---

@anchors:context/system.md
EOF

amplifier run --bundle test-bundle.md "test your module"
```

---

## Creating a New Module

See **[Module Structure Contract](https://github.com/microsoft/amplifier-module-resolution/blob/main/docs/SPECIFICATION.md#module-structure-contract)** for structure requirements.

### Quick Start

```bash
# Create from template (recommended)
amplifier module dev create tool-myfeature

# Or manual setup
mkdir amplifier-module-tool-myfeature
cd amplifier-module-tool-myfeature
uv init --lib
```

### Define Entry Point

```toml
# pyproject.toml
[project]
name = "amplifier-module-tool-myfeature"
requires-python = ">=3.11"
dependencies = ["amplifier-core"]

[project.entry-points."amplifier.modules"]
tool-myfeature = "amplifier_module_tool_myfeature"

[tool.uv.sources.amplifier-core]
git = "https://github.com/microsoft/amplifier-core"
branch = "main"
```

**Module ID must match entry point key** (`tool-myfeature`).

### Implement Protocol

```python
# amplifier_module_tool_myfeature/__init__.py
from amplifier_core.protocols import Tool

class MyFeatureTool(Tool):
    def get_schema(self):
        return {
            "name": "my_feature",
            "description": "Does something useful",
            "input_schema": {
                "type": "object",
                "properties": {
                    "param": {"type": "string"}
                },
                "required": ["param"]
            }
        }

    async def execute(self, **kwargs):
        return {"result": f"Processed: {kwargs['param']}"}
```

### Test and Publish

```bash
# Test locally
export AMPLIFIER_MODULE_TOOL_MYFEATURE=$(pwd)
amplifier run "test my tool"

# Publish to GitHub
git init
git add .
git commit -m "Initial implementation"
git push -u origin main
```

Users reference via git URL in their bundle:

```yaml
tools:
  - module: tool-myfeature
    source: git+https://github.com/you/amplifier-module-tool-myfeature@main
```

---

## Module Workspace Management

### Workspace Convention

**Location:** `.amplifier/modules/<module-id>/`

Modules here are auto-discovered (no config needed).

### Setup with Dev Command

```bash
cd your-dev-workspace
amplifier module dev init
```

Detects module repos in parent directory and offers to link them.

### Manual Setup

**Symlinks (always active):**
```bash
mkdir -p .amplifier/modules
cd .amplifier/modules
ln -s ../../amplifier-module-tool-bash tool-bash
ln -s ../../amplifier-module-tool-filesystem tool-filesystem
```

**Submodules (selective activation):**
```bash
cd .amplifier/modules
git submodule add <repo-url> <module-id>
git submodule update --init <module-id>

# Deactivate temporarily
git submodule deinit <module-id>
```

See **[Workspace Convention](https://github.com/microsoft/amplifier-module-resolution/blob/main/docs/SPECIFICATION.md#workspace-convention)** specification.

---

## Override Strategies

See **[Override Methods](https://github.com/microsoft/amplifier-module-resolution/blob/main/docs/USER_GUIDE.md#override-methods)** for complete reference.

**Quick reference:**

| Method | Scope | Persistence | Use Case |
|--------|-------|-------------|----------|
| Env var | Terminal session | Temporary | Quick debugging |
| Workspace | Project | Permanent | Multi-module dev |
| Project config | Project | Permanent | Team overrides |
| User config | Global | Permanent | Personal forks |
| Bundle source | Bundle-specific | Permanent | Distribution |

---

## Module Development Best Practices

### Keep Modules Focused

One responsibility per module. Avoid coupling.

**Good:** `FileReadTool` - reads files
**Bad:** `FileSystemTool` - reads, writes, watches, manages permissions...

### Follow Protocol Contracts

Implement only what the protocol requires.

See **[Protocol Contracts](https://github.com/microsoft/amplifier-module-resolution/blob/main/docs/SPECIFICATION.md#module-protocol-contract)**.

### Test Behavior, Not Implementation

```python
# Good
async def test_file_read():
    result = await tool.execute(operation="read", path="/data/file.txt")
    assert result["content"] == "expected"

# Bad
async def test_file_read():
    assert tool._buffer is not None  # Testing internals
```

### Document Public Interface

```python
class CustomTool(Tool):
    """One-line summary.

    Detailed description of purpose and usage.

    Example:
        await tool.execute(param="value")
    """
```

---

## Contributing Modules

### Reference Implementations

See microsoft/amplifier-module-* repos:
- https://github.com/microsoft/amplifier-module-tool-filesystem
- https://github.com/microsoft/amplifier-module-tool-bash
- https://github.com/microsoft/amplifier-module-provider-anthropic

### Publishing

```bash
# Standard structure
amplifier-module-{type}-{name}/
├── README.md
├── pyproject.toml
├── LICENSE
├── amplifier_module_*/
└── tests/

# Tag releases
git tag v1.0.0
git push origin v1.0.0
```

Users reference tagged versions:

```yaml
source: git+https://github.com/you/amplifier-module-tool-name@v1.0.0
```

---

## Related Documentation

- **[Module Resolution User Guide](https://github.com/microsoft/amplifier-module-resolution/blob/main/docs/USER_GUIDE.md)** - Customizing module sources
- **[Module Resolution Specification](https://github.com/microsoft/amplifier-module-resolution/blob/main/docs/SPECIFICATION.md)** - Technical specification
- [AMPLIFIER_AS_LINUX_KERNEL.md](./AMPLIFIER_AS_LINUX_KERNEL.md) - Module architecture philosophy
