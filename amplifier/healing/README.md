# Amplifier Self-Healing System

## Overview

The Self-Healing System is an automated code quality improvement framework that uses AI-powered refactoring to continuously improve code health. It monitors, analyzes, and heals Python modules using configurable strategies and safety controls.

## Architecture

```
amplifier/healing/
├── core/               # Core healing functionality
│   ├── health_monitor.py    # Module health analysis
│   ├── auto_healer.py       # Automated healing orchestration
│   └── validators.py        # Safety validation
├── prompts/           # AI prompt generation
│   ├── aggressive.py        # High-impact refactoring prompts
│   ├── zen.py              # Simplicity-focused prompts
│   └── decoupling.py       # Dependency reduction prompts
├── analysis/          # Code analysis tools
│   ├── coupling.py         # Dependency analysis
│   └── complexity.py       # Complexity metrics
├── experiments/       # Advanced healing strategies
│   ├── evolution.py        # Multi-variant competition
│   └── parallel.py         # Concurrent healing
└── runtime/           # Runtime data (gitignored)
    ├── logs/               # Healing logs
    ├── results/            # Healing results
    └── cache/              # Knowledge cache
```

## Core Concepts

### 1. Health Monitoring
Continuously monitors module health using metrics:
- **Cyclomatic Complexity**: Target < 10 per function
- **Lines of Code**: Target < 150 per module
- **Type Errors**: Target 0
- **Health Score**: 0-100 scale (70+ is healthy)

### 2. Healing Strategies

#### Aggressive Healing
For modules with health < 50:
- Demands 70% complexity reduction
- Enforces max 20 lines per function
- Eliminates nested conditionals > 2 levels

#### Zen Philosophy
For moderate issues:
- Ruthless simplification
- "Code that isn't there has no bugs"
- Prefer deletion over refactoring

#### Decoupling Strategy
For highly coupled modules:
- Dependency injection
- Interface extraction
- Event-based communication

### 3. Safety Controls

- **Git Branch Isolation**: All healing in separate branches
- **Validation Pipeline**: Syntax, imports, types, tests
- **Safe Module Filtering**: Only heals low-risk modules
- **Rollback on Failure**: Automatic reversion

### 4. Evolution Experiments

Generates multiple variants using different philosophies:
- **Performance**: Optimization-focused
- **Functional**: Pure functions, immutability
- **Modular**: Single responsibility
- **Zen**: Ultimate simplicity

Tournament selection determines the best variant.

## Quick Start

### Basic Health Check
```python
from amplifier.healing import HealthMonitor

monitor = HealthMonitor()
health = monitor.analyze_module("path/to/module.py")
print(f"Health: {health.health_score}/100")
```

### Auto-Heal Modules
```python
from amplifier.healing import AutoHealer

healer = AutoHealer()
results = healer.heal_batch(max_modules=3, threshold=70)
```

### Run Evolution Experiments
```python
from amplifier.healing import EvolutionExperiments

evolver = EvolutionExperiments()
winner = evolver.evolve_module("module.py", philosophies=["zen", "performance"])
```

## CLI Usage

### Monitor Health
```bash
python -m amplifier.healing.monitor path/to/code/
```

### Heal Modules
```bash
python -m amplifier.healing.heal --max 5 --threshold 60
```

### Run Evolution
```bash
python -m amplifier.healing.evolve module.py --philosophies zen functional
```

## Configuration

### Environment Variables
```bash
# Required for AI healing
ANTHROPIC_API_KEY=your-api-key

# Optional configuration
HEALING_TIMEOUT=300  # Seconds per module
HEALING_MAX_WORKERS=3  # Parallel healing workers
```

### Safety Patterns
Configure in `healing_config.yaml`:
```yaml
safe_patterns:
  - "**/utils/*.py"
  - "**/tools/*.py"
  - "**/test_*.py"

unsafe_patterns:
  - "**/core.py"
  - "**/cli.py"
  - "**/__init__.py"
```

## Metrics & Results

### Success Metrics
- **Health Improvement**: Average +25 points
- **Complexity Reduction**: Average -70%
- **LOC Reduction**: Average -60%
- **Success Rate**: ~60% (with proper prompts)

### Performance
- **Health Scan**: ~0.3s for 14 modules
- **Single Healing**: 30-300s depending on complexity
- **Evolution Tournament**: ~30s for 4 variants
- **Parallel Healing**: 3x faster with 3 workers

## Philosophy

The healing system follows Amplifier's core philosophies:

1. **Ruthless Simplicity**: Every line must justify its existence
2. **Bricks & Studs**: Modular components with clean interfaces
3. **Measure First**: Data-driven healing decisions
4. **Safe Experimentation**: Isolated branches, validation, rollback

## Advanced Features

### Coupling Analysis
```python
from amplifier.healing.analysis import CouplingAnalyzer

analyzer = CouplingAnalyzer()
metrics = analyzer.analyze_coupling("module.py")
strategy = analyzer.generate_decoupling_strategy(metrics)
```

### Custom Prompts
```python
from amplifier.healing.prompts import PromptGenerator

generator = PromptGenerator()
prompt = generator.create_custom(
    philosophy="aggressive",
    targets={"complexity": 10, "loc": 100}
)
```

### Knowledge Accumulation
The system learns from successful healings:
```python
healer.knowledge_base.add_pattern(
    "complexity_reduction",
    "Replaced nested if with guard clauses"
)
```

## Troubleshooting

### Common Issues

1. **Insufficient Improvement**
   - Use more aggressive prompts
   - Increase timeout to 300+ seconds
   - Target specific metrics

2. **Validation Failures**
   - Check test coverage
   - Verify import paths
   - Review type annotations

3. **API Rate Limits**
   - Reduce parallel workers
   - Add retry logic
   - Use caching

## Contributing

See [CONTRIBUTING.md](../../docs/contributing/healing.md) for guidelines on:
- Adding new healing strategies
- Creating custom prompts
- Improving validation
- Performance optimization

## License

Part of the Amplifier project. See root LICENSE file.