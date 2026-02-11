# Amplifier Component Catalog

Amplifier's modular architecture allows you to mix and match capabilities. This page catalogs all available components in the Amplifier ecosystem—core infrastructure, applications, libraries, bundles, and runtime modules.

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
| **amplifier-app-benchmarks** | Benchmarking and evaluating Amplifier | [amplifier-app-benchmarks](https://github.com/DavidKoleczek/amplifier-app-benchmarks) |

**Note**: When you install `amplifier`, you get the amplifier-app-cli as the executable application.

---

## Libraries

Foundational libraries used by **applications** (not used directly by runtime modules).

| Component | Description | Repository |
|-----------|-------------|------------|
| **amplifier-foundation** | Foundational library for bundles, module resolution, and shared utilities | [amplifier-foundation](https://github.com/microsoft/amplifier-foundation) |

**Architectural Boundary**: Libraries are consumed by applications (like amplifier-app-cli). Runtime modules only depend on amplifier-core and never use these libraries directly.

---

## Bundles

Composable configuration packages that combine providers, behaviors, agents, and context into reusable units.

| Bundle | Description | Repository |
|--------|-------------|------------|
| **recipes** | Multi-step AI agent orchestration with behavior overlays and standalone options | [amplifier-bundle-recipes](https://github.com/microsoft/amplifier-bundle-recipes) |
| **design-intelligence** | Comprehensive design intelligence with 7 specialized agents, design philosophy framework, and knowledge base | [amplifier-bundle-design-intelligence](https://github.com/microsoft/amplifier-bundle-design-intelligence) |
| **issues** | Persistent issue tracking with dependency management, priority scheduling, and session linking for autonomous work | [amplifier-bundle-issues](https://github.com/microsoft/amplifier-bundle-issues) |
| **lsp** | Core Language Server Protocol support for code intelligence operations | [amplifier-bundle-lsp](https://github.com/microsoft/amplifier-bundle-lsp) |
| **lsp-python** | Python code intelligence via Pyright language server (extends lsp bundle) | [amplifier-bundle-lsp-python](https://github.com/microsoft/amplifier-bundle-lsp-python) |
| **lsp-rust** | Rust code intelligence via rust-analyzer language server (extends lsp bundle) | [amplifier-bundle-lsp-rust](https://github.com/microsoft/amplifier-bundle-lsp-rust) |
| **lsp-typescript** | TypeScript/JavaScript code intelligence via typescript-language-server (extends lsp bundle) | [amplifier-bundle-lsp-typescript](https://github.com/microsoft/amplifier-bundle-lsp-typescript) |
| **notify** | Desktop and push notifications when assistant turns complete - works over SSH, supports ntfy.sh for mobile | [amplifier-bundle-notify](https://github.com/microsoft/amplifier-bundle-notify) |
| **observers** | Orchestration pattern where background observer sessions are configured and run in the background, in parallel to provide the main session with actionable observations | [amplifier-bundle-observers](https://github.com/microsoft/amplifier-bundle-observers) |
| **python-dev** | Comprehensive Python development tools - code quality (ruff, pyright), LSP integration, and expert agent | [amplifier-bundle-python-dev](https://github.com/microsoft/amplifier-bundle-python-dev) |
| **shadow** | OS-level sandboxed environments for testing local Amplifier ecosystem changes safely | [amplifier-bundle-shadow](https://github.com/microsoft/amplifier-bundle-shadow) |
| **stories** | Autonomous storytelling engine with 11 specialist agents, 4 output formats (HTML, Excel, Word, PDF), and automated recipes for case studies, release notes, and weekly digests | [amplifier-bundle-stories](https://github.com/microsoft/amplifier-bundle-stories) |
| **ts-dev** | Comprehensive TypeScript/JavaScript development tools - code quality, LSP, and expert agent | [amplifier-bundle-ts-dev](https://github.com/microsoft/amplifier-bundle-ts-dev) |

**Usage**: Bundles are loaded via the `amplifier bundle` commands:

```bash
# Add a bundle to the registry (name auto-derived from bundle metadata)
amplifier bundle add git+https://github.com/microsoft/amplifier-bundle-recipes@main

# Use a bundle by name
amplifier bundle use foundation
amplifier bundle use recipes

# Show current bundle
amplifier bundle current

# Check for bundle updates
amplifier bundle update --check

# Update bundle to latest
amplifier bundle update
```

**Creating Bundles**: See the [Bundle Guide](https://github.com/microsoft/amplifier-foundation/blob/main/docs/BUNDLE_GUIDE.md) for how to create your own bundles.

---

## Runtime Modules

These modules are loaded dynamically at runtime based on your bundle configuration.

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
| **tool-skills** | Load domain knowledge from skills following the Anthropic Skills format | [amplifier-module-tool-skills](https://github.com/microsoft/amplifier-module-tool-skills) |
| **tool-mcp** | Model Context Protocol integration for MCP servers | [amplifier-module-tool-mcp](https://github.com/microsoft/amplifier-module-tool-mcp) |
| **tool-slash-command** | Extensible slash command system with custom commands defined as Markdown files | [amplifier-module-tool-slash-command](https://github.com/microsoft/amplifier-module-tool-slash-command) |

### Context Managers

Manage conversation state and history.

| Module | Description | Repository |
|--------|-------------|------------|
| **context-simple** | In-memory context with automatic compaction | [amplifier-module-context-simple](https://github.com/microsoft/amplifier-module-context-simple) |
| **context-persistent** | File-backed persistent context across sessions | [amplifier-module-context-persistent](https://github.com/microsoft/amplifier-module-context-persistent) |

### Hooks

Extend lifecycle events and observability.

| Module | Description | Repository |
|--------|-------------|------------|
| **hooks-logging** | Unified JSONL event logging to per-session files | [amplifier-module-hooks-logging](https://github.com/microsoft/amplifier-module-hooks-logging) |
| **hooks-redaction** | Privacy-preserving data redaction for secrets/PII | [amplifier-module-hooks-redaction](https://github.com/microsoft/amplifier-module-hooks-redaction) |
| **hooks-approval** | Interactive approval gates for sensitive operations | [amplifier-module-hooks-approval](https://github.com/microsoft/amplifier-module-hooks-approval) |
| **hooks-backup** | Automatic session transcript backup | [amplifier-module-hooks-backup](https://github.com/microsoft/amplifier-module-hooks-backup) |
| **hooks-explanatory** | Inject explanatory output style with educational ★ Insight blocks | [amplifier-module-hooks-explanatory](https://github.com/michaeljabbour/amplifier-module-hooks-explanatory) |
| **hooks-streaming-ui** | Real-time console UI for streaming responses | [amplifier-module-hooks-streaming-ui](https://github.com/microsoft/amplifier-module-hooks-streaming-ui) |
| **hooks-status-context** | Inject git status and datetime into agent context | [amplifier-module-hooks-status-context](https://github.com/microsoft/amplifier-module-hooks-status-context) |
| **hooks-todo-reminder** | Inject todo list reminders into AI context | [amplifier-module-hooks-todo-reminder](https://github.com/microsoft/amplifier-module-hooks-todo-reminder) |
| **hooks-scheduler-cost-aware** | Cost-aware model routing for event-driven orchestration | [amplifier-module-hooks-scheduler-cost-aware](https://github.com/microsoft/amplifier-module-hooks-scheduler-cost-aware) |
| **hooks-scheduler-heuristic** | Heuristic-based model selection scheduler | [amplifier-module-hooks-scheduler-heuristic](https://github.com/microsoft/amplifier-module-hooks-scheduler-heuristic) |
| **hook-shell** | Shell-based hooks with Claude Code format compatibility | [amplifier-module-hook-shell](https://github.com/microsoft/amplifier-module-hook-shell) |

---

## Using Modules

### In Bundles

Modules are loaded via bundles (recommended):

```markdown
---
bundle:
  name: my-bundle
  version: 1.0.0

tools:
  - module: tool-web
    source: git+https://github.com/microsoft/amplifier-module-tool-web@main
  - module: tool-custom
    source: git+https://github.com/you/your-custom-tool@main
---

# My Bundle Instructions

Your system prompt here.
```

### Command Line

```bash
# Add a module override (MODULE_ID + --source)
amplifier module add tool-web --source git+https://github.com/microsoft/amplifier-module-tool-web@main

# See installed modules
amplifier module list

# Get module details
amplifier module show tool-filesystem
```

---

## Community Applications

Applications built by the community using Amplifier.

> **SECURITY WARNING**: Community applications execute arbitrary code in your environment with full access to your filesystem, network, and credentials. Only use applications from sources you trust. Review code before installation.

| Application | Description | Author | Repository |
|-------------|-------------|--------|------------|
| **app-transcribe** | Transform YouTube videos and audio files into searchable transcripts with AI-powered insights | [@robotdad](https://github.com/robotdad) | [amplifier-app-transcribe](https://github.com/robotdad/amplifier-app-transcribe) |
| **app-blog-creator** | AI-powered blog creation with style-aware generation and rich markdown editor | [@robotdad](https://github.com/robotdad) | [amplifier-app-blog-creator](https://github.com/robotdad/amplifier-app-blog-creator) |
| **app-voice** | Desktop voice assistant with native speech-to-speech via OpenAI Realtime API | [@robotdad](https://github.com/robotdad) | [amplifier-app-voice](https://github.com/robotdad/amplifier-app-voice) |
| **app-tool-generator** | AI-powered tool generator for creating custom Amplifier tools | [@samueljklee](https://github.com/samueljklee) | [amplifier-app-tool-generator](https://github.com/samueljklee/amplifier-app-tool-generator) |
| **amplifier-playground** | Interactive environment for building, configuring, and testing Amplifier AI agent sessions | [@samueljklee](https://github.com/samueljklee) | [amplifier-playground](https://github.com/samueljklee/amplifier-playground) |
| **amplifier-lakehouse** | Amplifier on top of your data (daemon and webapp) | [@payneio](https://github.com/payneio) | [amplifier-lakehouse](https://github.com/payneio/lakehouse) |
| **app-session-analyzer** | Analyze Amplifier session logs and generate interesting metrics about your usage! | [@DavidKoleczek](https://github.com/DavidKoleczek) | [amplifier-app-session-analyzer](https://github.com/DavidKoleczek/amplifier-app-session-analyzer) |

**Want to showcase your application?** Submit a PR to add your Amplifier-powered application to this list!

---

## Community Bundles

Bundles built by the community.

> **SECURITY WARNING**: Community bundles execute arbitrary code in your environment with full access to your filesystem, network, and credentials. Only use bundles from sources you trust. Review code before installation.

| Bundle | Description | Author | Repository |
|--------|-------------|--------|------------|
| **deepwiki** | AI-powered open-source project understanding via DeepWiki MCP - ask questions about any public GitHub repository | [@colombod](https://github.com/colombod) | [amplifier-bundle-deepwiki](https://github.com/colombod/amplifier-bundle-deepwiki) |
| **expert-cookbook** | Achieve the State of the Art with Microsoft Amplifier | [@DavidKoleczek](https://github.com/DavidKoleczek) | [amplifier-expert-cookbook](https://github.com/DavidKoleczek/amplifier-expert-cookbook) |
| **memory** | Persistent memory system with automatic capture, progressive disclosure context injection, and event broadcasting | [@michaeljabbour](https://github.com/michaeljabbour) | [amplifier-bundle-memory](https://github.com/michaeljabbour/amplifier-bundle-memory) |
| **perplexity** | Deep web research capabilities using Perplexity's Agentic Research API with citations and cost-aware guidance | [@colombod](https://github.com/colombod) | [amplifier-bundle-perplexity](https://github.com/colombod/amplifier-bundle-perplexity) |
| **browser** | Browser automation for AI agents using agent-browser - JS rendering, auth flows, form filling, and web research | [@samueljklee](https://github.com/samueljklee) | [amplifier-bundle-browser](https://github.com/samueljklee/amplifier-bundle-browser) |
| **tui-tester** | AI-assisted testing for TUI applications - spawn, drive, and capture Textual/terminal apps with visual analysis | [@colombod](https://github.com/colombod) | [amplifier-bundle-tui-tester](https://github.com/colombod/amplifier-bundle-tui-tester) |
| **web-ux-dev** | Web UX development tools - visual regression testing, console debugging, and pre-commit verification (extends browser bundle) | [@colombod](https://github.com/colombod) | [amplifier-bundle-web-ux-dev](https://github.com/colombod/amplifier-bundle-web-ux-dev) |

**Want to share your bundle?** Submit a PR to add your Amplifier bundle to this list!

---

## Community Modules

Modules built by the community.

> **SECURITY WARNING**: Community modules execute arbitrary code in your environment with full access to your filesystem, network, and credentials. Only use modules from sources you trust. Review code before installation.

### Providers

| Module | Description | Author | Repository |
|--------|-------------|--------|------------|
| **provider-bedrock** | AWS Bedrock integration with cross-region inference support for Claude models | [@brycecutt-msft](https://github.com/brycecutt-msft) | [amplifier-module-provider-bedrock](https://github.com/brycecutt-msft/amplifier-module-provider-bedrock) |
| **provider-perplexity** | Perplexity AI integration for chat completions with sonar models | [@colombod](https://github.com/colombod) | [amplifier-module-provider-perplexity](https://github.com/colombod/amplifier-module-provider-perplexity) |
| **provider-openai-realtime** | OpenAI Realtime API for native speech-to-speech interactions | [@robotdad](https://github.com/robotdad) | [amplifier-module-provider-openai-realtime](https://github.com/robotdad/amplifier-module-provider-openai-realtime) |

### Tools

| Module | Description | Author | Repository |
|--------|-------------|--------|------------|
| **tool-youtube-dl** | Download audio and video from YouTube with metadata extraction | [@robotdad](https://github.com/robotdad) | [amplifier-module-tool-youtube-dl](https://github.com/robotdad/amplifier-module-tool-youtube-dl) |
| **tool-whisper** | Speech-to-text transcription using OpenAI's Whisper API | [@robotdad](https://github.com/robotdad) | [amplifier-module-tool-whisper](https://github.com/robotdad/amplifier-module-tool-whisper) |
| **tool-memory** | Persistent memory tool for storing and retrieving facts across sessions | [@michaeljabbour](https://github.com/michaeljabbour) | [amplifier-module-tool-memory](https://github.com/michaeljabbour/amplifier-module-tool-memory) |
| **tool-rlm** | Recursive Language Model (RLM) for processing 10M+ token contexts via sandboxed Python REPL | [@michaeljabbour](https://github.com/michaeljabbour) | [amplifier-module-tool-rlm](https://github.com/michaeljabbour/amplifier-module-tool-rlm) |
| **module-image-generation** | Multi-provider AI image generation with DALL-E, Imagen, and GPT-Image-1 | [@robotdad](https://github.com/robotdad) | [amplifier-module-image-generation](https://github.com/robotdad/amplifier-module-image-generation) |
| **module-style-extraction** | Extract and apply writing style from text samples | [@robotdad](https://github.com/robotdad) | [amplifier-module-style-extraction](https://github.com/robotdad/amplifier-module-style-extraction) |
| **module-markdown-utils** | Markdown parsing, injection, and metadata extraction utilities | [@robotdad](https://github.com/robotdad) | [amplifier-module-markdown-utils](https://github.com/robotdad/amplifier-module-markdown-utils) |

### Hooks

| Module | Description | Author | Repository |
|--------|-------------|--------|------------|
| **hooks-event-broadcast** | Transport-agnostic event broadcasting for streaming UI applications | [@michaeljabbour](https://github.com/michaeljabbour) | [amplifier-module-hooks-event-broadcast](https://github.com/michaeljabbour/amplifier-module-hooks-event-broadcast) |

### Contributing Your Modules

Built something cool? Share it with the community!

1. **Build your module** - See [DEVELOPER.md](./DEVELOPER.md) for guidance
2. **Publish to GitHub** - Make your code publicly reviewable
3. **Test thoroughly** - Ensure it works with current Amplifier versions
4. **Submit a PR** - Add your module to this catalog

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

---

**Ready to build?** Check out [DEVELOPER.md](./DEVELOPER.md) to get started!
