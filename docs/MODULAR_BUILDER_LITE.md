# Modular Builder (Lite): Ask → Bootstrap → Plan → Generate → Review

One command to do the whole thing from a **natural-language ask**, using Amplifier’s agents/tools/hooks and the **Contracts & Specs Authoring Guide**.

**What it enforces**

- Isolation: worker reads only this module’s **contract/spec** + dependency **contracts**.
- **Output Files** are the single source of truth for what’s written.
- Every contract **Conformance Criterion** maps to tests.

## Run it

```
/modular-build Build a module that reads markdown summaries, synthesizes net-new ideas with provenance, and expands them into plans. mode: auto level: moderate
```

- Optional inline hints: `mode: auto|assist|dry-run`, `version: x.y.z`, `level: minimal|moderate|high`, `depends: modA:pathA,modB:pathB`

**Flow (who does what)**

1. **Module Intent** — sub‑agent **module-intent-architect** turns your ask into module metadata and persists `session.json` so you can continue later.
2. **Bootstrap** — **contract-spec-author** writes Contract + Spec (if missing) and normalizes to JSON.
3. **Plan** — **zen-architect** produces a STRICT JSON plan whose file tree matches the spec’s **Output Files**; validators enforce safety; optional self‑revise once.
4. **Generate** — **modular-builder** writes only the planned files; **test-coverage** adds tests per conformance mapping; validators enforce no drift; optional self‑revise once.
5. **Review** — **test-coverage** + **security-guardian** confirm conformance and readiness.
