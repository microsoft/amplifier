# How to Create Your Own Tool Like This

**You don't need to be a programmer. You just need to describe what you want.**

This document shows you how the Web To MD tool was created with minimal input, so you can create your own tools the same way.

## What the Creator Did

The person who "created" this tool didn't write a single line of code. Here's what they actually did:

### Step 1: Described What They Wanted

They started a conversation with Amplifier and described their goal in natural language:

> _I want you to look at the examples under @scenarios/ so we can make a new tool along those lines._
>
> _What I want is something that I can give a URL to of a web page, convert that to markdown, and save it under AMPLIFIER_CONTENT_DIRS in a folder there called sites/._
>
> _Each page should be in a subfolder named after the domain name of the site so it is easy to find them later._
>
> _We want to keep images, so probably just put them under sites/domain/images for each page we save._
>
> _We should also create an index.md file under sites that links to every page we save._
>
> _We probably want some metadata yaml style that is hidden at the top of each page about the url, date, etc when we retrieved it that could be used in the future to check for updates if we need to._

That's it. **No code. No architecture diagrams. No technical specifications.**

### Step 2: Described the Requirements, Not the Implementation

Notice what they described:

1. "Convert web page to markdown"
2. "Save in domain-based folders"
3. "Download and organize images"
4. "Create an index of all pages"
5. "Add metadata for future reference"

This is the **what**, not the **how**. They didn't specify which libraries to use, how to handle errors, or how to structure the code.

### Step 3: Let Amplifier Build It

Amplifier used specialized agents to handle different aspects:

**Planning Phase:**

- `amplifier-cli-architect` - Determined this fit the amplifier CLI pattern
- `zen-architect` - Designed the modular architecture

**Implementation Phase:**

- `modular-builder` - Implemented all 8 modules:
  - `fetcher/` - Downloads pages with retry logic
  - `converter/` - HTML to markdown conversion
  - `validator/` - Paywall and auth wall detection
  - `image_handler/` - Image downloading and organization
  - `enhancer/` - AI-powered markdown improvement
  - `organizer/` - Domain-based file organization
  - `indexer/` - Index generation
  - `state.py` - Resume capability

**The creator didn't need to know:**

- How to use httpx for web requests
- How markdownify converts HTML
- How BeautifulSoup parses HTML
- How to detect paywalls
- How to manage state for resume support
- How to integrate with Amplifier's path configuration
- Which error cases to handle

### Step 4: Iterated to Refine

The tool didn't work perfectly on the first try. Here are the issues that came up and how they were fixed:

**Issue 1: Output Directory Location**

- Problem: "Content is being saved to sites/ in project root instead of AMPLIFIER_CONTENT_DIRS"
- Solution: Amplifier integrated with `amplifier.config.paths` module

**Issue 2: Line Break Issues**

- Problem: "Mysterious line breaks in some of the content"
- Solution: Disabled automatic line wrapping in markdown conversion

**Issue 3: Paywall Detection**

- Problem: "We should have graceful failure for authenticated sites"
- Solution: Amplifier added a validator module with pattern detection

Total time from idea to working tool: one conversation session (with interruptions).

## How You Can Create Your Own Tool

### 1. Find a Need

Ask yourself:

- What repetitive task takes too much time?
- What process do I wish was automated?
- What would make my work easier?

**This tool came from:**
"I want to save web articles I find interesting for later reference and AI analysis"

### 2. Describe the Structure and Behavior

Not the code, the **what and where**. What should the tool do and how should it organize things?

**Good examples:**

- "Download web pages, convert to markdown, organize by domain"
- "Take this input, process it this way, save the output here"
- "Read these files, find patterns, create a report"

**Bad examples:**

- "Use httpx to fetch and BeautifulSoup to parse" (too technical)
- "Create a class called WebFetcher with method fetch()" (too implementation-focused)
- "Make it work" (too vague)

### 3. Start the Conversation

In your Amplifier environment:

```bash
claude
```

Then describe your goal using `/ultrathink-task`:

```
/ultrathink-task I want to create a tool that converts web pages to markdown and saves them organized by domain. [Include details about where to save, what metadata to include, etc.]
```

### 4. Provide Feedback as You Test

When you try the tool, you'll likely find issues. Just describe what's wrong:

**From this tool's development:**

- "The web page content is not being saved under AMPLIFIER_CONTENT_DIRS"
- "I see mysterious line breaks in some of the content"
- "We should have graceful failure for authenticated sites"

Each issue was fixed by describing the problem, not by writing code.

### 5. Share It Back (Optional)

If your tool works well and others might benefit:

