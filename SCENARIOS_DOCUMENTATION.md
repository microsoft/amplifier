# AMPLIFIER SCENARIOS SYSTEM - COMPREHENSIVE DOCUMENTATION

**Depth Level**: Very Thorough (Complete Inventory & Architecture Analysis)  
**Date**: 2025-11-06  
**Status**: Production Ready (Experimental)

---

## EXECUTIVE SUMMARY

The Amplifier Scenarios system is a curated collection of **5 production-ready, fully functional tools** that demonstrate how to leverage Amplifier's patterns to solve real-world problems with minimal code specification. Each scenario is built on a **metacognitive recipe** - a structured thinking process - rather than traditional imperative specifications.

**Key Finding**: The scenarios system embodies the project's core philosophy of "describe what you want and how it should think, then let AI build it." The `blog_writer` scenario serves as the exemplar for all others.

**Maturity Model Position**: Scenarios occupy the **middle tier** - beyond `ai_working/` (exploratory), but below `amplifier/` (core infrastructure). They're production-ready tools you can use today while serving as learning exemplars for tool creation.

---

## SECTION 1: COMPLETE SCENARIO INVENTORY

### 1.1 Overview Table

| Scenario | Purpose | Status | Complexity | Modules | Lines of Code |
|----------|---------|--------|-----------|---------|---------------|
| **blog_writer** | Transform rough ideas into polished blog posts matching author's voice | Ready to Use | Medium | 5 modules + orchestrator | ~1,300 |
| **tips_synthesizer** | Transform scattered tips into well-organized, cohesive guides | Ready to Use | Medium | Monolithic + CLI | ~500 |
| **article_illustrator** | Generate contextually relevant AI illustrations for markdown articles | Ready to Use | High | 4 modules + state mgmt | ~1,500 |
| **transcribe** | Convert YouTube videos/audio to searchable, timestamped transcripts | Ready to Use | High | 8 modules + state mgmt | ~2,000+ |
| **web_to_md** | Convert web pages to clean, organized markdown with domain grouping | Ready to Use | High | 8 modules + state mgmt | ~1,800+ |

### 1.2 Directory Tree Structure

```
scenarios/
├── README.md                          # Master documentation & philosophy
├── blog_writer/                       # THE EXEMPLAR - Study this first
│   ├── README.md                      # What it does, how to use it
│   ├── HOW_TO_CREATE_YOUR_OWN.md     # How blog_writer was built (metacognitive recipe example)
│   ├── __init__.py
│   ├── __main__.py                    # CLI entry point
│   ├── main.py                        # Orchestrator (452 lines) - Coordinates pipeline
│   ├── state.py                       # State management for resume (215 lines)
│   ├── blog_writer/                   # Module: Core writing engine
│   │   ├── __init__.py
│   │   └── core.py                    # BlogWriter class (240 lines)
│   ├── style_extractor/               # Module: Analyzes author's style
│   │   ├── __init__.py
│   │   └── core.py                    # StyleExtractor class (188 lines)
│   ├── source_reviewer/               # Module: Verifies accuracy
│   │   ├── __init__.py
│   │   └── core.py                    # SourceReviewer class (216 lines)
│   ├── style_reviewer/                # Module: Checks voice consistency
│   │   ├── __init__.py
│   │   └── core.py
│   ├── user_feedback/                 # Module: Handles user iteration
│   │   ├── __init__.py
│   │   └── core.py
│   └── tests/
│       ├── sample_brain_dump.md       # Example input
│       └── sample_writings/            # Example reference materials
│           ├── article1.md
│           └── article2.md
│
├── tips_synthesizer/                  # Tips aggregation pipeline
│   ├── README.md
│   ├── HOW_TO_CREATE_YOUR_OWN.md
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                         # CLI interface
│   ├── synthesizer.py                 # Main orchestration
│   ├── user_feedback.py               # Feedback integration
│   └── tests/
│       └── sample_tips/
│           ├── debugging_tricks.md
│           ├── productivity_tips.md
│           └── workflow_improvements.md
│
├── article_illustrator/               # AI image generation for articles
│   ├── README.md
│   ├── HOW_TO_CREATE_YOUR_OWN.md
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py                        # Orchestrator
│   ├── state.py                       # Session state for resume
│   ├── models.py                      # Data models
│   ├── content_analysis/              # Module: Analyzes article structure
│   │   ├── __init__.py
│   │   └── core.py
│   ├── prompt_generation/             # Module: Creates image prompts
│   │   ├── __init__.py
│   │   └── core.py
│   ├── image_generation/              # Module: Generates images via APIs
│   │   ├── __init__.py
│   │   ├── core.py
│   │   └── clients.py                 # Multi-API support (GPT, DALL-E, Imagen)
│   ├── markdown_update/               # Module: Inserts images into markdown
│   │   ├── __init__.py
│   │   └── core.py
│   └── tests/
│       ├── sample_article.md
│       └── illustrated/               # Example output
│           ├── .session_state.json
│           └── prompts.json
│
├── transcribe/                        # YouTube/audio transcription
│   ├── README.md
│   ├── HOW_TO_CREATE_YOUR_OWN.md
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py                        # Orchestrator
│   ├── state.py                       # Resume state
│   ├── test_cache.py
│   ├── video_loader/                  # Module: Downloads from YouTube
│   │   ├── __init__.py
│   │   └── core.py
│   ├── audio_extractor/               # Module: Extracts/compresses audio
│   │   ├── __init__.py
│   │   └── core.py
│   ├── whisper_transcriber/           # Module: Calls OpenAI Whisper API
│   │   ├── __init__.py
│   │   └── core.py
│   ├── transcript_formatter/          # Module: Creates readable paragraphs
│   │   ├── __init__.py
│   │   └── core.py
│   ├── summary_generator/             # Module: AI summaries
│   │   ├── __init__.py
│   │   └── core.py
│   ├── quote_extractor/               # Module: Pulls key quotes
│   │   ├── __init__.py
│   │   └── core.py
│   ├── insights_generator/            # Module: Creates insights document
│   │   ├── __init__.py
│   │   └── core.py
│   ├── index_generator/               # Module: Updates transcript index
│   │   ├── __init__.py
│   │   └── core.py
│   └── storage/                       # Module: File organization
│       ├── __init__.py
│       └── core.py
│
└── web_to_md/                         # Web page to markdown converter
    ├── README.md
    ├── HOW_TO_CREATE_YOUR_OWN.md
    ├── __init__.py
    ├── __main__.py
    ├── main.py                        # Orchestrator
    ├── state.py                       # Resume state
    ├── pyproject.toml                 # Standalone Python package config
    ├── fetcher/                       # Module: Downloads web pages
    │   ├── __init__.py
    │   └── core.py
    ├── validator/                     # Module: Paywall detection
    │   ├── __init__.py
    │   └── core.py
    ├── converter/                     # Module: HTML to markdown
    │   ├── __init__.py
    │   └── core.py
    ├── image_handler/                 # Module: Downloads & manages images
    │   ├── __init__.py
    │   └── core.py
    ├── enhancer/                      # Module: AI markdown improvement
    │   ├── __init__.py
    │   └── core.py
    ├── organizer/                     # Module: Domain-based organization
    │   ├── __init__.py
    │   └── core.py
    └── indexer/                       # Module: Index generation
        ├── __init__.py
        └── core.py
```

