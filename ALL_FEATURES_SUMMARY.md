# 🎯 Amplifier: Complete Feature Tour Summary

**You've just seen all 6 major features!** Here's your complete reference guide.

---

## 📚 Interactive Demo Scripts

Run any of these to explore features in detail:

```bash
python feature_demo_1_memory.py          # Memory System
python feature_demo_2_search.py          # Semantic Search
python feature_demo_3_extraction.py      # Knowledge Extraction
python feature_demo_4_agents.py          # Specialized Agents
python feature_demo_5_worktrees.py       # Parallel Worktrees
python feature_demo_6_knowledge_graph.py # Knowledge Graph
```

---

## 🧠 Feature #1: Memory System

**What**: Persistent memory that survives across sessions
**Why**: Stop re-explaining the same things to AI

### Key Capabilities
- ✅ Stores preferences, learnings, decisions, solutions, patterns
- ✅ Categorized and searchable
- ✅ Access tracking (knows what's useful)
- ✅ JSON storage (human-readable)
- ✅ Metadata for context

### Quick Start
```python
from amplifier.memory import MemoryStore, Memory

store = MemoryStore()
memory = Memory(
    content="User prefers dark mode",
    category="preference"
)
store.add_memory(memory)
```

### Storage Location
- `.data/memory.json` - All memories
- Categories: `preference`, `learning`, `decision`, `issue_solved`, `pattern`

---

## 🔍 Feature #2: Semantic Search

**What**: AI-powered search that understands meaning, not just keywords
**Why**: Find relevant information even with different words

### Key Capabilities
- ✅ Searches by meaning using AI embeddings
- ✅ 384-dimensional vector space
- ✅ Relevance scoring (0.0-1.0)
- ✅ Graceful fallback to keyword search
- ✅ Natural language queries

### Example
```python
from amplifier.search import MemorySearcher

searcher = MemorySearcher()
results = searcher.search(
    "database performance issues",
    memories,
    limit=5
)
# Finds: "Always use async/await for DB operations"
# Even though words are different!
```

### How It Works
1. Query → AI embedding vector
2. Memories → AI embedding vectors
3. Cosine similarity calculation
4. Rank by similarity score
5. Return top matches

---

## 📚 Feature #3: Knowledge Extraction

**What**: Automatically extracts structured knowledge from documents
**Why**: Build knowledge base without manual note-taking

### Key Capabilities
- ✅ AI-powered extraction (Claude Code SDK)
- ✅ Automatic categorization
- ✅ Works on any text (docs, notes, code comments)
- ✅ Rich metadata tracking
- ✅ Batch processing

### Workflow
```bash
# 1. Add your docs to content directory
echo 'AMPLIFIER_CONTENT_DIRS=~/docs' >> .env

# 2. Scan for content
make content-scan

# 3. Extract knowledge
make knowledge-sync

# 4. Query what you learned
make knowledge-query Q="API best practices"
```

### What Gets Extracted
From a single meeting note:
- ✅ Decisions with rationale
- ✅ Technical learnings
- ✅ Problem solutions
- ✅ Best practices & patterns
- ✅ Configuration preferences
- ✅ API limits & constraints

---

## 🤖 Feature #4: Specialized AI Agents (23 Total)

**What**: Expert AI agents for specific tasks
**Why**: Specialist > Generalist for complex work

### Categories

#### 🏗️ Architecture & Design
- `zen-architect` - System design and planning
- `modular-builder` - Implementation from specs
- `api-contract-designer` - API design
- `database-architect` - Database design
- `module-intent-architect` - Module specifications

#### 🐛 Debugging & Quality
- `bug-hunter` - Systematic bug investigation
- `test-coverage` - Testing strategies
- `post-task-cleanup` - Code cleanup
- `ambiguity-guardian` - Clarity enforcement

#### 🔒 Security & Performance
- `security-guardian` - Security audits
- `performance-optimizer` - Performance analysis

#### 📚 Knowledge & Analysis
- `concept-extractor` - Extract key concepts
- `insight-synthesizer` - Find patterns
- `knowledge-archaeologist` - Organize knowledge
- `pattern-emergence` - Pattern discovery
- `analysis-engine` - General analysis

#### 🎨 Specialized Domains
- `graph-builder` - Knowledge graph construction
- `visualization-architect` - Data visualization
- `integration-specialist` - System integration
- `subagent-architect` - Create new agents

### Usage Patterns

**Single Agent:**
```
"Use zen-architect to design my caching layer"
```

**Agent Chain:**
```
"Use zen-architect to design, then modular-builder to implement"
```

**Parallel Analysis:**
```
"Use bug-hunter and security-guardian to review this code"
```

### Real Workflow Example
Building an API endpoint:
1. `zen-architect` → Designs architecture
2. `api-contract-designer` → Specifies API contract
3. `modular-builder` → Implements code
4. `test-coverage` → Adds tests
5. `security-guardian` → Security review

---

## 🌳 Feature #5: Parallel Worktrees

**What**: Multiple working directories from same repo
**Why**: Work on multiple solutions simultaneously, no branch switching

### Key Capabilities
- ✅ Try multiple approaches in parallel
- ✅ No context loss from branch switching
- ✅ Each worktree completely isolated
- ✅ Compare side-by-side
- ✅ Risk-free experimentation

### Common Commands

```bash
# Create worktree
make worktree my-experiment

# List all worktrees
make worktree-list

# Hide (but keep) worktree
make worktree-stash my-experiment

# Remove worktree
make worktree-rm my-experiment

# Adopt remote branch
make worktree-adopt feature-branch
```

### Real-World Scenarios

**Try Two Architectures:**
```bash
make worktree feature-jwt-auth
make worktree feature-oauth-auth
# Implement both, test both, choose winner
```

**Risky Refactoring:**
```bash
make worktree risky-refactor
# Experiment safely, delete if it fails
```

**Urgent Hotfix:**
```bash
# Working on feature in main worktree
make worktree hotfix-critical
# Fix bug in hotfix, return to feature
# No branch switching needed!
```

### Pro Tips
- Share data: Set `AMPLIFIER_DATA_DIR` in `.env`
- Each worktree = separate VS Code window
- Keep main worktree clean, experiment in others
- Delete failed experiments regularly

---

## 🕸️ Feature #6: Knowledge Graph & Synthesis

**What**: Connected network of knowledge with relationships
**Why**: Discover insights you didn't explicitly write down

### Architecture Layers

1. **Extraction** - Extract concepts from documents
2. **Graph Building** - Connect concepts with relationships
3. **Synthesis** - Find patterns and tensions
4. **Query** - Search, navigate, explore

### Key Commands

```bash
# Build graph
make knowledge-graph-build

# Statistics
make knowledge-graph-stats

# Interactive visualization
make knowledge-graph-viz NODES=50

# Semantic search
make knowledge-graph-search Q="authentication"

# Find paths
make knowledge-graph-path FROM="JWT" TO="Security"

# Explore neighbors
make knowledge-graph-neighbors CONCEPT="API" HOPS=2

# Find contradictions
make knowledge-graph-tensions TOP=10
```

### Example Graph Structure

```
[Microservices]
    |--requires--> [Service Discovery]
    |--enables--> [Independent Scaling]
    |--challenges--> [Distributed Debugging]

[JWT Auth]
    |--fits-well-with--> [Microservices]
    |--requires--> [Token Validation]
    |--security-concern--> [Token Expiration]

[Session Auth]
    |--alternative-to--> [JWT Auth]
    |--conflicts-with--> [Microservices]
```

### Advanced Features

**Tension Detection:**
- Finds contradictory knowledge
- Surfaces trade-offs
- Helps decision-making

**Path Finding:**
- Discovers how concepts connect
- Reveals implicit dependencies
- Shows reasoning chains

**Pattern Emergence:**
- Central concepts (high degree)
- Knowledge clusters
- Gaps in understanding

**Interactive Visualization:**
- Click to explore
- Search and highlight
- Zoom and pan
- Filter relationships

### Use Cases

1. **Learning New Domain**
   - Extract from docs
   - Visualize concept map
   - Navigate by connections

2. **Architecture Decisions**
   - Build technology graph
   - Find tensions
   - Make informed trade-offs

3. **Team Knowledge Base**
   - Extract team docs
   - Find contradictions
   - Surface tribal knowledge

4. **Research Synthesis**
   - Process papers
   - Find connections
   - Identify gaps

---

## 🚀 Complete Workflow: Putting It All Together

### Day 1: Setup
```bash
# 1. Configure
cp .env.example .env
# Edit AMPLIFIER_DATA_DIR and AMPLIFIER_CONTENT_DIRS

# 2. Add your documentation
# Point AMPLIFIER_CONTENT_DIRS to your docs folder

# 3. Initial extraction
make content-scan
make knowledge-sync
make knowledge-graph-build
```

### Daily Usage
```bash
# Start Claude with all enhancements
claude

# Use specialized agents
"Use zen-architect to design feature X"
"Deploy bug-hunter to find why Y is broken"

# Try multiple approaches
make worktree approach-a
make worktree approach-b
# Work on both, choose winner

# Query knowledge
make knowledge-query Q="How do we handle auth?"
make knowledge-graph-search Q="performance"
```

### Weekly Maintenance
```bash
# Update knowledge base
make knowledge-sync

# Update graph
make knowledge-graph-update

# Clean up experiments
make worktree-list
make worktree-rm failed-experiment
```

---

## 📊 Feature Comparison

| Feature | What | When to Use |
|---------|------|-------------|
| **Memory** | Persistent storage | Preferences, learnings, decisions |
| **Search** | AI-powered search | Find relevant memories |
| **Extraction** | Auto knowledge extraction | Process documentation |
| **Agents** | Specialized experts | Complex domain-specific tasks |
| **Worktrees** | Parallel development | Try multiple approaches |
| **Graph** | Connected knowledge | Discover patterns & insights |

---

## 🎓 Learning Path

### Beginner (Week 1)
- [x] Run all 6 demo scripts
- [ ] Store some memories
- [ ] Try semantic search
- [ ] Use one agent (start with `zen-architect`)
- [ ] Create and delete a worktree

### Intermediate (Week 2-4)
- [ ] Set up external data directory
- [ ] Extract knowledge from your docs
- [ ] Build knowledge graph
- [ ] Chain multiple agents
- [ ] Use worktrees for real work

### Advanced (Month 2+)
- [ ] Create custom agent
- [ ] Contribute knowledge synthesis patterns
- [ ] Build complex agent workflows
- [ ] Automate with knowledge graph queries
- [ ] Share knowledge across team

---

## 💡 Key Insights from This Tour

`★ Insight ─────────────────────────────────────`

**1. Modular Architecture**
All features are self-contained "bricks and studs" - each module can be regenerated independently without breaking others

**2. Graceful Degradation**
Every AI feature has fallbacks - search falls back to keywords, extraction shows expected output, ensuring the system always works

**3. Emergence Over Control**
The knowledge graph doesn't force structure - patterns and insights emerge naturally from connections as you add more knowledge

**4. Specialist Over Generalist**
23 specialized agents outperform a single general AI - each brings focused expertise and consistent philosophy to its domain

**5. Parallel Thinking**
Worktrees enable true parallel development - try multiple solutions simultaneously instead of sequential attempts
`─────────────────────────────────────────────────`

---

## 🆘 Troubleshooting

**Memory not persisting?**
- Check `.data/memory.json` exists
- Verify write permissions

**Search not working?**
- Falls back to keyword search automatically
- Check sentence-transformers installation

**Agents not available?**
- Ensure you're in amplifier directory
- Check `.claude/agents/` exists

**Worktree creation fails?**
- Verify git repository
- Check parent directory permissions

**Graph build fails?**
- Ensure content extracted first
- Run `make knowledge-sync` first

---

## 📖 Next Steps

1. **Read the docs:**
   - `README.md` - Full project overview
   - `AGENTS.md` - AI assistant guidance
   - `docs/WORKTREE_GUIDE.md` - Advanced worktree features

2. **Experiment:**
   - Run demos
   - Try commands
   - Break things safely

3. **Build your knowledge base:**
   - Add your docs
   - Extract knowledge
   - Build graph
   - Query and explore

4. **Join the journey:**
   - This is a research demonstrator
   - Contribute ideas
   - Share learnings
   - Help improve

---

## 🎉 You're Ready!

You've now seen all 6 major features of Amplifier:
- ✅ Memory System
- ✅ Semantic Search
- ✅ Knowledge Extraction
- ✅ Specialized AI Agents
- ✅ Parallel Worktrees
- ✅ Knowledge Graph

**Pick a feature that excites you and dive deeper!**

Questions? Start Claude Code and ask it anything about Amplifier.
