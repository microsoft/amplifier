# Super-Planner Integration Test Setup

Complete setup guide for running comprehensive integration tests of the super-planner system with real amplifier tools and external dependencies.

## Test Environment Setup

### Prerequisites

```bash
# System requirements
- Python 3.11+
- Git 2.30+
- Node.js 18+ (for pyright type checking)
- Docker (for containerized testing)
- 8GB+ RAM (for large project tests)
- 10GB+ disk space (for test data and git repos)
```

### Installation

```bash
# Clone and setup amplifier
git clone https://github.com/microsoft/amplifier.git
cd amplifier

# Install dependencies including test requirements
uv sync --dev

# Verify installation
make check
pytest tests/planner/ --collect-only
```

### Environment Configuration

```bash
# Test environment variables
export PLANNER_TEST_MODE=true
export PLANNER_LOG_LEVEL=INFO
export PLANNER_DATA_DIR=/tmp/planner_test_data
export PLANNER_PERFORMANCE_MODE=false

# Mock service endpoints (for integration tests)
export MOCK_LLM_ENDPOINT=http://localhost:8001
export MOCK_AMPLIFIER_TASK_ENDPOINT=http://localhost:8002
export MOCK_GIT_SERVICE_ENDPOINT=http://localhost:8003

# Real service configuration (for full integration)
export OPENAI_API_KEY=your_api_key_here
export ANTHROPIC_API_KEY=your_api_key_here
```

## Test Execution Guide

### Quick Smoke Test

```bash
# Run basic functionality tests (5 minutes)
pytest tests/planner/unit/ -v --tb=short

# Run core integration tests (15 minutes)
pytest tests/planner/integration/ -v -k "not performance"

# Verify mock implementations work
pytest tests/planner/mocks/ -v
```

### Comprehensive Test Suite

```bash
# Run all tests including performance (60+ minutes)
make test-planner-full

# Run specific test categories
make test-planner-unit          # Unit tests only (5 min)
make test-planner-integration   # Integration tests (30 min)
make test-planner-e2e          # End-to-end tests (45 min)
make test-planner-performance  # Performance benchmarks (30 min)
```

### Test with Real External Services

```bash
# Setup real LLM services
export USE_REAL_LLM=true
export OPENAI_API_KEY=your_key

# Run with real amplifier Task tool
export USE_REAL_AMPLIFIER=true

# Execute integration tests with real services
pytest tests/planner/integration/ -v --real-services
```

## Test Data Management

### Golden Test Data

```bash
tests/planner/test_data/
├── projects/
│   ├── simple_web_app.json           # 8 tasks, 2 levels
│   ├── complex_microservices_platform.json  # 200+ tasks, complex deps
│   └── enterprise_integration.json   # 1000+ tasks, multi-team
├── failure_scenarios/
│   ├── network_partition.json        # Simulated network issues
│   ├── file_corruption.json          # Corrupted task data
│   └── circular_dependencies.json    # Invalid dependency scenarios
└── performance/
    ├── large_project_1000.json       # Performance test data
    ├── stress_test_5000.json         # Stress test scenarios
    └── concurrent_agents_20.json     # Multi-agent test data
```

### Test Data Generation

```bash
# Generate test projects of various sizes
python tests/planner/utils/generate_test_data.py \
  --project-sizes 10,50,100,500 \
  --complexity simple,complex,extreme \
  --output tests/planner/test_data/generated/

# Create failure scenario data
python tests/planner/utils/generate_failure_scenarios.py \
  --scenarios network,corruption,deadlock \
  --output tests/planner/test_data/failure_scenarios/
```

## Mock Service Setup

### Mock LLM Service