---

## SECTION 2: DETAILED SCENARIO ANALYSIS

### 2.1 BLOG WRITER - The Exemplar (Study This First)

#### Purpose & Problem Statement

**The Problem**:
- Writing blog posts from rough ideas takes hours
- Generic AI writing doesn't match author's voice
- Quality suffers without deep revision cycles
- No way to preserve personal writing style

**The Solution**:
A multi-stage pipeline that learns author's voice and iteratively refines content.

#### Architecture: The Metacognitive Recipe

The blog_writer embodies a structured **thinking process** (metacognitive recipe):

```
1. "First, understand the author's style from their existing writings"
   └─ StyleExtractor analyzes 3-5 existing posts

2. "Then draft content matching that style"
   └─ BlogWriter creates initial draft from brain dump

3. "Review the draft for accuracy against source material"
   └─ SourceReviewer verifies claims match input

4. "Review for style consistency with author's patterns"
   └─ StyleReviewer checks voice & tone preservation

5. "Get user feedback and incorporate iteratively"
   └─ UserFeedbackHandler integrates bracketed comments

6. "Repeat review cycle until quality gates pass"
   └─ Pipeline orchestrator manages state & iterations
```

**Critical Insight**: This is NOT imperative "how to implement" - it's DECLARATIVE "how to think about the problem."

#### Code Architecture

**Main Orchestrator** (`main.py`, 452 lines):
- `BlogPostPipeline` class coordinates all stages
- Implements async pipeline with explicit stage transitions
- Manages resume capability through state checkpoint
- Handles user interaction for feedback collection

**Core Modules** (each in `module_name/core.py`):

1. **StyleExtractor** (188 lines)
   - Analyzes author's writing patterns
   - Extracts tone, vocabulary, sentence structure
   - Returns structured style profile

2. **BlogWriter** (240 lines)
   - Generates initial draft from brain dump
   - Revises based on feedback
   - Incorporates style profile throughout

3. **SourceReviewer** (216 lines)
   - Verifies draft matches brain dump content
   - Checks user feedback is addressed
   - Blocks advancement if accuracy issues found

4. **StyleReviewer** (varies)
   - Compares draft to author's existing writings
   - Ensures tone/voice consistency
   - Suggests improvements for authenticity

5. **UserFeedbackHandler** (varies)
   - Parses bracketed comments from markdown
   - Structures feedback for next iteration
   - Treats user input as valid source material

**State Management** (`state.py`, 215 lines):
- `PipelineState` dataclass tracks complete pipeline status
- `StateManager` handles persistence to JSON
- Enables interruption/resume at any point
- Saves draft iterations separately for user review

#### Workflow: Step by Step

1. **User provides**: 
   - Brain dump markdown (rough ideas)
   - Directory of existing writings (for style learning)
   - Optional: additional instructions

2. **System executes**:
   - Load & validate inputs
   - Extract style profile from writings
   - Generate initial draft (iteration 1)
   - Review for source accuracy
   - Review for style consistency
   - Present to user for feedback

3. **User reviews**:
   - Opens `draft_iter_N.md` in editor
   - Adds `[bracketed comments]` marking changes
   - Saves file (triggers tool to continue)
   - Chooses: `approve` (done), `done` (refine), or `skip` (another iteration)

4. **System refines**:
   - Reads user feedback
   - Returns draft to BlogWriter with feedback context
   - Re-runs source and style reviews
   - Repeats until approved or max iterations reached

5. **Final output**:
   - Slugified filename from blog title
   - Full markdown with all iterations preserved in session directory
   - State file allows resuming if interrupted

#### Resume Capability Implementation

The state management enables true interruption/resume:

```python
# StateManager tracks:
- stage: "initialized" → "style_extracted" → "draft_written" → ...
- iteration: counter for refinement cycles
- max_iterations: limit (default 10)
- style_profile: extracted from writings
- current_draft: latest version
- source_review: results with pass/fail
- style_review: results with suggestions
- user_feedback: all feedback collected
- iteration_history: debugging info

# On resume:
1. Load state from session JSON
2. Check current stage
3. Continue from that point
4. Previous context available to all modules
```

#### Dependencies & Configuration

**Required Libraries**:
- `pydantic-ai`: LLM integration
- `click`: CLI interface
- `pathlib`: File operations

**Environment**:
- `ANTHROPIC_API_KEY`: For Claude API access
- Works offline for file operations (only API calls require internet)

**File Structure**:
```
.data/blog_post_writer/
├── YYYYMMDD_HHMMSS/           # Session directory
│   ├── state.json             # Resumable state
│   ├── draft_iter_1.md        # First iteration
│   ├── draft_iter_2.md        # User edited, system revised
│   ├── draft_iter_3.md        # After second user feedback
│   └── slug-title.md          # Final approved post
```

#### Usage Pattern

**Command Line**:
```bash
# Initial run
make blog-write \
  IDEA=rough_idea.md \
  WRITINGS=my_posts/

# Resume interrupted
make blog-resume

# With custom instructions
make blog-write \
  IDEA=idea.md \
  WRITINGS=posts/ \
  INSTRUCTIONS="Remove company names, keep technical details"
```

**Programmatic**:
```python
from scenarios.blog_writer import BlogPostPipeline, StateManager

state_mgr = StateManager()
pipeline = BlogPostPipeline(state_mgr)

success = await pipeline.run(
    brain_dump_path=Path("idea.md"),
    writings_dir=Path("my_posts/"),
    output_path=Path("output.md"),
    additional_instructions="Keep it under 2000 words"
)
```

