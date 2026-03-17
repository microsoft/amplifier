---
description: "Optimize any Amplifier skill via autonomous experimentation. Runs the skill repeatedly, scores against binary evals, mutates one thing at a time, keeps improvements. Based on Karpathy's autoresearch."
---

# /optimize-skill — Autonomous Skill Optimization

## Arguments

`/optimize-skill <path-to-SKILL.md-or-command.md>`

Example: `/optimize-skill .claude/commands/brainstorm.md`

## Before Starting: Gather Context

**STOP. Confirm all fields with the user before running any experiments.**

1. **Target skill** — path to the skill/command file to optimize
2. **Test inputs** — 3-5 different prompts/scenarios that cover different use cases (variety prevents overfitting)
3. **Eval criteria** — 3-6 binary yes/no checks defining "good output" (see Binary Eval Guide below)
4. **Runs per experiment** — How many times to run per mutation. Default: 3 (balance of reliability vs cost)
5. **Budget cap** — Max experiment cycles. Default: 10. Set higher for important skills.

## Binary Eval Guide

Every eval MUST be binary — pass or fail. No scales. No "rate 1-7". Scales compound variability.

**Format:**
```
EVAL [N]: [Short name]
Question: [Yes/no question about the output]
Pass: [What "yes" looks like — specific]
Fail: [What triggers "no" — specific]
```

**Rules for good evals:**
- Binary only. "Is the text readable?" is too vague. "Are all words spelled correctly with no truncated sentences?" is testable.
- 3-6 evals is the sweet spot. More than 6 and the skill starts parroting eval criteria.
- Each eval must be independently scorable — no overlapping checks.
- The 3-question test for each eval: (1) Would two agents score it the same? (2) Can the skill game it without improving? (3) Does the user actually care about this?

**Examples by skill type:**

For code/technical skills:
- "Does the code run without errors?" (execute it)
- "Does the output contain zero TODO or placeholder comments?"
- "Are all external calls wrapped in error handling?"

For design/visual skills:
- "Is all text legible with no truncated or overlapping words?"
- "Does the color palette avoid neon/high-saturation colors?"
- "Is the layout linear (left-to-right or top-to-bottom)?"

For workflow/process skills:
- "Does the output follow all steps in order?"
- "Does it ask the user for confirmation before destructive actions?"
- "Does it produce all required output artifacts?"

## Process

### Phase 1: Read and Understand

1. Read the target skill file completely
2. Read any referenced files (references/, templates/)
3. Identify the skill's core job, steps, and output format
4. Note existing quality checks and anti-patterns

### Phase 2: Baseline (Experiment #0)

1. Create working directory: `autoresearch-[skill-name]/` in the skill's parent folder. If the skill lives outside the Amplifier workspace, create it at `[AMPLIFIER_ROOT]/autoresearch-[skill-name]/` instead.
2. Copy the original as `[skill-name]-optimized.md` — ALL mutations happen on this copy. NEVER edit the original.
3. Save `SKILL.md.baseline` as revert target
4. Run the skill [N] times using test inputs
5. Score every output against every eval
6. Record baseline score: `max_score = [number of evals] * [runs per experiment]`

**If baseline is 90%+**, confirm with user — the skill may not need optimization.

### Phase 3: Experiment Loop

**For each cycle:**

1. **Analyze failures** — which evals fail most? Read the failing outputs. Identify the pattern.

2. **Form hypothesis** — pick ONE thing to change. Good mutations:
   - Add a specific instruction addressing the most common failure
   - Reword an ambiguous instruction to be more explicit
   - Add an anti-pattern for a recurring mistake
   - Move a buried instruction higher (priority = position)
   - Add a worked example showing correct behavior
   - Remove an instruction causing over-optimization

   Bad mutations (never do these):
   - Rewriting the entire skill
   - Adding 10 rules at once
   - Adding vague instructions ("make it better")

3. **Make the change** — edit `[skill-name]-optimized.md` with ONE targeted mutation.

4. **Run the experiment** — execute [N] times with same test inputs.

5. **Score** — auto-evaluate each output against every eval:
   - Dispatch a reviewer subagent to score outputs:
     ```
     # Haiku override: binary YES/NO scoring is simple enough — cheaper than routing matrix default (sonnet)
     Agent(subagent_type="code-quality-reviewer", model="haiku", description="Score experiment output",
       prompt="Score the following output against these binary evals. For each eval, answer YES or NO with a one-line justification.

       ## Evals
       [paste eval criteria]

       ## Output to score
       [paste the experiment output]

       Return a simple table: EVAL | PASS/FAIL | Reason (one line each). End with total: X/Y passed.")
     ```
   - If all evals pass unanimously across runs → score is clear, no user needed
   - If any eval is ambiguous (reviewer unsure) → flag for user review
   - Record scores in `results.tsv`

6. **Keep or discard:**
   - Score improved → **KEEP**. This is the new baseline.
   - Score same → **INCONCLUSIVE** at low N. If runs-per-experiment ≤3, re-run with more runs before discarding. Ties at N=3 are noise, not evidence.
   - Score worse → **DISCARD**. Revert to previous version.

7. **Log** — append to `changelog.md`:
   ```
   ## Experiment [N] — [keep/discard]
   Score: [X]/[max] ([percent]%)
   Change: [One sentence]
   Reasoning: [Why expected to help]
   Result: [Which evals improved/declined]
   ```

8. **Track experiment count.** When count reaches budget cap, stop immediately and proceed to Phase 4 regardless of score trajectory. **Repeat** until budget exhausted or 95%+ for 3 consecutive experiments.

**Quality escape hatch:** If all evals pass but output quality feels wrong — the evals are incomplete, not the skill. Stop experimenting. Add new evals covering the quality gap, re-baseline, then resume.

### Phase 4: Deliver Results

Present to user:
1. Score summary: baseline -> final (percent improvement)
2. Total experiments run, keep rate
3. Top 3 changes that helped most
4. Remaining failure patterns
5. Path to the improved file (original untouched)
6. Path to changelog.md

## Output Files

```
autoresearch-[skill-name]/
├── [skill-name]-optimized.md    # improved version
├── SKILL.md.baseline            # original (revert target)
├── changelog.md                 # every mutation tried
└── results.tsv                  # score log
```

**The original skill file is NEVER modified.** The user reviews the diff and manually applies changes if satisfied.

## Integration with Amplifier

- Use `/self-eval` rubrics as starting point for eval criteria
- Feed successful mutations into `/self-improve` as evidence
- The changelog is a research log that future sessions can continue from
- Run periodically on high-use skills (brainstorm, create-plan, tdd) for continuous improvement
- Auto-scoring via `code-quality-reviewer` agent reduces manual effort — user only reviews ambiguous results

## When to Use

- A skill works ~70% of the time but fails unpredictably
- After receiving user feedback that a skill "sometimes gets it wrong"
- Periodic maintenance on high-value skills (monthly)
- After major changes to CLAUDE.md or AGENTS.md that may affect skill behavior
