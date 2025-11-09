# How to Create Your Own Tool Like This

**You don't need to be a programmer. You just need to describe what you want.**

This document shows you how the Recipe Extractor was created using Document-Driven Development, so you can create your own tools the same way.

---

## What the Creator Did

The person who "created" this tool didn't write a single line of code. Here's what they actually did:

### Step 1: Described What They Wanted

They started with a simple, focused request:

> *"I want to create a tool that takes in a recipe website URL and pulls the recipe out and writes it to a new markdown file. I want to be able to search these recipes eventually. For now I just want to fetch, parse and save. I would also like it to have 1x, 2x, 3x section under ingredients list to help scale up recipes. I also want it to convert cups to grams or mls."*

That's it. **No code. No architecture diagrams. No technical specifications.** Just a clear description of the problem and what the solution should do.

### Step 2: Amplifier Proposed an Approach

Amplifier analyzed the request and performed reconnaissance:
- Found similar tools (web_to_md, blog_writer) to learn patterns
- Identified existing libraries that solve the hard parts
- Proposed using recipe-scrapers (200+ sites) instead of building custom parsers
- Suggested pint library for ingredient-aware unit conversions

The creator just said: **"sounds good"**

### Step 3: Document-Driven Development

Instead of jumping straight to code, Amplifier:
1. **Created a complete plan** (`ai_working/ddd/plan.md`) with:
   - Problem statement (why this matters)
   - Proposed solution (high-level approach)
   - Architecture design (module boundaries)
   - Implementation order (which pieces to build first)
   - Test strategy (how to verify it works)

2. **Got approval** before writing any code
   - "Does this design solve your problem?"
   - Creator: **"approved"**

3. **Wrote all documentation first** (this README, HOW_TO_CREATE_YOUR_OWN.md, etc.)
   - Documentation describes how the tool works (present tense)
   - Written as if the tool already exists
   - Code is built to match the docs exactly

4. **Implements the code** to match the specification
   - Documentation IS the specification
   - No guessing about requirements
   - No "we'll figure it out as we go"

### Step 4: The Creator Didn't Need to Know

The creator never wrote:
- Python code for fetching recipes
- Logic for parsing ingredients
- Math for scaling quantities
- Unit conversion algorithms
- State management for resumable processing
- CLI interface
- Error handling

Amplifier handled all of that based on the original simple request.

---

## The Key Insight: Use Proven Libraries

One of the best design decisions was **NOT building everything from scratch**:

### What We Didn't Build

- Recipe parsers for 200+ websites (would take months)
- Custom unit conversion system (complex and error-prone)
- Ingredient parsing from text (hard NLP problem)

### What We Used Instead

- `recipe-scrapers` library → Already supports 200+ sites
- `pint` library → Handles all unit conversions with ingredient awareness
- Simple Python modules → Glue code to connect the libraries

**Philosophy**: Use battle-tested libraries for the hard parts, write minimal glue code.

This is **ruthless simplicity** in action: solve the problem with the least code possible.

---

## How You Can Create Your Own Tool

### 1. Start with Document-Driven Development

Run `/ddd:1-plan` and describe what you want:

```bash
# Example prompt:
I want a tool that takes markdown files and extracts all the code blocks,
runs them through a linter, and reports which ones have issues. I'd like
to be able to fix them in place or save the corrected versions.
```

**What makes a good request:**
- Clear problem statement (what are you trying to solve?)
- Specific requirements (what should it do?)
- Scope boundaries (what's in, what's out?)

### 2. Amplifier Does Reconnaissance

Amplifier will:
- Search for similar existing tools to learn patterns
- Identify relevant libraries that solve parts of your problem
- Propose architecture approaches
- Ask clarifying questions if needed

**You don't need to know:**
- What libraries exist
- How to structure the code
- What patterns to follow

### 3. Review and Approve the Plan

Amplifier will present:
- **Problem framing**: Does this capture what you need?
- **Proposed solution**: Does this approach make sense?
- **Alternatives considered**: Other ways to solve it and why not chosen
- **Implementation plan**: How it will be built

**You just need to:**
- Read the plan
- Confirm it solves your problem
- Approve or provide feedback

### 4. Documentation Gets Written First

Before any code is written:
- README explains how the tool works
- Examples show what commands to run
- Output samples demonstrate results
- Philosophy alignment documented

**Why this matters:**
- Prevents building the wrong thing
- Creates clear specification for code
- Enables "retcon" approach (write as if exists)
- Much cheaper to change docs than code

### 5. Code Is Built to Match Docs

Implementation follows the documentation exactly:
- Every feature described in docs gets implemented
- Command syntax matches examples
- Output format matches samples
- No surprises or deviations

**You review by:**
- Using the tool (does it work as described?)
- Checking output (matches examples?)
- Testing edge cases (handles errors well?)

---

## Real Example: Recipe Extractor Timeline

### Planning Phase (30 minutes)

1. **Initial request** → User describes recipe extraction need
2. **Reconnaissance** → Amplifier finds similar tools and libraries
3. **Proposal** → Amplifier suggests recipe-scrapers + pint approach
4. **Approval** → User says "sounds good"
5. **Plan created** → Complete specification written
6. **Final approval** → User says "approved"

### Documentation Phase (Current)

