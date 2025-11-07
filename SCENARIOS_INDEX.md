# SCENARIOS SYSTEM - COMPLETE INDEX & NAVIGATION GUIDE

## Quick Navigation

This index helps you find what you need in the comprehensive Amplifier Scenarios documentation.

### Documentation Files Created

1. **SCENARIOS_SUMMARY.md** (6KB, 188 lines)
   - Quick overview
   - Start here for orientation
   - Key concepts explained simply
   - Learning roadmap

2. **SCENARIOS_DOCUMENTATION.md** (53KB, 1,639 lines)
   - Complete technical reference
   - Detailed architecture for each scenario
   - Cross-cutting patterns analysis
   - Code metrics and examples
   - Implementation deep-dives

---

## The 5 Scenarios at a Glance

### 1. Blog Writer (The Exemplar - Study This First)
**Location**: `/scenarios/blog_writer/`
**LOC**: 1,300 | **Modules**: 5 | **Complexity**: Medium
**What It Does**: Transforms rough ideas into polished blog posts matching author's voice
**Key Learning**: Orchestration, state persistence, user feedback loops
**Documentation**:
- Overview: SCENARIOS_SUMMARY.md § "The 5 Scenarios"
- Deep dive: SCENARIOS_DOCUMENTATION.md § Section 2.1
- How to create: `/scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md`
**Study Order**:
1. Read `/scenarios/blog_writer/README.md`
2. Read `/scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md`
3. Study code: state.py → main.py → core modules

### 2. Tips Synthesizer
**Location**: `/scenarios/tips_synthesizer/`
**LOC**: 500 | **Modules**: Monolithic | **Complexity**: Low
**What It Does**: Synthesizes scattered tips into well-organized guides
**Key Learning**: Simpler orchestration, good second scenario
**Documentation**:
- Overview: SCENARIOS_SUMMARY.md § "The 5 Scenarios"
- Deep dive: SCENARIOS_DOCUMENTATION.md § Section 2.2
- How to create: `/scenarios/tips_synthesizer/HOW_TO_CREATE_YOUR_OWN.md`

### 3. Article Illustrator
**Location**: `/scenarios/article_illustrator/`
**LOC**: 1,500 | **Modules**: 4 | **Complexity**: High
**What It Does**: Generates AI illustrations for markdown articles
**Key Learning**: Multi-API coordination, cost management, resumable sessions
**Documentation**:
- Overview: SCENARIOS_SUMMARY.md § "The 5 Scenarios"
- Deep dive: SCENARIOS_DOCUMENTATION.md § Section 2.3
- How to create: `/scenarios/article_illustrator/HOW_TO_CREATE_YOUR_OWN.md`

### 4. Transcribe
**Location**: `/scenarios/transcribe/`
**LOC**: 2,000+ | **Modules**: 8 | **Complexity**: Very High
**What It Does**: Converts YouTube/audio to searchable, timestamped transcripts
**Key Learning**: Large-scale orchestration, batch processing, 8-module coordination
**Documentation**:
- Overview: SCENARIOS_SUMMARY.md § "The 5 Scenarios"
- Deep dive: SCENARIOS_DOCUMENTATION.md § Section 2.4
- How to create: `/scenarios/transcribe/HOW_TO_CREATE_YOUR_OWN.md`

### 5. Web to MD
**Location**: `/scenarios/web_to_md/`
**LOC**: 1,800+ | **Modules**: 8 | **Complexity**: High
**What It Does**: Converts web pages to markdown with domain organization
**Key Learning**: Defensive programming, error handling, paywall detection
**Documentation**:
- Overview: SCENARIOS_SUMMARY.md § "The 5 Scenarios"
- Deep dive: SCENARIOS_DOCUMENTATION.md § Section 2.5
- How to create: `/scenarios/web_to_md/HOW_TO_CREATE_YOUR_OWN.md`

---

## Finding Information by Topic

### Want to Understand...

