# How to Create Your Own Tool Like This

**You don't need to be a programmer. You just need to describe what you want.**

This document shows you how the Blog Writer tool was created with minimal input, so you can create your own tools the same way.

## What the Creator Did

The person who "created" this tool didn't write a single line of code. Here's what they actually did:

### Step 1: Described What They Wanted

They started a conversation with Amplifier and described their goal in natural language:

> *Create me a tool that will take some brain dump I've done on a topic and write up a blog post in my style.*
>
> *I should be able to point to a directory of my current writings for it to use to understanding my style, and then also a source document that contains my new idea or brain dump.*
>
> *From there, it should have a writer that can read all of that in and draft up a first pass, trying to mimic my style, voice, etc.*
>
> *Afterwards, it should pass the resulting draft and the input brain dump to a source-reviewer to verify that it has captured my input content well, if it has not, give feedback and return it to the writer for improvement and back to the source-reviewer.*
>
> *After this, it should do pass the draft and my other writings and pass those to a style-reviewer to verify that it has captured my style, voice, and prior patterns from my other writing well - same deal, if not return to writer.*
>
> *Once it all passes, write the final version out for me to review. Give me the opportunity to mark up the doc with [bracket-enclosed-comments] and then pass it back to the tool to take in my feedback as the final reviewer - start back with the writer and then review again with the others, including passing my feedback along with the other context they previously had.*

That's it. **No code. No architecture diagrams. No technical specifications.**

### Step 2: Described the Thinking Process

Notice what they described:
1. "Understand my style from my writings"
2. "Draft content matching that style"
3. "Review for accuracy against my source"
4. "Review for style consistency"
5. "Get my feedback and refine"

This is what we call a **metacognitive recipe** - the "how should this tool think about the problem?" They described the thinking process, not the implementation.

### Step 3: Let Amplifier Build It

Amplifier:
- Used specialized agents (zen-architect, modular-builder, bug-hunter)
- Implemented all the code
- Added state management for interruption/resume
- Created file I/O for reading and writing
- Handled error recovery and retries
- Built the CLI interface

**The creator didn't need to know:**
- How to implement async/await
- How to manage state
- How to handle file I/O
- How to retry failed operations
- How to parse user feedback
- Which libraries to use

### Step 4: Iterated to Refine

The tool didn't work perfectly on the first try. A few rounds of feedback like:
- "User feedback is being flagged as 'not in source'"
- "Draft files are getting overwritten when I add comments"

Amplifier fixed these issues. Total time from idea to working tool: one conversation session.

## How You Can Create Your Own Tool

### 1. Find a Need

Ask yourself:
- What repetitive task takes too much time?
- What process do I wish was automated?
- What would make my work easier?

**Examples from this repo:**
- "I need to write blog posts but it takes hours"
- "I need to extract knowledge from my documentation"
- "I need to review code for security issues"

### 2. Describe the Thinking Process

Not the code, the **thinking**. How should the tool approach the problem?

**Good examples:**
- "First understand X, then do Y based on what you learned, then check if Z is correct"
- "Read these files, find patterns, create a summary, ask me to verify"
- "Take this input, transform it this way, validate it meets these criteria"

**Bad examples:**
- "Use this library to do X" (too technical)
- "Create a function that does Y" (too implementation-focused)
- "Make it work" (too vague)

### 3. Start the Conversation

In your Amplifier environment:

```bash
claude
```

Then describe your goal using `/ultrathink-task`:

```
/ultrathink-task Create me a tool that [describes your goal and thinking process]
```

### 4. Provide Feedback as Needed

When you try the tool, you'll likely find issues:
- "It's missing X feature"
- "This doesn't work when Y happens"
- "Can we add Z?"

Just describe what's wrong in natural language. Amplifier will fix it.

### 5. Share It Back (Optional)