#### Key Design Patterns Used

1. **Pipeline Pattern**: Sequential stages with explicit transitions
2. **State Pattern**: Persistence enables resume/recovery
3. **Strategy Pattern**: Different reviewers with same interface
4. **Iterator Pattern**: Handle multiple file inputs (writings directory)
5. **Observer Pattern**: State changes trigger logging/checkpointing

#### Success Metrics

- **Functionality**: Generates readable, authentic-sounding blog posts
- **Style Matching**: Output matches author's voice (verified by StyleReviewer)
- **Accuracy**: Content matches brain dump (verified by SourceReviewer)
- **Usability**: Clear feedback loop with inline comments
- **Resilience**: Can resume from any stage without data loss

---

### 2.2 TIPS SYNTHESIZER

#### Purpose & Problem Statement

**The Problem**:
- Valuable tips scattered across multiple documents
- No coherent organization or structure
- Redundancy across similar tips
- Missing connections between related concepts

**The Solution**:
A multi-stage synthesis pipeline that extracts, organizes, and synthesizes tips into a cohesive guide.

#### Metacognitive Recipe

```
1. Extract tips from all markdown files
2. Create individual notes for each tip
3. Synthesize into a unified document
4. Review for completeness & coherence
5. Refine based on reviewer feedback
6. Iterate until quality passes
```

#### Architecture

**Code Structure**:
- Monolithic design: `synthesizer.py` contains main logic
- CLI interface: `cli.py` for command-line parsing
- User interaction: `user_feedback.py` for incorporating changes
- No heavy modularization (simpler than blog_writer)

**Pipeline Stages**:
1. File discovery (recursive `**/*.md` glob)
2. Tip extraction (AI identifies tips in markdown)
3. Note creation (individual files for each tip)
4. Synthesis (combines into coherent guide)
5. Review (checks quality metrics)
6. Refinement (AI improves based on feedback)

#### Key Features

- **Recursive file search**: Finds tips in nested directories
- **Incremental processing**: Saves after each stage
- **Quality gates**: Automated review prevents incomplete synthesis
- **Iteration support**: Up to 3 review-refine cycles by default
- **Resume capability**: Can continue from saved checkpoint

#### Input/Output

**Input**:
```
my_tips/
├── productivity_tips.md
├── debugging_tricks.md
├── workflow_improvements.md
└── nested/
    └── advanced_tips.md
```

**Output**:
```
.data/tips_synthesizer/YYYYMMDD_HHMMSS/
├── state.json           # Pipeline state
├── temp/                # Individual tip notes
│   ├── tip_1.json
│   ├── tip_2.json
│   └── ...
├── draft_v1.md          # Iteration 1
├── draft_v2.md          # Iteration 2 (if refined)
└── final_guide.md       # Final output (copied to specified location)
```

#### Configuration

```bash
# Basic
make tips-synthesizer INPUT=my_tips/ OUTPUT=guide.md

# Advanced
python -m scenarios.tips_synthesizer \
  --input-dir ./tips/ \
  --output-file ./guide.md \
  --max-iterations 5 \
  --verbose
```

#### Unique Characteristics

- **Simpler orchestration** than blog_writer (more straightforward flow)
- **Defensive parsing**: Handles AI response formatting robustly
- **Cost-aware**: Processing fits within token budgets
- **No external APIs**: Uses only Claude for synthesis
- **Suitable as learning example**: Good second scenario to study after blog_writer

---

### 2.3 ARTICLE ILLUSTRATOR

#### Purpose & Problem Statement

**The Problem**:
- Finding relevant images for technical articles is time-consuming
- Stock photos rarely match specific content
- Creating custom illustrations requires specialized skills
- Consistency across multiple images is hard to maintain

**The Solution**:
AI-powered pipeline that analyzes content, generates targeted prompts, and creates contextually relevant illustrations.

#### Metacognitive Recipe

```
1. Analyze article content to identify illustration opportunities
2. Generate detailed, contextually relevant image prompts
3. Create images using multiple AI APIs
4. Insert images at optimal positions in markdown
5. Provide alternatives for different styles/APIs
```

#### Architecture

**Modular Design** (4 core modules + orchestrator):

1. **ContentAnalyzer** (`content_analysis/`)
   - Parses markdown structure
   - Identifies sections needing visual support
   - Determines optimal illustration points

2. **PromptGenerator** (`prompt_generation/`)
   - Creates detailed image descriptions
   - Maintains style consistency
   - Incorporates technical accuracy

3. **ImageGenerator** (`image_generation/`)
   - Calls multiple APIs (GPT-Image-1, DALL-E-3, Imagen-4)
   - Handles API errors gracefully
   - Tracks costs and budgets

4. **MarkdownUpdater** (`markdown_update/`)
   - Inserts images with proper formatting
   - Maintains HTML img tags for responsive sizing
   - Preserves markdown readability

5. **State Management** (`state.py`)
   - Tracks completion status
   - Enables session resume
   - Stores all prompts and image metadata

#### Key Features

- **Multi-API support**: Generate with GPT-Image-1, DALL-E-3, or Imagen-4
- **Parallel generation**: Speed up processing by trying multiple APIs
- **Cost tracking**: Shows estimated costs before processing
- **Prompts-only mode**: Preview what will be generated without creating images
- **Style variations**: Apply consistent themes across all illustrations
- **Alternative images**: Keep options for each illustration (selectable via HTML comments)

#### Workflow

1. **Input**: Markdown article file
2. **Analysis**: System identifies 3-5 illustration points
3. **Generation**: Creates images via selected API(s)
4. **Review**: Previews placement and relevance
5. **Output**: Illustrated markdown with embedded images

#### Output Structure

```
.data/article_illustrator/article_name_timestamp/
├── illustrated_article.md       # Main output
├── images/
│   ├── illustration-1-gptimage.png
│   ├── illustration-1-imagen.png
│   ├── illustration-1-dalle.png
│   ├── illustration-2-gptimage.png
│   └── ...
├── prompts.json                 # All used prompts
└── .session_state.json          # Resume data
```

#### Configuration

