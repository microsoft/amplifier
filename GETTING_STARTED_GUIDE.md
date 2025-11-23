# Amplifier: Beginner's Getting Started Guide

**A practical, step-by-step guide to taking control of Amplifier and using it to build AI-powered tools.**

---

## 🎯 What You'll Learn

By the end of this guide, you'll know how to:
1. Install and set up Amplifier
2. Use the pre-built tools
3. Create your own AI-powered tools without writing code
4. Navigate the repository structure
5. Use the development workflow

---

## 📋 Part 1: Installation & Setup

### Step 1: Check Prerequisites

Open your terminal and check what you have:

```bash
python3 --version  # Need 3.11 or higher
uv --version       # Python package manager
node --version     # Any recent version
pnpm --version     # Node package manager
git --version      # Any version
```

### Step 2: Install Missing Tools

**On Mac:**
```bash
brew install python3 node git pnpm uv
```

**On Ubuntu/Debian/WSL:**
```bash
# System packages
sudo apt update && sudo apt install -y python3 python3-pip nodejs npm git

# pnpm
npm install -g pnpm
pnpm setup && source ~/.bashrc

# uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**On Windows:**
1. Install [WSL2](https://learn.microsoft.com/windows/wsl/install)
2. Run the Ubuntu commands above inside WSL

### Step 3: Clone and Install Amplifier

```bash
# Clone the repository
git clone https://github.com/microsoft/amplifier.git
cd amplifier

# Install all dependencies (this may take a few minutes)
make install

# Activate the Python virtual environment
source .venv/bin/activate  # Linux/Mac/WSL
# .venv\Scripts\Activate.ps1  # Windows PowerShell
```

### Step 4: Start Claude Code

```bash
# Start the Claude Code interface
claude
```

You're now ready to use Amplifier! 🎉

---

## 🚀 Part 2: Using Pre-Built Tools (The Easy Way)

Amplifier comes with several ready-to-use tools. Let's try them!

### Example 1: Blog Writer

**What it does**: Turns rough notes into polished blog posts that sound like you wrote them.

**Step-by-step:**

1. **Create a rough idea file** (`my_idea.md`):
```markdown
# Why AI Development is Different

Random thoughts:
- Traditional coding: write every line yourself
- AI coding: describe what you want
- The shift is metacognitive - thinking about thinking
- Example: I built a tool just by describing how it should work
```

2. **Gather 3-5 of your existing blog posts** (for style learning):
```
my_writings/
├── post1.md
├── post2.md
└── post3.md
```

3. **Run the tool**:
```bash
make blog-write \
  IDEA=my_idea.md \
  WRITINGS=my_writings/
```

4. **Review the draft**:
   - Tool generates a draft matching your writing style
   - Opens file in `.data/blog_post_writer/<timestamp>/draft_iter_1.md`
   - Add `[bracketed comments]` where you want changes
   - Type `done` when ready

5. **Approve or iterate**:
   - Type `approve` when satisfied
   - Or add more feedback and iterate

**That's it!** You have a polished blog post.

### Example 2: Transcribe Audio/Video

**What it does**: Converts audio or video files into searchable text transcripts.

```bash
# Transcribe a single file
make transcribe FILE=path/to/recording.mp3

# Transcribe all files in a directory
make transcribe-dir DIR=path/to/recordings/
```

**Output**: Markdown files with timestamped transcripts in `.data/transcribe/`.

### Example 3: Web to Markdown

**What it does**: Converts web pages to clean markdown files.

```bash
# Convert a single URL
make web-to-md URL=https://example.com/article

# Convert multiple URLs from a file
make web-to-md-batch FILE=urls.txt
```

**Output**: Clean markdown files ready for processing.

---

## 🛠️ Part 3: Creating Your Own Tools (The Magic)

This is where Amplifier shines. You can create custom AI tools by just **describing what you want**.

### The Concept: Metacognitive Recipes

A **metacognitive recipe** = describing HOW to think through a problem step-by-step.

Instead of writing code, you describe:
1. What the tool should do
2. How it should think through the problem
3. What steps to follow

### Example: Creating a "Research Summarizer"

**Your goal**: A tool that researches a topic and creates a summary.

**Step 1: Describe Your Thinking Process**

Think about how YOU would do this task manually:

```markdown
I want a tool called "Research Summarizer"

