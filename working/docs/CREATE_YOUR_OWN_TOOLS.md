# Creating Your Own Scenario Tools

Amplifier is designed so **you can create new AI-powered tools** just by describing how they should think. This guide will walk you through the process of turning an idea into a working **scenario** (a custom tool) using **metacognitive recipes** – structured thought processes that the AI will follow. You don't need to write code; you’ll describe the **problem**, outline the **approach**, and let Amplifier build the solution.

**Workflow Overview:**

1.  **Identify a Problem or Need** – Pick a task or workflow you want to automate or improve.
2.  **Outline a Metacognitive Recipe** – Describe the step-by-step thinking process an expert would use.
3.  **Use Amplifier to Build the Tool** – Launch the creation process with your description (via `/ultrathink-task`).
4.  **Refine and Integrate** – Test the generated scenario, give feedback, and iterate until it works well.
5.  **Leverage and Evolve** – Use your new tool, combine it with others for bigger tasks, and contribute improvements.

## 1. Identify a Problem or Need

Every great scenario begins with a **clear need**. Start by pinpointing a task that is repetitive, complex, or time-consuming – something you wish an AI assistant could handle reliably. This could be anything from _research synthesis_ (gathering and refining information on a topic) to _content generation_ (writing a blog post in your style with proper source citation). The key is that you can describe **what the goal is** and **what a successful outcome looks like**.

If you’re unsure what to build, try **brainstorming with Amplifier**. For example, you can ask Amplifier for ideas:

```
/ultrathink-task I'm new to "metacognitive recipes". What are some useful tools I could create with Amplifier that show how recipes can self-evaluate and improve via feedback loops? Just brainstorm ideas, don't build them yet.
```

This will prompt the AI to suggest possible tools. You might get inspired by suggestions like a _“Documentation Quality Amplifier”_ or a _“Self-Debugging Error Recovery”_ tool. Use your own experience and needs to choose an idea that would be genuinely useful to you. Remember, Amplifier works best when the problem is something **concrete** that you can break down into parts.

## 2. Formulate a Metacognitive Recipe

Once you have a problem in mind, **outline the approach** an expert (or you, on your best day) would take to solve it. This outline is your **metacognitive recipe** – essentially the game plan for the tool. Focus on **how the AI should think**, not just what it should do. Think in terms of stages, decision points, and loops:

- **Break the task into steps:** Divide the problem into logical phases or sub-tasks. Each step should be something the AI can tackle in a single go. For example, a blog-writing tool might have steps for _extracting your writing style_, _drafting content_, _checking sources_, _reviewing style_, and _incorporating feedback_. If a task feels too big or complex, it's a sign to decompose it into smaller steps or tools (Amplifier excels at this incremental approach). As a rule of thumb, **avoid making one scenario handle “everything at once”** – smaller focused steps improve reliability. (_For more strategies on breaking down problems, see **THIS_IS_THE_WAY.md** in the docs, which covers best practices like task decomposition._)
- **Provide context and checkpoints:** Consider what information each step needs and when to pause for review. For instance, should the AI summarize its findings before moving on? Should it ask the user to confirm something if ambiguity arises? By building in checkpoints or reviews (even if just self-reviews), you make the process more robust. A scenario recipe might include a loop where the AI evaluates its own output or seeks user feedback before proceeding to the next stage.
- **Plan for errors or ambiguity:** Metacognitive recipes often include fallback plans. Think about what the AI should do if a step produces incomplete or low-quality results. For example, “If the draft content is weak, have the AI refine it again,” or “If no sources are found, the tool should explain the issue rather than proceeding blindly.” Designing these recovery or iteration steps helps the tool adapt when things don’t go perfectly on the first try.

Write down your recipe in plain language. It can be a numbered list of steps or a few short paragraphs describing the flow. The goal is to **describe the thinking process** clearly enough that Amplifier (and you) understand the intended logic. You’re essentially programming the AI with instructions, except you’re doing it in natural language. Don’t worry about syntax – **clarity and structure** are what count.

> **Tip:** Aim for the level of detail you’d give if delegating the task to a smart colleague. Include important details (criteria for decisions, what outputs to generate, etc.), but don’t micromanage every tiny action. Amplifier’s AI will fill in routine parts – you just define the high-level game plan.

## 3. Use Amplifier to Build the Tool

With your idea and recipe in hand, it’s time to **turn it into a scenario**. In the Amplifier environment (e.g. a Claude chat session connected to your Amplifier setup), you’ll use a special command to kick off the tool generation. The typical command is:

```
/ultrathink-task <Your tool description and recipe>
```

