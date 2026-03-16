---
description: "Route visual output requests to the right tool. Interactive config → playground skill. Diagrams, reviews, slides, explanations → visual-explainer skill. Use when the user wants any visual HTML output."
---

# Visual — Unified Visual Output Router

Single entry point for all visual HTML output. Routes to the best tool based on intent.

## Arguments

$ARGUMENTS

## Step 1: Classify Intent

Parse the user's request and classify into one of two tracks:

### Track A: Interactive Playground
The user wants to **configure, explore, or tweak** something visually with controls and live preview.

Trigger words: playground, explorer, interactive, configure, tweak, controls, sliders, presets, try different, compare options, prompt builder, query builder, concept map, review document, annotate, approve/reject

The playground skill has **6 specialized templates** — match the user's intent to the right one:

| Intent | Playground template | Example requests |
|--------|-------------------|------------------|
| Visual design (components, layouts, color, typography) | `design-playground` | "button style explorer", "tweak card shadows", "typography scale playground" |
| Data & query building (SQL, APIs, pipelines, regex) | `data-explorer` | "SQL query builder", "regex tester", "API parameter explorer" |
| Learning & exploration (concept maps, knowledge gaps) | `concept-map` | "concept map for Kubernetes", "explore the auth domain", "map what I don't know" |
| Document review (suggestions with approve/reject) | `document-critique` | "review this RFC interactively", "let me annotate the proposal" |
| Code review (diffs with line-by-line commenting) | `diff-review` | "interactive diff explorer", "let me comment on these changes" |
| Codebase architecture (components, data flow, layers) | `code-map` | "interactive architecture map", "explore component relationships" |

**Examples:**
- "make a playground for CSS border-radius" → design-playground
- "interactive color palette explorer" → design-playground
- "build a prompt configurator for image generation" → design-playground
- "let me tweak the API parameters visually" → data-explorer
- "SQL query builder playground" → data-explorer
- "concept map for microservices" → concept-map
- "let me review this doc interactively" → document-critique
- "interactive diff review with comments" → diff-review (playground)
- "explore the codebase architecture interactively" → code-map

→ Use the `playground` skill. Invoke: `/playground` with the user's topic.

### Track B: Visual Explanation
The user wants to **see, understand, review, or present** something as a styled HTML page.

Trigger words: diagram, architecture, flowchart, explain visually, diff review, plan review, slides, recap, visualize, show me, draw, overview, fact-check, table (4+ rows)

**Examples:**
- "draw a diagram of the auth flow"
- "visual diff review of my changes"
- "create slides about the new feature"
- "show me the project architecture"
- "fact-check this doc against the code"
- "visual plan review for the migration"

→ Use the appropriate visual-explainer command:

| Intent | Skill |
|--------|-------|
| Diagram / architecture / flowchart | `generate-web-diagram` |
| Implementation plan visualization | `generate-visual-plan` |
| Slide deck / presentation | `generate-slides` |
| Diff / code review | `diff-review` |
| Plan vs codebase review | `plan-review` |
| Project context recap | `project-recap` |
| Verify doc against code | `fact-check` |

### Ambiguous Cases

If unclear, default to **Track B** (visual explanation) — it's the more common need. If the user says "interactive" or "playground" explicitly, always use Track A.

**Overlap: diff-review and code-map exist in both tracks.** Disambiguate by intent:
- "show me the diff" / "review my changes" → Track B (static visual page)
- "let me explore the diff" / "interactive diff with comments" → Track A (playground)
- "show the architecture" / "diagram the system" → Track B (static diagram)
- "interactive architecture map" / "explore component relationships" → Track A (playground)

## Step 2: Dispatch

Invoke the selected skill using the Skill tool with the user's original request as arguments.

**Track A:**
```
Skill: playground
Args: [user's topic]
```

**Track B:**
```
Skill: [matched command from table]
Args: [user's topic/arguments]
```

## Step 3: Proactive Visual Output

This skill also triggers proactively (without being invoked) when:

1. You're about to render a table with **4+ rows or 3+ columns** → use skill `generate-web-diagram` to render it as styled HTML instead of ASCII
2. You're explaining a complex system architecture → offer: "Want me to render this as a visual diagram?"
3. You're reviewing a diff or plan → offer the visual review variant

## Notes

- Track A (playground) outputs to current directory as `*.html`
- Track B (visual-explainer) outputs to `~/.agent/diagrams/` with descriptive filenames
- Both auto-open in browser after generation
- Visual-explainer has opinionated design rules (banned colors, required font variety, anti-AI-slop) — trust its aesthetic judgment
