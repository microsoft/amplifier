# Scenarios: Amplifier-Powered Tools in Action

**Tools you can use today, built with minimal input using Amplifier's patterns.**

This directory showcases Amplifier-powered tools that serve a dual purpose:

1. **Practical utility** - Genuinely useful for everyday tasks
2. **Learning exemplar** - Shows what's possible when you describe what you want

These aren't toys or demos. They're experimental tools you'll actually use, built by sharing a goal and a thinking process with Amplifier.

## Featured Tools

### 📝 [blog-writer](./blog_writer/)

Transform rough ideas into polished blog posts that match your personal writing style.

**The Problem**: You have ideas but writing takes hours. Generic AI writing doesn't sound like you.

**The Solution**: A tool that thinks through blog writing:

- Learns your writing style from existing posts
- Drafts content matching your voice
- Reviews itself for accuracy and style
- Refines based on your feedback

**How it was built**: User described the goal and thinking process in one conversation turn. Amplifier handled all the implementation. Some iteration to refine, but it generally just worked.

**Status**: Ready to use (experimental)

---

### 📚 [tips-synthesizer](./tips_synthesizer/)

Transform scattered tips and tricks into comprehensive, well-organized guides.

**The Problem**: You have valuable tips scattered across multiple files. They're fragmented, have redundancy, lack structure, and miss the connections between related concepts.

**The Solution**: A multi-stage AI pipeline that synthesizes scattered knowledge:

- Extracts tips systematically from all your markdown files
- Categorizes and organizes related tips intelligently
- Creates a cohesive document with logical flow
- Reviews for completeness, accuracy, and clarity
- Refines iteratively based on automated feedback

**How it was built**: User described the goal and multi-stage thinking process - "extract tips, organize into notes, synthesize into a document, review for quality, refine until it passes." Amplifier implemented the complete pipeline with state management, defensive patterns, and review loops.

**Status**: Ready to use (experimental)

---

### 🎨 [article-illustrator](./article_illustrator/)

Automatically generate contextually relevant AI illustrations for your markdown articles.

**The Problem**: Finding or creating appropriate images for articles is time-consuming. Generic stock photos rarely match specific technical content.

**The Solution**: A tool that illustrates articles intelligently:

- Analyzes content to identify where images add value
- Generates contextually relevant image prompts
- Creates images using multiple AI APIs (GPT-Image-1, DALL-E, Imagen)
- Inserts images at optimal positions with proper formatting

**How it was built**: User described the thinking process - "analyze content, identify illustration points, create prompts, generate images, integrate them." Amplifier implemented the 4-stage pipeline with resumability, multi-API support, and style variations.

**Status**: Ready to use (experimental)

---

## What Makes a Good Scenario Tool?

### 1. Solves a Real Problem

Not "what if we..." but "I need to..."

- Blog writing takes too long → blog-writer automates it
- Code reviews are inconsistent → (future) code-reviewer enforces philosophy
- Knowledge gets lost → (future) knowledge-synthesizer extracts and connects it

### 2. Embodies a Metacognitive Recipe

A **metacognitive recipe** is a structured thinking process - the "how should AI think through this problem?"

The blog-writer's recipe:

1. "First, understand the author's style from their writings"
2. "Then draft content matching that style"
3. "Review the draft for accuracy against sources"
4. "Review the draft for style consistency"
5. "Get user feedback and refine"

You describe the thinking process, Amplifier handles making it work. No need to understand async/await, retry logic, state management, or file I/O - just describe HOW the tool should think.

### 3. Works Dependably

Because Amplifier's patterns handle the complexity, these tools:

- ✅ Can be interrupted and resumed
- ✅ Show progress as they work
- ✅ Save checkpoints automatically
- ✅ Provide clear error messages
- ✅ Handle retries and failures gracefully

You get dependable tools from minimal input.

### 4. Shows What's Possible

Each tool demonstrates:

- **README.md** - "What does this solve and how do I run it?"
- **HOW_TO_CREATE_YOUR_OWN.md** - "Here's how you can create something like this"
- **The recipe** - The thinking process that guides it
- **Real examples** - Actual inputs and outputs you can try

## Quick Start

**Prerequisites**: Complete the [Amplifier setup instructions](../README.md#-step-by-step-setup) first.

### Running a Tool

Each tool is self-contained and can be run via `make` commands (see each tool's README for specific usage).

### Learning from a Tool

1. **Start with README.md** - Understand the problem it solves
2. **Try it yourself** - Run with example inputs
3. **Read HOW_TO_CREATE_YOUR_OWN.md** - See how to create your own
4. **Understand the recipe** - What thinking process guides it?
5. **Build your own** - Describe your goal and recipe to Amplifier

## How to Create a Scenario Tool

1. **Describe your goal**: "I need a tool that does X"
2. **Describe the thinking process**: "It should think through the problem by doing A, then B, then C"
3. **Share with Amplifier**: Use `/ultrathink-task` or work with Claude Code
4. **Iterate if needed**: Refine based on usage
5. **Document the conversation**: Share what you said and how it worked

That's it! You don't need to understand async/await, retry logic, or state management. Just describe WHAT you want and HOW it should think through the problem.

**For detailed guidance and examples**, see [blog-writer/HOW_TO_CREATE_YOUR_OWN.md](./blog_writer/HOW_TO_CREATE_YOUR_OWN.md). The blog-writer tool serves as the exemplar - study its README, HOW_TO_CREATE_YOUR_OWN, and code structure to understand the pattern.

## Design Principles

### Ruthless Simplicity

- Start with the simplest thing that works
- Add complexity only when justified
- Prefer clarity over cleverness
- Code you don't write has no bugs

### Modular Architecture

- Each component has one clear responsibility
- Well-defined contracts between stages
- Components can be regenerated independently
- Following the ["bricks and studs" philosophy](../ai_context/MODULAR_DESIGN_PHILOSOPHY.md)

### User-First Experience

- Clear error messages
- Show progress for long operations
- Resume-friendly for interruptions
- Examples that actually work

## Why "Scenarios" Not "Examples"?

**Examples** are educational demos that show how something works.
**Scenarios** are real tools that solve actual problems _while_ showing what's possible.

The difference:

- ❌ Example: "Here's how to call an LLM"
- ✅ Scenario: "Here's a blog writing tool (built with one conversation)"

Examples teach by showing code. Scenarios teach by showing results.

## Philosophy

These tools demonstrate what's possible when you leverage Amplifier:

1. **Minimal input, maximum leverage** - Describe what you want, get a working tool
2. **Metacognitive recipes** - Structure the thinking process, not the code
3. **Dependable from minimal specification** - Amplifier's patterns handle complexity
4. **Learning through creating** - Build what you need, share what you learned

Every tool here started as "I wish I had something that..." and one conversation later, it existed.

## Getting Started

### Want to Use a Tool?

Pick one that solves your problem, run it with the examples, use it for your work.

### Want to Create a Tool?

Describe your goal and thinking process to Amplifier. That's it. Share the conversation afterward so others can learn.

---

**Remember**: These are experimental tools built with minimal input. They work, but they're not polished products. The goal is showing what's possible when you describe what you want to Amplifier.

Let's build tools by describing what we need, not by coding every detail.
