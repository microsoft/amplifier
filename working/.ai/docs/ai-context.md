# AI Context Management Guide

Master the art of feeding AI the right information at the right time for optimal results.

## 📚 Overview

The AI context system helps you:

- Provide consistent reference materials to your AI assistant
- Generate comprehensive project documentation
- Manage external library documentation
- Organize project-specific context
- Maintain philosophy alignment

## 🗂️ Directory Structure

```
ai_context/                    # Persistent reference materials
├── README.md                  # Directory documentation
├── IMPLEMENTATION_PHILOSOPHY.md   # Core development philosophy
├── MODULAR_DESIGN_PHILOSOPHY.md   # Architecture principles
├── generated/                 # Auto-generated project docs
│   └── [project-rollups]     # Created by build_ai_context_files.py
└── git_collector/            # External library docs
    └── [fetched-docs]        # Created by build_git_collector_files.py

ai_working/                   # Active AI workspace
├── README.md                 # Usage instructions
├── [feature-folders]/        # Feature-specific context
└── tmp/                      # Temporary files (git-ignored)
    └── [scratch-files]       # Experiments, debug logs, etc.
```

## 🎯 Quick Start

### 1. Generate Project Context

```bash
# Generate comprehensive project documentation
make ai-context-files

# Or run directly
python tools/build_ai_context_files.py
```

This creates rollup files in `ai_context/generated/` containing:

- All source code organized by type
- Configuration files
- Documentation
- Test files

### 2. Add External Documentation

```bash
# Fetch library documentation
python tools/build_git_collector_files.py

# Configure libraries in git_collector_config.json
{
  "libraries": [
    {
      "name": "react",
      "repo": "facebook/react",
      "docs_path": "docs/"
    }
  ]
}
```

### 3. Load Philosophy

```
# In your AI assistant
/prime

# Or manually reference
Please read @ai_context/IMPLEMENTATION_PHILOSOPHY.md and follow these principles
```

This can be skipped if the files are @mentioned in the root AGENTS.md or CLAUDE.md file or equivalent.

## 🧠 Philosophy Documents

### IMPLEMENTATION_PHILOSOPHY.md

Core principles that guide all development:

- **Simplicity First**: Clean, maintainable code
- **Human-Centric**: AI amplifies, doesn't replace
- **Pragmatic Choices**: Real-world solutions
- **Trust in Emergence**: Let good architecture emerge

### MODULAR_DESIGN_PHILOSOPHY.md

Architecture principles for scalable systems:

- **Bricks & Studs**: Self-contained modules with clear interfaces
- **Contract-First**: Define interfaces before implementation
- **Regenerate, Don't Patch**: Rewrite modules when needed
- **AI-Ready**: Design for future automation

### Using Philosophy in Prompts

```
/ultrathink-task Build a user authentication system following our philosophy:
@ai_context/IMPLEMENTATION_PHILOSOPHY.md
@ai_context/MODULAR_DESIGN_PHILOSOPHY.md

Focus especially on simplicity and contract-first design.
```

## 📋 Context Generation Tools

### build_ai_context_files.py

Generates comprehensive project documentation:

```python
# Default configuration
FILE_GROUPS = {
    "Source Code": {
        "patterns": ["**/*.py", "**/*.js", "**/*.ts"],
        "exclude": ["**/test_*", "**/*.test.*"]
    },
    "Configuration": {
        "patterns": ["**/*.json", "**/*.yaml", "**/*.toml"],
        "exclude": ["**/node_modules/**"]
    }
}
```

**Features**:

- Groups files by type
- Respects .gitignore
- Adds helpful headers
- Creates single-file rollups

**Customization**:

```python
# In build_ai_context_files.py
FILE_GROUPS["My Custom Group"] = {
    "patterns": ["**/*.custom"],
    "exclude": ["**/temp/**"]
}
```

### collect_files.py

Core utility for pattern-based file collection:

```bash
# Collect all Python files
python tools/collect_files.py "**/*.py" > python_files.md

# Collect with exclusions
python tools/collect_files.py "**/*.ts" --exclude "**/node_modules/**" > typescript.md
```

### build_git_collector_files.py

Fetches external documentation:

```bash
# Configure libraries
cat > git_collector_config.json << EOF
{
  "libraries": [
    {
      "name": "fastapi",
      "repo": "tiangolo/fastapi",
      "docs_path": "docs/",
      "include": ["tutorial/", "advanced/"]
    }
  ]
}
EOF

# Fetch documentation
python tools/build_git_collector_files.py
```

