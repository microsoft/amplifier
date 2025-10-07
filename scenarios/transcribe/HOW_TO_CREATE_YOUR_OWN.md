# How to Create Your Own Tool Like This

**You don't need to be a programmer. You just need to describe what you want.**

This document shows you how the Transcription tool was created through natural conversation with Amplifier, so you can create your own tools the same way.

## What the Creator Did

The creator didn't write a single line of code. Here's what they actually did:

### Step 1: Described What They Wanted

They started a conversation with Amplifier and described their goal in natural language:

> *"I want to make a new tool under @scenarios/ modeled on the others already there. What I want is a tool that can create transcripts from audio recordings or youtube videos."*

They specified requirements:
- Save transcripts in `AMPLIFIER_CONTENT_DIRS`
- Multiple output formats (JSON, Markdown, subtitles)
- Include summary with key quotes and timestamps
- Add YouTube timestamp links
- Use `.env` for API keys

**Notice**: This wasn't a technical specification. It was a description of **what the tool should do** and **how users would interact with it**.

### Step 2: Let Amplifier Build It

Amplifier broke down the work and used specialized agents:

1. **amplifier-cli-architect** - Evaluated if this fit the amplifier CLI pattern
2. **zen-architect** - Designed the modular architecture
3. **modular-builder** - Implemented the core pipeline:
   - `video_loader` - YouTube downloads and metadata
   - `audio_extractor` - Audio extraction and compression
   - `whisper_transcriber` - OpenAI Whisper API integration
   - `storage` - Multi-format output saving
   - `state` - Resume capability

All of this happened automatically based on the initial description.

### Step 3: Gave Feedback After Testing

The creator provided natural feedback after trying the tool:

**"Why don't I have the dependencies I need?"**

Amplifier immediately:
- Checked `pyproject.toml`
- Added missing packages: `uv add yt-dlp anthropic`
- Updated to latest versions
- Fixed installation documentation

**"I wonder if the quotes and summary should be a single markdown doc?"**

Amplifier:
- Used zen-architect to analyze the request
- Designed combined insights.md format
- Created insights_generator module
- Updated storage to use new formatter

**"Could we break the transcript down into paragraphs?"**

Amplifier:
- Designed paragraph grouping strategy
- Created transcript_formatter module
- Implemented readable paragraph output

**"What are we doing with the mp3 files? Users might want those..."**

Amplifier:
- Analyzed current behavior (audio was being deleted)
- Designed simple content-based caching
- Modified video_loader to check for existing files
- Audio now persists in output directory

**"Are we sure that anthropic dependency is current?"**

Amplifier:
- Checked latest version available
- Updated from 0.68.0 to 0.69.0
- Verified API compatibility

### Step 4: Continued Iterating with Questions

**"Can we put a part of the title in the folder name?"**

Amplifier:
- Used zen-architect to analyze options
- Recommended simpler approach (keep ID-only folders)
- Proposed index.md instead
- Implemented index generation

**"Can we prevent mid-sentence breaks in the transcript?"**

Amplifier:
- Examined current output
- Researched speaker identification (user asked about this too)
- Designed sentence boundary detection
- Implemented two-stage formatting (inline timestamps + smart paragraphs)

**"Can we automatically update the index when processing finishes?"**

Amplifier:
- Added index update to end of pipeline
- Graceful error handling
- Updated documentation

## The Pattern That Emerged

Throughout this conversation, the creator **never wrote code**. They:

1. ✅ **Described what they wanted**: "I want transcripts from YouTube videos"
2. ✅ **Gave feedback on outputs**: "This seems duplicated" or "Hard to read without paragraphs"
3. ✅ **Asked questions**: "What about podcast URLs?" or "Are we sure this dependency is current?"
4. ✅ **Made suggestions**: "Maybe those should be cached" or "Could we put title in folder name?"
5. ✅ **Decided on tradeoffs**: "I like the index approach, go with option B"

Amplifier handled:
- Architecture design (via zen-architect)
- Code implementation (via modular-builder)
- Research (web search for latest dependencies, platform support)
- Testing (verifying checks pass)
- Documentation (README, HOW_TO)

## What Amplifier Handled Automatically

