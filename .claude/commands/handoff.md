---
description: "Manage the full Claude ↔ Gemini handoff workflow. Auto-detects state from HANDOFF.md and executes the right phase: dispatch, monitor, review, merge, deploy, close."
---

# Handoff — Claude ↔ Gemini Task Workflow

## Overview

Single command that manages the entire handoff lifecycle between Claude Code (senior) and Gemini/OpenCode (junior). Reads HANDOFF.md state, determines the current phase, executes the appropriate action.

**Core principle:** Read state → Act on state → Advance state → Commit.

**Announce at start:** "I'm using the handoff command to manage the Claude ↔ Gemini workflow."

## Argument Handling

Parse `$ARGUMENTS`:

| Input | Action |
|-------|--------|
| `help` | Display help reference card → stop |
| `status` | Display current state summary → stop |
| `reset` | Force reset to IDLE with confirmation → stop |
| `<task description>` | Dispatch to Gemini (only valid when IDLE) |
| _(empty)_ | Auto-detect state and act |

## The Process

### Step 1: Read Current State

```bash
grep "^## Dispatch Status:" HANDOFF.md
```

Extract status: `IDLE`, `WAITING_FOR_GEMINI`, `IN_PROGRESS`, `PR_READY`, `REVIEWING`, `DEPLOYING`.

If HANDOFF.md missing or unparseable → report error and stop.

### Step 2: Guard Check

If `$ARGUMENTS` contains a task description AND state is NOT `IDLE`:
```
Cannot dispatch — current status is <STATE>.
A task is already active: <objective>

To dispatch a new task, first complete or reset the current cycle:
  /handoff        → continue the current workflow
  /handoff reset  → force back to IDLE (discards current task)
```
Stop. Do not proceed.

### Step 3: Route by State

Read the state extracted in Step 1 and branch:

```
if state == "IDLE"                → go to "State: IDLE"
if state == "WAITING_FOR_GEMINI"  → go to "State: WAITING_FOR_GEMINI"
if state == "IN_PROGRESS"         → go to "State: IN_PROGRESS"
if state == "PR_READY"            → go to "State: PR_READY"
if state == "REVIEWING"           → go to "State: REVIEWING"
if state == "DEPLOYING"           → go to "State: DEPLOYING"
otherwise                         → report "Unknown state: <value>" and stop
```

Execute **only** the matching state section below.

---

#### State: IDLE — Dispatch Task to Gemini

**Requires:** Task description from `$ARGUMENTS`. If empty, ask: "What task should I dispatch to Gemini?"

**2a. Parse intent** from the task description:
- **Objective** — one clear sentence
- **Branch name** — `feature/<kebab-case-summary>` (max 50 chars)
- **Priority** — detect `urgent` from language, otherwise `normal`

**2b. Gather context** — Dispatch a lightweight scout:

```
Task(subagent_type="agentic-search", model="haiku", max_turns=8,
  description="Scout files for handoff task",
  prompt="
    Find files related to this task: [task description]
    1. Search docs/specs/ for relevant spec files
    2. Identify source files that would need modification
    3. Suggest which agent tiers Gemini might need (senior-review or design-specialist)
    4. Map each part of the task to a Gemini agent from C:\Przemek\agents\:
       - modular-builder: code implementation (models, services, endpoints)
       - component-designer: UI components (Blazor pages, forms)
       - database-architect: schema design, migrations, repositories
       - api-contract-designer: API endpoint contracts
       - agentic-search: codebase exploration before implementation
       - bug-hunter: debugging, fixing issues
       - test-coverage: writing tests
    Return: spec path (if found), file list (paths only), tier unlock suggestions, agent assignment table
")
```

**2c. Build HANDOFF.md template** — Fill all fields:

