#!/bin/bash

# Test script to validate Dockerfile without Docker
# This checks for common issues and syntax problems

echo "🔍 Testing Dockerfile..."

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found"
    exit 1
fi

# Extract and test the entrypoint script
echo "📝 Extracting entrypoint script for testing..."
sed -n '/COPY <<EOF \/app\/entrypoint.sh/,/^EOF$/p' Dockerfile | sed '1d;$d' > /tmp/test-entrypoint.sh

# Check entrypoint script syntax
echo "🔍 Checking entrypoint script syntax..."
if bash -n /tmp/test-entrypoint.sh; then
    echo "✅ Entrypoint script syntax is valid"
else
    echo "❌ Entrypoint script has syntax errors"
    exit 1
fi

# Check for common Dockerfile issues
echo "🔍 Checking Dockerfile for common issues..."

# Check for COPY heredoc syntax (Docker 24.0+ feature)
if grep -q "COPY <<EOF" Dockerfile; then
    echo "⚠️  Warning: COPY heredoc requires Docker 24.0+. Consider using RUN with cat instead for compatibility."
fi

# Check for proper shell escaping
if grep -q '\$[A-Z_]' Dockerfile; then
    echo "✅ Found proper variable escaping in Dockerfile"
fi

# Validate key components
echo "🔍 Validating key components..."

components=(
    "FROM ubuntu"
    "apt-get update"
    "curl.*nodesource"
    "npm install.*claude-code"
    "git clone.*amplifier"
    "uv venv"
    "make install"
    "ENTRYPOINT"
)

for component in "${components[@]}"; do
    if grep -q "$component" Dockerfile; then
        echo "✅ Found: $component"
    else
        echo "❌ Missing: $component"
        exit 1
    fi
done

# Check the GitHub URL is correct
if grep -q "https://github.com/microsoft/amplifier" Dockerfile; then
    echo "✅ Correct GitHub URL found"
else
    echo "❌ GitHub URL missing or incorrect"
    exit 1
fi

echo "✅ Dockerfile validation completed successfully"
echo "💡 To fully test, you'll need Docker installed to build and run the image"

# Clean up
rm -f /tmp/test-entrypoint.sh