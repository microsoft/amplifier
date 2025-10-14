# How to Create Your Own Tool Like This

**You don't need to be a programmer. You just need to describe what you want.**

This document shows you how the Tips Synthesizer was created with minimal input, so you can create your own tools the same way.

## What the Creator Did

The person who "created" this tool didn't write code. Here's what they actually did:

### Step 1: Described What They Wanted

They started a conversation with Amplifier and described their goal in natural language:

> *I need a tool that I can point to a directory of markdown files that contain tips & tricks I've come up with. These are hidden knowledge items that I have that would benefit everyone else who uses the system.*
>
> *I need the tool to read all of these in at once, then write out individual notes files on specific tips & tricks that it can find from across all.*
>
> *Then I want it to take each of those and compile together a new document that is accessible to users of the system.*
>
> *But here is what else I want. I want a system where this doc is generated, and all of the working files are stored in a temp dir, but then have a separate reviewer that is comparing the generated doc and the original files and ensuring the generated doc is well grounded in the facts of the original files and that the generated doc also covers all of the tips and tricks.*
>
> *It should also ensure it's not overly redundant within the file. Then if it has feedback, send it back to the writer process to fix it up, then back to this reviewer to review if any changes were made.*
>
> *Keep doing this until it passes review, then save the final file to the final output dir/filename.*

That's it. **No code. No architecture diagrams. No technical specifications.**

### Step 2: Described the Thinking Process

Notice what they described:
1. "Read all tips from markdown files"
2. "Extract individual tips and create note files"
3. "Synthesize all tips into a unified document"
4. "Review for completeness and accuracy"
5. "Refine based on feedback until it passes"

This is what we call a **metacognitive recipe** - the "how should this tool think about the problem?" They described the thinking process, not the implementation.

### Step 3: Let Amplifier Build It

Amplifier:
- Used specialized agents (amplifier-cli-architect, modular-builder, bug-hunter)
- Implemented all the code
- Added state management for interruption/resume
- Created file I/O for reading and writing
- Handled error recovery and retries
- Built the CLI interface
- Added defensive patterns for reliability

**The creator didn't need to know:**
- How to implement async/await
- How to manage state across stages
- How to handle file I/O with retry logic
- How to parse LLM responses defensively
- How to structure a multi-stage pipeline
- Which libraries to use

### Step 4: Iterated to Refine

The initial implementation worked, and Amplifier:
- Added defensive JSON parsing automatically
- Implemented cloud-sync-aware file I/O
- Added progress visibility
- Included dry-run mode
- Created comprehensive documentation

Total time from idea to working tool: one conversation session with Amplifier's ultrathink-task mode.

## How You Can Create Your Own Tool

### 1. Find a Need

Ask yourself:
- What scattered information do I need to consolidate?
- What repetitive synthesis task takes too much time?
- What process would benefit from AI-powered organization?

**Examples from this repo:**
- "I need to synthesize scattered tips into cohesive guides"
- "I need to write blog posts but it takes hours"
- "I need to extract and organize knowledge from my documentation"

### 2. Describe the Thinking Process

Not the code, the **thinking**. How should the tool approach the problem?

**Good examples:**
- "First extract all X from these files, then organize them by Y, then synthesize into Z format, then review for quality"
- "Read these documents, find common patterns, create a summary, verify completeness"
- "Take scattered content, categorize it, remove redundancy, ensure flow, polish for clarity"

**Bad examples:**
- "Use this library to parse markdown" (too technical)
- "Create a class that processes files" (too implementation-focused)
- "Make it work somehow" (too vague)

### 3. Start the Conversation

In your Amplifier environment:

```bash
claude
```

Then describe your goal using `/ultrathink-task`:

```
/ultrathink-task I need a tool that [describes your goal and thinking process]
```

For example:
```
/ultrathink-task I need a tool that extracts meeting notes from multiple files, categorizes action items by person, creates a summary report, and ensures nothing is missed through an automated review process.
```

### 4. Provide Feedback as Needed

When you try the tool, you might find areas to improve:
- "Can it also handle subdirectories?"
- "The output format needs to be different"
- "Add a preview mode before processing"

Just describe what you want changed. Amplifier will update the tool.

### 5. Share It Back (Optional)