#### State Persistence & Resume Capability
- SCENARIOS_DOCUMENTATION.md § Section 3.2 (Shared Dependencies)
- SCENARIOS_DOCUMENTATION.md § Section 4.3 (Blog Writer Resume Implementation)
- File: `/scenarios/blog_writer/state.py` (215 lines, well-commented)

#### Pipeline Orchestration
- SCENARIOS_DOCUMENTATION.md § Section 3.1 (Pattern 3: Explicit Stage Transitions)
- SCENARIOS_DOCUMENTATION.md § Section 4.4 (Blog Writer Code Structure)
- File: `/scenarios/blog_writer/main.py` (452 lines)

#### Modular Architecture (Bricks & Studs)
- SCENARIOS_DOCUMENTATION.md § Section 3.1 (Pattern 1: Modular Design)
- Files: Any `*/core.py` (150-250 lines each)
- Reference: `ai_context/MODULAR_DESIGN_PHILOSOPHY.md`

#### Multi-API Coordination
- SCENARIOS_DOCUMENTATION.md § Section 2.3 (Article Illustrator)
- File: `/scenarios/article_illustrator/image_generation/clients.py`

#### Error Handling & Defensive Programming
- SCENARIOS_DOCUMENTATION.md § Section 3.3 (Error Handling Philosophy)
- File: `/scenarios/web_to_md/validator/core.py`
- Reference: `DISCOVERIES.md` (lessons learned section)

#### Large-Scale Batch Processing
- SCENARIOS_DOCUMENTATION.md § Section 2.4 (Transcribe - 8 modules)
- File: `/scenarios/transcribe/main.py` (orchestrator)

#### Metacognitive Recipes
- SCENARIOS_SUMMARY.md § "Key Insight"
- SCENARIOS_DOCUMENTATION.md § Section 4.2 (Blog Writer Creation Story)
- SCENARIOS_DOCUMENTATION.md § Section 10.1-10.3 (Creating Your Own)

#### How These Tools Were Built
- Each scenario has: `/scenarios/SCENARIO_NAME/HOW_TO_CREATE_YOUR_OWN.md`
- Blog Writer example: `/scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md` (236 lines)
- SCENARIOS_DOCUMENTATION.md § Section 4.2

### Want to Learn...

#### By Reading Level
**Easy**: SCENARIOS_SUMMARY.md (188 lines) - Start here
**Medium**: Individual scenario READMEs - What they do
**Hard**: SCENARIOS_DOCUMENTATION.md (1,639 lines) - Complete analysis

#### By Time Available
**5 minutes**: SCENARIOS_SUMMARY.md
**30 minutes**: SCENARIOS_SUMMARY.md + blog_writer README.md
**2 hours**: Blog Writer deep-dive (README + HOW_TO + code study)
**Full day**: Complete SCENARIOS_DOCUMENTATION.md

#### By Topic Progressively
1. **What are scenarios?** → SCENARIOS_SUMMARY.md § "What You Need to Know"
2. **How do they work?** → SCENARIOS_DOCUMENTATION.md § Section 3 (Patterns)
3. **How was blog_writer built?** → `/scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md`
4. **How do I read the code?** → SCENARIOS_DOCUMENTATION.md § Section 4
5. **How do I create my own?** → SCENARIOS_DOCUMENTATION.md § Section 10

#### By Complexity
**Simplest → Start Here**:
1. tips_synthesizer (500 LOC, monolithic)
2. blog_writer (1,300 LOC, orchestrated)
3. article_illustrator (1,500 LOC, multi-API)
4. web_to_md (1,800+ LOC, defensive)
5. transcribe (2,000+ LOC, 8 modules)

### Want to Use...

#### Blog Writer
- Start: `/scenarios/blog_writer/README.md` § "Quick Start"
- Usage: `make blog-write IDEA=path WRITINGS=path`
- Documentation: SCENARIOS_DOCUMENTATION.md § 2.1

#### Tips Synthesizer
- Start: `/scenarios/tips_synthesizer/README.md` § "Quick Start"
- Usage: `make tips-synthesizer INPUT=path OUTPUT=path`
- Documentation: SCENARIOS_DOCUMENTATION.md § 2.2

