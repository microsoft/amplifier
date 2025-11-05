# Automation Guide [Claude Code only]

This guide explains how automation works for Claude Code and how to extend it for your needs.

## 🔄 How Automation Works

### The Hook System

Claude Code supports hooks that trigger actions based on events:

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "pattern",
        "hooks": [
          {
            "type": "command",
            "command": "script-to-run.sh"
          }
        ]
      }
    ]
  }
}
```

### Current Automations

#### 1. **Automatic Quality Checks**

- **Trigger**: After any file edit/write
- **Script**: `.claude/tools/make-check.sh`
- **What it does**:
  - Finds the nearest Makefile
  - Runs `make check`
  - Reports results
  - Works with monorepos

#### 2. **Desktop Notifications**

- **Trigger**: Any Claude Code notification event
- **Script**: `.claude/tools/notify.sh`
- **Features**:
  - Native notifications on all platforms
  - Shows project context
  - Non-intrusive fallbacks

## 🛠️ The Make Check System

### How It Works

The `make-check.sh` script is intelligent:

```bash
# 1. Detects what file was edited
/path/to/project/src/component.tsx

# 2. Looks for Makefile in order:
/path/to/project/src/Makefile      # Local directory
/path/to/project/Makefile          # Project root
/path/to/Makefile                  # Parent directories

# 3. Runs make check from appropriate location
cd /path/to/project && make check
```

### Setting Up Your Makefile

Create a `Makefile` in your project root:

```makefile
.PHONY: check
check: format lint typecheck test

.PHONY: format
format:
	@echo "Formatting code..."
	# Python
	black . || true
	isort . || true
	# JavaScript/TypeScript
	prettier --write . || true

.PHONY: lint
lint:
	@echo "Linting code..."
	# Python
	ruff check . || true
	# JavaScript/TypeScript
	eslint . --fix || true

.PHONY: typecheck
typecheck:
	@echo "Type checking..."
	# Python
	mypy . || true
	# TypeScript
	tsc --noEmit || true

.PHONY: test
test:
	@echo "Running tests..."
	# Python
	pytest || true
	# JavaScript
	npm test || true
```

### Customizing Quality Checks

For different languages/frameworks:

**Python Project**:

```makefile
check: format lint typecheck test

format:
	uv run black .
	uv run isort .

lint:
	uv run ruff check .

typecheck:
	uv run mypy .

test:
	uv run pytest
```

**Node.js Project**:

```makefile
check: format lint typecheck test

format:
	npm run format

lint:
	npm run lint

typecheck:
	npm run typecheck

test:
	npm test
```

**Go Project**:

```makefile
check: format lint test

format:
	go fmt ./...

lint:
	golangci-lint run

test:
	go test ./...
```

## 🔔 Notification System

### How Notifications Work

1. **Event Occurs**: Claude Code needs attention
2. **Hook Triggered**: Notification hook activates
3. **Context Gathered**: Project name, session ID extracted
4. **Platform Detection**: Appropriate notification method chosen
5. **Notification Sent**: Native notification appears

### Customizing Notifications

Edit `.claude/tools/notify.sh`:

```bash
# Add custom notification categories
case "$MESSAGE" in
    *"error"*)
        URGENCY="critical"
        ICON="error.png"
        ;;
    *"success"*)
        URGENCY="normal"
        ICON="success.png"
        ;;
    *)
        URGENCY="low"
        ICON="info.png"
        ;;
esac
```

### Adding Sound Alerts

**macOS**:

```bash
# Add to notify.sh
afplay /System/Library/Sounds/Glass.aiff
```

**Linux**:

```bash
# Add to notify.sh
paplay /usr/share/sounds/freedesktop/stereo/complete.oga
```

**Windows/WSL**:

```powershell
# Add to PowerShell section
[System.Media.SystemSounds]::Exclamation.Play()
```

## 🎯 Creating Custom Automations

### Example: Auto-Format on Save

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/tools/auto-format.sh"
          }
        ]
      }
    ]
  }
}
```

Create `.claude/tools/auto-format.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Read JSON input
JSON_INPUT=$(cat)

# Extract file path
FILE_PATH=$(echo "$JSON_INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')

# Format based on file extension
case "$FILE_PATH" in
    *.py)
        black "$FILE_PATH"
        ;;
    *.js|*.jsx|*.ts|*.tsx)
        prettier --write "$FILE_PATH"
        ;;
    *.go)
        gofmt -w "$FILE_PATH"
        ;;
esac
```

