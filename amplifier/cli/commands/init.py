"""
Init command for Amplifier CLI v3.

This command initializes a new project with the required directory structure,
configuration files, and AI context documentation.

Contract:
    - Creates .claude/ directory with subdirectories
    - Creates .amplifier/ for metadata
    - Initializes manifest.json
    - Creates default settings.json
    - Creates project AI context files (CLAUDE.md, AGENTS.md, DISCOVERIES.md)
    - Creates ai_context/ directory with philosophy documentation
    - Optionally creates .mcp.json if not exists
"""

import json
from pathlib import Path

import click

from amplifier.cli.core import create_manifest
from amplifier.cli.core import ensure_directories
from amplifier.cli.core import get_claude_dir
from amplifier.cli.core import get_manifest_path
from amplifier.cli.core import get_settings_path
from amplifier.cli.core import save_manifest
from amplifier.cli.core import validate_paths
from amplifier.cli.core.decorators import handle_errors
from amplifier.cli.core.decorators import log_command
from amplifier.cli.core.errors import ConfigurationError
from amplifier.cli.core.file_utils import copy_with_permissions
from amplifier.cli.core.file_utils import get_package_data_path
from amplifier.cli.core.output import get_output_manager
from amplifier.cli.models import Settings


@click.command()
@click.option("--force", is_flag=True, help="Force initialization even if directories exist")
@click.option("--repair", is_flag=True, help="Attempt to repair corrupted configuration")
@click.option("--merge", is_flag=True, help="Merge Amplifier content into existing files")
@handle_errors()
@log_command("init")
@click.pass_context
def cmd(ctx: click.Context, force: bool, repair: bool, merge: bool) -> None:
    """Initialize Amplifier project structure.

    Creates .claude/ and .amplifier/ directories with required structure.
    """
    output = ctx.obj.get("output", get_output_manager())

    # Show initialization header
    output.info("🚀 Initializing Amplifier project...")

    # Check if already initialized
    claude_dir = get_claude_dir()
    manifest_path = get_manifest_path()

    if manifest_path.exists() and not (force or repair or merge):
        output.warning(
            "Project already initialized",
            detail="Use --force to reinitialize, --repair to fix issues, or --merge to update existing files",
        )
        return

    # Handle repair mode
    if repair:
        output.info("🔧 Running in repair mode...")
        _repair_project(output)
        return

    # Show what will be created
    output.section_header("Creating Project Structure")

    # Create directory structure
    with output.spinner("Creating directories..."):
        ensure_directories()

    # Show created directories
    for directory in ["agents", "tools", "commands", "mcp-servers"]:
        dir_path = claude_dir / directory
        if dir_path.exists():
            output.success(f"Created .claude/{directory}/")

    # Create amplifier directory
    amplifier_dir = Path(".amplifier")
    if amplifier_dir.exists():
        output.success("Created .amplifier/")

    # Create AI context files
    output.section_header("Creating AI Context Files")
    with output.spinner("Creating project documentation..."):
        created_files, skipped_files = _create_project_files(force=force, merge=merge)

    for file_path, action in created_files:
        if action == "created":
            output.success(f"Created {file_path}")
        elif action == "merged":
            output.success(f"Merged content into {file_path}")
        elif action == "preserved":
            output.info(f"Preserved existing {file_path}")

    # Report skipped files if any
    if skipped_files and not merge:
        output.warning(
            f"Skipped {len(skipped_files)} existing file(s)",
            detail="Use --merge to update these files with Amplifier content",
        )
        for file_path in skipped_files:
            output.info(f"  • {file_path} (exists, not updated)")

    # Create and save manifest
    with output.spinner("Creating manifest..."):
        manifest = create_manifest()
        save_manifest(manifest)
    output.success("Created manifest.json", detail=str(manifest_path))

    # Create default settings.json only if it doesn't exist
    # (init_new.py may have already created the real one from package data)
    settings_path = get_settings_path()
    if not settings_path.exists():
        with output.spinner("Creating settings..."):
            settings = Settings(
                defaults={
                    "auto_update": False,
                    "resource_source": "local",  # For Phase 1
                }
            )
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings.model_dump(mode="json"), f, indent=2)
        output.success("Created .claude/settings.json", detail=str(settings_path))

    # Validate paths were created correctly
    try:
        with output.spinner("Validating structure..."):
            validate_paths()
    except AssertionError as e:
        output.error(f"Initialization validation failed: {e}")
        raise ConfigurationError("Failed to create project structure correctly", config_file=str(manifest_path)) from e

    # Show success message with next steps
    output.panel(
        "✨ [bold green]Project initialized successfully![/bold green]\n\n"
        "[bold]Created:[/bold]\n"
        "  • Project structure (.claude/, .amplifier/)\n"
        "  • AI context files (CLAUDE.md, AGENTS.md, DISCOVERIES.md)\n"
        "  • Philosophy documentation (ai_context/)\n\n"
        "[bold]Next steps:[/bold]\n"
        "  • Review and customize CLAUDE.md for project-specific instructions\n"
        "  • Run [cyan]amplifier list --available[/cyan] to see available resources\n"
        "  • Run [cyan]amplifier install agents[/cyan] to install all agents\n"
        "  • Run [cyan]amplifier --help[/cyan] for more commands",
        title="[bold]Initialization Complete[/bold]",
        style="green",
    )

    # Show created paths in debug mode
    if ctx.obj.get("debug"):
        output.debug(f"Claude directory: {claude_dir}")
        output.debug(f"Manifest: {manifest_path}")
        output.debug(f"Settings: {settings_path}")