If your tool works well and others might benefit:
1. Document what it does (like this tool's README)
2. Document how you created it (like this file)
3. Contribute it back to the scenarios/ directory

## Real Examples from Your Brainstorming Session

Here are some tool ideas that came from asking Amplifier "What tools could I create?":

### Beginner-Friendly Ideas

**Documentation Quality Amplifier**
- **What it does**: Progressively improves documentation by simulating a confused reader
- **The recipe**: Write docs → Simulate confusion → Identify unclear parts → Rewrite → Repeat
- **Why it's good**: Easy to understand, clear feedback loop

**Conversational AI Tutor**
- **What it does**: Teaches a concept and adapts based on what works
- **The recipe**: Explain → Check comprehension → Analyze effectiveness → Adapt style → Personalize
- **Why it's good**: Relatable concept, obvious improvement metrics

### Intermediate Ideas

**Research Synthesis Quality Escalator**
- **What it does**: Extracts knowledge from documents and improves through self-evaluation
- **The recipe**: Extract concepts → Assess quality → Detect gaps → Re-read for gaps → Refine
- **Why it's good**: Shows multi-stage refinement

**Code Quality Evolution Engine**
- **What it does**: Writes code, tests it, analyzes failures, improves iteratively
- **The recipe**: Generate → Test → Analyze failures → Improve → Track patterns
- **Why it's good**: Demonstrates concrete improvement cycles

**Self-Debugging Error Recovery**
- **What it does**: Encounters errors and learns to fix them autonomously
- **The recipe**: Execute → Analyze error → Generate hypothesis → Test fix → Store solution
- **Why it's good**: Clear problem→solution learning

### Advanced Ideas

**Multi-Perspective Consensus Builder**
- **What it does**: Simulates different viewpoints and finds optimal solutions
- **The recipe**: Generate perspectives → Analyze independently → Detect conflicts → Debate → Synthesize
- **Why it's good**: Complex emergent behavior

**Performance Optimization Evolutionary Algorithm**
- **What it does**: Evolves better performance through competitive iterations
- **The recipe**: Baseline → Spawn variants → Benchmark → Analyze winners → Combine best → Mutate
- **Why it's good**: Competitive selection dynamics

**API Design Stress Tester**
- **What it does**: Designs APIs by simulating real-world usage
- **The recipe**: Design → Simulate clients → Detect pain points → Redesign → Test migration
- **Why it's good**: Sophisticated feedback through simulation

## The Key Principles

### 1. You Describe, Amplifier Builds

You don't need to know how to code. You need to know:
- What problem you're solving
- How a human would think through the problem
- What a good solution looks like

### 2. Metacognitive Recipes Are Powerful

A clear thinking process is all you need:
- "First do A, then B, then check C"
- "Repeat until X criteria is met"
- "Get feedback and incorporate it"

### 3. Iteration Is Normal

Your first description won't be perfect. That's fine. Describe what's wrong, and Amplifier will fix it. This is **much faster** than trying to specify everything perfectly upfront.

### 4. Working Code Beats Perfect Specs

The tools in this directory are experimental and ready to use, not production-perfect. They solve problems now. Improvements come later as needs emerge.

## Getting Started

1. **Complete the [Amplifier setup](../../README.md#-step-by-step-setup)**
2. **Think about what you need** - What would make your work easier?
3. **Describe your thinking process** - How should the tool approach the problem?
4. **Start the conversation** - Use `/ultrathink-task` to describe your goal
5. **Iterate to refine** - Provide feedback as you use it
6. **Share it back** - Help others by contributing your tool

## Common Questions

**Q: Do I need to be a programmer?**
A: No. You need to understand the problem domain and be able to describe a thinking process. Amplifier handles all the implementation.

**Q: How long does it take?**
A: The blog writer took one conversation session (a few hours including iteration). Your mileage may vary based on complexity.

**Q: What if I don't know how to describe the thinking process?**
A: Start with: "I want a tool that does X. It should first do A, then B, then C." Amplifier will help you refine from there.

**Q: Can I modify the code after Amplifier creates it?**
A: You can, but it's usually easier to describe what you want changed and let Amplifier update it. Remember: these tools follow the "describe and regenerate" pattern, not the "edit line by line" pattern.

**Q: What if my tool idea is too complex?**
A: Break it into smaller pieces. Create a simple version first, then add features one at a time.

## Next Steps

- **Try the blog writer tool** to see what's possible
- **Brainstorm ideas** for your own tools
- **Start a conversation** with Amplifier
- **Share what you create** so others can learn

---

**Remember**: The person who created this tool didn't write any code. They just described what they wanted and how it should think. You can do the same.

For more examples and guidance, see the [main scenarios README](../README.md).
