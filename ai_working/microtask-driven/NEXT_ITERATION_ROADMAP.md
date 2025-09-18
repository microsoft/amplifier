# Roadmap for Next Iteration: Structured Pipeline Generation

## Quick Start: What to Do Differently

### 1. Start with Structured Specifications (Not Natural Language)

**Instead of**:
```
"Read markdown files, summarize them with AI, then synthesize insights across summaries, then expand ideas using original sources"
```

**Use**:
```yaml
pipeline:
  name: document-insight-processor
  stages:
    - id: summarize
      input: "{source_dir}/*.md"
      processor: ai_summarize
      output: "{temp_dir}/summaries/{filename}.json"
      prompt_template: |
        Summarize this document focusing on key insights:
        {content}

    - id: synthesize
      input: "{temp_dir}/summaries/*.json"
      processor: ai_synthesize
      output: "{temp_dir}/synthesis.json"
      dependencies: [summarize]
      prompt_template: |
        Find patterns across these summaries:
        {all_summaries}

    - id: expand
      input: "{temp_dir}/synthesis.json"
      context: "{source_dir}/*.md"
      processor: ai_expand
      output: "{output_dir}/expanded_ideas.json"
      dependencies: [synthesize]
      prompt_template: |
        Expand this idea using source context:
        Idea: {idea}
        Source: {source_content}
```

### 2. Build the Pipeline Generator First

Before trying to generate tools, build the pipeline infrastructure:

```python
# amplifier_microtask/pipeline_generator.py

class PipelineGenerator:
    """Generates multi-stage pipelines from structured specs"""

    def __init__(self):
        self.stage_templates = self.load_stage_templates()

    def generate_from_spec(self, spec: PipelineSpec) -> str:
        """Generate complete pipeline code from specification"""
        stages = self.build_stages(spec)
        dag = self.build_dependency_graph(stages)
        code = self.generate_pipeline_code(dag)
        tests = self.generate_tests(spec)
        return code, tests

    def build_stages(self, spec: PipelineSpec) -> List[Stage]:
        """Convert spec stages to executable stages"""
        stages = []
        for stage_spec in spec.stages:
            stage = Stage(
                name=stage_spec.id,
                input_pattern=stage_spec.input,
                output_pattern=stage_spec.output,
                processor=self.get_processor(stage_spec.processor),
                dependencies=stage_spec.dependencies
            )
            stages.append(stage)
        return stages

    def generate_pipeline_code(self, dag: DependencyGraph) -> str:
        """Generate Python code for the pipeline"""
        # Use templates to generate clean, working code
        # Each stage gets its own method
        # Proper state management between stages
        # Resume capability built-in
```

### 3. Test-First Generation

Generate tests before implementation:

```python
def generate_tool(spec: ToolSpec):
    # 1. Generate test cases from spec
    test_cases = generate_test_cases(spec)
    test_file = write_tests(test_cases)

    # 2. Run tests (will fail)
    run_tests(test_file)  # Expected: all fail

    # 3. Generate implementation to pass tests
    implementation = generate_implementation_for_tests(spec, test_cases)

    # 4. Run tests again
    results = run_tests(test_file)

    # 5. Iterate until tests pass
    while not all_tests_pass(results):
        implementation = improve_implementation(implementation, results)
        results = run_tests(test_file)

    return implementation
```

### 4. Use Progressive Enhancement

Build complexity gradually:

```python
class ProgressiveGenerator:
    def generate(self, spec: ComplexSpec) -> Tool:
        # Start with simplest version
        v1 = self.generate_single_stage(spec.stages[0])
        self.validate(v1)

        # Add second stage
        v2 = self.add_stage(v1, spec.stages[1])
        self.validate(v2)

        # Add remaining stages
        for stage in spec.stages[2:]:
            v2 = self.add_stage(v2, stage)
            self.validate(v2)

        return v2
```

### 5. Implement Validation Gates

Don't proceed without validation:

