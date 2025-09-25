---
title: Vibe Code Like You Mean It
author: michaeljjabbour
date: 
source: https://michaeljjabbour.substack.com/p/vibe-code-like-you-mean-it
publication: michaeljjabbour
---

# Vibe Code Like You Mean It

*Narrating things into existence - Part 1*

What if coding isn't about syntax anymore—but about finding your rhythm with the machine?


## Introduction: Vibe Coding Isn’t a Joke

There’s a new form of creation emerging - less about typing code, more aboutcollaborating with the rhythm of AI. It's not traditional programming. It's not fully design. It’s something in between: rapid, expressive, vibe-led building.

This is an article for people who don’t think they can code—especially product managers, designers, or thinkers who shape software but feel locked out of "the build."

And more importantly, it's for those asking the question at the heart ofThe Arc: how do we stay human in the age of AI?Because vibe coding isn't just about building faster—it's about preserving our role as creators, not just consumers, in a world where machines can generate almost anything.

We’ll walk through what it means to vibe code, how to start, and how I built one of many experiments,AI VoiceGen—a voice feedback tool created entirely through vibe coding—to show the process in action.

This builds on ideas introduced inTuning Forks in a Tornado, where I explored rhythm as a core design and leadership skill. Now we bring that rhythm into your build process.

Last week in "The Rhythm Engine," I showed you why AI needs to match our rhythm, remember our context, and focus on outcomes over output. Now let me show you how to actually build this way.


## What Is Vibe Coding (and Why Should You Care)?

"Vibe coding" was coined byAndrej Karpathy:


> "I just see stuff, say stuff, run stuff, and copy paste stuff, and it mostly works."

"I just see stuff, say stuff, run stuff, and copy paste stuff, and it mostly works."

It’s chaotic, yes—but it also reflects a real, accessible shift.

Vibe coding means:

You express what you want using natural languageAI co-constructs code, with your feedback as the compassYou spend more time shaping, editing, and orchestrating than writing lines from scratch

- You express what you want using natural language
You express what you want using natural language

- AI co-constructs code, with your feedback as the compass
AI co-constructs code, with your feedback as the compass

- You spend more time shaping, editing, and orchestrating than writing lines from scratch
You spend more time shaping, editing, and orchestrating than writing lines from scratch

InIBM’s definition, it’s framed as "express intent, refine later." It’s acode-first, fix-later loop—best for prototypes, risky ideas, or workflows where learning matters more than elegance.

Some argue this should evolve into "Lego coding"—modular, recipe-based scaffolding that scales better across teams. And I agree. That’s exactly what I’m going to show you how to do.


## The Ancient Origin of Vibe Coding?

The phraseabracadabramight sound like stage magic, but its roots run deeper—into early Kabbalistic texts and writings in Hebrew and Aramaic. Most scholars believe it derives from the phrase:


> “Avra kedabra” – I will create as I speak.”

“Avra kedabra” – I will create as I speak.”

This wasn’t and didn’t need to be magic—it was method. Vibe coding works the same way: intention, expression, response, refinement. Language doesn’t just describe what we want. It starts to build it.

In mystical systems like Kabbalah, language isn’t just descriptive—it’s generative. The act of naming or speaking something aloud brings it closer to reality.Sound becomes structure.

This isn’t mere metaphor. Ultrasound waves are routinely used in medicine to promote bone healing and tissue repair.1At the cellular level, mechanical vibrations drive changes in gene expression and cell differentiation. Sound, quite literally, helps shape biological structures.

And isn’t that what vibe coding is?

You speak the intention. You refine the rhythm. The system responds.

In 2025, with Claude, Codex, Cursor, and CLI interfaces, we’re just rediscovering what those early mystics understood:creation begins with finding your voice.


## CLI-First: The Terminal Still Wins

For serious builds, Command Line Interface(CLI) vibe coding is currently the most reliable path. Here’s why:

Claude Codegives structure, readable scaffolds, and some early forms of memory (at least as storage). Claude Desktop is excellent for front-end orchestration.Codex CLIhelps generate files, directories, and shell workflows. Not perfect, but fast.Gradioor simple javascript/html can be a go-to for spinning up front-end interfaces in minutes. It pairs well with AI-driven UX.GPT-4o, ando4-mini-highare all exceptional at code QA, short scripts, and Minimally Viable Experiment (MVE) debugging, but not as consistent across multi-page workflows unless anchored in CLI.Github Copilot, Cline, Roo, and even now Claude Codeall have strengths in a development environment as they can deeply align with your Visual Studio Code (vscode) Integrated Development Environment (IDE).

- Claude Codegives structure, readable scaffolds, and some early forms of memory (at least as storage). Claude Desktop is excellent for front-end orchestration.
Claude Codegives structure, readable scaffolds, and some early forms of memory (at least as storage). Claude Desktop is excellent for front-end orchestration.

- Codex CLIhelps generate files, directories, and shell workflows. Not perfect, but fast.
Codex CLIhelps generate files, directories, and shell workflows. Not perfect, but fast.

