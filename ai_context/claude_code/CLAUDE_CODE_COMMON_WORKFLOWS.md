# Common workflows

> Learn about common workflows with Claude Code.

Each task in this document includes clear instructions, example commands, and best practices to help you get the most from Claude Code.

## Understand new codebases

### Get a quick codebase overview

Suppose you've just joined a new project and need to understand its structure quickly.

<Steps>
  <Step title="Navigate to the project root directory">
    ```bash  theme={null}
    cd /path/to/project
    ```
  </Step>

  <Step title="Start Claude Code">
    ```bash  theme={null}
    claude
    ```
  </Step>

  <Step title="Ask for a high-level overview">
    ```
    > give me an overview of this codebase
    ```
  </Step>

  <Step title="Dive deeper into specific components">
    ```
    > explain the main architecture patterns used here
    ```

    ```
    > what are the key data models?
    ```

    ```
    > how is authentication handled?
    ```

  </Step>
</Steps>

<Tip>
  Tips:

- Start with broad questions, then narrow down to specific areas
- Ask about coding conventions and patterns used in the project
- Request a glossary of project-specific terms
  </Tip>

### Find relevant code

Suppose you need to locate code related to a specific feature or functionality.

<Steps>
  <Step title="Ask Claude to find relevant files">
    ```
    > find the files that handle user authentication
    ```
  </Step>

  <Step title="Get context on how components interact">
    ```
    > how do these authentication files work together?
    ```
  </Step>

  <Step title="Understand the execution flow">
    ```
    > trace the login process from front-end to database
    ```
  </Step>
</Steps>

<Tip>
  Tips:

- Be specific about what you're looking for
- Use domain language from the project
  </Tip>

---

## Fix bugs efficiently

Suppose you've encountered an error message and need to find and fix its source.

<Steps>
  <Step title="Share the error with Claude">
    ```
    > I'm seeing an error when I run npm test
    ```
  </Step>

  <Step title="Ask for fix recommendations">
    ```
    > suggest a few ways to fix the @ts-ignore in user.ts
    ```
  </Step>

  <Step title="Apply the fix">
    ```
    > update user.ts to add the null check you suggested
    ```
  </Step>
</Steps>

<Tip>
  Tips:

- Tell Claude the command to reproduce the issue and get a stack trace
- Mention any steps to reproduce the error
- Let Claude know if the error is intermittent or consistent
  </Tip>

---

## Refactor code

Suppose you need to update old code to use modern patterns and practices.

<Steps>
  <Step title="Identify legacy code for refactoring">
    ```
    > find deprecated API usage in our codebase
    ```
  </Step>

  <Step title="Get refactoring recommendations">
    ```
    > suggest how to refactor utils.js to use modern JavaScript features
    ```
  </Step>

  <Step title="Apply the changes safely">
    ```
    > refactor utils.js to use ES2024 features while maintaining the same behavior
    ```
  </Step>

  <Step title="Verify the refactoring">
    ```
    > run tests for the refactored code
    ```
  </Step>
</Steps>

<Tip>
  Tips:

- Ask Claude to explain the benefits of the modern approach
- Request that changes maintain backward compatibility when needed
- Do refactoring in small, testable increments
  </Tip>

---

## Use specialized subagents

Suppose you want to use specialized AI subagents to handle specific tasks more effectively.

<Steps>
  <Step title="View available subagents">
    ```
    > /agents
    ```

    This shows all available subagents and lets you create new ones.

  </Step>

  <Step title="Use subagents automatically">
    Claude Code will automatically delegate appropriate tasks to specialized subagents:

    ```
    > review my recent code changes for security issues
    ```

    ```
    > run all tests and fix any failures
    ```

  </Step>

  <Step title="Explicitly request specific subagents">
    ```
    > use the code-reviewer subagent to check the auth module
    ```

    ```
    > have the debugger subagent investigate why users can't log in
    ```

  </Step>

  <Step title="Create custom subagents for your workflow">
    ```
    > /agents
    ```

    Then select "Create New subagent" and follow the prompts to define:

    * Subagent type (e.g., `api-designer`, `performance-optimizer`)
    * When to use it
    * Which tools it can access
    * Its specialized system prompt

  </Step>