```markdown
## Dispatch Status: WAITING_FOR_GEMINI

## Current Task

**From:** Claude → Gemini
**Branch:** feature/<derived-name>
**Priority:** normal | urgent
**Repository:** [exact repo path, e.g. C:\claude\fusecp-enterprise]
**Working Directory:** [where to run commands from, e.g. C:\claude\fusecp-enterprise]
**PR Target:** [target branch + repo for the PR, e.g. main on psklarkins/fusecp-enterprise]

### Objective
[One sentence from user's description]

### Detailed Requirements
[Specific, concrete changes needed. NOT vague — list exactly what to do with file paths and patterns to follow. If Gemini needs to follow an existing pattern, show the pattern inline or reference the exact file:line.]

### Spec
[Link to spec if found by scout, or "Inline — see Objective and Detailed Requirements"]

### Context Loading (use your full 1M context)
Load these files completely before starting:
- [relevant files from scout — full paths]
- COWORK.md — refresh protocol understanding
- This task section of HANDOFF.md

### Files YOU May Modify
- [concrete paths from scout]

### Files You Must NOT Modify
- .claude/* (always)
- CLAUDE.md (always)
- C:\FuseCP\* (always)
- C:\Przemek\OPENCODE.md (always)

### Acceptance Criteria
- [ ] [derived from objective — specific, testable]
- [ ] [additional criteria as needed]
- [ ] All tests pass
- [ ] No lint errors
- [ ] Code committed to feature branch with clear messages

### Build & Verify (MUST complete before creating PR)

Run these commands and confirm they pass. Do NOT create a PR until all pass:

```bash
[exact build command, e.g. cd /c/claude/fusecp-enterprise/src/FuseCP.Portal && dotnet build --configuration Release]
```

Expected: Build succeeded, 0 errors.

If build fails, fix the errors before proceeding. Include build output summary in PR description.

### Agent Assignments (MANDATORY — use subagents for implementation)

You MUST use your agents at `C:\Przemek\agents\` for this task. Do NOT implement everything in your main context — delegate to specialized agents.

| Task | Agent | What to delegate |
|------|-------|-----------------|
[Claude fills this table mapping each part of the work to a specific agent. Example:]
| [Part description] | [agent-name] | [specific deliverable] |

**How to use agents:** For each row above, dispatch the agent as a subagent with a focused prompt describing exactly what to implement. The agent will do the work and return results. Review the output, fix any issues, then move to the next task.

**Agent tier unlocks:** [primary + knowledge, or additional tiers if needed]
```

**2d. Present for confirmation.** Show the filled template to the user using AskUserQuestion:
- Option 1: "Approve and dispatch" — proceed to write
- Option 2: "Edit first" — ask what to change, update template, re-present
- Option 3: "Cancel" — abort dispatch, stay IDLE

Loop on Option 2 until user approves or cancels. Never write HANDOFF.md without explicit approval.

**2e. Write and commit:**
- Write template to HANDOFF.md (replace Current Task section, set status)
- Keep the State Transitions and History sections unchanged

```bash
git add HANDOFF.md && git commit -m "chore: dispatch task to Gemini — <objective summary>"
```

**2f. Report:**

```
Task dispatched.
  Status:   WAITING_FOR_GEMINI
  Branch:   feature/<name>
  Objective: <summary>

Next: Tell Gemini to check HANDOFF.md.
      Run /handoff to check progress.
```

---

#### State: WAITING_FOR_GEMINI — Monitor

Check if Gemini has started work:

```bash
# Check for feature branch
git branch -a | grep "feature/"

# Check for open PR
gh pr list --state open --json number,title,headRefName 2>/dev/null
```

**If PR found:** Offer to advance state:
```
Gemini has opened PR #<number>: <title>
Advance to PR_READY and start review? (yes/no)
```
If yes → use Edit tool to change `## Dispatch Status: WAITING_FOR_GEMINI` to `## Dispatch Status: PR_READY` in HANDOFF.md, then:
```bash
git add HANDOFF.md && git commit -m "chore: Gemini PR ready — advancing to review"
```
Then proceed immediately to the PR_READY phase below.

**If branch found but no PR:** Report and wait:
```
Status: WAITING_FOR_GEMINI
Task:   <objective>
Branch: <branch> (exists, no PR yet)

→ Gemini is working. Run /handoff again when PR is ready.
```

**If nothing found:** Report:
```
Status: WAITING_FOR_GEMINI
Task:   <objective>
Branch: <expected branch> (not created yet)

→ Tell Gemini to check HANDOFF.md and start working.
```

---

#### State: IN_PROGRESS — Monitor

Same checks as WAITING_FOR_GEMINI. If PR found, offer to advance to PR_READY.

```
Status: IN_PROGRESS
Task:   <objective>
Branch: <branch>

→ Waiting for Gemini to push PR.
→ Run /handoff again when PR is ready.
```

---

#### State: PR_READY — Review

**4a. Find the PR:**

```bash
gh pr list --state open --json number,title,headRefName,additions,deletions
```

Match by branch name from HANDOFF.md. If no PR found, report error.

**4b. Local build verification** — Before reviewing code, verify it builds:

```bash
# Checkout PR branch locally
git fetch origin
git checkout <branch-name>

# Run build command from HANDOFF.md "Build & Verify" section
# e.g.: cd /c/claude/fusecp-enterprise/src/FuseCP.Portal && dotnet build --configuration Release
```

