# Core Improvement: Working Directory Support

> **Source Branch**: `generator-from-code-cdx`
> **Created**: 2025-09-18
> **Status**: Phase 1 COMPLETED ✅ (items 1-3) - Phase 2+ specification
> **Context**: Core toolkit improvement specifications from module_generator analysis


## Priority: 🟡 Important (P2)

## Problem Statement

The toolkit doesn't support setting a working directory or additional context directories for the Claude session. The module generator shows these are essential for proper context and file operations.

## Current Implementation

```python
# ccsdk_toolkit/core/session.py
# No directory configuration
ClaudeSDKClient(
    options=ClaudeCodeOptions(
        system_prompt=self.options.system_prompt,
        max_turns=self.options.max_turns,
        # No cwd or add_dirs
    )
)
```

## Proposed Solution

### Add Directory Configuration to SessionOptions

```python
# ccsdk_toolkit/core/models.py
from pathlib import Path

class SessionOptions(BaseModel):
    # Existing fields...

    # Directory configuration
    cwd: Path | None = Field(
        default=None,
        description="Working directory for the session"
    )
    add_dirs: list[Path] | None = Field(
        default=None,
        description="Additional directories to include in context"
    )

    def model_post_init(self, __context) -> None:
        """Auto-detect cwd if not provided."""
        if self.cwd is None:
            # Try to find project root
            self.cwd = self._find_project_root()

    @staticmethod
    def _find_project_root() -> Path:
        """Find project root by looking for markers."""
        current = Path.cwd()
        markers = [".git", "pyproject.toml", "Makefile", "package.json"]

        while current != current.parent:
            if any((current / marker).exists() for marker in markers):
                return current
            current = current.parent

        return Path.cwd()  # Fallback to current directory
```

### Pass Directory Configuration to SDK

```python
# ccsdk_toolkit/core/session.py
async def __aenter__(self):
    options_dict = {
        "system_prompt": self.options.system_prompt,
        "max_turns": self.options.max_turns,
    }

    # Add directory configuration
    if self.options.cwd:
        options_dict["cwd"] = str(self.options.cwd)
    if self.options.add_dirs:
        options_dict["add_dirs"] = [str(d) for d in self.options.add_dirs]

    self.client = ClaudeSDKClient(
        options=ClaudeCodeOptions(**options_dict)
    )
```

## Usage Patterns

### Pattern 1: Explicit Working Directory

```python
options = SessionOptions(
    cwd=Path("/path/to/project"),
    add_dirs=[
        Path("/path/to/project/docs"),
        Path("/path/to/project/examples")
    ]
)

async with ClaudeSession(options) as session:
    # Claude operates in the project directory
    response = await session.query("Analyze the codebase structure")
```

### Pattern 2: Auto-Detection

```python
# Automatically finds project root
options = SessionOptions()  # cwd auto-detected

async with ClaudeSession(options) as session:
    response = await session.query("What files are in this project?")
```

### Pattern 3: Context-Rich Sessions

```python
def create_context_session(module_name: str) -> SessionOptions:
    """Create session with relevant context for a module."""
    project_root = Path.cwd()

    return SessionOptions(
        cwd=project_root,
        add_dirs=[
            project_root / "ai_context",
            project_root / "amplifier" / module_name,
            project_root / "docs"
        ],
        system_prompt=f"You are working on the {module_name} module."
    )
```

## Module Generator Pattern

```python
# sdk_client.py
async with ClaudeSDKClient(
    options=ClaudeCodeOptions(
        cwd=str(ctx.repo_root),
        add_dirs=[
            ctx.repo_root / "ai_context",
            ctx.repo_root / "amplifier"
        ]
    )
) as client:
```

## Implementation Details

1. Auto-detect project root when cwd not provided
2. Validate directories exist before passing to SDK
3. Convert Path objects to strings for SDK
4. Document common patterns for directory setup

## Testing Requirements

- Test auto-detection finds correct project root
- Verify cwd changes file operation context
- Test add_dirs provides additional context
- Ensure relative paths work correctly

## Migration Impact

- Default behavior uses current directory
- Auto-detection improves default experience
- Examples should show directory configuration

## Success Criteria

- Sessions operate in correct directory context
- Additional directories provide needed context
- Auto-detection works for common project structures
- Clear patterns for multi-directory projects

## Context Philosophy

The working directory establishes the session's perspective. Additional directories provide reference material without changing the operational context. This separation enables focused work with broad awareness.