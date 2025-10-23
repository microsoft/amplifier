# /modular-build

**Purpose:** One command to go from a natural‑language **ask** → **Contract & Spec** → **Plan** → **Generate** → **Review**.
It does not call other commands; it drives sub‑agents and micro‑tools directly. It force‑loads the authoring guide.

**Context include (MANDATORY):**
@ai_context/module_generator/CONTRACT_SPEC_AUTHORING_GUIDE.md

**Usage (NL ask via ARGUMENTS):**

```
/modular-build Build a module that reads markdown summaries, synthesizes net-new ideas with provenance, and expands them into plans. mode: auto level: moderate
```

- Optional inline hints: `mode: auto|assist|dry-run`, `version: x.y.z`, `level: minimal|moderate|high`, `depends: modA:pathA,modB:pathB`

**Modes**

- **auto** (default): run autonomously if confidence ≥ 0.75; otherwise switch to **assist**.
- **assist**: ask ≤ 5 crisp questions, then proceed.
- **dry-run**: produce/validate artifacts up to the next gate without writing code (planning only).

---

## ARGUMENTS

(if missing or not clear from the conversation context, or not continuing a prior session, ask the user for whatever is needed to be clear you know how to assist them best)

<ARGUMENTS>
$ARGUMENTS
</ARGUMENTS>

## ULTRATHINK SETUP (IMPORTANT)

Use deep reasoning. When uncertain, propose 2–3 options with tradeoffs, then pick one. Keep steps bounded and observable.
Apply the isolation model from the guide: worker reads only this module’s contract/spec + dependency **contracts**. Output Files are SSOT.
Use strict JSON when asked (no markdown fences).

## Phase A — Intent (derive/continue module metadata from the ask)

1. As **module-intent-architect**, derive/update metadata from `ARGUMENTS` + chat context and persist/merge `ai_working/<name>/session.json`:
   - `module_name`, `MODULE_ID`, `version` (default `0.1.0`), `level` (default `moderate`), `depends[]` (dependency **contracts**).
   - Compute a confidence score; if < 0.75 or mode=assist, ask ≤ 5 targeted questions; then proceed.
   - If a prior session exists, append the ask to `ask_history` and continue the flow from the appropriate phase.

## Phase B — Bootstrap (create Contract & Spec if missing)

1. If `ai_working/<name>/<MODULE_ID>.contract.md` or `...impl_spec.md` is missing:
   - As **contract-spec-author**, write both files per the Authoring Guide and the captured intent.
   - Contract front‑matter: `module`, `artifact: contract`, `version`, `depends_on` (declared dependency **contracts** only).
   - Spec front‑matter: `artifact: spec`, `contract_ref`, `targets`, `level`.
   - Spec **Output Files** must list every file the generator will write (SSOT).
2. Normalize for tooling:
   ```
   Bash(.claude/tools/spec_to_json.py          --contract "ai_working/<name>/<MODULE_ID>.contract.md"          --spec     "ai_working/<name>/<MODULE_ID>.impl_spec.md"          --out      "ai_working/<name>/spec_norm.json")
   ```
3. `TodoWrite("Bootstrapped <name> artifacts", status=completed, metadata={spec_norm:"ai_working/<name>/spec_norm.json"})`

## Phase C — Plan (STRICT JSON; no code writes)

1. As **zen-architect**, synthesize `plan.json` using only the module’s contract/spec and dependency **contracts**.
   - `file_tree` must **exactly** equal the spec’s **Output Files**.
   - Include `conformance_mapping`: each contract **Conformance Criterion** → ≥1 test path.
   - Save:
     - `Write(ai_working/<name>/plan.json, <strict JSON>)`
     - `Write(ai_working/<name>/plan.md, <human summary>)`
2. Validate & (optional) self‑revise (≤ 2 attempts):
   ```
   Bash(.claude/tools/plan_guard.py --plan "ai_working/<name>/plan.json" --spec-norm "ai_working/<name>/spec_norm.json" --root "." --name "<name>")
   Bash(.claude/tools/philosophy_check.py --spec-norm "ai_working/<name>/spec_norm.json" --plan "ai_working/<name>/plan.json" --root ".")
   ```
   If still failing, summarize blockers and stop.
3. In **dry-run** mode, stop here after validation.

## Phase D — Generate (write only planned files)

1. Confirm `plan.file_tree == spec_norm.spec.output_files`; if not, stop and request fix.
2. As **modular-builder**, create exactly the files in `file_tree` under `amplifier/<name>/…` (and tests per repo policy).
   - Use **test-coverage** to realize `conformance_mapping` with fast, deterministic tests.
3. Run repo checks (existing scripts/targets).
4. Validate & (optional) self‑revise (≤ 2 attempts):
   ```
   Bash(.claude/tools/drift_check.py --name "<name>" --plan "ai_working/<name>/plan.json" --root ".")
   Bash(.claude/tools/plan_guard.py --plan "ai_working/<name>/plan.json" --spec-norm "ai_working/<name>/spec_norm.json" --root "." --name "<name>")
   ```
   If still failing, summarize diagnostics in `ai_working/<name>/review.md` and stop.
5. Write `ai_working/<name>/build_summary.md` and mark TODO complete.

## Phase E — Review / Harden

1. Run tests:
   ```
   Bash(pytest -q)
   ```
2. As **test-coverage**, ensure each conformance criterion has ≥ 1 **passing** test; add minimal tests if needed.
3. As **security-guardian**, do a quick security/readiness pass (IO, subprocess, error mapping vs contract).
4. Write `ai_working/<name>/review.md` with conformance table and notes. Complete TODOs.
