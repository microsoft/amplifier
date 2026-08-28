---
last_updated: 2026-08-27
status: stable
audience: user
---

# How Bundles, Provider Instances, Routing Matrices, and Project Folders Fit Together

**The provider answering the top-level conversation and the provider chosen for
a delegated agent are separate decisions.** A conversation can use one provider
instance while a child agent uses another.

This page is a map of those decisions. It intentionally leaves configuration
schemas, command references, and matrix catalogs to the components that own
them.

## Conceptual flow

```text
Exact current working directory
        |
        v
Global -> project -> local -> session settings
        |
        v
Selected bundle + its includes + optional app-level bundles
        |
        v
Prepared mount plan: providers, tools, agents, hooks, context
        |
        +----> top-level provider: explicit selection or priority default
        |
        +----> optional routing hook resolves agent model roles
                         |
                         v
                 child provider chosen at delegation time
```

The bundle determines the session's available shape. Settings specialize that
shape for a user, project, machine, or session. Provider selection and optional
routing then decide which mounted provider instance performs each piece of
work.

## Bundles define what is available

A bundle is composable configuration that produces a session mount plan. It can
contribute providers, tools, agents, hooks, instructions and context, and spawn
policy. A bundle can include other bundles, and the application can compose
additional app-level bundles onto it.

Foundation is not a mandatory first layer. A bundle may include Foundation,
include another bundle, or stand alone. What matters is the final composed
mount plan presented to the session.

Bundles usually describe portable capabilities; app settings supply
environment-specific choices such as credentials, model defaults, provider
priority, and project policy. This separation allows the same bundle to run in
different environments.

## Provider modules and provider instances are different

A **provider module** is an implementation of a vendor protocol, such as an
adapter for a model service. A **configured provider instance** is one mounted
use of that module with its own identity and configuration.

One module can therefore back several instances:

- one account with different default models;
- separate work and personal accounts;
- separate endpoints or deployments for the same provider type.

The configured `id` field distinguishes those entries. Multiple instances of
the same provider module need unique IDs. Instance configuration supplies the
account, model, priority, and other runtime details. The composed bundle and
effective app settings together produce the concrete instances a session can
select.

## The top-level conversation chooses from mounted instances

At startup, the root session receives the provider instances in its prepared
mount plan. An explicit provider choice for that session takes precedence when
one is supplied. Otherwise, the orchestrator selects the instance with the
lowest numerical priority and uses that instance's default model.

Some interactive orchestrators also support changing the provider pinned to the
current conversation at runtime. That pin is session-only. It does not rewrite
saved defaults and does not automatically pin delegated child sessions.

## Routing matrices are conditional delegation policy

A routing matrix maps a semantic **model role**—for example, a request for fast
work or deep reasoning—to an ordered set of provider/model candidates. This
lets an agent ask for the kind of model it needs without hard-coding one
provider.

Routing is not universal or automatic. It applies only when the composed bundle
mounts a routing strategy, such as the routing-matrix hook. With that strategy
mounted, its `session:start` handling can resolve each agent's `model_role`
against the provider instances that are actually available and write the
resulting provider preferences into the agent configuration.

Without a routing strategy, a `model_role` alone does not select a provider.
An agent's explicit `provider_preferences` can still provide a portable
fallback, and an agent with neither kind of preference inherits the parent
session's provider defaults.

## Delegated sessions use spawn-time precedence

For the reference CLI, a child session's provider choice follows this order,
from highest to lowest precedence:

1. `provider_preferences` passed by the caller for this delegation;
2. the agent overlay's `provider_preferences`, either declared by the agent or
   written from `model_role` by a mounted routing hook at `session:start`;
3. the parent session's mount-plan defaults: provider priority order and each
   instance's default model.

If delegation tooling accepts both an explicit provider preference and a model
role, the explicit provider preference wins. This is application policy, not a
kernel-wide contract; another Amplifier application may implement different
spawn policy.

This is why changing the top-level conversation's provider is not the same as
changing an agent's provider. The child runs through the spawn decision above.

## Project folders select configuration by exact CWD

The reference CLI merges settings from broadest to most specific:

| Scope | Location | Purpose |
|---|---|---|
| Global | `~/.amplifier/settings.yaml` | User defaults across projects |
| Project | `<CWD>/.amplifier/settings.yaml` | Team-shared project configuration |
| Local | `<CWD>/.amplifier/settings.local.yaml` | Machine-specific project overrides |
| Session | `~/.amplifier/projects/<project-slug>/sessions/<session-id>/settings.yaml` | Overrides for one session |

Later scopes override earlier scopes, so the effective order is **global →
project → local → session**.

`<CWD>` means the exact current working directory. The CLI does not walk upward
to find a parent project's `.amplifier/settings.yaml`. Starting Amplifier in a
repository root and starting it in a nested subdirectory can therefore select
different project/local settings.

These scopes can affect the active bundle, app-level bundles, configured
provider instances, routing configuration, module source overrides, and other
app policy. They do not turn settings into a bundle; settings specialize the
bundle composition selected for that session.

## Project configuration and session storage are separate

Project configuration lives under `<CWD>/.amplifier/` in the exact current
directory. It can be shared with the project or kept machine-local, depending
on the settings file.

Session data lives under
`~/.amplifier/projects/<project-slug>/sessions/<session-id>/`. The project slug
is derived from the exact CWD. Transcripts, events, metadata, and
session-specific settings are stored separately from the exact-CWD project
configuration.

The same CWD therefore drives two related but distinct choices:

1. which project and local configuration files are read; and
2. which project-scoped session-storage bucket is used.

## End-to-end example

Suppose Amplifier starts in `/work/catalog-api`:

1. Global settings provide two configured provider instances: `primary` and
   `fast`.
2. `/work/catalog-api/.amplifier/settings.yaml` selects a development bundle
   and a routing matrix. A local settings file adjusts provider priority for
   this machine.
3. The application composes the selected bundle and its includes. Because this
   composition includes routing, the prepared mount plan contains the routing
   hook as well as the providers, tools, and agents.
4. The top-level conversation uses an explicit provider selection if present;
   otherwise it uses the lowest-priority-number instance.
5. At `session:start`, the routing hook resolves an explorer agent's
   `model_role` and records `fast` as its preferred instance.
6. When the conversation delegates to that explorer without a per-call
   override, the agent preference wins at spawn time. A caller-supplied
   preference would win instead.
7. The root and child can consequently use different providers. Their session
   records are stored under the project slug derived from `/work/catalog-api`.

If the bundle in step 3 did not mount routing, step 5 would not occur. The agent
would use its explicit fallback preferences, if any, or the parent defaults.

## When each decision happens

| Time | Decision |
|---|---|
| Before session creation | Resolve exact-CWD settings, select and compose bundles, apply app settings, prepare modules, and produce the mount plan |
| At session start | Mount modules; if routing is present, resolve agent roles into provider preferences |
| During the top-level conversation | Use the explicit or priority-default provider; an orchestrator that supports runtime pinning may change it for this conversation |
| At each delegation | Apply the reference CLI's spawn precedence and create the child session with the selected provider/model |

## Authoritative references

- [Bundle Guide](https://github.com/microsoft/amplifier-foundation/blob/main/docs/BUNDLE_GUIDE.md)
  — bundle concepts, composition, and app-level injection
- [Mount Plan Specification](https://github.com/microsoft/amplifier-core/blob/main/docs/specs/MOUNT_PLAN_SPECIFICATION.md)
  — the kernel configuration contract
- [Provider Pinning](https://github.com/microsoft/amplifier-app-cli/blob/main/docs/PROVIDER_PINNING.md)
  — top-level interactive provider selection
- [Routing Matrix Bundle](https://github.com/microsoft/amplifier-bundle-routing-matrix)
  — matrix-strategy behavior and model-role resolution
- [Spawn-Time Precedence Policy](https://github.com/microsoft/amplifier-app-cli/blob/main/docs/SPAWN_PRECEDENCE.md)
  — the reference CLI's delegated-provider precedence
- [App settings implementation](https://github.com/microsoft/amplifier-app-cli/blob/main/amplifier_app_cli/lib/settings.py)
  — exact paths and scope merge order
- [Project-scoped session storage decision](https://github.com/microsoft/amplifier-app-cli/blob/main/docs/decisions/ADR-0001-project-scoped-self-contained-sessions.md)
  — CWD-derived project identity and session storage
- [Repository awareness rules](REPOSITORY_RULES.md)
  — which repository owns each level of documentation