def _create_project_files(force: bool = False, merge: bool = False) -> tuple[list[tuple[str, str]], list[str]]:
    """Create essential project files for AI assistants.

    This function now copies real files from package data if available,
    otherwise falls back to creating template content.
    """
    # Use the implementation that copies real files from package data
    return _create_project_files_from_package_data(force, merge)


def _create_project_files_original(force: bool = False, merge: bool = False) -> tuple[list[tuple[str, str]], list[str]]:
    """Create essential project files for AI assistants.

    Args:
        force: Whether to overwrite existing files
        merge: Whether to merge content into existing files

    Returns:
        Tuple of (created_files, skipped_files) where:
        - created_files is list of (file_path, action) where action is "created", "merged", or "preserved"
        - skipped_files is list of file paths that exist but weren't updated
    """
    created_files = []
    skipped_files = []
    project_root = Path(".")

    # Create CLAUDE.md
    claude_md_path = project_root / "CLAUDE.md"
    amplifier_claude_section = """\n\n## Amplifier Resources

This project uses Amplifier CLI to manage Claude Code resources.

### Available Commands

- `amplifier list` - List available and installed resources
- `amplifier install agents <name>` - Install specific agents
- `amplifier update` - Update installed resources
- `amplifier remove <type> <name>` - Remove installed resources

### Project Structure

- `.claude/` - Claude Code resources (agents, tools, commands, mcp-servers)
- `.amplifier/` - Amplifier metadata and configuration
- `AGENTS.md` - Guidance for AI assistants
- `DISCOVERIES.md` - Documentation of solved problems and patterns
"""

    if not claude_md_path.exists():
        if force:
            # Create new file with full template
            claude_md_content = (
                """# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project-Specific Instructions

<!-- Add your project-specific instructions here -->

## Build Commands

- Install dependencies: `# Add your install command`
- Run tests: `# Add your test command`
- Build project: `# Add your build command`

## Code Style Guidelines

<!-- Add your project's code style guidelines -->
"""
                + amplifier_claude_section
            )
            claude_md_path.write_text(claude_md_content)
            created_files.append(("CLAUDE.md", "created"))
        else:
            # File doesn't exist, create it
            claude_md_content = (
                """# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project-Specific Instructions

<!-- Add your project-specific instructions here -->

## Build Commands

- Install dependencies: `# Add your install command`
- Run tests: `# Add your test command`
- Build project: `# Add your build command`

## Code Style Guidelines

<!-- Add your project's code style guidelines -->
"""
                + amplifier_claude_section
            )
            claude_md_path.write_text(claude_md_content)
            created_files.append(("CLAUDE.md", "created"))
    elif force:
        # Force overwrite existing file
        claude_md_content = (
            """# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project-Specific Instructions

<!-- Add your project-specific instructions here -->

## Build Commands

- Install dependencies: `# Add your install command`
- Run tests: `# Add your test command`
- Build project: `# Add your build command`

## Code Style Guidelines

<!-- Add your project's code style guidelines -->
"""
            + amplifier_claude_section
        )
        claude_md_path.write_text(claude_md_content)
        created_files.append(("CLAUDE.md", "created"))
    elif merge:
        # Merge: append Amplifier section if not already present
        existing_content = claude_md_path.read_text()
        if "## Amplifier Resources" not in existing_content:
            merged_content = existing_content.rstrip() + amplifier_claude_section
            claude_md_path.write_text(merged_content)
            created_files.append(("CLAUDE.md", "merged"))
        else:
            created_files.append(("CLAUDE.md", "preserved"))
    else:
        # File exists and no force or merge
        skipped_files.append("CLAUDE.md")
        created_files.append(("CLAUDE.md", "preserved"))

    # Create AGENTS.md
    agents_md_path = project_root / "AGENTS.md"
    amplifier_agents_section = """\n\n## Amplifier Agent Management

### Installing Agents

- `amplifier install agents` - Install all available agents
- `amplifier install agents zen-architect bug-hunter` - Install specific agents
- `amplifier list agents --installed` - Show installed agents
- `amplifier remove agents <name>` - Remove specific agents

### Using Agents in Claude Code

After installing agents, they are available in Claude Code:
- Type `@` to see available agents
- Agents provide specialized expertise for different tasks
- See `.claude/agents/` for installed agent definitions
"""

    if not agents_md_path.exists():
        # Create new file
        agents_md_content = (
            """# AI Assistant Guidance

This file provides guidance to AI assistants when working with code in this repository.

## Important: Consult DISCOVERIES.md

Before implementing solutions to complex problems:
1. **Check DISCOVERIES.md** for similar issues that have already been solved
2. **Update DISCOVERIES.md** when you encounter non-obvious problems

## Available Specialized Agents

See `.claude/AGENTS_CATALOG.md` for the full list of available specialized agents.

## Response Guidelines

### Professional Communication
- Focus on technical merit and trade-offs
- Provide honest technical assessment
- Avoid unnecessary agreement or praise

### Zero-BS Principle
- Build working code, not placeholders
- No unnecessary stubs or TODOs
- Implement or don't include

## Development Approach

### Vertical Slices
- Implement complete end-to-end functionality
- Start with core user journeys
- Add features horizontally after core flows work

### Testing Strategy
- Test after code changes
- Run type checks and linters
- Verify basic functionality
"""
            + amplifier_agents_section
        )
        agents_md_path.write_text(agents_md_content)
        created_files.append(("AGENTS.md", "created"))
    elif force:
        # Force overwrite
        agents_md_content = (
            """# AI Assistant Guidance

This file provides guidance to AI assistants when working with code in this repository.

## Important: Consult DISCOVERIES.md

Before implementing solutions to complex problems:
1. **Check DISCOVERIES.md** for similar issues that have already been solved
2. **Update DISCOVERIES.md** when you encounter non-obvious problems

## Available Specialized Agents

See `.claude/AGENTS_CATALOG.md` for the full list of available specialized agents.

## Response Guidelines

### Professional Communication
- Focus on technical merit and trade-offs
- Provide honest technical assessment
- Avoid unnecessary agreement or praise

### Zero-BS Principle
- Build working code, not placeholders
- No unnecessary stubs or TODOs
- Implement or don't include

## Development Approach

### Vertical Slices
- Implement complete end-to-end functionality
- Start with core user journeys
- Add features horizontally after core flows work

### Testing Strategy
- Test after code changes
- Run type checks and linters
- Verify basic functionality
"""
            + amplifier_agents_section
        )
        agents_md_path.write_text(agents_md_content)
        created_files.append(("AGENTS.md", "created"))
    elif merge:
        # Merge content
        existing_content = agents_md_path.read_text()
        if "## Amplifier Agent Management" not in existing_content:
            merged_content = existing_content.rstrip() + amplifier_agents_section
            agents_md_path.write_text(merged_content)
            created_files.append(("AGENTS.md", "merged"))
        else:
            created_files.append(("AGENTS.md", "preserved"))
    else:
        skipped_files.append("AGENTS.md")
        created_files.append(("AGENTS.md", "preserved"))

    # Create DISCOVERIES.md
    discoveries_md_path = project_root / "DISCOVERIES.md"
    discoveries_md_content = """# DISCOVERIES.md

This file documents non-obvious problems, solutions, and patterns discovered during development.

## Format for New Entries

When adding a new discovery, use this format:

```markdown
## [Brief Description] (YYYY-MM-DD)

### Issue
[Describe what problem was encountered]

### Root Cause
[Explain why the problem occurred]

### Solution
[Document how the problem was solved]

### Key Learnings
[List important takeaways]

### Prevention
[Suggest how to avoid this issue in the future]
```

---

<!-- Add new discoveries below this line -->
"""

    if not discoveries_md_path.exists() or force:
        discoveries_md_path.write_text(discoveries_md_content)
        created_files.append(("DISCOVERIES.md", "created"))
    elif merge:
        # DISCOVERIES.md doesn't need merging as it's append-only
        created_files.append(("DISCOVERIES.md", "preserved"))
    else:
        skipped_files.append("DISCOVERIES.md")
        created_files.append(("DISCOVERIES.md", "preserved"))

    # Create ai_context directory and philosophy files
    ai_context_dir = project_root / "ai_context"
    ai_context_dir.mkdir(exist_ok=True)

    # Create IMPLEMENTATION_PHILOSOPHY.md
    impl_philosophy_path = ai_context_dir / "IMPLEMENTATION_PHILOSOPHY.md"
    if not impl_philosophy_path.exists() or force:
        impl_philosophy_content = """# Implementation Philosophy

This document outlines the core implementation philosophy for this project.

## Core Philosophy

### Ruthless Simplicity
- Keep everything as simple as possible, but no simpler
- Start minimal, grow as needed
- Avoid future-proofing for hypothetical requirements
- Question everything that adds complexity

### Build Working Code
- Every function must work or not exist
- No placeholders or stubs without implementation
- Focus on what's needed now
- Trust in emergence over planning

## Development Approach

### Vertical Slices
- Implement complete end-to-end functionality
- One working feature > multiple partial features
- Get data flowing through all layers early

### Iterative Implementation
- 80/20 principle: High-value, low-effort features first
- Validate with real usage before enhancing
- Be willing to refactor as patterns emerge

## Decision Framework

When faced with implementation decisions:
1. **Necessity**: "Do we actually need this right now?"
2. **Simplicity**: "What's the simplest way to solve this?"
3. **Directness**: "Can we solve this more directly?"
4. **Value**: "Does the complexity add proportional value?"
5. **Maintenance**: "How easy will this be to change later?"

## Remember

- It's easier to add complexity later than to remove it
- Code you don't write has no bugs
- Favor clarity over cleverness
- The best code is often the simplest
"""
        impl_philosophy_path.write_text(impl_philosophy_content)
        created_files.append(("ai_context/IMPLEMENTATION_PHILOSOPHY.md", "created"))
    elif force:
        impl_philosophy_path.write_text(impl_philosophy_content)
        created_files.append(("ai_context/IMPLEMENTATION_PHILOSOPHY.md", "created"))
    else:
        created_files.append(("ai_context/IMPLEMENTATION_PHILOSOPHY.md", "preserved"))

    # Create MODULAR_DESIGN_PHILOSOPHY.md
    modular_philosophy_path = ai_context_dir / "MODULAR_DESIGN_PHILOSOPHY.md"
    if not modular_philosophy_path.exists() or force:
        modular_philosophy_content = """# Modular Design Philosophy

Building software with AI using a modular block approach.

## Core Concepts

### Think "Bricks & Studs"
- **A brick** = Self-contained directory with ONE clear responsibility
- **A stud** = Public contract (functions, API, data model) others connect to
- **Regeneratable** = Can be rebuilt from spec without breaking connections
- **Isolated** = All code, tests, fixtures inside the brick's folder

## Implementation Process

### 1. Start with the Contract
- Define purpose, inputs, outputs, side-effects
- Keep specifications small enough for one AI prompt
- Document the public interface clearly

### 2. Build in Isolation
- Put all code, tests, and fixtures in the module directory
- Expose only the contract via __all__ or interface
- No other module may import internals

### 3. Regenerate, Don't Patch
- When changes are needed, regenerate the whole module
- If contract changes, regenerate all dependent modules
- Prefer regeneration over line-by-line edits

## Module Structure

```
module_name/
├── __init__.py       # Public interface
├── README.md         # Contract specification
├── core.py          # Main implementation
├── models.py        # Data models
├── utils.py         # Internal utilities
└── tests/           # Module tests
    ├── test_core.py
    └── fixtures/
```

## Quality Criteria

### Self-Containment
- All logic inside module directory
- No reaching into other modules' internals
- Tests run without external setup
- Clear boundary between public/private

### Contract Clarity
- Single responsibility stated
- All inputs/outputs typed
- Side effects documented
- Error cases defined

## The Human Role

- **Architects**: Define vision and specifications
- **Quality Inspectors**: Validate behavior, not code
- **Work at specification level**: Design requirements, not implementation
- **Test outcomes**: Focus on whether it works, not how

## Building in Parallel

- Generate multiple solutions simultaneously
- Test variants side by side
- Learn from each approach
- Iterate rapidly based on results
"""
        modular_philosophy_path.write_text(modular_philosophy_content)
        created_files.append(("ai_context/MODULAR_DESIGN_PHILOSOPHY.md", "created"))
    elif force:
        modular_philosophy_path.write_text(modular_philosophy_content)
        created_files.append(("ai_context/MODULAR_DESIGN_PHILOSOPHY.md", "created"))
    else:
        created_files.append(("ai_context/MODULAR_DESIGN_PHILOSOPHY.md", "preserved"))

    # Create .mcp.json if it doesn't exist
    mcp_json_path = project_root / ".mcp.json"
    if not mcp_json_path.exists():
        mcp_json_content = {
            "mcpServers": {
                "example": {
                    "comment": "Add your MCP server configurations here",
                    "command": "example-server",
                    "args": [],
                    "env": {},
                }
            }
        }
        with open(mcp_json_path, "w", encoding="utf-8") as f:
            json.dump(mcp_json_content, f, indent=2)
        created_files.append((".mcp.json", "created"))
    else:
        created_files.append((".mcp.json", "preserved"))

    return created_files, skipped_files