### Example: Git Auto-Commit

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/tools/auto-commit.sh"
          }
        ]
      }
    ]
  }
}
```

Create `.claude/tools/auto-commit.sh`:

```bash
#!/usr/bin/env bash
# Auto-commit changes with descriptive messages

# ... parse JSON and get file path ...

# Generate commit message
COMMIT_MSG="Auto-update: $(basename "$FILE_PATH")"

# Stage and commit
git add "$FILE_PATH"
git commit -m "$COMMIT_MSG" --no-verify || true
```

### Example: Test Runner

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/tools/run-tests.sh"
          }
        ]
      }
    ]
  }
}
```

## 🏗️ Advanced Automation Patterns

### Conditional Execution

```bash
#!/usr/bin/env bash
# Only run on specific files

FILE_PATH=$(extract_file_path_from_json)

# Only check Python files
if [[ "$FILE_PATH" == *.py ]]; then
    python -m py_compile "$FILE_PATH"
fi

# Only test when source files change
if [[ "$FILE_PATH" == */src/* ]]; then
    npm test
fi
```

### Parallel Execution

```bash
#!/usr/bin/env bash
# Run multiple checks in parallel

{
    echo "Starting parallel checks..."

    # Run all checks in background
    make format &
    PID1=$!

    make lint &
    PID2=$!

    make typecheck &
    PID3=$!

    # Wait for all to complete
    wait $PID1 $PID2 $PID3

    echo "All checks complete!"
}
```

### Error Handling

```bash
#!/usr/bin/env bash
# Graceful error handling

set -euo pipefail

# Trap errors
trap 'echo "Check failed at line $LINENO"' ERR

# Run with error collection
ERRORS=0

make format || ((ERRORS++))
make lint || ((ERRORS++))
make test || ((ERRORS++))

if [ $ERRORS -gt 0 ]; then
    echo "⚠️  $ERRORS check(s) failed"
    exit 1
else
    echo "✅ All checks passed!"
fi
```

## 🔧 Debugging Automations

### Enable Debug Logging

```bash
# Add to any automation script
DEBUG_LOG="/tmp/claude-automation-debug.log"
echo "[$(date)] Script started" >> "$DEBUG_LOG"
echo "Input: $JSON_INPUT" >> "$DEBUG_LOG"
```

### Test Scripts Manually

```bash
# Test with sample input
echo '{"file_path": "/path/to/test.py", "success": true}' | .claude/tools/make-check.sh
```

### Common Issues

1. **Script Not Executing**

   - Check file permissions: `chmod +x .claude/tools/*.sh`
   - Verify path in settings.json

2. **No Output**

   - Check if script outputs to stdout
   - Look for error logs in /tmp/

3. **Platform-Specific Issues**
   - Test platform detection logic
   - Ensure fallbacks work

## 🚀 Best Practices

1. **Fast Execution**: Keep automations under 5 seconds
2. **Fail Gracefully**: Don't break Claude Code workflow
3. **User Feedback**: Provide clear success/failure messages
4. **Cross-Platform**: Test on Mac, Linux, Windows, WSL
5. **Configurable**: Allow users to customize behavior

## 📊 Performance Optimization

### Caching Results

```bash
# Cache expensive operations
CACHE_FILE="/tmp/claude-check-cache"
CACHE_AGE=$(($(date +%s) - $(stat -f %m "$CACHE_FILE" 2>/dev/null || echo 0)))

if [ $CACHE_AGE -lt 300 ]; then  # 5 minutes
    cat "$CACHE_FILE"
else
    make check | tee "$CACHE_FILE"
fi
```

### Incremental Checks

```bash
# Only check changed files
CHANGED_FILES=$(git diff --name-only HEAD)
for file in $CHANGED_FILES; do
    case "$file" in
        *.py) pylint "$file" ;;
        *.js) eslint "$file" ;;
    esac
done
```

## 🔗 Related Documentation

- [Command Reference](commands.md) - Available commands
- [Notifications Guide](notifications.md) - Desktop alerts
