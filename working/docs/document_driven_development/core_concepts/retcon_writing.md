# Retcon Writing

**Writing documentation as if the feature already exists**

---

## What is Retcon Writing?

**Retcon** (retroactive continuity) means writing documentation as if the new feature already exists and always worked this way. No historical references, no "will be implemented," just pure present-tense description of how it works.

**Purpose**: Eliminate ambiguity about what's current, what's planned, and what's historical.

---

## Why Retcon Writing Matters

### The Problem with Traditional Documentation

**Traditional approach**:
```markdown
## Provider Configuration (Updated 2025-01-15)

Previously, providers were configured using `amplifier setup`.
This approach has been deprecated as of version 2.0.

Now, use `amplifier init` instead.

In a future release, `setup` will be removed entirely.

For now, both work, but we recommend using `init`.
```

**What's wrong**:
- AI doesn't know which approach is current
- Mix of past, present, and future
- Unclear if `setup` still works
- Version numbers add confusion
- Multiple timelines create ambiguity

**Result**: AI might implement `setup`, or `init`, or both. Wrong decision made confidently.

### The Retcon Solution

**Retcon approach**:
```markdown
## Provider Configuration

Configure your provider using the init wizard:

```bash
amplifier init
```

The wizard guides you through provider selection and configuration.
```

**What's right**:
- Single timeline: NOW
- Clear current approach
- No version confusion
- No historical baggage
- Unambiguous for AI and humans

**Result**: AI knows exactly what to implement. Humans know exactly how to use it.

---

## Retcon Writing Rules

### DO:

✅ **Write in present tense** - "The system does X" not "will do X"

✅ **Write as if always existed** - Describe current reality only

✅ **Show actual commands** - Examples that work right now

✅ **Use canonical terminology** - No invented names

✅ **Document all complexity** - Be honest about what's required

✅ **Focus on now** - Not past, not future, just now

### DON'T:

❌ **"This will change to X"** - Write as if X is reality

❌ **"Coming soon" or "planned"** - Only document what you're implementing

❌ **Migration notes in main docs** - Belongs in CHANGELOG or git history

❌ **Historical references** - "Used to work this way"

❌ **Version numbers in docs** - Docs are always current

❌ **Future-proofing** - Document what exists, not what might

❌ **Transition language** - "Now use init instead of setup"

---

## Examples

### Example 1: Command Syntax

**BAD** (traditional):
```markdown
## Setup Command (Deprecated)

The `amplifier setup` command was used in v1.0 to configure providers.

As of v2.0, this is deprecated. Use `amplifier init` instead.

Example (old way - don't use):
amplifier setup

Example (new way - recommended):
amplifier init
```

**GOOD** (retcon):
```markdown
## Initial Configuration

Configure Amplifier on first use:

```bash
amplifier init
```

The init wizard guides you through provider and profile selection.
```

### Example 2: Configuration Files

**BAD** (traditional):
```markdown
## Settings Files

Previously, settings were stored in `~/.amplifier/config.json`.

In v2.0, we migrated to YAML format for better readability.

Old location (deprecated): `~/.amplifier/config.json`
New location: `~/.amplifier/settings.yaml`

If you're upgrading from v1.0, run `amplifier migrate` to convert your settings.
```

**GOOD** (retcon):
```markdown
## Settings Files

Amplifier stores settings in YAML format:

- `~/.amplifier/settings.yaml` - User-global settings
- `.amplifier/settings.yaml` - Project settings
- `.amplifier/settings.local.yaml` - Local overrides (gitignored)
```

### Example 3: API Changes

**BAD** (traditional):
```markdown
## Profile Management

The profile API changed in v2.0:

Old API (v1.0):
  amplifier profile apply dev

New API (v2.0):
  amplifier profile use dev

We kept `apply` as an alias for backward compatibility,
but `use` is now the preferred command.
```

**GOOD** (retcon):
```markdown
## Profile Management

Activate a profile:

```bash
amplifier profile use dev
```

This loads the profile's capability set and makes it active.
```

---

## Where Historical Information Goes

**Retcon main docs**, but preserve history where appropriate:

### CHANGELOG.md

```markdown
# Changelog

## [2.0.0] - 2025-01-15

### Changed
- Profile activation: `amplifier profile apply` → `amplifier profile use`
- Configuration format: JSON → YAML
- Setup command: `amplifier setup` → `amplifier init`

### Migration
Run `amplifier migrate` to update v1.0 settings to v2.0 format.
```

