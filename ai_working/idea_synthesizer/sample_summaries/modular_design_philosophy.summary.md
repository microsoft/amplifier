---
summary_path: modular_design_philosophy.summary.md
source_path: @ai_context/MODULAR_DESIGN_PHILOSOPHY.md
source_hash: 81af5a80f88fbea20a9ae76f87e61b7f99849d0debc5f8d206f7159e9aed12de
summary_hash: aaa567ac789d743560831966ef95be170f8a86ab34b3ba10e06818d77f5d01f3
created_at: "2025-09-17T13:51:47Z"
title: Modular Design Philosophy (Bricks & Studs, Contract-First)
tags: [philosophy, architecture, contracts, regeneration]
---

## Summary

The document defines a module as a small, self-contained brick with a minimal public surface (studs). It prioritizes contract-first design, explicit interfaces, and regeneration over patching. Modules must be replaceable from their contract and spec without tribal knowledge. Artifacts include an external contract for consumers and an internal implementation spec; both precede code. Resume-friendly workflows emphasize idempotent outputs, content hashing, and deterministic behavior under fixed seeds.


## Key Points

- Single responsibility, ≤ ~5 public facets ('studs').
- External contract and internal implementation spec are mandatory.
- Prefer regeneration from specs to ad-hoc patches.
- Traceability: decisions and assumptions documented alongside artifacts.
- Determinism and idempotency are quality bars, not afterthoughts.


## Risks & Constraints

- Over-scoping modules creates hidden coupling and brittle boundaries.
- Skipping contract work leads to incoherent interfaces and costly rework.