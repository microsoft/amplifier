# Claude Code Hook Logs

The `.claude/logs` directory contains file-based logs from Claude Code hooks for debugging and monitoring.

## Log Files

Each hook creates its own timestamped log file:

- `stop_hook_YYYYMMDD.log` - Memory extraction hook logs
- `session_start_YYYYMMDD.log` - Session initialization and memory retrieval logs
- `post_tool_use_YYYYMMDD.log` - Claim validation hook logs

## Log Format

Logs follow this format:

```
[YYYY-MM-DD HH:MM:SS.mmm] [hook_name] [LEVEL] message
```

Log levels:

- `INFO` - General information about hook execution
- `DEBUG` - Detailed debugging information
- `WARN` - Warning conditions
- `ERROR` - Error conditions with stack traces

## Log Rotation

Logs are automatically cleaned up after 7 days to prevent disk usage issues.

## Viewing Logs

To tail a specific hook's logs:

```bash
tail -f .claude/logs/stop_hook_*.log
```

To search for errors:

```bash
grep ERROR .claude/logs/*.log
```

To see today's logs:

```bash
ls -la .claude/logs/*_$(date +%Y%m%d).log
```

## Implementation

The logging is implemented in `.claude/tools/hook_logger.py` which provides:

- Automatic log directory creation
- Timestamped log files per hook
- Multiple log levels
- JSON preview capabilities
- Automatic cleanup of old logs
- Dual output to both file and stderr
