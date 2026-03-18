# Amplifier CLI — Design Spec

**Date:** 2026-03-18
**Status:** Approved for implementation

---

## Problem

Amplifier workflows today are conversational — you stay in an Opus session running `/brainstorm` → `/create-plan` → `/subagent-dev`, manually confirming each step. This produces four concrete gaps:

1. **No unattended execution.** Every node transition requires a human present in the session. Overnight or CI-triggered runs are impossible.
2. **Non-reproducible workflows.** Each run is an improvised conversation. There is no artifact that captures which steps ran in which order with which prompts.
3. **Expensive orchestrator context.** The Opus session accumulates context across all tasks. Each additional node pays for everything that came before it, even when earlier context is irrelevant.
4. **Quality gates depend on memory.** `/verify` and `/evaluate` run only if the user remembers to invoke them. There is no mechanism to enforce gates between steps.

---

## Goal

Build a minimal Python CLI (`amplifier`) that executes Fabro-compatible DOT workflow graphs using Claude Code as the agent runtime. The CLI handles:

- Graph parsing and validation
- Model routing via CSS-like stylesheets
- Per-node failure classification and retry
- Run tracking and friction recording

Claude Code handles the actual agent work: tool use, file editing, MCP servers. Each agent node is an independent Claude Code session — no context accumulates between nodes.

---

## Changes

### Change 1: Project Scaffold

**Repo:** New Gitea repository `claude/amplifier-cli`.

**Location:** Repository root — `pyproject.toml`, entry point, Click CLI skeleton.

**Structure:**

```
amplifier-cli/
├── pyproject.toml
├── amplifier_cli/
│   ├── __init__.py
│   ├── main.py
│   ├── parser.py
│   ├── stylesheet.py
│   ├── engine.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── command.py
│   │   ├── human.py
│   │   └── conditional.py
│   ├── failure.py
│   ├── run_dir.py
│   └── graph_render.py
├── tests/
│   ├── test_parser.py
│   ├── test_stylesheet.py
│   ├── test_engine.py
│   ├── test_failure.py
│   ├── test_run_dir.py
│   ├── test_handlers.py
│   ├── test_cross_platform.py
│   └── fixtures/
│       ├── hello.dot
│       ├── plan-implement.dot
│       ├── branch-loop.dot
│       ├── multi-model.dot
│       ├── parallel.dot
│       ├── human-gate.dot
│       ├── invalid-no-start.dot
│       ├── invalid-no-exit.dot
│       └── invalid-orphan.dot
├── workflows/
│   └── amplifier-implement.dot
└── README.md
```

**Runtime:** Python 3.13, uv-managed. Installable via `uv tool install git+https://gitea.ergonet.pl:3001/claude/amplifier-cli`.

**Dependencies:**

| Package | Purpose |
|---------|---------|
| `click` | CLI framework |
| `pydot` | DOT file parsing |
| `networkx` | Graph walking and validation |

Graphviz system binary is an optional runtime dependency for the `graph` command only; absence degrades gracefully.

### Change 2: DOT Parser (`parser.py`)

**Responsibility:** Parse a DOT file into a validated NetworkX directed graph with extracted node attributes.

**Node shapes and their handler mapping:**

| Shape | Handler | Constraint |
|-------|---------|------------|
| `Mdiamond` | start | Exactly one per graph |
| `Msquare` | exit | Exactly one per graph |
| `box` (default) | agent | Full Claude Code session with tools |
| `tab` | prompt | Single `claude --print`, no tools |
| `parallelogram` | command | Shell script via `bash -c` |
| `hexagon` | human | Pause for user input via `input()` |
| `diamond` | conditional | Route on edge conditions |

**Supported node attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `prompt` | string | Instruction text sent to Claude or displayed to human |
| `script` | string | Shell script content for command nodes |
| `model` | string | Explicit model override (e.g., `claude-opus-4-6`) |
| `class` | string | CSS class name for stylesheet matching |
| `goal_gate` | boolean | If true, engine enforces goal completion before continuing |
| `max_visits` | integer | Maximum times this node may be visited in one run |
| `max_retries` | integer | Maximum retry attempts on transient failure |
| `retry_target` | string | Node ID to jump to on retry (defaults to same node) |
| `reasoning_effort` | string | `low`, `medium`, `high` — passed to Claude |

