# Tips Synthesizer: Transform Scattered Tips into Cohesive Guides

**Turn your collection of tips and tricks into a well-organized, comprehensive guide.**

## The Problem

You have valuable tips scattered across multiple documents, but:
- **Information is fragmented** - Tips are spread across various files and contexts
- **No coherent structure** - Related tips aren't grouped or connected
- **Redundancy abounds** - Similar tips appear in different forms
- **Missing transitions** - Individual tips don't flow into a narrative
- **Quality varies** - Some tips are detailed, others are mere snippets

## The Solution

Tips Synthesizer is a multi-stage AI pipeline that:

1. **Extracts tips systematically** - Identifies and pulls tips from all your markdown files
2. **Categorizes intelligently** - Groups related tips by theme and context
3. **Synthesizes cohesively** - Creates a unified document with logical flow
4. **Reviews for quality** - Ensures completeness, accuracy, and clarity
5. **Refines iteratively** - Improves based on automated reviewer feedback

**The result**: A polished, comprehensive guide that transforms scattered knowledge into actionable wisdom.

## Quick Start

**Prerequisites**: Complete the [Amplifier setup instructions](../../README.md#-step-by-step-setup) first.

### Basic Usage

```bash
make tips-synthesizer \
  INPUT=path/to/tips/directory/ \
  OUTPUT=synthesized_tips.md
```

The tool will:
1. Scan all markdown files in the directory
2. Extract individual tips from each file
3. Synthesize them into a cohesive document
4. Review and refine through multiple iterations
5. Save the polished guide

### Your First Synthesis

1. **Gather your tips** - Collect markdown files with tips in a directory:

```
my_tips/
├── productivity_tips.md
├── debugging_tricks.md
├── workflow_improvements.md
└── tool_recommendations.md
```

2. **Run the synthesizer**:

```bash
make tips-synthesizer \
  INPUT=my_tips/ \
  OUTPUT=ultimate_guide.md \
  VERBOSE=true
```

3. **Watch the pipeline work**:
   - Stage 1: Extracts tips from each markdown file
   - Stage 2: Creates individual note files for organization
   - Stage 3: Synthesizes all tips into a unified document
   - Stage 4: Reviews for completeness, coherence, and quality
   - Stage 5: Refines based on automated feedback (up to 3 iterations)

4. **Get your polished guide** - The final document will have:
   - Logical organization by category
   - Smooth transitions between sections
   - Consistent tone and formatting
   - All tips preserved but redundancy removed
   - Professional structure ready to share

## Usage Examples

### Basic: Simple Synthesis

```bash
make tips-synthesizer \
  INPUT=scattered_tips/ \
  OUTPUT=organized_guide.md
```

**What happens**:
- Extracts all tips from markdown files
- Groups them by detected categories
- Creates a well-structured guide
- Reviews for quality and coherence
- Outputs polished documentation

### Advanced: Resume Interrupted Session

```bash
make tips-synthesizer \
  INPUT=scattered_tips/ \
  OUTPUT=organized_guide.md \
  RESUME=true
```

**What happens**:
- Finds previous session state
- Continues from last checkpoint
- Preserves all extracted tips
- Completes remaining stages
- No work is repeated

### Control Review Iterations

```bash
python -m scenarios.tips_synthesizer \
  --input-dir ./tips/ \
  --output-file ./guide.md \
  --max-iterations 5 \
  --verbose
```

**What happens**:
- Allows up to 5 review-refine cycles
- Each iteration improves quality
- Stops when document passes review
- Or after maximum iterations reached

### Preview Before Processing

```bash
make tips-synthesizer \
  INPUT=my_tips/ \
  OUTPUT=guide.md \
  --dry-run
```

**What happens**:
- Shows which files would be processed
- Displays the pipeline stages
- No actual processing occurs
- Helps verify input before running

## How It Works

### The Pipeline

```
Markdown Files with Tips
         ↓
   [Extract Tips] ──────→ Individual tip records
         ↓
  [Create Notes] ───────→ Categorized note files
         ↓
  [Synthesize] ─────────→ Initial unified document
         ↓
   [Review] ────────────→ Quality assessment
         ↓
   [Refine] ────────────→ Improved version (iterate)
         ↓
    Final Guide
```

### Key Components

- **Tips Extractor**: Identifies and extracts individual tips from markdown content
- **Note Creator**: Stores each tip as a structured note with metadata
- **Document Synthesizer**: Combines all tips into a cohesive narrative
- **Quality Reviewer**: Evaluates completeness, coherence, and clarity
- **Refinement Writer**: Improves document based on review feedback
- **State Manager**: Saves progress after every operation (interrupt-safe)

### Why It Works

**Code handles the structure**:
- File scanning and processing
- State management and checkpointing
- Pipeline orchestration
- Error recovery and retries

**AI handles the intelligence**:
- Understanding tip content and context
- Categorizing and organizing
- Creating coherent narratives
- Quality assessment and improvement

This separation ensures reliability (code manages flow) and quality (AI handles content).

## Configuration

### Command-Line Options

```bash
# Required
--input-dir PATH        # Directory with markdown files
--output-file PATH      # Output file for synthesized guide

# Optional
--temp-dir PATH         # Custom temp directory
--resume                # Resume from saved state
--max-iterations N      # Max review cycles (default: 3)
--verbose              # Show detailed progress
--dry-run              # Preview without processing
```

### Session Data

All working files are saved to `.data/tips_synthesizer/<session>/`:
- `state.json` - Pipeline state for resume
- `temp/*.json` - Individual tip notes
- `draft_v*.md` - Each iteration's draft
- Final output saved to your specified path

## Troubleshooting

### "Need at least 2 markdown files"

**Problem**: Not enough input files for synthesis.

**Solution**: Ensure your input directory contains at least 2 `.md` files with tips. The tool uses recursive search (`**/*.md`), so subdirectories are included.

### "Could not parse review response"

**Problem**: The AI reviewer's response wasn't properly formatted.

**Solution**: The tool handles this gracefully with defensive parsing and continues. Check verbose output for details.

### "Maximum iterations reached"

**Problem**: Document didn't pass review within iteration limit.

**Solution**: The current best version is saved. You can:
- Review manually and edit if needed
- Increase `--max-iterations` for more refinement cycles
- Check the review history in session data to see what feedback was given

### Session interrupted

**Problem**: Process was stopped before completion (Ctrl+C or crash).

**Solution**: Use `RESUME=true` to continue from the last checkpoint. All progress is preserved, and no work is repeated.

### "API key not found"

**Problem**: The Claude API key isn't configured.

**Solution**: Follow the [Amplifier setup instructions](../../README.md#-step-by-step-setup) to configure your API key.

## Learn More

- **[HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md)** - Create your own tool like this
- **[Amplifier](https://github.com/microsoft/amplifier)** - The framework that powers these tools
- **[Blog Writer](../blog_writer/)** - Similar pattern for blog post creation
- **[Scenario Tools](../)** - More tools like this one

## What's Next?

This tool demonstrates what's possible when you describe a thinking process to Amplifier:

1. **Use it** - Synthesize your scattered tips into comprehensive guides
2. **Learn from it** - See [HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md) for how to create your own tools
3. **Build your own** - Describe your goal and thinking process to Amplifier
4. **Share back** - Let others learn from what you create!

---

**Built with minimal input using Amplifier** - The entire tool came from describing the goal and thinking process in one conversation. See [HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md) for details.
