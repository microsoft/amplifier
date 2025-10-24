# DDD Plan: Multi-Project Remote Development with GitHub Codespaces

## Problem Statement

**What we're solving:**
Enable working on multiple projects simultaneously in persistent cloud-based development environments that continue running even when disconnected (e.g., commuting, switching locations).

**User value:**
- Work on multiple projects in parallel without local resource constraints
- Environments persist in the cloud when laptop disconnects
- Reconnect from anywhere (home, office, coffee shop) to continue work
- Each project isolated in its own environment
- Claude Code pre-configured in every environment

**Problem solved:**
- No more "I can't run 5 projects locally" resource limitations
- Work continues during commute/disconnect (no lost progress)
- True location independence - pick up work from any device
- Consistent dev environment across all projects
- No local setup complexity

## Proposed Solution

Create a **reusable devcontainer template** in `setup-remotedev/` that can be copied to any project repository. Each project gets its own GitHub Codespace with Claude Code pre-installed. Codespaces run in the cloud and persist when you disconnect, allowing true multi-project parallel work.

**Key Components:**

1. **Minimal Devcontainer Template** - Production-ready config ready to copy to any repo
2. **Management Scripts** - CLI tools to manage multiple active Codespaces
3. **Clear Documentation** - Guides for setup, usage, and multi-project workflows

## Alternatives Considered

### Alternative 1: Multiple Sessions in Single Codespace
**Description:** Run multiple Claude Code sessions within one Codespace using tmux/terminal multiplexing.

**Why not chosen:**
- ❌ Violates the goal - need to work on multiple **different projects/repos**
- ❌ Single point of failure - one Codespace crash affects all work
- ❌ Resource contention between projects
- ❌ Complex context switching

### Alternative 2: Enhance Only Amplifier's Devcontainer
**Description:** Just improve the existing `.devcontainer/` in amplifier repo.

**Why not chosen:**
- ❌ Doesn't help with other projects
- ❌ Not reusable across different repos
- ❌ User needs solution for ANY project, not just amplifier

### Alternative 3: Docker Compose Multi-Container
**Description:** Use Docker Compose to run multiple project containers locally.

**Why not chosen:**
- ❌ Still requires local machine to be running (defeats cloud persistence goal)
- ❌ Local resource constraints remain
- ❌ Can't reconnect from different device
- ❌ More complex than needed

**Why we chose the proposed solution:**
- ✅ Each project truly isolated in its own cloud environment
- ✅ Codespaces persist when disconnected (cloud-native)
- ✅ Reusable template = copy once, use everywhere
- ✅ Simple management with CLI scripts
- ✅ Aligns with GitHub Codespaces' designed use case

## Architecture & Design

### Key Interfaces (The "Studs")

**1. Devcontainer Template Interface:**
```
Input: Any project repository
Output: Codespace-ready config (copy template to .devcontainer/)
Contract: Works with any Python/Node/general-purpose project
```

**2. Management Scripts Interface:**
```
Input: gh CLI authentication
Output: List/connect/cleanup operations on Codespaces
Contract: Works across all repos user has access to
```

**3. Documentation Interface:**
```
Input: User needs to set up new project
Output: Step-by-step guide to copy template and create Codespace
Contract: Clear enough for someone unfamiliar with Codespaces
```

### Module Boundaries

**Module 1: Devcontainer Template (`setup-remotedev/.devcontainer/`)**
- Self-contained devcontainer configuration
- Minimal dependencies (Claude Code + essentials)
- Well-documented for customization
- Ready to copy to any project

**Module 2: Management Scripts (`setup-remotedev/scripts/`)**
- Thin wrappers around `gh` CLI
- Each script = one clear responsibility
- Can be used independently or together
- No shared state between scripts

**Module 3: Documentation (`setup-remotedev/docs/`)**
- Setup guide (copying template)
- Usage guide (managing multiple Codespaces)
- Workflow guide (multi-project patterns)
- Troubleshooting guide

**Clear Separation:**
- Template = what goes in each project
- Scripts = how to manage multiple projects
- Docs = how to use both effectively

### Data Models

**Codespace Identity:**
```json
{
  "name": "repo-name-branch",
  "repository": "owner/repo",
  "branch": "main",
  "state": "Available|Shutdown|Starting",
  "created": "2025-10-24T10:00:00Z",
  "machine": "basicLinux32gb"
}
```

**Template Configuration:**
```json
{
  "name": "project-name",
  "image": "python:3.11",
  "features": ["claude-code", "gh", "docker-in-docker"],
  "resources": {
    "cpus": 2,
    "memory": "8gb",
    "storage": "32gb"
  }
}
```

## Files to Change

### Non-Code Files (Phase 2)