**Supported graph-level attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `goal` | string | Required. Human-readable run goal, injected into every agent node |
| `model_stylesheet` | string | Path to `.css`-syntax stylesheet file |
| `default_max_retry` | integer | Global retry ceiling if node does not set `max_retries` |
| `stall_timeout` | integer | Seconds before a non-responding node is classified `transient` |
| `max_node_visits` | integer | Global max_visits ceiling applied to all nodes |

**Edge condition syntax:**

Edge `[condition="..."]` attributes are parsed as `key=value` pairs. Supported keys:

| Key | Example values |
|-----|---------------|
| `outcome` | `success`, `fail` |
| `failure_class` | `transient`, `deterministic`, `context_overflow`, `stuck_loop`, `canceled`, `scope_violation` |

**Validation rules (enforced at parse time):**

1. Graph has exactly one `Mdiamond` node (start). Error if zero or more than one.
2. Graph has exactly one `Msquare` node (exit). Error if zero or more than one.
3. Every non-start, non-exit node is reachable from start.
4. Every non-exit node has at least one outgoing edge.
5. Cycles are permitted; max_visits enforces termination.

### Change 3: Model Stylesheet (`stylesheet.py`)

**Responsibility:** Parse CSS-like stylesheet files and resolve the model and reasoning_effort for each node.

**Syntax:**

```css
*           { model: claude-haiku-4-5; }
box         { model: claude-sonnet-4-6; }
.coding     { model: claude-sonnet-4-6; reasoning_effort: high; }
#review     { model: claude-opus-4-6; }
```

**Selector specificity (lower number = lower priority):**

| Selector | Specificity |
|----------|------------|
| `*` (universal) | 0 |
| shape name (e.g., `box`) | 1 |
| `.class` name | 2 |
| `#id` (node ID) | 3 |

Resolution order: stylesheet selectors are applied in ascending specificity order. An explicit `model` attribute on a node overrides all stylesheet rules regardless of specificity.

**Supported properties:** `model`, `reasoning_effort`.

**Behavior when no stylesheet is specified:** All agent nodes use `claude-sonnet-4-6` as the default model.

### Change 4: Engine (`engine.py`)

**Responsibility:** Walk the graph from start to exit, dispatch each node's handler, route on outcomes, enforce guards.

**Per-node execution sequence:**

1. Resolve handler from node shape.
2. Resolve model from stylesheet + node attribute override.
3. Build context preamble: `goal` string + prior node outcomes (node ID, status, summary).
4. Execute handler (agent session, shell command, user prompt, or condition evaluation).
5. Classify result using the 6-class taxonomy (see Change 5).
6. Write one friction record to `tmp/friction.jsonl`.
7. Save node stdout to `{run_dir}/{node_id}.txt`.
8. Route to next node via edge conditions matching the outcome.
9. Enforce `max_visits` — if exceeded, classify `stuck_loop` and terminate.
10. Enforce `goal_gate` — if set, and Claude output does not contain an explicit success marker, route via the `fail` edge.

**Circuit breaker:** Track failure signatures as `(node_id, failure_class, normalized_error_prefix)`. When the same signature appears 3 times in one run, terminate immediately with exit code 2 and report the repeating signature to stdout.

**Context passing:** The preamble injected into each agent node is:

```
Goal: {graph.goal}

Prior node outcomes:
- {node_id}: {status} — {one_sentence_summary}
...

Your task:
{node.prompt}
```

**Routing:** When a node produces `outcome=success`, the engine follows edges with `condition="outcome=success"` or edges with no condition attribute. When outcome is `fail`, it follows `condition="outcome=fail"` edges. When outcome has a specific failure class, edges with `condition="failure_class={class}"` are tried first, then `condition="outcome=fail"`.

**Termination conditions:**

- Engine reaches the `Msquare` exit node → exit code 0.
- Circuit breaker fires → exit code 2.
- Node `max_visits` exceeded → exit code 2.
- Unroutable outcome (no matching edge) → exit code 1 with a clear error message.

### Change 5: Failure Classification (`failure.py`)

**Responsibility:** Classify every node result into one of six classes and apply retry/resume rules.

**Six-class taxonomy:**

