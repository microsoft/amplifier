# Principle Builder Tool

CLI tool for creating, validating, and managing AI-first principle specifications.

## Installation

The tool is standalone Python and requires no additional dependencies beyond Python 3.11+.

```bash
cd ai-first-principles
python3 tools/principle_builder.py --help
```

## Usage

### List All Principles

```bash
# List all principles
python3 tools/principle_builder.py list

# List by category
python3 tools/principle_builder.py list --category technology

# List only complete specifications
python3 tools/principle_builder.py list --status complete
```

**Example Output:**
```
📋 Found 44 principles:

✅ #01 - small-ai-first-working-groups (people)
✅ #02 - strategic-human-touchpoints (people)
...
```

### Validate a Principle

Check if a principle specification meets structural requirements:

```bash
python3 tools/principle_builder.py validate 31
```

**Example Output:**
```
✅ Principle #31 is valid

⚠️  Warnings:
  - Only 5 examples found, should have 5
```

### Check Quality

Perform comprehensive quality check with scoring:

```bash
python3 tools/principle_builder.py check-quality 31
```

**Example Output:**
```
🎯 Quality Check for Principle #31:
Score: 100.0%

Checks:
  ✅ Structure
  ✅ Examples
  ✅ Code Blocks
  ✅ Related Principles
  ✅ Checklist Items
  ✅ Common Pitfalls
  ✅ Tools Section
  ✅ Metadata Complete
```

### Update Progress Statistics

Scan all specifications and show completion statistics:

```bash
python3 tools/principle_builder.py update-progress
```

**Example Output:**
```
📊 Progress Update:
✅ 44/44 specifications complete (100.0%)

By category:
  People: 6/6
  Process: 13/13
  Technology: 18/18
  Governance: 7/7
```

### Create a New Principle Stub

Generate a new specification from the template:

```bash
# Create principle #45 (if extending the library)
python3 tools/principle_builder.py create 45 "new-principle-name"

# Create with explicit category
python3 tools/principle_builder.py create 45 "new-principle-name" --category governance
```

**Note:** The tool automatically determines category based on principle number ranges:
- People: 1-6
- Process: 7-19
- Technology: 20-37
- Governance: 38-44

## Quality Checks

The tool validates specifications against quality standards:

### Required Sections
- Plain-Language Definition
- Why This Matters for AI-First Development
- Implementation Approaches
- Good Examples vs Bad Examples (5 pairs minimum)
- Related Principles (6 minimum)
- Common Pitfalls (5-7 recommended)
- Tools & Frameworks
- Implementation Checklist (8-12 items)
- Metadata (complete)

### Quality Scoring

The `check-quality` command scores specifications on:
- **Structure**: All required sections present
- **Examples**: At least 5 example pairs
- **Code Blocks**: At least 10 code blocks (good/bad pairs)
- **Related Principles**: At least 6 cross-references
- **Checklist Items**: At least 8 actionable items
- **Common Pitfalls**: At least 5 documented
- **Tools Section**: Properly organized by category
- **Metadata**: Complete with category, number, status

## Workflow

### Adding a New Principle

1. **Create Stub**:
   ```bash
   python3 tools/principle_builder.py create 45 "new-principle-name"
   ```

2. **Edit Specification**:
   - Open the created file
   - Fill in all sections following `TEMPLATE.md`
   - Use `#31-idempotency-by-design.md` as quality reference

3. **Validate**:
   ```bash
   python3 tools/principle_builder.py validate 45
   ```

4. **Check Quality**:
   ```bash
   python3 tools/principle_builder.py check-quality 45
   ```

5. **Update Progress**:
   ```bash
   python3 tools/principle_builder.py update-progress
   ```

### Maintaining Existing Principles

1. **List specifications by status**:
   ```bash
   python3 tools/principle_builder.py list --status incomplete
   ```

2. **Validate all complete specs**:
   ```bash
   for i in {1..44}; do
     python3 tools/principle_builder.py validate $i
   done
   ```

3. **Quality check high-priority specs**:
   ```bash
   for i in 7 8 9 26 31 32; do
     python3 tools/principle_builder.py check-quality $i
   done
   ```

## Integration with Development Workflow

### Pre-Commit Hook

Add validation to your git pre-commit hook:

```bash
# .git/hooks/pre-commit
#!/bin/bash
cd ai-first-principles
for file in $(git diff --cached --name-only | grep 'principles/.*\.md$'); do
  number=$(basename "$file" | cut -d'-' -f1)
  python3 tools/principle_builder.py validate $number || exit 1
done
```

### CI/CD Integration

Include quality checks in CI pipeline:

```yaml
# .github/workflows/principles-quality.yml
name: Principles Quality Check
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate all principles
        run: |
          cd ai-first-principles
          for i in {1..44}; do
            python3 tools/principle_builder.py validate $i
          done
```

## Principles Demonstrated

This tool demonstrates several AI-first principles:

- **#28 CLI-First Design**: Command-line interface as primary interaction
- **#29 Tool Ecosystems as Extensions**: Extends the principles library with tooling
- **#25 Simple Interfaces by Design**: Clear, focused commands
- **#31 Idempotency by Design**: Validation is idempotent
- **#09 Tests as Quality Gate**: Quality checks validate specifications
- **#16 Docs Define, Not Describe**: Template defines what specs should contain
- **#37 Declarative Over Imperative**: Declare what to validate, not how

### Search for Principles

Find relevant principles based on keywords, concepts, or relationships:

```bash
# Search for principles mentioning "test"
python3 tools/principle_search.py keyword test

# Search with more context lines
python3 tools/principle_search.py keyword "error handling" --context 5

# Search for principles related to multiple concepts
python3 tools/principle_search.py concepts "error handling" "recovery" "resilience"

# Find principles related to principle #31
python3 tools/principle_search.py related 31

# List all technology principles
python3 tools/principle_search.py category technology

# Search for principles with specific code patterns
python3 tools/principle_search.py examples "async def"
```

**Search Modes:**
- **keyword**: Find principles containing specific terms with context
- **concepts**: Search for principles related to multiple concepts (ranked by relevance)
- **related**: Discover principles cross-referenced by a specific principle
- **category**: List all principles in a category (people/process/technology/governance)
- **examples**: Find principles with specific code patterns in examples

## Future Enhancements

Potential additions:
- Generate cross-reference index automatically
- Export specifications to different formats (PDF, HTML)
- Dependency graph visualization
- Automated quality report generation
- Integration with AI agents for spec completion
- Batch operations for bulk validation/quality checks

## Contributing

When extending this tool:
1. Follow the existing command structure
2. Add tests for new functionality
3. Update this README with new commands
4. Ensure tool remains dependency-free (stdlib only)
5. Keep CLI output clear and actionable