```bash
# Basic
make illustrate INPUT=article.md

# With style
make illustrate INPUT=article.md STYLE="pirate meme style"

# Multiple APIs
make illustrate INPUT=article.md APIS="gptimage imagen dalle"

# Prompts-only preview
uv run python -m scenarios.article_illustrator article.md --prompts-only
```

#### Cost Model

**Typical costs** (2025):
- Content analysis (GPT-4o-mini): ~$0.01 per article
- Prompt generation (Claude Haiku): ~$0.01 per prompt
- GPT-Image-1: $0.04 per image
- DALL-E 3: $0.04 per image
- Imagen 4: $0.03-$0.04 per image

**Example**: 5 illustrations = ~$0.20-$0.25 total

#### Unique Characteristics

- **Most expensive** of the scenarios (image generation costs)
- **Highest API complexity** (coordinates multiple services)
- **Sophisticated state management** (handles long-running operations)
- **Visual output** (actually generates files)
- **Best for learning**: Multi-API patterns and cost management

---

### 2.4 TRANSCRIBE

#### Purpose & Problem Statement

**The Problem**:
- Valuable content locked in video/audio format
- Can't search or quote what was said
- Re-watching entire videos to find specific moments
- No written record for offline access

**The Solution**:
Pipeline that downloads audio, transcribes with Whisper API, formats for readability, and extracts insights.

#### Metacognitive Recipe

```
1. Download audio from YouTube or use local file
2. Extract/compress audio for API limits
3. Transcribe using Whisper (speech-to-text)
4. Format into readable paragraphs with timestamps
5. Generate summary and extract key quotes
6. Create searchable index of all transcripts
```

#### Architecture

**8-Module Design** (most complex scenario):

1. **VideoLoader** (`video_loader/`)
   - Downloads from YouTube using yt-dlp
   - Validates URL and checks availability
   - Handles authentication/paywall detection

2. **AudioExtractor** (`audio_extractor/`)
   - Extracts audio from video files
   - Compresses to fit API limits (25MB max)
   - Converts to optimal format (MP3)

3. **WhisperTranscriber** (`whisper_transcriber/`)
   - Calls OpenAI's Whisper API
   - Handles rate limiting and retries
   - Returns detailed timing information

4. **TranscriptFormatter** (`transcript_formatter/`)
   - Groups words into readable paragraphs
   - Adds clickable timestamps
   - Preserves speaker information if available

5. **SummaryGenerator** (`summary_generator/`)
   - AI-generated summary of content
   - Identifies main topics
   - Creates executive overview

6. **QuoteExtractor** (`quote_extractor/`)
   - Pulls most relevant quotes
   - Maintains exact wording and timing
   - Provides context around each quote

7. **InsightsGenerator** (`insights_generator/`)
   - Combines summary and quotes
   - Creates standalone insights document
   - Useful for quick reference

8. **IndexGenerator** (`index_generator/`)
   - Maintains index of all transcripts
   - Auto-updates when new transcripts added
   - Enables search across all content

**State Management** (`state.py`):
- Tracks which videos processed
- Enables batch resume
- Records timestamps and costs

**Storage Management** (`storage/`):
- Organizes files by domain/source
- Manages audio caching
- Preserves both user-facing and technical outputs

#### Workflow

1. **Provide**: YouTube URL or local audio file
2. **Download**: System fetches audio (cached for future runs)
3. **Transcribe**: Whisper converts audio to text
4. **Format**: Creates readable markdown with timestamps
5. **Analyze**: Generates summary and key quotes
6. **Save**: Outputs to organized directory structure

#### Output Structure

```
User-Facing Content (~/amplifier/transcripts/):
├── index.md                         # All transcripts index
└── video-id/
    ├── audio.mp3                    # Preserved audio file
    ├── transcript.md                # Readable transcript with timestamps
    └── insights.md                  # Summary and key quotes

Technical Artifacts (.data/transcripts/):
└── video-id/
    ├── transcript.json              # Structured data
    ├── transcript.vtt               # WebVTT subtitles
    └── transcript.srt               # SRT subtitles
```

#### Configuration

```bash
# Single video
python -m scenarios.transcribe "https://youtube.com/watch?v=..."

# Multiple sources (batch)
python -m scenarios.transcribe video1.mp4 "https://youtube.com/..." podcast.mp3

# Resume interrupted batch
python -m scenarios.transcribe --resume video1.mp4 video2.mp4

# Verbose progress
python -m scenarios.transcribe url --verbose
```

#### Cost Model

**OpenAI Whisper API**:
- $0.006 per minute of audio
- 60-minute video: ~$0.36
- Typically shown before processing

#### Unique Characteristics

- **Most modular** (8 separate, well-defined modules)
- **Batch processing** (handle multiple videos)
- **Longest pipelines** (several external API calls)
- **Dual output** (both user and technical formats)
- **Search-centric** (designed for discoverability)
- **Best for learning**: Large-scale orchestration patterns

#### Dependencies

**External tools** (must be installed):
- `yt-dlp`: YouTube downloading
- `ffmpeg`: Audio processing

**Python libraries**:
- `openai`: Whisper API access
- `pathlib`: File organization

---

### 2.5 WEB TO MD

#### Purpose & Problem Statement

**The Problem**:
- Want to save web content as markdown for offline access
- Paywalled content or authentication walls waste time
- Images hosted externally break without the site
- No standardized organization across sources

**The Solution**:
Pipeline that validates content, converts to markdown, downloads images locally, and organizes by domain.

#### Metacognitive Recipe

```
1. Fetch web pages with retry logic
2. Validate content (detect paywalls/authentication)
3. Convert HTML to clean markdown
4. Download and organize images locally
5. Enhance markdown with AI (if available)
6. Organize by domain for discoverability
7. Generate index of all saved pages
8. Support resume for interrupted sessions
```

#### Architecture

**8-Module Design** (most comprehensive):

1. **Fetcher** (`fetcher/`)
   - Downloads web pages via HTTP
   - Implements retry logic with backoff
   - Handles redirects and cookies

2. **Validator** (`validator/`)
   - Detects paywalled content
   - Identifies authentication walls
   - Validates minimum content length
   - Prevents saving teaser/preview content

3. **Converter** (`converter/`)
   - Converts HTML to markdown using markdownify
   - Preserves structure and formatting
   - Handles various HTML patterns

4. **ImageHandler** (`image_handler/`)
   - Downloads images referenced in HTML
   - Saves locally in domain directory
   - Updates references to use local paths
   - Handles various image formats

