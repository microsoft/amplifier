# Idea Fusion CLI Plan

## Goal
Implement a resumable CLI (`idea-fusion`) that ingests markdown content and produces three artifact layers:
1. Source summaries written to `tmp/summaries/`.
2. Cross-document ideas with provenance in `out/ideas/`.
3. Expanded idea cases in `out/cases/`.

## Stages
1. **Ingest**: Select the first *X* `.md` files (default 5) in deterministic order. Emit a manifest containing file hashes to drive resume logic.
2. **Summarize**: For each manifest entry, generate a structured summary via Claude Code SDK. Skip work when `tmp/summaries/{digest}.json` already exists.
3. **Synthesize**: Feed all summaries to the Idea Synthesizer module, writing `out/ideas/index.jsonl` plus per-idea markdown briefs. Ensure each idea cites ≥2 source digests.
4. **Expand**: For every idea, reload referenced source files and produce a detailed case/plan to `out/cases/{idea_id}.md`.

## Operational Policies
- **Resume Support**: Content digests and per-stage artifacts determine whether to skip processing.
- **Observability**: Emit structured logs (JSONL) with timings, token usage, and Claude session IDs.
- **LLM Integration**: Use Claude Code SDK headless sessions with 120 s timeout, streaming responses, and project subagents defined in `.claude/agents/`.
- **Quality Gates**: Enforce schema validation for all persisted artifacts and deterministic IDs derived from inputs.

This plan anchors the example module specs consumed by the generator CLI.
