# Decision Record: CLI Unification Approach

**Date**: 2025-01-14  
**Status**: Implemented  
**Author**: Architecture Team

## Context

Amplifier had multiple entry points scattered across Make targets and individual Python scripts, creating:
- Inconsistent user experience
- Difficult installation and distribution
- Poor discoverability of features
- No standard way to pass options like `--force`, `--concurrency`, etc.

## Decision

Implement a unified CLI using Click framework with:
1. Single entry point: `amplifier` command
2. Hierarchical subcommands for different operations
3. Consistent option naming and behavior
4. Global installation via `pip install amplifier-toolkit`

## Rationale

- **Click framework**: Mature, well-documented, handles complex CLI patterns
- **Single command**: Reduces cognitive load, improves discoverability
- **Subcommands**: Natural grouping of related functionality
- **console_scripts**: Standard Python packaging approach for global CLIs

## Implementation

```
amplifier/
├── cli.py              # Main CLI entry point
├── utils/
│   ├── cache.py       # Artifact caching
│   └── events.py      # Event logging
```

Command structure:
```
amplifier
├── run                 # Full pipeline
├── extract            # Knowledge extraction
├── synthesize         # Synthesis stage
├── triage            # Content triage
├── smoke             # Smoke tests
├── doctor            # Environment check
├── events
│   ├── tail         # Tail event log
│   └── summary      # Event statistics
├── graph             # Visualize knowledge graph
├── self-update       # Update amplifier
└── install-global    # Global installation
```

## Alternatives Considered

1. **Keep Make targets**: Rejected - not portable, poor option handling
2. **Multiple CLI scripts**: Rejected - fragmented experience
3. **Argparse**: Rejected - more boilerplate, less features than Click
4. **Typer**: Considered - Similar to Click but less mature ecosystem

## Consequences

### Positive
- Consistent user experience across all commands
- Easy global installation with pipx/pip
- Better option handling and validation
- Improved help documentation
- Scriptable and composable

### Negative
- TODOs remain for command implementations (intentional - skeleton first)
- Migration period where Make targets coexist
- Additional dependency on Click

## Review Triggers

- User feedback on CLI ergonomics
- Need for more complex command patterns
- Performance issues with CLI startup time