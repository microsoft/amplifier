---
name: ecosystem-getting-started
description: 'Getting started paths for users, app developers, module developers, and contributors, plus deep-dive delegation table'
version: 1.0.0
---

## Getting Started Paths

### For Users
1. Start with `amplifier:docs/USER_ONBOARDING.md` (quick start and commands)
2. Choose a bundle from foundation
3. Run `amplifier run` with your chosen configuration

### For App Developers
1. Study `foundation:examples/` for working patterns
2. Read `foundation:docs/BUNDLE_GUIDE.md` for bundle composition
3. Build your app using bundle primitives

### For Module Developers
1. Understand kernel contracts via `core:docs/`
2. Follow module protocols
3. Test modules in isolation before integration

### For Contributors
1. Read `amplifier:docs/REPOSITORY_RULES.md` for governance
2. Understand the dependency hierarchy
3. Contribute to the appropriate repository

## Deep Dives (Delegate to Specialists)

For detailed information, delegate to the appropriate expert agent:

| Topic | Delegate To | Has Access To |
|-------|-------------|---------------|
| Ecosystem modules, repos, governance | `amplifier:amplifier-expert` | MODULES.md, REPOSITORY_RULES.md, USER_ONBOARDING.md |
| Bundle authoring, patterns, examples | `foundation:foundation-expert` | BUNDLE_GUIDE.md, examples/, PATTERNS.md |
| Kernel internals, module protocols | `core:core-expert` | kernel contracts, HOOKS_API.md, specs/ |
| Recipe authoring, validation | `recipes:recipe-author` | RECIPE_SCHEMA.md, example recipes |

These agents have the heavy documentation @mentioned directly and can provide authoritative answers.