- [ ] setup-remotedev/README.md - Overview of remote development setup
- [ ] setup-remotedev/docs/SETUP_GUIDE.md - How to copy template to a project
- [ ] setup-remotedev/docs/USAGE_GUIDE.md - Managing multiple Codespaces
- [ ] setup-remotedev/docs/WORKFLOW_PATTERNS.md - Multi-project workflows
- [ ] setup-remotedev/docs/TROUBLESHOOTING.md - Common issues and solutions
- [ ] setup-remotedev/.devcontainer/README.md - Template documentation
- [ ] setup-remotedev/.devcontainer/devcontainer.json - Minimal, reusable config
- [ ] setup-remotedev/.devcontainer/post-create.sh - Setup script
- [ ] setup-remotedev/.devcontainer/POST_SETUP_README.md - What happens after creation
- [ ] README.md - Add link to setup-remotedev in main README (if appropriate)

### Code Files (Phase 4)

- [ ] setup-remotedev/scripts/list-codespaces - List all active Codespaces
- [ ] setup-remotedev/scripts/connect-codespace - Connect to specific Codespace
- [ ] setup-remotedev/scripts/cleanup-codespaces - Delete inactive Codespaces
- [ ] setup-remotedev/scripts/create-codespace - Quick Codespace creation helper
- [ ] setup-remotedev/scripts/lib/common.sh - Shared functions (if needed)

**Note:** Scripts should be minimal bash wrappers around `gh codespace` commands.

## Philosophy Alignment

### Ruthless Simplicity

**Start minimal:**
- Devcontainer has ONLY what's needed: Claude Code, gh CLI, basic tools
- No pre-installing every possible tool "just in case"
- Users can extend per-project as needed

**Avoid future-proofing:**
- No complex orchestration systems
- No custom Codespace management platforms
- Just scripts wrapping existing `gh` CLI
- Leverage what GitHub already provides

**Clear over clever:**
- Scripts have obvious names: `list-codespaces`, not `cs-ls`
- Documentation is step-by-step, not assuming knowledge
- Template config has comments explaining each section

**What we're NOT building:**
- ❌ Custom Codespace orchestration platform
- ❌ Advanced monitoring dashboards
- ❌ Complex state synchronization between Codespaces
- ❌ Project-specific templates (just one general-purpose template)

### Modular Design

**Bricks (self-contained modules):**
1. **Devcontainer Template** - Can copy to any project, works independently
2. **List Script** - Shows all Codespaces, no dependencies on other scripts
3. **Connect Script** - Connects to one Codespace, standalone operation
4. **Cleanup Script** - Deletes Codespaces, independent operation
5. **Documentation** - Each guide stands alone

**Studs (connection points):**
1. **Template → Project** - Copy `.devcontainer/` folder, works immediately
2. **Scripts → gh CLI** - All scripts use `gh codespace` commands (standard interface)
3. **Docs → User** - Clear entry points for different use cases

**Regeneratable:**
- Can rebuild any script from its description
- Template can be regenerated from requirements
- Documentation can be rewritten from use cases
- Each piece independent and simple

**Human architects, AI builds:**
- Human defines: "I want to manage multiple Codespaces"
- AI builds: Scripts wrapping gh CLI with clear UX
- Human validates: "Does this help me work on 5 projects?"

## Test Strategy

### Unit Tests

**Devcontainer Template:**
- [ ] Validates devcontainer.json syntax
- [ ] post-create.sh runs without errors
- [ ] Claude CLI available after creation
- [ ] All specified features installed

**Management Scripts:**
- [ ] Each script has --help flag
- [ ] Scripts fail gracefully when gh not authenticated
- [ ] Scripts handle no Codespaces case
- [ ] Scripts handle API errors appropriately

### Integration Tests

**End-to-End Workflows:**
- [ ] Copy template to a test repo
- [ ] Create Codespace from template
- [ ] Verify Claude Code works in Codespace
- [ ] List Codespaces shows the new one
- [ ] Connect script can connect to it
- [ ] Cleanup script can delete it

**Multi-Project Testing:**
- [ ] Create Codespaces for 3 different repos
- [ ] List shows all 3
- [ ] Can connect to each independently
- [ ] Can clean up all at once

### User Testing (Manual)

**Real-World Scenarios:**
1. Copy template to a personal project
2. Create Codespace, start Claude Code session
3. Close laptop (simulate commute)
4. Reopen laptop, reconnect to same Codespace
5. Verify work persisted and continues
6. Create second Codespace for different project
7. Switch between Codespaces easily
8. Clean up when done

**Success Criteria:**
- ✅ Can set up new project in < 5 minutes
- ✅ Can switch between 5 active Codespaces easily
- ✅ Work persists when disconnected
- ✅ Documentation is clear enough for first-time user

## Implementation Approach

### Phase 2 (Docs) - Update All Non-Code Files

**Order of operations:**

1. **Create main README** (`setup-remotedev/README.md`)
   - What this is and why it exists
   - High-level overview of components
   - Quick links to detailed docs

