---
bundle:
  name: amplifier
  version: 1.0.0
  description: Amplifier ecosystem entry point - comprehensive documentation and expert guidance

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: amplifier:behaviors/amplifier-expert
  - bundle: amplifier:behaviors/module-catalog-expert
---

# Amplifier Ecosystem

@amplifier:context/ecosystem-overview.md

---

The **amplifier** bundle is the entry point for the complete Amplifier ecosystem. It provides:

- **Ecosystem Overview** - Understanding what Amplifier is and what's possible
- **Getting Started** - How to begin building with Amplifier
- **Expert Guidance** - The amplifier-expert agent for authoritative consultation

## Documentation

### User-Facing Documentation

@amplifier:docs/

Key documents:
- **USER_GUIDE.md** - Complete user guide for working with Amplifier
- **USER_ONBOARDING.md** - Getting started and quick reference
- **MODULES.md** - Understanding the module ecosystem
- **DEVELOPER.md** - Building applications with Amplifier

### Repository Governance

- **REPOSITORY_RULES.md** - What goes where across the ecosystem

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ amplifier (THIS BUNDLE) - Entry Point                        │
│ User-facing docs, ecosystem overview, getting started        │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ amplifier-    │   │ amplifier-    │   │ Modules       │
│ foundation    │   │ core          │   │ (providers,   │
│               │   │               │   │ tools, etc.)  │
│ Library for   │   │ Ultra-thin    │   │               │
│ building apps │   │ kernel        │   │ Swappable     │
│ and bundles   │   │ (mechanism    │   │ capabilities  │
│               │   │ only)         │   │               │
└───────────────┘   └───────────────┘   └───────────────┘
```

## When to Use This Bundle

Include this bundle when you need:
- Complete ecosystem awareness
- Getting started guidance
- Understanding what's possible with Amplifier
- Repository rules and governance

## Expert Agent

The **amplifier-expert** agent is the authoritative consultant for ALL Amplifier ecosystem knowledge. Consult it for:
- Initial research before starting work
- Understanding ecosystem capabilities
- Routing to appropriate components
- Validation of high-level approaches

## Recipes (Requires recipes bundle)

The **recipes bundle** provides generic, reusable recipes for repository analysis:

| Recipe | Description |
|--------|-------------|
| `repo-activity-analysis.yaml` | Analyze any GitHub repo (defaults to current directory, since yesterday) |
| `multi-repo-activity-report.yaml` | Analyze multiple repos and synthesize a comprehensive report |

**For Amplifier ecosystem analysis** (using MODULES.md), see @amplifier:context/recipes-usage.md for detailed instructions on discovering and analyzing all Amplifier repos.

---

@foundation:context/shared/common-system-base.md
