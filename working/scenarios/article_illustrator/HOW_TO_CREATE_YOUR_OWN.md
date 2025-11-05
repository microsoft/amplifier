# How to Create Your Own Tool Like This

**You don't need to be a programmer. You just need to describe what you want.**

This document shows you how the Article Illustrator was created with minimal input, so you can create your own tools the same way.

## What the Creator Did

The person who "created" this tool didn't write most of the code. Here's what they actually did:

### Step 1: Identified a Problem

They had a real need:
- Writing articles requires good imagery
- Finding or creating appropriate images takes too long
- Generic stock photos don't match specific technical content
- Quality and consistency across multiple images is difficult

### Step 2: Described the Thinking Process

They described HOW a tool should think through the problem:

> *I need a tool that can look at my markdown article and figure out where images would help.*
>
> *It should first analyze the content and understand the structure - find the key concepts, identify where visualizations would add value.*
>
> *Then it needs to create detailed prompts for each illustration - not just "a diagram" but specific descriptions that capture what the section is about.*
>
> *After that, it should use AI image generation APIs to create the actual images. Maybe support multiple APIs so I can pick the best result.*
>
> *Finally, it should insert the images back into the markdown at the right positions, with proper formatting and sizing.*
>
> *Oh, and it needs to be resumable - if it fails halfway through or I interrupt it, I don't want to lose all the work and spend money regenerating everything.*

That's it. **No code. No architecture diagrams. No technical specifications.**

### Step 3: Described the Stages

Notice what they described - a thinking process:

1. **Understand** - "Analyze the article to identify where images help"
2. **Identify** - "Find the specific sections that need visuals"
3. **Create** - "Generate detailed, contextually relevant prompts"
4. **Execute** - "Use the best API to create images"
5. **Integrate** - "Insert at optimal positions"

This is the **metacognitive recipe** - the "how should this tool think?" They described the thinking process, not the implementation.

### Step 4: Let Amplifier Build It

Amplifier:
- Used specialized agents (zen-architect, modular-builder, bug-hunter)
- Implemented the 4-stage pipeline
- Added state management for resumability
- Created file I/O for reading and writing
- Handled API coordination for multiple services
- Built error recovery and retries
- Created the CLI interface
- Set up proper logging and cost tracking

**The creator didn't need to know:**
- How to implement async/await in Python
- How to manage session state and checkpoints
- How to handle multiple API clients
- How to retry failed operations
- How to parse markdown and inject HTML
- Which libraries to use
- How to handle type checking

### Step 5: Iterated to Refine

The tool evolved through actual use:
- "Add support for multiple APIs so I can compare results"
- "The Imagen API model name needs updating"
- "GPT-Image-1 is the new default model"
- "Style variations would be cool for themed articles"

Amplifier refined the tool with each piece of feedback. Total development: a few iterations over one session.

## How You Can Create Your Own Tool

### 1. Find a Real Need

Ask yourself:
- What repetitive task takes too much time?
- What process do I wish was automated?
- What would make my work significantly easier?

**Examples from this repo:**
- "Writing blog posts takes hours" → blog-writer
- "Articles need good images" → article-illustrator
- "Code reviews are inconsistent" → (future) code-reviewer

### 2. Describe the Thinking Process

Not the code, the **thinking**. How should the tool approach the problem?

**Good examples:**
- "First understand the user's style, then draft content matching it, then check accuracy, then check style"
- "Analyze article structure, identify visual opportunities, create prompts, generate images, integrate them"
- "Read the codebase, find security patterns, check against best practices, report issues"

**Bad examples:**
- "Use this API to do X" (too technical - let Amplifier choose)
- "Create a class that inherits from Y" (too implementation-focused)
- "Make it work" (too vague - describe HOW it should work)

### 3. Start the Conversation

In your Amplifier environment:

```bash
claude
```

Then describe your goal using `/ultrathink-task`:

```
/ultrathink-task Create a tool that [describe your goal and thinking process]
```

**Example from Article Illustrator**:
```
/ultrathink-task Create a tool that analyzes markdown articles and generates relevant illustrations.

It should:
1. Understand the content and structure
2. Identify where images would add value
3. Generate contextual image prompts
4. Use AI image APIs to create the images
5. Insert them at optimal positions

Make it resumable so I can interrupt and continue later.
```

### 4. Provide Feedback as Needed

When you try the tool, you'll likely find issues or want improvements:
- "It's choosing odd places for images"
- "Can we support style variations?"
- "Need support for multiple APIs to compare results"

Just describe what's wrong or what you want added. Amplifier will iterate.

### 5. Share It Back (Optional)

