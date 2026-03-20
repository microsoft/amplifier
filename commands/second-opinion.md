---
description: "Multi-engine second opinion: review diffs, challenge code adversarially, or consult another AI. Engines: sonnet (default), gemini (OpenCode), codex (OpenAI). Use for independent code review, adversarial testing, or cross-model validation."
---

# /second-opinion — Multi-Engine Second Opinion

Get an independent review from a different AI engine. Three modes, three engines.

## Arguments

Parse the user's input for mode and engine:

| Pattern | Mode | Example |
|---------|------|---------|
| `/second-opinion` (no args) | auto-detect | Checks for diff → review, else → consult |
| `/second-opinion review [instructions]` | review | `/second-opinion review focus on security` |
| `/second-opinion challenge [focus]` | challenge | `/second-opinion challenge race conditions` |
| `/second-opinion consult <question>` | consult | `/second-opinion consult is this auth pattern safe?` |
| `--engine gemini` | use Gemini | `/second-opinion review --engine gemini` |
| `--engine codex` | use Codex | `/second-opinion challenge --engine codex` |
| `--engine sonnet` | use Sonnet | (default, explicit) |

## Step 0: Detect Platform and Available Engines

```bash
# Platform detection
PLATFORM=$(uname -s 2>/dev/null | tr '[:upper:]' '[:lower:]')
case "$PLATFORM" in
  *mingw*|*msys*|*cygwin*) PLATFORM="windows" ;;
  *linux*) PLATFORM="linux" ;;
  *darwin*) PLATFORM="macos" ;;
esac
echo "PLATFORM: $PLATFORM"

# Engine detection
ENGINES=""

# Sonnet — always available (claude CLI)
command -v claude >/dev/null 2>&1 && ENGINES="sonnet" && echo "ENGINE_SONNET: $(claude --version 2>/dev/null | head -1)"

# Gemini — via OpenCode
if command -v opencode >/dev/null 2>&1; then
  ENGINES="$ENGINES gemini"
  echo "ENGINE_GEMINI: opencode $(opencode --version 2>/dev/null | head -1)"
else
  echo "ENGINE_GEMINI: not found"
fi

# Codex — via npx @openai/codex (Windows) or opencode with codex model (Linux)
if [ "$PLATFORM" = "windows" ]; then
  if npx @openai/codex --version >/dev/null 2>&1; then
    ENGINES="$ENGINES codex"
    echo "ENGINE_CODEX: npx @openai/codex $(npx @openai/codex --version 2>/dev/null)"
  else
    echo "ENGINE_CODEX: not found (install: npm install -g @openai/codex)"
  fi
elif [ "$PLATFORM" = "linux" ]; then
  # On Linux, codex runs through OpenCode with model selection
  if command -v opencode >/dev/null 2>&1; then
    ENGINES="$ENGINES codex"
    echo "ENGINE_CODEX: via opencode (model selection)"
  else
    echo "ENGINE_CODEX: not found (requires opencode)"
  fi
fi

echo "AVAILABLE_ENGINES: $ENGINES"
```

Print the detected engines. If the user requested `--engine X` and it's not available, STOP and tell them what's missing and how to install it.

## Step 1: Detect Mode (if not specified)

If the user didn't specify a mode:

1. Check for a diff against the base branch:
```bash
# Detect base branch
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
git fetch origin "$BASE" --quiet 2>/dev/null
DIFF=$(git diff "origin/$BASE")
DIFF_SIZE=$(echo "$DIFF" | wc -c | tr -d ' ')
echo "DIFF_SIZE: $DIFF_SIZE bytes"
echo "---DIFF START---"
echo "$DIFF"
echo "---DIFF END---"
```

If the diff is empty, check for uncommitted changes: `git diff HEAD`

Save the diff content — it will be passed to the engine.

## Step 3A: Review Mode

### Engine: Sonnet (default)

Write the diff to a temp file and call claude --print with an adversarial reviewer persona:

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

### Engine: Gemini

```bash
DIFF_FILE=$(mktemp /tmp/second-opinion-diff-XXXXXX.txt)
git diff "origin/$BASE" > "$DIFF_FILE"
PROMPT="Review this code diff. For each issue found, classify as [P1 CRITICAL], [P2 IMPORTANT], or [P3 INFORMATIONAL] with file:line reference. Be direct and terse. If no issues: LGTM.

$(cat "$DIFF_FILE")"
opencode run -m google/gemini-2.5-pro "$PROMPT" 2>/dev/null
rm -f "$DIFF_FILE"
```

### Engine: Codex (Windows)

```bash
npx @openai/codex review --base "$BASE" 2>/dev/null
```

### Engine: Codex (Linux — via OpenCode)

