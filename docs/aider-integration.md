# Aider Integration for Amplifier

Amplifier now includes deep integration with [Aider](https://aider.chat/), an AI-powered code generation and regeneration tool. This integration enables automatic module regeneration following the Amplifier philosophies (Fractalized Thinking, Modular Design, and Zen Architecture).

## Installation

Aider is installed in a separate virtual environment to avoid dependency conflicts:

```bash
# Run the setup script
./scripts/setup-aider.sh

# Or use the Amplifier CLI
amplifier aider setup
```

## Usage

### CLI Commands

The Amplifier CLI provides several Aider commands:

#### Status Check

```bash
# Check Aider installation status
amplifier aider status

# Verbose status with version info
amplifier aider status --verbose
```

#### Regenerate a Single Module

```bash
# Regenerate with default (fractalized) philosophy
amplifier aider regenerate path/to/module.py

# Use a specific philosophy
amplifier aider regenerate path/to/module.py --philosophy zen

# Include a specification file
amplifier aider regenerate path/to/module.py --spec specs/module_spec.md
```

#### Batch Regeneration

```bash
# Regenerate all modules matching a pattern
amplifier aider batch "amplifier/**/*.py" --philosophy modular

# Dry run to see what would be regenerated
amplifier aider batch "amplifier/**/*.py" --dry-run
```

#### Direct Editing

```bash
# Direct Aider interface for custom edits
amplifier aider edit file1.py file2.py -m "Add error handling"

# Use a different model
amplifier aider edit file.py -m "Optimize performance" --model gpt-4
```

## Philosophy-Based Regeneration

The integration supports three development philosophies:

### 1. Fractalized Thinking (Default)

Based on your personal cognitive style of patient knot-untying:

```bash
amplifier aider regenerate module.py --philosophy fractalized
```

Principles applied:
- Find the smallest thread to start with
- Work patiently from simple to complex
- Recognize patterns that scale fractally
- Build bridges that hold creative tensions

### 2. Modular Design

Following the brick-and-stud philosophy:

```bash
amplifier aider regenerate module.py --philosophy modular
```

Principles applied:
- Keep modules self-contained with clear interfaces
- Maintain stable connection points (studs)
- Enable independent regeneration
- Focus on single responsibility

### 3. Zen Architecture

Embracing ruthless simplicity:

```bash
amplifier aider regenerate module.py --philosophy zen
```

Principles applied:
- Embrace ruthless simplicity
- Remove all unnecessary complexity
- Trust in emergence over control
- Keep code minimal and clear

## Pre-Commit Hook Integration

### Automatic Regeneration

Enable automatic regeneration before commits:

```bash
# Install the pre-commit hook
ln -sf ../../.githooks/pre-commit-aider .git/hooks/pre-commit

# Configure regeneration
export AIDER_REGENERATE=true
export AIDER_PHILOSOPHY=fractalized
export AIDER_AUTO_ADD=true

# Commit with regeneration
git commit -m "Feature: Add new capability"
```

### Configuration Options

Create `.aider-config` for persistent settings:

```bash
# .aider-config
AIDER_REGENERATE=true           # Enable/disable regeneration
AIDER_PHILOSOPHY=fractalized     # Choose philosophy
AIDER_AUTO_ADD=true             # Auto-stage regenerated files
```

### Per-Commit Control

Enable for a single commit:

```bash
AIDER_REGENERATE=true git commit -m "Regenerate and commit"
```

## Module Specifications

Place module specifications in `ai_working/module_specs/`:

```markdown
# ai_working/module_specs/my_module_spec.md

## Module Purpose
Clear description of what this module does

## Interface Contract
- Public functions and their signatures
- Expected inputs and outputs
- Error conditions

## Implementation Guidelines
- Key algorithms or patterns to use
- Performance requirements
- Philosophy-specific notes
```

When regenerating, Aider will automatically find and use matching specs:

```bash
# Automatically uses ai_working/module_specs/my_module_spec.md if it exists
amplifier aider regenerate amplifier/my_module.py
```

## Logs and Debugging

All Aider operations are logged:

```bash
# Logs are stored in .aider-logs/
ls -la .aider-logs/

# View recent log
cat .aider-logs/aider_20240126_143022.log
```

## Best Practices

### 1. Start with Specifications

Before regenerating, create clear module specifications:

```bash
# Create spec first
echo "Module specification..." > ai_working/module_specs/module_spec.md

# Then regenerate
amplifier aider regenerate module.py --spec ai_working/module_specs/module_spec.md
```

### 2. Choose Philosophy Appropriately

- **Fractalized**: For complex problems needing patient untangling
- **Modular**: For building reusable, composable components
- **Zen**: For simplifying overly complex code

### 3. Review Generated Code

Always review regenerated code before committing:

```bash
# Regenerate without auto-commit
amplifier aider regenerate module.py

# Review changes
git diff module.py

# Commit if satisfied
git add module.py && git commit
```

### 4. Use Batch Carefully

Test batch regeneration on a subset first:

```bash
# Test on one module
amplifier aider regenerate module1.py

# If good, batch regenerate similar modules
amplifier aider batch "similar_modules/*.py"
```

## Troubleshooting

### Aider Not Found

```bash
# Reinstall Aider
./scripts/setup-aider.sh
```

### Regeneration Fails

Check logs for details:

```bash
# Find recent logs
ls -lt .aider-logs/ | head -5

# View error details
cat .aider-logs/aider_TIMESTAMP.log
```

### Dependency Conflicts

Aider runs in isolated environment, but if issues persist:

```bash
# Clean and reinstall
rm -rf .aider-venv
./scripts/setup-aider.sh
```

## Advanced Usage

### Custom Instructions

Create project-specific regeneration instructions:

```python
# In your module
"""
AIDER_INSTRUCTIONS:
- Maintain compatibility with v2 API
- Use async/await patterns
- Include comprehensive error handling
"""
```

### CI/CD Integration

Add to GitHub Actions:

```yaml
- name: Regenerate modules
  run: |
    ./scripts/setup-aider.sh
    amplifier aider batch "src/**/*.py" --philosophy modular
```

## Philosophy Integration

The Aider integration reads and applies philosophy documents:

- `ai_context/FRACTALIZED_THINKING_PHILOSOPHY.md`
- `ai_context/MODULAR_DESIGN_PHILOSOPHY.md`
- `ai_context/IMPLEMENTATION_PHILOSOPHY.md`

These are automatically included when regenerating modules, ensuring consistent application of chosen philosophies.

## Future Enhancements

Planned improvements:

1. **Parallel Regeneration**: Process multiple modules concurrently
2. **Incremental Regeneration**: Only regenerate changed sections
3. **Philosophy Learning**: Adapt philosophy based on code patterns
4. **Team Synchronization**: Share regeneration patterns across team

## Summary

The Aider integration brings AI-powered code regeneration directly into the Amplifier workflow, allowing you to:

- Regenerate modules following consistent philosophies
- Automate code improvement before commits
- Maintain architectural integrity while evolving code
- Apply your unique cognitive style (fractalized thinking) to code generation

Use it to maintain high code quality while embracing rapid iteration and continuous improvement.