Goal: Research a topic and create a structured summary

Steps:
1. Search the web for the topic and collect 5-10 relevant articles
2. Extract the main themes from all articles
3. Show me the themes and ask which ones to explore deeper
4. Do in-depth research on my selected themes
5. Create a structured summary with:
   - Executive summary (3 sentences)
   - Main themes (with evidence from sources)
   - Key takeaways (bullet points)
   - Sources cited
6. Ask for my feedback and refine if needed
```

**Step 2: Give This to Amplifier**

Start Claude Code and use the special command:

```bash
claude  # Start Claude Code
```

Then in the Claude interface:

```
/ultrathink-task I want to create a tool called "Research Summarizer"

Goal: Research a topic and create a structured summary

Steps:
1. Search the web for the topic and collect 5-10 relevant articles
2. Extract the main themes from all articles
3. Show me the themes and ask which ones to explore deeper
4. Do in-depth research on my selected themes
5. Create a structured summary with:
   - Executive summary (3 sentences)
   - Main themes (with evidence from sources)
   - Key takeaways (bullet points)
   - Sources cited
6. Ask for my feedback and refine if needed
```

**Step 3: Amplifier Builds It**

- Amplifier asks clarifying questions (answer them)
- It generates the code for your tool
- Creates documentation
- Adds it to the `scenarios/` directory

**Step 4: Test and Refine**

```
Let's test it! Run research-summarizer on "quantum computing applications"
```

Watch it work, note any issues, and give feedback:

```
The summaries are too long. Please make them more concise -
aim for 2-3 sentences max per theme.
```

Amplifier adjusts the tool based on your feedback.

**Step 5: Use Your New Tool**

Your tool is now part of Amplifier! Use it anytime:

```bash
make research-summarizer TOPIC="machine learning ethics"
```

### What Makes a Good Recipe?

✅ **DO:**
- Break tasks into clear steps (5-10 steps max)
- Include decision points ("if X, then Y")
- Specify checkpoints ("show me results before continuing")
- Plan for iteration ("refine based on feedback")

❌ **DON'T:**
- Try to solve everything at once
- Micromanage every detail
- Write code yourself
- Skip the "why" behind each step

---

## 📁 Part 4: Understanding the Repository

### Key Directories

```
amplifier/
├── scenarios/              ← Pre-built tools (blog-writer, transcribe, etc.)
│   ├── blog_writer/       ← Example: blog writing tool
│   ├── transcribe/        ← Example: audio transcription
│   └── README.md          ← Overview of all tools
│
├── amplifier/             ← Core Python modules (the engine)
│   ├── ccsdk_toolkit/     ← Tools for building CLI apps with AI
│   ├── knowledge_*/       ← Knowledge extraction & synthesis
│   ├── memory/            ← Persistent memory system
│   └── utils/             ← Utilities
│
├── .claude/               ← Claude Code integration
│   ├── agents/            ← Specialized AI agents
│   ├── commands/          ← Slash commands (/ddd, etc.)
│   └── tools/             ← Development tools
│
├── docs/                  ← User documentation
│   ├── CREATE_YOUR_OWN_TOOLS.md  ← How to create tools
│   ├── THIS_IS_THE_WAY.md        ← Best practices
│   └── document_driven_development/  ← DDD workflow
│
├── ai_context/            ← AI guidance & philosophy
│   ├── IMPLEMENTATION_PHILOSOPHY.md
│   └── MODULAR_DESIGN_PHILOSOPHY.md
│
├── Makefile               ← All the commands you can run
└── README.md              ← Quick start guide
```

### Where Things Go

- **Your tools**: `scenarios/<your-tool-name>/`
- **Tool outputs**: `.data/<tool-name>/`
- **Experimental work**: `ai_working/`
- **Test code**: `tests/`

---

## 🎮 Part 5: Common Workflows

### Workflow 1: Daily Development

```bash
# Activate environment
source .venv/bin/activate

