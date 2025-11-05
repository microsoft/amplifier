#!/bin/bash

# Print Helper Functions for Amplifier Scripts
# Contains only color variables and print functions, no side effects

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[Amplifier]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[Amplifier]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[Amplifier]${NC} $1"
}

print_error() {
    echo -e "${RED}[Amplifier]${NC} $1"
}