### Git Commit Messages

```bash
git commit -m "refactor: Replace setup command with init

Replaces `amplifier setup` with `amplifier init`.

BREAKING CHANGE: `amplifier setup` has been removed.
Users should use `amplifier init` instead.

Migration: Manual update required for existing users."
```

### Migration Guides (If Necessary)

```markdown
# Migration Guide: v1.0 → v2.0

## For Existing Users

If upgrading from v1.0:

1. Run migration tool:
   ```bash
   amplifier migrate
   ```

2. Verify settings:
   ```bash
   amplifier config show
   ```

## What Changed

- Command: `setup` → `init`
- Config format: JSON → YAML
- Profile activation: `apply` → `use`
```

**Key point**: Migration info goes in dedicated migration docs, CHANGELOG, and git history. NOT in main user-facing documentation.

---

## Benefits of Retcon Writing

### 1. Eliminates Ambiguity

**Single timeline**: Documentation describes ONE reality (current state)

**AI benefit**: No confusion about what to implement

**Human benefit**: No confusion about how to use it

### 2. Prevents Context Poisoning

**No mixed timelines**: Can't load "old approach" by mistake

**No version confusion**: Docs are always current

**Clear specification**: AI knows exactly what to build

### 3. Cleaner Documentation

**Shorter**: No historical baggage

**Focused**: Just how it works now

**Maintainable**: One timeline to maintain

### 4. Better User Experience

**Users don't care about history**: They want to know how it works now

**Clear examples**: Commands that actually work

**No confusion**: Single approach shown

---

## Common Mistakes

### Mistake 1: Apologetic Language

**BAD**:
```markdown
The new approach is better because it's simpler and more intuitive.
We apologize for the inconvenience of changing the command.
```

**GOOD**:
```markdown
Configure Amplifier:

```bash
amplifier init
```
```

**Why**: Apologies imply something else was standard. Just describe how it works.

### Mistake 2: Transition Warnings

**BAD**:
```markdown
Note: If you're used to the old `setup` command, you'll need to
learn the new `init` command instead. The syntax is different.
```

**GOOD**:
```markdown
Initialize Amplifier configuration:

```bash
amplifier init
```
```

**Why**: Assumes users know old way. New users don't. Just describe current way.

### Mistake 3: Version Numbers in Headers

**BAD**:
```markdown
## Profile Management (v2.0+)

New in version 2.0: Profile management commands
```

**GOOD**:
```markdown
## Profile Management

Manage capability profiles:
```

**Why**: Docs are always current. Version numbers add noise.

---

## When NOT to Retcon

### Keep History When:

1. **CHANGELOG.md** - Explicitly about changes over time
2. **Migration guides** - Purpose is to document transition
3. **Git history** - Commit messages and history
4. **ADRs** (if used) - Architecture decision records

### Retcon Everywhere Else:

- Main README
- User guides
- API documentation
- Architecture docs
- Examples and tutorials

---

## Integration with DDD

Retcon writing is applied throughout:

- **[Phase 1](../phases/01_documentation_retcon.md)**: All documentation updates use retcon
- **[Phase 2](../phases/02_approval_gate.md)**: Review checks for non-retcon language
- **[Phase 4](../phases/04_code_implementation.md)**: Code implements current state only

---

## Quick Reference

### Retcon Writing Checklist

Before committing documentation:

- [ ] All present tense ("system does X")
- [ ] No "will" or "planned" language
- [ ] No historical references ("used to")
- [ ] No version numbers in main content
- [ ] No transition language ("now use X instead of Y")
- [ ] No backward compatibility notes in main docs
- [ ] Examples work with current code

### Quick Fixes

**Find non-retcon language**:
```bash
# Check for future tense
grep -rn "will be\|coming soon\|planned" docs/

# Check for historical references
grep -rn "previously\|used to\|old way\|new way" docs/

# Check for version numbers
grep -rn "v[0-9]\|version [0-9]" docs/

# Check for transition language
grep -rn "instead of\|rather than\|no longer" docs/
```

**Fix systematically**:
```bash
# Remove identified issues
# Rewrite in present tense
# Describe only current state
```

---

**Return to**: [Core Concepts](README.md) | [Main Index](../README.md)

**Related**: [File Crawling](file_crawling.md) | [Context Poisoning](context_poisoning.md)

**See Also**: [Phase 1 Step 3](../phases/01_documentation_retcon.md#step-3-retcon-writing-rules)