2. **Create SETUP_GUIDE** (`setup-remotedev/docs/SETUP_GUIDE.md`)
   - Prerequisites (gh CLI, GitHub account)
   - Copying template to a project
   - Creating first Codespace
   - Verifying Claude Code works

3. **Create devcontainer template docs**
   - `setup-remotedev/.devcontainer/README.md` - Template documentation
   - `setup-remotedev/.devcontainer/devcontainer.json` - Config with comments
   - `setup-remotedev/.devcontainer/POST_SETUP_README.md` - Post-creation info
   - `setup-remotedev/.devcontainer/post-create.sh` - Setup script (commented)

4. **Create USAGE_GUIDE** (`setup-remotedev/docs/USAGE_GUIDE.md`)
   - Listing active Codespaces
   - Connecting to a Codespace
   - Managing multiple Codespaces
   - Cleaning up unused Codespaces

5. **Create WORKFLOW_PATTERNS** (`setup-remotedev/docs/WORKFLOW_PATTERNS.md`)
   - Pattern: Feature development in parallel
   - Pattern: Different projects simultaneously
   - Pattern: Persistent background tasks
   - Pattern: Review/testing workflows

6. **Create TROUBLESHOOTING** (`setup-remotedev/docs/TROUBLESHOOTING.md`)
   - Codespace won't start
   - Claude Code not available
   - Can't reconnect to Codespace
   - Resource limits hit

7. **Update main README** (if appropriate)
   - Add link to setup-remotedev/
   - Brief mention of multi-project support

**File Crawling Strategy:**
- Process all docs in setup-remotedev/docs/ together
- Process all .devcontainer/ files together
- Review main README last (context from everything else)

### Phase 4 (Code) - Implement Scripts

**Order of operations:**

1. **list-codespaces** (simplest, no side effects)
   - Wraps `gh codespace list`
   - Adds formatted output
   - Shows: name, repo, status, created time

2. **connect-codespace** (read + action)
   - Interactive if no args (shows list, prompts for choice)
   - Direct if name provided
   - Wraps `gh codespace code --codespace <name>`

3. **cleanup-codespaces** (destructive, needs confirmation)
   - Lists inactive/old Codespaces
   - Prompts for confirmation
   - Wraps `gh codespace delete`

4. **create-codespace** (optional, nice-to-have)
   - Interactive wizard for quick Codespace creation
   - Prompts: repo, branch, machine type
   - Wraps `gh codespace create`

5. **common.sh** (only if real duplication emerges)
   - Shared functions for formatting output
   - Error handling patterns
   - Only create if 3+ scripts need same code

**Implementation principles:**
- Start with simplest possible script (direct gh CLI wrapper)
- Add polish only if needed (colors, formatting, etc.)
- Each script must work standalone
- Add --help and --version to each script

## Success Criteria

**Setup Success:**
- [ ] Can copy template to new project in < 2 minutes
- [ ] Codespace creates successfully from template
- [ ] Claude Code launches and works in Codespace
- [ ] Documentation clear enough for non-expert to follow

**Multi-Project Success:**
- [ ] Can run 5+ Codespaces simultaneously
- [ ] Can switch between Codespaces in < 30 seconds
- [ ] Work persists when laptop disconnects
- [ ] Can reconnect from different device and continue work

**Management Success:**
- [ ] Can see all active Codespaces at a glance
- [ ] Can connect to specific Codespace by name
- [ ] Can clean up unused Codespaces easily
- [ ] Scripts are intuitive (no reading docs to use)

**Philosophy Success:**
- [ ] Template has no unnecessary complexity
- [ ] Scripts are simple wrappers (< 100 lines each)
- [ ] Documentation is clear and concise
- [ ] Everything follows ruthless simplicity principle

## Next Steps

✅ Phase 1 Complete: Planning & Design

**Ready for Phase 2:** Update all non-code files (docs, configs, templates)

**Command:** `/ddd:2-docs`

The plan is complete and approved. All subsequent DDD phases will use this plan as their guide. Each phase command can run without arguments.

---

## Notes

**Key Insights:**
- GitHub Codespaces already handles persistence - we just need to make it easy to manage multiple ones
- Template approach is simpler than complex orchestration
- Scripts should be thin wrappers around `gh` CLI, not reinvent it
- Focus on documentation - the tech is simple, the workflow is what matters

**Questions Resolved:**
- ✅ Multi-project across different repos (not multi-session in one Codespace)
- ✅ Cloud persistence is GitHub Codespaces' native behavior
- ✅ Reusable template approach balances simplicity and flexibility

**Assumptions:**
- User has GitHub account with Codespaces access
- User will install gh CLI locally for management scripts
- Projects are in GitHub repos (Codespaces requirement)
- User comfortable with command-line tools

**Future Enhancements (NOT in this phase):**
- TUI (terminal UI) for managing Codespaces
- Codespace health monitoring
- Cost tracking/alerts
- Template variants for different project types