The creator didn't need to know:
- How to integrate OpenAI Whisper API
- How to use yt-dlp for YouTube downloads
- How to implement state management for resume capability
- How to format WebVTT and SRT subtitle files
- How to detect sentence boundaries
- Which Anthropic models to use for summaries
- How to implement audio file caching
- How to structure modular Python code
- How to generate clickable YouTube timestamp links

Amplifier chose appropriate:
- Libraries (yt-dlp, openai, anthropic, ffmpeg)
- Architectures (modular pipeline with state management)
- Patterns (content-based caching, graceful degradation)
- Error handling (retry logic, validation)

## Real Examples from Our Conversation

### Example 1: Understanding vs Building

**Creator**: "What about podcasts? Can we support Apple Podcasts, iHeart, Spotify URLs?"

**Amplifier**:
- Researched yt-dlp support for each platform
- Found: Apple/iHeart work, Spotify broken
- Researched RSS feed alternatives
- **Recommended against adding it** (complexity vs value)
- Explained the reasoning

**Creator**: "Good points, let's leave as is"

Notice: The creator asked a question, Amplifier researched and made a recommendation, creator decided. No code written because the feature was rejected.

### Example 2: Format Iteration

**Creator**: "Can we prevent mid-sentence breaks? I'm curious if we can include speaker identification but no is a fine answer there."

