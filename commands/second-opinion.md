---
description: "Quick second opinion from Claude Sonnet: review diffs, challenge code adversarially, or consult on a question. For Codex or Gemini reviews with Gitea integration, use /codex-review or /gemini-review instead."
effort: high
---

# /second-opinion — Sonnet Second Opinion

Get a fast, independent review from Claude Sonnet. Three modes: review, challenge, consult.

For full Gitea-integrated reviews with other engines, use `/codex-review` (OpenAI) or `/gemini-review` (Google).

## Arguments

| Pattern | Mode | Example |
|---------|------|---------|
| `/second-opinion` (no args) | auto-detect | Checks for diff → review, else → consult |
| `/second-opinion review [instructions]` | review | `/second-opinion review focus on security` |
| `/second-opinion challenge [focus]` | challenge | `/second-opinion challenge race conditions` |
| `/second-opinion consult <question>` | consult | `/second-opinion consult is this auth pattern safe?` |

## Step 1: Detect Mode (if not specified)

If the user didn't specify a mode:

1. Check for a diff against the base branch:
```bash
BASE=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
[ -z "$BASE" ] && BASE="main"
DIFF_STAT=$(git diff "origin/$BASE" --stat 2>/dev/null | tail -1)
echo "BASE: $BASE"
echo "DIFF: $DIFF_STAT"
```

2. If a diff exists → default to **review** mode
3. If no diff → ask the user:
   - A) Review uncommitted changes (`--uncommitted`)
   - B) Consult — I have a question
   - C) Challenge — try to break recent code

## Step 2: Get the Diff (review and challenge modes)

```bash
BASE=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
[ -z "$BASE" ] && BASE="main"
DIFF_FILE=$(mktemp /tmp/second-opinion-diff-XXXXXX.txt)
git diff "origin/$BASE" > "$DIFF_FILE" 2>/dev/null || git diff "$BASE" > "$DIFF_FILE" 2>/dev/null
DIFF_SIZE=$(wc -c < "$DIFF_FILE" | tr -d ' ')
echo "DIFF_SIZE: $DIFF_SIZE bytes"
```

If the diff is empty, check for uncommitted changes: `git diff HEAD > "$DIFF_FILE"`

## Step 3A: Review Mode

```bash
DIFF_FILE=$(mktemp /tmp/second-opinion-diff-XXXXXX.txt)
git diff "origin/$BASE" > "$DIFF_FILE"

REVIEW_PROMPT="You are an independent code reviewer. Be direct, terse, and technically precise.

Review this diff for:
1. [P1 CRITICAL] Security vulnerabilities, data loss risks, production-breaking bugs
2. [P2 IMPORTANT] Race conditions, N+1 queries, missing error handling, bad trust boundaries
3. [P3 INFORMATIONAL] Code quality, naming, test gaps, dead code

For each finding, output:
[P1/P2/P3] file:line — description

If no issues found, say: LGTM — no issues found.

USER INSTRUCTIONS: ${REVIEW_INSTRUCTIONS:-none}

THE DIFF:
$(cat "$DIFF_FILE")"

echo "$REVIEW_PROMPT" | claude --print --model sonnet --system-prompt "You are a paranoid staff engineer doing a pre-landing code review. Output ONLY findings, no preamble." --no-session-persistence 2>/dev/null
rm -f "$DIFF_FILE"
```

### After review output

1. Parse output for P1/P2/P3 markers
2. Gate verdict:
   - Any `[P1]` → **FAIL**
   - Only `[P2]`/`[P3]` or no findings → **PASS**

3. Present:

```
SECOND OPINION (Sonnet — review):
════════════════════════════════════════════════════════════
<full output verbatim — do not truncate or summarize>
════════════════════════════════════════════════════════════
GATE: PASS/FAIL    Engine: Sonnet    Findings: N P1, N P2, N P3
```

4. **Cross-model comparison:** If `/codex-review` or `/gemini-review` was already run in this conversation, compare findings:

```
CROSS-MODEL ANALYSIS:
  Both found:        [findings that overlap]
  Only Sonnet found: [unique to Sonnet]
  Only OTHER found:  [unique to other engine]
  Agreement: X%
```

## Step 3B: Challenge Mode (Adversarial)

```bash
DIFF_FILE=$(mktemp /tmp/second-opinion-diff-XXXXXX.txt)
git diff "origin/$BASE" > "$DIFF_FILE"

CHALLENGE_PROMPT="Review the changes in this diff. Your job is to find ways this code will FAIL in production. Think like an attacker and a chaos engineer. Find: edge cases, race conditions, security holes, resource leaks, failure modes, silent data corruption. Be adversarial. Be thorough. No compliments — just the problems.

${FOCUS:+Focus specifically on: $FOCUS}

THE DIFF:
$(cat "$DIFF_FILE")"

echo "$CHALLENGE_PROMPT" | claude --print --model sonnet --system-prompt "You are a chaos engineer and security researcher. Find every way this code can fail." --no-session-persistence 2>/dev/null
rm -f "$DIFF_FILE"
```

Present:
```
SECOND OPINION (Sonnet — adversarial challenge):
════════════════════════════════════════════════════════════
<full output verbatim>
════════════════════════════════════════════════════════════
Engine: Sonnet
```

## Step 3C: Consult Mode (Freeform)

```bash
echo "$QUESTION" | claude --print --model sonnet --add-dir . --no-session-persistence 2>/dev/null
```

Present:
```
SECOND OPINION (Sonnet — consult):
════════════════════════════════════════════════════════════
<full output verbatim>
════════════════════════════════════════════════════════════
Engine: Sonnet
```

After presenting, note any points where you (Claude Opus) disagree:
"**Claude's take:** I disagree on X because Y." or "**Claude's take:** I agree with all points."

## Important Rules

- **Never modify files.** This command is READ-ONLY.
- **Present output verbatim.** Do not truncate, summarize, or editorialize before showing.
- **Add synthesis AFTER, not instead of.** Any Claude commentary comes after the full output.
- **5-minute timeout** on all calls (`timeout: 300000` on Bash).
- **Clean up temp files** after every call.
- **For Codex or Gemini reviews:** Tell user to use `/codex-review` or `/gemini-review` instead.
