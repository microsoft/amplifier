# 🎯 Amplifier Feature Tour - Complete Index

Welcome to your complete Amplifier feature tour! This guide shows you everything step by step.

---

## 🚀 Quick Start

### Run Everything at Once
```bash
./run_all_demos.sh
```

This interactive script walks you through all 6 features with pauses between each.

### Run Individual Features
```bash
python feature_demo_1_memory.py          # 🧠 Memory System
python feature_demo_2_search.py          # 🔍 Semantic Search
python feature_demo_3_extraction.py      # 📚 Knowledge Extraction
python feature_demo_4_agents.py          # 🤖 Specialized Agents
python feature_demo_5_worktrees.py       # 🌳 Parallel Worktrees
python feature_demo_6_knowledge_graph.py # 🕸️  Knowledge Graph
```

---

## 📚 Documentation Hierarchy

### For First-Time Users
**Start here:** `QUICKSTART.md`
- Getting started
- Basic concepts
- First steps

### After Running Demos
**Next read:** `ALL_FEATURES_SUMMARY.md`
- Complete feature reference
- All commands
- Real-world examples
- Troubleshooting

### Deep Dive
**Then explore:**
- `README.md` - Full project overview
- `AGENTS.md` - AI assistant guidelines
- `CLAUDE.md` - Claude Code specific instructions
- `docs/WORKTREE_GUIDE.md` - Advanced worktree features
- `docs/KNOWLEDGE_WORKFLOW.md` - Knowledge synthesis deep dive

---

## 🎓 Recommended Learning Path

### Day 1: Understanding (30 minutes)
1. ✅ Run `./run_all_demos.sh` to see all features
2. ✅ Read `QUICKSTART.md`
3. ✅ Browse `ALL_FEATURES_SUMMARY.md`

**Goal:** Understand what Amplifier can do

### Week 1: Hands-On (2-3 hours)
1. [ ] Start Claude Code: `claude`
2. [ ] Use memory system to store preferences
3. [ ] Try semantic search
4. [ ] Use one agent: `"Use zen-architect to design X"`
5. [ ] Create and delete a test worktree

**Goal:** Get comfortable with basic features

### Week 2: Knowledge Base (3-5 hours)
1. [ ] Set up `.env` with your content directories
2. [ ] Run `make content-scan`
3. [ ] Run `make knowledge-sync`
4. [ ] Build knowledge graph: `make knowledge-graph-build`
5. [ ] Visualize: `make knowledge-graph-viz`

**Goal:** Build your personal knowledge base

### Month 1: Advanced Usage
1. [ ] Use external data directory for cloud sync
2. [ ] Chain multiple agents for complex tasks
3. [ ] Use worktrees for real parallel development
4. [ ] Query knowledge graph regularly
5. [ ] Explore agent catalog: `.claude/agents/`

**Goal:** Integrate Amplifier into daily workflow

### Month 2+: Mastery
1. [ ] Create custom specialized agent
2. [ ] Contribute improvements to patterns
3. [ ] Share knowledge base across team
4. [ ] Build automated workflows
5. [ ] Help others get started

**Goal:** Become an Amplifier power user

---

## 🎯 Feature Decision Guide

**Not sure which feature to use? Use this guide:**

