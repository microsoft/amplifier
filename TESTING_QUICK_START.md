# Amplifier Testing - Quick Start Guide

## One-Minute Setup
```bash
# Install dependencies
make install

# Run all tests
make test && make check
```

## Common Commands

### Quick Verification (30 seconds)
```bash
make check     # Formatting, linting, type check, stub detection
```

### Run Tests
```bash
make test      # Unit tests (5 tests in 4s)
make smoke-test # Integration smoke tests (31 tests, slower)
```

### Run Specific Tests
```bash
# Single test file
uv run pytest tests/test_stub_detection.py -v

# Specific test
uv run pytest tests/test_antisycophantic.py::test_sycophancy_detection -v

# With coverage report
uv run pytest --cov=amplifier --cov-report=html
```

## Test Locations

| What | Location | Command |
|------|----------|---------|
| Core tests | `/tests/` | `make test` |
| Smoke tests | `/amplifier/smoke_tests/` | `make smoke-test` |
| Transcribe feature | `/scenarios/transcribe/test_cache.py` | Included in `make test` |
| Code quality | Multiple tools | `make check` |

## Understanding Test Results

### Perfect Run
```
✓ 5 tests passed
✓ 0 linting errors
✓ 0 type errors
✓ No stubs found
```

### What Tests Check

**test_stub_detection.py**
- Catches: `raise NotImplementedError`, TODO, FIXME, HACK, mock_, fake_, dummy_, placeholder, "coming soon"
- Prevents incomplete code from being committed
- Run with: `make test` or `pytest tests/test_stub_detection.py`

**test_antisycophantic.py** (2 tests)
- Catches: "You're absolutely right!", "That's brilliant!", overly flattering responses
- Ensures professional, substantive communication
- Run with: `make test` or `pytest tests/test_antisycophantic.py`

**test_parallel_execution.py**
- Checks: whether parallelizable tasks run in parallel
- Calculates parallelism score (0-1)
- Run with: `make test` or `pytest tests/test_parallel_execution.py`

**test_cache.py** (Transcribe)
- Tests: audio file caching, JSON metadata, cache detection
- Run with: `make test` or `pytest scenarios/transcribe/test_cache.py`

**Smoke Tests** (31 tests, AI-evaluated)
- Tests: make help, check, content scan, knowledge query, graph operations, imports
- Evaluated by Claude Code SDK for success criteria
- Gracefully skips evaluation if SDK unavailable
- Run with: `make smoke-test`

## Troubleshooting

**Tests won't run**
```bash
# Activate venv
source .venv/bin/activate

# Or use uv (recommended)
uv run pytest
```

**Import errors**
```bash
# Make sure you're in project root
cd /home/ufeld/dev/amplifier
make test
```

**Smoke tests timeout**
```bash
# Expected outside Claude Code environment
# SDK will gracefully skip evaluation
# Tests pass even without AI evaluation
make smoke-test
```

**Want to see what test does**
```bash
# Run with verbose output
uv run pytest -vv --tb=short tests/test_stub_detection.py
```

## Philosophy Enforcement

The test suite ensures:

1. **Zero-BS Principle**: No incomplete code (stubs, TODO, NotImplementedError)
2. **Anti-Sycophancy**: Responses are professional, substantive, not flattering
3. **Parallel Execution**: Multi-file operations run in parallel

If code violates these principles, tests will fail and prevent commit.

## For More Details

See `TESTING_REPORT.md` for:
- Complete test documentation
- Manual verification checklist
- CI/CD setup recommendations
- Advanced testing topics
- Performance benchmarking info

## Key Files

```
/home/ufeld/dev/amplifier/
├── Makefile                           # test, check, smoke-test targets
├── pyproject.toml                     # pytest configuration
├── tests/                             # Unit tests
├── amplifier/smoke_tests/tests.yaml  # 31 smoke tests
├── tools/check_stubs.py              # Stub detection tool
├── TESTING_REPORT.md                 # Full documentation
└── TESTING_QUICK_START.md            # This file
```
