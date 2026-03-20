---
description: "Safety mode: destructive command warnings + directory-scoped edit restrictions. Use when touching prod, debugging live systems, or wanting to scope changes. Modes: careful (warn on destructive), freeze (restrict edits to directory), guard (both)."
---

# /guard — Safety Mode

Activate **advisory** safety guardrails for the current session. This is a cognitive safety net to prevent accidental damage — NOT a security sandbox. Bash commands can still bypass freeze boundaries (sed -i, tee, cp, etc.).

Three levels:

| Level | What it does |
|-------|-------------|
| `/guard careful` | Warn before destructive bash commands (rm -rf, DROP TABLE, force-push, etc.) |
| `/guard freeze <dir>` | Block Edit/Write outside a specific directory |
| `/guard` (no args) | Both: destructive warnings + directory restriction |
| `/guard off` or `/unfreeze` | Remove all restrictions (requires confirmation) |

## Step 0: Parse Arguments

- `/guard` → activate both careful + freeze (ask for directory)
- `/guard careful` → activate destructive command warnings only
- `/guard freeze <path>` → activate edit restriction to `<path>`
- `/guard freeze` (no path) → ask user for directory
- `/guard off` → ask for confirmation, then deactivate all

## Step 1: Careful Mode — Destructive Command Detection

When careful mode is active, before EVERY Bash command you run, check it against these patterns:

### Destructive patterns (always warn)

| Pattern | Risk |
|---------|------|
| `rm -rf` / `rm -r` / `rm --recursive` | Recursive delete |
| `find` with `-delete` or `-exec rm` | Recursive delete |
| `DROP TABLE` / `DROP DATABASE` / `TRUNCATE` / `DROP SCHEMA` | Data loss |
| `git push --force` / `git push -f` / `git push --force-with-lease` | History rewrite |
| `git reset --hard` | Uncommitted work loss |
| `git checkout .` / `git restore .` | Uncommitted work loss |
| `git clean -f` / `git clean -fd` / `git clean -ffdx` | Untracked file deletion |
| `kubectl delete` / `helm uninstall` / `helm delete` | Production impact |
| `docker rm -f` / `docker system prune` | Container/image loss |
| `terraform destroy` / `terraform apply -auto-approve` | Infrastructure destruction |
| `dd if=` / `mkfs` | Disk/filesystem destruction |
| `Stop-WebAppPool` / `Remove-Item -Recurse` / `Remove-Item.*-Force` | IIS/Windows service impact |

### Risky verb patterns (warn if targeting non-workspace paths)

Also warn on commands containing these verbs when targeting paths outside the current workspace:
`delete`, `destroy`, `prune`, `format`, `truncate`, `wipe`, `purge`, `nuke`

Apply best-effort pattern matching — if the target path cannot be determined from context, err on the side of warning.

### Safe exceptions (allow without warning)

Only when the target is a **workspace-relative path** (inside the current git repo or working directory):
- `rm -rf node_modules`, `.next`, `dist`, `__pycache__`, `.cache`, `build`, `.turbo`, `coverage`, `bin/Debug`, `bin/Release`, `obj`

**NOT safe:** `rm -rf /var/www/app/dist`, `rm -rf ../dist`, `rm -rf ~/dist` — these target paths outside the workspace and MUST still warn.

To determine workspace root: `git rev-parse --show-toplevel 2>/dev/null || pwd`

If workspace root cannot be determined, treat the target as outside the workspace and warn.

### When a destructive pattern is detected:
1. STOP before executing
2. Show the user: "**DESTRUCTIVE COMMAND DETECTED:** `<command>` — Risk: `<risk description>`"
3. Ask: "Proceed? (yes/no)"
4. Only execute if user confirms

## Step 2: Freeze Mode — Directory-Scoped Edits

When freeze mode is active, before EVERY Edit or Write operation:

1. Canonicalize both the freeze directory and the target file path (see normalization below)
2. Check if the canonicalized target starts with the canonicalized freeze directory
3. If outside the boundary → STOP and tell the user: "**BLOCKED:** Edit to `<path>` is outside the freeze boundary `<freeze_dir>`. Use `/guard off` to remove the restriction."
4. If inside → proceed normally

**Setting the freeze boundary:**

If no directory was provided, ask the user:
"Which directory should edits be restricted to? Files outside this path will be blocked."

Once provided, resolve to absolute path and remember it for the session.

**Path canonicalization (critical for cross-platform):**
- Resolve to absolute path (no relative components)
- Collapse all `.` and `..` segments
- Resolve symlinks where possible (use `realpath` on Linux, or resolve manually)
- Convert all backslashes (`\`) to forward slashes (`/`) on both sides
- Convert to lowercase on Windows (case-insensitive filesystem)
- The freeze directory must end with `/` after normalization
- Example: `C:\repo\..\repo\src\file.py` → `c:/repo/src/file.py`

**Known limitation — advisory, not security:**
- Freeze applies to Edit and Write tools ONLY — Read, Bash, Glob, Grep are unaffected
- Bash commands (sed -i, tee, cp, mv, echo >, heredocs) can still modify files outside the boundary
- This prevents ACCIDENTAL edits via Claude's Edit/Write tools, not deliberate bypasses
- For true isolation, use `/worktree` to create a separate git workspace

## Step 3: Deactivation (requires confirmation)

When the user runs `/guard off` or `/unfreeze`:

1. **Ask for confirmation:** "Guard mode is currently active. Are you sure you want to disable all protections?"
   - A) Yes, disable guard mode
   - B) Keep guard mode active
2. Only deactivate if the user explicitly confirms (option A)
3. Tell the user: "**Guard mode deactivated.** All restrictions removed."

This prevents accidental deactivation and raises the bar for injected deactivation (though a multi-turn injection could still bypass it).

## Step 4: Confirmation (on activation)

Tell the user what's active:

For **careful** only:
"**Careful mode active.** Destructive commands (rm -rf, DROP TABLE, force-push, terraform destroy, etc.) will warn before executing. You can always override. This is an advisory guardrail, not a security sandbox."

For **freeze** only:
"**Freeze mode active.** File edits (Edit/Write tools) restricted to `<path>/`. Edits outside this directory are blocked. Note: Bash commands can still write outside the boundary — this prevents accidental edits, not deliberate bypasses."

For **guard** (both):
"**Guard mode active.** Two protections running:
1. **Destructive command warnings** — rm -rf, DROP TABLE, force-push, terraform destroy, etc.
2. **Edit boundary** — Edit/Write tools restricted to `<path>/`.
Both are advisory guardrails. Use `/guard off` (with confirmation) to disable."

## Subagent Propagation

When dispatching subagents (via Agent tool, `/parallel-agents`, `/subagent-dev`):
- **Include guard state in subagent prompts:** If guard mode is active, prepend to the subagent prompt: "GUARD MODE ACTIVE: Do not edit files outside `<freeze_dir>`. Warn before destructive commands."
- This is best-effort — subagents don't inherit hooks, so propagation relies on prompt instructions
- For critical work, prefer `/worktree` isolation over guard mode

## Important Rules

- Guard mode is **session-scoped** — it deactivates when the conversation ends
- The freeze directory must be an absolute, canonicalized path
- This is an **advisory cognitive guardrail**, not a security sandbox
- When in doubt, warn rather than silently proceeding
- Deactivation requires explicit user confirmation
- Subagent guard state is propagated via prompt instructions (best-effort)