If your tool works well and others might benefit:
1. Document what it does (like this tool's README)
2. Document how you created it (like this file)
3. Contribute it to the scenarios/ directory
4. Help others learn from your creation

## Real Examples: Tool Ideas

Here are tool ideas that follow the same pattern:

### Beginner-Friendly

**Documentation Consistency Checker**
- **What it does**: Analyzes docs for inconsistencies and suggests fixes
- **The recipe**: Read docs → Identify inconsistencies → Categorize issues → Suggest fixes
- **Why it's good**: Clear input/output, obvious value

**README Generator**
- **What it does**: Analyzes code and generates comprehensive README
- **The recipe**: Analyze code structure → Extract key features → Write usage examples → Format as README
- **Why it's good**: Solves common pain point, straightforward flow

### Intermediate

**API Documentation Validator**
- **What it does**: Compares API docs to actual implementation, finds mismatches
- **The recipe**: Parse API docs → Analyze actual code → Compare → Report discrepancies
- **Why it's good**: Prevents doc drift, valuable for teams

**Test Case Generator**
- **What it does**: Analyzes code and suggests comprehensive test cases
- **The recipe**: Understand code logic → Identify edge cases → Generate test scenarios → Format as tests
- **Why it's good**: Improves test coverage systematically

### Advanced

**Architectural Debt Detector**
- **What it does**: Finds patterns that violate project's design principles
- **The recipe**: Learn project principles → Scan codebase → Detect violations → Suggest refactorings
- **Why it's good**: Maintains architecture quality over time

**Cross-Repository Pattern Finder**
- **What it does**: Identifies common patterns across multiple repos
- **The recipe**: Analyze multiple repos → Extract patterns → Find commonalities → Suggest reusable libraries
- **Why it's good**: Reduces duplication across organization

## The Key Principles

### 1. Describe, Don't Code

You need to know:
- What problem you're solving
- How a human would think through the problem
- What success looks like

You don't need to know how to implement it.

### 2. Metacognitive Recipes Are Powerful

A clear thinking process is all you need:
- "First do A, then B, check C, repeat until D"
- "Understand X, then create Y based on X"
- "Compare A and B, report differences"

This guides the entire implementation.

### 3. Iteration Is Normal and Fast

Your first description won't be perfect. That's fine!

Describe what's wrong, and Amplifier will fix it. This is **much faster** than trying to specify everything perfectly upfront.

The article illustrator evolved through:
- Initial creation
- API updates as models changed
- Style variation support
- Multiple API support

Each iteration was quick because you're describing changes, not implementing them.

### 4. Working Tools Beat Perfect Specs

The tools in scenarios/ are experimental but genuinely useful. They solve real problems right now. Improvements come as needs emerge, not from trying to anticipate everything upfront.

## The Article Illustrator's Journey

### Initial Request (Session 1)

*"Create a tool that generates illustrations for markdown articles using AI image generation."*

Result: Basic tool with one API, no style support, basic error handling.

### Refinements (Same session)

- "The Imagen model name is outdated" → Updated to Imagen-4
- "Add the new GPT-Image-1 model" → Added as third API option
- "Make GPT-Image-1 the default" → Updated default configuration

### Later Additions (User discovered through use)

- Style variations support for themed articles
- Better cost tracking
- Improved error messages
- Resume capability refinements

All of this happened through conversation, not code editing.

## Getting Started

1. **Complete the [Amplifier setup](../../README.md#-step-by-step-setup)**
2. **Think about your need** - What would make your work easier?
3. **Describe the thinking process** - How should the tool approach it?
4. **Start the conversation** - Use `/ultrathink-task` to describe your goal
5. **Iterate to refine** - Provide feedback as you use it
6. **Share it back** - Help others by contributing your tool

## Common Questions

**Q: Do I need to be a programmer?**
A: No. You need to understand the problem domain and describe a thinking process. Amplifier handles implementation.

**Q: How long does it take?**
A: The article illustrator migration took one session. Creating from scratch might be 2-3 sessions depending on complexity.

**Q: What if I don't know how to describe the thinking process?**
A: Start simple: "I want a tool that does X. It should first do A, then B, then C." Amplifier helps you refine from there.

**Q: Can I modify the code after Amplifier creates it?**
A: You can, but it's usually easier to describe what you want changed. These tools follow "describe and regenerate" rather than "edit line by line."

**Q: What if my tool idea is too complex?**
A: Break it into phases. Create a simple version first, then add features one at a time.

**Q: How do I know if my idea is good for a scenario tool?**
A: If it:
- Solves a real problem you have
- Can be described as a thinking process
- Would benefit others facing similar challenges

Then it's probably a good candidate!

## Next Steps

- **Try the article illustrator** to see what's possible
- **Brainstorm your own tool ideas** - what would help your work?
- **Start a conversation** with Amplifier using `/ultrathink-task`
- **Share what you create** so others can learn

---

**Remember**: The person who created this tool described what they wanted and how it should think. They didn't write the implementation. You can do the same.

For more examples and guidance, see the [main scenarios README](../README.md) and study the [blog_writer](../blog_writer/) as another exemplar.
