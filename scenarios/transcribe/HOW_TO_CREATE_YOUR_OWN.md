# How This Transcription Tool Was Created

**This tool was built through a collaborative conversation, not by writing code from scratch.**

This document shows you how the Transcribe tool was created through natural dialogue with Amplifier, so you can understand the process and create your own tools the same way.

## What the Creator Did

The creator didn't write code - they described what they wanted, provided feedback, and let Amplifier handle the implementation. Here's the actual conversation flow:

### Step 1: Initial Request

The creator started with a clear goal:

> *"I want to make a new tool under @scenarios/ modeled on the others already there. What I want is a tool that can create transcripts from audio recordings or youtube videos."*

They specified requirements:
- Save transcripts in `AMPLIFIER_CONTENT_DIRS` under a transcripts subfolder
- Use `.env` for configuration (OpenAI API key, Anthropic API key)
- Consider using YouTube transcripts vs creating our own
- Save video to the same directory
- Multiple output formats (JSON for transforms, MD for readability)
- Include summary document with key quotes and timestamps
- Add YouTube timestamp links to quotes

**Notice**: This wasn't a technical specification. It was a description of **what the tool should do** and **how users would want to interact with it**.

### Step 2: Amplifier Orchestrated the Build

Amplifier broke down the work and used specialized agents:

1. **amplifier-cli-architect** (CONTEXTUALIZE mode) - Evaluated if this fit the amplifier CLI pattern
2. **zen-architect** (ANALYZE/ARCHITECT mode) - Designed the modular architecture
3. **modular-builder** - Implemented the core pipeline with modules:
   - `video_loader` - YouTube downloads and metadata
   - `audio_extractor` - Audio extraction and compression
   - `whisper_transcriber` - OpenAI Whisper API integration
   - `storage` - Multi-format output saving
   - `state` - Resume capability

All of this happened automatically based on the initial description.

### Step 3: Hit an API Error, Restored Context

The conversation was interrupted by an API error. The creator simply asked:

> *"Please read the transcript and restore your context on my request and where you were at."*

Amplifier picked up exactly where it left off and completed the implementation.

### Step 4: Iterated Based on Feedback

The creator provided natural feedback after testing:

**Missing Dependencies Issue:**
> *"I ran uv sync in my venv why do I not have the dependencies I need?"*

Amplifier immediately:
- Identified missing `yt-dlp` and `anthropic` packages
- Added them to `pyproject.toml`
- Updated to latest versions
- Fixed README installation instructions

**Output Format Improvements:**
> *"I wonder if the quotes and summary should be a single summary markdown doc. For the transcript.md doc I wonder if we need both the timestamped and transcript sections, it is the same content right? Could we break the transcript down so it is easier to read into paragraphs?"*

Amplifier:
- Used zen-architect to analyze the request
- Designed improved output format (combined insights.md, paragraphed transcript.md)
- Created new modules (transcript_formatter, insights_generator)
- Updated storage to use new formatters

**Audio File Management:**
> *"What are we doing with the mp3 from the youtube video? Maybe those should be cached under our .data directory so we don't have to do that over and over again, but also just seems like the user might want those..."*

Amplifier:
- Analyzed current behavior (audio was being deleted)
- Designed simple content-based caching (audio lives with transcript)
- Implemented cache checking and audio persistence
- Added `--force-download` flag for control

## Key Features That Emerged

Through this iterative conversation:

✅ **Core Functionality**
- YouTube and local file transcription
- OpenAI Whisper API integration
- Multi-format output (JSON, MD, VTT, SRT)
- State management for resume capability

✅ **User Experience Improvements**
- Readable paragraph formatting with timestamps
- Clickable YouTube timestamp links
- Combined insights document (summary + quotes)
- Audio file caching (avoid re-downloads)
- Cost estimation before processing

✅ **Developer Experience**
- Modular "bricks & studs" architecture
- Clean separation of concerns
- Easy to extend or modify
- Follows project philosophy

## The Conversation Pattern

Notice how the creator interacted:

1. **Described goals, not implementations**: "I want to transcribe videos" not "Create a class that calls the Whisper API"

2. **Provided context**: Referenced existing tools, mentioned the AMPLIFIER_CONTENT_DIRS pattern

3. **Asked questions**: "Should we use YouTube's transcript or create our own?"

4. **Gave natural feedback**: "This seems duplicated" or "Users probably want access to the audio files"

5. **Trusted the process**: Let Amplifier choose architectures, libraries, and implementations

## What Amplifier Handled Automatically

The creator didn't need to know:
- How to integrate OpenAI Whisper API
- How to use yt-dlp for YouTube downloads
- How to implement state management for resume capability
- How to format WebVTT and SRT subtitle files
- How to group text into paragraphs based on natural pauses
- Which Anthropic models to use for summaries
- How to implement audio file caching
- How to structure modular Python code

