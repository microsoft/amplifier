# Amplifier Repository Awareness Rules

**Last Updated**: 2025-10-31
**Purpose**: Define where documentation belongs and what can reference what

---

## Overview

Amplifier uses a modular repository architecture with clear boundaries. This document defines the awareness hierarchy to ensure documentation lives in the right place and prevents context poisoning through duplication.

**Core Principles**:
1. **Single source of truth** - Content lives in ONE place
2. **Link, don't duplicate** - Other repos link via GitHub URLs
3. **Respect awareness** - Don't reference what you're not aware of
4. **Dependency-based awareness** - Only reference what you actually depend on
5. **Challenge necessity** - Only create content that provides unique value
6. **Docs are contract** - Documentation defines what code must implement

---

## Dependency-Based Awareness (Critical Rule)

**The Golden Rule**: A repository/module can only reference another repository/module if it has a **declared dependency** on it.

### What "Dependency" Means

**Code dependency**: Listed in `pyproject.toml` dependencies, imported in code, or consumed via API

**NOT dependency**: Nice to know about, related concepts, similar domain, built by same team

### Why This Matters

**Context poisoning prevention**: When libraries reference other libraries they don't depend on, AI tools load inconsistent information about which components exist and how they relate.

**Example of the problem**:
- A public library references a private development repository in its docs
- Problem: Public repos pointing to inaccessible private repo
- Users cloning public repos got broken links
- AI tools loaded references to concepts they couldn't access

### Application by Repository Type

| Repository Type | Awareness Rule | Examples |
|----------------|---------------|----------|
| **Kernel** (amplifier-core) | References ONLY entry point | Can reference amplifier for "see getting started" |
| **Libraries** | Reference core + entry + **dependencies only** | amplifier-foundation provides primitives other libraries can depend on |
| **Modules** | Reference core + possibly entry, **never peers** | amplifier-module-tool-bash cannot reference amplifier-module-tool-filesystem |
| **Applications** | Reference anything they consume | amplifier-app-cli uses all libraries → can reference all |
| **Entry Point** | Reference everything | amplifier links to all components |

### Decision Framework

Before adding a reference to another repo, ask:

1. **Is this in my pyproject.toml dependencies?**
   - YES → Can reference ✅
   - NO → Continue to question 2

2. **Do I import code from this repo?**
   - YES → Can reference ✅
   - NO → Continue to question 3

3. **Is this amplifier-core and I'm a module/library?**
   - YES → Can reference ✅
   - NO → Continue to question 4

4. **Is this amplifier entry point?**
   - YES → Can reference ✅ (for "see getting started" only)
   - NO → **Cannot reference ❌**

### Correct Examples

```markdown
<!-- amplifier-bundle-recipes/docs/AUTHORING.md -->
<!-- ✅ CORRECT: Bundles can reference amplifier-foundation -->
For bundle primitives, see [amplifier-foundation](https://github.com/microsoft/amplifier-foundation).

<!-- ✅ CORRECT: All libraries can reference kernel -->
This implements the protocol from [amplifier-core](https://github.com/microsoft/amplifier-core).

<!-- ✅ CORRECT: Can reference entry point for getting started -->
For initial setup, see [Getting Started](https://github.com/microsoft/amplifier).
```

### Incorrect Examples

```markdown
<!-- amplifier-module-provider-anthropic/docs/SPECIFICATION.md -->
<!-- ❌ WRONG: Module does NOT depend on amplifier-foundation -->
Provider configuration uses utilities from [amplifier-foundation](https://github.com/microsoft/amplifier-foundation).

<!-- ❌ WRONG: Module referencing another module (no peer awareness) -->
<!-- amplifier-module-tool-bash/README.md -->
Works well with [amplifier-module-tool-filesystem](https://github.com/microsoft/amplifier-module-tool-filesystem).

<!-- ❌ WRONG: Library referencing private development repo -->
<!-- amplifier-foundation/docs/AUTHORING.md -->
See [Module Development](https://github.com/private-repo/docs/MODULE_DEVELOPMENT.md).
```

### Special Case: Describing Without Referencing

**When you need to explain a concept without depending on it**, use generic language:

```markdown
<!-- ✅ CORRECT: Describes concept generically -->
Modules are loaded by applications using this resolution mechanism.

<!-- ❌ WRONG: References specific library not depended on -->
Modules are loaded using amplifier-foundation's internal APIs directly.
```

