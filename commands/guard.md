---
description: "Safety mode: destructive command warnings + directory-scoped edit restrictions. Use when touching prod, debugging live systems, or wanting to scope changes. Modes: careful (warn on destructive), freeze (restrict edits to directory), guard (both)."
---

# /guard — Safety Mode

Activate safety guardrails for the current session. Three levels:

| Level | What it does |
|-------|-------------|
| `/guard careful` | Warn before destructive bash commands (rm -rf, DROP TABLE, force-push, etc.) |
| `/guard freeze <dir>` | Block Edit/Write outside a specific directory |
| `/guard` (no args) | Both: destructive warnings + directory restriction |
| `/guard off` or `/unfreeze` | Remove all restrictions |

## Step 0: Parse Arguments

- `/guard` → activate both careful + freeze (ask for directory)
- `/guard careful` → activate destructive command warnings only
- `/guard freeze <path>` → activate edit restriction to `<path>`
- `/guard freeze` (no path) → ask user for directory
- `/guard off` → deactivate all

## Step 1: Careful Mode — Destructive Command Detection

When careful mode is active, before EVERY Bash command you run, check it against these patterns:

| Pattern | Risk |
|---------|------|
| `rm -rf` / `rm -r` / `rm --recursive` | Recursive delete |
| `DROP TABLE` / `DROP DATABASE` / `TRUNCATE` | Data loss |
| `git push --force` / `git push -f` | History rewrite |
| `git reset --hard` | Uncommitted work loss |
| `git checkout .` / `git restore .` | Uncommitted work loss |
| `git clean -f` / `git clean -fd` | Untracked file deletion |
| `kubectl delete` | Production impact |
| `docker rm -f` / `docker system prune` | Container/image loss |
| `Stop-WebAppPool` / `Remove-Item -Recurse` | IIS/Windows service impact |
| `powershell.*-Force.*Remove` | Force deletion |

**Safe exceptions** (allow without warning):
- `rm -rf node_modules`, `.next`, `dist`, `__pycache__`, `.cache`, `build`, `.turbo`, `coverage`, `bin/Debug`, `bin/Release`, `obj`

**When a destructive pattern is detected:**
1. STOP before executing
2. Show the user: "**DESTRUCTIVE COMMAND DETECTED:** `<command>` — Risk: `<risk description>`"
3. Ask: "Proceed? (yes/no)"
4. Only execute if user confirms

## Step 2: Freeze Mode — Directory-Scoped Edits

When freeze mode is active, before EVERY Edit or Write operation:

1. Check if the target file path starts with the allowed directory
2. If outside the boundary → STOP and tell the user: "**BLOCKED:** Edit to `<path>` is outside the freeze boundary `<freeze_dir>`. Use `/guard off` to remove the restriction."
3. If inside → proceed normally

**Setting the freeze boundary:**

If no directory was provided, ask the user:
"Which directory should edits be restricted to? Files outside this path will be blocked."

Once provided, resolve to absolute path and remember it for the session.

**Path normalization (critical for cross-platform):**
- Normalize BOTH the freeze directory AND the target file path before comparing
- Convert all backslashes (`\`) to forward slashes (`/`) on both sides
- Convert to lowercase on Windows (case-insensitive filesystem)
- Compare using forward-slash normalized paths: `C:\repo\src\file.py` → `c:/repo/src/file.py`
- The freeze directory should end with `/` after normalization

**Scope notes:**
- Freeze applies to Edit and Write tools ONLY — Read, Bash, Glob, Grep are unaffected
- This prevents accidental edits, not a security boundary
- Bash commands (sed, echo >) can still modify files outside the boundary

## Step 3: Confirmation

Tell the user what's active:

For **careful** only:
"**Careful mode active.** Destructive commands (rm -rf, DROP TABLE, force-push, etc.) will warn before executing. You can always override."

For **freeze** only:
"**Freeze mode active.** File edits restricted to `<path>/`. Edits outside this directory are blocked."

For **guard** (both):
"**Guard mode active.** Two protections running:
1. **Destructive command warnings** — rm -rf, DROP TABLE, force-push, etc.
2. **Edit boundary** — file edits restricted to `<path>/`."

For **off:**
"**Guard mode deactivated.** All restrictions removed."

## Important Rules

- Guard mode is **session-scoped** — it deactivates when the conversation ends
- The freeze directory must be an absolute path
- Add trailing `/` to freeze directory to prevent `/src` matching `/src-old`
- This is a cognitive guardrail, not a security sandbox
- When in doubt, warn rather than silently proceeding