```python
class GenerationPipeline:
    def __init__(self):
        self.gates = []

    def add_gate(self, name: str, validator: Callable) -> None:
        self.gates.append((name, validator))

    def process(self, spec: Spec) -> Result:
        artifact = spec

        for gate_name, validator in self.gates:
            # Transform artifact
            artifact = self.transform(artifact)

            # Validate before proceeding
            is_valid, errors = validator(artifact)
            if not is_valid:
                self.report_failure(gate_name, errors)
                raise ValidationError(f"Failed at {gate_name}: {errors}")

            self.report_success(gate_name)

        return artifact

# Usage
pipeline = GenerationPipeline()
pipeline.add_gate("requirements", validate_requirements_extracted)
pipeline.add_gate("design", validate_design_complete)
pipeline.add_gate("code", validate_code_matches_design)
pipeline.add_gate("tests", validate_tests_pass)
```

## Architecture for Success

### Core Components Needed

```
amplifier_microtask_v2/
├── core/
│   ├── pipeline_spec.py       # Structured spec definitions
│   ├── stage_processor.py      # Stage execution engine
│   ├── dag_builder.py          # Dependency graph builder
│   └── validator.py            # Progressive validation
│
├── generators/
│   ├── test_generator.py       # Test-first generation
│   ├── code_generator.py       # Implementation generation
│   ├── pipeline_generator.py   # Multi-stage pipeline generation
│   └── template_engine.py      # Code template system
│
├── templates/
│   ├── stage_templates/        # Templates for different stage types
│   ├── test_templates/         # Test generation templates
│   └── pipeline_templates/     # Complete pipeline templates
│
├── monitoring/
│   ├── progress_monitor.py     # (Keep from v1)
│   ├── timeout_manager.py      # (Enhanced from v1)
│   └── state_tracker.py        # Stage state management
│
└── validation/
    ├── requirements_validator.py
    ├── design_validator.py
    ├── code_validator.py
    └── test_validator.py
```

### Key Design Decisions

1. **Structured Specs Over Natural Language**
   - Use YAML/JSON for pipeline definitions
   - Natural language only for AI prompts within stages

2. **Explicit Stage Contracts**
   - Each stage declares inputs/outputs
   - Type checking between stages
   - No implicit data flow

3. **Template-Based Generation**
   - Pre-built templates for common patterns
   - Composition over generation
   - Predictable output structure

4. **Validation-Driven Progress**
   - Cannot proceed without passing validation
   - Each gate catches specific issues
   - Clear error reporting at each stage

## Reusable Components from V1

### Definitely Keep:
1. **progress_monitor.py** - File-based monitoring works great
2. **Adaptive timeout logic** - The calculation formula is solid
3. **Philosophy context injection** - Helps with code quality
4. **File-based state management** - Robust against failures

### Improve and Keep:
1. **Validation framework** - Good structure, needs integration
2. **Resume capability** - Works but needs stage awareness
3. **Error handling patterns** - Add stage context

### Replace Completely:
1. **Natural language DESC parsing** - Use structured specs
2. **Single-stage assumption** - Build for multi-stage from start
3. **Flat requirements extraction** - Preserve structure

## Success Metrics for V2

### Must Have:
- [ ] Generate working 4-stage pipeline from spec
- [ ] Each stage validates independently
- [ ] Cross-stage data flow works correctly
- [ ] Generated tests pass
- [ ] Resume from any stage

### Should Have:
- [ ] Parallel stage execution where possible
- [ ] Clear progress reporting
- [ ] Helpful error messages
- [ ] Efficient re-generation

### Nice to Have:
- [ ] Visual DAG representation
- [ ] Stage performance metrics
- [ ] Automatic optimization suggestions
- [ ] Multiple implementation strategies

## Implementation Order

### Phase 1: Foundation (Week 1)
1. Define structured spec format
2. Build stage processor engine
3. Create validation framework
4. Test with manual specs

