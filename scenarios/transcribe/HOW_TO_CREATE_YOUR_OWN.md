# How to Create Your Own Tool Like This

**You don't need to be a programmer. You just need to describe what you want.**

This document shows you how the Transcribe tool was created with minimal input, so you can create your own tools the same way.

## What the Creator Did

The person who "created" this tool didn't write a single line of code. Here's what they actually did:

### Step 1: Described What They Wanted

They started a conversation with Amplifier and described their goal in natural language:

> *"I want to make a new tool under @scenarios/ modeled on the others already there. What I want is a tool that can create transcripts from audio recordings or youtube videos."*

That's it. **No code. No architecture diagrams. No technical specifications.**

### Step 2: Described the Thinking Process

Notice what they described:
1. "Download audio from YouTube or use local files"
2. "Transcribe using speech-to-text"
3. "Format into readable paragraphs"
4. "Generate summaries with key quotes"
5. "Save everything for future reference"

This is what we call a **metacognitive recipe** - the "how should this tool think about the problem?" They described the thinking process, not the implementation.

### Step 3: Let Amplifier Build It

Amplifier:
- Used specialized agents (zen-architect, modular-builder)
- Implemented all the code (~2900 lines across 21 files)
- Added YouTube download support
- Integrated OpenAI Whisper API
- Created readable formatting
- Built state management for resume
- Handled all error cases

**The creator didn't need to know:**
- How to use yt-dlp for YouTube downloads
- How to integrate Whisper API
- How to format timestamps
- How to handle audio compression
- How to manage state for resume
- Which libraries to use

### Step 4: Iterated to Refine

The tool didn't work perfectly on the first try. A few rounds of natural feedback:

**"I wonder if the quotes and summary should be a single markdown doc?"**

Amplifier immediately:
- Combined them into insights.md
- Created the insights_generator module
- Updated storage logic

**"What about podcasts? Can we support Apple Podcasts URLs?"**

Amplifier:
- Researched platform support
- Found technical limitations
- Recommended focusing on YouTube (complexity vs value)
- Creator agreed: "Good points, let's leave as is"

**"Can we prevent mid-sentence breaks in the transcript?"**

Amplifier:
- Analyzed current output
- Implemented sentence boundary detection
- Fixed paragraph formatting

**"What are we doing with the mp3 files? Users might want those..."**

Amplifier:
- Changed from deleting to preserving audio
- Added caching to avoid re-downloads
- Audio now saved with transcripts

## How You Can Create Your Own Tool

### 1. Find a Need

Ask yourself:
- What repetitive task takes too much time?
- What process do I wish was automated?
- What would make my work easier?

**Examples from this repo:**
- "I need to transcribe videos and extract insights"
- "I need to write blog posts but it takes hours"
- "I need to extract knowledge from my documentation"

### 2. Describe the Thinking Process

Not the code, the **thinking**. How should the tool approach the problem?

**Good examples:**
- "First download the audio, then transcribe it, then format it nicely, then extract key points"
- "Read my existing writings, understand my style, draft new content matching that style"
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
- "The output format seems hard to read"
- "I think users would want these files preserved"
- "Can we add feature X?"

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
A: The transcribe tool took about 90 minutes of conversation across 3 sessions. Your mileage may vary based on complexity.

**Q: What if I don't know how to describe the thinking process?**
A: Start with: "I want a tool that does X. It should first do A, then B, then C." Amplifier will help you refine from there.

**Q: Can I modify the code after Amplifier creates it?**
A: You can, but it's usually easier to describe what you want changed and let Amplifier update it. Remember: these tools follow the "describe and regenerate" pattern, not the "edit line by line" pattern.

**Q: What if my tool idea is too complex?**
A: Break it into smaller pieces. Create a simple version first, then add features one at a time.

## Next Steps

- **Try the transcribe tool** to see what's possible
- **Brainstorm ideas** for your own tools
- **Start a conversation** with Amplifier
- **Share what you create** so others can learn

---

**Remember**: The person who created this tool didn't write any code. They just described what they wanted and how it should think. You can do the same.

For more examples and guidance, see the [main scenarios README](../README.md).