def _create_project_files_from_package_data(
    force: bool = False, merge: bool = False
) -> tuple[list[tuple[str, str]], list[str]]:
    """Create essential project files by copying from package data.

    Args:
        force: Whether to overwrite existing files
        merge: Whether to merge content into existing files

    Returns:
        Tuple of (created_files, skipped_files)
    """
    created_files = []
    skipped_files = []
    project_root = Path(".")

    # Files to copy from package data
    files_to_copy = [
        ("CLAUDE.md", "CLAUDE.md"),
        ("AGENTS.md", "AGENTS.md"),
        ("DISCOVERIES.md", "DISCOVERIES.md"),
    ]

    # Copy main documentation files
    for source_name, target_name in files_to_copy:
        source_path = get_package_data_path(source_name)
        target_path = project_root / target_name

        if not source_path.exists():
            # Fall back to template creation if package data doesn't exist
            continue

        if target_path.exists() and not force and not merge:
            skipped_files.append(target_name)
            created_files.append((target_name, "preserved"))
        else:
            if target_path.exists() and merge and target_name == "CLAUDE.md":
                # For CLAUDE.md, merge content
                existing_content = target_path.read_text()
                if "## Amplifier Resources" not in existing_content:
                    amplifier_section = """\n\n## Amplifier Resources

This project uses Amplifier CLI to manage Claude Code resources.

### Available Commands

- `amplifier list` - List available and installed resources
- `amplifier install agents <name>` - Install specific agents
- `amplifier update` - Update installed resources
- `amplifier remove <type> <name>` - Remove installed resources

### Project Structure

- `.claude/` - Claude Code resources (agents, tools, commands, mcp-servers)
- `.amplifier/` - Amplifier metadata and configuration
- `AGENTS.md` - Guidance for AI assistants
- `DISCOVERIES.md` - Documentation of solved problems and patterns
"""
                    merged_content = existing_content.rstrip() + amplifier_section
                    target_path.write_text(merged_content)
                    created_files.append((target_name, "merged"))
                else:
                    created_files.append((target_name, "preserved"))
            else:
                # Copy the file (force=True or file doesn't exist)
                copy_with_permissions(source_path, target_path)
                created_files.append((target_name, "created"))

    # Copy .claude directory with tools and commands from repo
    claude_source = get_package_data_path(".claude")
    claude_target = project_root / ".claude"

    if claude_source.exists():
        # Copy specific subdirectories we want to include
        subdirs = ["tools", "commands"]

        for subdir in subdirs:
            source_subdir = claude_source / subdir
            target_subdir = claude_target / subdir

            if not source_subdir.exists():
                continue

            target_subdir.mkdir(parents=True, exist_ok=True)

            # Copy files preserving permissions
            for file in source_subdir.iterdir():
                if file.is_file() and not file.name.startswith("."):
                    target_file = target_subdir / file.name

                    if target_file.exists() and not force:
                        skipped_files.append(str(target_file.relative_to(project_root)))
                    else:
                        copy_with_permissions(file, target_file)
                        created_files.append((str(target_file.relative_to(project_root)), "created"))

    # Copy settings.json from package data
    settings_source = claude_source / "settings.json" if claude_source.exists() else None
    settings_target = claude_target / "settings.json"

    if settings_source and settings_source.exists():
        if not settings_target.exists() or force:
            settings_target.parent.mkdir(parents=True, exist_ok=True)
            copy_with_permissions(settings_source, settings_target)
            created_files.append((".claude/settings.json", "created"))
        else:
            created_files.append((".claude/settings.json", "preserved"))

    # Create ai_context directory structure
    ai_context_dir = project_root / "ai_context"
    ai_context_dir.mkdir(exist_ok=True)

    # Copy philosophy files if they exist in package data
    philosophy_files = ["ai_context/IMPLEMENTATION_PHILOSOPHY.md", "ai_context/MODULAR_DESIGN_PHILOSOPHY.md"]

    for rel_path in philosophy_files:
        source_path = get_package_data_path(rel_path)
        target_path = project_root / rel_path

        if source_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if not target_path.exists() or force:
                copy_with_permissions(source_path, target_path)
                created_files.append((rel_path, "created"))
            else:
                created_files.append((rel_path, "preserved"))

    # Create .mcp.json if it doesn't exist
    mcp_json_path = project_root / ".mcp.json"
    if not mcp_json_path.exists():
        mcp_json_content = {
            "mcpServers": {
                "example": {
                    "comment": "Add your MCP server configurations here",
                    "command": "example-server",
                    "args": [],
                    "env": {},
                }
            }
        }
        mcp_json_path.write_text(json.dumps(mcp_json_content, indent=2))
        created_files.append((".mcp.json", "created"))
    else:
        created_files.append((".mcp.json", "preserved"))

    return created_files, skipped_files


