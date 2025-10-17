# Desktop Notifications Guide [Claude Code only]

Never miss important Claude Code events with native desktop notifications on all platforms.

## 🔔 Overview

The notification system keeps you in flow by alerting you when:

- Claude Code needs permission to proceed
- Tasks complete successfully
- Errors require your attention
- Long-running operations finish
- Custom events you define occur

## 🖥️ Platform Support

### macOS

- Native Notification Center
- Supports title, subtitle, and message
- Respects Do Not Disturb settings
- Sound alerts optional

### Linux

- Uses `notify-send` (libnotify)
- Full desktop environment support
- Works with GNOME, KDE, XFCE, etc.
- Custom icons supported

### Windows

- Native Windows toast notifications
- Action Center integration
- Works in PowerShell/WSL
- Supports notification grouping

### WSL (Windows Subsystem for Linux)

- Automatically detects WSL environment
- Routes to Windows notifications
- Full feature support
- No additional setup needed

## 🚀 Quick Start

### For CLI Tools

Notifications are **OFF by default** for CLI tools. Enable them with:

```bash
# Enable notifications for a command
NOTIFY=true amplifier-synthesis process article.md

# Or use make with notification support
make synthesis  # Uses NOTIFY=true internally
```

### Automatic Detection

The system automatically:

1. Detects your platform
2. Uses the best notification method
3. Falls back to console output if needed

## 🛠️ How It Works

### Notification Flow

```
Claude Code Event
    ↓
Notification Hook Triggered
    ↓
notify.sh Receives JSON
    ↓
Platform Detection
    ↓
Native Notification Sent
    ↓
You Stay In Flow ✨
```

### JSON Input Format

The notification script receives:

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project",
  "hook_event_name": "Notification",
  "message": "Task completed successfully"
}
```

### Smart Context Detection

Notifications include:

- **Project Name**: From git repo or directory name
- **Session ID**: Last 6 characters for multi-window users
- **Message**: The actual notification content

Example: `MyProject (abc123): Build completed successfully`

## 🎨 Customization

### Custom Messages

Edit `.claude/settings.json` to customize when notifications appear:

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": ".*error.*",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/tools/notify-error.sh"
          }
        ]
      }
    ]
  }
}
```

### Adding Sounds

**macOS** - Add to `notify.sh`:

```bash
# Play sound with notification
osascript -e 'display notification "..." sound name "Glass"'
```

**Linux** - Add to `notify.sh`:

```bash
# Play sound after notification
paplay /usr/share/sounds/freedesktop/stereo/complete.oga &
```

**Windows/WSL** - Add to PowerShell section:

```powershell
# System sounds
[System.Media.SystemSounds]::Exclamation.Play()
```

### Custom Icons

**Linux**:

```bash
notify-send -i "/path/to/icon.png" "Title" "Message"
```

**macOS** (using terminal-notifier):

```bash
terminal-notifier -title "Claude Code" -message "Done!" -appIcon "/path/to/icon.png"
```

### Notification Categories

Add urgency levels:

```bash
# In notify.sh
case "$MESSAGE" in
    *"error"*|*"failed"*)
        URGENCY="critical"
        TIMEOUT=0  # Don't auto-dismiss
        ;;
    *"warning"*)
        URGENCY="normal"
        TIMEOUT=10000
        ;;
    *)
        URGENCY="low"
        TIMEOUT=5000
        ;;
esac

# Linux
notify-send -u "$URGENCY" -t "$TIMEOUT" "$TITLE" "$MESSAGE"
```

## 🔧 Troubleshooting

### No Notifications Appearing

1. **Check permissions**:

   ```bash
   # Make script executable
   chmod +x .claude/tools/notify.sh
   ```

2. **Test manually**:

   ```bash
   echo '{"message": "Test notification", "cwd": "'$(pwd)'"}' | .claude/tools/notify.sh
   ```

3. **Enable debug mode**:
   ```bash
   echo '{"message": "Test"}' | .claude/tools/notify.sh --debug
   # Check /tmp/claude-code-notify-*.log
   ```

### Platform-Specific Issues

**macOS**:

- Check System Preferences → Notifications → Terminal/Claude Code
- Ensure notifications are allowed
- Try: `osascript -e 'display notification "Test"'`

**Linux**:

- Install libnotify: `sudo apt install libnotify-bin`
- Test: `notify-send "Test"`
- Check if notification daemon is running

**Windows/WSL**:

- Ensure Windows notifications are enabled
- Check Focus Assist settings
- Test PowerShell directly

### Silent Failures

Enable verbose logging:

```bash
# Add to notify.sh
set -x  # Enable command printing
exec 2>/tmp/notify-debug.log  # Redirect errors
```

## 📊 Advanced Usage

### Notification History

Track all notifications:

```bash
# Add to notify.sh
echo "$(date): $MESSAGE" >> ~/.claude-notifications.log
```

### Conditional Notifications

Only notify for important events:

```bash
# Skip trivial notifications
if [[ "$MESSAGE" =~ ^(Saved|Loaded|Reading) ]]; then
    exit 0
fi
```

### Remote Notifications

Send to your phone via Pushover/Pushbullet:

```bash
# Add to notify.sh for critical errors
if [[ "$MESSAGE" =~ "critical error" ]]; then
    curl -s -F "token=YOUR_APP_TOKEN" \
         -F "user=YOUR_USER_KEY" \
         -F "message=$MESSAGE" \
         https://api.pushover.net/1/messages.json
fi
```

### Notification Groups

Group related notifications:

```bash
# macOS - Show with project subtitle
osascript -e "display notification \"$MESSAGE\" with title \"Amplifier\" subtitle \"$PROJECT\""
```

## 🎯 Best Practices

1. **Be Selective**: Too many notifications reduce their value
2. **Add Context**: Include project and session info
3. **Use Urgency**: Critical errors should stand out
4. **Test Regularly**: Ensure notifications work after updates
5. **Provide Fallbacks**: Always output to console too

## 🔌 Integration Examples

### Build Status

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash.*make.*build",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/tools/notify-build.sh"
          }
        ]
      }
    ]
  }
}
```

### Test Results

```bash
# In notify-build.sh
if grep -q "FAILED" <<< "$TOOL_OUTPUT"; then
    MESSAGE="❌ Build failed! Check errors."
else
    MESSAGE="✅ Build successful!"
fi
```

### Long Task Completion

```bash
# Track task duration
START_TIME=$(date +%s)
# ... task runs ...
DURATION=$(($(date +%s) - START_TIME))
MESSAGE="Task completed in ${DURATION}s"
```

## 🌟 Tips & Tricks

1. **Use Emojis**: They make notifications scannable

   - ✅ Success
   - ❌ Error
   - ⚠️ Warning
   - 🔄 In Progress
   - 🎉 Major Success

2. **Keep It Short**: Notifications should be glanceable

3. **Action Words**: Start with verbs

   - "Completed build"
   - "Fixed 3 errors"
   - "Need input for..."

4. **Session Context**: Include session ID for multiple windows

5. **Project Context**: Always show which project

## 🔗 Related Documentation

- [Automation Guide](automation.md) - Hook system
- [Command Reference](commands.md) - Triggering notifications
