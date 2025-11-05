# Profile Management Command

Manage development profiles: list, view, switch, and compare.

## Usage

```bash
/profile list                    # List all available profiles
/profile show [name]             # Show details of a profile (default: current)
/profile use <name>              # Switch to a different profile
/profile compare <name1> <name2> # Compare two profiles
```

## Commands

### List Profiles

```bash
/profile list
```

Shows all available profiles in `profiles/` directory with:
- Profile name
- One-line description from profile.md
- (active) marker for current profile

Example output:
```
Available Profiles:
-------------------
* default - Document-Driven Ruthless Minimalism (active)
  profile-meta - Methodology Development Profile
  waterfall - Phased Sequential Development
```

### Show Profile

```bash
/profile show [profile-name]
```

Displays detailed information about a profile:
- Full description from profile.md
- Core philosophy summary
- Process overview
- When to use / when not to use
- Available commands and agents
- Composition (what it imports from shared/)

If no name provided, shows current active profile.

### Use Profile

```bash
/profile use <profile-name>
```

Switches to a different profile by updating the `.claude/active-profile` symlink.

**Process:**
1. Validate profile exists in `profiles/` directory
2. Confirm switch with user (show what's changing)
3. Update `.claude/active-profile` symlink to point to new profile
4. Show new profile's overview
5. Suggest reading `/profile show` for full details

**Note**: This changes the development methodology for subsequent work. Current session context remains, but new commands/agents from the profile become available.

### Compare Profiles

```bash
/profile compare <profile1> <profile2>
```

Shows side-by-side comparison:
- Philosophy differences
- Process approach
- Trade-offs
- When to use each
- Key differences in commands/agents

Example:
```
Comparing: default vs waterfall
================================

Philosophy:
-----------
default:    Documentation leads, code follows. Embrace change.
waterfall:  Comprehensive upfront planning. Change is expensive.

Process:
--------
default:    Iterative phases with flexible gates
waterfall:  Sequential phases with strict gates

Best For:
---------
default:    Evolving requirements, rapid iteration
waterfall:  Clear requirements, expensive changes

Trade-offs:
-----------
default:    Speed & flexibility vs. comprehensive documentation
waterfall:  Predictability & traceability vs. adaptation speed
```

## Implementation Notes

### Profile Discovery

Scan `profiles/` directory for subdirectories containing `profile.md`:
```python
profile_dirs = [d for d in Path('profiles').iterdir()
                if d.is_dir() and (d / 'profile.md').exists()]
```

### Active Profile Detection

Read symlink target:
```bash
readlink .claude/active-profile
# Returns: ../profiles/default
```

### Switching Profiles

Update symlink:
```bash
ln -sf ../profiles/<new-profile> .claude/active-profile
```

### Profile Validation

Before switching, verify:
- Profile directory exists
- `profile.md` exists
- Required structure is present (use `/test-profile` validation)

## Success Criteria

- User can easily discover available profiles
- Switching profiles is simple and clear
- Profile differences are easy to understand
- Active profile is always obvious