Amplifier chose appropriate:
- Libraries (yt-dlp, openai, anthropic, ffmpeg)
- Architectures (modular pipeline with state management)
- Patterns (content-based caching, graceful degradation)
- Error handling (retry logic, validation)

## Timeline

From idea to working tool:
- **Initial request**: Described the goal
- **First implementation**: ~7 minutes (3 agents in sequence)
- **Dependency fixes**: ~2 minutes
- **Output improvements**: ~5 minutes (zen-architect → modular-builder)
- **Audio caching**: ~4 minutes (zen-architect → modular-builder)

**Total active time**: About 20 minutes of conversation spread across multiple sessions.

## How You Can Create Your Own Tool

### 1. Start with a Clear Goal

Describe what you want to accomplish:
- "I need to transcribe videos and extract key quotes"
- "I want to summarize long documents"
- "I need to process images and extract text"

### 2. Provide Context

Reference existing patterns:
- "Like the blog_writer but for videos"
- "Use AMPLIFIER_CONTENT_DIRS for output"
- "Save results in multiple formats"

### 3. Use `/ultrathink-task`

Start your conversation:
```
/ultrathink-task Create me a tool that [your goal]
```

Amplifier will:
- Use specialized agents (zen-architect, modular-builder, etc.)
- Design the architecture
- Implement the code
- Add error handling and state management
- Create documentation

### 4. Provide Natural Feedback

When you test the tool, just describe what you notice:
- "The output format seems duplicated"
- "I think users would want access to these files"
- "Could this be more readable?"
- "What happens if I run this twice on the same video?"

### 5. Trust the Iteration

Amplifier will:
- Understand your feedback
- Design improvements
- Implement changes
- Verify everything still works

## Real Examples from This Tool

### Example 1: Dependency Management

**User**: "Why don't I have the dependencies I need?"

**Amplifier**:
1. Checked pyproject.toml
2. Identified missing packages
3. Added with correct versions: `uv add yt-dlp anthropic`
4. Updated documentation
5. Verified all checks pass

### Example 2: Output Format Refinement

**User**: "Could we break the transcript down into paragraphs?"

**Amplifier**:
1. Used zen-architect to analyze the request
2. Designed paragraph grouping strategy (30-60 second windows, natural pauses)
3. Created transcript_formatter module
4. Implemented insights_generator to combine summary and quotes
5. Updated storage to use new formatters
6. Verified readable output

### Example 3: Audio File Caching

**User**: "Maybe those [audio files] should be cached... users might want those"

**Amplifier**:
1. Used zen-architect to design caching strategy
2. Chose simple content-based storage (not complex cache system)
3. Modified video_loader to check for existing files
4. Added save_audio to storage module
5. Removed audio cleanup
6. Added --force-download flag for control

## Principles That Made This Work

### 1. Describe Intent, Not Implementation

**Good**: "I want cached audio to avoid re-downloading"
**Not**: "Create a LRU cache with TTL and size limits"

### 2. Provide Feedback Based on Usage

**Good**: "The transcript is hard to read without paragraph breaks"
**Not**: "Implement a text segmentation algorithm"

### 3. Trust Specialized Agents

Amplifier used:
- `zen-architect` for design decisions
- `modular-builder` for implementation
- `bug-hunter` for issues (when needed)
- `post-task-cleanup` for final cleanup

### 4. Iterate Naturally

The tool evolved:
1. Basic transcription ✅
2. Fixed dependencies ✅
3. Improved readability ✅
4. Added caching ✅

Each iteration was a conversation, not a specification.

## Common Questions

**Q: Do I need to understand the code?**
A: No. You need to understand your problem domain and be able to describe what you want. Amplifier handles implementation.

**Q: What if I don't know the right architecture?**
A: That's fine. Describe your goal and let zen-architect design the architecture. It follows project philosophy automatically.

**Q: Can I modify the code after?**
A: Yes, but it's usually easier to describe what you want changed and let Amplifier update it. These tools follow "describe and regenerate" pattern.

**Q: How do I know if my tool should be a scenario?**
A: If it processes multiple items with AI, uses structured iteration, and would be useful as a permanent CLI tool, it's probably a good fit for scenarios/.

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

4. **Iterate based on usage** - Provide feedback naturally as you use it

5. **Share what you create** - Add it to scenarios/ to help others

---

**Remember**: The person who created this tool described what they wanted in natural language. Amplifier handled all the implementation details. You can do the same.

For more examples and guidance, see [HOW_TO_CREATE_YOUR_OWN.md in the blog_writer scenario](../blog_writer/HOW_TO_CREATE_YOUR_OWN.md) and the [main scenarios README](../README.md).
