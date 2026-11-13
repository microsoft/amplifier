# Amplifier Component Catalog

Amplifier's modular architecture allows you to mix and match capabilities. This page catalogs public components in the Amplifier ecosystem—core infrastructure, applications, libraries, bundles, runtime modules, and development tools.

**Scope and status (reviewed 2026-11-13):** The Microsoft entries cover public Amplifier ecosystem repositories, including embedded implementations linked from their owning repository. Community entries are curated contributions, not an exhaustive inventory of GitHub. Public visibility does not imply a stable API, a supported release, or cross-engine feature parity. Experimental, preview, and deprecated components are identified where their owners document that status; follow each repository for current contracts, installation, and qualification evidence.

---

## Core Infrastructure

The foundational kernel that everything builds on.

| Component | Description | Repository |
|-----------|-------------|------------|
| **amplifier-core** | Native Rust kernel for modular AI agent systems, with Python bindings and Node/C-ABI interfaces in the same repository | [amplifier-core](https://github.com/microsoft/amplifier-core) |

Core's [workspace](https://github.com/microsoft/amplifier-core/blob/main/Cargo.toml), [Python binding](https://github.com/microsoft/amplifier-core/tree/main/bindings/python), [Node binding](https://github.com/microsoft/amplifier-core/tree/main/bindings/node), and [C-ABI crate](https://github.com/microsoft/amplifier-core/tree/main/crates/amplifier-ffi) are source components, not separate loop repositories. Binding source presence does not establish released artifacts, platform qualification, or identical history APIs.

---

## Applications

User-facing applications that compose libraries and modules.

| Component | Description | Repository |
|-----------|-------------|------------|
| **amplifier** | Main Amplifier project and entry point - installs amplifier-app-cli via `uv tool install` | [amplifier](https://github.com/microsoft/amplifier) |
| **amplifier-distro** | Curated distribution of Amplifier experiences | [amplifier-distro](https://github.com/microsoft/amplifier-distro) |
| **amplifier-app-actions** | AI-powered GitHub Actions for automated issue triage and PR review | [amplifier-app-actions](https://github.com/microsoft/amplifier-app-actions) |
| **amplifier-app-cli** | Reference CLI application implementing the Amplifier platform | [amplifier-app-cli](https://github.com/microsoft/amplifier-app-cli) |
| **amplifier-unified** | Local, authenticated workspace and web app for chat, voice, and work with configured Amplifier bundles and tools | [amplifier-unified](https://github.com/microsoft/amplifier-unified) |
| **amplifier-app-tui** | Optional native terminal client for Unified, with an explicit standalone mode; connected mode is a prerelease with draft contracts, not full cross-client parity | [amplifier-app-tui](https://github.com/microsoft/amplifier-app-tui) |
| **amplifier-client-macos** | Native Mac client connecting to an existing Unified host, with quick chat, notifications, and optional Tempo companion; early public preview | [amplifier-client-macos](https://github.com/microsoft/amplifier-client-macos) |
| **amplifier-agent** | Public Python/TypeScript agent/session/turn bindings and an owned engine composing pinned Core, streaming-loop, context, provider, and tool components; HTTP and ACP faces serve other clients | [amplifier-agent](https://github.com/microsoft/amplifier-agent) |
| **amplifier-drumbeat** | An automation engine for long-running agent sessions — write an automation as a markdown file (a schedule, a notify policy, an ordered list of steps) and drumbeat runs it in a pinned agent session, on time, unattended, on top of amplifier-agent | [amplifier-drumbeat](https://github.com/microsoft/amplifier-drumbeat) |
| **amplifier-app-nanoclaw** | Setup and integration for running [NanoClaw](https://nanoclaw.dev) — a small, auditable AI-assistant harness that routes messages from channels (CLI, Telegram, Discord, WhatsApp) into per-agent Docker containers — on top of amplifier-agent as the agent backend | [amplifier-app-nanoclaw](https://github.com/microsoft/amplifier-app-nanoclaw) |
| **amplifier-app-opencode** | One-command launcher (`amplifier-opencode`) that auto-configures the [opencode](https://opencode.ai) TUI on top of amplifier-agent's OpenAI-compatible HTTP face — discovers live models from `/v1/models`, writes a working opencode config from that discovery, and starts the backend server if needed | [amplifier-app-opencode](https://github.com/microsoft/amplifier-app-opencode) |
| **amplifier-app-paperclip** | Setup and integration for running [paperclip](https://github.com/paperclipai/paperclip) with the `amplifier_local` adapter — paperclip agents run on the Amplifier engine via amplifier-agent, per-turn | [amplifier-app-paperclip](https://github.com/microsoft/amplifier-app-paperclip) |
| **amplifier-app-simulated-user-research** | Automated product-audit rounds: seeded scratch instance, real-browser persona sessions and design reviews, synthesized into an evidence-tiered findings spec behind a human gate | [amplifier-app-simulated-user-research](https://github.com/microsoft/amplifier-app-simulated-user-research) |
| **amplifier-eval-harness** | Configurable test harness for evaluating Amplifier bundles across scenarios and providers in isolated Digital Twin Universe environments. Captures wall time, LLM time, per-call tokens, cache traffic, request counts, and per-`provider/model` breakdowns across the full session tree (parent + every sub-session) for cross-bundle and cross-provider comparison. | [amplifier-eval-harness](https://github.com/microsoft/amplifier-eval-harness) |
| **amplifier-app-log-viewer** | Web-based log viewer for debugging sessions with real-time updates | [amplifier-app-log-viewer](https://github.com/microsoft/amplifier-app-log-viewer) |
| **amplifier-app-benchmarks** | Benchmarking and evaluating Amplifier | [amplifier-app-benchmarks](https://github.com/DavidKoleczek/amplifier-app-benchmarks) |
| **amplifierd** | Localhost HTTP daemon exposing amplifier-core and amplifier-foundation over REST and SSE - drive sessions from any language or framework | [amplifierd](https://github.com/microsoft/amplifierd) |
| **amplifier-chat** | Chat UI plugin for amplifierd - browser-based conversational interface for creating and managing Amplifier sessions | [amplifier-chat](https://github.com/microsoft/amplifier-chat) |
| **amplifier-voice** | Voice plugin for amplifierd - WebRTC voice interface using the OpenAI Realtime API, standalone or as a plugin | [amplifier-voice](https://github.com/microsoft/amplifier-voice) |
| **amplifier-app-aiuser** | Reusable "AI User" that drives a lower-level AI session toward a goal across multiple turns given a persona, scenario, and invocation guide, then reports a verdict — built to be embedded for testing and evaluation. | [amplifier-app-aiuser](https://github.com/microsoft/amplifier-app-aiuser) |
| **amplifier-app-openclaw** | OpenClaw skill for the Amplifier project | [amplifier-app-openclaw](https://github.com/microsoft/amplifier-app-openclaw) |
| **amplifier-browser-bridge** | Lets an agent running on one machine drive the user's real, logged-in Microsoft Edge browser on other devices — desktop or Android — over their own Tailscale network, with no third-party relay | [amplifier-browser-bridge](https://github.com/microsoft/amplifier-browser-bridge) |
| **amplifier-app-repo-weaver** | Repo Weaver app for the Amplifier project | [amplifier-app-repo-weaver](https://github.com/microsoft/amplifier-app-repo-weaver) |
| **amplifier-app-wiki-weaver** | Wiki Weaver LLM-WIKI bundle for the Amplifier project | [amplifier-app-wiki-weaver](https://github.com/microsoft/amplifier-app-wiki-weaver) |
| **amplifier-context-intelligence** | Context Intelligence services for the Amplifier project | [amplifier-context-intelligence](https://github.com/microsoft/amplifier-context-intelligence) |
| **amplifier-workspace** | Workspace tool for the Amplifier project | [amplifier-workspace](https://github.com/microsoft/amplifier-workspace) |
| **amplifier-constellation-runtime** | Standalone native Rust ACP engine with providers, durable sessions, and serial runtime tool dispatch; separate from Core-loaded loop modules | [amplifier-constellation-runtime](https://github.com/microsoft/amplifier-constellation-runtime) |
| **amplifier-constellation-instance** | Independent installed agents with setup, profiles, authorized context, and management UI/API | [amplifier-constellation-instance](https://github.com/microsoft/amplifier-constellation-instance) |
| **amplifier-constellation-observatory** | Fleet management and observation across machines with ACP and optional management adapters | [amplifier-constellation-observatory](https://github.com/microsoft/amplifier-constellation-observatory) |
| **amplifier-constellation-conversations** | Browser conversations for people and ACP agents with threads, permissions, and source context | [amplifier-constellation-conversations](https://github.com/microsoft/amplifier-constellation-conversations) |
| **amplifier-persona-workshop** | Communication and working-style profile authoring with portable AGENTS.md, SOUL.md, and native exports | [amplifier-persona-workshop](https://github.com/microsoft/amplifier-persona-workshop) |
| **amplifier-acp-slack** | Slack conversation and presentation adapter for ACP-compatible agents | [amplifier-acp-slack](https://github.com/microsoft/amplifier-acp-slack) |
| **amplifier-acp-teams** | Teams conversation adapter for ACP-compatible agents; live tenant validation pending | [amplifier-acp-teams](https://github.com/microsoft/amplifier-acp-teams) |
| **amplifier-acp-lab** | Repeatable collaborative-agent experiments with participation observations and separate artifact evaluations | [amplifier-acp-lab](https://github.com/microsoft/amplifier-acp-lab) |
| **amplifier-acp-minecraft** | Independent ACP agents as Minecraft players with scoped game tools and bounded collaboration | [amplifier-acp-minecraft](https://github.com/microsoft/amplifier-acp-minecraft) |

**Note**: When you install `amplifier`, you get the amplifier-app-cli as the executable application. `amplifierd` is a separate daemon that exposes Amplifier capabilities over HTTP, and `amplifier-chat` and `amplifier-voice` are plugins that extend it with web-based chat and voice interfaces.

---

## Documentation & Learning

These are the canonical documentation and learning sites for the Amplifier ecosystem. They reflect the framework but do not run it.

| Component | Description | Repository |
|-----------|-------------|------------|
| **amplifier-docs** | Documentation for the Amplifier project | [amplifier-docs](https://github.com/microsoft/amplifier-docs) |
| **amplifier-constellation** | Starting point, vision, component map, and shared contracts for independent persistent agents | [amplifier-constellation](https://github.com/microsoft/amplifier-constellation) |
| **amplifier-converge** | Vision, collaboration contracts, and practical guides for people and agents leading larger bodies of work; distinct from the executable Converge bundle | [amplifier-converge](https://github.com/microsoft/amplifier-converge) |
| **amplifier-smart-tools-catalog** | Discoverable Smart Tools catalog with upstream manifest snapshots and provenance; listing is not installation or qualification | [amplifier-smart-tools-catalog](https://github.com/microsoft/amplifier-smart-tools-catalog) |

Previously listed `michaeljabbour/amplifier-app-learn` was unavailable at review time; its public status or replacement could not be confirmed.

---

## Development Tools & Skills

Specifications, library-first CLIs, and skills that can be used with Amplifier or other agent hosts. These are not all runtime modules or bundles.

| Component | Description | Repository |
|-----------|-------------|------------|
| **amplifier-smart-tools** | Smart Tools specification, machine-checkable conformance kit, and authoring skill for packaging domain expertise into tools any agent can use | [amplifier-smart-tools](https://github.com/microsoft/amplifier-smart-tools) |
| **amplifier-smart-tool-creator** | Scaffolds, validates, reviews, and adds model-backed capabilities to Smart Tools using a selected agent provider | [amplifier-smart-tool-creator](https://github.com/microsoft/amplifier-smart-tool-creator) |
| **amplifier-smart-tool-digital-twin-universe** | Library-first CLI for isolated Docker Compose environments and model-assisted setup; distinct from the Digital Twin Universe bundle | [amplifier-smart-tool-digital-twin-universe](https://github.com/microsoft/amplifier-smart-tool-digital-twin-universe) |
| **amplifier-smart-tool-reality-check** | Evidence-oriented app testing through browsers, desktops, or Digital Twin Universe environments; Smart Tool and optional MCP app, not a CI/release gate | [amplifier-smart-tool-reality-check](https://github.com/microsoft/amplifier-smart-tool-reality-check) |
| **amplifier-smart-tool-team-pulse** | Library-first CLI for a team's mined corpus, source-cited model-backed answers, and explicit reflection-answer submission | [amplifier-smart-tool-team-pulse](https://github.com/microsoft/amplifier-smart-tool-team-pulse) |
| **amplifier-smart-tool-tmux** | Library-first CLI for observing tmux fleets and, under explicit confirmation, acting on sessions; model-backed triage uses amplifier-agent | [amplifier-smart-tool-tmux](https://github.com/microsoft/amplifier-smart-tool-tmux) |
| **amplifier-drumpack-tmux** | Drumbeat drumpack placing the tmux Smart Tool and its agent-facing card on an automation's PATH | [amplifier-drumpack-tmux](https://github.com/microsoft/amplifier-drumpack-tmux) |
| **amplifier-skill-revisioner** | Skills for finding and testing risky assumptions in project visions and generating a review UX | [amplifier-skill-revisioner](https://github.com/microsoft/amplifier-skill-revisioner) |

---

## Libraries

Application-facing composition libraries, plus explicitly optional support contracts.

| Component | Description | Repository |
|-----------|-------------|------------|
| **amplifier-foundation** | Foundational library for bundles, module resolution, and shared utilities | [amplifier-foundation](https://github.com/microsoft/amplifier-foundation) |
| **amplifier-lib** | Python library for Amplifier | [amplifier-lib](https://github.com/microsoft/amplifier-lib) |
| **amplifier-module-resolution** | Module resolution library | [amplifier-module-resolution](https://github.com/microsoft/amplifier-module-resolution) |
| **amplifier-lib-decisions** | Experimental, optional typed contracts for bounded predicate, choice, and ordinal-score requests; no Core or Foundation dependency | [amplifier-lib-decisions](https://github.com/microsoft/amplifier-lib-decisions) |

**Architectural Boundary**: Core defines runtime module contracts; Foundation and module-resolution helpers are application-facing, not runtime-module dependencies. The optional decision integrations explicitly use the separate, Core/Foundation-independent decision library; that does not authorize runtime modules to import Foundation or applications.

---

## Bundles

Composable configuration packages that combine providers, behaviors, agents, and context into reusable units.

| Bundle | Description | Repository |
|--------|-------------|------------|
| **a2a** | Agent-to-Agent communication via Google's A2A protocol — discovery, trust, message routing across Amplifier sessions | [amplifier-bundle-a2a](https://github.com/microsoft/amplifier-bundle-a2a) |
| **amplifier-tester** | Validates Amplifier ecosystem changes (core, modules, bundles, foundation, app-cli) in isolated Digital Twin Universe environments — dynamically generates profiles, mirrors repos to Gitea, and runs targeted validation checks | [amplifier-bundle-amplifier-tester](https://github.com/microsoft/amplifier-bundle-amplifier-tester) |
| **alexa-tester** | Alexa custom skill testing — 3 specialist agents (operator, voice-tester, debugger) driving signed Alexa request envelopes against a live skill endpoint, with response conformance checks and utterance routing verified against Amazon's real NLU | [amplifier-bundle-alexa-tester](https://github.com/microsoft/amplifier-bundle-alexa-tester) |
| **android-tester** | Android app testing on emulators and devices — 3 specialist agents (operator, visual-tester, debugger) driving apps via the accessibility tree with screenshot-based visual verification, plus emulator provisioning and host diagnostics | [amplifier-bundle-android-tester](https://github.com/microsoft/amplifier-bundle-android-tester) |
| **attractor** | Experimental opinionated agents, bundles, examples, and authoring guidance over Dot Runner's coding-agent and pipeline loops; not a separate current loop implementation | [amplifier-bundle-attractor](https://github.com/microsoft/amplifier-bundle-attractor) |
| **browser** | Browser-hosted Amplifier runtime using Pyodide and a JavaScript facade; distinct from community browser-automation bundles | [amplifier-bundle-browser](https://github.com/microsoft/amplifier-bundle-browser) |
| **browser-tester** | Browser automation and testing with 3 specialized agents (operator, researcher, visual documenter) using agent-browser CLI | [amplifier-bundle-browser-tester](https://github.com/microsoft/amplifier-bundle-browser-tester) |
| **computer-use** | Computer Use bundle for the Amplifier project | [amplifier-bundle-computer-use](https://github.com/microsoft/amplifier-bundle-computer-use) |
| **containers** | Container-based execution environments | [amplifier-bundle-containers](https://github.com/microsoft/amplifier-bundle-containers) |
| **converge** | Vision-first, contract-driven development — direction lands in ratified contracts first, work is derived from the contract-vs-reality gap: reconciliation ledger, candidate-guard hook, owner-gated wave recipes | [amplifier-bundle-converge](https://github.com/microsoft/amplifier-bundle-converge) |
| **context-intelligence** | Context Intelligence bundle for the Amplifier project | [amplifier-bundle-context-intelligence](https://github.com/microsoft/amplifier-bundle-context-intelligence) |
| **context-managed** | LLM-powered rolling context summarization with persistent transcript, budget-aware tracking, and on-demand history recovery via bundled read_transcript tool | [amplifier-bundle-context-managed](https://github.com/microsoft/amplifier-bundle-context-managed) |
| **design-intelligence** | Comprehensive design intelligence with 7 specialized agents, design philosophy framework, and knowledge base | [amplifier-bundle-design-intelligence](https://github.com/microsoft/amplifier-bundle-design-intelligence) |
| **digital-twin-universe** | On-demand isolated environments from declarative profiles — Incus containers with URL rewriting, PyPI overrides, and LLM API passthrough for evidence-based verification of deployed software | [amplifier-bundle-digital-twin-universe](https://github.com/microsoft/amplifier-bundle-digital-twin-universe) |
| **distro** | Managed bundle for Amplifier distro | [amplifier-bundle-distro](https://github.com/microsoft/amplifier-bundle-distro) |
| **dot-graph** | DOT/Graphviz infrastructure — knowledge, validation, rendering, and graph intelligence for the Amplifier ecosystem | [amplifier-bundle-dot-graph](https://github.com/microsoft/amplifier-bundle-dot-graph) |
| **dot-runner** | Experimental DOT pipeline execution engine, CLI, unified LLM client, coding-agent loop, and amplifier-agent adapter; embedded loop implementations are linked below | [amplifier-bundle-dot-runner](https://github.com/microsoft/amplifier-bundle-dot-runner) |
| **evaluation** | One-stop-shop for evaluating AI agents, bundles, and recipes across the Amplifier ecosystem — provides an `evaluation` mode for designing evaluations plus a Python harness for running pre-defined tasks against agents in a Digital Twin Universe | [amplifier-bundle-evaluation](https://github.com/microsoft/amplifier-bundle-evaluation) |
| **execution-environments** | Instance-based execution environments — create, target, and destroy local, Docker, and SSH environments on demand with 11 tools, composable wrappers, and NLSpec-aligned protocol | [amplifier-bundle-execution-environments](https://github.com/microsoft/amplifier-bundle-execution-environments) |
| **filesystem** | Filesystem tools (read, write, edit, glob, grep) | [amplifier-bundle-filesystem](https://github.com/microsoft/amplifier-bundle-filesystem) |
| **foreman** | Assistant pattern where the conversation assistant manages a fleet of other assistants, each with their own sessions, leveraging capabilities from amplifier-bundle-orchestration | [amplifier-bundle-foreman](https://github.com/payneio/amplifier-bundle-foreman) |
| **gitea** | On-demand ephemeral Gitea instances for isolated git workflows — mirror repos from GitHub, work freely, and promote results back when ready | [amplifier-bundle-gitea](https://github.com/microsoft/amplifier-bundle-gitea) |
| **issues** | Persistent issue tracking with dependency management, priority scheduling, and session linking for autonomous work | [amplifier-bundle-issues](https://github.com/microsoft/amplifier-bundle-issues) |
| **ios-tester** | iOS app testing on simulators and devices — 3 specialist agents (operator, visual-tester, debugger) driving apps via the accessibility tree with points/pixels-aware coordinates, plus simulator provisioning and host diagnostics | [amplifier-bundle-ios-tester](https://github.com/microsoft/amplifier-bundle-ios-tester) |
| **imagegen** | Composable image generation/editing tool and skill with receipts and optional provider routing; source candidate with draft contracts, not a release or delivery-acceptance claim | [amplifier-bundle-imagegen](https://github.com/microsoft/amplifier-bundle-imagegen) |
| **llm-wiki** | Karpathy LLM Wiki pattern as composable workflow modes — wiki-init, wiki-ingest, wiki-lint, wiki-publish, wiki-query; zero-cost-when-dormant via per-mode shared orientation | [amplifier-bundle-llm-wiki](https://github.com/microsoft/amplifier-bundle-llm-wiki) |
| **lsp** | Core Language Server Protocol support for code intelligence operations | [amplifier-bundle-lsp](https://github.com/microsoft/amplifier-bundle-lsp) |
| **lsp-python** | DEPRECATED — forwarding stub, use python-dev instead | [amplifier-bundle-lsp-python](https://github.com/microsoft/amplifier-bundle-lsp-python) |
| **lsp-rust** | DEPRECATED — forwarding stub, use rust-dev instead | [amplifier-bundle-lsp-rust](https://github.com/microsoft/amplifier-bundle-lsp-rust) |
| **lsp-typescript** | DEPRECATED — forwarding stub, use typescript-dev instead | [amplifier-bundle-lsp-typescript](https://github.com/microsoft/amplifier-bundle-lsp-typescript) |
| **modes** | Dynamic runtime behavior overlays (brainstorm, debug, plan, verify, finish) | [amplifier-bundle-modes](https://github.com/microsoft/amplifier-bundle-modes) |
| **memory** | Local, Git-backed standing preferences with session integration, explicit setup, and optional suggestion jobs; distinct from the community memory bundle | [amplifier-bundle-memory](https://github.com/microsoft/amplifier-bundle-memory) |
| **my-voice** | Personalized voice and communication style | [amplifier-bundle-my-voice](https://github.com/microsoft/amplifier-bundle-my-voice) |
| **notify** | Desktop and push notifications when assistant turns complete - works over SSH, supports ntfy.sh for mobile | [amplifier-bundle-notify](https://github.com/microsoft/amplifier-bundle-notify) |
| **observers** | Orchestration pattern where background observer sessions are configured and run in the background, in parallel to provide the main session with actionable observations | [amplifier-bundle-observers](https://github.com/microsoft/amplifier-bundle-observers) |
| **orchestration** | Adds event-driven orchestration primitives (bundle spawning, events, triggers) for multi-session coordination | [amplifier-bundle-orchestration](https://github.com/microsoft/amplifier-bundle-orchestration) |
| **python-dev** | Comprehensive Python development tools - code quality (ruff, pyright), LSP integration, and expert agent | [amplifier-bundle-python-dev](https://github.com/microsoft/amplifier-bundle-python-dev) |
| **reality-check** | Intent-driven verification of built software — derives acceptance tests from user conversations, deploys in a Digital Twin Universe environment, runs app specific validations, and produces gap analysis reports | [amplifier-bundle-reality-check](https://github.com/microsoft/amplifier-bundle-reality-check) |
| **recipes** | Multi-step AI agent orchestration with behavior overlays and standalone options | [amplifier-bundle-recipes](https://github.com/microsoft/amplifier-bundle-recipes) |
| **redaction** | Amplifier bundle with redaction library and redaction hook | [amplifier-bundle-redaction](https://github.com/microsoft/amplifier-bundle-redaction) |
| **routing-matrix** | Declarative model routing with 13 semantic roles, 7 curated matrices, and CLI tooling — agents declare what they do, matrices resolve them to the right model | [amplifier-bundle-routing-matrix](https://github.com/microsoft/amplifier-bundle-routing-matrix) |
| **rust-dev** | Comprehensive Rust development tools — code quality (cargo fmt, clippy, cargo check), LSP integration, and expert agent | [amplifier-bundle-rust-dev](https://github.com/microsoft/amplifier-bundle-rust-dev) |
| **shadow** | OS-level sandboxed environments for testing local Amplifier ecosystem changes safely | [amplifier-bundle-shadow](https://github.com/microsoft/amplifier-bundle-shadow) |
| **skills** | Skills tool and Microsoft-curated skills collection with two composable behaviors (full with curated skills, or tool-only) | [amplifier-bundle-skills](https://github.com/microsoft/amplifier-bundle-skills) |
| **stories** | Autonomous storytelling engine with 11 specialist agents, 4 output formats (HTML, Excel, Word, PDF), and automated recipes for case studies, release notes, and weekly digests | [amplifier-bundle-stories](https://github.com/microsoft/amplifier-bundle-stories) |
| **superpowers** | TDD-driven development workflows with brainstorm, plan, execute, verify, and finish modes — includes specialized agents and a full development cycle recipe | [amplifier-bundle-superpowers](https://github.com/microsoft/amplifier-bundle-superpowers) |
| **systems-design** | Systems-design capabilities for Amplifier sessions | [amplifier-bundle-systems-design](https://github.com/microsoft/amplifier-bundle-systems-design) |
| **team-pulse** | Read-only lens over your team's shared knowledge — members, projects, initiatives, tasks, and a mined document corpus — via the Team Pulse API, with a `/team-pulse` mode and expert agent | [amplifier-bundle-team-pulse](https://github.com/microsoft/amplifier-bundle-team-pulse) |
| **terminal-tester** | Terminal application testing and inspection with 3 specialist agents (operator, visual-tester, debugger) using dual-mode capture — screen-dump for Ratatui/crossterm, PTY/pyte for any terminal app | [amplifier-bundle-terminal-tester](https://github.com/microsoft/amplifier-bundle-terminal-tester) |
| **ts-dev** | Comprehensive TypeScript/JavaScript development tools - code quality, LSP, and expert agent | [amplifier-bundle-ts-dev](https://github.com/microsoft/amplifier-bundle-ts-dev) |
| **typescript-dev** | TypeScript development tools (linting, type checking, LSP) | [amplifier-bundle-typescript-dev](https://github.com/microsoft/amplifier-bundle-typescript-dev) |
| **ui-use** | Experimental bounded browser/computer controller and Amplifier adapter, with ordinary selection by default and explicitly selected optional decision backends | [amplifier-bundle-ui-use](https://github.com/microsoft/amplifier-bundle-ui-use) |
| **wayfinder** | Early-ring curated in-session guidance and capability offers using authored packets and a hook; proposes actions before running them | [amplifier-bundle-wayfinder](https://github.com/microsoft/amplifier-bundle-wayfinder) |
| **webllm** | WebLLM with WebGPU for running amplifier-core in browsers | [amplifier-bundle-webllm](https://github.com/microsoft/amplifier-bundle-webllm) |
| **webruntime** | Web runtime for browser-based Amplifier | [amplifier-bundle-webruntime](https://github.com/microsoft/amplifier-bundle-webruntime) |
| **windows-shell** | Native Windows shell support — the `pwsh` tool with pinned UTF-16LE payload encoding, a stdin-gated Win32 Job Object, and PowerShell-shaped safety profiles matching tool-bash's config surface | [amplifier-bundle-windows-shell](https://github.com/microsoft/amplifier-bundle-windows-shell) |
| **work** | Provider-neutral live-host working bundle combining delegation, compaction, transcript retrieval, filesystem/shell/search, and optional composed capabilities | [amplifier-bundle-work](https://github.com/microsoft/amplifier-bundle-work) |
| **work-tracker** | Multi-agent work coordination — atomic claiming so exactly one agent ever holds an item, PID-bound custody that survives long autonomous and long idle holds, feedback routed back to whoever reported it, and an executable contract suite that makes storage-layer churn fail loudly. Built on Beads. | [amplifier-work-tracker](https://github.com/microsoft/amplifier-work-tracker) |

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
| **loop-basic** | Non-streaming request/response loop with parallel tool batches and ordered result insertion | [amplifier-module-loop-basic](https://github.com/microsoft/amplifier-module-loop-basic) |
| **loop-streaming** | Streaming-oriented agent loop with parallel tool batches, ordered history updates, request budgeting, and optional cooperative suspension | [amplifier-module-loop-streaming](https://github.com/microsoft/amplifier-module-loop-streaming) |
| **loop-events** | Event-driven loop with sequential tool execution and optional scheduler veto or tool replacement | [amplifier-module-loop-events](https://github.com/microsoft/amplifier-module-loop-events) |
| **loop-live** | Experimental streaming-derived orchestrator for identified live inputs, request-boundary steering, and background jobs; persistence and native steering require host/provider capabilities | [amplifier-module-loop-live](https://github.com/microsoft/amplifier-module-loop-live) |

These are the four public standalone Microsoft `amplifier-module-loop-*` repositories at review time. A sequential model/tool cycle does not imply serial execution within a tool batch. Streaming, structured-content retention, native steering, and resumability differ by path and provider; no common media-reference or native-history compatibility is implied. See each owner's implementation and contracts before substituting engines.

#### Embedded orchestrators and execution boundaries

These implementations live inside owning repositories rather than standalone `amplifier-module-loop-*` repositories.

| Implementation | Description and boundary | Owning source |
|----------------|--------------------------|---------------|
| **loop-agent** | Dot Runner's coding-agent worker: typed turn history, provider calls, steering, and configurable parallel tool batches; seeded history is reconstructed, not arbitrary-metadata passthrough | [Dot Runner module](https://github.com/microsoft/amplifier-bundle-dot-runner/tree/main/modules/loop-agent) |
| **loop-pipeline** | DOT graph orchestrator with retries, explicit parallel branches, checkpoint/resume, and direct or spawned workers; graph state and node-exchange history are not a worker's complete tool/media transcript | [Dot Runner module](https://github.com/microsoft/amplifier-bundle-dot-runner/tree/main/modules/loop-pipeline) |
| **loop-amplifier-agent** | Pipeline-worker adapter creating a fresh ephemeral session through public amplifier-agent handles; seeded history accepts text roles, rejects semantic metadata/non-text content, and is not a lossless native-history import | [Dot Runner module](https://github.com/microsoft/amplifier-bundle-dot-runner/tree/main/modules/loop-amplifier-agent) |
| **unified LLM generation loop** | Inner provider/tool loop used by Dot Runner's direct worker; separate request/message models and parallel active-tool batches, not an additional Core orchestrator module | [Dot Runner client](https://github.com/microsoft/amplifier-bundle-dot-runner/tree/main/modules/unified-llm-client) |
| **pipeline manager loop** | Observe/evaluate/steer/wait supervisor over child graph execution, not another provider-calling agent loop | [Dot Runner handler](https://github.com/microsoft/amplifier-bundle-dot-runner/blob/main/modules/loop-pipeline/amplifier_module_loop_pipeline/handlers/manager_loop.py) |
| **BrowserOrchestrator (browser bundle)** | Embedded Pyodide/Core-facing, text-oriented WebGPU loop with manual serial tool calling; current source permits one tool execution per invocation, not generic structured-media passthrough | [Browser runtime source](https://github.com/microsoft/amplifier-bundle-browser/blob/main/src/amplifier_webruntime.py) |
| **BrowserOrchestrator (webruntime bundle)** | Related but separate browser-loop implementation, not a re-export of the browser bundle or standalone streaming loop; WebLLM itself supplies a provider bridge rather than another agent loop | [Webruntime source](https://github.com/microsoft/amplifier-bundle-webruntime/blob/main/src/amplifier_webruntime.py) |

Attractor's current bundles select Dot Runner's loops. Amplifier Agent assembles its own pinned streaming-loop dependency; its public binding records and durable history have their own contracts. Core dispatches to a mounted orchestrator rather than supplying another built-in agent loop. These distinctions matter when moving history or proposing media references: metadata containers alone do not establish end-to-end retention, provider-wire support, or cross-engine compatibility.

**Native history boundary:** Constellation Runtime has its own [Rust execution loop](https://github.com/microsoft/amplifier-constellation-runtime/blob/main/src/engine.rs), not a Core binding. Its [migration importer](https://github.com/microsoft/amplifier-constellation-runtime/blob/main/src/migrate.rs) accepts public user/assistant text only—not executable continuation, tool transcripts, permissions, or media. Its public history projection is not a lossless native-state export.

### Providers

Connect to AI model providers.

| Module | Description | Repository |
|--------|-------------|------------|
| **provider-anthropic** | Anthropic Claude integration (Sonnet 4.5, Opus, etc.) | [amplifier-module-provider-anthropic](https://github.com/microsoft/amplifier-module-provider-anthropic) |
| **provider-openai** | OpenAI GPT integration | [amplifier-module-provider-openai](https://github.com/microsoft/amplifier-module-provider-openai) |
| **provider-openai-chatgpt** | ChatGPT subscription backend (Plus/Pro/Team/Enterprise) via Codex CLI OAuth | [amplifier-module-provider-openai-chatgpt](https://github.com/microsoft/amplifier-module-provider-openai-chatgpt) |
| **provider-azure-openai** | Azure OpenAI with managed identity support | [amplifier-module-provider-azure-openai](https://github.com/microsoft/amplifier-module-provider-azure-openai) |
| **provider-chat-completions** | OpenAI Chat Completions wire-format integration (llama.cpp, vLLM, LM Studio, LocalAI, etc.) | [amplifier-module-provider-chat-completions](https://github.com/microsoft/amplifier-module-provider-chat-completions) |
| **provider-gemini** | Google Gemini integration with 1M context and thinking | [amplifier-module-provider-gemini](https://github.com/microsoft/amplifier-module-provider-gemini) |
| **provider-vllm** | vLLM server integration for self-hosted models | [amplifier-module-provider-vllm](https://github.com/microsoft/amplifier-module-provider-vllm) |
| **provider-ollama** | Local Ollama models for offline development | [amplifier-module-provider-ollama](https://github.com/microsoft/amplifier-module-provider-ollama) |
| **provider-github-copilot** | GitHub Copilot models via the Copilot SDK | [amplifier-module-provider-github-copilot](https://github.com/microsoft/amplifier-module-provider-github-copilot) |
| **provider-litellm** | LiteLLM integration for unified access to 100+ LLM providers | [amplifier-module-provider-litellm](https://github.com/microsoft/amplifier-module-provider-litellm) |
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
| **tool-exec** | Bounded JavaScript orchestration of already-mounted tools through the host's approved dispatch lease; requires host support, not a general shell or Node runtime | [amplifier-module-tool-exec](https://github.com/microsoft/amplifier-module-tool-exec) |

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
| **hooks-jev-decisions** | Experimental optional Jev decision backend, registered as a hook/capability rather than a chat provider; requires explicit consumer selection | [amplifier-module-provider-jev](https://github.com/microsoft/amplifier-module-provider-jev) |
| **hooks-local-decisions** | Experimental optional local decision-model backends exposed through a hook/capability; separate from ordinary chat models and fallback | [amplifier-module-provider-local-decisions](https://github.com/microsoft/amplifier-module-provider-local-decisions) |

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
| **app-tool-generator** | AI-powered tool generator for creating custom Amplifier tools; repository archived, retained for reference | [@samueljklee](https://github.com/samueljklee) | [amplifier-app-tool-generator](https://github.com/samueljklee/amplifier-app-tool-generator) |
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
| **memory** | Consolidated evidence/fact memory capability with a portable skill and optional retained Amplifier bundle integration; formerly linked as amplifier-bundle-memory | [@michaeljabbour](https://github.com/michaeljabbour) | [amplifier-capability-memory](https://github.com/michaeljabbour/amplifier-capability-memory) |
| **parallax-discovery** | Multi-agent deep investigation methodology. Dispatches independent agent teams from different angles (code-tracer, behavior-observer, integration-mapper) to build true understanding of complex systems through progressive waves: broad discovery → focused verification → execution-based adversarial testing → synthesis. Includes 5 agents, 4 modes, 2 recipes, and a progressive-reveal skill. | [@bkrabach](https://github.com/bkrabach) | [amplifier-bundle-parallax-discovery](https://github.com/bkrabach/amplifier-bundle-parallax-discovery) |
| **perplexity** | Deep web research capabilities using Perplexity's Agentic Research API with citations and cost-aware guidance | [@colombod](https://github.com/colombod) | [amplifier-bundle-perplexity](https://github.com/colombod/amplifier-bundle-perplexity) |
| **browser** | Browser automation for AI agents using agent-browser - JS rendering, auth flows, form filling, and web research | [@samueljklee](https://github.com/samueljklee) | [amplifier-bundle-browser](https://github.com/samueljklee/amplifier-bundle-browser) |
| **tui-tester** | AI-assisted testing for TUI applications - spawn, drive, and capture Textual/terminal apps with visual analysis | [@colombod](https://github.com/colombod) | [amplifier-bundle-tui-tester](https://github.com/colombod/amplifier-bundle-tui-tester) |
| **web-ux-dev** | Web UX development tools - visual regression testing, console debugging, and pre-commit verification (extends browser bundle) | [@colombod](https://github.com/colombod) | [amplifier-bundle-web-ux-dev](https://github.com/colombod/amplifier-bundle-web-ux-dev) |
| **frontdoor** | Authentication gateway and service dashboard for Tailscale-based hosts. Provides PAM-based SSO, Caddy forward_auth integration, and a service discovery dashboard. Includes skills for host infrastructure discovery and web app setup. | [@robotdad](https://github.com/robotdad) | [amplifier-bundle-frontdoor](https://github.com/robotdad/frontdoor) |
| **codebase-to-course** | Transform any codebase or GitHub URL into a self-contained interactive HTML course for non-technical learners — scroll-based navigation, animated visualizations, embedded quizzes, and code-with-plain-English side-by-side translations | [@johannao76](https://github.com/johannao76) | [amplifier-bundle-codebase-to-course](https://github.com/johannao76/amplifier-bundle-codebase-to-course) |
| **research** | Consolidated research capability and portable skill for evidence-linked decisions, experiments, and papers; formerly linked as amplifier-bundle-research | [@michaeljabbour](https://github.com/michaeljabbour) | [amplifier-capability-research](https://github.com/michaeljabbour/amplifier-capability-research) |
| **taste** | Anti-slop frontend design discipline with named hard-bans on LLM UI defaults (Inter font, purple-blue gradients, centered heroes, equal-card grids), 3 parametric dials (`DESIGN_VARIANCE` / `MOTION_INTENSITY` / `VISUAL_DENSITY`), 4 mutually-exclusive aesthetic archetypes, and always-on output discipline. Adapted from [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill). | [@michaeljabbour](https://github.com/michaeljabbour) | [amplifier-bundle-taste](https://github.com/michaeljabbour/amplifier-bundle-taste) |

Some community repositories now package portable skills/capabilities alongside retained bundle integrations. Follow their current installation guides rather than inferring the package type from a historical repository name.

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
| **youtube** | YouTube download, search, and account feed access — audio/video download, keyword and filtered search (YouTube Data API + yt-dlp fallback), watch history, subscriptions, liked videos, and more | [@robotdad](https://github.com/robotdad) | [amplifier-youtube](https://github.com/robotdad/amplifier-youtube) |
| **tool-whisper** | Speech-to-text transcription using OpenAI's Whisper API | [@robotdad](https://github.com/robotdad) | [amplifier-module-tool-whisper](https://github.com/robotdad/amplifier-module-tool-whisper) |
| **long-read (formerly tool-rlm)** | Consolidated long-document capability with a portable skill, bounded evidence retrieval, and an optional native recursive engine; formerly linked as amplifier-module-tool-rlm | [@michaeljabbour](https://github.com/michaeljabbour) | [amplifier-capability-long-read](https://github.com/michaeljabbour/amplifier-capability-long-read) |
| **module-image-generation** | Multi-provider AI image generation with DALL-E, Imagen, and GPT-Image-1 | [@robotdad](https://github.com/robotdad) | [amplifier-module-image-generation](https://github.com/robotdad/amplifier-module-image-generation) |
| **module-style-extraction** | Extract and apply writing style from text samples | [@robotdad](https://github.com/robotdad) | [amplifier-module-style-extraction](https://github.com/robotdad/amplifier-module-style-extraction) |
| **module-markdown-utils** | Markdown parsing, injection, and metadata extraction utilities | [@robotdad](https://github.com/robotdad) | [amplifier-module-markdown-utils](https://github.com/robotdad/amplifier-module-markdown-utils) |

### Hooks

| Module | Description | Author | Repository |
|--------|-------------|--------|------------|
| **hooks-concise-display** | Cleaner, more condensed terminal output for Amplifier sessions | [@obra](https://github.com/obra) | [amplifier-module-hooks-concise-display](https://github.com/obra/amplifier-module-hooks-concise-display) |
| **hooks-compact** | Compress verbose bash stdout via command-aware filters (git, pytest, cargo, npm, ruff, etc.) before it enters the LLM context | [@samueljklee](https://github.com/samueljklee) | [amplifier-module-hooks-compact](https://github.com/samueljklee/amplifier-module-hooks-compact) |

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

## Deprecated Components

These components are deprecated or superseded. Most are from earlier architecture iterations (collections, profiles, config); other migration bridges are identified separately. Listed here for historical reference and discoverability. Deprecation does not necessarily mean the GitHub repository is archived.

| Component | Description | Superseded By | Repository |
|-----------|-------------|---------------|------------|
| **amplifier-collections** | Collection library | Bundles | [amplifier-collections](https://github.com/microsoft/amplifier-collections) |
| **amplifier-collection-design-intelligence** | Design intelligence collection | amplifier-bundle-design-intelligence | [amplifier-collection-design-intelligence](https://github.com/microsoft/amplifier-collection-design-intelligence) |
| **amplifier-collection-issues** | Issue management collection | amplifier-bundle-issues | [amplifier-collection-issues](https://github.com/microsoft/amplifier-collection-issues) |
| **amplifier-collection-recipes** | Recipes collection | amplifier-bundle-recipes | [amplifier-collection-recipes](https://github.com/microsoft/amplifier-collection-recipes) |
| **amplifier-collection-toolkit** | Toolkit collection | Bundles | [amplifier-collection-toolkit](https://github.com/microsoft/amplifier-collection-toolkit) |
| **amplifier-config** | Config library | Bundle configuration | [amplifier-config](https://github.com/microsoft/amplifier-config) |
| **amplifier-profiles** | Profile library | Bundles | [amplifier-profiles](https://github.com/microsoft/amplifier-profiles) |
| **amplifier-bundle-amplifier-online** | Deprecated temporary Amplifier Online v1-to-v2 setup bridge | Owner-documented CLI and `amplifier-online-deploy` skill workflow | [amplifier-bundle-amplifier-online](https://github.com/microsoft/amplifier-bundle-amplifier-online) |

---

**Ready to build?** Check out [DEVELOPER.md](./DEVELOPER.md) to get started!