| Class | Trigger | Retry? | Route? |
|-------|---------|--------|--------|
| `transient` | Non-zero exit from `claude` due to rate limit, API 500, network timeout | Yes — up to `max_retries` | Via `condition="failure_class=transient"` edge if defined, else same node |
| `deterministic` | Non-zero exit with a specific error message (wrong path, missing file, bad syntax) | No | Via `condition="outcome=fail"` edge |
| `context_overflow` | `claude` outputs turn-limit exceeded message | No | Via `condition="failure_class=context_overflow"` edge if defined |
| `stuck_loop` | Node visited more than `max_visits` times in one run | No | Terminates run |
| `canceled` | User sends SIGINT during node execution | No | Terminates run cleanly |
| `scope_violation` | Command handler attempts to write outside allowed paths (detected via guard-paths.sh exit code) | No | Via `condition="outcome=fail"` edge |

**Detection mechanism:** The agent and command handlers capture stdout, stderr, and exit code. The classifier inspects these in order:

1. SIGINT received → `canceled`.
2. Exit code 0 → `success`.
3. Stdout contains `Turn limit` or `context window` → `context_overflow`.
4. Visit count exceeds `max_visits` → `stuck_loop`.
5. Exit code non-zero with recognizable error pattern → `deterministic`.
6. Exit code non-zero without recognizable pattern → `transient`.

**Retry behavior for `transient`:** The engine re-executes the same node up to `max_retries` times (node attribute) or `default_max_retry` (graph attribute). Each retry appends to the friction log with `resume_count` incremented.

### Change 6: Handlers (`handlers/`)

**agent.py** — Executes a full Claude Code session:

```
claude --no-session-persistence --model {model} --print
```

The node prompt (with context preamble) is written to a temp file and passed via stdin. `reasoning_effort` is passed as `--reasoning-effort {value}` if set. Captures stdout, stderr, and exit code. Returns a `NodeResult(status, output, exit_code)`.

**command.py** — Executes shell scripts:

```
bash -c "{node.script}"
```

On both Windows (Git Bash) and Linux. Captures stdout, stderr, exit code. Failure if exit code != 0.

**human.py** — Pauses for user input:

Prints `node.prompt` to stdout, then calls `input("Continue? [approve/revise/abort]: ")`. Maps responses: `approve` → `success`, `revise` → `fail` with class `deterministic`, `abort` → `canceled`.

**conditional.py** — Evaluates edge conditions without executing anything:

Receives the prior node's `NodeResult`. Evaluates all outgoing edge conditions against `outcome` and `failure_class`. Returns the ID of the target node whose condition matches. Raises `UnroutableError` if no edge matches.

### Change 7: Run Directory + Friction (`run_dir.py`)

**Responsibility:** Create and manage the run directory; write friction records; clean up old runs.

**Run directory path:** `tmp/runs/YYYY-MM-DD-HHMMSS-{workflow-stem}/`

**Directory contents:**

| File | Content |
|------|---------|
| `run.json` | Run metadata (see schema below) |
| `{node_id}.txt` | Raw stdout captured from that node |
| `workflow.dot` | Copy of the workflow file used for this run |

**run.json schema:**

```json
{
  "run_id": "2026-03-18-143012-amplifier-implement",
  "workflow": "workflows/amplifier-implement.dot",
  "goal": "Add user auth to the API",
  "started_at": "2026-03-18T14:30:12Z",
  "finished_at": "2026-03-18T14:47:55Z",
  "status": "success",
  "nodes_executed": ["start", "plan", "implement", "verify", "exit"],
  "failure_summary": null
}
```

**friction.jsonl record (one line per node execution, same file as hook-based recording):**

```json
{
  "ts": "2026-03-18T14:35:01Z",
  "agent": "amplifier-cli:agent-node",
  "node_id": "implement",
  "workflow": "amplifier-implement.dot",
  "model": "claude-sonnet-4-6",
  "status": "failed",
  "failure_class": "transient",
  "friction_kind": "retry",
  "resume_count": 1,
  "loop_detected": false,
  "turns_used": null,
  "description": "claude API rate limit on first attempt; retried successfully"
}
```

The `agent` field uses `amplifier-cli:{node_id}` to distinguish CLI-originated records from hook-based records. The `/retro` command reads both sources from the same file.

**Cleanup:** On every `amplifier run` invocation, after the run directory is created, delete all run directories older than 7 days from `tmp/runs/`.

### Change 8: Graph Rendering (`graph_render.py`)

**Responsibility:** Render a DOT workflow as an SVG file; install the Graphviz system binary.

