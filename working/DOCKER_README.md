# Dockerized Amplifier

This directory contains Docker setup to run Amplifier in any project directory without installing dependencies locally.

## Quick Start

### Linux/macOS
```bash
# Make the script executable
chmod +x amplify.sh

# Run Amplifier on a project
./amplify.sh /path/to/your/project

# With custom data directory
./amplify.sh /path/to/your/project /path/to/amplifier-data
```

### Windows (PowerShell)
```powershell
# Run Amplifier on a project
.\amplify.ps1 "C:\path\to\your\project"

# With custom data directory
.\amplify.ps1 "C:\path\to\your\project" "C:\path\to\amplifier-data"
```

## Prerequisites

1. **Docker**: Install Docker Desktop
2. **API Keys**: Set one of these environment variables:
   - `ANTHROPIC_API_KEY` - For Claude API
   - AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`) - For AWS Bedrock

## What It Does

The dockerized Amplifier:

1. **Clones Amplifier**: Downloads the latest Amplifier from GitHub
2. **Sets up environment**: Installs Python, Node.js, uv, Claude Code, and all dependencies
3. **Mounts your project**: Makes your target directory available as `/workspace`
4. **Configures Claude Code**: Automatically adds your project directory to Claude Code
5. **Starts interactive session**: Launches Claude Code with the proper context

## Architecture

```
Host System
├── Your Project Directory ──────────► /workspace (mounted)
├── Amplifier Data Directory ───────► /app/amplifier-data (mounted)
└── API Keys (env vars) ─────────────► Forwarded to container

Docker Container
├── /app/amplifier ──────────────────► Cloned Amplifier repository
├── /workspace ─────────────────────► Your mounted project
├── /app/amplifier-data ────────────► Persistent Amplifier data
└── Python + Node.js + Claude Code ► Fully configured environment
```

## Environment Variables

The wrapper scripts automatically forward these environment variables to the container:

- `ANTHROPIC_API_KEY`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION`
- `AWS_REGION`

Set these in your host environment before running the scripts.

## Data Persistence

Amplifier data (memory, knowledge synthesis results, etc.) is stored in the data directory you specify (or `./amplifier-data` by default). This directory is mounted into the container, so data persists between sessions.

## Directory Structure

```
amplifier/
├── Dockerfile ──────────────► Docker image definition
├── amplify.sh ──────────────► Linux/macOS wrapper script
├── amplify.ps1 ─────────────► Windows PowerShell wrapper script
└── DOCKER_README.md ────────► This documentation
```

## Troubleshooting

### Docker Issues
- **"Docker not found"**: Install Docker Desktop and ensure it's in your PATH
- **"Docker not running"**: Start Docker Desktop before running the scripts

### API Key Issues
- **No API keys detected**: Set `ANTHROPIC_API_KEY` or AWS credentials in your environment
- **Authentication failed**: Verify your API keys are correct and have proper permissions

### Path Issues (Windows)
- Use full paths with drive letters: `C:\Users\yourname\project`
- Enclose paths with spaces in quotes: `"C:\My Projects\awesome-app"`

### Container Issues
- **Port conflicts**: Each container gets a unique name with process ID
- **Permission denied**: On Linux, ensure your user can run Docker commands

## Manual Docker Commands

If you prefer to run Docker manually:

```bash
# Build the image
docker build -t amplifier:latest .

# Run with your project
docker run -it --rm \
  -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  -v "/path/to/your/project:/workspace" \
  -v "/path/to/amplifier-data:/app/amplifier-data" \
  amplifier:latest
```

## Customization

To modify the setup:

1. **Edit Dockerfile**: Change Python version, add tools, modify installation
2. **Edit wrapper scripts**: Add new environment variables, change default paths
3. **Edit entrypoint**: Modify the startup sequence inside the container

## Security Notes

- API keys are passed as environment variables (not stored in the image)
- Your project directory is mounted read-write (Amplifier can modify files)
- Amplifier data directory stores persistent data between sessions
- Container runs as root (standard for development containers)