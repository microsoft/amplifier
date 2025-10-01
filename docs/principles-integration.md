# AI-First Principles Integration

## Overview

The Amplifier framework now includes comprehensive integration with AI-First Principles, providing tools for knowledge synthesis, search, and application of development best practices. This integration enables teams to leverage 55+ proven principles for AI-driven software development.

## Installation

The principles module is included with the amplifier package:

```bash
# Install amplifier with dependencies
make install
```

## Architecture

The principles integration consists of three main components:

### 1. PrincipleLoader
- Loads and parses principle specifications from markdown files
- Extracts structured metadata (examples, approaches, checklists)
- Provides efficient access to principle content

### 2. PrincipleSearcher
- Advanced search capabilities with multiple filters
- Relationship graph analysis
- Cluster detection for interconnected principles
- Similar principle discovery

### 3. PrincipleSynthesizer
- Context-aware principle recommendations
- Task-specific synthesis
- Implementation roadmap generation
- Coverage analysis for projects

## CLI Usage

### List All Principles

```bash
# List all principles
uv run python -m amplifier.cli.main principles list

# List by category
uv run python -m amplifier.cli.main principles list --category technology

# List only complete specifications
uv run python -m amplifier.cli.main principles list --complete

# Output as JSON
uv run python -m amplifier.cli.main principles list --format json
```

### Search Principles

```bash
# Search by keyword
uv run python -m amplifier.cli.main principles search "testing"

# Search with more context
uv run python -m amplifier.cli.main principles search "error handling" --context 5
```

### Show Specific Principle

```bash
# Display detailed information about a principle
uv run python -m amplifier.cli.main principles show 31
```

### Synthesize for Tasks

```bash
# Get relevant principles for a specific task
uv run python -m amplifier.cli.main principles synthesize "Build a REST API with authentication"

# Detailed output
uv run python -m amplifier.cli.main principles synthesize "Implement caching layer" --format detailed
```

### Generate Implementation Roadmap

```bash
# Create roadmap for implementing specific principles
uv run python -m amplifier.cli.main principles roadmap 7 8 9 26 31 32
```

### Analyze Coverage

```bash
# Analyze which principles are being used in your project
uv run python -m amplifier.cli.main principles coverage 7 8 9 10 11

# Save report to file
uv run python -m amplifier.cli.main principles coverage 7 8 9 --output coverage-report.json
```

### View Statistics

```bash
# Get comprehensive statistics about the principles library
uv run python -m amplifier.cli.main principles stats
```

### Analyze Connections

```bash
# Analyze relationships for a specific principle
uv run python -m amplifier.cli.main principles connections 31
```

## Python API Usage

### Basic Loading and Search

```python
from amplifier.principles import PrincipleLoader, PrincipleSearcher

# Load principles
loader = PrincipleLoader()

# Get a specific principle
principle = loader.get_principle(31)  # Idempotency by Design
print(f"Title: {principle.title}")
print(f"Category: {principle.category}")
print(f"Related: {principle.related_principles}")

# Search for principles
searcher = PrincipleSearcher(loader)
results = searcher.search(
    query="testing",
    category="process",
    min_examples=5
)
```

### Task-Specific Synthesis

```python
from amplifier.principles import PrincipleSynthesizer

synthesizer = PrincipleSynthesizer()

# Synthesize for a specific task
result = synthesizer.synthesize_for_task(
    "Implement a microservices architecture with event sourcing"
)

print("Relevant principles:", result['relevant_principles'])
print("Recommendations:", result['recommendations'])
print("Implementation order:", result['implementation_order'])
```

### Project Phase Analysis

```python
# Get principles for different project phases
planning_synthesis = synthesizer.synthesize_for_phase("planning")
implementation_synthesis = synthesizer.synthesize_for_phase("implementation")
deployment_synthesis = synthesizer.synthesize_for_phase("deployment")
```

### Coverage Analysis

```python
# Analyze principle coverage in your project
principles_used = [7, 8, 9, 26, 31]  # Track which principles you're following
coverage = synthesizer.analyze_principle_coverage(principles_used)

print(f"Coverage: {coverage['coverage_percentage']:.1f}%")
print(f"Missing critical: {coverage['missing_critical']}")
print(f"Underutilized: {coverage['underutilized_categories']}")
```

### Implementation Roadmap

