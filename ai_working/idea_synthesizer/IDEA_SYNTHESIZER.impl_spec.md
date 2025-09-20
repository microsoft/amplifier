# Implementation Requirements: Idea Synthesizer

## Design Overview
The synthesizer runs in three steps: load → partition → synthesize.

1) **Load** summaries (`*.summary.md`) from `summaries_dir`, compute a **source_manifest_hash** (order-stable list of `(path, sha256)`).
2) **Partition** if necessary (e.g., >N summaries), orchestrating several AI calls in parallel—each receives a compacted set of summaries with aggressive context budgeting.
3) **Synthesize** candidate ideas in parallel, then **dedupe** by semantic/title similarity to produce a final set.

We will use Claude Code **subagents** (e.g., `idea-synthesizer`) to keep this reasoning separate from other stages and to leverage **parallelization** safely. Subagents carry dedicated prompts, tools, and isolated context windows.

## SDK Usage Mode
- **Primary:** Python SDK (`claude-code-sdk`) with `query()`/`ClaudeCodeOptions` to stream results and continue sessions across calls as needed.
- **Alternative:** Headless CLI (`claude -p ... --output-format json`) for simple batch invocations.

### Session & Memory
- Persist **session IDs** between retries to allow controlled multi-turn synthesis when needed.
- Rely on project `CLAUDE.md` / memory to prime consistent style and philosophy (auto-loaded).

### Permissions/Policies
- Respect `.claude/settings.json` permissions; allow read-only tools for this module (e.g., `Read`, `Grep`, `Glob`). These rules are **read from settings**, not set in code. Tool approvals follow the deny→allow→ask chain.

## Subagents
- **`idea-synthesizer`** (project-level): purpose-statement to "synthesize net-new ideas from multiple concise summaries with explicit provenance."
  - As per SDK: subagents are Markdown files under `.claude/agents` and are auto-detected; there is **no programmatic creation**—the generator step writes those files before runs.
- Optional: leverage an existing "architect" or "zen-architect" agent for structuring outputs if present.

## Prompt I/O Contracts (model-side)
- **Input prompt (per partition):**
  - Brief instruction: "Produce cross-summary net-new ideas; cite which summaries inspired each idea; do not restate single-summary ideas."
  - Payload: compressed summaries (title + 3–5 bullet key points), max token budget; require JSON schema output.
- **Output expectation:**
  - List of candidate ideas with `title`, `summary`, `rationale`, `novelty/impact/effort` (0..1), `provenance` (summary file + hash).
  - Hard JSON; failure triggers one retry with stricter schema reminder.

## Determinism & Dedupe
- Use a stable seed & sorted input order.
- Title-based slug + 32-bit content hash; jaccard/title-similarity dedupe step.

## Resume/Idempotency Rules
- If `ideas/<idea-id>.idea.json` exists with matching `source_manifest_hash`, skip.
- If `_index.jsonl` lacks a known idea but file exists, append missing index entry.

## Observability
- Emit TODO events to SDK's todo tracker (Pending → In Progress → Completed) to mirror user-visible progress when running via Claude Code; SDK provides built-in todo lifecycle.
- Log per-partition latencies and model token usage (track via SDK cost/metrics if available; or wrap in our own log).

## Failure Handling
- On malformed model JSON, one structured retry; then quarantine payload under `ideas/_quarantine/<timestamp>.json`.
- On write failures, keep temp file and emit actionable log.

## Quality Bar (Definition of Done)
- ≥ K net-new ideas (configurable), each with ≥1 provenance link.
- Zero schema violations.
- Re-run with same summaries + seed yields identical `idea-id`s and counts.

## Philosophy Alignment
- This module is a **brick** with a single responsibility and a small set of **studs** (its outputs and their schema). Contract-first enables regeneration without breaking downstream consumers.