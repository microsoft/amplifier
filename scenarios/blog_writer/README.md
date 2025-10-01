# Blog Writer: Transform Ideas Into Polished Posts

**Turn rough notes into blog posts that sound exactly like you.**

## The Problem

You have ideas worth sharing, but:
- **Writing takes forever** - Turning rough notes into polished prose is time-consuming
- **Your voice gets lost** - Generic AI writing doesn't capture your unique style
- **Quality suffers** - Rushed posts lack the depth and personality readers expect
- **Iteration is painful** - Editing and refining feels like starting over

## The Solution

Blog Writer is a multi-stage AI pipeline that:

1. **Learns your style** - Analyzes your existing writings to extract your unique voice
2. **Transforms ideas** - Converts rough brain dumps into structured drafts
3. **Ensures accuracy** - Reviews content for factual consistency with your source material
4. **Maintains authenticity** - Checks that the output matches your writing style
5. **Incorporates feedback** - Iterates based on your input until it's right

**The result**: A blog post that reads like you wrote it, in a fraction of the time.

## Quick Start

**Prerequisites**: Complete the [Amplifier setup instructions](../../README.md#-step-by-step-setup) first.

### Basic Usage

```bash
make blog-write \
  IDEA=path/to/your/idea.md \
  WRITINGS=path/to/your/existing/posts/
```

The tool will:
1. Extract your writing style from existing posts
2. Generate an initial draft
3. Review and refine it
4. Present it for your feedback
5. Iterate until you approve

### Your First Blog Post

1. **Prepare your idea** - Create a markdown file with your rough thoughts:

```markdown
# Idea: Why I Love Building with AI

Random thoughts:
- AI is changing how we build software
- The magic is in combining code structure with AI creativity
- Example: this blog writer tool itself!
- People focus too much on the AI, not enough on the architecture
```

2. **Point to your writings** - Provide a directory with 3-5 of your existing blog posts:

```
my_writings/
├── post_about_productivity.md
├── post_about_software_design.md
└── post_about_learning.md
```

3. **Run the tool**:

```bash
make blog-write \
  IDEA=my_idea.md \
  WRITINGS=my_writings/
```

4. **Review and refine** - The tool will:
   - Create a draft
   - Save it to `.data/blog_post_writer/<session>/draft_iter_1.md`
   - Prompt you to review and add `[bracketed comments]` where you want changes
   - Generate a revised version incorporating your feedback

5. **Approve when ready** - Type `approve` when the draft is ready, and the final post will be saved with a slug-based filename.

## Usage Examples

### Basic: Simple Blog Post

```bash
make blog-write \
  IDEA=rough_idea.md \
  WRITINGS=my_blog_posts/
```

**What happens**:
- Extracts your style from existing posts
- Generates a draft matching your voice
- Reviews for accuracy and consistency
- Presents for your feedback
- Saves final post when approved

### Advanced: With Custom Instructions

```bash
make blog-write \
  IDEA=sensitive_topic.md \
  WRITINGS=my_posts/ \
  INSTRUCTIONS="Remove any mentions of specific company names or internal projects"
```

**What happens**:
- Same workflow as basic usage
- Additional instructions guide the AI throughout
- Source reviewer checks compliance with instructions
- Ensures sensitive information is handled appropriately

### Resume Interrupted Session

```bash
make blog-resume
```

**What happens**:
- Finds your most recent session
- Loads state from where you left off
- Continues from the exact same point
- All previous context and iterations preserved

## How to Give Feedback

During the review phase, the tool presents a draft and asks for your input. You can:

### Option 1: Add Inline Comments

Open the draft file (e.g., `.data/blog_post_writer/<session>/draft_iter_1.md`) and add `[bracketed comments]` where you want changes:

```markdown
This paragraph explains the concept [but needs a concrete example here].

The transition feels abrupt [maybe add a sentence connecting to the previous section?].

Great point about architecture [let's expand this with the pirate ship metaphor].
```

Save the file and type `done` at the prompt.

### Option 2: Approve As-Is

If the draft is ready, simply type `approve` at the prompt.

### Option 3: Skip Review

Type `skip` to continue to the next iteration without making changes (useful if you want to see another AI revision first).

## How It Works

### The Pipeline

```
Your Idea + Your Writings
         ↓
    [Extract Style]
         ↓
  [Generate Draft]
         ↓
   [Review Sources] ────→ [Revise if needed]
         ↓
   [Review Style] ──────→ [Revise if needed]
         ↓
   [Your Feedback] ─────→ [Revise if requested]
         ↓
    Final Post
```

### Key Components

- **Style Extractor**: Analyzes 3-5 of your existing posts to identify tone, voice, vocabulary patterns
- **Blog Writer**: Generates content based on your idea and style profile
- **Source Reviewer**: Checks that claims match your source material (including your feedback!)
- **Style Reviewer**: Verifies consistency with your writing patterns
- **State Manager**: Saves progress after every step (you can interrupt and resume anytime)

### Why It Works

**Code handles the structure**:
- Pipeline orchestration and flow control
- State management and checkpointing
- File I/O and error handling
- User interaction and feedback parsing

**AI handles the intelligence**:
- Understanding your writing style
- Generating creative content
- Making nuanced quality judgments
- Incorporating feedback effectively

This separation means the tool is both reliable (code manages the flow) and creative (AI handles the content).

## Configuration

### Command-Line Options

```bash
# Required
--idea PATH              # Path to your idea/brain dump file
--writings-dir PATH      # Directory with your existing writings

# Optional
--instructions TEXT      # Additional guidance (e.g., "keep it under 1000 words")
--output PATH           # Custom output path (default: auto-generated from title)
--resume                # Resume from saved state
--reset                 # Start fresh (discard saved state)
--max-iterations N      # Maximum refinement iterations (default: 10)
--verbose              # Enable detailed logging
```

### Session Data

All working files are saved to `.data/blog_post_writer/<timestamp>/`:
- `state.json` - Pipeline state for resume
- `draft_iter_N.md` - Each iteration's draft (immutable after you edit)
- `<slug>.md` - Final approved blog post

## Troubleshooting

### "No writings found"

**Problem**: The tool couldn't find any markdown files in your writings directory.

**Solution**: Ensure your writings directory contains `.md` files and use the full path.

### "Draft file not found for feedback"

**Problem**: The tool is looking for a draft that doesn't exist yet.

**Solution**: This was a bug in earlier versions. Make sure you're using the latest version where draft files are created correctly.

### "API key not found"

**Problem**: The Claude API key isn't configured.

**Solution**: Follow the [Amplifier setup instructions](../../README.md#-step-by-step-setup) to configure your API key.

### "Review flagged user-requested changes"

**Problem**: Earlier versions incorrectly flagged your feedback as "not in source."

**Solution**: This is fixed in the current version. User feedback is now treated as valid source material.

## Learn More

- **[HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md)** - Create your own tool like this
- **[Amplifier](https://github.com/microsoft/amplifier)** - The framework that powers these tools
- **[Scenario Tools](../)** - More tools like this one

## What's Next?

This tool demonstrates what's possible when you describe a thinking process to Amplifier:

1. **Use it** - Generate blog posts from your ideas
2. **Learn from it** - See [HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md) for how to create your own tools
3. **Build your own** - Describe your goal and thinking process to Amplifier
4. **Share back** - Let others learn from what you create!

---

**Built with minimal input using Amplifier** - The entire tool came from one conversation describing the goal and thinking process. See [HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md) for details.
