# Amplifier Development Environment

The orchestrator repository for developing the Amplifier ecosystem - a modular AI-powered development platform.

## Overview

`amplifier-dev` provides a unified development environment for working across multiple Amplifier modules. It orchestrates the setup, testing, and integration of the entire Amplifier ecosystem, enabling developers to work seamlessly across module boundaries.

## Architecture

### Current State: Multi-Directory Development

The development environment currently uses a multi-directory structure where each Amplifier module lives in a sibling directory:

```
amplifier-dev/           # This repository - orchestrator and dev tools
├── install_all.py       # Auto-discovery installer
├── README.md           # This file
└── ...

amplifier/              # Core Amplifier package
amplifier-core/         # Core utilities and shared components
amplifier-**/           # Additional modules (auto-discovered)
```

## Quick Start

### Prerequisites

- Python 3.11+
- uv package manager: `pip install uv`

### Installation

1. **Clone the amplifier-dev repository**:

```bash
git clone https://github.com/microsoft/amplifier-dev
cd amplifier-dev
```

2. **Run the installer** (creates virtual environment automatically):

```bash
python install_all.py
```

The installer will:

- Create a virtual environment if needed
- Guide you through activation
- Auto-discover and install all amplifier modules
- Handle dependencies automatically

3. **Verify installation**:

```bash
amplifier --version
amplifier list-modes
```

4. **Set up API keys** (for AI-powered tools):

```bash
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
```

5. **Test with a demo**:

```bash
amplifier run demo ultra_think "What is consciousness?"
```

### Installation Options

```bash
# Check what would be installed without actually installing
python install_all.py --check-only

# Install with verbose output
python install_all.py --verbose

# Install independent modules in parallel
python install_all.py --parallel

# Install as non-editable packages
python install_all.py --no-editable
```

## Development Workflow

### Working Across Modules

The development environment enables seamless cross-module development:

1. **Make changes** in any module directory
2. **Test locally** - changes are immediately reflected (editable installs)
3. **Run integration tests** to verify cross-module compatibility
4. **Commit changes** in each module's repository

### Adding New Modules

New modules are automatically discovered if they follow the naming convention:

1. Create a new directory: `amplifier-yourmodule/`
2. Add a `pyproject.toml` file with proper metadata
3. Run `python install_all.py` to include it in the environment

### Module Dependencies

Modules can depend on each other through standard Python dependencies:

```toml
# In amplifier-yourmodule/pyproject.toml
[project]
dependencies = [
    "amplifier-core>=0.1.0",
    "amplifier>=0.2.0",
]

# For local development (optional)
[tool.uv.sources]
amplifier-core = { path = "../amplifier-core", editable = true }
amplifier = { path = "../amplifier", editable = true }
```

## Module Structure

Each Amplifier module follows the "bricks and studs" philosophy:

- **Brick**: Self-contained module with one clear responsibility
- **Studs**: Well-defined public interfaces (the contract)

### Core Modules

1. **amplifier-core**: Shared utilities and base components
2. **amplifier**: Main Amplifier CLI and framework

### Extension Modules

Additional `amplifier-*` modules extend functionality:

- Domain-specific tools
- Integration adapters
- Specialized agents
- Custom scenarios

## Testing

### Unit Tests

Run tests within each module:

```bash
cd ../amplifier
make test
```

## Advanced Usage

### Custom Module Discovery

The installer can be configured to use a different base directory:

```bash
python install_all.py --base-dir /path/to/modules
```
