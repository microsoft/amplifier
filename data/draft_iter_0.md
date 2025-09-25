# The Paradox of Failure: How Our Worst AI Sessions Taught Us the Most

I've been running an experiment for the past week that completely flipped my assumptions about AI-assisted development. 

Eight different attempts at the same goal. Eight wildly different outcomes. And here's the kicker: the sessions that failed the hardest taught us the most.

Let me back up.

## The Setup

We'd been working on evolving our blueprint and codebase generation approach — something we'd originally prototyped in our Recipe Tool — into a more robust system powered by Amplifier CLI tooling. The full vision felt too ambitious to tackle in one go. You know that feeling when you're staring at a mountain and thinking, "There's no way I'm climbing that in a single push"?

So I broke it down into composable parts.

The first major step: build a "module generator" CLI tool that would encapsulate our metacognitive-recipe-like workflow directly into the tool itself. This tool would take a structured pairing of public-facing contracts and internal specification docs, then generate functioning code from them. Think of it as teaching the AI to be a master craftsman who can read blueprints and build the furniture — except the furniture is software modules.

## The Unconventional Approach

Here's where I did something unusual.

Instead of using Amplifier for everything (which I normally do), I deliberately split the work. I kept my Amplifier worktree sessions focused purely on building the actual CLI tooling. For the higher-level planning and research? I offloaded that to a separate assistant with deep research capabilities.

This wasn't because Amplifier couldn't handle planning — it absolutely could. But I wanted to avoid the rabbit hole of improving Amplifier's research capabilities when my goal was to ship the module generator.

To accelerate context-building, I used Repomix to quickly roll up code from two key repos. Then I hit the assistant with an intentionally open-ended prompt:

*"Please consider this repo as we chat about how I want to make improvements in how we are using Claude Code SDK as part of our Amplifier CLI Tools strategy..."*

That prompt was deliberately vague. I wanted the assistant to synthesize what we had before diving into planning. And it worked — the assistant came back with clarifying questions that forced me to articulate what I actually wanted.

Seven minutes and 68 searches later, it had cranked out a comprehensive doc pulling from 16 different sources.

## The Eight Experiments

Now here's where it gets interesting.

I ran eight different sessions, each with progressively different starting contexts:

The first attempt had minimal context — just the research doc and basic instructions. It failed. Hard. I lost count of how many iterations we went through where I kept saying, "No, that doesn't meet my needs."

The second had a tighter proposal with a sample project definition and actual contract/spec documents to test with.

Another iteration involved having the chat assistant "vibe check" all the code without actually running it, then passing those artifacts to a fresh session with instructions to "try running this and fix whatever is needed."

The last experiment? I explained everything directly in Amplifier while in planning mode, with no external context at all.

## The Plot Twist

The two best performers — the ones that worked with minimal iteration — were the session that had pre-written code to work from (even though it was more pseudo-code than production) and the one where I'd collaborated on the plan first.

But here's the twist that blindsided me:

**The greatest improvements in our metacognitive recipes came from the sessions that failed the hardest.**

I sat there, stunned by the realization.

## Why Failure Was Our Best Teacher

Think about it: when something works on the first try, you don't learn much about the edges. You don't discover the assumptions. You don't find the gaps.

But when you're iterating twelve times on the same problem? When you're repeatedly hitting walls? That's when you're forced to articulate your thinking. To encode your decision-making. To create recipes for handling edge cases.

My guidance to these struggling sessions was always the same: solve problems by introducing more of my thinking and strategies as recipe-like capabilities. So these sessions — the ones that struggled most — got the richest set of problem-solving recipes.

Meanwhile, the "successful" sessions provided different value. They showed us how to get more success from fewer interactions. How to structure context for optimal first-pass results. How to reduce the cognitive load on the AI.

Without both ends of that spectrum, we wouldn't have achieved the capability jump we did in a single week.

## The New Process

This experience led me to develop an entirely new process. 

After each session, I could gather context from all the variants and pull their best ideas forward. Each worktree had done something different — provided a unique approach or solution. So I'd take those improvements back to the main branch for everyone to use.

But here's where it gets meta: I could then bring those improvements *back* into each worktree. The Amplifier instances could determine where they still had valuable contributions to make, while also leveraging the improvements from other branches.

The result? Significant jumps in capability. Reduction in code complexity. Solutions that none of the individual sessions would have reached alone.

## The Lesson

To be clear: this wasn't planned. I didn't set out thinking, "Let me run the worst possible version to learn from it." 

But in hindsight, it makes perfect sense. 

We often optimize for immediate success. For the shortest path. For the cleanest implementation. But there's immense value in the struggle. In the failures. In the twelve-iteration debugging sessions that force you to articulate every assumption and encode every bit of domain knowledge.

The paradox is this: our best tools — the ones with the most sophisticated problem-solving capabilities — came from our worst sessions. The ones that failed hardest forced us to embed the most knowledge, create the most recipes, develop the richest set of patterns.

Now imagine if we did this intentionally. If we deliberately ran experiments across the spectrum from "minimal context" to "everything and the kitchen sink." If we treated failure not as something to avoid but as a rich source of learning to mine.

That's the essence of what I discovered this week: sometimes the path to the best solution runs straight through the worst attempts. 

And maybe that's not a bug. Maybe it's the most important feature.