5. **Enhancer** (`enhancer/`)
   - Uses Claude Code SDK for AI improvements
   - Adds YAML frontmatter with metadata
   - Improves heading hierarchy
   - Cleans formatting issues
   - Graceful fallback if SDK unavailable

6. **Organizer** (`organizer/`)
   - Groups pages by domain
   - Creates domain subdirectories
   - Manages file naming
   - Tracks duplicates

7. **Indexer** (`indexer/`)
   - Creates searchable index of all content
   - Updates automatically on new saves
   - Links between related pages
   - Enables cross-domain search

8. **State Management** (`state.py`)
   - Tracks processed URLs
   - Records success/failure with reasons
   - Enables batch resume

#### Workflow

1. **Provide**: One or more URLs
2. **Validate**: Check for paywalls/authentication
3. **Fetch**: Download web page
4. **Convert**: Transform HTML to markdown
5. **Images**: Download and localize references
6. **Enhance**: Improve formatting (if SDK available)
7. **Organize**: Group by domain
8. **Index**: Update master index
9. **Resume**: Can continue if interrupted

#### Output Structure

```
sites/ (organized by domain)
├── blog.example.com/
│   ├── article-title.md
│   ├── another-post.md
│   └── images/
│       ├── img_a1b2c3d4.jpg
│       └── img_e5f6g7h8.png
├── news.example.com/
│   ├── story.md
│   └── images/
│       └── img_i9j0k1l2.gif
└── index.md                         # Auto-generated index

Technical:
.data/web_to_md/state.json           # Resume state
```

#### Configuration

**Integration with Amplifier**:
- Reads from `amplifier.config.paths`
- Uses centralized `.data/` directory
- Standalone mode if Amplifier unavailable

**Usage**:
```bash
# Single page
make web-to-md URL=https://example.com/article

# Multiple pages
make web-to-md URL=url1 URL2=url2

# Custom output
make web-to-md URL=https://example.com OUTPUT=./my-sites

# Resume
python -m web_to_md --url https://example.com/page1 --resume

# Verbose
python -m web_to_md --url https://example.com --verbose
```

#### Paywall Detection

**What it detects**:
- "Member-only" markers (Medium, Substack)
- Authentication prompts/redirects
- Subscription walls
- Content teasers (too-short content)

**Strategy**: Validates minimum content length and checks for paywall indicators

#### Unique Characteristics

- **Most defensive** (extensive error handling for web scenarios)
- **Most integrated** (works standalone AND with Amplifier)
- **Most polished** (includes separate pyproject.toml)
- **Best for learning**: Web scraping patterns, error handling, integration patterns

#### Dependencies

**Python packages**:
- `markdownify`: HTML to markdown
- `httpx`: HTTP client with retries
- `beautifulsoup4`: HTML parsing
- `pyyaml`: YAML handling
- `click`: CLI

**Optional**:
- `amplifier.ccsdk_toolkit`: For AI enhancement (graceful fallback)

---

## SECTION 3: CROSS-CUTTING PATTERNS & SHARED ARCHITECTURE

### 3.1 Consistent Patterns Across All Scenarios

Every scenario follows these proven patterns:

#### Pattern 1: Modular Design (Bricks & Studs)

Each scenario is composed of **self-contained modules**:
- One responsibility per module
- Clear input/output contracts (`__init__.py` exports)
- Can be understood and modified independently
- Designed for potential regeneration

**Example** (blog_writer):
```
blog_writer/ ─────────────────┐
style_extractor/ ─────────────┤─ Pipeline Orchestrator
source_reviewer/ ──────────────┤ (main.py + state.py)
style_reviewer/ ───────────────┤
user_feedback/ ────────────────┘
```

#### Pattern 2: State Persistence for Resume

All scenarios save state after every operation:

```python
class StateManager:
    def save(self) -> None:
        """Save current state to JSON file"""
        # Enables: interrupt → resume at same point
```

**Benefits**:
- User can Ctrl+C anytime without losing work
- Continuation is automatic
- Previous context available to all modules
- Debugging via state inspection

#### Pattern 3: Explicit Stage Transitions

Pipeline moves through defined stages:

```
initialized → extraction_complete → 
writing_done → review_passed → 
complete
```

**State file tracks current stage** - resume picks up from there.

#### Pattern 4: Async/Await for LLM Calls

All LLM operations are async:

```python
async def write_blog(self, ...) -> str:
    """Uses async to enable non-blocking API calls"""
```

**Enables**: 
- Timeout handling
- Retry logic with backoff
- Progress reporting during long operations

#### Pattern 5: Defensive Parsing of LLM Responses

LLMs don't always return perfectly formatted data:

```python
# From DISCOVERIES.md:
from amplifier.ccsdk_toolkit.defensive.file_io import parse_llm_json

# Handles: markdown blocks, extra text, malformed quotes
result = parse_llm_json(llm_response)
```

**Used in**: All scenarios that need structured JSON from Claude

#### Pattern 6: CLI Entry Points

All scenarios have consistent CLI interfaces:

```bash
# Pattern:
python -m scenarios.SCENARIO_NAME [OPTIONS]

# Examples:
python -m scenarios.blog_writer --idea idea.md --writings-dir posts/
python -m scenarios.tips_synthesizer --input-dir tips/ --output-file guide.md
python -m scenarios.article_illustrator article.md --style "pirate theme"
python -m scenarios.transcribe "https://youtube.com/watch?v=..."
python -m web_to_md --url https://example.com/page1 --output ./sites/
```

**Also support**:
- `make` commands for Amplifier integration
- Direct invocation via `__main__.py`
- Programmatic use via Python imports

#### Pattern 7: Test Data & Sample Inputs

Every scenario includes working example inputs:

```
scenarios/SCENARIO/tests/
├── sample_input.md
└── sample_data/
    ├── file1.md
    └── file2.md
```

**Enables**:
- Quick testing without prep work
- Learning by example
- Understanding expected formats

#### Pattern 8: Comprehensive README + HOW_TO_CREATE

Every scenario has:
- **README.md**: What it does, how to use it, troubleshooting
- **HOW_TO_CREATE_YOUR_OWN.md**: How this scenario was built, so you can create similar ones

**The HOW_TO documents** are crucial - they explain the **metacognitive recipe** that guided creation.

### 3.2 Shared Dependencies & Utilities

#### Amplifier Core Utilities (Used by All)