### "I want to remember important information"
→ **Memory System** (Feature #1)
- Store preferences, learnings, decisions
- Persistent across sessions
- `python feature_demo_1_memory.py`

### "I need to find something I learned before"
→ **Semantic Search** (Feature #2)
- Search by meaning, not keywords
- Natural language queries
- `python feature_demo_2_search.py`

### "I have lots of documentation to process"
→ **Knowledge Extraction** (Feature #3)
- Automatic extraction from docs
- Builds searchable knowledge base
- `python feature_demo_3_extraction.py`

### "I need expert help on a specific task"
→ **Specialized Agents** (Feature #4)
- 23 domain experts
- Architecture, debugging, security, etc.
- `python feature_demo_4_agents.py`

### "I want to try multiple approaches"
→ **Parallel Worktrees** (Feature #5)
- Multiple solutions simultaneously
- No branch switching needed
- `python feature_demo_5_worktrees.py`

### "I want to see connections in my knowledge"
→ **Knowledge Graph** (Feature #6)
- Visual knowledge network
- Find patterns and tensions
- `python feature_demo_6_knowledge_graph.py`

---

## 📊 Feature Comparison Matrix

| Feature | Input | Output | Best For | Time to Value |
|---------|-------|--------|----------|---------------|
| **Memory** | Manual entries | Persistent storage | Ongoing learnings | Immediate |
| **Search** | Natural query | Relevant memories | Finding info | Immediate |
| **Extraction** | Documents | Structured knowledge | Batch processing | 1-2 hours |
| **Agents** | Task description | Expert guidance | Complex problems | Per task |
| **Worktrees** | Git branch | Isolated environment | Parallel experiments | Minutes |
| **Graph** | Knowledge base | Connected network | Pattern discovery | Few hours |

---

## 🛠️ Common Workflows

### Daily Development
```bash
# Start enhanced environment
claude

# Use agents for tasks
"Use zen-architect to design feature X"
"Deploy bug-hunter to investigate Y"
```

### Weekly Knowledge Update
```bash
# Extract from new docs
make knowledge-sync

# Update graph
make knowledge-graph-update

# Query for insights
make knowledge-query Q="topic"
```

### Experimental Development
```bash
# Try multiple approaches
make worktree approach-a
make worktree approach-b

# Work on both
code ../amplifier-approach-a
code ../amplifier-approach-b

# Choose winner
make worktree-rm approach-b
```

### Learning New Domain
```bash
# Add domain docs
echo 'AMPLIFIER_CONTENT_DIRS=~/new-domain-docs' >> .env

# Extract and visualize
make content-scan
make knowledge-sync
make knowledge-graph-build
make knowledge-graph-viz

# Explore in browser
```

---

## 🎨 Visual Overview

```
┌─────────────────────────────────────────────────────────┐
│                    AMPLIFIER FEATURES                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  🧠 Memory System ─────────┐                            │
│     └─ Persistent storage  │                            │
│                             │                            │
│  🔍 Semantic Search ───────┤                            │
│     └─ AI-powered find     │                            │
│                             ├─► 💾 Knowledge Base       │
│  📚 Knowledge Extraction ──┤                            │
│     └─ Auto extract        │                            │
│                             │                            │
│  🕸️  Knowledge Graph ──────┘                            │
│     └─ Connected insights                               │
│                                                          │
│  🤖 Specialized Agents (23)                             │
│     └─ Domain experts                                   │
│                                                          │
│  🌳 Parallel Worktrees                                  │
│     └─ Multiple solutions simultaneously                │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 Pro Tips

### Memory System
- Use categories consistently
- Add rich metadata
- Review access counts to see what's useful

### Semantic Search
- Use natural language
- Don't worry about exact words
- Check similarity scores

### Knowledge Extraction
- Organize docs by topic first
- Run incremental updates
- Review extracted knowledge

### Specialized Agents
- Start with zen-architect
- Chain agents for complex tasks
- Run parallel agents for comprehensive analysis

### Parallel Worktrees
- Keep main worktree clean
- Use descriptive names
- Delete failed experiments promptly
- Share data directory across worktrees

### Knowledge Graph
- Build incrementally
- Visualize regularly
- Query for tensions
- Explore neighborhoods

---

## 🆘 Getting Help

### Quick Reference
```bash
make help                    # All available commands
claude                       # Start enhanced environment
./run_all_demos.sh          # Run all feature demos
```

### Documentation
- `QUICKSTART.md` - Getting started
- `ALL_FEATURES_SUMMARY.md` - Complete reference
- `README.md` - Full overview

### In Claude Code
```
"Explain how the memory system works"
"Show me examples of using agents"
"How do I build a knowledge graph?"
```

Claude Code knows everything about Amplifier!

---

## 🎉 You're All Set!

**Files created for you:**
- ✅ 6 interactive demo scripts
- ✅ Master demo runner (`run_all_demos.sh`)
- ✅ Complete feature summary (`ALL_FEATURES_SUMMARY.md`)
- ✅ Quick start guide (`QUICKSTART.md`)
- ✅ This index (`FEATURE_TOUR_INDEX.md`)

**Next steps:**
1. Run `./run_all_demos.sh` if you haven't yet
2. Read `ALL_FEATURES_SUMMARY.md` for complete reference
3. Start using Amplifier: `claude`
4. Pick one feature and master it
5. Build from there!

**Happy amplifying! 🚀**