</Steps>

<Tip>
  Tips:

- Create project-specific subagents in `.claude/agents/` for team sharing
- Use descriptive `description` fields to enable automatic delegation
- Limit tool access to what each subagent actually needs
- Check the [subagents documentation](/en/docs/claude-code/sub-agents) for detailed examples
  </Tip>

---

## Use Plan Mode for safe code analysis

Plan Mode instructs Claude to create a plan by analyzing the codebase with read-only operations, perfect for exploring codebases, planning complex changes, or reviewing code safely.

### When to use Plan Mode

- **Multi-step implementation**: When your feature requires making edits to many files
- **Code exploration**: When you want to research the codebase thoroughly before changing anything
- **Interactive development**: When you want to iterate on the direction with Claude

### How to use Plan Mode

**Turn on Plan Mode during a session**

You can switch into Plan Mode during a session using **Shift+Tab** to cycle through permission modes.

If you are in Normal Mode, **Shift+Tab** will first switch into Auto-Accept Mode, indicated by `⏵⏵ accept edits on` at the bottom of the terminal. A subsequent **Shift+Tab** will switch into Plan Mode, indicated by `⏸ plan mode on`.

**Start a new session in Plan Mode**

To start a new session in Plan Mode, use the `--permission-mode plan` flag:

```bash theme={null}
claude --permission-mode plan
```

**Run "headless" queries in Plan Mode**

You can also run a query in Plan Mode directly with `-p` (i.e., in ["headless mode"](/en/docs/claude-code/sdk/sdk-headless)):

```bash theme={null}
claude --permission-mode plan -p "Analyze the authentication system and suggest improvements"
```

### Example: Planning a complex refactor

```bash theme={null}
claude --permission-mode plan
```

```
> I need to refactor our authentication system to use OAuth2. Create a detailed migration plan.
```

Claude will analyze the current implementation and create a comprehensive plan. Refine with follow-ups:

```
> What about backward compatibility?
> How should we handle database migration?
```

### Configure Plan Mode as default

```json theme={null}
// .claude/settings.json
{
  "permissions": {
    "defaultMode": "plan"
  }
}
```