**`amplifier graph workflow.dot -o out.svg`:** Calls the `dot` system binary with `-Tsvg`. Color-codes nodes by shape:

| Shape | Fill color |
|-------|-----------|
| `Mdiamond` (start) | `#d4f0c4` (green) |
| `Msquare` (exit) | `#f0c4c4` (red) |
| `box` (agent) | `#c4d4f0` (blue) |
| `tab` (prompt) | `#e8e8e8` (grey) |
| `parallelogram` (command) | `#f0e8c4` (yellow) |
| `hexagon` (human) | `#f0d4f0` (purple) |
| `diamond` (conditional) | `#f0f0c4` (light yellow) |

If the `dot` binary is not found, the command prints:
```
Graphviz not found. Run: amplifier graph install
```
and exits with code 1.

**`amplifier graph install`:** Installs the Graphviz system binary using the platform-native package manager:

| Platform | Command |
|----------|---------|
| Windows | `winget install Graphviz.Graphviz` |
| Linux (Debian/Ubuntu) | `apt-get install -y graphviz` |
| macOS | `brew install graphviz` |

Platform detected via `sys.platform`. No hardcoded paths. Prints the install command before running it, so the user can see what is being executed.

### Change 9: CLI Interface (`main.py`)

**Entry point:** `amplifier` (registered in `pyproject.toml` as a console script).

**Commands:**

```bash
# Execute a workflow
amplifier run workflow.dot --goal "Add user auth" [--dry-run] [--model opus]

# Validate without running
amplifier validate workflow.dot

# Render workflow graph
amplifier graph workflow.dot -o workflow.svg

# Install Graphviz
amplifier graph install
```

**`run` flags:**

| Flag | Type | Description |
|------|------|-------------|
| `--goal` | string | Required. Overrides the graph-level `goal` attribute if both are set |
| `--dry-run` | boolean | Parse, validate, and print the execution plan without running any node |
| `--model` | string | Override the default model for all nodes (stylesheet still applies for explicit class/id rules) |

**`validate` output:** Prints validation result to stdout. Exit code 0 on success, 1 on failure with specific error messages.

**`graph` subcommand group:** `amplifier graph [workflow.dot -o out.svg | install]`.

### Change 10: Dogfood Workflow (`workflows/amplifier-implement.dot`)

**Responsibility:** Demonstrate the CLI by encoding the standard Amplifier implement workflow as a DOT file.

**Nodes:** start → plan → implement → verify → conditional (pass?) → [exit | fix_loop] → exit

This workflow is used in Layer 3 E2E test 3.5 (dogfood) to verify end-to-end CLI execution on a real task against the Amplifier codebase.

### Change 11: Unit Tests (`tests/`)

**7 test files, all run with `uv run pytest`:**

- `test_parser.py` — valid graph parsing, attribute extraction, all 3 invalid fixtures (no-start, no-exit, orphan)
- `test_stylesheet.py` — specificity resolution, cascading, explicit node override beats all stylesheet rules
- `test_engine.py` — linear walk success, branch on fail, max_visits enforcement, goal gate enforcement
- `test_failure.py` — all 6 class detections, circuit breaker triggers on 3rd identical signature
- `test_run_dir.py` — directory creation, run.json schema validation, cleanup deletes dirs older than 7 days
- `test_handlers.py` — command exit 0 → success, exit 1 → failure, human input mapping, conditional routing
- `test_cross_platform.py` — pathlib path handling, `bash -c` wrapping on Windows and Linux, Amplifier root detection

### Change 12: Workflow Fixtures (`tests/fixtures/`)

**9 DOT files, used in dry-run mode and unit tests:**

| File | Purpose |
|------|---------|
| `hello.dot` | Minimal: start → one agent node → exit |
| `plan-implement.dot` | Two agent nodes in sequence |
| `branch-loop.dot` | Conditional branching with a retry loop |
| `multi-model.dot` | Nodes using different models via stylesheet |
| `parallel.dot` | Parallel edge fanout (engine must handle) |
| `human-gate.dot` | Hexagon human node between two agents |
| `invalid-no-start.dot` | No Mdiamond node — parser rejects |
| `invalid-no-exit.dot` | No Msquare node — parser rejects |
| `invalid-orphan.dot` | Node unreachable from start — parser rejects |

---

## Files Changed