If build fails → post build errors as PR comment, request changes, stay at PR_READY:
```bash
gh pr comment <number> --body "Build failed. Errors: <paste errors>. Please fix and push."
```

If build passes → proceed to code review.

**4c. Fetch PR details:**

```bash
gh pr view <number> --json title,body,additions,deletions,changedFiles
gh pr diff <number>
```

**4d. Dispatch review** — Run spec compliance and code quality checks in parallel:

```
>> Dispatching test-coverage (model: haiku) — spec compliance review

Task(subagent_type="test-coverage", model="haiku", max_turns=10,
  description="Spec compliance review for handoff PR",
  prompt="
    Review PR #<number> against these acceptance criteria:
    [paste acceptance criteria from HANDOFF.md]

    Run: gh pr diff <number>
    Read the actual code changes.
    Verify each acceptance criterion is met.
    Report: PASS or FAIL with specific file:line references.
")

>> Dispatching zen-architect (model: sonnet) — code quality review

Task(subagent_type="zen-architect", model="sonnet", max_turns=12,
  description="Code quality review for handoff PR",
  prompt="
    Code quality review for PR #<number>.
    Mode: REVIEW
    Run: gh pr diff <number>
    Review for: architecture alignment, code quality, simplicity, testing.
    Report: Strengths, Issues (Critical/Important/Minor), Assessment.
")
```

**4e. Consolidate and present findings.**

Both agents run in parallel via a single message with two Task calls. Wait for both to return, then merge:

- **Spec compliance** (test-coverage): Extract PASS/FAIL verdict and any unmet criteria
- **Code quality** (zen-architect): Extract Assessment (Approved/Needs changes) and issue list

Determine overall recommendation:
- If spec PASS **and** quality Approved → Recommend **Approve**
- If spec FAIL **or** quality has Critical issues → Recommend **Request Changes**
- If spec PASS **but** quality has Important (non-critical) issues → Present both options, let user decide

Present:

```
PR #<number> Review Results
═══════════════════════════
Spec Compliance: PASS/FAIL
  [list each acceptance criterion with check/cross]

Code Quality: Approved / Needs changes
  Strengths: [brief list]
  Issues: [Critical/Important/Minor with file:line refs]

Recommendation: Approve / Request Changes
  [reasoning in one sentence]
```

**4f. User decision:**

- **Approve (no issues)** → Update HANDOFF.md to `REVIEWING`, proceed to merge.

- **Approve + fix ourselves (default for non-critical issues)** → Merge the PR, then Claude fixes the review issues in a follow-up commit on master. This is faster than sending back to Gemini and avoids round-trip delays. After merge:
  1. Fix all Important/Minor issues identified in review
  2. Build and verify
  3. Commit with message referencing the PR: `fix: address review issues from PR #<number>`
  4. Proceed to REVIEWING → DEPLOYING.

- **Request changes (Critical issues only)** → Post review on PR:
  ```bash
  gh pr review <number> --request-changes --body "<consolidated review feedback>"
  ```
  Stay at PR_READY. Only use this for Critical issues that would be harder for Claude to fix than for Gemini to redo (e.g., fundamentally wrong approach, needs complete rewrite).

**Policy: Claude always fixes non-critical issues.** Sending work back to Gemini for minor/important fixes wastes time on round-trips. Claude is the senior developer and should fix review issues directly after merge.

---

#### State: REVIEWING — Merge & Deploy

**5a. Merge the PR:**

```bash
gh pr merge <number> --merge --delete-branch
git pull origin main
```

**5b. Update state** → Set `DEPLOYING` in HANDOFF.md, commit.

**5c. Ask about deployment** (CI/CD policy — always ask):

```
PR #<number> merged to main.

Deploy to local server?
  - This will build and deploy the project
  - Requires confirmation per CI/CD policy

Proceed with deployment? (yes/skip)
```

- **yes** → Run project-specific deploy steps (user provides or command detects from project)
- **skip** → Stay at DEPLOYING. User deploys manually, then runs `/handoff` to close.

---

#### State: DEPLOYING — Close Cycle

**6a. Verify deployment.** Check in this order:

1. If project has a test command (`make test`, `dotnet test`, `npm test`): run it
2. If project has a health endpoint: `curl -s http://localhost:<port>/health`
3. Otherwise: ask user "Did the deployment succeed? (yes/no)"

If verification fails → stay at DEPLOYING, report the failure, let user investigate.

**6b. Update history table** — Append row to the History section of HANDOFF.md:

```markdown
| <YYYY-MM-DD> | Gemini → Claude | <objective summary> | #<pr-number> | Success |
```