```python
# tests/planner/mocks/mock_llm_service.py
class MockLLMService:
    """Mock LLM service for task breakdown testing"""

    def __init__(self, port: int = 8001):
        self.port = port
        self.app = FastAPI()
        self.setup_routes()

    def setup_routes(self):
        @self.app.post("/v1/task/breakdown")
        async def breakdown_task(request: TaskBreakdownRequest):
            # Return realistic task breakdown based on input
            return generate_mock_breakdown(request)

    async def start(self):
        config = uvicorn.Config(self.app, host="127.0.0.1", port=self.port)
        server = uvicorn.Server(config)
        await server.serve()
```

### Mock Git Service

```bash
# Start mock git service for testing git operations
docker run -d \
  --name mock-git-service \
  -p 8003:80 \
  -v $(pwd)/test_repos:/git/repos \
  gitea/gitea:latest
```

### Service Orchestration

```bash
# Start all mock services
docker-compose -f tests/planner/docker/test-services.yml up -d

# Verify services are running
curl http://localhost:8001/health  # Mock LLM
curl http://localhost:8002/health  # Mock Task Tool
curl http://localhost:8003/health  # Mock Git Service

# Run tests with mock services
pytest tests/planner/integration/ -v --use-mock-services

# Cleanup
docker-compose -f tests/planner/docker/test-services.yml down
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/super-planner-tests.yml
name: Super-Planner Tests

on:
  push:
    paths:
    - 'amplifier/planner/**'
    - 'tests/planner/**'
  pull_request:
    paths:
    - 'amplifier/planner/**'
    - 'tests/planner/**'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install uv
        uv sync --dev

    - name: Run unit tests
      run: |
        pytest tests/planner/unit/ \
          --junitxml=test-results-unit.xml \
          --cov=amplifier.planner \
          --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests

    services:
      mock-services:
        image: planner-mock-services:latest
        ports:
        - 8001:8001
        - 8002:8002
        - 8003:8003

    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install uv
        uv sync --dev

    - name: Wait for mock services
      run: |
        timeout 60 bash -c 'until curl -f http://localhost:8001/health; do sleep 2; done'

    - name: Run integration tests
      run: |
        pytest tests/planner/integration/ \
          --junitxml=test-results-integration.xml \
          --use-mock-services

  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Setup real services
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        pip install uv
        uv sync --dev
        export USE_REAL_SERVICES=true

    - name: Run E2E tests
      run: |
        pytest tests/planner/e2e/ \
          --junitxml=test-results-e2e.xml \
          --real-services \
          --timeout=3600  # 1 hour timeout for E2E

  performance-tests:
    runs-on: ubuntu-latest-8-cores
    needs: integration-tests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install uv
        uv sync --dev
        pip install pytest-benchmark

    - name: Run performance benchmarks
      run: |
        pytest tests/planner/performance/ \
          --benchmark-json=benchmark-results.json \
          --benchmark-only

    - name: Compare with baseline
      run: |
        python tests/planner/utils/compare_benchmarks.py \
          --current benchmark-results.json \
          --baseline tests/planner/performance/baseline.json \
          --threshold 0.15

    - name: Upload benchmark results
      uses: actions/upload-artifact@v3
      with:
        name: performance-results
        path: benchmark-results.json
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml (add to existing)
repos:
- repo: local
  hooks:
  - id: planner-unit-tests
    name: Super-planner unit tests
    entry: pytest tests/planner/unit/ -x --tb=short
    language: system
    files: ^(amplifier/planner/|tests/planner/).*\.py$
    pass_filenames: false

  - id: planner-integration-smoke
    name: Super-planner integration smoke test
    entry: pytest tests/planner/integration/test_basic_workflow.py -v
    language: system
    files: ^(amplifier/planner/|tests/planner/).*\.py$
    pass_filenames: false
```

## Test Quality Assurance

### Test Coverage Requirements

```bash
# Coverage targets
Unit Tests: 85%+ line coverage, 80%+ branch coverage
Integration Tests: 70%+ end-to-end path coverage
Critical Components: 95%+ coverage (state management, coordination)

# Generate coverage reports
pytest tests/planner/ \
  --cov=amplifier.planner \
  --cov-report=html \
  --cov-report=term \
  --cov-fail-under=85
```