#### Article Illustrator
- Start: `/scenarios/article_illustrator/README.md` § "Quick Start"
- Usage: `make illustrate INPUT=path`
- Documentation: SCENARIOS_DOCUMENTATION.md § 2.3

#### Transcribe
- Start: `/scenarios/transcribe/README.md` § "Quick Start"
- Usage: `python -m scenarios.transcribe URL_OR_FILE`
- Documentation: SCENARIOS_DOCUMENTATION.md § 2.4

#### Web to MD
- Start: `/scenarios/web_to_md/README.md` § "Usage"
- Usage: `make web-to-md URL=url`
- Documentation: SCENARIOS_DOCUMENTATION.md § 2.5

### Want to Create...

#### A Tool Like Blog Writer
- Reference: `/scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md`
- Pattern: SCENARIOS_DOCUMENTATION.md § Section 10
- Process: SCENARIOS_SUMMARY.md § "If You Want to CREATE"

#### Using the Metacognitive Recipe Approach
- Explained: SCENARIOS_DOCUMENTATION.md § Section 7.3
- Template: SCENARIOS_DOCUMENTATION.md § Section 10.3
- Example: Blog Writer creation story in § Section 4.2

#### Your Own Multi-API Scenario
- Reference: Article Illustrator (`/scenarios/article_illustrator/`)
- Code: `/scenarios/article_illustrator/image_generation/clients.py`

#### Your Own Batch Processing Tool
- Reference: Transcribe (`/scenarios/transcribe/`)
- Pattern: 8 coordinated modules (SCENARIOS_DOCUMENTATION.md § 2.4)

#### With Defensive Error Handling
- Reference: Web to MD (`/scenarios/web_to_md/`)
- Details: SCENARIOS_DOCUMENTATION.md § 2.5 & 3.3

---

## Key Concepts Explained

### Metacognitive Recipe
**What**: A structured thinking process (not code)
**Why**: Describes HOW to approach problem, not imperative implementation
**Example**: Blog writer's 5-step thinking process
**Learn More**: SCENARIOS_DOCUMENTATION.md § Section 7.3

### State Persistence
**What**: Saving complete pipeline state after every operation
**Why**: Enables resume from any point without data loss
**How**: JSON file with stage tracking
**Learn More**: SCENARIOS_DOCUMENTATION.md § Section 3.1, Pattern 2

### Modular Design (Bricks & Studs)
**What**: Self-contained modules with clear contracts
**Why**: Each module can be understood and modified independently
**Size**: 150-250 lines per module
**Learn More**: SCENARIOS_DOCUMENTATION.md § Section 3.1, Pattern 1 & `ai_context/MODULAR_DESIGN_PHILOSOPHY.md`

### Production Experimental Status
**What**: Code works and implements solid patterns
**Why**: Tools are useful NOW but may evolve
**Important**: Safe to use and build on top of
**Learn More**: SCENARIOS_DOCUMENTATION.md § Section 5.3

### Maturity Model Positioning
**Position**: Between `ai_working/` (exploration) and `amplifier/` (core)
**Meaning**: Real tools that work, learning exemplars, research starting point
**Learn More**: SCENARIOS_DOCUMENTATION.md § Section 5

---

## Cross-References to Other Documentation

### Amplifier Project Philosophy
- `CLAUDE.md` - Project instructions (includes scenario guidance)
- `AGENTS.md` - AI assistant guidance
- `ai_context/IMPLEMENTATION_PHILOSOPHY.md` - Design philosophy
- `ai_context/MODULAR_DESIGN_PHILOSOPHY.md` - Modular approach
- `ai_context/DESIGN-PHILOSOPHY.md` - Design system philosophy

### Lessons Learned
- `DISCOVERIES.md` - Includes defensive patterns used by all scenarios

### Related Systems
- `amplifier/` - Core infrastructure that scenarios depend on
- `ai_working/` - Exploration and research (precursor to scenarios)

---

## Quick Reference Tables

