# Resume Plan — Idea Synthesizer Module Generator

1. **Start by reading these documents (in order):**
   - @ai_working/module_generator/CONTEXT_STATE_2025-09-23.md  ← freshest status snapshot
   - @ai_working/module_generator/CONTEXT_STATE_2025-09-22.md  ← prior-day details for comparison
   - @ai_working/ccsdk-amplifier-improvement-plan.md           ← strategic CCSDK/generator roadmap
   - @ai_working/ccsdk-toolkit-comprehensive-analysis.md       ← toolkit philosophy and defensive patterns

2. **Rehydrate your working memory:**
   - Skim the refreshed contracts/specs under `ai_working/idea_synthesizer/` (especially the top-level `IDEA_SYNTHESIZER.*`).
   - Inspect the generated brick implementations in `amplifier/idea_synthesizer/` (focus on orchestrator conversions and synthesis heuristics) and the validation script `scripts/run_idea_synth_sample.py`.
   - Review `_tmp/module_generator_run.log` (if present) for an example of streaming Claude output and to understand timing expectations.
   - If you need conversational colour, read `~/amplifier/transcripts/2025-09-23-amplifier-generator-from-code-cdx-partial.txt` (partial chat dump).

3. **Re-confirm the current failure mode manually (until the generator handles it automatically):**
```bash
SAMPLE_FIXTURES_DIR=ai_working/idea_synthesizer/sample_summaries \
SAMPLE_TIMEOUT_S=600 \
  .venv/bin/python scripts/run_idea_synth_sample.py \
  --output-dir tmp/idea_synth_output --format summary --clean
```
You should hit the `ContextPartitioner` import error described in the context file. Once the generator is fixed, this command must succeed.

4. **When regenerating the module:**
```bash
AMPLIFIER_CLAUDE_PLAN_TIMEOUT=240 \
AMPLIFIER_CLAUDE_GENERATE_TIMEOUT=3600 \
  .venv/bin/python -m amplifier.tools.module_generator generate \
  ai_working/idea_synthesizer/IDEA_SYNTHESIZER.contract.md \
  ai_working/idea_synthesizer/IDEA_SYNTHESIZER.impl_spec.md \
  --refresh-plan --force
```
This takes ~1 hour. Ensure progress output is streaming; if the run stays silent for minutes, inspect the CCSDK progress hooks.

Optional: capture the run output.
```bash
mkdir -p _tmp
AMPLIFIER_CLAUDE_PLAN_TIMEOUT=240 AMPLIFIER_CLAUDE_GENERATE_TIMEOUT=3600 \
  .venv/bin/python -m amplifier.tools.module_generator generate ... \
  > _tmp/module_generator_run.log 2>&1
```
If the run stalls or errors, inspect the log and the retry loop in `decomposer/specs.py`.

5. **Environment watch-outs:**
   - CCSDK toolkit writes to `.claude/`; ignore or clean as desired.
   - Streaming requires the new `SessionOptions` fields—if you touch `amplifier/ccsdk_toolkit`, re-run `uv run python -m compileall amplifier/ccsdk_toolkit` to catch syntax errors.
   - Generator creates untracked artefacts (`amplifier/idea_synthesizer/`, `scripts/tests/`, etc.). Decide whether to commit or remove them after regeneration to keep the tree tidy.
   - The orchestrator currently hard-codes `ORCH_QUALITY_THRESHOLD=0.3` for sample fixtures. Adjust once higher-quality ideas are available.

6. **Next logical tasks (after digesting the context files):**
   - Fix generator prompts/templates so bricks export the symbols the orchestrator expects (`ContextPartitioner`, etc.).
   - Ensure the generator writes the package README + validation script and runs the script automatically, retrying on failure with Claude feedback.
   - Decide on CLI packaging (`idea-synth` entry point) or update docs/scripts to use `python -m amplifier.idea_synthesizer.cli`.
   - Merge latest `origin/main` before committing to avoid conflicts.
   - Update `.gitignore` if we choose to leave generated artefacts untracked.

7. **If something new breaks:**
   - Record discoveries in `DISCOVERIES.md` (Date, Issue, Root Cause, Solution, Prevention).
   - Use specialised sub-agents (e.g., `amplifier-cli-architect`) when planning substantial changes.
   - Keep prompts referencing the key philosophy docs explicitly via `@` mentions.
