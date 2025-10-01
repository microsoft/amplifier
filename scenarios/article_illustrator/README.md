# Article Illustrator: AI-Powered Article Imagery

**Automatically generate contextually relevant illustrations for your markdown articles.**

## The Problem

You've written a great article, but:
- **Finding images takes forever** - Searching stock photos or creating custom illustrations is time-consuming
- **Generic images don't fit** - Stock photos rarely match your specific content
- **Consistency is hard** - Maintaining visual style across multiple illustrations requires effort
- **Quality varies** - Hand-picking images leads to inconsistent quality and relevance

## The Solution

Article Illustrator is a multi-stage AI pipeline that:

1. **Understands your content** - Analyzes markdown structure to identify key concepts
2. **Creates targeted prompts** - Generates contextually relevant image descriptions
3. **Generates images** - Uses multiple AI image generation APIs for best results
4. **Integrates seamlessly** - Inserts images at optimal positions in your article

**The result**: Professional illustrations that enhance your content, generated in minutes.

## Quick Start

**Prerequisites**: Complete the [Amplifier setup instructions](../../README.md#-step-by-step-setup) first.

### Basic Usage

```bash
# Via Makefile (recommended) - creates timestamped output directory
make illustrate INPUT=path/to/article.md

# Direct invocation
uv run python -m scenarios.article_illustrator path/to/article.md
```

**Output location**: By default, creates a timestamped directory in `.data/article_illustrator/{article_name}_{timestamp}/` to keep sessions organized and prevent accidental overwrites.

The tool will:
1. Analyze your article for illustration opportunities
2. Generate targeted image prompts
3. Create images using GPT-Image-1 (default)
4. Insert images at optimal positions
5. Save the illustrated version with all images in the output directory

### Your First Illustrated Article

1. **Prepare your article** - Any markdown file will work:

```markdown
# My Technical Article

Explaining complex concepts...

## Key Architecture

The system has three main components...

## Implementation Details

Here's how it works in practice...
```

2. **Run the illustrator**:

```bash
make illustrate INPUT=my_article.md
```

3. **Review the output** - Find your illustrated article in the output directory with:
   - Generated images in `images/` folder
   - Updated markdown with embedded images
   - Prompts saved in `prompts.json`

## Usage Examples

### Basic: Simple Article

```bash
make illustrate INPUT=article.md
```

**What happens**:
- Identifies key sections needing visual support
- Generates contextually relevant image prompts
- Creates images using GPT-Image-1
- Inserts at optimal positions with proper sizing

### Style Variations: Themed Illustrations

```bash
make illustrate \
  INPUT=article.md \
  STYLE="pirate meme style with treasure maps and parrots"
```

**What happens**:
- Same analysis and placement
- Prompts adapted to pirate theme
- Images generated with consistent style
- Creates fun, themed version of your article

**More style examples**:
```bash
# Minimalist technical diagrams
STYLE="minimalist black and white line art"

# Retro 80s aesthetic
STYLE="retro 80s synthwave with neon colors and grid patterns"

# Watercolor illustrations
STYLE="soft watercolor technical diagrams"
```

### Advanced: Multiple APIs for Comparison

```bash
make illustrate \
  INPUT=article.md \
  APIS="gptimage imagen dalle"
```

**What happens**:
- Generates images using all three APIs
- Saves alternatives as HTML comments
- You can swap between versions easily
- Compare quality and style across APIs

### Prompts-Only Mode: Preview Before Generating

```bash
uv run python -m scenarios.article_illustrator article.md --prompts-only
```

**What happens**:
- Analyzes content and identifies illustration points
- Generates detailed image prompts
- Saves prompts to JSON (no images generated)
- Preview what will be created before spending money

### Output Control & Session Management

**Custom output location:**
```bash
# Specify exact output directory
make illustrate INPUT=article.md OUTPUT=custom/output/path/
```

**Session resumption** (for expensive interrupted operations):
```bash
# Resume an interrupted session
make illustrate INPUT=article.md OUTPUT=path/to/existing/session/ RESUME=true
```

**What the tool checks when resuming:**
- Article path must match
- Style parameters must match (if specified)
- Warns you if parameters don't match and asks for confirmation

**Session isolation by default:**
- Each run creates a new timestamped directory (e.g., `.data/article_illustrator/my_article_20251001_153653/`)
- Sessions organized in centralized `.data/article_illustrator/` directory
- Prevents accidental overwrites when experimenting with different styles/APIs
- Explicit OUTPUT required to resume or reuse a directory
- Old sessions preserved for comparison

**Example workflow:**
```bash
# First run - creates .data/article_illustrator/article_20251001_150000/
make illustrate INPUT=article.md STYLE="minimalist"

# Second run with different style - creates .data/article_illustrator/article_20251001_150230/
make illustrate INPUT=article.md STYLE="pirate theme"

# Resume first session if interrupted
make illustrate INPUT=article.md OUTPUT=.data/article_illustrator/article_20251001_150000/ RESUME=true
```

## How It Works

### The Pipeline

```
Article Input
     ↓
[Content Analysis] ────→ Identify illustration opportunities
     ↓
[Prompt Generation] ───→ Create contextual image prompts
     ↓
[Image Generation] ────→ Generate with multiple APIs
     ↓
[Markdown Update] ─────→ Insert images at optimal positions
     ↓
Illustrated Article
```

### The Metacognitive Recipe

This tool embodies a structured thinking process:

1. **Understand** - Analyze article structure and identify key concepts that need visual support
2. **Identify** - Find sections where images would add the most value
3. **Create** - Generate detailed, contextually relevant prompts for each illustration
4. **Execute** - Use the best available API to create high-quality images
5. **Integrate** - Insert images at positions that enhance comprehension and flow

This recipe guides the tool through intelligent decision-making at each stage.

### Key Components

- **Content Analyzer**: Uses LLM to understand article structure and identify illustration opportunities
- **Prompt Generator**: Creates detailed, contextually relevant image descriptions
- **Image Generator**: Orchestrates multiple APIs (GPT-Image-1, Imagen-4, DALL-E-3)
- **Markdown Updater**: Intelligently inserts images with proper formatting
- **State Manager**: Saves progress after every step (interrupt and resume anytime)

### Why It Works

**Code handles the structure**:
- Pipeline orchestration and flow control
- State management and checkpointing
- File I/O and error handling
- API coordination and retry logic

**AI handles the intelligence**:
- Understanding article content and structure
- Identifying where images add value
- Creating contextually relevant prompts
- Generating creative, appropriate imagery

This separation means the tool is both reliable (code manages the flow) and creative (AI handles the content).

## Configuration

### Command-Line Options

```bash
# Required
INPUT=path/to/article.md         # Your markdown article

# Optional
OUTPUT=path/to/output/           # Custom output directory (default: timestamped)
STYLE="description"              # Style theme for illustrations
APIS="api1 api2"                # Space-separated API list
RESUME=true                      # Resume existing session (requires OUTPUT)

# Via direct invocation
python -m scenarios.article_illustrator article.md \
  --output-dir custom/path/ \
  --style "minimalist line art" \
  --apis gptimage --apis imagen \
  --max-images 3 \
  --cost-limit 5.00 \
  --resume \
  --prompts-only
```

**Important notes:**
- If OUTPUT not specified, creates `.data/article_illustrator/{article_name}_{timestamp}/`
- RESUME flag requires OUTPUT to be specified (tells tool which session to resume)
- Without RESUME, tool creates new session even if OUTPUT directory has existing session

### API Configuration

Set environment variables in `.env` file:

```bash
# OpenAI (for content analysis, GPT-Image-1, and DALL-E 3)
OPENAI_API_KEY=your_openai_api_key

# Google (for Imagen 4 via Gemini API)
GOOGLE_API_KEY=your_google_api_key
```

### Session Data

All working files are saved to `.data/article_illustrator/<timestamp>/`:
- `.session_state.json` - Pipeline state for resume
- `images/` - Generated images
- `prompts.json` - All generated prompts
- `illustrated_article.md` - Final output

## Output Structure

```
output_dir/
├── illustrated_article.md       # Updated article with images
├── images/                       # Generated images
│   ├── illustration-1-gptimage.png
│   ├── illustration-1-imagen.png
│   └── illustration-1-dalle.png
├── prompts.json                 # All generated prompts
└── .session_state.json          # Resumable session data
```

### Markdown Format

Generated markdown uses HTML img tags for responsive sizing:

```html
<img src="./images/illustration-1-gptimage.png" alt="Section Title" width="50%">

<!-- ALTERNATIVES
<img src="./images/illustration-1-imagen.png" alt="imagen version" width="50%">
<img src="./images/illustration-1-dalle.png" alt="dalle version" width="50%">

To use an alternative, replace the main image above.
Generated from: illustration-1
-->
```

Images render at 50% width for optimal readability.

## Cost Management

- Estimated costs tracked per image
- Running total maintained in session
- Cost limit enforced if specified
- Summary displayed at completion

**Typical costs (2025 pricing)**:
- Content analysis (GPT-4o-mini): ~$0.01 per article
- Prompt generation (Claude Haiku): ~$0.01 per prompt
- GPT-Image-1: $0.04 per image (1024x1024, auto quality)
- DALL-E 3: $0.04 per image (1024x1024, standard quality)
- Imagen 4: $0.03-$0.04 per image

**Example**: Generating 5 illustrations costs approximately **$0.20-$0.25 total**.

## Troubleshooting

### "No illustration points found"

**Problem**: Article too short or lacks visual concepts.

**Solution**: Ensure article has multiple sections with technical concepts, architecture, or processes that benefit from visualization.

### "API key not found"

**Problem**: Environment variables not configured.

**Solution**: Create `.env` file in project root with required API keys.

### Session doesn't resume

**Problem**: Session state file not found or corrupted.

**Solution**: Use `--resume` flag and ensure output directory is correct. Start fresh without flag if needed.

### Images not loading in markdown

**Problem**: Relative paths incorrect.

**Solution**: Open illustrated markdown from output directory or adjust paths based on your markdown renderer.

## Learn More

- **[HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md)** - Create your own scenario tool
- **[Amplifier](https://github.com/microsoft/amplifier)** - The framework powering these tools
- **[Scenario Tools](../)** - More tools like this one

## What's Next?

This tool demonstrates what's possible when you describe a thinking process to Amplifier:

1. **Use it** - Generate illustrations for your articles
2. **Experiment** - Try different styles and APIs
3. **Learn from it** - See [HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md)
4. **Build your own** - Create tools that match your workflow

---

**Built with minimal input using Amplifier** - Describe the thinking process, Amplifier handles the implementation. See [HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md) for how this was created.