1. Document what it does (like this tool's README)
2. Document how you created it (this file)
3. Contribute it back to the scenarios/ directory

## What This Tool Demonstrates

### Modular Architecture Patterns

Each module is self-contained and does one thing:

- **fetcher** - Just downloads pages
- **converter** - Just converts HTML to markdown
- **validator** - Just checks for paywalls
- **image_handler** - Just handles images
- **enhancer** - Just improves formatting
- **organizer** - Just saves files in the right place
- **indexer** - Just generates the index

This is the "bricks and studs" philosophy in action.

### Graceful Degradation

The tool works in multiple contexts:

- **With Amplifier**: Uses integrated paths, ToolkitLogger, AI enhancement
- **Without Amplifier**: Falls back to simple logging, current directory
- **With Claude Code SDK**: Enhances markdown with AI
- **Without SDK**: Uses basic formatting

### Error Recovery

Built-in resilience:

- Retry logic for network failures
- State management for resume capability
- Paywall detection to avoid incomplete content
- Cloud sync retry for file I/O (OneDrive/Dropbox)

## The Key Principles

### 1. You Describe, Amplifier Builds

You don't need to know how to code. You need to know:

- What problem you're solving
- What the tool should do with the input
- Where and how to organize the output
- What makes a good vs bad result

### 2. Structure Over Implementation

A clear structure description is all you need:

- "Save pages organized by domain"
- "Include metadata in YAML frontmatter"
- "Don't save pages behind paywalls"
- "Create an index of everything saved"

### 3. Iteration Is Normal

This tool went through several refinements:

1. Initial implementation (working but incorrect output location)
2. Path integration fix (now saves to proper location)
3. Line break fix (cleaner markdown output)
4. Paywall detection (avoids incomplete content)

Each iteration involved describing what wasn't right, not writing code.

### 4. Working Code Beats Perfect Specs

The tool is experimental and ready to use now, not production-perfect. It solves the problem. Improvements come as needs emerge.

## Common Questions

**Q: Do I need to be a programmer?**
A: No. You need to understand what you want and be able to describe it. Amplifier handles all the implementation.

**Q: How long does it take?**
A: This tool took one conversation session (including iteration and fixes). Your mileage may vary based on complexity.

**Q: What if I don't know how to describe what I want?**
A: Start with the basics: "I want a tool that does X. It should save the results to Y." Amplifier will ask clarifying questions.

**Q: Can I modify the code after Amplifier creates it?**
A: You can, but it's usually easier to describe what you want changed and let Amplifier update it. Remember: these tools follow the "describe and regenerate" pattern.

**Q: How do I know if my idea is too complex?**
A: If you can describe it in a few paragraphs, it's probably fine. Break complex ideas into smaller pieces - create a simple version first, then add features.

## Real-World Example: This Tool's Creation

### The Original Request

```
I want a tool that converts web pages to markdown, saves them organized
by domain under AMPLIFIER_CONTENT_DIRS, keeps images in domain/images/,
creates an index.md, and includes metadata YAML frontmatter.
```

### What Amplifier Did

1. **Used amplifier-cli-architect** to understand the scenario pattern
2. **Used zen-architect** to design the modular structure
3. **Used modular-builder** to implement all modules
4. **Used zen-architect again** to review the implementation
5. **Tested and iterated** based on user feedback

### The Iterations

**Iteration 1:** "Content not saving to AMPLIFIER_CONTENT_DIRS"

- Amplifier: Integrated with `amplifier.config.paths`
- Result: Now saves to correct location

**Iteration 2:** "Mysterious line breaks in content"

- Amplifier: Removed line wrapping from conversion
- Result: Clean, natural paragraph flow

**Iteration 3:** "Need graceful failure for authenticated sites"

- Amplifier: Created validator module with paywall detection
- Result: Rejects Medium "member-only" content, NYTimes 403s, etc.

## Getting Started

1. **Complete the [Amplifier setup](../../README.md)**
2. **Think about what you need** - What would make your work easier?
3. **Describe the structure** - What should it do and where should it save things?
4. **Start the conversation** - Use `/ultrathink-task` to describe your goal
5. **Iterate to refine** - Provide feedback as you test it
6. **Share it back** - Help others by contributing your tool

## Example Tool Ideas

Based on the web_to_md pattern, you could create:

### Document Archiver

"A tool that downloads documentation pages from multiple sites, converts to markdown, and organizes by project name"

### Research Paper Collector

"A tool that takes arXiv URLs, downloads PDFs, converts to text, extracts metadata, and organizes by topic"

### Blog Post Scraper

"A tool that monitors RSS feeds, downloads new posts, converts to markdown, and notifies me of new content"

### Knowledge Base Builder

"A tool that crawls a documentation site, converts all pages, and creates a searchable markdown knowledge base"

## Next Steps

- **Try the web_to_md tool** to see what's possible
- **Brainstorm ideas** for your own tools
- **Start a conversation** with Amplifier
- **Share what you create** so others can learn

---

**Remember**: The person who created this tool described what they wanted in a few paragraphs. Amplifier handled all the complexity: choosing libraries, handling errors, integrating with the workspace, detecting paywalls, managing state. You can do the same.

For more examples and guidance, see the [main scenarios README](../README.md).
