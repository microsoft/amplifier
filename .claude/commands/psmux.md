# psmux - Terminal Multiplexer Orchestration

## Usage

`/psmux <command>`

Commands: `status`, `run <command>`, `parallel <cmd1> ||| <cmd2>`, `setup`, `cleanup`

## Overview

psmux is a native Windows terminal multiplexer (tmux alternative) installed at `$HOME/AppData/Local/psmux/`. Claude Code can programmatically control psmux sessions to run commands in separate panes, monitor their output, and orchestrate parallel workflows.

**Key constraint**: psmux requires a running interactive session. The user must have started psmux in a Windows Terminal tab first. Claude Code cannot start detached sessions headlessly.

## Prerequisites

Before using any psmux command, verify the session is running:

```bash
psmux has-session -t default 2>/dev/null && echo "ready" || echo "no session"
```

If no session exists, tell the user:
> "psmux is not running. Please open a new Windows Terminal tab and type `psmux` to start a session, then try again."

## Commands

### `/psmux status`

Show current psmux state:
```bash
psmux ls 2>&1
psmux list-windows -t default 2>&1
psmux list-panes -t default 2>&1
```

### `/psmux run <command>`

Execute a command in a new psmux pane:
1. Create a new window: `psmux new-window -t default -n "claude-task"`
2. Send the command: `psmux send-keys -t default "<command>" Enter`
3. Wait and capture output: `sleep <reasonable_time> && psmux capture-pane -t default -p`

### `/psmux parallel <cmd1> ||| <cmd2> [||| <cmd3>]`

Run multiple commands in parallel panes:
1. Create a new window: `psmux new-window -t default -n "parallel"`
2. For each additional command, split: `psmux split-window -t default -v` (or `-h`)
3. Send commands to each pane using target syntax: `psmux send-keys -t default:N.M "<cmd>" Enter`
4. Monitor with: `psmux capture-pane -t default:N.M -p`

### `/psmux setup`

Create a standard Claude Code workspace layout:
```bash
# Window 0: main (user's shell - don't touch)
# Window 1: build - for compilation/test runs
psmux new-window -t default -n "build"
# Window 2: monitor - for logs/watchers
psmux new-window -t default -n "monitor"
# Window 3: scratch - for quick commands
psmux new-window -t default -n "scratch"
```

### `/psmux cleanup`

Close Claude Code windows (preserve window 0):
```bash
# Kill all windows except the first one
psmux kill-window -t default:1 2>/dev/null
psmux kill-window -t default:1 2>/dev/null
psmux kill-window -t default:1 2>/dev/null
```

## Core psmux Commands Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `psmux ls` | List sessions | `psmux ls` |
| `psmux list-windows` | List windows | `psmux list-windows -t default` |
| `psmux list-panes` | List panes | `psmux list-panes -t default` |
| `psmux new-window` | Create window | `psmux new-window -t default -n "name"` |
| `psmux split-window` | Split pane | `psmux split-window -t default -v` |
| `psmux send-keys` | Send command | `psmux send-keys -t default "cmd" Enter` |
| `psmux capture-pane` | Read output | `psmux capture-pane -t default -p` |
| `psmux select-window` | Switch window | `psmux select-window -t default:1` |
| `psmux select-pane` | Switch pane | `psmux select-pane -t default -U` |
| `psmux kill-pane` | Close pane | `psmux kill-pane -t default` |
| `psmux kill-window` | Close window | `psmux kill-window -t default:1` |
| `psmux pipe-pane` | Pipe output | `psmux pipe-pane -t default "cat > /tmp/log"` |
| `psmux has-session` | Check exists | `psmux has-session -t default` |

## Target Syntax

Targets follow tmux format: `session:window.pane`
- `-t default` — current window/pane in default session
- `-t default:1` — window index 1
- `-t default:1.0` — window 1, pane 0
- `-t default:build` — window named "build"

## Patterns for Claude Code

### Run a build and capture result
```bash
psmux send-keys -t default:build "dotnet build 2>&1" Enter
sleep 10
psmux capture-pane -t default:build -p
```

### Run tests in parallel
```bash
psmux new-window -t default -n "tests"
psmux send-keys -t default:tests "npm test -- --suite unit" Enter
psmux split-window -t default:tests -v
psmux send-keys -t default:tests "npm test -- --suite integration" Enter
```

### Monitor a log file
```bash
psmux send-keys -t default:monitor "tail -f /c/FuseCP/Portal/logs/portal.log" Enter
```

## Important Notes

- Always check `psmux has-session` before sending commands
- The user's window 0 is their shell — avoid sending commands there unless asked
- Use `capture-pane -p` to read output back (prints to stdout)
- `send-keys` requires `Enter` as a separate argument to press Enter
- psmux is at `$HOME/AppData/Local/psmux/psmux.exe` (in PATH via .bash_profile)
- The psmux session persists as long as the user's terminal tab is open

## Arguments

$ARGUMENTS
