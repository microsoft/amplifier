# Pragmatic Aider Workflow for Amplifier

A realistic approach to AI-powered code improvement that works with current tools.

## What We Can Actually Do Today

### Phase 0: Health Telemetry (✅ Implemented)

Monitor code health without changing anything:

```bash
# Scan current codebase
python amplifier/tools/health_monitor.py amplifier/

# Show modules needing attention
python amplifier/tools/health_monitor.py --heal

# Example output:
# Modules needing healing (threshold: 70):
#   complex_module.py
#     Health: 45.2
#     Issues: complexity=25, loc=450
```

### Phase 0.5: Controlled Regeneration (✅ Implemented)

Regenerate specific modules with validation:

```bash
# Manual regeneration with Aider
python amplifier/tools/aider_regenerator.py \
    amplifier/complex_module.py \
    --philosophy zen

# Semi-automated healing
python amplifier/tools/simple_healer.py --heal --max 1 --dry-run

# With validation
python amplifier/tools/simple_healer.py --heal --max 1
# Automatically runs: make check
```

## Realistic Workflow

### 1. Daily Health Check

```bash
# Morning scan
python amplifier/tools/health_monitor.py --heal

# If issues found, review candidates
python amplifier/tools/simple_healer.py --scan
```

### 2. Targeted Healing

```bash
# Heal one module at a time
python amplifier/tools/simple_healer.py --heal --max 1

# Review changes
git diff

# If good, commit
git commit -m "heal: Simplify module_name.py"

# If bad, revert
git checkout -- module_name.py
```

### 3. Safe Experimentation

```bash
# Create healing branch
git checkout -b healing/experiment

# Try healing multiple modules
python amplifier/tools/simple_healer.py --heal --max 3

# Test thoroughly
make check
make test

# If successful, merge
git checkout main
git merge healing/experiment
```

## What Makes This Pragmatic

### ✅ Works Today
- Uses existing Aider installation
- Integrates with make check
- Simple health metrics (complexity, LOC)
- Git-based safety (branch, test, merge)

### ✅ Minimal Risk
- One module at a time
- Dry-run mode for preview
- Validation before accepting changes
- Easy rollback with git

### ✅ Observable
- Health scores tracked in `.data/module_health.json`
- Healing attempts logged in `.data/healing_log.json`
- Clear before/after metrics

### ✅ Gradual Adoption
- Start with utility modules
- Build confidence with successes
- Expand to core modules later
- Learn what works

## Near-Term Improvements (Weeks 1-2)

### 1. Better Health Metrics
```python
# Add to health_monitor.py:
- Import coupling analysis
- Test coverage integration
- Performance benchmarks
```

### 2. Smarter Healing Prompts
```python
# Context-aware prompts:
- Include module purpose from docstrings
- Reference successful patterns from healthy modules
- Specify contracts to preserve
```

### 3. Batch Safety
```python
# Parallel healing with isolation:
- Create branch per module
- Validate independently
- Merge successful healings
- Report on failures
```

## Medium-Term Vision (Weeks 3-4)

### Knowledge-Informed Healing
```python
# Learn from successes:
patterns = analyze_successful_healings()
prompt = build_prompt_with_patterns(patterns)
```

### Proactive Monitoring
```python
# CI integration:
# .github/workflows/health-check.yml
- Run health monitor on PRs
- Flag degrading modules
- Suggest healing before merge
```

### Evolution Experiments
```python
# Safe experimentation:
for philosophy in ['zen', 'modular', 'fractalized']:
    branch = heal_with_philosophy(module, philosophy)
    results[philosophy] = benchmark(branch)
pick_winner(results)
```

## Metrics That Matter

### Health Improvements
- Average complexity: 25 → 10
- Average LOC per module: 300 → 150
- Type error rate: 5% → 0%
- Test coverage: 60% → 80%

### Process Metrics
- Healing success rate: 70%
- Validation pass rate: 90%
- Time per healing: <2 minutes
- Human intervention rate: 30%

## Anti-Patterns to Avoid

### ❌ Over-Automation
Don't try to heal everything automatically. Start small, build trust.

### ❌ Ignoring Context
Don't regenerate without understanding module purpose and contracts.

### ❌ Batch Failures
Don't heal 10 modules at once. One failure shouldn't block 9 successes.

### ❌ Blind Trust
Don't accept AI changes without validation. Always run tests.

## Getting Started

1. **Install Aider**:
   ```bash
   bash scripts/setup-aider.sh
   export ANTHROPIC_API_KEY='your-key'
   ```

2. **Baseline Health**:
   ```bash
   python amplifier/tools/health_monitor.py
   cat .data/module_health.json | jq '.summary'
   ```

3. **First Healing**:
   ```bash
   # Dry run first
   python amplifier/tools/simple_healer.py --heal --max 1 --dry-run

   # Then real healing
   python amplifier/tools/simple_healer.py --heal --max 1
   ```

4. **Review & Learn**:
   ```bash
   # Check what changed
   git diff

   # Review healing log
   cat .data/healing_log.json | jq '.'

   # Commit if good
   git commit -am "heal: Applied AI improvements"
   ```

## Success Stories

### Example: Complexity Reduction
```python
# Before: complexity=35, loc=400
def process_data(items, config, mode, flags, cache):
    # 400 lines of nested if/else

# After: complexity=8, loc=120
def process_data(items, config):
    # Clear, simple pipeline
    validated = validate_items(items)
    transformed = apply_transforms(validated, config)
    return format_output(transformed)
```

### Example: Test Coverage Improvement
```python
# AI noticed untested edge cases
# Generated focused test cases
# Coverage: 45% → 85%
```

## The Reality

This isn't magic. It's a tool that:
- Finds modules that need attention
- Suggests improvements via AI
- Validates changes work
- Tracks what happened

Start with one module. Build confidence. Scale gradually.

The future of self-healing code starts with pragmatic steps today.