```python
# Generate a roadmap for adopting principles
target_principles = [1, 2, 3, 7, 8, 9, 26, 31, 32]
roadmap = synthesizer.generate_implementation_roadmap(target_principles)

for phase in roadmap['phases']:
    print(f"\n{phase['name'].upper()} PHASE")
    print(f"Focus: {phase['focus']}")
    for principle in phase['principles']:
        print(f"  - #{principle['number']:02d} {principle['name']}")
```

### Finding Similar Principles

```python
# Find principles similar to a given one
similar = searcher.find_similar(31, max_results=5)
for principle in similar:
    print(f"#{principle.number} - {principle.name}")
```

### Cluster Analysis

```python
# Discover clusters of related principles
clusters = searcher.find_clusters()
for cluster_name, members in clusters.items():
    print(f"{cluster_name}: {members}")
```

## Integration with Development Workflow

### 1. Project Planning

Use the synthesis tools during project kickoff to identify relevant principles:

```python
# During project planning
task = "Build a real-time collaborative editing system"
synthesis = synthesizer.synthesize_for_task(task)

# Get top recommendations
for rec in synthesis['recommendations']:
    print(f"• {rec}")
```

### 2. Code Reviews

Reference principles during code reviews:

```python
# Check if code follows principles
principle_31 = loader.get_principle(31)  # Idempotency
print("Checklist for idempotent operations:")
for item in principle_31.checklist:
    print(f"  [ ] {item}")
```

### 3. Architecture Decisions

Use principles to guide architectural choices:

```python
# Get principles for architecture decisions
arch_principles = loader.get_by_category("technology")
for p in arch_principles:
    if "architecture" in p.name or "design" in p.name:
        print(f"Consider: #{p.number} - {p.title}")
```

### 4. Team Training

Create learning paths for team members:

```python
# Generate a learning path
learning_path = searcher.find_learning_path([1, 7, 20, 38])
print("Recommended learning order:", learning_path)
```

## Advanced Usage

### Custom Principle Sources

```python
from pathlib import Path

# Load principles from custom directory
custom_loader = PrincipleLoader(
    principles_dir=Path("/path/to/custom/principles")
)
```

### Batch Processing

```python
# Process multiple tasks at once
tasks = [
    "Implement authentication",
    "Add caching layer",
    "Setup monitoring",
    "Create CI/CD pipeline"
]

for task in tasks:
    result = synthesizer.synthesize_for_task(task)
    print(f"\n{task}:")
    for p in result['relevant_principles'][:3]:
        print(f"  - #{p['number']}: {p['name']}")
```

### Export for Documentation

```python
import json

# Export principle data for documentation
all_principles = loader.get_all_principles()
export_data = {
    "principles": [p.to_dict() for p in all_principles],
    "statistics": loader.get_statistics(),
    "clusters": searcher.find_clusters()
}

with open("principles-export.json", "w") as f:
    json.dump(export_data, f, indent=2)
```

## Testing

Run the principle integration tests:

```bash
# Run principle tests
uv run pytest tests/test_principles.py -v

# Run with coverage
uv run pytest tests/test_principles.py --cov=amplifier.principles
```

## Best Practices

1. **Start Small**: Begin with a few core principles and expand gradually
2. **Track Usage**: Use coverage analysis to monitor principle adoption
3. **Team Alignment**: Ensure team understanding before implementing principles
4. **Iterate**: Use the roadmap feature to plan phased implementation
5. **Document Decisions**: Reference principle numbers in code comments and PRs

## Troubleshooting

### Principles Not Loading

If principles aren't loading:
1. Check that the `ai-first-principles` directory exists
2. Verify markdown files follow the naming pattern: `{number}-{name}.md`
3. Ensure files are in the correct category subdirectories

### Search Not Finding Results

If search returns no results:
1. Try broader keywords
2. Check spelling and case sensitivity
3. Use the `--context` flag to see more surrounding text

### Performance Issues

For large principle sets:
1. The searcher builds indices on first load (one-time cost)
2. Consider caching synthesis results for repeated queries
3. Use filtered searches to reduce result sets

## Contributing

To add new principles:

1. Create a markdown file following the template
2. Place in the appropriate category directory
3. Run validation: `python tools/principle_builder.py validate {number}`
4. Update cross-references in related principles

## Principle Categories

- **People** (1-6): Team formation, human factors
- **Process** (7-19, 53-55): Development workflows, validation
- **Technology** (20-37, 45-52): Technical implementation, tools
- **Governance** (38-44): Compliance, lifecycle management

## References

- [AI-First Principles Repository](../ai-first-principles/)
- [Principle Builder Tool](../ai-first-principles/tools/)
- [Amplifier Documentation](./README.md)