1. **README.md** → How to use the tool (you're reading the result)
2. **HOW_TO_CREATE_YOUR_OWN.md** → This file explaining the process
3. **pyproject.toml** → Dependencies and configuration
4. **Makefile** → Command integration
5. **scenarios/README.md** → Updated with new tool

### Implementation Phase (Next)

1. **Code reconnaissance** → Map out exact files to create
2. **Module implementation** → Build each piece (fetcher, converter, etc.)
3. **Testing** → Verify against documented behavior
4. **Cleanup** → Polish and prepare for use

**Total time from idea to working tool: One development session**

---

## The Document-Driven Development Phases

### Phase 0: Planning & Design
- Describe what you want
- Amplifier researches solutions
- Design is proposed and approved
- Complete plan created

### Phase 1: Documentation Retcon
- All docs written first
- Examples and usage patterns defined
- Written as if tool already exists
- User reviews and approves

### Phase 2: Code Reconnaissance
- Map existing codebase
- Identify files to change
- Create implementation plan
- Verify understanding

### Phase 3: Implementation
- Build modules following plan
- Test against documented behavior
- Iterate on feedback

### Phase 4: Verification & Cleanup
- Test all examples from docs
- Fix any issues found
- Polish and finalize

**Key principle**: Each phase has an approval gate. Nothing moves forward without explicit approval.

---

## Key Principles That Made This Work

### 1. Library-First Thinking

Don't build what already exists:
- Recipe parsing? → Use recipe-scrapers (200+ sites)
- Unit conversion? → Use pint (ingredient-aware)
- State management? → Follow existing patterns from web_to_md

**Time saved**: Weeks of development avoided

### 2. Start Minimal, Grow as Needed

The request explicitly said:
- "For now I just want to fetch, parse and save"
- "I want to be able to search these recipes eventually"

**What we built**: Just fetch, parse, save
**What we designed for**: Rich metadata for future search
**What we didn't build**: Search (not needed yet)

This is **ruthless simplicity**: Do what's needed now, enable growth later.

### 3. Documentation IS the Specification

Traditional approach:
```
Write vague docs → Build code → Code doesn't match docs → Update docs → Repeat
```

DDD approach:
```
Write complete docs (as if exists) → Build code to match → Done
```

**Why this works**: No ambiguity, no guessing, clear success criteria.

### 4. Philosophy Alignment

Every design decision checked against:
- **Ruthless Simplicity**: Use libraries, avoid custom code
- **Modular Design**: Clear boundaries between fetcher/converter/writer
- **Follow Patterns**: Learn from existing scenario tools

---

## Common Questions

### Q: Do I need to be a programmer?

**A**: No. You need to:
- Describe your problem clearly
- Understand what you want the tool to do
- Provide feedback on the design

Amplifier handles all implementation.

### Q: How long does it take?

**A**: For the recipe extractor:
- Planning: 30 minutes
- Documentation: 1-2 hours
- Implementation: 2-3 hours (estimated)

**Total**: One development session from idea to working tool.

### Q: What if I don't know what libraries exist?

**A**: That's Amplifier's job. During reconnaissance, Amplifier:
- Searches for relevant libraries
- Evaluates trade-offs
- Proposes the best approach
- Explains the reasoning

You just approve or ask questions.

### Q: Can I change my mind later?

**A**: Absolutely. Because of the modular design:
- Modules can be regenerated independently
- Changes don't break the whole system
- Documentation update triggers code update

Example: Want to add image downloading? Update docs, regenerate the fetcher module.

### Q: What makes a good tool request?

**Good requests are:**
- **Specific**: "Extract recipes from URLs and save as markdown"
- **Focused**: "Just fetch, parse, save for now"
- **Honest about scope**: "I want to search them eventually"

**Bad requests are:**
- **Vague**: "Make something for recipes"
- **Kitchen sink**: "Do everything related to recipes"
- **Technically detailed**: "Use BeautifulSoup to parse HTML"

---

## Try It Yourself

### Step 1: Think of a Tool You Need

Examples:
- Extract quotes from PDFs into markdown
- Analyze code for common patterns
- Generate test data from schemas
- Summarize long documents
- Convert between file formats

### Step 2: Run DDD Planning

```bash
make claude

# In Claude Code:
/ddd:1-plan I want a tool that [describe your need]
```

### Step 3: Follow the Process

- Review reconnaissance findings
- Approve or provide feedback on design
- Review documentation when complete
- Test the working tool

### Step 4: Share What You Learn

If your tool works well:
- Add it to scenarios/
- Write your own HOW_TO_CREATE_YOUR_OWN.md
- Help others learn from your process

---

## Next Steps

**See it in action**:
- Try the recipe extractor: `make recipe-extract URL=https://example.com/recipe`
- Read the complete plan: `cat ai_working/ddd/plan.md`
- Study the DDD methodology: `docs/document_driven_development/`

**Create your own**:
- Think about what tool you need
- Run `/ddd:1-plan` with your description
- Follow the phases
- Share what you create

---

## The Bottom Line

**You provided**: One paragraph describing what you wanted

**Amplifier provided**:
- Research into existing solutions
- Architecture design
- Complete documentation
- Implementation plan
- Working code (coming next phase)

**Time saved**: Weeks of development

**Code you wrote**: Zero lines

That's the power of Document-Driven Development with Amplifier.

---

**Return to**: [Recipe Extractor README](./README.md) | [Scenarios Overview](../README.md)