```python
from amplifier.ccsdk_toolkit import ClaudeSession, SessionOptions
from amplifier.ccsdk_toolkit.defensive.file_io import (
    read_json_with_retry,
    write_json_with_retry,
    parse_llm_json
)
from amplifier.utils.logger import get_logger
from amplifier.config.paths import (
    CONTENT_DIRS,
    DATA_DIR,
    CACHE_DIR
)
```

#### Defensive Patterns (From DISCOVERIES.md)

All scenarios implement patterns documented in DISCOVERIES.md:

1. **File I/O with Retries**: Handle OneDrive/cloud sync delays
2. **LLM Response Parsing**: Extract JSON from various formats
3. **Progressive Checkpointing**: Save after every operation

### 3.3 Error Handling Philosophy

**Consistent approach**:
1. Fail fast for configuration errors (missing files, API keys)
2. Retry transient errors (network timeouts, rate limits)
3. Continue gracefully on non-blocking errors
4. Preserve all work on catastrophic failure
5. Provide clear error messages with solutions

**Example** (from web_to_md):
```python
try:
    content = await fetcher.fetch(url)
except PaywallDetected:
    logger.warning(f"Paywall detected: {url}")
    # Continue to next URL, don't fail entire batch
except NetworkError as e:
    logger.error(f"Network error: {e}")
    # Will retry on next resume
```

---

## SECTION 4: BLOG WRITER EXEMPLAR - DETAILED ANALYSIS

### 4.1 Why Blog Writer is the Exemplar

**Blog Writer serves as the reference implementation** because it:

1. **Demonstrates core patterns**: State management, modular architecture, stage transitions
2. **Shows complexity progression**: Readable but non-trivial (1,300 lines)
3. **Embodies metacognitive recipe**: Clear thinking process driving architecture
4. **Includes all features**: Resume, iteration, feedback integration
5. **Solves real problem**: Actually useful for content creation
6. **Best documented**: Extensive README + HOW_TO guide
7. **Learning value**: Complexity is manageable (not overwhelming like transcribe)

### 4.2 Creation Story

From `blog_writer/HOW_TO_CREATE_YOUR_OWN.md`:

**What the creator actually did**:

1. **Described the goal** (natural language):
   > "Create me a tool that will take a brain dump I've done on a topic and write up a blog post in my style."

2. **Described the thinking process** (not code):
   > "First understand my style, then draft content, then review for accuracy, then review for style, then get my feedback and refine."

3. **Let Amplifier build it**:
   - Used specialized agents (zen-architect, modular-builder, bug-hunter)
   - Implemented all orchestration, state management, file I/O
   - Integrated with existing Amplifier utilities

4. **Iterated to refine**:
   - "User feedback is being flagged as not in source" → Fixed
   - "Draft files are getting overwritten" → Fixed
   - Total time: **one conversation session**

**Key insight**: The creator **never wrote a line of code**. They described what they wanted and how it should think.

### 4.3 How to Study Blog Writer as a Learner

**Step 1**: Read the README to understand what it does
**Step 2**: Read HOW_TO_CREATE_YOUR_OWN to understand the recipe
**Step 3**: Try running it with sample inputs (in tests/)
**Step 4**: Review the code in this order:
- `state.py` - Understand state persistence pattern
- `main.py` - Understand orchestration/pipeline flow
- `blog_writer/core.py` - Understand module structure
- Other `*/core.py` files - See similar module patterns

**Step 5**: Consider: How would YOU describe a similar tool for a different problem?

### 4.4 Code Structure Analysis

**LOC Distribution** (1,311 total):

| Component | Lines | Purpose |
|-----------|-------|---------|
| main.py | 452 | Pipeline orchestration, CLI, user interaction |
| state.py | 215 | State persistence, lifecycle management |
| blog_writer/core.py | 240 | Content generation engine |
| source_reviewer/core.py | 216 | Accuracy validation |
| style_extractor/core.py | 188 | Voice/tone analysis |

**Principles**:
- Each module roughly 150-250 lines (manageable size)
- Orchestrator larger because it handles coordination
- State management separate for clarity
- Each module has single responsibility

---

## SECTION 5: MATURITY MODEL - SCENARIOS' POSITION

### 5.1 Amplifier Three-Tier System

```
┌─────────────────────────────────────────┐
│  amplifier/ (PRODUCTION CORE)           │  ← Core infrastructure
│  - CLIkit, SDK, patterns               │  ← Stable, well-tested
│  - Used BY other tools                 │  ← High reliability requirement
└─────────────────────────────────────────┘
              ↑ depends on
┌─────────────────────────────────────────┐
│  scenarios/ (PRODUCTION EXEMPLARS)      │  ← CURRENT POSITION
│  - Real tools solving actual problems   │  ← Experimental but usable
│  - Learning templates                   │  ← Shows what's possible
│  - Ready to use NOW                     │  ← Works, but may iterate
└─────────────────────────────────────────┘
              ↑ uses patterns from
┌─────────────────────────────────────────┐
│  ai_working/ (EXPLORATION SANDBOX)      │  ← Design & research
│  - Design decisions                     │  ← Thinking & planning
│  - Explorations & prototypes            │  ← Not yet stable
│  - Ideas being tested                   │  ← May be abandoned
└─────────────────────────────────────────┘
```

### 5.2 Scenarios Are NOT...

