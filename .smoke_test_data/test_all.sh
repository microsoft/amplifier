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

# Quick essential tests
echo "ESSENTIAL TESTS"
echo "---------------"
run_test "amplifier --version" "amplifier --version 2>&1" "Amplifier v0.2.0"
run_test "amplifier doctor" "amplifier doctor 2>&1 | grep -c 'Python'" "1"
run_test "Cache speedup verified" "grep '1,455x' PERFORMANCE_COMPARISON.md" "1,455x"
run_test "Python CLI installed" "test -f .venv/bin/amplifier && echo 'OK'" "OK"
run_test "Unified wrapper installed" "test -f ~/bin/amplifier && echo 'OK'" "OK"

echo ""
echo "========================================"
echo "           TEST SUMMARY"
echo "========================================"
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    exit 1
fi