## 🎨 Best Practices

### 1. Layer Your Context

```
Base Layer (Philosophy)
    ↓
Project Layer (Generated docs)
    ↓
Feature Layer (Specific requirements)
    ↓
Task Layer (Current focus)
```

### 2. Reference Strategically

```
# Good: Specific, relevant context
@ai_context/generated/api_endpoints.md
@ai_working/auth-feature/requirements.md

# Avoid: Everything at once
@ai_context/**/*
```

### 3. Keep Context Fresh

```bash
# Update before major work
make ai-context-files

# Add to git hooks
echo "make ai-context-files" >> .git/hooks/pre-commit
```

### 4. Use Working Spaces

```
ai_working/
├── feature-x/
│   ├── requirements.md    # What to build
│   ├── decisions.md       # Architecture choices
│   ├── progress.md        # Current status
│   └── blockers.md        # Issues to resolve
└── tmp/
    └── debug-session-1/   # Temporary investigation
```

## 🔧 Advanced Techniques

### Dynamic Context Loading

```
# Load context based on current task
/ultrathink-task I need to work on the API layer.
Load relevant context:
@ai_context/generated/api_*.md
@ai_context/api-guidelines.md
```

### Context Templates

Create reusable context sets:

```bash
# .ai/contexts/api-work.md
# API Development Context

## Load these files:
- @ai_context/generated/api_routes.md
- @ai_context/generated/models.md
- @ai_context/api-standards.md
- @docs/api/README.md

## Key principles:
- RESTful design
- Comprehensive error handling
- OpenAPI documentation
```

### Incremental Context

Build context progressively:

```
# Start broad
Read @ai_context/IMPLEMENTATION_PHILOSOPHY.md

# Get specific
Now read @ai_context/generated/auth_module.md

# Add requirements
Also consider @ai_working/auth-v2/requirements.md
```

### Context Versioning

Track context evolution:

```bash
# Version generated docs
cd ai_context/generated
git add .
git commit -m "Context snapshot: pre-refactor"
```

## 📊 Context Optimization

### Size Management

```python
# In build_ai_context_files.py
MAX_FILE_SIZE = 100_000  # Skip large files
MAX_ROLLUP_SIZE = 500_000  # Split large rollups
```

### Relevance Filtering

```python
# Custom relevance scoring
def is_relevant(file_path: Path) -> bool:
    # Skip generated files
    if 'generated' in file_path.parts:
        return False

    # Skip vendor code
    if 'vendor' in file_path.parts:
        return False

    # Include based on importance
    important_dirs = ['src', 'api', 'core']
    return any(d in file_path.parts for d in important_dirs)
```

### Context Caching

```bash
# Cache expensive context generation
CONTEXT_CACHE=".ai/context-cache"
CACHE_AGE=$(($(date +%s) - $(stat -f %m "$CONTEXT_CACHE" 2>/dev/null || echo 0)))

if [ $CACHE_AGE -gt 3600 ]; then  # 1 hour
    make ai-context-files
    touch "$CONTEXT_CACHE"
fi
```

## 🎯 Common Patterns

### Feature Development

```
1. Create feature workspace:
   mkdir -p ai_working/new-feature

2. Add requirements:
   echo "..." > ai_working/new-feature/requirements.md

3. Generate fresh context:
   make ai-context-files

4. Start development:
   /ultrathink-task Implement @ai_working/new-feature/requirements.md
```

### Debugging Sessions

```
1. Capture context:
   echo "Error details..." > ai_working/tmp/debug-notes.md

2. Add relevant code:
   python tools/collect_files.py "**/auth*.py" > ai_working/tmp/auth-code.md

3. Analyze:
   Help me debug using:
   @ai_working/tmp/debug-notes.md
   @ai_working/tmp/auth-code.md
```

### Documentation Updates

```
1. Generate current state:
   make ai-context-files

2. Update docs:
   Update the API documentation based on:
   @ai_context/generated/api_routes.md

3. Verify consistency:
   /review-code-at-path docs/
```

## 🚀 Pro Tips

1. **Front-Load Philosophy**: Always start with philosophy docs
2. **Layer Gradually**: Add context as needed, not all at once
3. **Clean Regularly**: Remove outdated context from ai_working
4. **Version Important Context**: Git commit key snapshots
5. **Automate Generation**: Add to build pipelines

## 🔗 Related Documentation

- [Command Reference](commands.md) - Commands that use context
- [Philosophy Guide](philosophy.md) - Core principles
