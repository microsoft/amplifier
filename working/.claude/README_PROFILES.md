# Claude Directory and Profiles System

This `.claude/` directory has been updated to work with the new **Profiles System**, which makes development methodologies first-class, mutable abstractions.

## What Changed?

### Before: Monolithic Configuration

Previously, `.claude/` contained all commands, agents, and configuration in one place:
```
.claude/
├── commands/
├── agents/
├── tools/
└── settings.json
```

### After: Profile-Based Configuration

Now, commands and agents live in **profiles**, with `.claude/` pointing to the active profile:
```
.claude/
├── active-profile -> ../profiles/default/  (symlink)
├── tools/          (hooks and utilities remain here)
├── settings.json   (global settings remain here)
└── README_PROFILES.md (this file)
```

## How It Works

### Active Profile Symlink

The `active-profile` symlink points to the currently active development profile:

```bash
# View current profile
ls -la .claude/active-profile
# → ../profiles/default

# Switch profiles
ln -sf ../profiles/waterfall .claude/active-profile

# Or use the command
/profile use waterfall
```

### Profile Structure

Profiles live in `profiles/` directory at the root:

```
profiles/
├── default/          # Document-driven ruthless minimalism (current)
│   ├── profile.md
│   ├── philosophy/
│   ├── commands/
│   └── agents/
├── profile-meta/     # For developing methodologies
├── waterfall/        # Phased sequential development
└── shared/          # Resources shared across profiles
    ├── commands/
    ├── agents/
    └── tools/
```

### What Stays in .claude/

**Global configuration and hooks remain here:**
- `settings.json` - Global Claude Code settings
- `tools/` - Hooks that run across all profiles
- ` AGENT_PROMPT_INCLUDE.md` - Global agent instructions
- `README_LOGS.md` - Logging documentation

**Profile-specific resources moved to:**
- Commands → `profiles/{active-profile}/commands/`
- Agents → `profiles/{active-profile}/agents/`
- Philosophy → `profiles/{active-profile}/philosophy/`

## Using Profiles

### List Available Profiles

```bash
/profile list
```

### View Current Profile

```bash
/profile show
```

### Switch Profiles

```bash
/profile use profile-meta  # For developing new methodologies
/profile use waterfall     # For fixed-requirement projects
/profile use default       # Back to doc-driven minimalism
```

### Compare Profiles

```bash
/profile compare default waterfall
```

## Creating New Profiles

Switch to `profile-meta` to create or refine methodologies:

```bash
/profile use profile-meta
/create-profile           # Create new methodology
/refine-profile default   # Improve existing profile
```

## Benefits of Profiles

### Before: One Methodology for All Contexts

Everyone uses the same process regardless of project needs.

### After: Context-Appropriate Methodologies

- **Evolving requirements?** → Use `default` profile
- **Fixed requirements, expensive changes?** → Use `waterfall` profile
- **Developing new processes?** → Use `profile-meta` profile
- **Your unique context?** → Create custom profile

## Backward Compatibility

The default profile (`profiles/default/`) contains the same commands and agents that were previously in `.claude/`:

- `/ddd:*` workflow commands
- `/ultrathink-task`, `/designer`, etc.
- `zen-architect`, `modular-builder`, etc.

Your existing workflows continue to work unchanged!

## Philosophy

**Methodologies are tools, not dogma.**

Different projects have different needs:
- Some need comprehensive upfront planning (waterfall)
- Some need iterative evolution (default/DDD)
- Some need process experimentation (profile-meta)

By externalizing methodologies as profiles, we make them:
- **Explicit** - Clearly documented
- **Measurable** - Effectiveness can be assessed
- **Evolvable** - Refined based on results
- **Composable** - Mix and match techniques
- **Teachable** - Easily shared and learned

This elevates Amplifier from a toolkit to a **cognitive prosthesis** where even the development process itself is externalized and subject to improvement.

## Further Reading

- `../profiles/README.md` - Complete profiles system documentation
- `../profiles/default/profile.md` - Default methodology details
- `../profiles/profile-meta/profile.md` - Meta-development details
- `../PROFILES.md` - High-level overview and vision

---

_"The unexamined methodology is not worth following."_