This tells Amplifier to engage its tool-creation workflow (sometimes called the “ultra-think” mode). In practice, you would type something like:

```
/ultrathink-task I want to create a tool called "Research Synthesizer". Goal: help me research a topic by finding sources, extracting key themes, then asking me to choose which themes to explore in depth, and finally producing a summarized report.

Steps:
1. Do a preliminary web research on the topic and collect notes.
2. Extract the broad themes from the notes.
3. Present me the list of themes and highlight the top 2-3 you recommend focusing on (with reasons).
4. Allow me to refine or add to that theme list.
5. Do in-depth research on the refined list of themes.
6. Draft a report based on the deep research, ensuring the report stays within my requested length and style.
7. Offer the draft for my review and incorporate any feedback.
```

You can adjust the formatting – the key is that you are giving Amplifier a **name for the tool, a clear goal, and the step-by-step thinking approach**. When you submit this prompt, Amplifier will spring into action:

- **Planning and generation:** Amplifier’s AI will interpret your description and begin creating the scenario. It will generate the necessary code modules (in the [/scenarios](../scenarios/) directory) that implement your described workflow. You might see the AI outline the plan first, then write code for each step (this all happens behind the scenes or in the Claude interface output). Remember, _you_ are not writing the code – Amplifier is, based on your instructions.
- **Interactive clarification:** Depending on the complexity and the AI’s confidence, it may ask you a few clarifying questions (particularly if it’s running in an “assist” mode). For example, it might ask, “Do you want the report in Markdown or plain text?” or “Should the tool prioritize newer sources over older ones?” Answer these questions to guide the build. This is Amplifier making sure it correctly understands your intent before finalizing the tool.
- **Automatic documentation:** Amplifier automatically creates a usage guide for your new tool as part of the scenario. For example, when the blog writer scenario was built, Amplifier produced a file [HOW_TO_CREATE_YOUR_OWN.md](../scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md) in the [/scenarios/blog_writer](../scenarios/blog_writer) folder, explaining how that tool was created. Similarly, your scenario will include a markdown file documenting the process. This is useful for you and others to later review _how_ the tool works or even improve it. It’s essentially capturing the conversation and design rationale you provided.

When Amplifier finishes running `/ultrathink-task`, you’ll have a new scenario ready to go. Check your repository’s [/scenarios](../scenarios/) directory – there should be a new folder named after your tool (e.g. `/scenarios/research_synthesizer`). Inside, you’ll find the generated code (likely an orchestrator script and maybe supporting modules) and the documentation file. At this point, **the tool is now part of Amplifier’s toolkit**.

## 4. Refine the Scenario (Iterate and Improve)

Newly generated scenario tools might work on the first try, but often you’ll need a round of tweaking to get them just right. Treat this as an iterative **conversation with the AI**:

- **Test the tool:** Run your scenario on a sample task or input. In Amplifier’s chat, you can invoke it (typically by name or via a command – see the scenario’s documentation for how to trigger it). For example, if you created `research_synthesizer`, you might say: _“Use the Research Synthesizer to investigate topic XYZ.”_ The tool should execute its steps and produce an output (like a draft report, in this example).
- **Observe and note issues:** As it runs, watch for any steps that seem off. Does it skip a step? Is the output of a phase not what you expected? For instance, maybe it didn’t actually wait for your theme feedback in step 4, or the report draft is too long. These observations will guide your refinements.
- **Provide feedback in context:** You can improve the tool by continuing the chat with Amplifier. For example, if the draft was too long, you might say: _“The report was too lengthy. Please adjust the scenario so that the final report respects the length I initially requested.”_ Because Amplifier keeps track of the scenario it just built (and it generated the code from your conversation), it can modify the code or parameters accordingly. You might see it update the scenario’s code to enforce the length check. In essence, you’re debugging or tuning the tool through natural language.
- **Iterate until satisfied:** Repeat testing and providing adjustments. Amplifier will update the scenario’s code with each refinement step you discuss. Since Amplifier also captured the creation process in the scenario’s `HOW_TO_CREATE_YOUR_OWN.md` file (Example: [/scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md](../scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md)), your iterations might even be reflected or can be added there for documentation. Don’t hesitate to iterate; this is a normal part of crafting a reliable tool. Even complex multi-step scenarios can usually be perfected with a few rounds of feedback.

Throughout this refinement, keep the **metacognitive principles** in mind: if a particular step is failing, maybe it needs to be broken into two steps, or given more context. You can instruct Amplifier to make such changes. For example: _“Break the source review into a separate step before drafting, so it filters out bad sources first.”_ Amplifier will modify the workflow accordingly. The result is a better, more reliable tool.

