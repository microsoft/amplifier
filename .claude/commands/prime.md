---
description: "Load project context: install dependencies, run checks and tests, prime the session for development."
---

## Usage

`/prime <ADDITIONAL_GUIDANCE>`

## Process

Perform all actions below.

Instructions assume you are in the repo root directory, change there if needed before running.

READ (or RE-READ if already READ):
@ai_context/IMPLEMENTATION_PHILOSOPHY.md
@ai_context/MODULAR_DESIGN_PHILOSOPHY.md

RUN:
make install
source .venv/bin/activate
make check
make test

### Code Review Graph
Update the codebase knowledge graph for blast radius analysis:
```bash
code-review-graph update  # incremental, <2s for most repos
```
If the graph doesn't exist yet, this will do a full build (~10s for 500 files). The graph is stored in `.code-review-graph/graph.db` (gitignored).

## Additional Guidance

$ARGUMENTS
