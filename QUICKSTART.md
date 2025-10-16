# 🚀 Amplifier Quick Start Guide

**You're ready to run Amplifier!** The system is installed and working.

## ✅ What Just Worked

The demo just successfully:
1. ✅ Loaded the memory system
2. ✅ Created and stored memories
3. ✅ Performed semantic search using AI embeddings
4. ✅ Found relevant memories by meaning (not just keywords!)

You now have **8 example memories** stored in `.data/memory.json`.

---

## 🎯 Try These Commands Now

### 1. Run the Demo Again
```bash
python demo_amplifier.py
```

### 2. Explore Available Commands
```bash
make help
```

### 3. Start a Claude Code Session
```bash
# Make sure you're in the amplifier directory
cd /Users/max/Documents/GitHub/amplifier

# Start Claude Code (uses all Amplifier enhancements automatically)
claude
```

### 4. Use Amplifier on Your Own Projects
```bash
# Start Claude with both Amplifier and your project
claude --add-dir /path/to/your/project

# Then paste this as your first message:
# "I'm working in /path/to/your/project. Please cd there and work there.
#  Do NOT update any issues or PRs in the Amplifier repo."
```

---

## 🧠 What Makes Amplifier Special?

### **20+ Specialized AI Agents**

Instead of one general assistant, you get experts:

- `zen-architect` - System design and architecture
- `bug-hunter` - Find and fix bugs
- `security-guardian` - Security review and hardening
- `test-coverage` - Comprehensive testing strategies
- `refactor-architect` - Code improvement and refactoring

**Example usage in Claude:**
```
"Use the zen-architect agent to design my authentication system"
"Deploy bug-hunter to find why my API is slow"
```

### **Memory System** (What you just ran!)

The system remembers:
- **Preferences** - Your coding style, tool choices
- **Learnings** - API limits, framework quirks
- **Decisions** - Why you chose approach X over Y
- **Solutions** - How you solved tricky problems

### **Knowledge Synthesis**

Extract patterns from your documentation:

```bash
# Scan your docs/articles
make content-scan

# Extract knowledge
make knowledge-update

# Query what you've learned
make knowledge-query Q="What are the best practices for async?"
```

### **Parallel Worktrees**

Test multiple solutions simultaneously:

```bash
# Try two different approaches at once
make worktree feature-approach-a
make worktree feature-approach-b

# Compare and choose the winner
make worktree-list
make worktree-rm feature-approach-b  # Remove the one you don't want
```

---

## 📚 Key Directories

```
amplifier/
├── amplifier/          # Core modules
│   ├── memory/         # Memory storage and retrieval
│   ├── search/         # Semantic search
│   ├── extraction/     # Knowledge extraction
│   └── knowledge/      # Knowledge synthesis
├── .data/              # Your data (git-ignored)
│   ├── memory.json     # Stored memories
│   └── embeddings.json # AI embeddings for search
├── tools/              # Automation scripts
└── .claude/            # Claude Code configuration
    └── agents/         # 20+ specialized agents
```

---

## 🎓 Learning Path

### Beginner
1. ✅ Run `demo_amplifier.py` (you just did this!)
2. Start `claude` in this directory
3. Ask Claude: "Show me how the memory system works"

### Intermediate
1. Create a worktree: `make worktree experiment-1`
2. Use an agent: "Use zen-architect to plan feature X"
3. Query knowledge: `make knowledge-query Q="your question"`

### Advanced
1. Configure external data dir in `.env` (enables cloud backup)
2. Build knowledge graph: `make knowledge-graph-build`
3. Create custom agents (see `.claude/AGENTS_CATALOG.md`)

---

## 🔧 Configuration

### Optional: Use Cloud Storage

Keep your knowledge across machines:

```bash
# Copy example config
cp .env.example .env

# Edit to use your cloud storage
# Example for macOS with iCloud:
AMPLIFIER_DATA_DIR=~/Library/Mobile\ Documents/com~apple~CloudDocs/amplifier/data
AMPLIFIER_CONTENT_DIRS=~/Library/Mobile\ Documents/com~apple~CloudDocs/amplifier/content
```

Benefits:
- ✅ Knowledge syncs across devices
- ✅ Automatic cloud backup
- ✅ Shared across all worktrees

---

## 💡 Next Steps

### **Immediate** (next 5 minutes)
```bash
# Explore what the system can do
make help

# Start coding with AI assistance
claude
```

### **Today** (next hour)
1. Read the [full README](README.md)
2. Browse available [agents catalog](.claude/AGENTS_CATALOG.md)
3. Try using an agent on a real task

### **This Week**
1. Set up cloud storage for persistence
2. Extract knowledge from your docs: `make knowledge-update`
3. Create a worktree for an experiment

---

## 🆘 Troubleshooting

### Demo Shows Duplicate Memories?

That's normal! Each run adds new memories. To reset:
```bash
rm .data/memory.json
python demo_amplifier.py
```

### Can't Find a Command?

```bash
make help  # Shows ALL available commands
```

### Claude Code Not Finding Agents?

Make sure you're in the amplifier directory:
```bash
cd /Users/max/Documents/GitHub/amplifier
claude  # Agents auto-load from .claude/agents/
```

---

## 📖 Documentation

- [README.md](README.md) - Full project overview
- [AGENTS.md](AGENTS.md) - AI assistant guidance
- [.claude/AGENTS_CATALOG.md](.claude/AGENTS_CATALOG.md) - All available agents
- [WORKTREE_GUIDE.md](docs/WORKTREE_GUIDE.md) - Parallel development
- [AMPLIFIER_VISION.md](AMPLIFIER_VISION.md) - Project philosophy

---

## 🎉 You're Ready!

The system is installed and working. Pick a next step from above and dive in!

**Questions?** Ask Claude Code - it knows everything about this system:
```bash
claude
# Then: "Explain how the knowledge synthesis system works"
```