### Phase 2: Generation (Week 2)
1. Build template engine
2. Create code generator
3. Implement test generator
4. Test with simple pipelines

### Phase 3: Complex Pipelines (Week 3)
1. Build DAG processor
2. Handle stage dependencies
3. Add cross-stage validation
4. Test with document-insight pipeline

### Phase 4: Polish (Week 4)
1. Improve error messages
2. Add progress visualization
3. Optimize performance
4. Document patterns

## Example: Document Insight Pipeline V2

Here's how the problematic document-insight-pipeline would work in V2:

```python
# Generated code structure
class DocumentInsightPipeline:
    def __init__(self, source_dir: Path, output_dir: Path):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.temp_dir = output_dir / "temp"
        self.state = PipelineState.load_or_create()

    async def run(self, max_files: int = 5):
        """Execute the complete pipeline"""
        # Stage 1: Summarize
        if not self.state.is_complete("summarize"):
            await self.stage_summarize(max_files)
            self.state.mark_complete("summarize")

        # Stage 2: Synthesize
        if not self.state.is_complete("synthesize"):
            await self.stage_synthesize()
            self.state.mark_complete("synthesize")

        # Stage 3: Expand
        if not self.state.is_complete("expand"):
            await self.stage_expand()
            self.state.mark_complete("expand")

        # Stage 4: Implementation plans
        if not self.state.is_complete("implement"):
            await self.stage_implement()
            self.state.mark_complete("implement")

    async def stage_summarize(self, max_files: int):
        """Stage 1: Summarize each document"""
        summaries_dir = self.temp_dir / "summaries"
        summaries_dir.mkdir(parents=True, exist_ok=True)

        for md_file in list(self.source_dir.glob("*.md"))[:max_files]:
            if self.state.is_processed("summarize", md_file):
                continue

            summary = await self.ai_summarize(md_file.read_text())
            output_file = summaries_dir / f"{md_file.stem}.json"
            output_file.write_text(json.dumps(summary))
            self.state.mark_processed("summarize", md_file)

    async def stage_synthesize(self):
        """Stage 2: Synthesize across summaries"""
        summaries = []
        for summary_file in (self.temp_dir / "summaries").glob("*.json"):
            summaries.append(json.loads(summary_file.read_text()))

        synthesis = await self.ai_synthesize(summaries)
        synthesis_file = self.temp_dir / "synthesis.json"
        synthesis_file.write_text(json.dumps(synthesis))

    async def stage_expand(self):
        """Stage 3: Expand ideas with source context"""
        synthesis = json.loads((self.temp_dir / "synthesis.json").read_text())
        expanded = []

        for idea in synthesis["ideas"]:
            source_file = self.source_dir / idea["source"]
            source_content = source_file.read_text()

            expanded_idea = await self.ai_expand(idea, source_content)
            expanded.append(expanded_idea)

        expanded_file = self.temp_dir / "expanded.json"
        expanded_file.write_text(json.dumps(expanded))

    async def stage_implement(self):
        """Stage 4: Generate implementation plans"""
        expanded = json.loads((self.temp_dir / "expanded.json").read_text())
        plans = []

        for idea in expanded:
            plan = await self.ai_implement(idea)
            plans.append(plan)

        output_file = self.output_dir / "implementation_plans.json"
        output_file.write_text(json.dumps(plans))
```

## Closing Thoughts

The V1 experiment taught us that:
1. Complex requirements need structure, not interpretation
2. Validation must be progressive, not final
3. Stage boundaries must be explicit, not implicit
4. File-based state management is robust
5. Adaptive timeouts are essential

V2 should be a synthesis of these lessons, building on what worked while replacing what didn't. The key insight is that **we're not building a code generator, we're building a pipeline generator** - and pipelines need structure.

---

*This roadmap provides a concrete path forward based on lessons learned from the microtask-driven experiment. Following this approach should yield a working multi-stage pipeline generator.*