| File | Repo | Change |
|------|------|--------|
| `pyproject.toml` | `claude/amplifier-cli` | Project config: name=amplifier-cli, python=3.13, deps=[click,pydot,networkx], console_scripts=[amplifier=amplifier_cli.main:cli] |
| `amplifier_cli/__init__.py` | `claude/amplifier-cli` | Package init (empty) |
| `amplifier_cli/main.py` | `claude/amplifier-cli` | Click CLI: `run`, `validate`, `graph` commands with all flags |
| `amplifier_cli/parser.py` | `claude/amplifier-cli` | pydot → NetworkX digraph, attribute extraction, 5-rule validation, raises `GraphValidationError` |
| `amplifier_cli/stylesheet.py` | `claude/amplifier-cli` | CSS-like selector parsing, specificity resolution for model and reasoning_effort |
| `amplifier_cli/engine.py` | `claude/amplifier-cli` | Graph walker, context preamble builder, goal gate enforcement, circuit breaker |
| `amplifier_cli/handlers/__init__.py` | `claude/amplifier-cli` | Handler registry mapping shape → handler function |
| `amplifier_cli/handlers/agent.py` | `claude/amplifier-cli` | `claude --no-session-persistence --model {model} --print` execution, stdin preamble injection |
| `amplifier_cli/handlers/command.py` | `claude/amplifier-cli` | `bash -c "{script}"` execution, stdout/stderr capture |
| `amplifier_cli/handlers/human.py` | `claude/amplifier-cli` | `input()` prompt, approve/revise/abort mapping |
| `amplifier_cli/handlers/conditional.py` | `claude/amplifier-cli` | Edge condition evaluation, UnroutableError on no match |
| `amplifier_cli/failure.py` | `claude/amplifier-cli` | 6-class classifier, retry loop, circuit breaker with signature tracking |
| `amplifier_cli/run_dir.py` | `claude/amplifier-cli` | Run directory creation, run.json writer, friction.jsonl appender, 7-day cleanup |
| `amplifier_cli/graph_render.py` | `claude/amplifier-cli` | SVG rendering via `dot` binary, color map, platform-aware Graphviz install |
| `tests/test_parser.py` | `claude/amplifier-cli` | Unit tests: valid parsing, attribute extraction, all 3 invalid fixtures |
| `tests/test_stylesheet.py` | `claude/amplifier-cli` | Unit tests: specificity, cascading, explicit override |
| `tests/test_engine.py` | `claude/amplifier-cli` | Unit tests: linear walk, branching, max_visits, goal gates |
| `tests/test_failure.py` | `claude/amplifier-cli` | Unit tests: all 6 classes, circuit breaker at 3 signatures |
| `tests/test_run_dir.py` | `claude/amplifier-cli` | Unit tests: directory creation, run.json schema, cleanup |
| `tests/test_handlers.py` | `claude/amplifier-cli` | Unit tests: command exit codes, human input mapping, conditional routing |
| `tests/test_cross_platform.py` | `claude/amplifier-cli` | Unit tests: pathlib handling, bash wrapping, platform detection |
| `tests/fixtures/hello.dot` | `claude/amplifier-cli` | Minimal valid workflow |
| `tests/fixtures/plan-implement.dot` | `claude/amplifier-cli` | Two-node sequence |
| `tests/fixtures/branch-loop.dot` | `claude/amplifier-cli` | Branching with retry loop |
| `tests/fixtures/multi-model.dot` | `claude/amplifier-cli` | Multi-model stylesheet exercise |
| `tests/fixtures/parallel.dot` | `claude/amplifier-cli` | Parallel edge fanout |
| `tests/fixtures/human-gate.dot` | `claude/amplifier-cli` | Human gate between two agents |
| `tests/fixtures/invalid-no-start.dot` | `claude/amplifier-cli` | Parser rejection: missing Mdiamond |
| `tests/fixtures/invalid-no-exit.dot` | `claude/amplifier-cli` | Parser rejection: missing Msquare |
| `tests/fixtures/invalid-orphan.dot` | `claude/amplifier-cli` | Parser rejection: unreachable node |
| `workflows/amplifier-implement.dot` | `claude/amplifier-cli` | Dogfood workflow: plan → implement → verify → fix loop |
| `README.md` | `claude/amplifier-cli` | Installation, CLI usage, DOT syntax reference, stylesheet syntax |