See [settings documentation](/en/docs/claude-code/settings#available-settings) for more configuration options.

---

## Work with tests

Suppose you need to add tests for uncovered code.

<Steps>
  <Step title="Identify untested code">
    ```
    > find functions in NotificationsService.swift that are not covered by tests
    ```
  </Step>

  <Step title="Generate test scaffolding">
    ```
    > add tests for the notification service
    ```
  </Step>

  <Step title="Add meaningful test cases">
    ```
    > add test cases for edge conditions in the notification service
    ```
  </Step>

  <Step title="Run and verify tests">
    ```
    > run the new tests and fix any failures
    ```
  </Step>
</Steps>

<Tip>
  Tips:

- Ask for tests that cover edge cases and error conditions
- Request both unit and integration tests when appropriate
- Have Claude explain the testing strategy
  </Tip>

---

## Create pull requests

Suppose you need to create a well-documented pull request for your changes.

<Steps>
  <Step title="Summarize your changes">
    ```
    > summarize the changes I've made to the authentication module
    ```
  </Step>

  <Step title="Generate a PR with Claude">
    ```
    > create a pr
    ```
  </Step>

  <Step title="Review and refine">
    ```
    > enhance the PR description with more context about the security improvements
    ```
  </Step>

  <Step title="Add testing details">
    ```
    > add information about how these changes were tested
    ```
  </Step>
</Steps>

<Tip>
  Tips:

- Ask Claude directly to make a PR for you
- Review Claude's generated PR before submitting
- Ask Claude to highlight potential risks or considerations
  </Tip>

## Handle documentation

Suppose you need to add or update documentation for your code.

<Steps>
  <Step title="Identify undocumented code">
    ```
    > find functions without proper JSDoc comments in the auth module
    ```
  </Step>

  <Step title="Generate documentation">
    ```
    > add JSDoc comments to the undocumented functions in auth.js
    ```
  </Step>

  <Step title="Review and enhance">
    ```
    > improve the generated documentation with more context and examples
    ```
  </Step>

  <Step title="Verify documentation">
    ```
    > check if the documentation follows our project standards
    ```
  </Step>
</Steps>

<Tip>
  Tips:

- Specify the documentation style you want (JSDoc, docstrings, etc.)
- Ask for examples in the documentation
- Request documentation for public APIs, interfaces, and complex logic
  </Tip>

---

## Work with images

Suppose you need to work with images in your codebase, and you want Claude's help analyzing image content.

<Steps>
  <Step title="Add an image to the conversation">
    You can use any of these methods:

    1. Drag and drop an image into the Claude Code window
    2. Copy an image and paste it into the CLI with ctrl+v (Do not use cmd+v)
    3. Provide an image path to Claude. E.g., "Analyze this image: /path/to/your/image.png"

  </Step>

  <Step title="Ask Claude to analyze the image">
    ```
    > What does this image show?
    ```

    ```
    > Describe the UI elements in this screenshot
    ```

    ```
    > Are there any problematic elements in this diagram?
    ```

  </Step>

  <Step title="Use images for context">
    ```
    > Here's a screenshot of the error. What's causing it?
    ```

    ```
    > This is our current database schema. How should we modify it for the new feature?
    ```

  </Step>

  <Step title="Get code suggestions from visual content">
    ```
    > Generate CSS to match this design mockup
    ```

    ```
    > What HTML structure would recreate this component?
    ```

  </Step>
</Steps>

<Tip>
  Tips:

- Use images when text descriptions would be unclear or cumbersome
- Include screenshots of errors, UI designs, or diagrams for better context
- You can work with multiple images in a conversation
- Image analysis works with diagrams, screenshots, mockups, and more
  </Tip>

---

## Reference files and directories

Use @ to quickly include files or directories without waiting for Claude to read them.

<Steps>
  <Step title="Reference a single file">
    ```
    > Explain the logic in @src/utils/auth.js
    ```

    This includes the full content of the file in the conversation.

  </Step>

  <Step title="Reference a directory">
    ```
    > What's the structure of @src/components?
    ```

    This provides a directory listing with file information.

  </Step>

  <Step title="Reference MCP resources">
    ```
    > Show me the data from @github:repos/owner/repo/issues
    ```

    This fetches data from connected MCP servers using the format @server:resource. See [MCP resources](/en/docs/claude-code/mcp#use-mcp-resources) for details.

  </Step>
</Steps>

<Tip>
  Tips:

- File paths can be relative or absolute
- @ file references add CLAUDE.md in the file's directory and parent directories to context
- Directory references show file listings, not contents
- You can reference multiple files in a single message (e.g., "@file1.js and @file2.js")
  </Tip>

---

## Use extended thinking

Suppose you're working on complex architectural decisions, challenging bugs, or planning multi-step implementations that require deep reasoning.

<Note>
  [Extended thinking](/en/docs/build-with-claude/extended-thinking) is disabled by default in Claude Code. You can enable it on-demand by using `Tab` to toggle Thinking on, or by using prompts like "think" or "think hard". You can also enable it permanently by setting the [`MAX_THINKING_TOKENS` environment variable](/en/docs/claude-code/settings#environment-variables) in your settings.
</Note>

<Steps>
  <Step title="Provide context and ask Claude to think">
    ```
    > I need to implement a new authentication system using OAuth2 for our API. Think deeply about the best approach for implementing this in our codebase.
    ```

    Claude will gather relevant information from your codebase and
    use extended thinking, which will be visible in the interface.

  </Step>

  <Step title="Refine the thinking with follow-up prompts">
    ```
    > think about potential security vulnerabilities in this approach
    ```

    ```
    > think hard about edge cases we should handle
    ```

  </Step>
</Steps>

<Tip>
  Tips to get the most value out of extended thinking:

[Extended thinking](/en/docs/build-with-claude/extended-thinking) is most valuable for complex tasks such as:

- Planning complex architectural changes
- Debugging intricate issues
- Creating implementation plans for new features
- Understanding complex codebases
- Evaluating tradeoffs between different approaches

Use `Tab` to toggle Thinking on and off during a session.

The way you prompt for thinking results in varying levels of thinking depth:

- "think" triggers basic extended thinking
- intensifying phrases such as "keep hard", "think more", "think a lot", or "think longer" triggers deeper thinking

For more extended thinking prompting tips, see [Extended thinking tips](/en/docs/build-with-claude/prompt-engineering/extended-thinking-tips).
</Tip>

<Note>
  Claude will display its thinking process as italic gray text above the
  response.
</Note>

---

## Resume previous conversations

Suppose you've been working on a task with Claude Code and need to continue where you left off in a later session.

Claude Code provides two options for resuming previous conversations:

- `--continue` to automatically continue the most recent conversation
- `--resume` to display a conversation picker

<Steps>
  <Step title="Continue the most recent conversation">
    ```bash  theme={null}
    claude --continue
    ```

    This immediately resumes your most recent conversation without any prompts.

  </Step>

  <Step title="Continue in non-interactive mode">
    ```bash  theme={null}
    claude --continue --print "Continue with my task"
    ```

    Use `--print` with `--continue` to resume the most recent conversation in non-interactive mode, perfect for scripts or automation.

  </Step>

  <Step title="Show conversation picker">
    ```bash  theme={null}
    claude --resume
    ```

    This displays an interactive conversation selector with a clean list view showing:

    * Session summary (or initial prompt)
    * Metadata: time elapsed, message count, and git branch

    Use arrow keys to navigate and press Enter to select a conversation. Press Esc to exit.

  </Step>
</Steps>

<Tip>
  Tips:

- Conversation history is stored locally on your machine
- Use `--continue` for quick access to your most recent conversation
- Use `--resume` when you need to select a specific past conversation
- When resuming, you'll see the entire conversation history before continuing
- The resumed conversation starts with the same model and configuration as the original

How it works:

1. **Conversation Storage**: All conversations are automatically saved locally with their full message history
2. **Message Deserialization**: When resuming, the entire message history is restored to maintain context
3. **Tool State**: Tool usage and results from the previous conversation are preserved
4. **Context Restoration**: The conversation resumes with all previous context intact

Examples:

```bash theme={null}
# Continue most recent conversation
claude --continue

# Continue most recent conversation with a specific prompt
claude --continue --print "Show me our progress"

# Show conversation picker
claude --resume

# Continue most recent conversation in non-interactive mode
claude --continue --print "Run the tests again"
```

</Tip>

---

## Run parallel Claude Code sessions with Git worktrees

Suppose you need to work on multiple tasks simultaneously with complete code isolation between Claude Code instances.

<Steps>
  <Step title="Understand Git worktrees">
    Git worktrees allow you to check out multiple branches from the same
    repository into separate directories. Each worktree has its own working
    directory with isolated files, while sharing the same Git history. Learn
    more in the [official Git worktree
    documentation](https://git-scm.com/docs/git-worktree).
  </Step>

  <Step title="Create a new worktree">
    ```bash  theme={null}
    # Create a new worktree with a new branch
    git worktree add ../project-feature-a -b feature-a

    # Or create a worktree with an existing branch
    git worktree add ../project-bugfix bugfix-123
    ```

    This creates a new directory with a separate working copy of your repository.

  </Step>

  <Step title="Run Claude Code in each worktree">
    ```bash  theme={null}
    # Navigate to your worktree
    cd ../project-feature-a

    # Run Claude Code in this isolated environment
    claude
    ```

  </Step>

  <Step title="Run Claude in another worktree">
    ```bash  theme={null}
    cd ../project-bugfix
    claude
    ```
  </Step>

  <Step title="Manage your worktrees">
    ```bash  theme={null}
    # List all worktrees
    git worktree list

    # Remove a worktree when done
    git worktree remove ../project-feature-a
    ```

  </Step>
</Steps>

<Tip>
  Tips:

- Each worktree has its own independent file state, making it perfect for parallel Claude Code sessions
- Changes made in one worktree won't affect others, preventing Claude instances from interfering with each other
- All worktrees share the same Git history and remote connections
- For long-running tasks, you can have Claude working in one worktree while you continue development in another
- Use descriptive directory names to easily identify which task each worktree is for
- Remember to initialize your development environment in each new worktree according to your project's setup. Depending on your stack, this might include:
  _ JavaScript projects: Running dependency installation (`npm install`, `yarn`)
  _ Python projects: Setting up virtual environments or installing with package managers \* Other languages: Following your project's standard setup process
  </Tip>

---

## Use Claude as a unix-style utility

### Add Claude to your verification process

Suppose you want to use Claude Code as a linter or code reviewer.

**Add Claude to your build script:**

```json theme={null}
// package.json
{
    ...
    "scripts": {
        ...
        "lint:claude": "claude -p 'you are a linter. please look at the changes vs. main and report any issues related to typos. report the filename and line number on one line, and a description of the issue on the second line. do not return any other text.'"
    }
}
```

<Tip>
  Tips:

- Use Claude for automated code review in your CI/CD pipeline
- Customize the prompt to check for specific issues relevant to your project
- Consider creating multiple scripts for different types of verification
  </Tip>

### Pipe in, pipe out

Suppose you want to pipe data into Claude, and get back data in a structured format.

**Pipe data through Claude:**

```bash theme={null}
cat build-error.txt | claude -p 'concisely explain the root cause of this build error' > output.txt
```

<Tip>
  Tips:

- Use pipes to integrate Claude into existing shell scripts
- Combine with other Unix tools for powerful workflows
- Consider using --output-format for structured output
  </Tip>

### Control output format

Suppose you need Claude's output in a specific format, especially when integrating Claude Code into scripts or other tools.

<Steps>
  <Step title="Use text format (default)">
    ```bash  theme={null}
    cat data.txt | claude -p 'summarize this data' --output-format text > summary.txt
    ```

    This outputs just Claude's plain text response (default behavior).

  </Step>

  <Step title="Use JSON format">
    ```bash  theme={null}
    cat code.py | claude -p 'analyze this code for bugs' --output-format json > analysis.json
    ```

    This outputs a JSON array of messages with metadata including cost and duration.

  </Step>

  <Step title="Use streaming JSON format">
    ```bash  theme={null}
    cat log.txt | claude -p 'parse this log file for errors' --output-format stream-json
    ```

    This outputs a series of JSON objects in real-time as Claude processes the request. Each message is a valid JSON object, but the entire output is not valid JSON if concatenated.

  </Step>
</Steps>

<Tip>
  Tips:

- Use `--output-format text` for simple integrations where you just need Claude's response
- Use `--output-format json` when you need the full conversation log
- Use `--output-format stream-json` for real-time output of each conversation turn
  </Tip>

---

## Create custom slash commands

Claude Code supports custom slash commands that you can create to quickly execute specific prompts or tasks.

For more details, see the [Slash commands](/en/docs/claude-code/slash-commands) reference page.

### Create project-specific commands

Suppose you want to create reusable slash commands for your project that all team members can use.

<Steps>
  <Step title="Create a commands directory in your project">
    ```bash  theme={null}
    mkdir -p .claude/commands
    ```
  </Step>

  <Step title="Create a Markdown file for each command">
    ```bash  theme={null}
    echo "Analyze the performance of this code and suggest three specific optimizations:" > .claude/commands/optimize.md
    ```
  </Step>

  <Step title="Use your custom command in Claude Code">
    ```
    > /optimize
    ```
  </Step>
</Steps>

<Tip>
  Tips:

- Command names are derived from the filename (e.g., `optimize.md` becomes `/optimize`)
- You can organize commands in subdirectories (e.g., `.claude/commands/frontend/component.md` creates `/component` with "(project:frontend)" shown in the description)
- Project commands are available to everyone who clones the repository
- The Markdown file content becomes the prompt sent to Claude when the command is invoked
  </Tip>

### Add command arguments with \$ARGUMENTS

Suppose you want to create flexible slash commands that can accept additional input from users.

<Steps>
  <Step title="Create a command file with the $ARGUMENTS placeholder">
    ```bash  theme={null}
    echo 'Find and fix issue #$ARGUMENTS. Follow these steps: 1.
    Understand the issue described in the ticket 2. Locate the relevant code in
    our codebase 3. Implement a solution that addresses the root cause 4. Add
    appropriate tests 5. Prepare a concise PR description' >
    .claude/commands/fix-issue.md
    ```
  </Step>

  <Step title="Use the command with an issue number">
    In your Claude session, use the command with arguments.

    ```
    > /fix-issue 123
    ```

    This will replace \$ARGUMENTS with "123" in the prompt.

  </Step>
</Steps>

<Tip>
  Tips:

- The \$ARGUMENTS placeholder is replaced with any text that follows the command
- You can position \$ARGUMENTS anywhere in your command template
- Other useful applications: generating test cases for specific functions, creating documentation for components, reviewing code in particular files, or translating content to specified languages
  </Tip>

### Create personal slash commands

Suppose you want to create personal slash commands that work across all your projects.

<Steps>
  <Step title="Create a commands directory in your home folder">
    ```bash  theme={null}
    mkdir -p ~/.claude/commands
    ```
  </Step>

  <Step title="Create a Markdown file for each command">
    ```bash  theme={null}
    echo "Review this code for security vulnerabilities, focusing on:" >
    ~/.claude/commands/security-review.md
    ```
  </Step>

  <Step title="Use your personal custom command">
    ```
    > /security-review
    ```
  </Step>
</Steps>

<Tip>
  Tips:

- Personal commands show "(user)" in their description when listed with `/help`
- Personal commands are only available to you and not shared with your team
- Personal commands work across all your projects
- You can use these for consistent workflows across different codebases
  </Tip>

---

## Ask Claude about its capabilities

Claude has built-in access to its documentation and can answer questions about its own features and limitations.

### Example questions

```
> can Claude Code create pull requests?
```

```
> how does Claude Code handle permissions?
```

```
> what slash commands are available?
```

```
> how do I use MCP with Claude Code?
```

```
> how do I configure Claude Code for Amazon Bedrock?
```

```
> what are the limitations of Claude Code?
```

<Note>
  Claude provides documentation-based answers to these questions. For executable examples and hands-on demonstrations, refer to the specific workflow sections above.
</Note>

<Tip>
  Tips:

- Claude always has access to the latest Claude Code documentation, regardless of the version you're using
- Ask specific questions to get detailed answers
- Claude can explain complex features like MCP integration, enterprise configurations, and advanced workflows
  </Tip>

---

## Next steps

<Card title="Claude Code reference implementation" icon="code" href="https://github.com/anthropics/claude-code/tree/main/.devcontainer">
  Clone our development container reference implementation.
</Card>
