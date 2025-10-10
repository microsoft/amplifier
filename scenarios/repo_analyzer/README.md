# Repository Analyzer: Find Improvement Opportunities Through Comparative Analysis

**Learn from the best to make your code better.**

## The Problem

You want to improve your codebase, but:
- **Don't know where to start** - Which improvements would have the most impact?
- **Missing proven patterns** - What architectural approaches work well in practice?
- **Reinventing wheels** - Solutions already exist in other repositories
- **Philosophy misalignment** - Suggestions that don't fit your project's style

## The Solution

Repository Analyzer is a multi-stage AI pipeline that:

1. **Processes repositories** - Uses `repomix` to create analyzable snapshots
2. **Deep comparative analysis** - Identifies patterns, gaps, and opportunities
3. **Generates proposals** - Creates detailed, actionable improvement plans
4. **Reviews for quality** - Ensures suggestions are grounded, aligned, and complete
5. **Iterates with feedback** - Refines based on your specific needs

**The result**: A prioritized list of improvements tailored to your repository, with implementation guidance.

## Quick Start

**Prerequisites**: Complete the [Amplifier setup instructions](../../README.md#-step-by-step-setup) first.

### Basic Usage

```bash
make repo-analyze \
  SOURCE=path/to/reference/repo \
  TARGET=path/to/your/repo \
  REQUEST="Find architectural improvements and missing features"
```

The tool will:
1. Process both repositories with `repomix`
2. Perform comparative analysis
3. Generate improvement opportunities
4. Review for quality (grounding, philosophy, completeness)
5. Present results for your feedback
6. Iterate based on your input

### Your First Analysis

1. **Choose repositories**:
   - **Source**: A well-architected reference repository
   - **Target**: Your repository to improve

2. **Define your request**:
```bash
REQUEST="Compare authentication patterns and identify security improvements"
# OR
REQUEST="Find opportunities to improve testing and code quality"
# OR
REQUEST="Identify missing features and architectural patterns"
```

3. **Run the analysis**:
```bash
make repo-analyze \
  SOURCE=./reference-app \
  TARGET=./my-app \
  REQUEST="Find architectural improvements"
```

4. **Review results**:
   - Tool presents top opportunities
   - Each with priority, effort estimate, and implementation guidance
   - Review full details in `.data/repo_analyzer/<session>/opportunities.json`

5. **Provide feedback**:
   - `approve` - Accept the analysis
   - `filter` - Filter by priority/category/complexity
   - `refine` - Request specific improvements
   - `focus` - Re-analyze with different focus areas

## Usage Examples

### Basic: Architecture Comparison

```bash
make repo-analyze \
  SOURCE=well-designed-api \
  TARGET=my-api \
  REQUEST="Compare API design patterns and error handling"
```

**What happens**:
- Analyzes both API codebases
- Identifies architectural patterns in source
- Finds gaps in your API
- Generates specific improvements
- Reviews for accuracy and fit

### Advanced: With Focus Areas

```bash
make repo-analyze \
  SOURCE=production-app \
  TARGET=my-app \
  REQUEST="Find improvement opportunities" \
  FOCUS="security,performance,testing"
```

**What happens**:
- Same analysis workflow
- Extra attention to specified areas
- Opportunities prioritized by focus
- Deeper analysis in focus areas

### Filtered File Analysis

```bash
make repo-analyze \
  SOURCE=reference \
  TARGET=my-project \
  REQUEST="Analyze Python architecture" \
  INCLUDE="*.py,src/**/*.py" \
  EXCLUDE="test/**,*.min.js"
```

**What happens**:
- Only processes matching files
- Faster analysis for large repos
- More focused results

### Resume Interrupted Session

```bash
make repo-resume
```

**What happens**:
- Finds most recent session
- Loads saved state
- Continues from exact stopping point
- All context preserved

## How It Works

### The Pipeline

```
Source Repo + Target Repo + Request
            ↓
     [Process with Repomix]
            ↓
     [Comparative Analysis]
            ↓
    [Generate Opportunities]
            ↓
    [Grounding Review] ──→ Check against actual code
            ↓
   [Philosophy Review] ──→ Ensure alignment with target
            ↓
  [Completeness Review] ─→ Verify full coverage
            ↓
     [Human Feedback] ───→ Iterate if needed
            ↓
      Final Results
```

### Key Components

- **Repo Processor**: Converts repositories to analyzable format using `npx repomix@latest`
- **Analysis Engine**: Deep comparative analysis with pattern recognition
- **Opportunity Generator**: Creates detailed, actionable proposals
- **Grounding Reviewer**: Verifies suggestions are based on real code, not assumptions
- **Philosophy Reviewer**: Ensures alignment with target repository's style
- **Completeness Reviewer**: Checks that all aspects are covered
- **State Manager**: Enables interruption and resume at any point

### Quality Through Reviews

Each opportunity goes through three isolated review contexts:

1. **Grounding**: "Is this based on actual code patterns?"
2. **Philosophy**: "Does this fit the target repo's style?"
3. **Completeness**: "Did we cover everything requested?"

This prevents hallucinated suggestions and ensures practical value.

## Output Format

Results are saved as structured JSON:

```json
{
  "opportunities": [
    {
      "id": "opp_1",
      "title": "Implement centralized error handling",
      "category": "architecture",
      "priority": 9,
      "implementation": {
        "steps": ["Step-by-step guide"],
        "code_examples": ["Concrete examples"],
        "estimated_effort": "days"
      },
      "impact": {
        "benefits": ["Improved maintainability"],
        "risk_level": "low"
      }
    }
  ]
}
```

## Configuration

### Command-Line Options

```bash
# Required
--source PATH          # Source/reference repository
--target PATH          # Target repository to improve  
--request TEXT         # What to analyze

# Optional
--focus TEXT           # Focus areas (multiple allowed)
--include PATTERN      # File patterns to include
--exclude PATTERN      # File patterns to exclude
--output PATH          # Custom output path
--resume              # Resume from saved state
--reset               # Start fresh
--max-iterations N    # Max feedback iterations (default: 3)
--verbose            # Detailed logging
```

### Session Data

All data saved to `.data/repo_analyzer/<timestamp>/`:
- `state.json` - Pipeline state for resume
- `opportunities_iter_N.json` - Results from each iteration
- `source_repo.xml` - Processed source repository
- `target_repo.xml` - Processed target repository

## Troubleshooting

### "npx: command not found"

**Problem**: Node.js/npm not installed.

**Solution**: Install Node.js from https://nodejs.org/

### "repomix@latest not found"

**Problem**: Repomix package unavailable.

**Solution**: The tool will auto-install via npx. Ensure internet connection.

### "Context window exceeded"

**Problem**: Repositories too large for analysis.

**Solution**: Use `--include` and `--exclude` to focus on specific files:
```bash
--include "src/**/*.py" --exclude "test/**,docs/**"
```

### "Analysis seems generic"

**Problem**: Suggestions not specific to your code.

**Solution**: The grounding reviewer should catch this. If not, use the `refine` option to request more specific analysis.

## Advanced Usage

### Custom Review Prompts

Advanced users can customize review behavior by editing prompts in `prompts/` directory. See `prompts/README.md` for details.

### Programmatic Usage

```python
from scenarios.repo_analyzer.state import StateManager
from scenarios.repo_analyzer.pipeline_orchestrator import PipelineOrchestrator

state = StateManager()
pipeline = PipelineOrchestrator(state)

await pipeline.run(
    source_path=Path("./source"),
    target_path=Path("./target"),
    analysis_request="Your request"
)
```

## Learn More

- **[HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md)** - Build your own analysis tool
- **[Amplifier](https://github.com/microsoft/amplifier)** - The framework powering this tool
- **[Blog Writer](../blog_writer/)** - Example of feedback loops in action

## What Makes This Different?

### Multi-Stage Review Process

Unlike single-pass analysis tools, this implements isolated review contexts:
- Each reviewer has no knowledge of previous analysis
- Prevents confirmation bias and hallucination
- Results in more accurate, grounded suggestions

### Implementation Focus

Goes beyond identifying problems:
- Detailed step-by-step implementation guides
- Code examples from actual patterns
- Effort and risk estimates
- Success validation criteria

### Feedback Loops

Not just one-shot analysis:
- Iterate based on your specific needs
- Filter, refine, or refocus analysis
- Maximum 3 iterations to prevent endless loops
- Each iteration builds on previous learning

## Examples of Opportunities You Might Find

- **Architecture**: "Add service layer between controllers and database"
- **Testing**: "Implement snapshot testing for React components"
- **Performance**: "Add caching layer for expensive computations"
- **Security**: "Implement rate limiting on API endpoints"
- **Code Quality**: "Extract shared utilities into dedicated module"
- **Features**: "Add pagination to list endpoints like in source repo"

Each with detailed implementation guidance based on proven patterns from the source repository.

---

**Built with Amplifier** - This tool demonstrates AI-orchestrated analysis with human-in-the-loop feedback. See [HOW_TO_CREATE_YOUR_OWN.md](./HOW_TO_CREATE_YOUR_OWN.md) for creating similar tools.
