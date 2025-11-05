Filtered Graph Export
=====================

Overview
- The graph builder can export a filtered subgraph for cleaner downstream analysis.
- Filters apply only to export; internal graph remains complete.

Flags
- `--only-predicate-edges`: Include only edges that have a `predicate` (SPO relations). Excludes `mentions` or `co-occurs`.
- `--allowed-predicates="a,b,c"`: Only include edges whose predicate is one of the provided values.
- `--drop-untype-nodes`: Drop nodes with no `type` attribute (e.g., article/source IDs).

Make Targets
- Default export: `make knowledge-graph-export FORMAT=gexf`
- Filtered export: `make knowledge-graph-export FORMAT=graphml CLEAN=1`
- Allowed predicates: `make knowledge-graph-export FORMAT=gexf CLEAN=1 ALLOWED_PREDICATES="enables,requires"`

Outputs
- `.data/knowledge/graph.gexf` or `.data/knowledge/graph.graphml`