# Start Claude Code
claude

# In Claude, tell it what you want:
"Let's create a tool that extracts action items from meeting notes"

# Follow the prompts and describe your thinking process
```

### Workflow 2: Document-Driven Development (DDD)

For building complete features with planning:

```bash
# Start Claude
claude

# Use the DDD workflow
/ddd:1-plan         # Design the feature
/ddd:2-docs         # Update documentation
/ddd:3-code-plan    # Plan implementation
/ddd:4-code         # Implement and test
/ddd:5-finish       # Clean up and finalize
```

Each step creates artifacts that the next step uses. You control everything.

### Workflow 3: Parallel Experimentation

Try multiple approaches simultaneously:

```bash
# Create parallel worktrees for different approaches
make worktree feature-approach-a
make worktree feature-approach-b

# Work on both in parallel (in different terminal windows)
# Each has its own branch, environment, and context

# Compare results
make worktree-list

# Keep the winner, delete the loser
make worktree-rm feature-approach-a
```

### Workflow 4: Testing & Validation

```bash
# Run all checks (lint, format, type-check)
make check

# Run all tests
make test

# Test a specific scenario
make blog-write IDEA=test.md WRITINGS=samples/
```

---

## 💡 Part 6: Practical Examples

### Example 1: Meeting Notes to Action Items

**Your request to Claude:**
```
/ultrathink-task Create a tool called "action-extractor"

Goal: Extract action items from meeting notes

Steps:
1. Read the meeting notes file
2. Identify all action items (tasks, commitments, decisions)
3. Extract who is responsible for each item
4. Extract deadlines if mentioned
5. Categorize by priority (urgent, important, normal)
6. Output a structured markdown file with:
   - Summary of key decisions
   - Action items table (task, owner, deadline, priority)
   - Follow-up questions or unclear items
```

**Result**: A tool you can run anytime:
```bash
make action-extractor NOTES=meeting.md
```

### Example 2: Code Review Assistant

**Your request to Claude:**
```
/ultrathink-task Create a tool called "code-reviewer"

Goal: Review code for common issues and philosophy alignment

Steps:
1. Read the code files in the specified directory
2. Check against our design philosophy (ruthless simplicity)
3. Look for common issues:
   - Overly complex abstractions
   - Missing error handling
   - Accessibility concerns
   - Security vulnerabilities
4. Suggest specific improvements with examples
5. Prioritize findings (critical, important, nice-to-have)
6. Output a review report with actionable feedback
```

**Result**: Automated code reviews:
```bash
make code-reviewer DIR=src/auth/
```

### Example 3: Learning Journal

**Your request to Claude:**
```
/ultrathink-task Create a tool called "learning-digest"

Goal: Turn my scattered learning notes into a weekly digest

Steps:
1. Find all markdown files in my learning directory from the past week
2. Extract key concepts, insights, and questions
3. Group related topics together
4. Create connections between different learnings
5. Identify patterns or themes
6. Generate a weekly digest with:
   - Top 3 insights
   - New concepts learned
   - Questions to explore further
   - Suggested next learning topics
```

**Result**: Weekly learning summaries:
```bash
make learning-digest DIR=notes/learning/
```

---

## 🔧 Part 7: Essential Commands

### Development Commands

```bash
make install          # Install all dependencies
make check           # Lint, format, type-check everything
make test            # Run all tests
make clean           # Clean up generated files
```

### Tool Usage Commands

```bash
# See all available commands
make help

# Blog writing
make blog-write IDEA=idea.md WRITINGS=posts/
make blog-resume     # Resume interrupted session

# Transcription
make transcribe FILE=audio.mp3
make transcribe-dir DIR=recordings/

