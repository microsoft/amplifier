---
description: Dispatch Gemini (via OpenCode) to review a PR or branch diff against Gitea. Gemini runs with Gitea MCP for full PR context. Posts findings as PR comment.
category: code-review
effort: medium
allowed-tools: Bash, Read, Glob, Grep
---
# /gemini-review — Gemini PR Review with Gitea Integration

Dispatch Google Gemini (via OpenCode) to review code changes. OpenCode already has Gitea MCP configured, giving Gemini access to PR metadata, comments, and the ability to understand full repo context.

## Arguments

Parse the user's input:

| Pattern | Behavior |
|---------|----------|
| `/gemini-review` | Auto-detect: find open PR for current branch, or review branch diff |
| `/gemini-review #123` | Review PR #123 by number |
| `/gemini-review --base develop` | Review diff against specific base branch |
| `/gemini-review --uncommitted` | Review uncommitted local changes |
| `/gemini-review "focus on security"` | Custom review instructions |

## Step 0: Preflight Checks

Run ALL checks in parallel:

```bash
# Check 1: OpenCode available
opencode --version 2>&1

# Check 2: Gitea MCP in OpenCode
opencode mcp list 2>&1

# Check 3: Git state
git rev-parse --abbrev-ref HEAD 2>/dev/null
```

**Stop conditions:**
- No `opencode` → STOP. Tell user to install OpenCode.
- No `gitea` in MCP list → STOP. Tell user Gitea MCP is missing from OpenCode config.

## Step 1: Resolve PR Context

If the user gave a PR number, use it directly. Otherwise, detect:

```bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)
BASE=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
[ -z "$BASE" ] && BASE="main"
REPO=$(git remote get-url origin 2>/dev/null | sed -E 's|.*/([^/]+)\.git$|\1|; s|.*/([^/]+)$|\1|')
echo "BRANCH: $BRANCH | BASE: $BASE | REPO: $REPO"
```

Then use Gitea MCP (`mcp__gitea__list_repo_pull_requests`) to find an open PR for this branch:
- `owner="admin"`, `repo=$REPO`, `state="open"`
- Find PR where `head.ref == $BRANCH`
- If found: capture PR number, title, body
- If not found: proceed with branch diff only

## Step 2: Get the Diff

```bash
BASE=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
[ -z "$BASE" ] && BASE="main"

DIFF_FILE=$(mktemp /tmp/gemini-review-diff-XXXXXX.txt)
git diff "origin/$BASE" > "$DIFF_FILE" 2>/dev/null || git diff "$BASE" > "$DIFF_FILE" 2>/dev/null
DIFF_SIZE=$(wc -c < "$DIFF_FILE" | tr -d ' ')
echo "DIFF_FILE: $DIFF_FILE ($DIFF_SIZE bytes)"
```

If `--uncommitted`, use `git diff HEAD` instead.

If diff is empty, check for uncommitted changes with `git diff HEAD`. If still empty, STOP: "No changes to review."

## Step 3: Dispatch Gemini via OpenCode

Build the review prompt and pipe the diff:

```bash
DIFF_FILE=$(mktemp /tmp/gemini-review-diff-XXXXXX.txt)
git diff "origin/$BASE" > "$DIFF_FILE"

REVIEW_PROMPT="You are an independent code reviewer. Be direct, terse, technically precise.

Review this diff for:
1. [P1 CRITICAL] Security vulnerabilities, data loss risks, production-breaking bugs
2. [P2 IMPORTANT] Race conditions, N+1 queries, missing error handling, bad trust boundaries
3. [P3 INFORMATIONAL] Code quality, naming, test gaps, dead code

For each finding, output EXACTLY:
[P1/P2/P3] file:line — description

If no issues found, say: LGTM — no issues found.

You have Gitea MCP tools available. If PR #${PR_NUMBER:-none} exists on repo admin/${REPO}, use gitea tools to read PR description and any existing comments for additional context.

${CUSTOM_INSTRUCTIONS:+ADDITIONAL INSTRUCTIONS: $CUSTOM_INSTRUCTIONS}

THE DIFF:
$(cat "$DIFF_FILE")"

opencode run -m google/gemini-3.1-pro-preview "$REVIEW_PROMPT" 2>/dev/null
rm -f "$DIFF_FILE"
```

**Model selection:**
- Default: `google/gemini-3.1-pro-preview` (best reasoning for code review)
- Fallback for lighter reviews: `google/gemini-3.0-flash-preview`
- Gemini has Gitea MCP via OpenCode config — it can call gitea tools natively

**Timeout:** 300000ms (5 minutes). If OpenCode hangs, kill and report.

**Capture the full output** for presentation and optional PR posting.

## Step 4: Present Results

```
GEMINI REVIEW:
════════════════════════════════════════════════════════════
<full Gemini output verbatim — do not truncate or summarize>
════════════════════════════════════════════════════════════
Engine: Gemini    Model: gemini-3.1-pro-preview    via: OpenCode
```

Parse output for P1/P2/P3 markers:
- Any `[P1]` → **GATE: FAIL**
- Only `[P2]`/`[P3]` or clean → **GATE: PASS**

```
GATE: PASS/FAIL    Findings: N P1, N P2, N P3
```

## Step 5: Post to Gitea PR (if PR exists)

If a PR was found in Step 1, offer to post findings:

> Gemini found N findings on PR #X. Post as PR comment? [y/n]

If user says yes, use `mcp__gitea__create_issue_comment` to post:

```markdown
## Gemini Review — [ENGINE: gemini-3.1-pro-preview]

**Gate:** PASS/FAIL | **Findings:** N P1, N P2, N P3

<findings formatted as markdown>

---
*Automated review by Gemini via Amplifier `/gemini-review`*
```

If user says no, or no PR exists, skip.

## Step 6: Cross-Model Comparison (if applicable)

If `/codex-review`, `/second-opinion`, or any review command was already run in this conversation, compare:

```
CROSS-MODEL ANALYSIS:
  Both found:        [overlapping findings]
  Only Gemini found: [unique to Gemini]
  Only OTHER found:  [unique to other engine]
  Agreement: X%
```

## Important Rules

- **Never modify code.** This command is READ-ONLY.
- **Present output verbatim.** Do not truncate or editorialize before showing.
- **5-minute timeout** on OpenCode. Kill if stuck.
- **Clean up temp files** after every run.
- **Gitea MCP is for context and posting, not for fetching diffs.** Git handles diffs locally.
- **Gemini has long context** — don't worry about diff size, Gemini handles large diffs well.