- Gradioor simple javascript/html can be a go-to for spinning up front-end interfaces in minutes. It pairs well with AI-driven UX.
Gradioor simple javascript/html can be a go-to for spinning up front-end interfaces in minutes. It pairs well with AI-driven UX.

- GPT-4o, ando4-mini-highare all exceptional at code QA, short scripts, and Minimally Viable Experiment (MVE) debugging, but not as consistent across multi-page workflows unless anchored in CLI.
GPT-4o, ando4-mini-highare all exceptional at code QA, short scripts, and Minimally Viable Experiment (MVE) debugging, but not as consistent across multi-page workflows unless anchored in CLI.

- Github Copilot, Cline, Roo, and even now Claude Codeall have strengths in a development environment as they can deeply align with your Visual Studio Code (vscode) Integrated Development Environment (IDE).
Github Copilot, Cline, Roo, and even now Claude Codeall have strengths in a development environment as they can deeply align with your Visual Studio Code (vscode) Integrated Development Environment (IDE).


## Walkthrough: How I Vibe Built AI VoiceGen

I’m not a full-time developer. I’m more of a clinician and/or CIO than anything else. But I needed a simple tool that could read my writing aloud in different voices and tones—because voice helps me hear errors and rhythm more clearly when I write.

So, I builtaivoicegen—an TTS generator that connects to OpenAI, ElevenLabs, and Gemini.


### Not from scratch. From vibe.

I built the UI via Claude Desktop-generated HTML/CSS and refined with light editsI prompted Claude to write the scaffolding for the appI used Github Copilot with GPT-4.1 to test and fix logicI iterated quickly, asking other AI’s for feedback on how to improve

- I built the UI via Claude Desktop-generated HTML/CSS and refined with light edits
I built the UI via Claude Desktop-generated HTML/CSS and refined with light edits

- I prompted Claude to write the scaffolding for the app
I prompted Claude to write the scaffolding for the app

- I used Github Copilot with GPT-4.1 to test and fix logic
I used Github Copilot with GPT-4.1 to test and fix logic

- I iterated quickly, asking other AI’s for feedback on how to improve
I iterated quickly, asking other AI’s for feedback on how to improve

The result: a tool that speaks your drafts, tunes your copy, and helps you hear what you wrote - in lots of voices and styles.


## A Vibe Coding Framework

This is the flow I now teach others to use. It keeps the loop tight, the scope clear, and the toolchain light. Note, sometimes I will put a rapid UI/UX stage between IDEA and SPEC.


#### 1. IDEA – Narrate Your Intent

Why:This is where you move fromintuitiontointent, just likeLuca Rossi’s“top-down vibe coding” model emphasizes.

Example Prompt:


#### 2. SPEC – Build the Blueprint

Prompt your AI for “spec-first systems.”

Or use this shortcut prompt:

New framing:You’re not writing code. You’re writing the Lego bricks the code will be built from. We would call that a recipe.


### 3. MVE – Minimally Viable Experiment

An MVE is smaller than an MVP—it’s one moment that proves your idea has legs. A button that speaks. A single input-output path. Something that shows the system heard you.

Pick one path—

Build one user moment (e.g. click to generate voice) - a single user interaction (e.g. button → text → voice output) before wiring logic.

Remember: "More output is just more noise unless it moves the needle." One working interaction beats ten half-built features.


