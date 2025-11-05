# Amplifier Roadmap

> [!IMPORTANT] > **This roadmap is more _"guidelines"_ than commitments. This is subject to change based on new information, priorities, and the occasional perfect storm.**

## Amplifier Core workstream

Use Amplifier to improve and build Amplifier. This involves building the scaffolding and climbing the ladder of the metacognitive-recipes, progressively driving more and more of the buildout, vs specifically going and just building the one-off solutions. Shifting from current acceleration to more compounding progress. This is our critical path to Amplifier being able to take lists of our ideas and explore them unattended and engage human drivers for review, feedback and acceptance at higher levels of automation, capability, and success.

A helpful framing is to think of Amplifier like a Linux-kernel project: a small, protected core paired with a diverse and experimental userland. This resonates with a loose vision of an Amplifier Kernel providing interfaces for core features that may be central to all Amplifier experiences and usage, such as core capabilities, logging, audit/replay, storage, and memory rights. While the kernel analogy is useful, near-term work should remain focused on fast iteration, plumbing, and modularity rather than prematurely freezing a kernel-like design.

## Amplifier usage workstream

Leverage the value that emerges along the way by recognizing the value and use-cases that exist outside the Amplifier Core workstream objectives. Surface and evangelize these emergent uses, especially those that extend outside the code development space. It will also be part of this workstream to make the onboarding needed to access these capabilities more accessible to others, including improving for non-developers over time.

This workstream should also produce regular demos of emergent value and use-cases, content that provides visibility to where the project is at and going (automated, build the tools that generate this from the context we already provide the system, leverage our growing capabilities to do this only once – a demonstration in itself), and casting vision for how these could be adapted for use in other, adjacent scenarios.

The focus is on leveraging the emergent capabilities and discoveries over focusing on improvements that seek to provide desired capabilities that don’t yet exist or work as hoped – as in, a focus on improving support for developing non-Amplifier related codebases more generally is not in the scope of this (though emergent capabilities that do help in those scenarios are very much candidates for surfacing, demoing, sharing, making more accessible, etc.)

## Opportunities

For the above workstreams, here is a _partial_ list of some of the observed challenges and ways we’re thinking about pushing forward in the short term. All work is being treated as candidate to be thrown away and replaced within weeks by something better, more informed by learnings, and being rebuilt faster, more capable through the improvements in Amplifier itself. Prioritization is on moving and learning over extensive up-front analysis and planning for the longer term _at this point in time_. It’s the mode we’re currently in, to be periodically revisited and re-evaluated.

### Amplifier agentic loop

Today, Amplifier depends on Claude Code for an agentic loop. That enforces directory structures and hooks that complicate context and modularity our own plumbing to express our patterns, systems, etc. have to fit into. We are exploring what it would take to provide our own agentic loop that for increased flexibility. There are also unknowns to be discovered along this path.

### Multi-Amplifier and “modes”

Amplifier should allow multiple configurations tailored to specific tasks (e.g., creating Amplifier-powered user tools, self-improvement development, general software development, etc.). These “modes” could be declared through manifests that specify which sub-agents, commands, hooks, and philosophy documents to load, including external to the repo. Having a structured way to switch between modes and external sources makes it easier to share experimental tools, reduce conflicts, and quickly reconfigure the system for different kinds of work.

### Metacognitive recipes and non-developer use

Amplifier should evolve beyond being only a developer tool. As we continue to build support for metacognitive recipes - structured workflows described in natural language that are a mix of specific tasks and procedures but also higher-level philosophy, decision-making rationale, techniques for problem solving within the recipe’s domain, all that is supported by a code-first, but leveraging AI where appropriate in decomposed tasks - so that non-developers can leverage it effectively (e.g., transforming a raw idea dump into a blog post with reviewers and feedback and iteration loops, improving Amplifier’s develop-on-behalf-of-the-user skills with more of our learned debug and recovery techniques at its disposal). This emphasis on general, context-managed workflows also shapes kernel design.

### Standard artifacts and templates for collaboration

To encourage effective collaboration, Amplifier should adopt standardized templates for documentation, clear conventions for where context files and philosophy docs live, and definitions of acceptable sub-agents. Contributors should provide these artifacts so others can plug them into their own Amplifier instances. This is not limited to the items that drive the Amplifier system itself, but also those that we may selectively load and share as teams, workstreams, etc. – such as how we share, organize, and format content and context items for a team project, ideas or priority list, learnings that can be leveraged by human and/or fed to Amplifier.

### Leveraging sessions for learning and improvement

Amplifier should include a tool to parse session data, reconstruct conversation logs, and analyzing patterns. This should be done to unlock capabilities where users who share their usage data can enable others to query “how would <other user> approach <challenge>”. This would also allow Amplifier to learn from prior work and leverage the metacognitive recipe and tools patterns to improve its capabilities at that level vs documenting and hoping for compliance with a bunch of context notes. A prototype already exists for reconstructing transcripts and producing summaries to feed back into context and manually walking through the above ideas has proven successful.

### Context sharing

Team members should be able to share context without exposing private data publicly or merging into the public repository. Options include private Git repositories or shared OneDrive folders mounted as context for Amplifier. Whether Git or file shares are used, the key requirements are version history and ease of use. A mount-based approach is appealing for now because it treats everything as files and avoids custom API connectors, and allows for individual user-choice of any remote storage or synchronization platforms. Tools and guidance will be provided to make it simple for anyone to use the most recommended approaches.
