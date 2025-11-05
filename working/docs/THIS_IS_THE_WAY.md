# The Amplifier Way: Effective Strategies for AI-Assisted Development

This guide distills hard-won insights for working effectively with Amplifier and Claude Code. These aren't theoretical best practices—they're battle-tested strategies that transform how you approach complex development challenges.

## Understanding Capability vs. Context

Amplifier isn't yet capable of doing all of the things we will eventually be able to do with it, but it's also not stuck in its current state. It is highly capable of helping improve itself for those who have the patience and willingness to help it learn.

### When Tasks Don't Complete: Two Root Causes

If you've made an ask of Amplifier that is too challenging for it to complete within a few requests, your requests likely have one or both of the following problems:

1. **Too challenging for current capabilities** - The task genuinely exceeds what Amplifier can reliably accomplish right now
2. **Not enough of the _right_ context** - Missing information that would enable completion

### The Context Solution Space is Bigger Than You Think

The "not enough context" problem has a _very_ big space. It could be that more context on the details of your ask are required, but it could _also_ mean that **metacognitive strategies** as part of its context can be provided to overcome the "too challenging for current capabilities" issue.

**Example:** If you ask Amplifier to go off and perform an action on a collection of a hundred files, it likely will only get partially through that on its own (though it's getting better, so maybe it can by now). **BUT** if you tell it to:

1. Write a tool that will read in the list of files
2. Create a file for tracking status
3. Have that tool iterate through each file
4. Perform whatever action you need (great place to have it also create a tool to do that processing)

Then you are likely to get 100% completion. Technically, this is "just" giving it the context it needs to drive this behavior. This is why I'd consider this a context solution (whereas the lack of tooling and pre-provided context hints about the use of the tooling and such, without user guidance, would be in the "too challenging for current capabilities" area).

## Decomposition: Breaking Down Big Swings

### Building Systems That Are Too Large

If you are trying to build a new system (maybe a "super planner" or tools for managing your social media presence, etc.) and that system doesn't end up achieving all you hope for, consider that maybe your system is trying to do too much in too large of a swing.

**Ask yourself:** What can you decompose and break apart into smaller, useful units?

**The Pattern:**

1. Have Amplifier help solve for and build tools for tackling those smaller units first
2. Then, go back to your larger scenario and ask it to create it again
3. This time provide the tools you had it create

This is a bit of a "cognitive offloading" that reduces the complexity (and token capacity and attention challenges) of trying to do it all in one larger "space".

**Bonus Value:** Those smaller tools usually also provide re-use value for other scenarios, etc. Contributed back or shared with others extend their value further.

### The Persistence Principle

**If something is too big to get it to do reliably, don't give up.**

Lean in, leverage the decomposition ideas above, and keep plowing forward. Amplifier is continuously improving and can help improve itself with patience and willingness to guide it through learning.

## Learning from Collaborative Problem-Solving

When you find yourself in a position where a task isn't completing as hoped, you can spend the following turns collaboratively / coaching it through to co-discover a solution (or you can just direct it) and that can work for sure.

**But also this:** You can use the transcript from this collaborative session to have it improve its future capabilities.

This transforms one-time debugging into permanent capability improvements.

## Transcript Tools: Capturing Your Work

### Building Readable Transcripts

You can run `./tools/claude_transcript_builder.py` in your project dir and it'll (by default) create a dir in `./output/<project-dir-name>/<session_id>` that has the original `session.jsonl` for the session.

**But the real gold** is it also creates (great for both human reading _and_ to feed to Amplifier/assistants for context/analysis/etc.):

- **`transcript.md`** - Reconstructed from across all of your session logs (building from a DAG that understands all the complexity of the CC logging, branching, sidechains, tools calls, etc.). This is the more human readable version that truncates all tool calls/results and sidechains to more easily read/consume the top level conversation.

- **`transcript_extended.md`** - Same as transcript.md except has the full tool calls/results and sidechain conversations (conversation between "Claude" and subagent, as invoked by TaskTool calls). Great for having the full, end-to-end with _all_ the sub-details.

- **`sidechains/` subdirectory** - Contains subdirs for _each_ subchain, and each of these have their own `transcript.md` which has the full details of that _subchain_, including full tool calls/results, etc.

You can run this command in the same dir you launch Claude Code from and it'll pull in all of the sessions you've _ever_ run in that dir (even non-Amplifier, all the way back to release of CC if you haven't cleared your ~/.claude logs).

### Other Options Available

Including one that will transform _all_ of your Claude Code sessions from _all_ of your dirs you ever ran Claude Code in, storing in `~/.claude/transcripts`:

```bash
./tools/claude_transcript_builder.py --help
```

Available options:

- `--project PROJECT` - Project name or directory (fuzzy match supported)
- `--list` - List all available projects and sessions
- `--session SESSION` - Session UUID or filename within project
- `--output OUTPUT` - Output directory for transcripts (default: ./output)
- `--include-system` - Include system messages in simple transcript
- `--debug` - Enable debug logging

**Examples:**

```bash
claude_transcript_builder.py                     # Process most recent session
claude_transcript_builder.py --list              # List all projects and sessions
claude_transcript_builder.py --project amplifier # Process most recent from project
claude_transcript_builder.py --session UUID      # Process specific session
claude_transcript_builder.py session.jsonl       # Process specific file
```

### Practical Use Cases for Transcripts

**1. Recovering Lost Conversations**

Load transcripts into a clean Amplifier session to continue work:

> /ultrathink-task Continuing from @output/transcripts/<path> ... <your new ask as if you were just taking your next turn>

This works really well for recovering a conversation that might have been lost to other methods, including those that were pre-Amplifier or done outside of Amplifier.

**2. Improving Amplifier's Capabilities**

Use transcripts to have Amplifier analyze and improve itself:

> /ultrathink-task Please analyze @output/transcripts/<path> and then identify where I had to provide you guidance on how to do something that it seems like a bit more metacognitive capability on your part could have allowed you to do without me. Then go read @ai_context/AMPLIFIER_CLAUDE_CODE_LEVERAGE.md and see if you can figure out what improvements could be made across your entire system to move this learning into your capabilities.

**This is _one of the ways_** that I have had it take something I helped solve during a session and turning it into something it can now do for me _and everyone else_ when I merged it in.

## Demo-Driven Development: Building Useful Examples

### The Evolving Demo Pattern

For my next demo, I think I'll demo the current public Amplifier by having it write a tool that takes all of my tips & tricks I've collected into an Obsidian collection and generates/updates docs in the repo in a format that is commit-worthy for a public repo. Then have the tool put into the "scenarios" dir as both another example and tool for others to do similar with (it'll just point to any input dir, doesn't matter if it was Obsidian or other method to drop files into it). **Win-win: good demo and useful tool.**

### Why Demos Need to Keep Evolving

Since the demos I do end up producing actually useful tools/examples with "how I created" as "how you can create" docs for each, they get merged in and then technically aren't great demos anymore because Amplifier now knows how to do that one.

**So my new pattern going forward:** Always come up with a new/useful tool and demo that.

Each demo will be framed as:

> "Let's improve Amplifier by building a useful tool that we want/need right now, but also so that it and everyone who uses it can _also_ get that value"

### The Self-Improving Cycle

When you demo by building actually useful tools:

1. **Immediate value** - You get a working tool that solves a real problem
2. **Documentation** - The tool serves as an example for others
3. **Knowledge growth** - Amplifier learns from the pattern
4. **Compound benefits** - Future users can build on your contribution

The demos become part of the system's knowledge, making Amplifier more capable for everyone.

## Key Takeaways

### Shift Your Mindset

- **Context over capability** - Most "limitations" are actually context gaps
- **Decomposition over monoliths** - Break big problems into tool-building steps
- **Learning over one-offs** - Turn collaborative debugging into permanent improvements
- **Tools over manual guidance** - Encode workflows in reusable tools

### Practical Strategies

1. **For batch operations** - Have Amplifier write a tool with status tracking and iteration
2. **For large systems** - Build smaller useful components first, then compose them
3. **When stuck** - Don't give up, provide metacognitive strategies as context
4. **After success** - Capture transcripts and use them to improve Amplifier's capabilities
5. **For demos** - Build genuinely useful tools that serve as examples

### The Amplifier Philosophy

Amplifier is highly capable of helping improve itself. Your patience and willingness to guide it through learning doesn't just solve your immediate problem—it makes the system better for everyone.

**Don't give up. Lean in. Keep plowing forward.**

The challenges you overcome today become capabilities Amplifier has tomorrow.
