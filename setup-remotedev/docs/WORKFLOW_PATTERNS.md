# Workflow Patterns: Multi-Project Development

This guide describes proven patterns for working with multiple concurrent Codespaces.

## Core Patterns

### Pattern 1: Parallel Feature Development

**Use Case:** Work on multiple features simultaneously without context switching overhead.

**Setup:**
```bash
# Feature A in its own Codespace
gh codespace create --repo user/project --branch feature/auth

# Feature B in separate Codespace
gh codespace create --repo user/project --branch feature/payments

# Main branch for reviews
gh codespace create --repo user/project --branch main
```

**Workflow:**
1. Morning: Start Feature A work in its Codespace
2. Blocked on Feature A? Switch to Feature B Codespace
3. Continue productive work without losing context
4. Review PRs in main branch Codespace

**Benefits:**
- No mental context switching cost
- Each feature has clean isolated environment
- Can run tests for both simultaneously
- Easy to compare implementations

**Example Day:**
```
9:00 AM  - Connect to feature/auth Codespace
           Ask Claude to implement OAuth flow

10:30 AM - Waiting for API keys from team
           Switch to feature/payments Codespace
           Continue Stripe integration

12:00 PM - API keys arrived
           Switch back to feature/auth
           Continue without losing context

3:00 PM  - Review teammate's PR
           Connect to main branch Codespace
           Test changes in clean environment
```

---

### Pattern 2: Different Projects Simultaneously

**Use Case:** Maintain multiple active projects (work, side projects, experiments).

**Setup:**
```bash
# Work project
gh codespace create --repo company/production-app

# Side project
gh codespace create --repo personal/side-hustle

# Learning/experiment
gh codespace create --repo personal/learning-rust
```

**Workflow:**
1. Work hours: Primary focus on work project
2. Lunch break: Quick check on side project progress
3. Evening: Continue side project or learning
4. All environments remain active and ready

**Benefits:**
- Instant switching between projects
- No "which branch was I on?" confusion
- Each project maintains its own dependencies
- Can run long-running tasks (tests, builds) in background

**Example Workflow:**
```
Morning:
- Start work in company/production-app
- Claude helps implement feature
- Tests running (takes 20 minutes)

While tests run:
- Switch to personal/side-hustle
- Make quick updates
- Deploy to staging
- Switch back to check test results

Evening:
- Continue side project where you left off
- No setup, no context loss
```

---

### Pattern 3: Persistent Background Work

**Use Case:** Long-running operations continue while you're disconnected.

**Examples:**
- Large test suites
- Data processing scripts
- Documentation generation
- Deployment pipelines

**Setup:**
```bash
# Start long-running task in Codespace
gh codespace ssh --codespace project-main-abc123

# Inside Codespace, use tmux or screen
tmux new -s tests
npm run test:all  # Runs for 30+ minutes

# Detach: Ctrl+B, then D
# Close laptop, commute home

# Later: Reconnect and reattach
gh codespace ssh --codespace project-main-abc123
tmux attach -t tests
# Tests still running or completed
```

**Benefits:**
- Work continues during commute
- No keeping laptop awake
- Can check progress from phone (GitHub Codespaces app)
- Results waiting when you reconnect

**Real-World Example:**
```
3:00 PM - Office
  Start comprehensive test suite
  Takes 2 hours to complete

3:10 PM - Commute starts
  Close laptop
  Tests continue in cloud

5:30 PM - Home
  Reconnect to Codespace
  Review test results
  All passed! Ready to merge
```

---

### Pattern 4: Review and Development Separation

**Use Case:** Keep review environment clean from development changes.

**Setup:**
```bash
# Development Codespace
gh codespace create --repo user/project --branch dev

# Review Codespace (always pristine main)
gh codespace create --repo user/project --branch main
```

**Workflow:**
1. Do all development in dev Codespace
2. Commit and push changes
3. Switch to review Codespace
4. Pull changes and review as user would see them
5. Test in clean environment without dev artifacts

**Benefits:**
- Clean testing environment
- No "works on my machine" issues
- Can review PRs without affecting dev work
- Ensures changes work from fresh clone

---

### Pattern 5: Experimentation Sandbox

**Use Case:** Try risky changes without affecting main work.

**Setup:**
```bash
# Main work (safe)
gh codespace create --repo user/project --branch main

# Experiment (disposable)
gh codespace create --repo user/project --branch experiment/new-arch
```

**Workflow:**
1. Keep main work in stable Codespace
2. Create experiment Codespace for risky refactoring
3. If experiment works: merge changes
4. If experiment fails: delete Codespace, no cleanup needed

**Benefits:**
- Risk-free experimentation
- Can abandon failed experiments cleanly
- Main work untouched if experiment goes wrong
- Easy to compare approaches side-by-side

---

### Pattern 6: Team Collaboration

**Use Case:** Share work-in-progress with team members for pair programming or debugging.

**Approach:**

