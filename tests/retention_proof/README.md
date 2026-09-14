# Request retention integration proof

The candidate preserves current hook instructions and the first/latest human
prompts through context compaction without changing amplifier-core. This fixture
is test infrastructure; never add it to a normal bundle.

## Verified result

Six CLI runs, including resumes, produced **50 exported raw provider requests**
on 2026-09-14. Both candidate runs completed six real tool calls, crossed three
forced pressure boundaries, and answered both the original task and resumed
correction correctly. Each candidate also compacted during resume.

| Provider | Context / loop | Raw requests | Original fact visible | Active policy visible | Initial result |
|---|---|---:|---:|---:|---|
| OpenAI | new / new | 8 | 8/8 | 8/8 | Both facts correct |
| Anthropic | new / new | 8 | 8/8 | 8/8 | Both facts correct |
| OpenAI | old / old | 8 | 1/8 | 8/8 | Original fact unavailable |
| Anthropic | old / old | 4 | 1/4 | 4/4 | Stopped after two tool calls |
| OpenAI | new / old | 8 | 8/8 | 4/8 | Policy UNKNOWN after compaction |
| OpenAI | old / new | 14 | 1/14 | 10/14 | Original fact unavailable; resumed task continued incorrectly |

Counts include the resumed request(s). The mixed combinations loaded and ran on
unchanged core 1.6.1; they do not receive the complete fix. Their model responses
are not a claim of identical behavior across stochastic runs. Module regression
tests also cover the legacy request path and explicit tail mode.

The new-context/old-loop control isolates the unchanged-injection bug: its
canonical transcript retains the policy, but four outgoing requests omit it and
the final answer says UNKNOWN. The joint candidate retains the current policy in
every outgoing request. Old-context controls also show why protecting the first
and last **user role** is insufficient when machines use that role.

See [results.json](results.json) for per-request visibility, source hashes,
compaction counts, responses, and cache observations. [source-identities.json](source-identities.json)
pins the imported module and fixture files. [check.py](check.py) verifies the
exported logs against those identities and asserts candidate delivery and task
completion. Full raw logs remain private investigation artifacts; the public
summary contains synthetic facts and hashes, not transcripts or endpoints.

## What was tested

- CLI source: `772bdb42f135fa310e217d6634dd727039d2d840`.
- Published amplifier-core **1.6.1**, unchanged. No core, provider, or application
  source edits are part of this candidate.
- Provider source pins and fixture pin: [run.py](run.py).
- Models: OpenAI `gpt-5.6-terra`, Anthropic `claude-sonnet-5`.
- Ubuntu 24.04 DTU, two CPUs, 4 GiB RAM; unpublished candidates fetched from Gitea.
- Actual CLI module loading, hook merging, tool dispatch, provider calls, context
  compaction, context-intelligence JSONL logging, and CLI session resume.
- Both complete module suites in that DTU: **132 context tests passed, one
  pre-existing compaction-storm test xfailed; 274 orchestrator tests passed**.
  The same suites pass locally. New cases cover sticky restoration, withdrawal,
  changed instructions, missing canonical content, resume, duplicate selection,
  impossible budgets, stale actual-token measurements, pending tool injections,
  iteration-limit finalization, and optional-capability fallback.

The fixture forces a 12,000-token **estimated input budget** by overriding model
window metadata in the test process. It appends 45 synthetic assistant progress
records at requests 2, 4, and 6, followed by a machine-authored user-role work
checkpoint. These are controlled test inputs, not production workload captures.
No model response is mocked. The fixture does not rewrite provider requests.
A real tool reports work-step completion; the model chooses its subsequent calls.

## Cache evidence and limits

For OpenAI, the entire preceding input-message array is an exact prefix at each
of the three transitions between pressure boundaries. System instructions stay
unchanged. Anthropic preserves the same message content at those transitions
when cache-control markers are excluded; its existing breakpoint placement moves
markers, so its full raw arrays are **not** byte-identical prefixes. Its system
content also stays unchanged.

All 16 candidate responses reported cache reads. These runs used warm caches and
a synthetic workload, so they do not establish a cost, latency, or cache-hit-rate
improvement. Compaction and restoring a previously reduced requirement can
change the prefix. This repair preserves existing cache behavior between those
changes; it cannot make arbitrary compaction append-only.

This is one accepted run per provider, plus controlled mixed-version and baseline
runs. It is not a long-duration reliability estimate. Middle human corrections
after later human prompts, one-shot instructions, and independent lifetimes
inside merged hook results remain unsolved. No semantic summarization or exact
whole-provider-payload budget accounting is added. An irreducible required set
fails with ContextLengthError instead of silently discarding its instructions.

## Reproduce

1. Create an isolated DTU with the resource limits above. Pass OpenAI/Anthropic
   credentials and endpoint variables through the DTU's passthrough mechanism.
   Install the pinned CLI using `uv tool install
   git+https://github.com/microsoft/amplifier-app-cli@772bdb42f135fa310e217d6634dd727039d2d840`.
2. For unpublished work, serve these three repositories and their pinned histories
   from Gitea. For the published pins, `--gitea https://github.com/microsoft`
   selects their GitHub locations instead. The name of that argument describes
   its primary development use; the runner accepts either endpoint.
3. Copy `run.py` into the DTU. Run each arm in a **new output directory**:

   ```bash
   python3 run.py --gitea "$REPO_ENDPOINT" --provider openai --arm candidate --output /root/proof/openai-candidate
   python3 run.py --gitea "$REPO_ENDPOINT" --provider anthropic --arm candidate --output /root/proof/anthropic-candidate
   ```

   Repeat with `--arm baseline`, and for OpenAI also `new-context` and `new-loop`.
   If updating an already installed fixture with changed package metadata,
   reinstall that fixture in the CLI environment. A declared source pin alone
   is insufficient: verify the recorded imported-source hashes.
4. Export each complete output directory before destroying the DTU. From this
   directory run `python check.py <exported-run> ... --output <summary.json>`.
   The checker rejects missing captures, wrong sources, incomplete candidate
   sequences, incorrect recall, and missing pressure. A successful CLI process
   exit by itself is **not** acceptance.
5. Run each module's complete pytest suite inside the same DTU against its pinned
   source, then destroy the owned DTU and Gitea resources.

## Fixture calibration excluded from acceptance

Earlier development runs exposed a missing module package/metadata convention,
a stale fixture entry point, overly aggressive history pressure, ambiguous tool
sequence wording, and an unintended Anthropic assistant-prefill ending. Those
runs were retained as diagnostics and excluded from the six-run table. The final
fixture records its own imported hash, uses a fresh output directory, avoids
trailing assistant whitespace, and ends generated progress with an explicit
machine checkpoint. Candidate source hashes in the accepted runs match the
candidate feature commits. All six accepted runs used those same production
module source files.
