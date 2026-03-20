---
description: "Dispatch OpenAI Codex CLI to review a PR or branch diff against Gitea. Codex runs with Gitea MCP for full PR context. Posts findings as PR comment."
category: code-review
effort: high
allowed-tools: Bash, Read, Glob, Grep
---

# /codex-review — Codex PR Review with Gitea Integration

Dispatch OpenAI Codex to review code changes. Codex has Gitea MCP registered, giving it access to PR metadata, comments, and the ability to post review findings.

## Arguments

Parse the user's input:

| Pattern | Behavior |
|---------|----------|
| `/codex-review` | Auto-detect: find open PR for current branch, or review branch diff |
| `/codex-review #123` | Review PR #123 by number |
| `/codex-review --base develop` | Review diff against specific base branch |
| `/codex-review --uncommitted` | Review uncommitted local changes |
| `/codex-review "focus on security"` | Custom review instructions |

## Step 0: Preflight Checks

Run ALL checks in parallel:

```bash
# Check 1: OPENAI_API_KEY
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+set (${#OPENAI_API_KEY} chars)}"

# Check 2: Codex CLI
npx @openai/codex --version 2>&1

# Check 3: Gitea MCP registered with Codex
npx @openai/codex mcp list 2>&1

# Check 4: Git state
git rev-parse --abbrev-ref HEAD 2>/dev/null
```

**Stop conditions:**
- No `OPENAI_API_KEY` → STOP. Tell user: `export OPENAI_API_KEY="sk-..." in .bash_profile`
- No Codex CLI → STOP. Tell user: `npm install -g @openai/codex`
- No `gitea` in MCP list → Run: `npx @openai/codex mcp add gitea --env "GITEA_TOKEN=8b07dad95e88429dd611b7f82c2ceb46dc18f507" -- "C:/claude/gitea-mcp-bin/gitea-mcp.exe" -t stdio --host "https://gitea.ergonet.pl:3001"`

## Step 1: Resolve PR Context

If the user gave a PR number, use it directly. Otherwise, detect:

```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)
BASE=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
[ -z "$BASE" ] && BASE="main"
echo "BRANCH: $BRANCH"
echo "BASE: $BASE"
```

Then use Gitea MCP to find an open PR for this branch:
- Call `mcp__gitea__list_repo_pull_requests` with `owner="admin"`, `repo=<detected-from-origin>`, `state="open"`
- Find a PR where `head.ref == $BRANCH`
- If found: capture PR number, title, body
- If not found: proceed with branch diff only (no PR comment posting)

Extract the repo name from the git remote:
```bash
REPO=$(git remote get-url origin 2>/dev/null | sed -E 's|.*/([^/]+)\.git$|\1|; s|.*/([^/]+)$|\1|')
echo "REPO: $REPO"
```

## Step 2: Get the Diff

```bash
BASE=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
[ -z "$BASE" ] && BASE="main"
DIFF_STAT=$(git diff "origin/$BASE" --stat 2>/dev/null | tail -1)
echo "DIFF_STAT: $DIFF_STAT"
```

If `--uncommitted` was specified, use `git diff HEAD` instead.

## Step 3: Dispatch Codex Review

Build the Codex review command based on context:

### Standard branch review (most common):
```bash
npx @openai/codex review \
  --base "$BASE" \
  "Review this code for:
1. [P1 CRITICAL] Security vulnerabilities, data loss, production-breaking bugs
2. [P2 IMPORTANT] Race conditions, missing error handling, bad trust boundaries
3. [P3 INFORMATIONAL] Code quality, naming, test gaps

For each finding: [P1/P2/P3] file:line — description.
If no issues: LGTM — no issues found.

Use the gitea MCP tools to read PR context if PR #${PR_NUMBER:-none} exists.
${CUSTOM_INSTRUCTIONS:-}" 2>&1
```

### Uncommitted changes:
```bash
npx @openai/codex review \
  --uncommitted \
  "${CUSTOM_INSTRUCTIONS:-Review for bugs, security issues, and code quality.}" 2>&1
```

**Timeout:** 300000ms (5 minutes). If Codex hangs, kill and report.

**Capture the full output** — store in a variable for presentation and optional PR posting.

## Step 4: Present Results

```
CODEX REVIEW:
════════════════════════════════════════════════════════════
<full Codex output verbatim — do not truncate or summarize>
════════════════════════════════════════════════════════════
Engine: Codex (codex-cli)    Model: o3
```

Parse output for P1/P2/P3 markers:
- Any `[P1]` → **GATE: FAIL**
- Only `[P2]`/`[P3]` or clean → **GATE: PASS**

```
GATE: PASS/FAIL    Findings: N P1, N P2, N P3
```

## Step 5: Post to Gitea PR (if PR exists)

If a PR was found in Step 1, offer to post findings:

> Codex found N findings on PR #X. Post as PR comment? [y/n]

If user says yes, use `mcp__gitea__create_issue_comment` to post:

```markdown
## Codex Review — [ENGINE: codex-cli]

**Gate:** PASS/FAIL | **Findings:** N P1, N P2, N P3

<findings formatted as markdown>

---
*Automated review by Codex via Amplifier `/codex-review`*
```

If user says no, or no PR exists, skip.

## Step 6: Cross-Model Comparison (if applicable)

If `/gemini-review`, `/second-opinion`, or any review command was already run in this conversation, compare:

```
CROSS-MODEL ANALYSIS:
  Both found:        [overlapping findings]
  Only Codex found:  [unique to Codex]
  Only OTHER found:  [unique to other engine]
  Agreement: X%
```

## Important Rules

- **Never modify code.** This command is READ-ONLY. Codex runs in read-only sandbox.
- **Present output verbatim.** Do not truncate or editorialize before showing.
- **5-minute timeout** on Codex. Kill if stuck.
- **Always check OPENAI_API_KEY first.** Don't let Codex fail with a cryptic auth error.
- **Gitea MCP is for context and posting, not for fetching diffs.** Git handles diffs locally.
