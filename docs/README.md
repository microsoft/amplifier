---
last_updated: 2025-11-18
status: stable
audience: all
---

# Amplifier Core — Contracts & Mechanisms

- **Mechanism, not policy.** Kernel publishes small, stable interfaces: request envelope, streaming grammar, adapter protocol, identity model, and event taxonomy bridge. **Policies** (provider choice, logging detail, privacy redaction) live in edge modules. fileciteturn1file6
- **Text‑first, inspectable.** JSON schemas for everything. One canonical JSONL stream for observability. fileciteturn1file8
- **Studs & sockets.** Contracts remain stable so teams can regenerate bricks independently. fileciteturn1file2

## Documentation by Audience

### 🚀 New Users - Start Here

**Get up and running quickly:**

- [USER_ONBOARDING.md](./USER_ONBOARDING.md) — **Start here!** Complete getting started guide
- [BUNDLES_PROVIDERS_ROUTING_PROJECTS.md](./BUNDLES_PROVIDERS_ROUTING_PROJECTS.md) — Understand how session configuration and model selection fit together
- **[Bundle Guide](https://github.com/microsoft/amplifier-foundation/blob/main/docs/BUNDLE_GUIDE.md)** — Create and customize bundles
- **[Agent Authoring](https://github.com/microsoft/amplifier-foundation/blob/main/docs/AGENT_AUTHORING.md)** — Create specialized agents
- [SCENARIO_TOOLS_GUIDE.md](./SCENARIO_TOOLS_GUIDE.md) — Building sophisticated CLI tools

**When you need help:**

- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) — Common issues and solutions

### 👨‍💻 Module Developers

**Building and extending Amplifier:**

- [LOCAL_DEVELOPMENT.md](./LOCAL_DEVELOPMENT.md) — Set up development environment
- [MODULE_DEVELOPMENT.md](./MODULE_DEVELOPMENT.md) — Create and test modules
- **[Module Resolution](https://github.com/microsoft/amplifier-module-resolution)** — Module source resolution library
  - **[User Guide](https://github.com/microsoft/amplifier-module-resolution/blob/main/docs/USER_GUIDE.md)** — Customizing module sources
  - **[Technical Specification](https://github.com/microsoft/amplifier-module-resolution/blob/main/docs/SPECIFICATION.md)** — Resolution strategy and contracts
- [TESTING_GUIDE.md](./TESTING_GUIDE.md) — Testing your modules

**Advanced topics:**

- **[Agent Delegation](https://github.com/microsoft/amplifier-app-cli/blob/main/docs/AGENT_DELEGATION_IMPLEMENTATION.md)** — How amplifier-app-cli implements sub-session delegation
- **[Mount Plan Specification](https://github.com/microsoft/amplifier-core/blob/main/docs/specs/MOUNT_PLAN_SPECIFICATION.md)** — Kernel configuration contract
- `specs/provider/…` — Provider protocol and contracts
- `specs/events/…` — Event taxonomy

### 🏗️ Contributors & Architecture

**Understanding the system design:**

- [AMPLIFIER_AS_LINUX_KERNEL.md](./AMPLIFIER_AS_LINUX_KERNEL.md) — Core metaphor for decision-making
- [AMPLIFIER_CONTEXT_GUIDE.md](./AMPLIFIER_CONTEXT_GUIDE.md) — Essential context for contributors

**Philosophy & principles:**

- [context/KERNEL_PHILOSOPHY.md](./context/KERNEL_PHILOSOPHY.md) — Kernel design principles
- [context/IMPLEMENTATION_PHILOSOPHY.md](./context/IMPLEMENTATION_PHILOSOPHY.md) — Development philosophy
- [context/MODULAR_DESIGN_PHILOSOPHY.md](./context/MODULAR_DESIGN_PHILOSOPHY.md) — Modular architecture

**Decisions & specifications:**

- `decisions/…` — Architecture decision records (ADRs)
- `specs/…` — Technical specifications for all contracts
- `schemas/…` — JSON schemas for validation

> These docs are **contracts** that amplifier‑core code and all modules will honor. Build against them and it will "just work."

## Architecture Decision Records (ADR)

The ADR system supports long-lived, searchable, and citeable decisions with clear **context, rationale, alternatives, consequences, and status**. It complements your Kernel/Modular/Implementation philosophies by making **why** explicit and durable.

See the `decisions` directory for details on how to use this system.

### @Mention System

- [MENTION_PROCESSING.md](MENTION_PROCESSING.md) — General-purpose @mention guide
- [CONTEXT_LOADING.md](CONTEXT_LOADING.md) — Context loading with @mentions
- [REQUEST_ENVELOPE_MODELS.md](REQUEST_ENVELOPE_MODELS.md) — Message models guide
