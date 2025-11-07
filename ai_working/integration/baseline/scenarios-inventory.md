# Amplifier Scenarios Inventory - Baseline

**Generated**: 2025-11-06
**Purpose**: Inventory of all production scenarios in `scenarios/`
**Status**: 5 scenarios documented ✅

---

## Quick Overview

**Total Scenarios**: 5
**Status**: Production-ready experimental (works, may evolve)
**Maturity Position**: Between `ai_working/` (exploration) and `amplifier/` (core)

---

## Complete Inventory

### 1. Blog Writer (THE EXEMPLAR)

**Purpose**: Transforms ideas into blog posts matching author's voice
**Complexity**: Moderate (1,300 LOC, 5 modules + orchestrator)
**Learning Value**: ⭐⭐⭐⭐⭐ (Start here)

**Key Teachings**:
- Orchestration patterns
- State persistence (resume from any point)
- Feedback loops
- Modular design (150-250 lines per module)

**Directory**: `scenarios/blog_writer/`

---

### 2. Tips Synthesizer (SIMPLEST)

**Purpose**: Synthesizes scattered tips into cohesive guides
**Complexity**: Simple (500 LOC, monolithic)
**Learning Value**: ⭐⭐⭐⭐ (Good second scenario)

**Key Teachings**:
- Simplest working scenario
- Good starting point after blog_writer
- Monolithic design pattern

**Directory**: `scenarios/tips_synthesizer/`

---

### 3. Article Illustrator (MULTI-API)

**Purpose**: Generates AI illustrations for articles
**Complexity**: Moderate (1,500 LOC, 4 modules)
**Learning Value**: ⭐⭐⭐

**Key Teachings**:
- API coordination (multiple providers)
- Cost tracking patterns
- Error handling across services

**Directory**: `scenarios/article_illustrator/`

---

### 4. Transcribe (MOST COMPLEX)

**Purpose**: Converts YouTube/audio to searchable transcripts
**Complexity**: High (2,000+ LOC, 8 coordinated modules)
**Learning Value**: ⭐⭐⭐⭐⭐ (Advanced)

**Key Teachings**:
- Large-scale orchestration
- Multi-stage processing
- Defensive programming
- Complex state management

**Directory**: `scenarios/transcribe/`

---

### 5. Web to MD (DEFENSIVE)

**Purpose**: Converts web pages to markdown
**Complexity**: Moderate-High (1,800+ LOC, 8 modules)
**Learning Value**: ⭐⭐⭐⭐

**Key Teachings**:
- Error handling patterns
- Paywall detection
- Content extraction
- Defensive LLM parsing

**Directory**: `scenarios/web_to_md/`

---

## Cross-Cutting Patterns (All Scenarios)

1. **Modular Design**: 150-250 lines per module
2. **State Persistence**: Resume from any point
3. **Async/Await**: For LLM operations
4. **Defensive Parsing**: LLM response handling
5. **Explicit Stages**: Clear stage transitions
6. **CLI Entry Points**: `amplifier <scenario> <args>`
7. **Test Data**: Samples for validation
8. **Complete Documentation**: README, architecture, workflow

---

## Metacognitive Recipe

**Key Insight**: Scenarios built by describing thinking process, not code
- Blog writer created from 5-step thinking process
- Amplifier generated all implementation
- Zero lines of code written by creator

**Example**: "Think like this: 1) Extract key points, 2) Organize structure, 3) Draft, 4) Refine, 5) Polish" → Full working tool generated

---

## Learning Paths

**Beginner** (2-3 hours):
1. Read `scenarios/blog_writer/README.md`
2. Trace code in blog_writer (start with orchestrator)
3. Run sample: `amplifier blog-writer test`

**Intermediate** (1 day):
1. Complete beginner path
2. Study tips_synthesizer (simplest)
3. Compare article_illustrator (API patterns)
4. Identify common patterns

**Advanced** (2-3 days):
1. Complete intermediate
2. Deep dive transcribe (most complex)
3. Study web_to_md (defensive patterns)
4. Create own scenario using learned patterns

---

## File Structure (Typical)

```
scenarios/<name>/
├── README.md           # Overview & usage
├── orchestrator.py     # Main coordination
├── modules/
│   ├── module1.py     # 150-250 lines each
│   ├── module2.py
│   └── ...
├── config.yaml        # Configuration
├── tests/
│   └── test_data/     # Sample inputs
└── examples/          # Usage examples
```

---

**Status**: Complete baseline ✅
**Reference**: Full 30-page detailed report available in agent findings
