# Amplifier CLI Tool Template

This template provides a starting point for building your own Amplifier CLI Tool following the "Code for Structure, AI for Intelligence" pattern.

## Tool Name: [Your Tool Name]

### Purpose
[Brief description of what your tool does and the problem it solves]

## 1. Problem Analysis

### Core Challenge
[What makes this problem suitable for the Amplifier Pattern?]

### Why Code + AI?
- **Code handles**: [List deterministic, structural aspects]
- **AI handles**: [List creative, analytical, intelligence-requiring aspects]

## 2. Architecture Design

### Component Breakdown

```
┌─────────────────────────────────────────────────────┐
│                  CLI Orchestrator                    │
│  (Python/TypeScript - handles flow & structure)      │
└─────────────────┬───────────────────────────────────┘
                  │
    ┌─────────────┴──────────────┬─────────────────┐
    ▼                            ▼                 ▼
┌──────────┐              ┌──────────┐      ┌──────────┐
│ Analyzer │              │ Processor │      │ Verifier │
│   (AI)   │              │   (AI)    │      │   (AI)   │
└──────────┘              └──────────┘      └──────────┘
                                │
                          ┌─────┴─────┐
                          │  State    │
                          │  Manager  │
                          │  (Code)   │
                          └───────────┘
```

### Core Modules

#### 1. CLI Orchestrator (`cli.py`)
```python
"""
Handles:
- Command-line argument parsing
- Session management
- Pipeline orchestration
- Error handling and retries
"""

import asyncio
from pathlib import Path
from typing import Optional
import typer

app = typer.Typer()

@app.command()
def process(
    input_path: Path,
    output_path: Optional[Path] = None,
    max_iterations: int = 3,
    use_ai: bool = True
):
    """Main entry point for your tool"""
    # Your orchestration logic here
    pass
```

#### 2. State Manager (`state.py`)
```python
"""
Handles:
- Session persistence
- Progress tracking
- Metadata management
- Recovery from interruptions
"""

from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Any, Dict, List

@dataclass
class ProcessingState:
    session_id: str
    current_step: str
    items_processed: int
    items_total: int
    metadata: Dict[str, Any]
    history: List[Dict[str, Any]]

    def save(self, path: Path):
        """Save state after each operation"""
        path.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls, path: Path) -> "ProcessingState":
        """Load previous state for resumption"""
        data = json.loads(path.read_text())
        return cls(**data)
```

#### 3. Analyzer Module (`analyzer.py`)
```python
"""
AI-powered analysis component
"""

async def analyze_input(content: str, context: dict) -> dict:
    """
    Analyze input and identify issues/opportunities

    Returns:
        dict: Analysis results with identified patterns
    """
    # Use Claude/GPT for intelligent analysis
    pass
```

#### 4. Processor Module (`processor.py`)
```python
"""
AI-powered processing component
"""

async def process_item(item: dict, strategy: str) -> dict:
    """
    Process item using selected strategy

    Progressive specialization levels:
    - Level 0: General processing
    - Level 1: Domain-specific processing
    - Level 2: Deep specialization
    - Level 3: Metacognitive intervention
    """
    # Implement progressive specialization
    pass
```

#### 5. Verifier Module (`verifier.py`)
```python
"""
AI-powered quality verification
"""

async def verify_output(original: dict, processed: dict) -> dict:
    """
    Verify processing quality and decide if iteration needed

    Returns:
        dict: Verification results with pass/fail and feedback
    """
    # Quality checks and iteration decisions
    pass
```

## 3. Progressive Specialization Implementation

### Level 0: General Handler
```python
def general_processor(item):
    """Basic processing for all items"""
    # Simple, pattern-based improvements
    pass
```

### Level 1: Domain-Specific Handler
```python
def domain_specific_processor(item, domain_context):
    """Specialized for your specific domain"""
    # Domain-aware processing
    pass
```

### Level 2: Deep Specialization
```python
async def deep_specialist_processor(item, failure_history):
    """AI-powered deep processing for difficult cases"""
    # Use AI for complex cases
    pass
```

### Level 3: Metacognitive Handler
```python
async def metacognitive_processor(item, all_attempts):
    """AI analyzes failures and selects new strategy"""
    # AI decides how to proceed
    pass
```

## 4. Implementation Checklist

### Phase 1: Basic Structure
- [ ] CLI interface with argument parsing
- [ ] Basic input/output handling
- [ ] Simple processing pipeline
- [ ] Error handling

### Phase 2: State Management
- [ ] Session tracking
- [ ] Progress persistence
- [ ] Incremental saves
- [ ] Resume capability

