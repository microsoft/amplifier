---
summary_path: testing_and_observability.summary.md
source_path: @docs/TESTING_AND_OBSERVABILITY.md
source_hash: 2036bdcbd526a7bf11735e27265511f0c50016c25b7122aeb98125d05497fad0
summary_hash: efcd4bb68444e2059584ccf2bd503135d50a7ec121194da88b2923260e4220cb
created_at: "2025-09-17T13:51:47Z"
title: Testing & Observability (Doctests, Coverage, Metrics)
tags: [testing, observability, doctest, metrics]
---

## Summary

The testing strategy favors fast, deterministic tests that reflect the public contract. Executable examples in docs (doctests) serve both as usage guidance and regression safeguards. Coverage is balanced: critical paths must be exercised; flaky or cost-heavy tests are avoided. Operational metrics (latency, cost, tokens, idea counts) and audit logs (session IDs) help validate completeness and performance.


## Key Points

- Doctests keep contract examples runnable and trustworthy.
- Unit + integration split ensures both speed and realism.
- Metrics (latency/cost/tokens) captured per run and per stage.
- Determinism under fixed seeds is part of the definition of done.


## Risks & Constraints

- Over-mocking hides integration issues.
- Unbounded test data causes nondeterministic failures.