```bash
DIFF_FILE=$(mktemp /tmp/second-opinion-diff-XXXXXX.txt)
git diff "origin/$BASE" > "$DIFF_FILE"
PROMPT="Review this code diff as a paranoid staff engineer. Classify findings as [P1 CRITICAL], [P2 IMPORTANT], [P3 INFORMATIONAL]. Be terse.

$(cat "$DIFF_FILE")"
opencode run -m openai/o3 "$PROMPT" 2>/dev/null
rm -f "$DIFF_FILE"
```

### After review output

1. Parse the output for P1/P2/P3 markers
2. Determine gate verdict:
   - Any `[P1]` → **FAIL**
   - Only `[P2]`/`[P3]` or no findings → **PASS**

3. Present:

```
SECOND OPINION (ENGINE_NAME — review):
════════════════════════════════════════════════════════════
<full output verbatim — do not truncate or summarize>
════════════════════════════════════════════════════════════
GATE: PASS/FAIL    Engine: ENGINE_NAME    Findings: N P1, N P2, N P3
```

4. **Cross-model comparison:** If `/review` or `/request-review` was already run in this conversation, compare findings:

```
CROSS-MODEL ANALYSIS:
  Both found:        [findings that overlap between Claude review and second opinion]
  Only ENGINE found: [unique to second opinion]
  Only Claude found: [unique to Claude's review]
  Agreement: X% (N/M total unique findings overlap)
```

## Step 3B: Challenge Mode (Adversarial)

Construct an adversarial prompt and send to the selected engine.

**Default adversarial prompt:**
"Review the changes on this branch. Your job is to find ways this code will FAIL in production. Think like an attacker and a chaos engineer. Find: edge cases, race conditions, security holes, resource leaks, failure modes, silent data corruption. Be adversarial. Be thorough. No compliments — just the problems."

**With focus** (e.g., `/second-opinion challenge security`):
Append: "Focus specifically on: {focus area}"

### Engine dispatch:

- **Sonnet:** pipe prompt + diff to `claude --print --model sonnet` with system prompt "You are a chaos engineer and security researcher. Find every way this code can fail."
- **Gemini:** `opencode run -m google/gemini-2.5-pro "<adversarial prompt + diff>"`
- **Codex (Windows):** `npx @openai/codex exec "<adversarial prompt>" -s read-only`
- **Codex (Linux):** `opencode run -m openai/o3 "<adversarial prompt + diff>"`

Present output:
```
SECOND OPINION (ENGINE_NAME — adversarial challenge):
════════════════════════════════════════════════════════════
<full output verbatim>
════════════════════════════════════════════════════════════
Engine: ENGINE_NAME
```

## Step 3C: Consult Mode (Freeform)

Pass the user's question directly to the selected engine with repo context.

### Engine dispatch:

- **Sonnet:** `echo "<question>" | claude --print --model sonnet --add-dir . --no-session-persistence`
- **Gemini:** `opencode run -m google/gemini-2.5-pro "<question>"`
- **Codex (Windows):** `npx @openai/codex exec "<question>" -s read-only`
- **Codex (Linux):** `opencode run -m openai/o3 "<question>"`

Present output:
```
SECOND OPINION (ENGINE_NAME — consult):
════════════════════════════════════════════════════════════
<full output verbatim>
════════════════════════════════════════════════════════════
Engine: ENGINE_NAME
```

After presenting, note any points where you (Claude) disagree with the second opinion:
"**Claude's take:** I disagree on X because Y." or "**Claude's take:** I agree with all points."

## Important Rules

- **Never modify files.** This command is READ-ONLY. All engines run in read-only/sandbox mode.
- **Present output verbatim.** Do not truncate, summarize, or editorialize the engine's output before showing it. Show it in full inside the SECOND OPINION block.
- **Add synthesis AFTER, not instead of.** Any Claude commentary comes after the full output.
- **5-minute timeout** on all engine calls (`timeout: 300000` on Bash).
- **Clean up temp files** after every engine call.
- **No double-reviewing.** If `/review` was already run, the second opinion is independent — don't re-run Claude's own review.

## Engine Selection Guide

| Engine | Best for | Model | Speed | Cost |
|--------|----------|-------|-------|------|
| **sonnet** | Quick second opinion, balanced | Claude Sonnet | Fast | Low |
| **gemini** | Different perspective, long context | Gemini 2.5 Pro | Medium | Low |
| **codex** | Deep code analysis, tool use | o3/codex | Slow | Higher |

**Default engine selection:** If no `--engine` specified, use **sonnet**. It's fastest and always available.

**Multi-engine mode:** User can run `/second-opinion review` then `/second-opinion review --engine gemini` to get opinions from multiple engines. The cross-model comparison accumulates across the conversation.