---

## The Complete Hierarchy

### Entry Point
**amplifier** (microsoft/amplifier)
- **Purpose**: Main entry point for users and developers
- **Can Reference**: Everything (it's the entry point)
- **Referenced By**: All other repos (as the canonical "how to get started")
- **Contains**:
  - Getting started guide
  - Overview of ecosystem
  - Links to all components (via GitHub URLs)
  - Repository rules (this document)

### Kernel
**amplifier-core** (microsoft/amplifier-core)
- **Purpose**: Ultra-thin kernel providing mechanisms only
- **Can Reference**: ONLY amplifier
- **Referenced By**: Everything (it's the kernel)
- **CANNOT Reference**: Any libraries, modules, apps (they don't exist to kernel)
- **Contains**:
  - Kernel philosophy
  - Core mechanisms (session, coordinator, events)
  - Kernel contracts (Mount Plan, events, protocols)
  - Specifications

### Libraries (Provide APIs)

**amplifier-foundation** (microsoft/amplifier-foundation)
- **Purpose**: Foundational library for building on the Amplifier ecosystem
- **Can Reference**: amplifier-core, amplifier
- **Referenced By**: Applications, other libraries
- **CANNOT Be Referenced By**: amplifier-core, modules
- **Contains**:
  - Bundle primitives (composition, validation, resolution)
  - Best-practice mount plans, configs, and instructions
  - Shared utilities (deep_merge, file I/O, path handling)
  - Reference bundles (providers/, behaviors/, agents/, context/)
  - Examples for app/service developers
  - Recommended approaches for common features

### Applications (Consume Libraries)

**amplifier-app-cli** (microsoft/amplifier-app-cli)
- **Purpose**: Reference CLI application

**amplifier-app-log-viewer** (microsoft/amplifier-app-log-viewer)
- **Purpose**: Web-based log viewer for debugging sessions
- **Can Reference**: All libraries, modules, core
- **Referenced By**: Nothing (it's an endpoint)
- **Contains**:
  - CLI command reference
  - App-specific implementation docs (agent delegation, etc.)
  - Toolkit utilities for building sophisticated tools
  - How THIS app uses libraries

### Bundles (Composable Configurations)

**amplifier-bundle-recipes**
**amplifier-bundle-***
- **Purpose**: Composable configuration packages combining providers, behaviors, agents, and context
- **Can Reference**: Modules, libraries (looser rules, evolving)
- **Intra-Bundle Awareness**: Components within the same bundle CAN reference each other (this is the common use case - bundles group related/interdependent items that would otherwise require users to understand complex combinations)
- **Referenced By**: Applications (via `amplifier bundle use`)
- **Contains**:
  - Provider configurations
  - Behavior overlays
  - Agent definitions
  - Context files
  - Bundle-specific documentation

### Modules (Kernel Extensions)

For the current list of all runtime modules (orchestrators, providers, tools, context managers, hooks), see **[Module Catalog](MODULES.md)**.

**All Modules**:
- **Referenced By**: Apps/libraries via mount plans
- **Can Reference**: ONLY amplifier-core, possibly amplifier
- **CANNOT Reference**: Other modules, libraries, apps (unaware of peers)
- **Contains**: Module implementation, module-specific documentation

---

## What Goes Where: Decision Tree

### Is it a kernel contract/mechanism?
→ **amplifier-core** (`docs/specs/`)

**Examples**:
- Mount Plan specification
- Event taxonomy
- Core protocols
- Session forking contract

### Is it library API documentation?
→ **amplifier-{library}** (`README.md`, `docs/`)

**What lives in library repos**:
- Complete API reference
- User guides for library concepts
- System design and architecture
- All examples and patterns
- Schemas and protocols

**Libraries**:
- **amplifier-foundation** - Bundle primitives, shared utilities, reference bundles (primary library)

### Is it app-specific implementation?
→ **amplifier-app-cli** (or other app) (`README.md`, `docs/`)

**Examples**:
- Command reference
- CLI-specific behavior (search paths, env vars)
- How THIS app uses libraries
- Toolkit utilities

### Is it user/dev entry point?
→ **amplifier** (`README.md`, `docs/`)

**What lives here**:
- Getting started (thin overview)
- Ecosystem overview
- Links to detailed docs (via GitHub URLs)
- Repository rules (this document)
- NO duplicate content from libraries

### Is it module-specific?
→ **amplifier-module-{name}** (`README.md`)

**Examples**:
- Module implementation details
- Module configuration options
- Module-specific usage examples

---

## Content Ownership Examples

### Example 1: Bundle System

**Owner**: amplifier-foundation library

**What lives there**:
- Bundle primitives and composition APIs
- "What are bundles?" conceptual explanation
- "How do I create bundles?" user guide (BUNDLE_AUTHORING.md)
- Bundle schemas and validation
- Composition and overlay merging design
- All bundle examples and patterns

**What links there**:
- amplifier README - Links to bundle authoring guide via GitHub URL
- amplifier-app-cli README - Links to bundle API docs via GitHub URL
- Other docs reference via GitHub URLs

**What does NOT live elsewhere**:
- ❌ Bundle authoring guide in amplifier (just link)
- ❌ Bundle concepts in app-cli docs (just link)
- ❌ Duplicated bundle examples (just link)

### Example 2: Mount Plan Contract

**Owner**: amplifier-core

**What lives there**:
- Mount Plan specification (kernel contract)
- Format and structure
- Validation rules

**What links there**:
- Module docs - Modules are mounted via this contract

**Why this works**:
- Kernel contract lives in kernel
- Libraries reference kernel contracts

### Example 3: Agent Delegation

**Conceptual docs owner**: amplifier-foundation library
**Implementation docs owner**: amplifier-app-cli

**amplifier-foundation contains**:
- "What are agents?" concepts
- Agent schemas and formats
- Agent authoring guide
- Agent resolution utilities

**amplifier-app-cli contains**:
- How CLI resolves agents (search paths)
- CLI-specific features (environment variables)
- CLI commands (agent list, agent show)
- Links to amplifier-foundation for concepts

**Why split**:
- Concepts = library's domain
- Implementation = app's domain
- Clear separation of concerns

---

## Link Patterns

### External Links (GitHub URLs)

**Use when**: Referencing authoritative docs in other repos

**Format**:
```markdown
**→ [Bundle Authoring Guide](https://github.com/microsoft/amplifier-foundation/blob/main/docs/BUNDLE_AUTHORING.md)**

For bundle primitives, see [amplifier-foundation](https://github.com/microsoft/amplifier-foundation).
```

**Why**:
- Always points to latest version
- Clear it's external documentation
- Users can follow link to authoritative source
- No duplication

### Internal Links (Relative)

**Use when**: Referencing docs within same repo

**Format**:
```markdown
See [System Design](docs/DESIGN.md) for architecture details.
```

**Why**:
- Works in local clones
- Simpler for same-repo references

---

## Anti-Patterns (Common Mistakes to Avoid)

### ❌ WRONG: Duplicate Content

```markdown
<!-- In amplifier README -->
## Creating Bundles

Bundles are composable configuration packages...
[500 lines of duplicated bundle documentation]
```

**Problem**: Duplication causes context poisoning when content diverges

**Fix**: Link to authoritative source
```markdown
## Creating Bundles

**→ [Bundle Authoring Guide](https://github.com/microsoft/amplifier-foundation/blob/main/docs/BUNDLE_AUTHORING.md)**
```

### ❌ WRONG: Core References Library

```markdown
<!-- In amplifier-core/README.md -->
For bundle configuration, see amplifier-foundation library.
```

**Problem**: Core shouldn't know libraries exist

**Fix**: Don't mention libraries in core docs (core only knows itself and entry point)

### ❌ WRONG: Module References Other Module

```markdown
<!-- In amplifier-module-tool-bash/README.md -->
Works well with amplifier-module-tool-filesystem.
```

**Problem**: Modules don't know about peer modules

**Fix**: Don't reference other modules by name

### ❌ WRONG: Library References App

```markdown
<!-- In amplifier-foundation/README.md -->
Used by amplifier-app-cli for bundle management.
```

**Problem**: Library shouldn't know about specific apps

**Fix**: Generic language
```markdown
Used by applications for bundle management.
```

### ❌ WRONG: Local File Link to External Repo

```markdown
<!-- In amplifier README -->
See [Bundle Guide](../amplifier-foundation/docs/BUNDLE_AUTHORING.md)
```

**Problem**: Assumes local multi-repo structure, breaks for users who clone single repo

**Fix**: Use GitHub URL
```markdown
**→ [Bundle Authoring Guide](https://github.com/microsoft/amplifier-foundation/blob/main/docs/BUNDLE_AUTHORING.md)**
```

---

## Validation Checklist

Before creating/moving documentation:

- [ ] **Ownership**: Is this the right repository for this content?
- [ ] **Awareness**: Does this respect the hierarchy?
- [ ] **Duplication**: Is this duplicating content from another repo?
- [ ] **Necessity**: Does this provide unique value, or can users follow links?
- [ ] **Links**: Are external references via GitHub URLs?
- [ ] **Contract**: Is this documentation the contract (vs implementation)?

---

## Content Distribution Examples

### User Wants to Create a Bundle

**Journey**:
1. Start at amplifier README
2. See "Creating Bundles" section
3. Click link to amplifier-foundation/docs/BUNDLE_AUTHORING.md
4. Read complete authoring guide
5. Reference API docs in amplifier-foundation/README.md as needed

**Why this works**:
- Entry point guides user
- Authoritative docs in library
- No duplication

### Developer Building an App

**Journey**:
1. Start at amplifier README
2. See "For Developers" section with library links
3. Click link to amplifier-foundation
4. Read bundle primitives API documentation
5. Reference design docs as needed

**Why this works**:
- Entry point provides discovery
- Library provides complete API docs
- App examples show integration

### Contributor to amplifier-foundation

**Journey**:
1. Clone amplifier-foundation repo
2. Read README for API overview
3. Read docs/DESIGN.md for architecture
4. Read code with docs as contract
5. Make changes maintaining contracts

**Why this works**:
- All bundle/foundation knowledge in one repo
- Complete context for contributors
- Docs define contracts code must implement

---

## Maintenance

### When Adding New Documentation

**Process**:
1. **Identify owner**: Where does this content belong?
2. **Check for duplication**: Does this exist elsewhere?
3. **Add to owner repo**: Put it in the right place
4. **Update links**: Add links from other repos via GitHub URLs
5. **Update this doc**: If new patterns emerge

**Example**:
```
# Adding bundle authoring guide
1. Owner: amplifier-foundation (it's about bundles)
2. Check: Does amplifier-app-cli mention this? (no)
3. Add: amplifier-foundation/docs/BUNDLE_AUTHORING.md
4. Link: Update amplifier to link to it
5. Update: Note in this doc if needed
```

### When Moving Documentation

**Process**:
1. **Find all references**: Grep for links to old location
2. **Update to GitHub URLs**: Replace with external links
3. **Verify hierarchy**: Ensure moves respect awareness
4. **Test links**: Verify all links work
5. **Delete old location**: Remove from original repo

### Regular Audits

**Quarterly review**:
- Search for duplicated content (`grep -r "same content"`)
- Verify awareness rules followed
- Check for broken links
- Update examples and patterns

---

## Summary Reference

**Repository Types**:
- **Entry Point**: amplifier - Links to everything
- **Kernel**: amplifier-core - Contracts and mechanisms only
- **Libraries**: amplifier-foundation - Bundle primitives, shared utilities
- **Applications**: amplifier-app-cli - Implementation and commands
- **Bundles**: amplifier-bundle-* - Composable configuration packages
- **Modules**: amplifier-module-* - Isolated kernel extensions

**Content Flow**:
- Authoritative source → Single repo (library or core)
- Other repos → Link via GitHub URLs
- NO duplication
- Challenge necessity of all content

**Awareness Rules**:
- Entry point can reference all ✅
- Core references nothing except entry ✅
- Libraries reference core + entry + **declared dependencies only** ✅
- Apps reference libs + modules + core ✅
- Modules reference only core (+ possibly entry), **never peers** ✅
- No circular references ✅

**Dependency-Based**: Only reference what you actually depend on (in pyproject.toml or imported)

**Philosophy**:
- Docs are contract, code is implementation
- Maximum DRY eliminates context poisoning
- Users can follow links to find details
- Each repo is self-contained for its domain

---

**For questions about where content belongs, use the decision tree above or ask in discussions.**