- **Core infrastructure** (that's `amplifier/`)
- **Experimental toys** (that's `ai_working/`)
- **Production-hardened tools** (ready to use but may iterate)
- **Exhaustively documented** (intentionally leave room for learning)

### 5.3 Scenarios ARE...

- **Real working tools** you can use today
- **Learning exemplars** showing Amplifier's potential
- **Modular reference implementations** you can study
- **Starting points** for building your own tools
- **Production-ready experimental software** (works, may improve)

### 5.4 Status of Each Scenario

| Scenario | Status | Maturity | Can Use Now? | Learn From? |
|----------|--------|----------|-------------|------------|
| blog_writer | Ready | Production Experimental | Yes | YES - exemplar |
| tips_synthesizer | Ready | Production Experimental | Yes | Yes - simpler |
| article_illustrator | Ready | Production Experimental | Yes | Yes - APIs |
| transcribe | Ready | Production Experimental | Yes | Yes - complex |
| web_to_md | Ready | Production Experimental | Yes | Yes - error handling |

**"Production Experimental"** means:
- Code works and is tested
- Implements solid patterns
- May evolve based on usage
- Not guaranteed to never change
- Safe to build on top of

---

## SECTION 6: WORKFLOW & USAGE PATTERNS

### 6.1 Using a Scenario Tool

**Five-step workflow**:

1. **Understand the problem**: Read README.md
2. **Prepare inputs**: Gather files/data it needs
3. **Run the tool**: `make scenario-name` or `python -m scenarios.scenario_name`
4. **Review outputs**: Check generated files
5. **Iterate if needed**: Provide feedback, tool refines (for blog_writer, tips_synthesizer)

### 6.2 Creating Your Own Scenario Tool

**Four-step process**:

1. **Identify the problem**: "What would make my work easier?"
2. **Describe the thinking process**: "It should do A, then B, then C"
3. **Start a conversation**: Use `/ultrathink-task` with Amplifier
4. **Share it back**: Document what you learned

**Reference**:
- Use `blog_writer/HOW_TO_CREATE_YOUR_OWN.md` as your template
- Study the metacognitive recipe
- Describe THINKING, not IMPLEMENTATION

### 6.3 Integration Points

**With Amplifier**:
- All scenarios use Amplifier utilities
- State saves to centralized `.data/` directory
- Config reads from `amplifier.config.paths`
- Can be extended with Amplifier CLI commands

**Standalone**:
- Each scenario can run independently
- Uses local directories if Amplifier unavailable
- Graceful degradation pattern (web_to_md example)

---

## SECTION 7: KEY INSIGHTS & LEARNINGS

### 7.1 What Makes These Tools Work

**Factor 1: Clear Metacognitive Recipe**
- Success requires explicit "how to think about this" design
- Not "how to code it" but "how to approach it"
- Recipe guides both AI AND orchestration code

**Factor 2: State Persistence**
- Resume capability enabled by saving state after EVERY operation
- Cloudinary-safe patterns from DISCOVERIES.md
- Users don't lose work on interruption

**Factor 3: Modular Architecture**
- Each module ~150-250 lines (manageable)
- Clear contracts via `__init__.py`
- Can understand piece-by-piece

**Factor 4: User Feedback Integration**
- Not "generate and done" but "generate, user feedback, refine"
- Bracketed comments are simple feedback mechanism
- Iteration cycles improve quality

**Factor 5: Defensive Programming**
- Expect LLM responses to be messy
- Retry failed operations
- Preserve all work on failure
- Clear error messages

### 7.2 Anti-Patterns Avoided

**What Doesn't Work**:
- Monolithic 5000-line files (unmaintainable)
- Implicit state transitions (confusing)
- Lost work on failure (frustrating)
- Unclear error messages (debugging nightmare)
- Over-engineering for hypothetical futures (complexity)

**These scenarios avoid all of these**.

### 7.3 The "Describe & Regenerate" Philosophy

**Traditional approach**:
```
Code → Edit line 42 → Edit line 105 → Debug → Ship
```

**Amplifier approach**:
```
Describe recipe → Amplifier generates → Describe what's wrong → 
Amplifier regenerates → Test → Ship
```

**Key difference**: Regenerate entire modules rather than edit lines.

Scenarios embody this by having clear specs (`README.md` + `state.py`) that enable full regeneration if needed.

---

## SECTION 8: FILE REFERENCE GUIDE

### 8.1 Essential Reading (In Order)

1. **/scenarios/README.md** - Master overview, philosophy, all scenarios
2. **/scenarios/blog_writer/README.md** - How to use the exemplar
3. **/scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md** - How it was built
4. **/scenarios/blog_writer/state.py** - State persistence pattern
5. **/scenarios/blog_writer/main.py** - Orchestration pattern

### 8.2 Architecture Documentation

- `CLAUDE.md` - Project instructions (includes scenario guidance)
- `AGENTS.md` - AI assistant guidance
- `DISCOVERIES.md` - Lessons learned (defensive patterns)
- `ai_context/IMPLEMENTATION_PHILOSOPHY.md` - Design philosophy
- `ai_context/MODULAR_DESIGN_PHILOSOPHY.md` - Modular approach

### 8.3 By Learning Goal

**Want to understand state persistence?**
- → `blog_writer/state.py` (215 lines, well-commented)

**Want to understand pipeline orchestration?**
- → `blog_writer/main.py` (452 lines, shows all stages)

**Want to understand modular architecture?**
- → Compare `blog_writer/style_extractor/core.py`, `blog_writer/blog_writer/core.py`, etc.

**Want to understand error handling?**
- → `web_to_md/validator/core.py` (paywall detection)

**Want to understand batch processing?**
- → `transcribe/` (8 modules coordinating)

**Want to understand multi-API coordination?**
- → `article_illustrator/image_generation/clients.py`

---

## SECTION 9: COMMON OPERATIONS

### 9.1 Running a Scenario

```bash
# Blog Writer
make blog-write IDEA=idea.md WRITINGS=posts/
make blog-resume

# Tips Synthesizer
make tips-synthesizer INPUT=tips/ OUTPUT=guide.md

# Article Illustrator
make illustrate INPUT=article.md
make illustrate INPUT=article.md STYLE="pirate theme"

# Transcribe
python -m scenarios.transcribe "https://youtube.com/watch?v=..."
python -m scenarios.transcribe --resume

# Web to MD
make web-to-md URL=https://example.com
python -m web_to_md --url https://example.com --resume
```

### 9.2 Monitoring Progress

**All scenarios log progress**:
```
✓ Stage: style_extracted
✓ Iteration: 2/10
✓ Draft saved to: .data/blog_post_writer/..../draft_iter_2.md
```

**Check state files**:
```bash
cat .data/blog_post_writer/TIMESTAMP/state.json | jq
```

### 9.3 Troubleshooting

**Standard diagnosis**:
1. Check logs for explicit error message
2. Look at `.data/` state files for what completed
3. Verify input files exist and are readable
4. Check API keys in `.env`
5. Try again - transient errors may self-correct

**Resume interrupted run**:
```bash
# Blog writer
make blog-resume

# Tips synthesizer
make tips-synthesizer INPUT=tips/ OUTPUT=guide.md RESUME=true

# Others
python -m scenarios.SCENARIO_NAME --resume
```

---

## SECTION 10: CREATING YOUR OWN SCENARIO

### 10.1 The Recipe-First Approach

**Bad approach**:
> "I'll create a tool that uses GPT-4 with a vector database and Redis caching..."

**Good approach**:
> "I'll create a tool that:
> 1. First understands the user's needs
> 2. Then searches related documents
> 3. Then synthesizes an answer
> 4. Then gets user feedback
> 5. Then refines if needed"

The second is a **metacognitive recipe** - it describes THINKING, not IMPLEMENTATION.

### 10.2 Idea-to-Scenario Journey

**Step 1**: Identify a real problem
- Something that takes your time
- Something you wish was automated
- Something with clear input/output

**Step 2**: Describe the recipe
- "It should first do X" (LLM call? file processing? research?)
- "Then do Y" (validation? iteration? refinement?)
- "Finally do Z" (output? presentation? integration?)

**Step 3**: Get Amplifier to build it
```
/ultrathink-task Create me a tool that [GOAL]. 
It should think through the problem by: [RECIPE]
```

**Step 4**: Test & iterate
- Try with real data
- Describe what's wrong
- Amplifier refines

**Step 5**: Share it back
- Document your recipe
- Add example inputs
- Write HOW_TO for others

### 10.3 Template for New Scenarios

```
my_scenario/
├── README.md                    # What it does, how to use it
├── HOW_TO_CREATE_YOUR_OWN.md   # The recipe & how you made it
├── __init__.py
├── __main__.py                  # CLI entry point
├── main.py                      # Orchestrator
├── state.py                     # State persistence
├── module_1/                    # Each module has one responsibility
│   ├── __init__.py
│   └── core.py
├── module_2/
│   ├── __init__.py
│   └── core.py
└── tests/
    ├── sample_input.md
    └── sample_data/
```

**Key principle**: Each `module_*/core.py` is ~150-250 lines with clear responsibilities.

---

## SECTION 11: SUMMARY & CONCLUSIONS

### 11.1 What We Learned

**The Scenarios system demonstrates**:

1. **Minimal input, maximum leverage**
   - Describe what you want and how to think about it
   - Amplifier builds the full implementation
   - No boilerplate, no framework understanding needed

2. **Patterns enable complexity**
   - State persistence makes resume trivial
   - Modular design makes understanding easy
   - Clear recipes make thinking explicit

3. **Real tools, real problems**
   - These aren't demos or toys
   - They solve actual, pressing problems
   - People use them for real work

4. **Learning by example**
   - Each scenario teaches different patterns
   - Blog Writer: Orchestration & feedback loops
   - Tips Synthesizer: Simpler approach
   - Article Illustrator: Multi-API coordination
   - Transcribe: Large-scale batch processing
   - Web to MD: Defensive programming & error handling

### 11.2 Next Steps for Users

**If you want to USE these tools**:
1. Pick one that solves your problem
2. Follow the Quick Start in its README
3. Run with example data
4. Adapt for your content

**If you want to LEARN from these tools**:
1. Read blog_writer/HOW_TO_CREATE_YOUR_OWN.md
2. Study blog_writer code in order: state.py → main.py → core modules
3. Try running with test data
4. Modify one module and see what breaks

**If you want to CREATE your own tool**:
1. Describe your problem
2. Describe your thinking recipe (not code)
3. Use `/ultrathink-task` with Amplifier
4. Test and iterate
5. Share your creation

### 11.3 The Bigger Picture

Scenarios embody a **fundamental shift** in how we build software:

**From**: "Learn programming → Build tools → Document them"
**To**: "Describe what you want → AI builds it → Document the thinking"

This is enabled by Amplifier's patterns, defensive utilities, and integration of LLM capabilities with traditional software architecture.

The scenarios prove that **you don't need to be a programmer to create useful AI-powered tools** - you need to be able to describe:
- What problem you're solving
- How a human would think through it
- What inputs and outputs you expect

Everything else can be generated.

---

## APPENDIX A: QUICK REFERENCE

### CLI Commands Summary

```bash
# Blog Writer
make blog-write IDEA=path WRITINGS=path
make blog-resume

# Tips Synthesizer  
make tips-synthesizer INPUT=path OUTPUT=path

# Article Illustrator
make illustrate INPUT=path
make illustrate INPUT=path STYLE="style description"

# Transcribe
python -m scenarios.transcribe URL_or_FILE
python -m scenarios.transcribe --resume

# Web to MD
make web-to-md URL=url
python -m web_to_md --url url --resume
```

### File Locations

**User content**:
- `~amplifier/transcripts/` - Transcription output
- `sites/` - Web to MD output
- `.data/*/` - Tool working directories

**Configuration**:
- `.env` - API keys
- `amplifier.config.paths` - Amplifier paths
- `pyproject.toml` - Python dependencies

### Key Files to Study

| Goal | File |
|------|------|
| Understand state persistence | `blog_writer/state.py` |
| Understand orchestration | `blog_writer/main.py` |
| Understand modules | `blog_writer/blog_writer/core.py` |
| Understand error handling | `web_to_md/validator/core.py` |
| Understand the recipe | `blog_writer/HOW_TO_CREATE_YOUR_OWN.md` |

---

## APPENDIX B: METRICS & STATISTICS

### Code Metrics

| Scenario | Modules | LOC | Complexity | Learning Difficulty |
|----------|---------|-----|-----------|---------------------|
| blog_writer | 5+orch | 1,300 | Medium | Easy-Medium |
| tips_synthesizer | Mono | 500 | Low | Easy |
| article_illustrator | 4+orch | 1,500 | High | Medium |
| transcribe | 8+orch | 2,000+ | Very High | Hard |
| web_to_md | 8+orch | 1,800+ | High | Medium-Hard |

### Feature Comparison

| Feature | blog | tips | article | transcribe | web |
|---------|------|------|---------|-----------|-----|
| State persistence | Yes | Yes | Yes | Yes | Yes |
| Resume capability | Yes | Yes | Yes | Yes | Yes |
| Batch processing | No | Yes | Yes | Yes | Yes |
| User feedback loop | Yes | Yes | No | No | No |
| External APIs | Claude | Claude | Multiple | Whisper | Multiple |
| Documentation | Excellent | Good | Good | Good | Good |

---

**END OF COMPREHENSIVE SCENARIOS DOCUMENTATION**

*This report represents a complete analysis of Amplifier's scenarios system as of 2025-11-06. The system is production-ready and recommended for immediate use and learning.*
