#!/bin/bash

# Comprehensive Amplifier Test Suite
# Tests all functionality to avoid back-and-forth debugging

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "Testing: $test_name... "
    
    # Run command and capture output
    if output=$(eval "$test_command" 2>&1); then
        if [[ -z "$expected_pattern" ]] || echo "$output" | grep -q "$expected_pattern"; then
            echo -e "${GREEN}✓ PASS${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} - Expected pattern not found: $expected_pattern"
            echo "  Output: $(echo "$output" | head -1)"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
    else
        echo -e "${RED}✗ FAIL${NC} - Command failed with exit code $?"
        echo "  Output: $(echo "$output" | head -1)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

echo "========================================"
echo "    AMPLIFIER COMPREHENSIVE TEST SUITE"
echo "========================================"
echo ""

# 1. Installation Tests
echo "1. INSTALLATION TESTS"
echo "---------------------"
run_test "Virtual environment exists" "test -f .venv/bin/activate && echo 'exists'" "exists"
run_test "Python version >= 3.11" "python --version | grep -E 'Python 3\.(1[1-9]|[2-9][0-9])'" "Python 3"
run_test "uv is installed" "which uv > /dev/null && echo 'found'" "found"
run_test "Dependencies installed" "python -c 'import amplifier' 2>/dev/null && echo 'success'" "success"

echo ""

# 2. Package Configuration Tests
echo "2. PACKAGE CONFIGURATION"
echo "------------------------"
run_test "Package name is amplifier-toolkit" "grep 'name = \"amplifier-toolkit\"' pyproject.toml" "amplifier-toolkit"
run_test "Version is 0.2.0" "grep 'version = \"0.2.0\"' pyproject.toml" "0.2.0"
run_test "Entry point configured" "grep 'amplifier = \"amplifier.cli:cli\"' pyproject.toml" "amplifier.cli:cli"
run_test "uv package enabled" "grep 'package = true' pyproject.toml" "package = true"

echo ""

# 3. Global Command Tests
echo "3. GLOBAL COMMAND TESTS"
echo "-----------------------"
run_test "amplifier command exists" "which amplifier > /dev/null && echo 'found'" "found"
run_test "amplifier-cli symlink exists" "test -L ~/bin/amplifier-cli && echo 'exists'" "exists"
run_test "amplifier --version works" "amplifier --version 2>&1" "Amplifier v0.2.0"
run_test "amplifier doctor runs" "amplifier doctor 2>&1 | grep -c 'Python'" "1"

echo ""

# 4. CLI Subcommands Tests
echo "4. CLI SUBCOMMANDS"
echo "------------------"
run_test "Doctor command" "amplifier doctor 2>&1 | grep 'Running environment diagnostics'" "Running environment"
run_test "Help command" "amplifier --help 2>&1 | grep 'AI-powered knowledge synthesis'" "AI-powered"
run_test "Smoke command exists" "amplifier smoke --help 2>&1 | grep 'Run smoke tests'" "smoke tests"

echo ""

# 5. Unified Command Routing Tests
echo "5. UNIFIED COMMAND ROUTING"
echo "--------------------------"
run_test "CLI routing (--version)" "amplifier --version 2>&1" "Amplifier v0.2.0"
run_test "Unified wrapper exists" "test -f bin/amplifier-unified && echo 'exists'" "exists"
run_test "Wrapper is executable" "test -x bin/amplifier-unified && echo 'executable'" "executable"

echo ""

# 6. Cache System Tests
echo "6. CACHE SYSTEM TESTS"
echo "---------------------"
run_test "Cache module imports" "python -c 'from amplifier.utils.cache import ArtifactCache; print(\"OK\")'" "OK"
run_test "Cache directory creation" "python -c 'from amplifier.utils.cache import ArtifactCache; c = ArtifactCache(); print(\"OK\")'" "OK"
run_test "Cache fingerprinting" "python -c 'from amplifier.utils.cache import ArtifactCache; c = ArtifactCache(); fp = c.compute_fingerprint(\"test\", \"stage\"); print(len(fp))' | grep -E '^16$'" "16"

echo ""

# 7. Event System Tests
echo "7. EVENT SYSTEM TESTS"
echo "--------------------"
run_test "Event module imports" "python -c 'from amplifier.utils.events import EventLogger; print(\"OK\")'" "OK"
run_test "Event creation" "python -c 'from amplifier.utils.events import Event; e = Event(\"test\", \"ok\"); print(\"OK\")'" "OK"

echo ""

# 8. Code Quality Tests
echo "8. CODE QUALITY TESTS"
echo "--------------------"
run_test "Ruff format check" "ruff format --check test_performance_comparison.py test_cache_performance.py 2>&1 | grep -E '(left unchanged|would reformat)' || echo 'OK'" "OK"
run_test "Ruff lint check" "ruff check test_performance_comparison.py test_cache_performance.py 2>&1 && echo 'PASS' || echo 'FAIL'" "PASS"
run_test "Python imports work" "python -c 'import amplifier.cli; import amplifier.utils.cache; import amplifier.utils.events; print(\"OK\")'" "OK"

echo ""

# 9. Performance Test Files
echo "9. PERFORMANCE TEST FILES"
echo "------------------------"
run_test "test_cache_performance.py exists" "test -f test_cache_performance.py && echo 'exists'" "exists"
run_test "test_performance_comparison.py exists" "test -f test_performance_comparison.py && echo 'exists'" "exists"
run_test "Cache performance test runs" "timeout 10 python test_cache_performance.py 2>&1 | grep 'Speedup'" "Speedup"

echo ""

# 10. Makefile Integration Tests
echo "10. MAKEFILE INTEGRATION"
echo "------------------------"
run_test "make help works" "make help 2>&1 | grep 'Quick Start'" "Quick Start"
run_test "install-global target exists" "grep 'install-global:' Makefile" "install-global:"
run_test "Unified wrapper in Makefile" "grep 'amplifier-unified' Makefile" "amplifier-unified"

echo ""

# 11. Documentation Tests
echo "11. DOCUMENTATION"
echo "-----------------"
run_test "PERFORMANCE_COMPARISON.md exists" "test -f PERFORMANCE_COMPARISON.md && echo 'exists'" "exists"
run_test "Performance doc shows 1,455x speedup" "grep '1,455x' PERFORMANCE_COMPARISON.md" "1,455x"
run_test "IMPLEMENTATION_SUMMARY.md exists" "test -f IMPLEMENTATION_SUMMARY.md && echo 'exists'" "exists"
run_test "UNIFIED_COMMAND_SUMMARY.md exists" "test -f UNIFIED_COMMAND_SUMMARY.md && echo 'exists'" "exists"

echo ""

# 12. Integration Tests
echo "12. INTEGRATION TESTS"
echo "--------------------"
run_test "amplifier + Claude CLI check" "amplifier doctor 2>&1 | grep 'Claude CLI.*OK'" "OK"
run_test "Data directory check" "amplifier doctor 2>&1 | grep 'Data directory.*OK'" "OK"

echo ""
echo "========================================"
echo "           TEST SUMMARY"
echo "========================================"
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo "The Amplifier installation and features are working correctly."
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo "Please review the failed tests above."
    exit 1
fi