### Test Quality Metrics

```python
# tests/planner/quality/test_metrics.py
def test_coverage_requirements():
    """Ensure test coverage meets requirements"""
    coverage = get_coverage_data()

    assert coverage['unit_tests']['line'] >= 85
    assert coverage['unit_tests']['branch'] >= 80
    assert coverage['integration_tests']['path'] >= 70

    critical_components = [
        'amplifier.planner.protocols.state_transitions',
        'amplifier.planner.protocols.agent_coordination',
        'amplifier.planner.core.task_manager'
    ]

    for component in critical_components:
        assert coverage['components'][component]['line'] >= 95

def test_no_flaky_tests():
    """Ensure tests are deterministic"""
    # Run critical tests multiple times to detect flakiness
    for _ in range(10):
        result = subprocess.run([
            'pytest', 'tests/planner/unit/test_state_transitions.py',
            '-q', '--tb=no'
        ], capture_output=True)

        assert result.returncode == 0, "Tests should be deterministic"

def test_performance_stability():
    """Ensure performance tests are stable"""
    baseline_times = load_performance_baseline()

    # Run performance tests 5 times
    results = []
    for _ in range(5):
        result = run_performance_benchmark('core_operations')
        results.append(result)

    # Check for consistency (coefficient of variation < 0.2)
    mean_time = statistics.mean(results)
    std_dev = statistics.stdev(results)
    cv = std_dev / mean_time

    assert cv < 0.2, f"Performance tests too variable: CV={cv:.3f}"
```

### Manual Testing Checklist

```markdown
## Pre-Release Manual Testing

### Core Functionality
- [ ] Create new project via CLI
- [ ] Load existing project successfully
- [ ] Break down complex tasks into subtasks
- [ ] Assign tasks to agents appropriately
- [ ] Handle task state transitions correctly
- [ ] Resolve dependency conflicts
- [ ] Commit changes to git properly

### Error Scenarios
- [ ] Handle corrupted project files
- [ ] Recover from agent failures
- [ ] Manage network connectivity issues
- [ ] Deal with git merge conflicts
- [ ] Handle disk space exhaustion
- [ ] Manage circular dependencies

### Performance
- [ ] Load 1000+ task project in reasonable time
- [ ] Support 10+ concurrent agents
- [ ] Maintain responsiveness under load
- [ ] Handle memory efficiently
- [ ] Scale linearly with project size

### Integration
- [ ] Work with real LLM services
- [ ] Integrate with amplifier Task tool
- [ ] Compatible with amplifier git workflow
- [ ] Use CCSDK defensive utilities properly
```

## Troubleshooting Test Issues

### Common Test Failures

```bash
# Mock service connection issues
Error: Connection refused to localhost:8001
Solution: Ensure mock services are running
docker-compose -f tests/planner/docker/test-services.yml up -d

# Performance test timeout
Error: Test timeout after 300s
Solution: Increase timeout or run on more powerful hardware
pytest tests/planner/performance/ --timeout=3600

# Git operation failures
Error: Git command failed with exit code 128
Solution: Ensure git is configured properly in test environment
git config --global user.email "test@example.com"
git config --global user.name "Test User"

# File permission issues
Error: Permission denied writing to test directory
Solution: Ensure test directories are writable
chmod -R 755 tests/planner/test_data/
```

### Debug Mode Testing

```bash
# Run tests with debug logging
PLANNER_LOG_LEVEL=DEBUG pytest tests/planner/integration/ -v -s

# Keep test artifacts for inspection
pytest tests/planner/ --keep-test-data --pdb-trace

# Run single test with maximum verbosity
pytest tests/planner/integration/test_multi_agent_coordination.py::test_concurrent_task_claiming -vvv -s --tb=long
```

This integration setup ensures comprehensive testing of the super-planner system across all deployment scenarios, from development through production, maintaining the high quality standards expected for enterprise software.