> “Keep it simple. Ask for one step you can test. Reset the chat per feature.”(Peter Yang, Rule #6, #10)

“Keep it simple. Ask for one step you can test. Reset the chat per feature.”

(Peter Yang, Rule #6, #10)


### 4. UI/UX – Prompt from Screenshots or Voice

Ask Claude:

Iterate with screenshots and voice notes. Vibe coding isn’t silent. “Include screenshots of the issue or layout. AI sees better than it infers.” (Rule #7 from Peter Yangdiscussed below, and common across Cursor usage guidelines)


### 5. MVP – Recombine the Working Blocks

Once you have 2–3 MVEs tested, connect them with:

Input → processing → outputGradio or Streamlit as the glueClaude or Codex CLI for wiring + config

- Input → processing → output
Input → processing → output

- Gradio or Streamlit as the glue
Gradio or Streamlit as the glue

- Claude or Codex CLI for wiring + config
Claude or Codex CLI for wiring + config

Then:

Add basic state managementTest for regressions (and revert as needed—Rule #9)Reduce code sprawl where possible, ask the AI to help

- Add basic state management
Add basic state management

- Test for regressions (and revert as needed—Rule #9)
Test for regressions (and revert as needed—Rule #9)

- Reduce code sprawl where possible, ask the AI to help
Reduce code sprawl where possible, ask the AI to help

Alternatively, if your spec is good enough - sometimes AI can skip this step and automagically integrate these backend steps heuristically.


## The “Structured Vibe” Workflow

Based on real-world vibe builders:


### 1. Start with vibe PMing

Use natural language to describe outcomes and milestones. Don't overthink. Let the AI catch your rhythm—remember, "when rhythm is random, no one can dance."


### 2. Let AI ask the questions

Use: “Ask me one question at a time until we reach a shared spec.”


### 3. Use checklists to track your path

todolist.mdtest.mdoutput folder

- todolist.md
todolist.md

- test.md
test.md

- output folder
output folder


### 4. Stay in the 40–55% AI zone, for now

Let AI scaffold, test, and summarize. Keep key decisions human.

In a 10-project analysis bySaranyan Vigraham, the sweet spot for AI contribution was 40–55%. Below that, output slowed. Above it, debugging time spiked. That said, I and my peers have easily vibe coded 80-100% of an app without bugs and problems. Something to note is app/feature size, the larger the app the harder it is for the AI coder to help on large tasks.


### 5. Use Git, revert often, test continuously

Peter Yang's12 Rulesare non-negotiable for sanity.

Start with vibe PMingKeep your tech stack simpleGive AI the right rules & documentationAsk AInotto codeAsk AI for options and pick the simple oneBreak tasks into small stepsInclude images to give AI contextTest ruthlessly after every changeDon’t hesitate to revertUse GitHub for version controlUse your voice to feel the vibesAsk AI to explain the code

- Start with vibe PMing
Start with vibe PMing

- Keep your tech stack simple
Keep your tech stack simple

- Give AI the right rules & documentation
Give AI the right rules & documentation

- Ask AInotto code
Ask AInotto code

- Ask AI for options and pick the simple one
Ask AI for options and pick the simple one

- Break tasks into small steps
Break tasks into small steps

- Include images to give AI context
Include images to give AI context

- Test ruthlessly after every change
Test ruthlessly after every change

- Don’t hesitate to revert
Don’t hesitate to revert

- Use GitHub for version control
Use GitHub for version control

- Use your voice to feel the vibes
Use your voice to feel the vibes

- Ask AI to explain the code
Ask AI to explain the code

This creates the memory trail that prevents you from becoming a parrot—your AI assistant can see what's been tried, what worked, and why.


## Tool Guide: My Current Stack


## The Human Choice

As we embrace vibe coding, we face a crucial question: will we use these tools to create thoughtful, intentional software—or will we let them generate an endless stream of algorithmic content? The same AI that can help us carefully compose digital experiences can also pump out infinite variations without purpose or meaning.

This is why vibe coding as a practice matters. It's not just about speed—it's about maintaining our role as intentional creators who know why we're building, not just how. When we vibe with intention, we're choosing curation over chaos.

AsSam Schillacewisely notes in "We are still professionals," there's a crucial balance here: "we have to not forget that we are professionals and need to do real engineering, when it comes to scaled, complex projects that AI can't fully handle today, while at the same time remembering that letting lots of people make code that we absolutely hate is actually a good thing.” The democratization of creation doesn't eliminate the need for craft—it makes understanding the difference between a quick vibe and a lasting build even more important.


## From Rhythm to Repo

If you’ve followed my previous writing, this article is an extension of the following:

The Last Skill- friction mattersOut of Time- time compression changes cognitionThe Warp and the Woof- we weave cognition + coordinationThe First & Last Principle- agency is a trainable loopTuning Forks in a Tornado- the power of rhythmThe Rhythm Engine- from determinism to dependable dance

- The Last Skill- friction matters
The Last Skill- friction matters

- Out of Time- time compression changes cognition
Out of Time- time compression changes cognition

- The Warp and the Woof- we weave cognition + coordination
The Warp and the Woof- we weave cognition + coordination

- The First & Last Principle- agency is a trainable loop
The First & Last Principle- agency is a trainable loop

- Tuning Forks in a Tornado- the power of rhythm
Tuning Forks in a Tornado- the power of rhythm

- The Rhythm Engine- from determinism to dependable dance
The Rhythm Engine- from determinism to dependable dance

Now, we vibe to build.


## Conclusion: Vibe Like You Mean It

This isn’t about hacking. This is about literacy.

Vibe coding teaches coordination and AI-collaboration over syntax.Specs are how we scaffold.Rhythm is how we scale.Agency is how we stay human.

- Vibe coding teaches coordination and AI-collaboration over syntax.
Vibe coding teaches coordination and AI-collaboration over syntax.

- Specs are how we scaffold.
Specs are how we scaffold.

- Rhythm is how we scale.
Rhythm is how we scale.

- Agency is how we stay human.
Agency is how we stay human.

You don’t need to write code to shape products. You need to prompt, scaffold, and guide. That’s what vibe coding teaches—coordination over syntax.

Strike your fork. Define your groove. Let others tune to it. More next week -


### References

Chen, Y., Yang, H., Wang, Z., Zhu, R., Cheng, L., & Cheng, Q. (2023).Low-intensity pulsed ultrasound promotes mesenchymal stem cell transplantation-based articular cartilage regeneration via inhibiting the TNF signaling pathway.Stem Cell Research & Therapy, 14(93). https://doi.org/10.1186/s13287-023-03296-6

“Low-intensity pulsed ultrasound (LIPUS) has been shown to accelerate bone healing and influence cell fate through mechanical vibrations—a modern echo of how sound, quite literally, shapes structure” (Chen et al., 2023).