### Scenario Complexity Progression
| Level | Scenario | Reason |
|-------|----------|--------|
| 1 - Start Here | tips_synthesizer | Monolithic, simple flow |
| 2 - Next | blog_writer | Modular, showcases patterns |
| 3 - Advanced | article_illustrator | Multi-API coordination |
| 4 - Hard | web_to_md | Defensive programming |
| 5 - Expert | transcribe | 8-module orchestration |

### File Sizes
| File | Size | Best For |
|------|------|----------|
| SCENARIOS_SUMMARY.md | 6KB | Quick overview |
| SCENARIOS_DOCUMENTATION.md | 53KB | Complete reference |
| blog_writer README.md | ~10KB | Understanding one scenario |
| blog_writer HOW_TO_CREATE_YOUR_OWN.md | ~8KB | Learning the recipe |

### Learning Time Estimates
| Goal | Time | Resources |
|------|------|-----------|
| Overview | 5 min | SCENARIOS_SUMMARY.md |
| One scenario | 30 min | README + quick code review |
| Blog writer deep dive | 2 hours | README + HOW_TO + code study |
| Create your own | Full day | All above + experimentation |
| Master system | 3-5 days | Study all scenarios in order |

---

## Navigation By Scenario

### Blog Writer Ecosystem
```
/scenarios/blog_writer/
├── README.md ..................... What it does, how to use
├── HOW_TO_CREATE_YOUR_OWN.md ..... How this tool was made (ESSENTIAL)
├── main.py (452 LOC) ............. Pipeline orchestration (STUDY THIS)
├── state.py (215 LOC) ............ State persistence (STUDY THIS)
├── blog_writer/ .................. Writing engine module
├── style_extractor/ .............. Style analysis module
├── source_reviewer/ .............. Accuracy validation module
├── style_reviewer/ ............... Voice consistency module
├── user_feedback/ ................ User interaction module
└── tests/ ........................ Example inputs & outputs

Documentation:
- SCENARIOS_DOCUMENTATION.md § Section 2.1 (Blog Writer Overview)
- SCENARIOS_DOCUMENTATION.md § Section 4 (Complete Analysis)
```

### Other Scenarios
Similar structure for each:
- `/scenarios/tips_synthesizer/` - Simpler pattern
- `/scenarios/article_illustrator/` - Multi-API pattern
- `/scenarios/transcribe/` - Large-scale pattern
- `/scenarios/web_to_md/` - Defensive pattern

---

## Where to Find Specific Information

**How state persistence works**: 
- Quick: SCENARIOS_SUMMARY.md § "Architecture Patterns"
- Detailed: SCENARIOS_DOCUMENTATION.md § "Pattern 2: State Persistence"
- Code: `/scenarios/blog_writer/state.py`

**How to create a tool like blog_writer**:
- Start: `/scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md`
- Theory: SCENARIOS_DOCUMENTATION.md § Section 10

**How multi-API coordination works**:
- Code: `/scenarios/article_illustrator/image_generation/clients.py`
- Overview: SCENARIOS_DOCUMENTATION.md § Section 2.3

**How batch processing works**:
- Code: `/scenarios/transcribe/` (8 modules)
- Analysis: SCENARIOS_DOCUMENTATION.md § Section 2.4

**How error handling works**:
- Code: `/scenarios/web_to_md/validator/core.py`
- Philosophy: SCENARIOS_DOCUMENTATION.md § Section 3.3

---

## Next Steps

1. **Orient yourself** (5 min)
   - Read SCENARIOS_SUMMARY.md

2. **Pick a scenario** (2 min)
   - Use complexity guide above

3. **Read its documentation** (20 min)
   - README.md → HOW_TO_CREATE_YOUR_OWN.md

4. **Study the code** (1-2 hours)
   - Recommended order in blog_writer subsection

5. **Try running it** (30 min)
   - Use sample data in tests/ directories

6. **Consider creating your own** (ongoing)
   - Use the metacognitive recipe approach

---

**Total Documentation**: 1,827 lines across 2 files
**Scenarios Documented**: 5 (all production-ready)
**Architecture Patterns Explained**: 8 cross-cutting
**Code Examples**: 20+
**Learning Paths**: 6 different approaches