### Phase 3: AI Integration
- [ ] Analyzer component
- [ ] Processor component
- [ ] Verifier component
- [ ] Context management

### Phase 4: Progressive Specialization
- [ ] General handlers
- [ ] Domain-specific handlers
- [ ] Deep specialization
- [ ] Metacognitive layer

### Phase 5: Quality Loops
- [ ] Verification after processing
- [ ] Iteration on failures
- [ ] Feedback incorporation
- [ ] Success metrics

## 5. Key Patterns to Implement

### Incremental Saves
```python
# Save after EVERY item processed
for i, item in enumerate(items):
    result = await process_item(item)
    results.append(result)
    state.items_processed = i + 1
    state.save(state_path)  # Never lose progress
```

### Re-entrant Pipeline
```python
# Support revisions at any stage
if args.revise:
    state = State.load(session_path)
    # Jump back to appropriate stage
    pipeline.resume_from(state.current_step)
```

### Metacognitive Decision Loop
```python
# AI analyzes its own failures
if not verification_passed:
    strategy = await decide_strategy(
        item=item,
        attempts=state.history,
        failures=failure_patterns
    )
    return await process_with_strategy(item, strategy)
```

## 6. Makefile Integration

```makefile
# Add to project Makefile
[tool-name]-process: ## Process input with your tool
	@echo "Processing with [tool-name]..."
	uv run python -m amplifier.[tool_name].cli process \
		--input "$(INPUT)" \
		--output "$(OUTPUT)" \
		$(if $(MAX_ITER),--max-iterations $(MAX_ITER),) \
		$(if $(NO_AI),--no-ai,)

[tool-name]-analyze: ## Analyze input without processing
	@echo "Analyzing with [tool-name]..."
	uv run python -m amplifier.[tool_name].cli analyze "$(INPUT)"

[tool-name]-resume: ## Resume interrupted session
	@echo "Resuming session: $(SESSION)"
	uv run python -m amplifier.[tool_name].cli resume "$(SESSION)"
```

## 7. Testing Strategy

### Unit Tests
```python
# Test deterministic code components
def test_state_persistence():
    """Test state saves and loads correctly"""
    pass

def test_pipeline_flow():
    """Test orchestration logic"""
    pass
```

### Integration Tests
```python
# Test AI components with mocked responses
async def test_analyzer_integration():
    """Test analyzer with sample inputs"""
    pass
```

### Quality Metrics
```python
# Define success criteria
QUALITY_THRESHOLDS = {
    "min_improvement_score": 0.8,
    "max_iterations": 3,
    "success_rate": 0.95
}
```

## 8. Documentation Template

### README.md
```markdown
# [Tool Name]

An Amplifier CLI Tool for [purpose].

## Features
- Progressive specialization for handling edge cases
- Incremental progress saving
- Metacognitive self-improvement
- Quality verification loops

## Installation
```bash
make install
```

## Usage
```bash
# Basic processing
make [tool-name]-process INPUT=data.txt

# With custom settings
make [tool-name]-process INPUT=data.txt MAX_ITER=5 OUTPUT=results/
```

## Architecture
[Link to architecture diagram]

## How It Works
1. Analyzes input to identify patterns
2. Processes using appropriate specialization level
3. Verifies quality of output
4. Iterates if needed with adjusted strategy
5. Saves progress incrementally throughout
```

## 9. Common Pitfalls to Avoid

1. **Don't block on AI failures** - Always have fallback strategies
2. **Save frequently** - After every atomic operation
3. **Keep AI tasks focused** - Smaller tasks = better results
4. **Preserve context** - Pass relevant history to AI
5. **Design for interruption** - User should be able to stop/resume
6. **Version your strategies** - Track what worked/failed

## 10. Next Steps

1. **Identify your problem domain** - What needs structure vs intelligence?
2. **Design your pipeline** - Map out the processing stages
3. **Start simple** - Build basic CLI first, add AI progressively
4. **Measure quality** - Define success metrics early
5. **Iterate based on results** - Let failures guide specialization

## Resources

- [Amplifier Pattern Guide](./AMPLIFIER_PATTERN_GUIDE.md)
- [Metacognitive Patterns](./METACOGNITIVE_PATTERNS.md)
- [Example: Slides Quality Tool](../amplifier/slides_quality/)
- [Philosophy Documents](./IMPLEMENTATION_PHILOSOPHY.md)

---

This template provides the foundation for building your own Amplifier CLI Tool. Remember: **Code for Structure, AI for Intelligence**.