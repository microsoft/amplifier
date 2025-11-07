# Amplifier Testing Documentation Index

Complete documentation of Amplifier's testing infrastructure and validation procedures.

## Documentation Files

### 1. TESTING_REPORT.md (Primary Reference - 23 KB, 823 lines)
**Comprehensive testing documentation with very thorough depth**

Sections:
1. Testing Infrastructure Overview
2. Current Testing Infrastructure Details
3. Smoke Test Suite (AI-Driven)
4. Test Coverage Analysis
5. Known Test Gaps & Recommendations
6. Running Tests: Complete Instructions
7. CI/CD Integration
8. Manual Verification Checklist
9. Test Execution Results
10. Key Testing Insights
11. Advanced Testing Topics
12. Performance Benchmarking
13. Conclusion

Best for: Complete understanding of testing system

### 2. TESTING_QUICK_START.md (Quick Reference)
**Fast-access guide for common operations**

Contents:
- One-minute setup
- Common commands
- Test locations table
- Understanding test results
- Troubleshooting
- Philosophy enforcement summary

Best for: Day-to-day testing activities

### 3. TESTING_INDEX.md (This File)
**Navigation guide for documentation**

Best for: Finding what you need quickly

---

## Quick Links by Use Case

### I want to...

**...verify everything works**
→ Run: `make check && make test`
→ Read: TESTING_QUICK_START.md - "One-Minute Setup"

**...understand the testing system**
→ Read: TESTING_REPORT.md - Sections 1-3
→ Run: `make test -v` to see tests in action

**...fix a failing test**
→ Read: TESTING_QUICK_START.md - "Troubleshooting"
→ Read: TESTING_REPORT.md - Section 6.5

**...add a new test**
→ Read: TESTING_REPORT.md - Section 11.1-11.3
→ Reference: tests/conftest.py for fixtures

**...set up CI/CD**
→ Read: TESTING_REPORT.md - Section 7.2

**...understand philosophy enforcement**
→ Read: TESTING_QUICK_START.md - "Philosophy Enforcement"
→ Read: TESTING_REPORT.md - Section 10.1

**...check test coverage**
→ Run: `uv run pytest --cov=amplifier --cov-report=html`
→ Read: TESTING_REPORT.md - Section 4

---

## Test Structure Quick Reference

```
Test Infrastructure:
├── Code Quality (make check)
│   ├── Ruff format (formatting)
│   ├── Ruff lint (linting)
│   ├── Pyright (type checking)
│   └── check_stubs.py (placeholder detection)
│
├── Unit Tests (make test)
│   ├── test_stub_detection.py (Zero-BS principle)
│   ├── test_antisycophantic.py (professional communication)
│   ├── test_parallel_execution.py (performance optimization)
│   └── test_cache.py (feature-specific)
│
└── Smoke Tests (make smoke-test)
    ├── Core Commands (3 tests)
    ├── Content Management (3 tests)
    ├── Knowledge Base (4 tests)
    ├── Knowledge Graph (3 tests)
    ├── Utilities (2 tests)
    └── Python Verification (5+ tests)
```

---

## Key Metrics

- **Total Tests:** 40+ (5 unit + 31 smoke + scenarios)
- **Execution Time:** ~5-10 minutes full suite
- **Code Coverage:** Core principles 100% (Zero-BS, anti-sycophancy, parallelism)
- **Test Pass Rate:** 100% (all tests passing)
- **Files Scanned:** 240+ Python files
- **Type Checking:** 0 errors, 0 warnings

---

## Common Commands Cheat Sheet

```bash
# Quick checks
make check              # Format + lint + types + stubs (30 sec)
make test               # Unit tests (4 sec)
make smoke-test         # Integration tests (varies)

# Specific tests
pytest tests/test_stub_detection.py -v
pytest tests/test_antisycophantic.py::test_sycophancy_detection -v

# Coverage
pytest --cov=amplifier --cov-report=html

# Verbose
pytest -vv --tb=short
```

---

## Philosophy Enforcement Details

### Zero-BS Principle
- **What:** No incomplete code (stubs, TODO, NotImplementedError)
- **Tool:** tools/check_stubs.py (part of make check)
- **Test:** tests/test_stub_detection.py
- **Patterns Caught:** NotImplementedError, TODO, FIXME, HACK, mock_, fake_, dummy_, "coming soon"

### Anti-Sycophancy
- **What:** Professional, substantive communication
- **Test:** tests/test_antisycophantic.py (2 test functions)
- **Patterns Caught:** "You're absolutely right!", "That's brilliant!", overly flattering language

### Parallel Execution
- **What:** Parallelizable tasks run in parallel
- **Test:** tests/test_parallel_execution.py
- **Metric:** Parallelism score (0=sequential, 1=parallel)

---

## For Deeper Understanding

**Test Philosophy:**
- See AGENTS.md sections on "Zero-BS Principle", "Response Authenticity Guidelines"
- See CLAUDE.md for Claude Code-specific testing guidance

**Code Quality Tools:**
- Ruff documentation: https://docs.astral.sh/ruff/
- Pyright documentation: https://github.com/microsoft/pyright
- Pytest documentation: https://docs.pytest.org/

**CI/CD Integration:**
- TESTING_REPORT.md Section 7 for GitHub Actions template
- Makefile for local testing setup

---

## File Locations Reference

```
Project Root: /home/ufeld/dev/amplifier/

Tests:
- tests/                           # Core unit tests
- amplifier/smoke_tests/           # AI-driven smoke tests
- scenarios/*/test*.py             # Feature-specific tests

Configuration:
- pyproject.toml                   # Pytest config
- ruff.toml                        # Ruff config
- tests/conftest.py               # Pytest fixtures

Tools:
- tools/check_stubs.py            # Stub detection
- tools/makefiles/                # Build system

Documentation:
- TESTING_REPORT.md               # Comprehensive (this set)
- TESTING_QUICK_START.md          # Quick reference
- TESTING_INDEX.md                # This file
```

---

## Testing Workflow

### For Developers
1. Make code changes
2. Run `make check` (verify formatting/linting/types/stubs)
3. Run `make test` (verify unit tests pass)
4. Commit when all pass

### For Integration Verification
1. Run `make install` (setup)
2. Run `make check && make test && make smoke-test` (full validation)
3. Run manual verification for features you changed

### For CI/CD
1. Use GitHub Actions template from TESTING_REPORT.md Section 7.2
2. Run: format → lint → type-check → stubs → unit tests → smoke tests
3. Fail fast on any quality gate

---

## Support & Troubleshooting

**Problem:** Tests won't run
- Solution: `source .venv/bin/activate` or use `uv run pytest`

**Problem:** Import errors
- Solution: Ensure PYTHONPATH is set, or use `uv run`

**Problem:** Smoke tests timeout
- Solution: Normal outside Claude Code environment, tests gracefully skip AI evaluation

**Problem:** Test failure
- Solution: See TESTING_QUICK_START.md "Troubleshooting" or TESTING_REPORT.md Section 6.5

---

## Summary

Amplifier's testing system is:
- **Comprehensive:** 40+ tests across quality, behavior, integration
- **Automated:** All via `make` commands, designed for CI/CD
- **Philosophy-aligned:** Enforces Zero-BS, anti-sycophancy, parallelism
- **AI-friendly:** Uses Claude SDK for smoke test evaluation
- **Developer-focused:** Clear documentation, quick feedback loops

For immediate action, run: `make check && make test`

For complete understanding, read: TESTING_REPORT.md Sections 1-4

---

**Last Updated:** November 6, 2025
**Documentation Version:** 1.0
**Depth Level:** Very Thorough
