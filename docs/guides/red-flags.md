# Red Flags — Metacognitive Checklist

On-demand reference for common reasoning traps during development. Retrieved via `/docs search red flags`.

If you catch yourself thinking any of the following, stop and apply the reality check before proceeding.

| If you're thinking... | Reality check |
|-----------------------|---------------|
| "This is simple, I'll just implement it directly" | Run /brainstorm first. Simplicity is confirmed after analysis, not assumed before it. |
| "I already know the codebase well enough" | Dispatch agentic-search anyway. Memory of past sessions is lossy. |
| "I'll write tests after the implementation" | /tdd exists for a reason. Tests first is not optional for non-trivial features. |
| "I'll skip the worktree, it's a small change" | Branch first always. Main is protected; there is no "small enough to skip". |
| "I can review my own code" | Two-stage review catches category errors that self-review misses. |
| "The user seems in a hurry, I'll skip brainstorming" | Rushing causes design mistakes that cost 10x the time saved. |
| "This refactor is obvious, no plan needed" | /create-plan takes 2 minutes. The blast radius of "obvious" refactors is routinely underestimated. |
| "I'll just fix this one file" | Check blast radius with grep first. Changes propagate in ways that are not always visible from one file. |
| "I tested it mentally, it should work" | /verify requires evidence, not claims. Mental testing has a well-documented failure rate. |
| "I'll clean up later" | Run /post-task-cleanup now. "Later" accumulates and becomes never. |