**6c. Clear task and set IDLE:**

Replace the Current Task section with:
```markdown
## Current Task

_No active task. Claude: write a task below and set status to WAITING_FOR_GEMINI._

### Task Template (copy when dispatching)
[keep the existing template reference]
```

Set `## Dispatch Status: IDLE`.

**6d. Commit:**

```bash
git add HANDOFF.md && git commit -m "chore: complete handoff cycle — <objective summary>"
```

**6e. Report:**

```
Handoff cycle complete.
  Task:   <objective>
  PR:     #<number>
  Result: Success

Status: IDLE — ready for next task.
Run /handoff <description> to dispatch.
```

---

## Help

When `$ARGUMENTS` equals `help`, display this reference card and **stop** (do not proceed with state detection):

```
HANDOFF — Claude ↔ Gemini Task Workflow
═══════════════════════════════════════

USAGE
  /handoff <task description>     Dispatch task to Gemini (when IDLE)
  /handoff                        Auto-detect state and act
  /handoff status                 Show current state + task summary
  /handoff reset                  Force IDLE (with confirmation)
  /handoff help                   This help

STATE MACHINE
  IDLE ──→ WAITING_FOR_GEMINI ──→ IN_PROGRESS ──→ PR_READY
    ↑                                                 │
    └──── DEPLOYING ←──── REVIEWING ←─────────────────┘

WHAT HAPPENS AT EACH STATE
  IDLE                Dispatch: parse task → build template → write HANDOFF.md
  WAITING_FOR_GEMINI  Monitor: check for branch/PR, report status
  IN_PROGRESS         Monitor: check for PR, report status
  PR_READY            Review: fetch PR → spec + quality review → approve/reject
  REVIEWING           Merge: merge PR → deploy (with confirmation)
  DEPLOYING           Close: verify → update history → set IDLE

BRANCH RULES
  Gemini works on:  feature/*  gemini/*
  Claude works on:  main  review/*  hotfix/*

EXAMPLES
  /handoff Add dark mode toggle to FuseCP portal sidebar
  /handoff Implement mailbox quota warnings per Phase 3 spec
  /handoff urgent: Fix broken login redirect on Exchange page
  /handoff status
  /handoff reset
```

## Status

When `$ARGUMENTS` equals `status`, display state summary and **stop**:

1. Read HANDOFF.md dispatch status
2. If active task exists:
   - Show: status, objective, branch, priority
   - Show time since dispatch: check `git log -1 --format="%ar" -- HANDOFF.md`
   - Show next action hint
3. If IDLE: show "No active task" and hint to dispatch
4. Show last 5 history entries (if any)

## Reset

When `$ARGUMENTS` equals `reset`:

1. **Confirm:** "This will clear the current task and force status to IDLE. Type 'reset' to confirm."
2. Wait for exact confirmation.
3. If confirmed:
   - Add history entry: `| <date> | — | <objective or "N/A"> | — | Reset by user |`
   - Clear Current Task section (restore template placeholder)
   - Set `## Dispatch Status: IDLE`
   - Commit: `chore: reset handoff state to IDLE`
4. If not confirmed: "Reset cancelled."

## Red Flags

**Never:**
- Dispatch while not IDLE (user must reset first)
- Skip user confirmation on dispatch template
- Merge PR without running both spec and quality review
- Deploy without user confirmation (CI/CD policy)
- Advance state without completing the phase's work
- Modify files in `C:\Przemek\` (Gemini's workspace)

**Always:**
- Read HANDOFF.md before acting
- Present dispatch template for user approval before writing
- Run parallel review (spec compliance + code quality) on PR
- Commit every state transition
- Update history table when closing the cycle
- Preserve the Task Template reference in HANDOFF.md when clearing

## Integration

**Delegates to (patterns, not direct command calls):**
- `/request-review` pattern — spec compliance (test-coverage) + code quality (zen-architect)
- `/finish-branch` pattern — PR merge and branch cleanup

**Works with:**
- `/create-plan` — Plans produce task descriptions that feed into `/handoff` dispatch
- `/brainstorm` — Designs feed into plans that feed into dispatch
- COWORK.md — Full protocol reference
- HANDOFF.md — State machine and task storage (this command's data file)

**Related files:**
- `HANDOFF.md` — Source of truth for dispatch state and task details
- `COWORK.md` — Roles, branches, boundaries, memory architecture
- `C:\Przemek\OPENCODE.md` — Gemini's identity and rules (read-only for Claude)
- `C:\Przemek\agents\` — Gemini's agent copies (managed by sync script)