**Amplifier**:
- Examined current output (found massive 3000-word paragraphs)
- Researched speaker identification (Whisper doesn't support it)
- Recommended: Fix paragraphs (high value), skip speakers (low value/complexity ratio)

**Creator**: "I would prefer even if at 2x to wait until the punctuation break"

**Amplifier**:
- Updated design to always wait for sentence endings
- Implemented simpler approach than originally proposed
- No forced breaks at any duration

Notice: The creator refined requirements mid-implementation. Amplifier adapted.

### Example 3: Storage Location

**Creator**: "It might make more sense to save the .json, srt/vtt files in .data folder rather than the content folder as this is more related data"

**Amplifier**:
- Used zen-architect to analyze both approaches
- **Argued against the change** (self-contained folders better)
- Explained VTT/SRT are user content, not technical artifacts

**Creator**: "Good points, let's leave as is"

Notice: Amplifier pushed back with reasoning. Creator accepted the architectural guidance.

## Timeline of Development

**Session 1:**
- Initial request and implementation (~20 minutes)
- Hit API error mid-work

**Session 2:**
- Restored context from transcript
- Fixed type errors
- Added missing dependencies
- Output format improvements (insights.md, paragraphs, timestamps)
- Audio caching implementation
- (~30 minutes)

**Session 3:**
- Dependency version check (anthropic upgrade)
- Podcast URL research (decided against)
- Transcript organization (index.md approach)
- Sentence boundary detection
- Two-stage formatting redesign
- Auto-update index
- (~40 minutes)

**Total active conversation time**: About 90 minutes spread across 3 sessions.

**Total lines of code generated**: ~2900 lines across 21 Python files.

## Principles That Made This Work

### 1. Describe Intent, Not Implementation

**Good**: "I want cached audio to avoid re-downloading"
**Not**: "Create a LRU cache with TTL and size limits"

**Good**: "The transcript is hard to read without paragraph breaks"
**Not**: "Implement a text segmentation algorithm"

**Good**: "Can we prevent mid-sentence breaks?"
**Not**: "Add sentence boundary detection using regex pattern matching"

### 2. Ask Questions Instead of Making Demands

**The creator asked**:
- "What about podcasts?"
- "Are we sure that dependency is current?"
- "What are we doing with the mp3 files?"
- "Can we include speaker identification?"

Amplifier researched, analyzed, and recommended. The creator then decided.

### 3. Provide Feedback on Outputs, Not Code

**The creator said**:
- "This seems duplicated"
- "Hard to read without paragraphs"
- "I don't think this is quite what we want"
- "I would prefer to wait until punctuation break"

They described **what they saw** and **what they wanted**, not how to fix it.

### 4. Trust Specialized Agents

Amplifier orchestrated:
- `zen-architect` for design decisions
- `modular-builder` for implementation
- `post-task-cleanup` for final cleanup
- Web search for research

The creator never needed to know these agents existed.

### 5. Make Decisions on Tradeoffs

When presented with options, the creator decided:
- "I like the index approach, go with option B"
- "Good points, let's leave as is"
- "Just go with the sentence boundary fix"

Amplifier presented analysis and recommendations. Creator made final calls.

## Features That Emerged Through Conversation

**Initial concept:**
- Basic transcription
- Multiple output formats
- Summary and quotes

**After iteration:**
- ✅ Audio file caching (user suggestion)
- ✅ Combined insights.md (user feedback)
- ✅ Readable paragraphs (user feedback)
- ✅ Inline timestamps (user refinement)
- ✅ Sentence boundary detection (user preference)
- ✅ Transcript index (user idea)
- ✅ Auto-updating index (user request)
- ❌ Podcast URLs (researched, decided against)
- ❌ Speaker identification (researched, too complex)
- ❌ Title in folder names (zen-architect recommended against)

Notice: Not all ideas became features. Some were researched and rejected based on complexity/value analysis.

## How You Can Create Your Own Tool

### 1. Find a Need

Ask yourself:
- What repetitive task takes too much time?
- What process do I wish was automated?
- What would make my work easier?

**Examples from this repo:**
- "I need to transcribe videos and extract insights"
- "I need to write blog posts in my style"
- "I need to extract knowledge from documentation"

### 2. Describe the Thinking Process

Not the code, the **thinking**. How should the tool approach the problem?

**Good examples:**
- "Download audio, transcribe it, generate a summary, extract key quotes"
- "Read my writings, understand my style, draft content matching that style"
- "Process each file, extract concepts, find relationships, build a knowledge graph"

**Bad examples:**
- "Use this library to do X" (too technical)
- "Create a class that does Y" (too implementation-focused)
- "Make it work" (too vague)

### 3. Start the Conversation

In your Amplifier environment:

```bash
claude
```

Then describe your goal using `/ultrathink-task`:

```
/ultrathink-task Create me a tool that [describes your goal]
```

### 4. Provide Feedback as You Test

When you try the tool, just describe what you see:
- "The output format seems duplicated"
- "I think users would want access to these files"
- "Could this be more readable?"
- "I don't think this is quite what we want"
- "Can we prevent X from happening?"

Amplifier will fix it.

### 5. Ask Questions When Unsure

Don't know if something is possible? Ask:
- "What about podcast URLs?"
- "Can we include speaker identification?"
- "Are we sure this dependency is current?"

Amplifier will research and provide recommendations.

### 6. Make Decisions on Tradeoffs

When Amplifier presents options:
- Listen to the reasoning
- Ask clarifying questions
- Decide what aligns with your needs

You're guiding the vision. Amplifier is implementing it.

## Common Questions

**Q: Do I need to be a programmer?**
A: No. You need to understand the problem domain and be able to describe what you want. Amplifier handles all implementation.

**Q: What if I don't know how to describe the thinking process?**
A: Start with: "I want a tool that does X. It should first do A, then B, then C." Amplifier will help you refine from there.

**Q: Can I modify the code after Amplifier creates it?**
A: You can, but it's usually easier to describe what you want changed and let Amplifier update it. Remember: these tools follow the "describe and regenerate" pattern.

**Q: What if my idea doesn't work?**
A: That's fine. Amplifier can research feasibility (like we did with podcast URLs and speaker identification). Some ideas become features, others get refined or rejected based on analysis.

**Q: How long does it take?**
A: This tool took about 90 minutes of conversation across 3 sessions. Your mileage will vary based on complexity and iteration needs.

## Next Steps

1. **Try the transcribe tool** to see what's possible:
   ```bash
   make transcribe SOURCE="https://youtube.com/watch?v=..."
   ```

2. **Think about your own needs**:
   - What repetitive tasks take too much time?
   - What would make your work easier?

3. **Start a conversation** with Amplifier:
   ```bash
   /ultrathink-task Create me a tool that [your goal]
   ```

4. **Iterate based on usage** - Provide feedback naturally as you test it

5. **Share what you create** - Add it to scenarios/ to help others

---

**Remember**: The person who created this tool described what they wanted in natural language and gave feedback on what they saw. Amplifier handled all the code, architecture, research, and implementation. You can do the same.

For more examples and guidance, see [HOW_TO_CREATE_YOUR_OWN.md in the blog_writer scenario](../blog_writer/HOW_TO_CREATE_YOUR_OWN.md) and the [main scenarios README](../README.md).
