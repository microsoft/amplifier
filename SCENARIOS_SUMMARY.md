# Amplifier Scenarios System - Quick Summary

## What You Need to Know

The **Scenarios** directory contains 5 production-ready, fully functional tools that demonstrate Amplifier's core value proposition:

> "Describe what you want and how to think about it. Amplifier handles the implementation."

### The 5 Scenarios

1. **blog_writer** (THE EXEMPLAR) - 1,300 LOC
   - Transforms rough ideas into polished blog posts
   - Learns author's writing style from examples
   - Iterative feedback loop with user
   - **Study this first** - it's the reference implementation

2. **tips_synthesizer** - 500 LOC
   - Synthesizes scattered tips into cohesive guides
   - Multi-stage extraction → organization → synthesis
   - Simpler than blog_writer, good learning example

3. **article_illustrator** - 1,500 LOC
   - Generates AI illustrations for markdown articles
   - Multi-API support (GPT-Image-1, DALL-E, Imagen)
   - Cost tracking and resumable sessions
   - **Learn multi-API patterns here**

4. **transcribe** - 2,000+ LOC
   - Converts YouTube/audio to searchable transcripts
   - 8 coordinated modules (most complex scenario)
   - Batch processing with state management
   - **Learn large-scale orchestration here**

5. **web_to_md** - 1,800+ LOC
   - Converts web pages to markdown
   - Detects and blocks paywalled content
   - Downloads images locally, organizes by domain
   - **Learn defensive programming & error handling**

## Key Insight: The Metacognitive Recipe

Each scenario is built on a **thinking process**, not code specifications:

**blog_writer's recipe:**
1. "Understand author's style from their writings"
2. "Draft content matching that style"
3. "Review for accuracy against source material"
4. "Review for style consistency"
5. "Get user feedback and refine iteratively"

**The creator** didn't write a single line of code. They:
- Described the goal
- Described the thinking process
- Let Amplifier build it
- Iterated to refine

**Total time**: One conversation session.

## Architecture Patterns (Used in All Scenarios)

### Pattern 1: Modular Design
- Each module has ONE clear responsibility
- Organized in subdirectories (150-250 lines each)
- Clear contracts via `__init__.py`
- Can be understood independently

### Pattern 2: State Persistence
- Save state after EVERY operation
- Enables resume from any point
- No work lost on interruption
- JSON-based for transparency

### Pattern 3: Async/Await for LLMs
- Non-blocking API calls
- Timeout and retry handling
- Progress reporting during long ops

### Pattern 4: Defensive Parsing
- LLMs don't return perfect JSON
- Use `parse_llm_json()` utilities
- Handle markdown blocks, extra text, etc.

### Pattern 5: Explicit Stage Transitions
```
initialized → extraction → writing → review → complete
```
- State file tracks current stage
- Resume picks up from same stage
- Clear pipeline flow

## Where to Start

### If You Want to USE These Tools
1. Pick one that solves your problem
2. Read its README.md
3. Try with example data (in tests/ directory)
4. Adapt for your content

### If You Want to LEARN from These Tools
**Recommended order:**
1. Read `/scenarios/README.md` - System philosophy
2. Read `/scenarios/blog_writer/README.md` - What it does
3. Read `/scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md` - How it was built
4. Study code in order:
   - `state.py` (215 lines) - State persistence
   - `main.py` (452 lines) - Orchestration
   - `blog_writer/core.py` (240 lines) - Module pattern
   - Other `*/core.py` files - See similar modules

### If You Want to CREATE Your Own Tool
1. Identify a real problem you want to solve
2. Describe the **thinking recipe** (not code)
3. Use `/ultrathink-task` to start conversation with Amplifier:
   ```
   /ultrathink-task Create a tool that [GOAL].
   It should think through this by: [THINKING PROCESS]
   ```
4. Let Amplifier generate the implementation
5. Test and iterate
6. Share your creation

## File Locations & Key Documents

**Master Documentation**:
- `scenarios/README.md` - System overview and philosophy
- `SCENARIOS_DOCUMENTATION.md` - This comprehensive analysis

**Each Scenario Has**:
- `README.md` - What it does and how to use it
- `HOW_TO_CREATE_YOUR_OWN.md` - How it was created
- `__main__.py` - CLI entry point
- `main.py` - Pipeline orchestrator
- `state.py` - State persistence
- `module_name/` - Each module directory
- `tests/` - Example inputs

**Supporting Documentation**:
- `CLAUDE.md` - Project instructions
- `AGENTS.md` - AI guidance
- `DISCOVERIES.md` - Lessons learned (defensive patterns)
- `ai_context/IMPLEMENTATION_PHILOSOPHY.md` - Design philosophy
- `ai_context/MODULAR_DESIGN_PHILOSOPHY.md` - Modular approach

## Key Statistics

| Aspect | Finding |
|--------|---------|
| **Total Scenarios** | 5 (all production-ready) |
| **Total LOC** | ~7,800 (excluding tests) |
| **Smallest** | tips_synthesizer (500 LOC) |
| **Largest** | transcribe (2,000+ LOC) |
| **Modules** | 1 (tips) to 8 (transcribe/web) |
| **Pattern Consistency** | All use same core patterns |
| **Learning Difficulty** | Easy (tips) to Hard (transcribe) |

## The Bigger Picture

Scenarios demonstrate a **paradigm shift**:

**Old Way**: Learn to code → Build tools → Document them
**New Way**: Describe what you want → AI builds it → Document the thinking

This works because:
1. **Amplifier provides patterns** - State, modules, orchestration
2. **LLMs handle implementation** - Code generation from specs
3. **Humans provide thinking** - How to approach the problem
4. **Combined = working tools** - Built from minimal specification

## Important: These Are Experimental

**Status**: "Production Experimental"
- Code works and is tested
- Implements solid patterns
- Ready to use TODAY
- May evolve based on usage
- Safe to build on top of

## Next Actions

1. **Explore**: Read `scenarios/README.md`
2. **Study**: Use blog_writer as reference implementation
3. **Try**: Run with sample data in `tests/` directories
4. **Learn**: Follow learning order above
5. **Create**: Build your own tool using the recipe

---

For complete technical details, see: `SCENARIOS_DOCUMENTATION.md`
