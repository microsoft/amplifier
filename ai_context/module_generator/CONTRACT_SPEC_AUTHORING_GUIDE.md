# Contracts & Specs Authoring Guide (Amplifier Module Generator)

> **Audience:** Maintainers writing module **contracts** and **implementation specs**, and AI workers that consume them via the Amplifier module generator.
> **Companion reading:** `ai_context/MODULAR_DESIGN_PHILOSOPHY.md`.
> **Execution model:** During generation a worker sees **only**:
> 1. Its own module’s **contract**;
> 2. Its own module’s **spec**; and
> 3. The **contracts** of any declared dependencies.
>
> Workers never see other modules’ specs or source code. The design below keeps every module regenerable in isolation.

---

## 1. Roles of the two artifacts

| Artifact  | Purpose | Audience |
|-----------|---------|----------|
| **Contract** | Stable external agreement (public surface, semantics, error model). | All consumers and dependent modules. |
| **Spec** | Implementation playbook: internal architecture, algorithms, logging, error mappings, tests. | Module generator worker for *this* module only. |

Contracts change rarely and require SemVer discipline. Specs can evolve to refine implementation as long as the contract’s guarantees remain intact.

---

## 2. Core principles

1. **Boundary first:** Write and review the contract before touching the spec.
2. **Single source of truth:** Anything external lives **only** in the contract.
3. **Dependency discipline:** Specs reference other modules strictly through their **contracts**.
4. **Machine ready:** Contracts/specs use consistent YAML front matter so tooling can parse metadata.
5. **Testability:** Every contract guarantee maps to spec test coverage.
6. **Parallel safety:** A worker must be able to regenerate a module without touching other modules’ specs or code.

---

## 3. File layout used by the generator

For module `foo_bar`, the generator expects:

```
ai_working/foo_bar/FOO_BAR.contract.md
ai_working/foo_bar/FOO_BAR.impl_spec.md
```

Names should be deterministic (`<MODULE_ID>.contract.md`, `<MODULE_ID>.impl_spec.md`).

Generated source goes under `amplifier/foo_bar/…` according to the plan produced by the planner.

---

## 4. Contract contents (public, stable)

**Front matter (YAML, required at top):**

```yaml
---
module: foo_bar                # stable identifier (snake_case)
artifact: contract
version: 1.0.0                 # SemVer
status: stable | beta | experimental
depends_on:
  - module: summary_loader
    contract: ai_working/summary_loader/SUMMARY_LOADER.contract.md
  - module: context_partitioner
    contract: ai_working/context_partitioner/CONTEXT_PARTITIONER.contract.md
---
```

**Sections (in order):**

1. **Role & Purpose** – 2–3 sentences with no implementation detail.
2. **Public API** – each operation with signature, parameters, return shape, side effects, preconditions, postconditions, invariants.
3. **Data Models** – full schema for inputs/outputs (JSON Schema or precise typed fields).
4. **Error Model** – canonical error codes/names, when they occur, retryability guidance.
5. **Performance & Resource Expectations** – latency, throughput, limits that consumers must know.
6. **Configuration (Consumer-Visible)** – env vars/config keys affecting public behavior (required/optional, format, default).
7. **Conformance Criteria** – testable statements tying the contract to verification.
8. **Compatibility & Versioning** – SemVer rules, deprecation policy.
9. **Usage Examples** *(non-normative)* – brief snippet showing correct use.

**Do NOT include**: private helpers, logging strategies, internal error mappings, filesystem layout, or other implementation guidance.

---

## 5. Spec contents (internal, regenerable)

**Front matter:**

```yaml
---
module: foo_bar
artifact: spec
contract_ref:
  module: foo_bar
  version: "1.0.0"
targets:
  - python>=3.11
level: moderate   # minimal | moderate | high
---
```

**Sections:**

1. **Implementation Overview** – chosen approach and key constraints.
2. **Core Requirements Traceability** – map contract promises → planned classes/functions/tests.
3. **Internal Design & Data Flow** – components, state, concurrency model, caching.
4. **Dependency Usage** – for each dependency declared in the contract, list the operations (per dependency contract) you call, expected inputs/outputs, error translations.
5. **Logging** – levels, required messages, redaction rules.
6. **Error Handling** – internal exceptions, mapping to contract error codes, retry boundaries.
7. **Configuration (Internal)** – env vars / knobs **not** surfaced in the contract, with validation rules.
8. **Output Files** – explicit relative paths the generator must produce.
9. **Test Plan** – unit/integration tests, fixtures, performance smoke tests; map them to conformance criteria.
10. **Risks & Open Questions** – ambiguities or TODOs for maintainers.

Keep specs precise enough that a worker can implement deterministically, but avoid restating the entire contract.

---

## 6. Level-of-detail rubric for specs

- **Minimal** – trivial helper where implementation choices are obvious.
- **Moderate** – typical default; describe main flows, edge cases, logging/error handling.
- **High** – brittle integrations, external SDK rituals, complex algorithms.

Match the `level` field in front matter to the chosen depth.

---

## 7. Dependency handling

- Contracts must list dependencies in `depends_on` with both the module id **and** exact contract path.
- Specs reference dependency behavior strictly via those contracts.
- Workers receive the dependency contract text alongside the spec and must not peek at dependency code.

---

## 8. Testability expectations

- Every conformance criterion in the contract should map to a concrete test in the spec’s plan.
- Specs must name the files where tests live.
- Generated modules must add tests; failing to do so is a generation bug.

---

## 9. Checklist summaries

### Contract checklist
- [ ] Front matter present with `module`, `artifact`, `version`, `depends_on`.
- [ ] Role & Purpose succinct and external facing.
- [ ] Public API defined with signatures and semantics.
- [ ] Data models precise and machine-readable.
- [ ] Error model complete with retry guidance.
- [ ] Consumer-visible config documented.
- [ ] Conformance criteria are testable statements.
- [ ] Usage example matches the API.
- [ ] No implementation details leak in.

### Spec checklist
- [ ] Front matter references the contract version.
- [ ] Traceability covers all contract requirements.
- [ ] Internal design & data flow articulated.
- [ ] Dependency usage mapped to dependency contracts.
- [ ] Logging/error handling specified.
- [ ] Output files enumerated.
- [ ] Test plan covers success, edge, failure, performance smoke.
- [ ] Risks/open questions noted.
- [ ] No consumer-facing behavior invented.

---

## 10. AI worker protocol (prompt expectations)

1. Read the module’s contract and spec.
2. Read contracts for all declared dependencies.
3. Plan implementation: map files, classes, tests.
4. Generate code strictly in the directories listed under *Output Files*.
5. Honour logging and error mapping guidance.
6. Produce tests satisfying the contract’s conformance criteria.
7. Exit without creating unexpected files.

---

## 11. Notes for authors

- Store canonical docs in Git; avoid duplicating information between contract and spec.
- When breaking changes are required, bump the contract version and regenerate dependents after updating their specs.
- Keep contracts concise; specs carry the detailed implementation burden.
- Update this guide as conventions evolve.

By following this guide plus `ai_context/MODULAR_DESIGN_PHILOSOPHY.md`, the module generator can reliably build Amplifier modules in parallel while keeping boundaries explicit and regeneration frictionless.