If your tool works well and others might benefit:
1. Document what it does (like this tool's README)
2. Document how you created it (like this file)
3. Contribute it back to the scenarios/ directory

## Real Examples from Synthesis Needs

Here are some synthesis tool ideas you could create the same way:

### Beginner-Friendly Ideas

**Meeting Notes Consolidator**
- **What it does**: Combines meeting notes from multiple sessions into action-oriented summaries
- **The recipe**: Extract notes → Group by project → Identify action items → Create summaries → Review completeness
- **Why it's good**: Clear input/output, obvious value

**Documentation Deduplicator**
- **What it does**: Finds and consolidates duplicate information across documentation
- **The recipe**: Scan docs → Detect duplicates → Identify canonical versions → Consolidate → Verify accuracy
- **Why it's good**: Solves a real pain point

### Intermediate Ideas

**Research Paper Synthesizer**
- **What it does**: Creates literature reviews from multiple research papers
- **The recipe**: Extract findings → Identify themes → Group by topic → Synthesize → Review citations
- **Why it's good**: Saves hours of manual work

**Code Pattern Extractor**
- **What it does**: Extracts common coding patterns from a codebase into best practices documentation
- **The recipe**: Analyze code → Identify patterns → Extract examples → Document → Review quality
- **Why it's good**: Automates knowledge capture

**API Documentation Unifier**
- **What it does**: Combines scattered API documentation into a comprehensive guide
- **The recipe**: Find API docs → Extract endpoints → Group by resource → Synthesize → Validate completeness
- **Why it's good**: Creates consistency

### Advanced Ideas

**Cross-Repository Knowledge Synthesizer**
- **What it does**: Extracts knowledge from multiple code repositories and creates unified documentation
- **The recipe**: Scan repos → Extract patterns → Find relationships → Synthesize knowledge → Review accuracy
- **Why it's good**: Enterprise-scale knowledge management

**Multi-Source Policy Consolidator**
- **What it does**: Combines policy documents from different sources, resolves conflicts, creates unified policy
- **The recipe**: Extract policies → Detect conflicts → Resolve → Synthesize → Validate consistency
- **Why it's good**: Complex conflict resolution

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
- "Review and refine based on feedback"

### 3. Iteration Is Normal

Your first description won't be perfect. That's fine. Describe what needs to change, and Amplifier will update it. This is **much faster** than trying to specify everything perfectly upfront.

### 4. Working Tools Beat Perfect Specs

The tools in this directory are experimental and ready to use, not production-perfect. They solve problems now. Improvements come later as needs emerge.

## Getting Started

1. **Complete the [Amplifier setup](../../README.md#-step-by-step-setup)**
2. **Think about what you need** - What scattered information needs organization?
3. **Describe your thinking process** - How should the tool approach the problem?
4. **Start the conversation** - Use `/ultrathink-task` to describe your goal
5. **Iterate to refine** - Provide feedback as you use it
6. **Share it back** - Help others by contributing your tool

## Common Questions

**Q: Do I need to be a programmer?**
A: No. You need to understand the problem domain and be able to describe a thinking process. Amplifier handles all the implementation.

**Q: How long does it take?**
A: The tips synthesizer took one conversation session (a few hours including testing and iteration). Your timeline may vary based on complexity.

**Q: What if I don't know how to describe the thinking process?**
A: Start with: "I want a tool that does X. It should first do A, then B, then C." Amplifier will help you refine from there. Think about how you would manually solve the problem, then describe those steps.

**Q: Can I modify the code after Amplifier creates it?**
A: You can, but it's usually easier to describe what you want changed and let Amplifier update it. These tools follow the "describe and regenerate" pattern, not the "edit line by line" pattern.

**Q: What if my tool idea is too complex?**
A: Break it into smaller pieces. Create a simple version first (like "just extract and organize"), then add features one at a time ("now add review", "now add multiple output formats").

**Q: What about technical requirements like state management or error handling?**
A: Amplifier adds these automatically based on patterns. You describe what the tool should do, and Amplifier ensures it's done reliably with proper error handling, progress saving, and resume capability.

**Q: Can I see the actual code?**
A: Yes! Check the tool's source code in this directory. But remember: the value is in describing what you want, not in understanding every implementation detail.

## Next Steps

- **Try the tips synthesizer tool** to see what's possible
- **Brainstorm synthesis needs** - What scattered information do you have?
- **Start a conversation** with Amplifier about your idea
- **Share what you create** so others can learn

---

**Remember**: The person who created this tool didn't write any code. They just described what they wanted and how it should think through the problem. You can do the same.

For more examples and guidance, see the [main scenarios README](../README.md) and the [blog writer example](../blog_writer/).