---

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|----------------|
| Project scaffold | `amplifier-core:modular-builder` | `pyproject.toml`, `__init__.py`, Click CLI skeleton with `run`/`validate`/`graph` commands, entry point registration |
| DOT parser | `amplifier-core:modular-builder` | `parser.py`: pydot → NetworkX, all attribute extraction, 5 validation rules, `GraphValidationError` exception class |
| Model stylesheet | `amplifier-core:modular-builder` | `stylesheet.py`: CSS selector parser, specificity table, cascade resolution, explicit attribute override |
| Engine + handlers | `amplifier-core:modular-builder` | `engine.py` + `handlers/*.py`: graph walker, context preamble builder, agent/command/human/conditional dispatch, goal gate enforcement |
| Failure + circuit breaker | `amplifier-core:modular-builder` | `failure.py`: 6-class classifier, retry loop with max_retries, circuit breaker with `(node_id, failure_class, error_prefix)` signature tracking |
| Run directory + friction | `amplifier-core:modular-builder` | `run_dir.py`: run directory creation, `run.json` writer, `friction.jsonl` appender, 7-day cleanup on each `amplifier run` invocation |
| Graph rendering + install | `amplifier-core:modular-builder` | `graph_render.py`: SVG output via `dot` binary, node color map, platform-aware Graphviz install via winget/apt/brew |
| Unit tests | `amplifier-core:test-coverage` | All 7 `tests/test_*.py` files: parser, stylesheet, engine, failure, run_dir, handlers, cross_platform |
| Workflow fixtures | `amplifier-core:test-coverage` | All 9 DOT fixtures in `tests/fixtures/` — 6 valid, 3 invalid |
| E2E verification | `amplifier-core:test-coverage` | Layer 3 tests: hello.dot run, implement+verify, failure recovery, human gate, dogfood, graph render, friction integration |

---

## Impact

**New capabilities:**

- Workflows become artifacts: reproducible, version-controlled, shareable as `.dot` files.
- Unattended execution: run workflows from CI or overnight without a session.
- Cheaper orchestration: each node is a fresh Claude Code session. No context accumulates across nodes.
- Enforced quality gates: `goal_gate` attribute prevents proceeding past a node that did not complete its objective.

**Integration with existing Amplifier infrastructure:**

- Friction records appended to `tmp/friction.jsonl` use the same schema as hook-based records. The `/retro` command reads both sources without modification.
- The 6-class failure taxonomy in `failure.py` mirrors the taxonomy in `AGENTS.md`. Same vocabulary, same routing rules.
- Run directories in `tmp/runs/` are ephemeral. The existing `tmp/` cleanup policy (7 days) applies.

**No changes required to:**

- `AGENTS.md` or `CLAUDE.md` (the failure taxonomy is already there; `failure.py` implements it in code)
- Existing hook scripts (friction.jsonl schema is additive; agent field distinguishes CLI vs. hook sources)
- Any existing Amplifier command (the CLI is a separate tool, not a replacement for interactive commands)

---

## Test Plan

### Layer 1 — Unit Tests (7 files, automated, `uv run pytest`)

**test_parser.py:**

1. Valid graph with all node shapes parses without error.
2. Attribute extraction returns correct values for `prompt`, `model`, `class`, `goal_gate`, `max_visits`, `max_retries`, `retry_target`, `reasoning_effort`.
3. Graph-level `goal` attribute is extracted.
4. `invalid-no-start.dot` raises `GraphValidationError` with message containing "start".
5. `invalid-no-exit.dot` raises `GraphValidationError` with message containing "exit".
6. `invalid-orphan.dot` raises `GraphValidationError` with message containing "unreachable".

**test_stylesheet.py:**

1. Universal selector `*` applies to all nodes.
2. Shape selector overrides universal selector (specificity 1 > 0).
3. Class selector overrides shape selector (specificity 2 > 1).
4. ID selector `#node_id` overrides class selector (specificity 3 > 2).
5. Explicit `model` attribute on a node overrides `#id` stylesheet rule.
6. `reasoning_effort` cascades independently of `model`.

**test_engine.py:**

1. Linear walk from start to exit produces node results in order.
2. Agent failure routes via `condition="outcome=fail"` edge.
3. `max_visits=2` on a node terminates run on third visit with `stuck_loop`.
4. `goal_gate=true` on a node routes to fail edge when Claude output lacks success marker.
5. Context preamble passed to second node contains first node's outcome.