# Web to markdown
make web-to-md URL=https://example.com
```

### Worktree Commands (Parallel Development)

```bash
make worktree <name>        # Create new worktree
make worktree-list          # List all worktrees
make worktree-rm <name>     # Remove worktree
```

### Transcript Commands

```bash
make transcript-list                    # List saved conversations
make transcript-search TERM="auth"      # Search conversations
```

---

## 🎓 Part 8: Learning Path

### Beginner (Week 1)
1. ✅ Set up Amplifier (you did this!)
2. ✅ Use 2-3 pre-built tools (try blog-writer, transcribe)
3. ✅ Read the scenarios README
4. Create your first simple tool (action extractor or note organizer)

### Intermediate (Week 2-3)
1. Create 2-3 more custom tools
2. Learn the DDD workflow (`/ddd:1-plan` etc.)
3. Experiment with worktrees (parallel approaches)
4. Read `THIS_IS_THE_WAY.md` for best practices

### Advanced (Week 4+)
1. Build multi-stage pipelines (chaining tools together)
2. Create specialized agents for your domain
3. Contribute patterns back to the community
4. Use knowledge synthesis features

---

## 🆘 Part 9: Troubleshooting

### "Command not found: make"

**Problem**: Make isn't installed

**Solution**:
```bash
# Ubuntu/Debian
sudo apt install make

# Mac
brew install make
```

### "Python version too old"

**Problem**: Need Python 3.11+

**Solution**:
```bash
# Ubuntu/Debian
sudo apt install python3.11

# Mac
brew install python@3.11
```

### "API key not configured"

**Problem**: Claude API key missing

**Solution**: Follow Anthropic's setup guide to get an API key, then configure it in your environment.

### "No module named 'amplifier'"

**Problem**: Virtual environment not activated

**Solution**:
```bash
source .venv/bin/activate
```

### "Tool didn't work as expected"

**Problem**: The generated tool has issues

**Solution**: Give feedback in Claude:
```
The tool is generating summaries that are too long.
Please adjust it to create concise summaries (2-3 sentences max).
```

---

## 🎯 Part 10: Quick Reference

### The 3-Step Pattern

1. **Describe what you want**
   - "I need a tool that does X"

2. **Describe how to think about it**
   - "It should work by: step 1, step 2, step 3..."

3. **Let Amplifier build it**
   - `/ultrathink-task <your description>`

### The 5 Questions to Ask

Before creating a tool, ask yourself:

1. **What problem does this solve?** (Be specific)
2. **How would I do this manually?** (Step by step)
3. **Where should it pause for feedback?** (Checkpoints)
4. **What makes a good result?** (Success criteria)
5. **What could go wrong?** (Error handling)

### The Golden Rules

✅ **DO:**
- Start simple, iterate to complexity
- Break big tasks into smaller tools
- Give clear, specific feedback
- Test with real examples
- Document your thinking process

❌ **DON'T:**
- Try to build everything at once
- Write code manually (let Amplifier do it)
- Skip testing your tools
- Forget to give feedback
- Expect perfection on first try

---

## 🚀 Next Steps

**You're ready!** Here's what to do next:

1. **Try a pre-built tool** - Run `make blog-write` or `make transcribe`
2. **Create your first tool** - Pick something simple you do often
3. **Read the docs** - Check out `docs/CREATE_YOUR_OWN_TOOLS.md`
4. **Join the community** - Share what you build
5. **Experiment** - The more you use it, the better you'll get

---

## 📚 Additional Resources

- **[README.md](README.md)** - Main project overview
- **[CREATE_YOUR_OWN_TOOLS.md](docs/CREATE_YOUR_OWN_TOOLS.md)** - Detailed tool creation guide
- **[THIS_IS_THE_WAY.md](docs/THIS_IS_THE_WAY.md)** - Best practices and strategies
- **[scenarios/README.md](scenarios/README.md)** - Overview of all pre-built tools
- **[Document-Driven Development](docs/document_driven_development/)** - Complete feature workflow

---

## 🤝 Getting Help

**Remember**: This is an experimental system. Things break. That's part of learning!

- **Read error messages carefully** - They often tell you exactly what's wrong
- **Check the docs** - Most questions are answered there
- **Experiment** - Try things, see what happens
- **Give feedback** - Tell Amplifier when something doesn't work
- **Iterate** - Few things work perfectly on the first try

---

**Welcome to Amplifier! Now go build something amazing.** 🎉
