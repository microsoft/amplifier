# The Paradox of Failure: How Our Worst AI Sessions Taught Us the Most

Imagine you're a master watchmaker teaching an apprentice. You've laid out all your tools — the tiny screwdrivers, the magnifying glass, the delicate springs and gears. Everything's organized, labeled, ready to go. Then you give your apprentice the most complex mechanism you have: a perpetual calendar movement with moon phases and minute repeater.

They fail. Spectacularly. Springs shoot across the room. Gears mesh where they shouldn't. The whole thing looks more like abstract art than precision engineering.

Here's the thing: that disaster of an attempt — where they had to disassemble everything and start over seventeen times — that's when they actually learned how timepieces work. That's when they understood not just the what, but the why.

I've been running an experiment for the past week that completely flipped my assumptions about AI-assisted development. Eight different attempts at the same goal. Eight wildly different outcomes.

And the sessions that failed the hardest — the ones that felt like watching that apprentice launch springs into orbit — taught us the most.

Let me back up.

## The Setup

We'd been evolving our approach to blueprint and codebase generation — something we'd originally explored in our experimental [Recipe Tool](https://github.com/microsoft/recipe-tool) project — into something more robust using [Amplifier](https://github.com/microsoft/amplifier), our new experimental tooling framework. The full vision felt like trying to build a cathedral while standing in the foundation pit — you know where you want to go, but you can't see the whole structure from where you're standing.

So I broke it down into composable parts.

The first major milestone: build a module generator tool that would take structured pairings of public contracts and internal specifications, then generate functioning code from them. The idea was to capture patterns and problem-solving strategies directly into the tool itself — building in the kind of adaptive intelligence that could handle the unexpected.

Think of it as teaching the AI to be not just a watchmaker, but a watchmaker who understands why certain gears mesh, why specific tensions matter, why Swiss movements differ from Japanese ones.

## The Unconventional Approach

Here's where I did something unusual.

Instead of using Amplifier for everything (which I normally do), I deliberately split the work. I kept my Amplifier worktree sessions focused purely on building the actual tooling. For the higher-level planning and deep research? I offloaded that to a separate assistant with deep research capabilities.

The practical reason was simple: I needed to ship the module generator, not improve Amplifier's research capabilities. Like a watchmaker who sends an assistant to source materials so they can focus on the actual assembly.

To accelerate context-building, I used [Repomix](https://repomix.com) to quickly roll up code from two key repos. Then I started the assistant with this exact prompt:

*"Please consider this repo as we chat about how I want to make improvements in how we are using Claude Code SDK as part of our Amplifier strategy. I have some ideas for how I want a new CCSDK tool to be able to handle generating code modules, and I want to talk through the approach and have you offer suggestions for improvements."*

I wanted the assistant to synthesize what we had before diving into planning.

And it worked.

The assistant came back with clarifying questions that forced me to articulate what I actually wanted. Seven minutes and 68 searches later, it had cranked out a comprehensive doc pulling from 16 different sources using its deep research capabilities.

## The Eight Experiments

Now here's where it gets interesting.

I ran eight different sessions, each with progressively different starting contexts — like asking eight different watchmakers to build the same movement, but giving each one a different combination of tools, blueprints, and prior knowledge.

The first attempt had minimal context — just the research doc and basic instructions. It failed. Hard. I lost count of how many iterations we went through where I kept saying variations of "This doesn't seem to follow the patterns I'm asking for."

The second had a tighter proposal with a sample project definition and actual contract/spec documents to test with.

Another iteration involved having the chat assistant review all the code without actually running it, then passing those artifacts to a fresh session with instructions to run and fix whatever was needed.

There were also several 'Amplified' Codex CLI sessions that worked okay, but needed more guidance than I'd hoped.

At one point, I even paused the CLI development entirely to build an interactive version — the one users are working with now.

The last experiment? I explained everything directly in Amplifier while in planning mode, with no external context at all.

## The Plot Twist

The two best performers — the ones that worked with minimal iteration — were the session that had pre-written code to work from (even though it was more pseudo-code than production) and the one where I'd collaborated on the plan first.

But here's the thing that blindsided me:

**The greatest improvements in our problem-solving patterns came from the sessions that failed the hardest.**

In the quiet moments after each failed attempt, when the frustration settled like dust after an explosion, that's when I saw it. The failures weren't bugs — they were features. They were forcing functions for encoding knowledge.

## Why Failure Was Our Best Teacher

Think about learning to play chess. When you win your first game, you feel good but you haven't really learned much. You don't know which moves were brilliant and which were lucky. You don't understand the near-misses, the almost-disasters, the thin ice you skated over without realizing.

But when you lose? When you get demolished in twelve moves? That's when you learn. That's when you understand why controlling the center matters. Why developing pieces early isn't optional. Why that innocent-looking pawn push opened a highway for your opponent's queen.

The same principle applied here.

When something works on the first try, you get a result but not understanding. You get output but not insight. You complete the task but don't map the territory.

But when you're iterating twelve times on the same problem? When you're repeatedly hitting walls that shouldn't exist? That's when you're forced to articulate your thinking. To encode your decision-making. To create patterns for handling edge cases.

My guidance to these struggling sessions was always the same: solve problems by introducing more of my thinking and strategies as built-in capabilities. So these sessions — the ones that struggled most — got the richest set of problem-solving patterns. They became like master craftsmen's notebooks, filled with marginalia about every conceivable problem because they'd encountered every conceivable problem.

Meanwhile, the "successful" sessions provided different value. They showed us the optimal starting conditions. How to structure context for first-pass success. How to reduce the cognitive load on the AI — like discovering exactly how to hold a jeweler's loupe so your hand doesn't cramp after hours of detail work.

Without both ends of that spectrum, we wouldn't have achieved the capability jump we did in a single week.

## The New Process

This experience led me to develop an entirely new process — one that feels more like conducting parallel experiments in a laboratory than following a single development path.

After each session, I used Amplifier to gather insights from all the variants and synthesize their best ideas. This wasn't a traditional git merge — it worked at the idea level. Amplifier could analyze the approaches taken, understand the context of each exploration, grasp the rationale behind different changes, and then synthesize a new approach incorporating the best elements from each session.

Most importantly, it made improvements at the problem-solving level itself, enhancing the overall capabilities of the system.

Here's the thing: I could then bring those improvements *back* into each worktree. The Amplifier instances could determine where they still had valuable contributions to make, while also leveraging the improvements from other branches.

The result? 

Significant jumps in capability. Reduction in code complexity. Solutions that none of the individual sessions would have reached alone.

## The Lesson

To be clear: this wasn't planned. I didn't set out thinking, "Let me run the worst possible version to learn from it." I stumbled into this realization like a watchmaker discovering that studying broken movements teaches more about precision than examining perfect ones.

But in hindsight, it makes perfect sense.

We often optimize for immediate success. For the shortest path. For the cleanest implementation. But there's immense value in the struggle — in those twelve-iteration debugging sessions that force you to articulate every assumption and encode every bit of domain knowledge.

The paradox is this: our best tools — the ones with the most sophisticated problem-solving capabilities — came from our worst sessions. The ones that failed hardest forced us to embed the most knowledge, create the most patterns, develop the richest set of strategies.

Now imagine if we did this intentionally.

If we deliberately ran experiments across the spectrum from "minimal context" to "everything and the kitchen sink." If we treated failure not as something to avoid but as a rich vein to mine. Like master watchmakers who deliberately study every possible failure mode — not just to fix them, but to understand the deep mechanics of why they occur.

## What You Can Try

You don't need Amplifier or Recipe Tool to experiment with these ideas. Here's how you can explore this paradox with whatever AI tools you're using:

**Run parallel experiments.** Next time you're solving a problem with AI, don't just iterate on one conversation. Start three or four with different contexts. Give one minimal information. Give another your entire thought process. Watch how they fail differently — and what you learn from each failure mode.

**Build your own problem-solving patterns.** When your AI assistant struggles with something, don't just fix the immediate problem. Write down the pattern: "When X happens, think about Y, then try Z." Start collecting these. You're not just coding solutions — you're encoding problem-solving strategies.

**Create deliberate failure modes.** Pick a task you know how to do well. Now try to make your AI assistant fail at it in interesting ways. Remove key context. Add contradictory requirements. See what breaks. Each breaking point teaches you something about the boundaries and assumptions of your tools.

**Synthesize across attempts.** After multiple sessions, step back. What did each attempt teach you? What patterns emerged? Don't just take the best solution — understand why it was best and what the failures contributed to that understanding.

The goal isn't to accumulate failures. It's to recognize that our tools get smarter not from perfect runs, but from the rich problem-solving capabilities we encode when things go wrong.

That's the essence of what I discovered this week: sometimes the most direct path to the best solution runs straight through deliberate exploration of the worst attempts.

And maybe that's not a bug.

Maybe it's the most important feature.