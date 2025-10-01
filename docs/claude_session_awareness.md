# Claude Session Awareness for Amplifier

A lightweight, integrated solution for enabling multiple Claude Code sessions to be aware of each other's activity in the same Amplifier project.

## Features

- **Minimal footprint**: Clean integration into Amplifier's modular architecture
- **Zero disruption**: Fails silently if any issues occur, never breaks existing workflows
- **Automatic cleanup**: Stale sessions removed after 5 minutes of inactivity
- **Activity logging**: Maintains a rolling log of recent activity across all sessions
- **Cross-session communication**: Broadcast messages to all active sessions

## Installation

The Claude session awareness module is included in Amplifier. No additional installation needed.

## Usage

### Command Line Interface

The session awareness features are accessible through the Amplifier CLI:

```bash
# Check status of all active sessions
python scripts/claude_cli.py status

# Track an activity for the current session
python scripts/claude_cli.py track "Working on feature X" --details "Adding authentication"

# Broadcast a message to all sessions
python scripts/claude_cli.py broadcast "Starting deployment - please pause edits"

# View recent activity log
python scripts/claude_cli.py activity --limit 20
```

### Python API

You can also use the session awareness programmatically:

```python
from amplifier.claude import SessionAwareness

# Initialize session awareness
sa = SessionAwareness()

# Register an activity
sa.register_activity("Edit", "Modified auth module")

# Get active sessions
sessions = sa.get_active_sessions()
for session in sessions:
    print(f"Session {session.session_id}: PID {session.pid}")

# Get recent activity
activities = sa.get_recent_activity(limit=10)
for activity in activities:
    print(f"{activity.session_id}: {activity.action}")

# Broadcast a message
sa.broadcast_message("Database migration starting")

# Get comprehensive status
status = sa.get_status()
print(f"Active sessions: {status['active_sessions']}")
```

## Data Storage

Session data is stored in `.data/session_awareness/`:

- `sessions.json` - Active session information
- `activity.jsonl` - Activity log (append-only, auto-trimmed to last 1000 entries)

## Environment Variables

- `CLAUDE_SESSION_ID` - Override the automatic session ID generation (optional)

## Integration with Claude Code Hooks

You can integrate session awareness with Claude Code's hook system by adding to your `.claude/settings.json`:

```json
{
  "hooks": {
    "onToolCall": "python /path/to/amplifier/scripts/claude_cli.py track \"$TOOL_NAME\" --details \"$TOOL_ARGS\""
  }
}
```

## Architecture

The session awareness module follows Amplifier's modular design philosophy:

```
amplifier/
  claude/                    # Claude integration module
    __init__.py             # Module exports
    session_awareness.py    # Core logic (minimal, focused)
    cli.py                  # Click CLI commands
scripts/
  claude_cli.py             # Standalone CLI entry point
tests/
  test_claude_session_awareness.py  # Comprehensive test suite
```

## Design Principles

Following Amplifier's ruthless simplicity philosophy:

- **File-based storage**: Simple JSON files, no database complexity
- **Automatic cleanup**: Self-maintaining without user intervention
- **Fail silently**: Never disrupts workflow if issues occur
- **Minimal dependencies**: Uses only standard library + logging
- **Clear boundaries**: Modular design allows easy removal if not needed

## Testing

Run the test suite:

```bash
# Run Claude session awareness tests
uv run pytest tests/test_claude_session_awareness.py -v

# Run with coverage
uv run pytest tests/test_claude_session_awareness.py --cov=amplifier.claude
```

## Troubleshooting

### Sessions Not Appearing

- Check that `.data/session_awareness/` directory exists and is writable
- Verify no file permission issues
- Sessions are considered stale after 5 minutes of inactivity

### Activity Log Issues

- Old activity logs with incompatible formats can be safely deleted
- Run `rm .data/session_awareness/activity.jsonl` to reset

### Performance Considerations

- Activity log is trimmed to last 1000 entries automatically
- Session cleanup happens on every activity registration
- File I/O is minimal and optimized for append operations

## Future Enhancements

Potential improvements (keeping with simplicity):

- Inter-session messaging system
- Session activity visualization
- Integration with Amplifier's notification system
- Activity pattern analysis

## Contributing

When contributing to session awareness:

1. Maintain ruthless simplicity - no unnecessary complexity
2. Ensure all tests pass
3. Update documentation for any API changes
4. Follow Amplifier's coding standards
5. Consider impact on existing Claude Code workflows

## License

Part of the Amplifier project. See main project license.