**test_failure.py:**

1. Exit code 0 → `success`.
2. SIGINT received → `canceled`.
3. Stdout containing "Turn limit" → `context_overflow`.
4. Non-zero exit with recognizable error pattern → `deterministic`.
5. Non-zero exit without recognizable pattern → `transient`.
6. Visit count > max_visits → `stuck_loop`.
7. Circuit breaker: same `(node_id, failure_class, error_prefix)` signature three times → run terminates with exit code 2.

**test_run_dir.py:**

1. `create_run_dir("workflow.dot")` creates `tmp/runs/YYYY-MM-DD-HHMMSS-workflow/`.
2. `write_run_json(...)` produces valid JSON matching the schema (all required fields present).
3. Run directory contains `workflow.dot` copy.
4. Cleanup deletes directories older than 7 days; directories 6 days old are retained.

**test_handlers.py:**

1. `command.py`: `bash -c "exit 0"` → `NodeResult(status="success", exit_code=0)`.
2. `command.py`: `bash -c "exit 1"` → `NodeResult(status="failed", exit_code=1)`.
3. `human.py`: input "approve" → `NodeResult(status="success")`.
4. `human.py`: input "revise" → `NodeResult(status="failed", failure_class="deterministic")`.
5. `human.py`: input "abort" → `NodeResult(status="canceled")`.
6. `conditional.py`: prior result `outcome=success` routes to the edge with `condition="outcome=success"`.
7. `conditional.py`: no matching edge raises `UnroutableError`.

**test_cross_platform.py:**

1. All path construction uses `pathlib.Path` (no string concatenation with `/` or `\`).
2. `command.py` wraps scripts with `bash -c` on both `sys.platform == "win32"` and `"linux"`.
3. Amplifier root detection returns a `Path` object, not a string.
4. `tmp/runs/` path resolves correctly relative to Amplifier root on both platforms.

### Layer 2 — Workflow Fixtures (dry-run mode, automated)

For each of the 6 valid fixture files, `amplifier validate {fixture}` exits 0. For each of the 3 invalid fixture files, `amplifier validate {fixture}` exits 1 with an error message matching the validation rule violated.

### Layer 3 — Real Workflow Tests (manual, post-deployment)

**3.1 — Hello World:**

- Run: `amplifier run tests/fixtures/hello.dot --goal "Print hello world"`
- Acceptance: exits 0, `tmp/runs/` contains a run directory with `run.json` (status: success) and one node output file.

**3.2 — Implement + Verify with fix loop:**

- Run: `amplifier run tests/fixtures/plan-implement.dot --goal "Add a hello world function to a temp file"`
- Acceptance: exits 0 after both agent nodes complete. Verify node output file contains Claude's verification output. `friction.jsonl` contains two entries with `agent` starting with `amplifier-cli:`.

**3.3 — Failure recovery:**

- Run: `amplifier run tests/fixtures/branch-loop.dot --goal "Test failure routing"` with the command node scripted to `exit 1` on first visit.
- Acceptance: engine routes via `condition="outcome=fail"` edge, retries, second visit succeeds, exits 0.

**3.4 — Human gate:**

- Run: `amplifier run tests/fixtures/human-gate.dot --goal "Test human gate"`
- Acceptance: engine pauses at hexagon node, displays prompt, accepts "approve" input, continues to exit node, exits 0.

**3.5 — Amplifier dogfood:**

- Run: `amplifier run workflows/amplifier-implement.dot --goal "Add a log_version() function to amplifier_cli/__init__.py"`
- Acceptance: exits 0, all nodes in the workflow execute, `run.json` status is "success", the function exists in `amplifier_cli/__init__.py`.

**3.6 — Graph rendering + validation:**

- Run: `amplifier graph workflows/amplifier-implement.dot -o /tmp/test-render.svg`
- Acceptance: exits 0, `/tmp/test-render.svg` is a valid SVG file (contains `<svg` tag), node colors match the shape color map.
- Run: `amplifier validate tests/fixtures/invalid-orphan.dot`
- Acceptance: exits 1, error message contains "unreachable".

**3.7 — Friction + retro integration:**

- After test 3.2 completes, run `/retro` in the Amplifier session.
- Acceptance: `/retro` output includes the amplifier-cli nodes from `friction.jsonl`. Smoothness rating is computed. No error about unrecognized `agent` field format.
