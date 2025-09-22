# Amplifier UI Integration

## Overview

This branch introduces a modern, web-based user interface for Microsoft Amplifier, transforming the powerful command-line toolkit into an intuitive visual development environment. The UI enables developers to manage multiple AI development sessions simultaneously through a clean, Manus-style interface.

## What's New

### 🎨 **Modern Web Interface**
- **Three-panel layout** following familiar UX patterns (Manus/ChatGPT style)
- **React 18 + Vite** for fast development and optimized performance
- **Dark theme** with professional accessibility and contrast
- **Responsive design** that works across desktop and mobile devices

### 🤖 **Multi-Session Management**
- **Parallel session creation** for different development contexts
- **Real-time session monitoring** with cost, duration, and status tracking
- **Seamless session switching** without losing workflow context
- **Visual session indicators** with color-coded health monitoring

### 💬 **Enhanced Chat Interface**
- **Rich text editor** with multi-line support and formatting toolbar
- **File attachment handling** with document preview and download
- **Task progress tracking** with visual completion indicators
- **AI-powered suggestions** for contextual follow-up actions
- **Real-time message exchange** with Claude agents

### ⚡ **Real Claude Code Integration**
- **Direct integration** with Microsoft Amplifier's Claude Code SDK
- **Actual session creation** using the existing toolkit infrastructure
- **Agent marketplace** with deployment of specialized AI assistants
- **Project directory management** with git worktree support

## Quick Start

### Prerequisites
```bash
# Node.js and package manager
node --version  # 22+
pnpm --version  # latest

# Python environment
python3 --version  # 3.11+
pip3 --version     # latest

# Claude Code CLI
npm install -g @anthropic-ai/claude-code
claude --version   # 1.0.120+
```

### Environment Setup
```bash
# Set Anthropic API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Navigate to UI directory
cd ui/

# Install dependencies
pnpm install

# Start backend (in separate terminal)
python3 amplifier-backend-real.py

# Start frontend development server
pnpm run dev
```

## Key Features

### Session Management
- **Create Sessions**: One-click session creation with custom naming
- **Session List**: Left sidebar showing all active sessions with status
- **Cost Tracking**: Real-time monitoring of API usage and expenses
- **Duration Tracking**: Live session timing and activity monitoring

### Agent Marketplace
- **Specialized Agents**: Pre-configured AI assistants for different tasks
- **One-Click Deployment**: Easy agent assignment to sessions
- **Status Monitoring**: Live indicators for agent activity
- **Categories**: Organized by Development, Analysis, and Knowledge tasks

### Chat Interface
- **Message History**: Persistent conversation logs per session
- **Rich Formatting**: Support for code blocks, lists, and emphasis
- **File Attachments**: Upload and reference project files
- **Suggested Actions**: AI-generated follow-up recommendations
- **Task Completion**: Visual progress tracking with checkmarks

## Security

- **Environment Variables**: API keys managed through environment variables only
- **No Hardcoded Secrets**: All sensitive data externalized
- **CORS Configuration**: Proper cross-origin request handling
- **Session Isolation**: Each session runs in isolated environments
- **Input Validation**: Sanitized user inputs and file uploads

This integration brings Microsoft Amplifier into the modern web era, making powerful AI development tools accessible through an intuitive visual interface.