**Option A: Live Share in Codespace**
```bash
# Start your Codespace
gh codespace code --codespace project-feature-abc123

# In VS Code: Start Live Share session
# Share link with teammate
# Both work in same environment simultaneously
```

**Option B: Transfer Codespace Ownership** (Enterprise only)
```bash
# Create Codespace for teammate to use
# They connect to same Codespace
# Shared state, shared environment
```

**Benefits:**
- No "send me your code" friction
- Shared environment eliminates "works for me" issues
- Real-time collaboration
- Teammate sees exact same state

---

## Advanced Patterns

### Multi-Stage Development Pipeline

**Use Case:** Different Codespaces for different stages.

```bash
# Stage 1: Development
project-dev-*

# Stage 2: Integration testing
project-integration-*

# Stage 3: Performance testing
project-perf-*

# Stage 4: Staging verification
project-staging-*
```

Move work through stages, each with appropriate configuration and data.

---

### Monorepo Multi-Service Development

**Use Case:** Work on multiple services in monorepo simultaneously.

```bash
# Frontend service
gh codespace create --repo company/monorepo --branch feature/ui

# Backend API
gh codespace create --repo company/monorepo --branch feature/api

# Data pipeline
gh codespace create --repo company/monorepo --branch feature/pipeline
```

Each Codespace focuses on one service. Port forwarding connects them.

---

### Documentation and Code in Parallel

**Use Case:** Update docs while implementing features.

```bash
# Code Codespace
gh codespace create --repo user/project --branch feature/new-api

# Docs Codespace
gh codespace create --repo user/project --branch feature/docs-update
```

Write code in one, document in the other, switch seamlessly.

---

## Cost Optimization Patterns

### Pattern: Auto-Stop Configuration

Let Codespaces auto-stop when idle (default 30 minutes):

```bash
# Codespace stops after 30 minutes of no activity
# Restart is quick (< 1 minute)
# No charges while stopped
```

**Best for:** Codespaces you might return to but not actively using.

---

### Pattern: Scheduled Work Hours

**Morning startup:**
```bash
#!/usr/bin/env bash
# ~/bin/workday-start
gh codespace code --repo company/main-project
gh codespace code --repo company/side-project
```

**Evening shutdown:**
```bash
#!/usr/bin/env bash
# ~/bin/workday-end
gh codespace list --json name | \
  jq -r '.[].name' | \
  xargs -I {} gh codespace stop --codespace {}
```

**Best for:** Predictable work schedules. Minimize overnight costs.

---

### Pattern: Delete Completed Work

```bash
# After PR merged, delete Codespace
gh codespace delete --codespace feature-auth-abc123

# Create new for next feature
gh codespace create --repo user/project --branch feature/next
```

**Best for:** Short-lived feature branches. No accumulation of old Codespaces.

---

## Anti-Patterns to Avoid

### ❌ Too Many Active Codespaces

**Problem:** 10+ active Codespaces, hard to track, unnecessary cost.

**Solution:** Limit to 3-5 active at once. Delete or stop others.

---

### ❌ Single Codespace for Everything

**Problem:** Loses isolation benefit. Context switching still required.

**Solution:** Use multiple Codespaces for different contexts.

---

### ❌ Never Stopping/Deleting

**Problem:** Accumulate dozens of unused Codespaces, high costs.

**Solution:** Weekly cleanup routine. Delete Codespaces older than 7 days.

---

### ❌ Using Largest Machine for Everything

**Problem:** Unnecessary costs. Most work doesn't need 8-core machines.

**Solution:** Use 2-core for most work. Upgrade only when needed.

---

## Quick Start Patterns

### Pattern: Copy This Routine

```bash
# Morning
alias morning='gh codespace code --repo work/main && gh codespace code --repo personal/side'

# Quick switch
alias work='gh codespace code --repo work/main'
alias side='gh codespace code --repo personal/side'

# Evening cleanup
alias evening='gh codespace list --json name,state | jq -r ".[] | select(.state==\"Available\") | .name" | xargs -I {} gh codespace stop --codespace {}'
```

Add to `~/.bashrc` or `~/.zshrc`.

---

## Measuring Success

**You're using Codespaces effectively when:**

✅ Can switch projects in < 30 seconds
✅ Never lose context switching between tasks
✅ Long operations complete during commute
✅ Can work from any device seamlessly
✅ Team collaboration is frictionless
✅ Costs are predictable and reasonable

**Red flags:**

❌ Confused which Codespace has which work
❌ Regularly recreating Codespaces from scratch
❌ Costs higher than expected
❌ Waiting for Codespaces to start (use prebuilds)

---

## Resources

**GitHub Documentation:**
- [Codespaces Overview](https://docs.github.com/en/codespaces)
- [Prebuilds](https://docs.github.com/en/codespaces/prebuilding-your-codespaces)
- [Billing](https://docs.github.com/en/billing/managing-billing-for-github-codespaces)

**Related Guides:**
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Initial setup
- [USAGE_GUIDE.md](USAGE_GUIDE.md) - Daily commands
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

---

**Next:** Explore these patterns in your daily work. Find what works for your workflow.