def _repair_project(output) -> None:
    """Attempt to repair a corrupted project.

    Args:
        output: OutputManager instance
    """
    claude_dir = get_claude_dir()
    manifest_path = get_manifest_path()
    settings_path = get_settings_path()

    issues_found = []
    repairs_made = []

    # Check directory structure
    for directory in ["agents", "tools", "commands", "mcp-servers"]:
        dir_path = claude_dir / directory
        if not dir_path.exists():
            issues_found.append(f"Missing directory: .claude/{directory}/")
            dir_path.mkdir(parents=True, exist_ok=True)
            repairs_made.append(f"Created .claude/{directory}/")

    # Check manifest
    if not manifest_path.exists():
        issues_found.append("Missing manifest.json")
        manifest = create_manifest()
        save_manifest(manifest)
        repairs_made.append("Created new manifest.json")
    else:
        try:
            with open(manifest_path, encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError:
            issues_found.append("Corrupted manifest.json")
            manifest = create_manifest()
            save_manifest(manifest)
            repairs_made.append("Recreated manifest.json")

    # Check settings
    if not settings_path.exists():
        issues_found.append("Missing settings.json")
        settings = Settings(
            defaults={
                "auto_update": False,
                "resource_source": "local",
            }
        )
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings.model_dump(mode="json"), f, indent=2)
        repairs_made.append("Created default settings.json")

    # Check AI context files
    project_root = Path(".")
    ai_files = [
        ("CLAUDE.md", project_root / "CLAUDE.md"),
        ("AGENTS.md", project_root / "AGENTS.md"),
        ("DISCOVERIES.md", project_root / "DISCOVERIES.md"),
        ("ai_context/IMPLEMENTATION_PHILOSOPHY.md", project_root / "ai_context" / "IMPLEMENTATION_PHILOSOPHY.md"),
        ("ai_context/MODULAR_DESIGN_PHILOSOPHY.md", project_root / "ai_context" / "MODULAR_DESIGN_PHILOSOPHY.md"),
    ]

    for file_name, file_path in ai_files:
        if not file_path.exists():
            issues_found.append(f"Missing {file_name}")
            # Create the missing file
            created_files, _ = _create_project_files(force=False, merge=False)
            for created_path, action in created_files:
                if action == "created" and created_path == file_name:
                    repairs_made.append(f"Created {file_name}")

    # Report results
    if issues_found:
        output.warning(f"Found {len(issues_found)} issue(s):")
        for issue in issues_found:
            output.info(f"  • {issue}")

        if repairs_made:
            output.success(f"Made {len(repairs_made)} repair(s):")
            for repair in repairs_made:
                output.info(f"  ✓ {repair}")
    else:
        output.success("No issues found - project structure is intact")
