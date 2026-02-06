# Amplifier Component Catalog

Amplifier's modular architecture allows you to mix and match capabilities. This page catalogs all available components in the Amplifier ecosystem—core infrastructure, applications, libraries, collections, and runtime modules.

> **Note**: Component links point to GitHub repositories. We're moving fast, so some may be temporarily unavailable as we reorganize.

---

## Core Infrastructure

The foundational kernel that everything builds on.

| Component | Description | Repository |
|-----------|-------------|------------|
| **amplifier-core** | Ultra-thin kernel for modular AI agent system | [amplifier-core](https://github.com/microsoft/amplifier-core) |

---

## Applications

User-facing applications that compose libraries and modules.

| Component | Description | Repository |
|-----------|-------------|------------|
| **amplifier** | Main Amplifier project and entry point - installs amplifier-app-cli via `uv tool install` | [amplifier](https://github.com/microsoft/amplifier) |
| **amplifier-app-cli** | Reference CLI application implementing the Amplifier platform | [amplifier-app-cli](https://github.com/microsoft/amplifier-app-cli) |
| **amplifier-app-log-viewer** | Web-based log viewer for debugging sessions with real-time updates | [amplifier-app-log-viewer](https://github.com/microsoft/amplifier-app-log-viewer) |
| **amplifier-app-benchmarks** | Benchmarking and evaluating Amplifier  | [amplifier-app-benchmarks](https://github.com/DavidKoleczek/amplifier-app-benchmarks) |
| **Amplifier Lakehouse** | Amplifier on top of your data (daemon and webapp) | [amplifier-lakehouse](https://github.com/payneio/lakehouse) |

**Note**: When you install `amplifier`, you get the amplifier-app-cli as the executable application.

---

## Libraries

Foundational libraries used by **applications** (not used directly by runtime modules).

| Component | Description | Repository |
|-----------|-------------|------------|
| **amplifier-profiles** | Profile and agent loading with inheritance and Mount Plan compilation | [amplifier-profiles](https://github.com/microsoft/amplifier-profiles) |
| **amplifier-collections** | Convention-based collection discovery and management | [amplifier-collections](https://github.com/microsoft/amplifier-collections) |
| **amplifier-module-resolution** | Module source resolution with pluggable strategies | [amplifier-module-resolution](https://github.com/microsoft/amplifier-module-resolution) |
| **amplifier-config** | Three-scope configuration management (user/project/env) | [amplifier-config](https://github.com/microsoft/amplifier-config) |

**Architectural Boundary**: Libraries are consumed by applications (like amplifier-app-cli). Runtime modules only depend on amplifier-core and never use these libraries directly.

---

## Collections

Packaged bundles of profiles, agents, and context for specific domains.

| Collection | Description | Repository |
|------------|-------------|------------|
| **toolkit** | Building sophisticated CLI tools using metacognitive recipes | [amplifier-collection-toolkit](https://github.com/microsoft/amplifier-collection-toolkit) |
| **design-intelligence** | Comprehensive design intelligence capability with specialized agents | [amplifier-collection-design-intelligence](https://github.com/microsoft/amplifier-collection-design-intelligence) |
| **recipes** | Multi-step AI agent orchestration for repeatable workflows | [amplifier-collection-recipes](https://github.com/microsoft/amplifier-collection-recipes) |
| **issues** | Issue management | [amplifier-collection-issues](https://github.com/microsoft/amplifier-collection-issues) |

**Installation**: Collections are **not loaded by default**. Install them explicitly:

```bash
# Install a collection
amplifier collection add git+https://github.com/microsoft/amplifier-collection-toolkit@main

# Update installed collections
amplifier collection refresh

# List installed collections
amplifier collection list
```

---

## Runtime Modules

These modules are loaded dynamically at runtime based on your profile configuration.

### Orchestrators

Control the AI agent execution loop.

| Module | Description | Repository |
|--------|-------------|------------|
| **loop-basic** | Standard sequential execution - simple request/response flow | [amplifier-module-loop-basic](https://github.com/microsoft/amplifier-module-loop-basic) |
| **loop-streaming** | Real-time streaming responses with extended thinking support | [amplifier-module-loop-streaming](https://github.com/microsoft/amplifier-module-loop-streaming) |
| **loop-events** | Event-driven orchestrator with hook integration | [amplifier-module-loop-events](https://github.com/microsoft/amplifier-module-loop-events) |

### Providers

Connect to AI model providers.

| Module | Description | Repository |
|--------|-------------|------------|
| **provider-anthropic** | Anthropic Claude integration (Sonnet 4.5, Opus, etc.) | [amplifier-module-provider-anthropic](https://github.com/microsoft/amplifier-module-provider-anthropic) |
| **provider-openai** | OpenAI GPT integration | [amplifier-module-provider-openai](https://github.com/microsoft/amplifier-module-provider-openai) |
| **provider-azure-openai** | Azure OpenAI with managed identity support | [amplifier-module-provider-azure-openai](https://github.com/microsoft/amplifier-module-provider-azure-openai) |
| **provider-gemini** | Google Gemini integration with 1M context and thinking | [amplifier-module-provider-gemini](https://github.com/microsoft/amplifier-module-provider-gemini) |
| **provider-vllm** | vLLM server integration for self-hosted models | [amplifier-module-provider-vllm](https://github.com/microsoft/amplifier-module-provider-vllm) |
| **provider-ollama** | Local Ollama models for offline development | [amplifier-module-provider-ollama](https://github.com/microsoft/amplifier-module-provider-ollama) |
| **provider-mock** | Mock provider for testing without API calls | [amplifier-module-provider-mock](https://github.com/microsoft/amplifier-module-provider-mock) |

### Tools

Extend AI capabilities with actions.

| Module | Description | Repository |
|--------|-------------|------------|
| **tool-filesystem** | File operations (read, write, edit, list, glob) | [amplifier-module-tool-filesystem](https://github.com/microsoft/amplifier-module-tool-filesystem) |
| **tool-bash** | Shell command execution | [amplifier-module-tool-bash](https://github.com/microsoft/amplifier-module-tool-bash) |
| **tool-web** | Web search and content fetching | [amplifier-module-tool-web](https://github.com/microsoft/amplifier-module-tool-web) |
| **tool-search** | Code search capabilities (grep/glob) | [amplifier-module-tool-search](https://github.com/microsoft/amplifier-module-tool-search) |
| **tool-task** | Agent delegation and sub-session spawning | [amplifier-module-tool-task](https://github.com/microsoft/amplifier-module-tool-task) |
| **tool-todo** | AI self-accountability and todo list management | [amplifier-module-tool-todo](https://github.com/microsoft/amplifier-module-tool-todo) |

### Context Managers

Manage conversation state and history.

| Module | Description | Repository |
|--------|-------------|------------|
| **context-simple** | In-memory context with automatic compaction | [amplifier-module-context-simple](https://github.com/microsoft/amplifier-module-context-simple) |
| **context-persistent** | File-backed persistent context across sessions | [amplifier-module-context-persistent](https://github.com/microsoft/amplifier-module-context-persistent) |

### Memory System

Persistent memory and session tracking for AI learning across sessions.

> **Bundling Recommendation**: These three modules work together as a complete memory system. 
> For best results, bundle all three: **tool-memory** (storage), **hooks-memory-capture** (automatic capture), 
> and **context-memory** (context injection). They pair well with **context-persistent** for full session continuity.

| Module | Description | Repository |
|--------|-------------|------------|
| **tool-memory** | Persistent memory with FTS5 search, observation types, session tracking | [amplifier-module-tool-memory](https://github.com/michaeljabbour/amplifier-module-tool-memory) |
| **context-memory** | Inject relevant memories at session start using progressive disclosure | [amplifier-module-context-memory](https://github.com/michaeljabbour/amplifier-module-context-memory) |
| **hooks-memory-capture** | Automatic observation capture from tool outputs via tool:post | [amplifier-module-hooks-memory-capture](https://github.com/michaeljabbour/amplifier-module-hooks-memory-capture) |
| **hooks-event-broadcast** | Relay kernel events to WebSocket/transport for desktop apps | [amplifier-module-hooks-event-broadcast](https://github.com/michaeljabbour/amplifier-module-hooks-event-broadcast) |

**Memory System Features:**
- **Observation Types**: bugfix, feature, refactor, change, discovery, decision
- **Session Tracking**: Track sessions with request/investigated/learned/completed summaries
- **FTS5 Full-Text Search**: Fast search across all memory content
- **Progressive Disclosure**: Index view with token estimates, full details on demand
- **Automatic Capture**: hooks-memory-capture captures learnings from tool outputs

### Hooks

Extend lifecycle events and observability.

| Module | Description | Repository |
|--------|-------------|------------|
| **hooks-logging** | Unified JSONL event logging to per-session files | [amplifier-module-hooks-logging](https://github.com/microsoft/amplifier-module-hooks-logging) |
| **hooks-redaction** | Privacy-preserving data redaction for secrets/PII | [amplifier-module-hooks-redaction](https://github.com/microsoft/amplifier-module-hooks-redaction) |
| **hooks-approval** | Interactive approval gates for sensitive operations | [amplifier-module-hooks-approval](https://github.com/microsoft/amplifier-module-hooks-approval) |
| **hooks-backup** | Automatic session transcript backup | [amplifier-module-hooks-backup](https://github.com/microsoft/amplifier-module-hooks-backup) |
| **hooks-streaming-ui** | Real-time console UI for streaming responses | [amplifier-module-hooks-streaming-ui](https://github.com/microsoft/amplifier-module-hooks-streaming-ui) |
| **hooks-status-context** | Inject git status and datetime into agent context | [amplifier-module-hooks-status-context](https://github.com/microsoft/amplifier-module-hooks-status-context) |
| **hooks-todo-reminder** | Inject todo list reminders into AI context | [amplifier-module-hooks-todo-reminder](https://github.com/microsoft/amplifier-module-hooks-todo-reminder) |
| **hooks-scheduler-cost-aware** | Cost-aware model routing for event-driven orchestration | [amplifier-module-hooks-scheduler-cost-aware](https://github.com/microsoft/amplifier-module-hooks-scheduler-cost-aware) |
| **hooks-scheduler-heuristic** | Heuristic-based model selection scheduler | [amplifier-module-hooks-scheduler-heuristic](https://github.com/microsoft/amplifier-module-hooks-scheduler-heuristic) |

---

## Using Modules

### In Profiles

Modules are loaded via profiles (recommended):

```yaml
# ~/.amplifier/profiles/my-profile.md
---
profile:
  name: my-profile
  extends: base

tools:
  - module: tool-web
    source: git+https://github.com/microsoft/amplifier-module-tool-web@main
  - module: tool-custom
    source: git+https://github.com/you/your-custom-tool@main
---
```

### Command Line

```bash
# See installed modules
amplifier module list

# Get module details
amplifier module show tool-filesystem
```

---

## Community Applications

Applications built by the community using Amplifier.

> **⚠️ SECURITY WARNING**
>
> Community applications execute arbitrary code in your environment with full access to your filesystem, network, and credentials.
>
> - **Only use applications from sources you absolutely trust**
> - **Review application code before installation** - read every line
> - **Understand what the application does** - don't trust descriptions alone
> - **Use at your own risk** - no warranties, guarantees, or security vetting
>
> You are responsible for what runs on your machine. When in doubt, don't install it.

| Application | Description | Author | Repository | Compatible | Status |
|-------------|-------------|--------|------------|------------|--------|
| **app-transcribe** | Transform YouTube videos and audio files into searchable transcripts with AI-powered insights (uses tool-youtube-dl and tool-whisper) | @robotdad | [amplifier-app-transcribe](https://github.com/robotdad/amplifier-app-transcribe) | Amplifier 0.1.x | Active |
| **app-blog-creator** | AI-powered blog creation with style-aware generation and rich markdown editor (web interface designed with design-intelligence collection, uses image-generation, style-extraction, and markdown-utils modules) | @robotdad | [amplifier-app-blog-creator](https://github.com/robotdad/amplifier-app-blog-creator) | Amplifier 0.1.x | Active |
| **app-voice** | Desktop voice assistant with native speech-to-speech via OpenAI Realtime API (uses provider-openai-realtime) | @robotdad | [amplifier-app-voice](https://github.com/robotdad/amplifier-app-voice) | Amplifier 0.1.x | Experimental |
| **amplifier-app-tool-generator** | AI-powered tool generator for creating custom Amplifier tools | @samueljklee | [amplifier-app-tool-generator](https://github.com/samueljklee/amplifier-app-tool-generator) | Amplifier | Active |
| **amplifier-playground** | Interactive environment for building, configuring, and testing Amplifier AI agent sessions with web UI and CLI | @samueljklee | [amplifier-playground](https://github.com/samueljklee/amplifier-playground) | Amplifier | Active |

**Want to showcase your application?** Submit a PR to add your Amplifier-powered application to this list!

---

## Community Modules

> **⚠️ CRITICAL SECURITY WARNING**
>
> Community modules execute arbitrary code in your environment with full access to your filesystem, network, and credentials.
>
> - **Only use modules from sources you absolutely trust**
> - **Review module code before installation** - read every line
> - **Understand what the module does** - don't trust descriptions alone
> - **Use at your own risk** - no warranties, guarantees, or security vetting
> - **Assume malicious intent** until proven otherwise
>
> You are responsible for what runs on your machine. When in doubt, don't install it.

### Contributing Your Modules

Built something cool? Share it with the community!

**To add your module to this catalog:**

1. **Build your module** - See [DEVELOPER.md](./DEVELOPER.md) for guidance
2. **Publish to GitHub** - Make your code publicly reviewable
3. **Test thoroughly** - Ensure it works with current Amplifier versions
4. **Submit a PR** - Add your module to the "Community Modules" section below with:
   - Module name and description
   - GitHub repository link
   - Your name/organization
   - Compatible Amplifier version
   - **Clear documentation** in your repo's README

**Module submission guidelines:**
- Must follow Amplifier module conventions
- Must include comprehensive README
- Must include tests
- Must specify compatible Amplifier versions
- Source code must be publicly available for review

### Community-Contributed Modules

- **provider-bedrock** by @brycecutt-msft - AWS Bedrock integration with cross-region inference support for Claude models
  - Repository: https://github.com/brycecutt-msft/amplifier-module-provider-bedrock
  - Compatible: Amplifier 0.1.x
  - Status: Active

- **tool-mcp** by @robotdad - Model Context Protocol integration enabling connection to MCP servers with Tools, Resources, and Prompts support
  - Repository: https://github.com/robotdad/amplifier-module-tool-mcp
  - Compatible: Amplifier 0.1.x
  - Status: Active

- **tool-skills** by @robotdad - Load domain knowledge from skills with progressive disclosure and Anthropic Skills support
  - Repository: https://github.com/robotdad/amplifier-module-tool-skills
  - Compatible: Amplifier 0.1.x
  - Status: Active

- **collection-ddd** by @robotdad - Document-Driven Development collection with 5 specialized workflow agents for evolving existing codebases
  - Repository: https://github.com/robotdad/amplifier-collection-ddd
  - Compatible: Amplifier 0.1.x
  - Status: Active

- **collection-spec-kit** by @robotdad - Specification-Driven Development collection with 8 specialized agents and constitutional governance for greenfield development
  - Repository: https://github.com/robotdad/amplifier-collection-spec-kit
  - Compatible: Amplifier 0.1.x
  - Status: Experimental

- **tool-youtube-dl** by @robotdad - Download audio and video from YouTube with metadata extraction and screenshot capture
  - Repository: https://github.com/robotdad/amplifier-module-tool-youtube-dl
  - Compatible: Amplifier 0.1.x
  - Status: Active

- **tool-whisper** by @robotdad - Speech-to-text transcription using OpenAI's Whisper API with timestamped segments
  - Repository: https://github.com/robotdad/amplifier-module-tool-whisper
  - Compatible: Amplifier 0.1.x
  - Status: Active

- **module-image-generation** by @robotdad - Multi-provider AI image generation with DALL-E, Imagen, and GPT-Image-1 support
  - Repository: https://github.com/robotdad/amplifier-module-image-generation
  - Compatible: Amplifier 0.1.x
  - Status: Active

- **module-style-extraction** by @robotdad - Extract and apply writing style from text samples for style-aware content generation
  - Repository: https://github.com/robotdad/amplifier-module-style-extraction
  - Compatible: Amplifier 0.1.x
  - Status: Active

- **module-markdown-utils** by @robotdad - Markdown parsing, injection, and metadata extraction utilities
  - Repository: https://github.com/robotdad/amplifier-module-markdown-utils
  - Compatible: Amplifier 0.1.x
  - Status: Active

- **provider-openai-realtime** by @robotdad - OpenAI Realtime API provider enabling native speech-to-speech interactions with ultra-low latency
  - Repository: https://github.com/robotdad/amplifier-module-provider-openai-realtime
  - Compatible: Amplifier 0.1.x
  - Status: Experimental

- **bundle-loop-safety** by @michaeljabbour - Loop detection and safe orchestration with automatic circuit-breaking to prevent runaway agent loops
  - Repository: https://github.com/michaeljabbour/amplifier-bundle-loop-safety
  - Compatible: Amplifier 0.1.x
  - Status: Active

- **hooks-insight-blocks** by @michaeljabbour - Generate structured insight blocks that inject contextual knowledge and explanations into agent responses
  - Repository: https://github.com/michaeljabbour/amplifier-module-hooks-insight-blocks
  - Compatible: Amplifier 0.1.x
  - Status: Active

---

## Building Your Own Modules

Amplifier can help you build Amplifier modules! See [DEVELOPER.md](./DEVELOPER.md) for how to use AI to create custom modules with minimal manual coding.

The modular architecture makes it easy to:
- Extend capabilities with new tools
- Add support for new AI providers
- Create domain-specific agents
- Build custom interfaces (web, mobile, voice)
- Experiment with new orchestration strategies

---

## Module Architecture

All modules follow the same pattern:

1. **Entry point**: Implement `mount(coordinator, config)` function
2. **Registration**: Register capabilities with the coordinator
3. **Isolation**: Handle errors gracefully, never crash the kernel
4. **Contracts**: Follow one of the stable interfaces (Tool, Provider, Hook, etc.)

For technical details, see:
- [amplifier-core](https://github.com/microsoft/amplifier-core) - Kernel interfaces and protocols
- [amplifier-dev docs](https://github.com/microsoft/amplifier-dev/tree/main/docs) - Architecture guides

---

## Component Summary

**Total Components**: 38

- **Core**: 1 (amplifier-core)
- **Applications**: 3 (amplifier, amplifier-app-cli, amplifier-app-log-viewer)
- **Libraries**: 4 (profiles, collections, module-resolution, config)
- **Collections**: 3 (toolkit, design-intelligence, recipes)
- **Runtime Modules**: 28
  - Orchestrators: 3
  - Providers: 5
  - Tools: 7 (including tool-memory)
  - Context: 3 (including context-memory)
  - Memory: 4 (tool-memory, context-memory, hooks-memory-capture, hooks-event-broadcast)
  - Hooks: 11 (including memory-capture, event-broadcast)

---

**Ready to build?** Check out [DEVELOPER.md](./DEVELOPER.md) to get started!