## 5. Use Your Tool and Enrich Amplifier

Congratulations – you’ve built a new scenario! Now it’s time to put it to work and integrate it into your broader workflows:

- **Direct usage:** You can call your scenario tool whenever you need it. It behaves like a built-in capability of Amplifier now. For instance, once the _Research Synthesizer_ is ready, you can invoke it in any future Claude session connected to Amplifier to help with research tasks. Each scenario may have its own instructions on how to invoke it (some may introduce a new slash-command, others run based on context). Generally, speaking the tool’s name and goal should trigger it, as Amplifier’s orchestrator knows about the scenarios in the [/scenarios](../scenarios/) directory.
- **Combination and composition:** One of the most powerful aspects of Amplifier is that **tools can be combined**. Your new scenario can be used alongside others to handle bigger tasks. For example, you might first run a _web-to-markdown_ converter scenario on a set of URLs, then feed those results into your _research synthesizer_ scenario to analyze them. Or use a _blog writer_ scenario after the _research synthesizer_ to turn the research into a polished article. Over time, you’ll build up a suite of specialized tools, and you’ll find you can chain them together – the output of one becoming the input to another – to accomplish complex, higher-order workflows. This composability is by design: **small tools can work in concert to solve large problems**.
- **Reusable recipes:** The recipe you encoded in your scenario is now a part of Amplifier’s knowledge. In some cases, Amplifier’s knowledge base will index the patterns from your scenario’s transcripts and code. This means future tasks could potentially learn from what you’ve built. Even if you tackle a different project, you might reuse the same pattern. For example, the approach used in your research tool (e.g. _“extract themes → get user input → deep dive”_) could be repurposed in a totally different domain by spawning a new tool. In essence, each scenario is not just a one-off solution, but also a **recipe that can be referenced and remixed**.
- **Daily improvements:** The Amplifier system is evolving constantly. As you add scenarios, you’re extending the overall capability of the environment. Every tool you create and refine contributes to a richer ecosystem of AI assistants. Your tools might even surface insights for future development (for example, you might discover a better prompting technique or a useful chain-of-thought pattern, which can then inform other recipes or be added to Amplifier’s best practices). Amplifier is built to learn from usage – transcripts are saved and can be mined for improvements, and patterns of success get folded into the docs and examples. By building and using custom scenarios, you’re helping Amplifier get smarter and more useful for everyone, day by day.

## 6. Sharing and Next Steps

Part of Amplifier’s vision is to build a community-driven library of scenario tools. If your new tool is broadly useful, consider sharing it. At the moment (as of this writing), the project maintainers are **not yet accepting external contributions** directly into the repository (the system is still experimental and changing quickly), but this is likely to change. Keep an eye on the official guidelines – eventually you may be able to contribute your scenario to the [/scenarios](../scenarios/) collection for others to use. In the meantime, you can share the idea or even the recipe text with colleagues or friends running Amplifier.

To deepen your understanding and improve your recipe-writing skills, make sure to read the existing guides and scenario examples in the repo. Notable resources include:

- **The Amplifier Way – Effective Strategies** ([/docs/THIS_IS_THE_WAY.md](THIS_IS_THE_WAY.md)): A guide outlining the philosophy and tactics for AI-assisted development with Amplifier. It covers patterns like _decomposing tasks_, _“demo-driving”_ (iteratively proving out a concept), and _mining transcripts_ for continuous learning. These insights will help you craft better scenarios and troubleshoot when you hit challenges.
- **Existing Scenario Examples:** Browse the [/scenarios/README.md](../scenarios/README.md) for an overview of available tools. You can also read the individual scenario docs (for example, the blog writer’s creation notes in [/scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md](../scenarios/blog_writer/HOW_TO_CREATE_YOUR_OWN.md)) to see how others have framed their recipes. Each scenario’s documentation will show you the conversation and thought process that led to its creation – they’re gold mines for learning the conventions and possibilities.
- **Amplifier Vision and Roadmap:** For context on where this is all heading, check out [/AMPLIFIER_VISION.md](../AMPLIFIER_VISION.md) and [/ROADMAP.md](../ROADMAP.md) at the repository root. While not directly about creating scenarios, they illustrate the bigger picture – a future where creating and sharing AI workflows is effortless. It might spark ideas for new tools or improvements to existing ones.

By following this guide, you should be able to turn your own ideas into reliable, reusable Amplifier tools. **Find a need, describe the approach, and let the AI build it.** You’ll be expanding Amplifier’s capabilities with each scenario you create. Have fun experimenting, and happy building!
