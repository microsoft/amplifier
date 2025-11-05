# Claude Code settings

> Configure Claude Code with global and project-level settings, and environment variables.

Claude Code offers a variety of settings to configure its behavior to meet your needs. You can configure Claude Code by running the `/config` command when using the interactive REPL, which opens a tabbed Settings interface where you can view status information and modify configuration options.

## Settings files

The `settings.json` file is our official mechanism for configuring Claude
Code through hierarchical settings:

- **User settings** are defined in `~/.claude/settings.json` and apply to all
  projects.
- **Project settings** are saved in your project directory:
  - `.claude/settings.json` for settings that are checked into source control and shared with your team
  - `.claude/settings.local.json` for settings that are not checked in, useful for personal preferences and experimentation. Claude Code will configure git to ignore `.claude/settings.local.json` when it is created.
- For enterprise deployments of Claude Code, we also support **enterprise
  managed policy settings**. These take precedence over user and project
  settings. System administrators can deploy policies to:
  - macOS: `/Library/Application Support/ClaudeCode/managed-settings.json`
  - Linux and WSL: `/etc/claude-code/managed-settings.json`
  - Windows: `C:\ProgramData\ClaudeCode\managed-settings.json`
- Enterprise deployments can also configure **managed MCP servers** that override
  user-configured servers. See [Enterprise MCP configuration](/en/docs/claude-code/mcp#enterprise-mcp-configuration):
  - macOS: `/Library/Application Support/ClaudeCode/managed-mcp.json`
  - Linux and WSL: `/etc/claude-code/managed-mcp.json`
  - Windows: `C:\ProgramData\ClaudeCode\managed-mcp.json`

```JSON Example settings.json theme={null}
{
  "permissions": {
    "allow": [
      "Bash(npm run lint)",
      "Bash(npm run test:*)",
      "Read(~/.zshrc)"
    ],
    "deny": [
      "Bash(curl:*)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ]
  },
  "env": {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp"
  }
}
```

### Available settings

`settings.json` supports a number of options:

| Key                          | Description                                                                                                                                                                                   | Example                                                     |
| :--------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------- |
| `apiKeyHelper`               | Custom script, to be executed in `/bin/sh`, to generate an auth value. This value will be sent as `X-Api-Key` and `Authorization: Bearer` headers for model requests                          | `/bin/generate_temp_api_key.sh`                             |
| `cleanupPeriodDays`          | How long to locally retain chat transcripts based on last activity date (default: 30 days)                                                                                                    | `20`                                                        |
| `env`                        | Environment variables that will be applied to every session                                                                                                                                   | `{"FOO": "bar"}`                                            |
| `includeCoAuthoredBy`        | Whether to include the `co-authored-by Claude` byline in git commits and pull requests (default: `true`)                                                                                      | `false`                                                     |
| `permissions`                | See table below for structure of permissions.                                                                                                                                                 |                                                             |
| `hooks`                      | Configure custom commands to run before or after tool executions. See [hooks documentation](hooks)                                                                                            | `{"PreToolUse": {"Bash": "echo 'Running command...'"}}`     |
| `disableAllHooks`            | Disable all [hooks](hooks)                                                                                                                                                                    | `true`                                                      |
| `model`                      | Override the default model to use for Claude Code                                                                                                                                             | `"claude-sonnet-4-5-20250929"`                              |
| `statusLine`                 | Configure a custom status line to display context. See [statusLine documentation](statusline)                                                                                                 | `{"type": "command", "command": "~/.claude/statusline.sh"}` |
| `outputStyle`                | Configure an output style to adjust the system prompt. See [output styles documentation](output-styles)                                                                                       | `"Explanatory"`                                             |
| `forceLoginMethod`           | Use `claudeai` to restrict login to Claude.ai accounts, `console` to restrict login to Claude Console (API usage billing) accounts                                                            | `claudeai`                                                  |
| `forceLoginOrgUUID`          | Specify the UUID of an organization to automatically select it during login, bypassing the organization selection step. Requires `forceLoginMethod` to be set                                 | `"xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"`                    |
| `enableAllProjectMcpServers` | Automatically approve all MCP servers defined in project `.mcp.json` files                                                                                                                    | `true`                                                      |
| `enabledMcpjsonServers`      | List of specific MCP servers from `.mcp.json` files to approve                                                                                                                                | `["memory", "github"]`                                      |
| `disabledMcpjsonServers`     | List of specific MCP servers from `.mcp.json` files to reject                                                                                                                                 | `["filesystem"]`                                            |
| `useEnterpriseMcpConfigOnly` | When set in managed-settings.json, restricts MCP servers to only those defined in managed-mcp.json. See [Enterprise MCP configuration](/en/docs/claude-code/mcp#enterprise-mcp-configuration) | `true`                                                      |
| `awsAuthRefresh`             | Custom script that modifies the `.aws` directory (see [advanced credential configuration](/en/docs/claude-code/amazon-bedrock#advanced-credential-configuration))                             | `aws sso login --profile myprofile`                         |
| `awsCredentialExport`        | Custom script that outputs JSON with AWS credentials (see [advanced credential configuration](/en/docs/claude-code/amazon-bedrock#advanced-credential-configuration))                         | `/bin/generate_aws_grant.sh`                                |

### Permission settings

| Keys                           | Description                                                                                                                                                                                                                                                                                                                   | Example                                                                |
| :----------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------- |
| `allow`                        | Array of [permission rules](/en/docs/claude-code/iam#configuring-permissions) to allow tool use. **Note:** Bash rules use prefix matching, not regex                                                                                                                                                                          | `[ "Bash(git diff:*)" ]`                                               |
| `ask`                          | Array of [permission rules](/en/docs/claude-code/iam#configuring-permissions) to ask for confirmation upon tool use.                                                                                                                                                                                                          | `[ "Bash(git push:*)" ]`                                               |
| `deny`                         | Array of [permission rules](/en/docs/claude-code/iam#configuring-permissions) to deny tool use. Use this to also exclude sensitive files from Claude Code access. **Note:** Bash patterns are prefix matches and can be bypassed (see [Bash permission limitations](/en/docs/claude-code/iam#tool-specific-permission-rules)) | `[ "WebFetch", "Bash(curl:*)", "Read(./.env)", "Read(./secrets/**)" ]` |
| `additionalDirectories`        | Additional [working directories](iam#working-directories) that Claude has access to                                                                                                                                                                                                                                           | `[ "../docs/" ]`                                                       |
| `defaultMode`                  | Default [permission mode](iam#permission-modes) when opening Claude Code                                                                                                                                                                                                                                                      | `"acceptEdits"`                                                        |
| `disableBypassPermissionsMode` | Set to `"disable"` to prevent `bypassPermissions` mode from being activated. See [managed policy settings](iam#enterprise-managed-policy-settings)                                                                                                                                                                            | `"disable"`                                                            |

### Settings precedence

Settings are applied in order of precedence (highest to lowest):

1. **Enterprise managed policies** (`managed-settings.json`)

   - Deployed by IT/DevOps
   - Cannot be overridden

2. **Command line arguments**

   - Temporary overrides for a specific session

3. **Local project settings** (`.claude/settings.local.json`)

   - Personal project-specific settings

4. **Shared project settings** (`.claude/settings.json`)

   - Team-shared project settings in source control

5. **User settings** (`~/.claude/settings.json`)
   - Personal global settings

This hierarchy ensures that enterprise security policies are always enforced while still allowing teams and individuals to customize their experience.

### Key points about the configuration system

- **Memory files (CLAUDE.md)**: Contain instructions and context that Claude loads at startup
- **Settings files (JSON)**: Configure permissions, environment variables, and tool behavior
- **Slash commands**: Custom commands that can be invoked during a session with `/command-name`
- **MCP servers**: Extend Claude Code with additional tools and integrations
- **Precedence**: Higher-level configurations (Enterprise) override lower-level ones (User/Project)
- **Inheritance**: Settings are merged, with more specific settings adding to or overriding broader ones

### System prompt availability

<Note>
  Unlike for claude.ai, we do not publish Claude Code's internal system prompt on this website. Use CLAUDE.md files or `--append-system-prompt` to add custom instructions to Claude Code's behavior.
</Note>

### Excluding sensitive files

To prevent Claude Code from accessing files containing sensitive information (e.g., API keys, secrets, environment files), use the `permissions.deny` setting in your `.claude/settings.json` file:

```json theme={null}
{
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./config/credentials.json)",
      "Read(./build)"
    ]
  }
}
```

This replaces the deprecated `ignorePatterns` configuration. Files matching these patterns will be completely invisible to Claude Code, preventing any accidental exposure of sensitive data.

## Subagent configuration

Claude Code supports custom AI subagents that can be configured at both user and project levels. These subagents are stored as Markdown files with YAML frontmatter:

- **User subagents**: `~/.claude/agents/` - Available across all your projects
- **Project subagents**: `.claude/agents/` - Specific to your project and can be shared with your team

Subagent files define specialized AI assistants with custom prompts and tool permissions. Learn more about creating and using subagents in the [subagents documentation](/en/docs/claude-code/sub-agents).

## Environment variables

Claude Code supports the following environment variables to control its behavior:

<Note>
  All environment variables can also be configured in [`settings.json`](#available-settings). This is useful as a way to automatically set environment variables for each session, or to roll out a set of environment variables for your whole team or organization.
</Note>

| Variable                                   | Purpose                                                                                                                                                                                                                                                                                                                                        |
| :----------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ANTHROPIC_API_KEY`                        | API key sent as `X-Api-Key` header, typically for the Claude SDK (for interactive usage, run `/login`)                                                                                                                                                                                                                                         |
| `ANTHROPIC_AUTH_TOKEN`                     | Custom value for the `Authorization` header (the value you set here will be prefixed with `Bearer `)                                                                                                                                                                                                                                           |
| `ANTHROPIC_CUSTOM_HEADERS`                 | Custom headers you want to add to the request (in `Name: Value` format)                                                                                                                                                                                                                                                                        |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL`            | See [Model configuration](/en/docs/claude-code/model-config#environment-variables)                                                                                                                                                                                                                                                             |
| `ANTHROPIC_DEFAULT_OPUS_MODEL`             | See [Model configuration](/en/docs/claude-code/model-config#environment-variables)                                                                                                                                                                                                                                                             |
| `ANTHROPIC_DEFAULT_SONNET_MODEL`           | See [Model configuration](/en/docs/claude-code/model-config#environment-variables)                                                                                                                                                                                                                                                             |
| `ANTHROPIC_MODEL`                          | Name of the model setting to use (see [Model Configuration](/en/docs/claude-code/model-config#environment-variables))                                                                                                                                                                                                                          |
| `ANTHROPIC_SMALL_FAST_MODEL`               | \[DEPRECATED] Name of [Haiku-class model for background tasks](/en/docs/claude-code/costs)                                                                                                                                                                                                                                                     |
| `ANTHROPIC_SMALL_FAST_MODEL_AWS_REGION`    | Override AWS region for the Haiku-class model when using Bedrock                                                                                                                                                                                                                                                                               |
| `AWS_BEARER_TOKEN_BEDROCK`                 | Bedrock API key for authentication (see [Bedrock API keys](https://aws.amazon.com/blogs/machine-learning/accelerate-ai-development-with-amazon-bedrock-api-keys/))                                                                                                                                                                             |
| `BASH_DEFAULT_TIMEOUT_MS`                  | Default timeout for long-running bash commands                                                                                                                                                                                                                                                                                                 |
| `BASH_MAX_OUTPUT_LENGTH`                   | Maximum number of characters in bash outputs before they are middle-truncated                                                                                                                                                                                                                                                                  |
| `BASH_MAX_TIMEOUT_MS`                      | Maximum timeout the model can set for long-running bash commands                                                                                                                                                                                                                                                                               |
| `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR` | Return to the original working directory after each Bash command                                                                                                                                                                                                                                                                               |
| `CLAUDE_CODE_API_KEY_HELPER_TTL_MS`        | Interval in milliseconds at which credentials should be refreshed (when using `apiKeyHelper`)                                                                                                                                                                                                                                                  |
| `CLAUDE_CODE_CLIENT_CERT`                  | Path to client certificate file for mTLS authentication                                                                                                                                                                                                                                                                                        |
| `CLAUDE_CODE_CLIENT_KEY_PASSPHRASE`        | Passphrase for encrypted CLAUDE_CODE_CLIENT_KEY (optional)                                                                                                                                                                                                                                                                                     |
| `CLAUDE_CODE_CLIENT_KEY`                   | Path to client private key file for mTLS authentication                                                                                                                                                                                                                                                                                        |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | Equivalent of setting `DISABLE_AUTOUPDATER`, `DISABLE_BUG_COMMAND`, `DISABLE_ERROR_REPORTING`, and `DISABLE_TELEMETRY`                                                                                                                                                                                                                         |
| `CLAUDE_CODE_DISABLE_TERMINAL_TITLE`       | Set to `1` to disable automatic terminal title updates based on conversation context                                                                                                                                                                                                                                                           |
| `CLAUDE_CODE_IDE_SKIP_AUTO_INSTALL`        | Skip auto-installation of IDE extensions                                                                                                                                                                                                                                                                                                       |
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS`            | Set the maximum number of output tokens for most requests                                                                                                                                                                                                                                                                                      |
| `CLAUDE_CODE_SKIP_BEDROCK_AUTH`            | Skip AWS authentication for Bedrock (e.g. when using an LLM gateway)                                                                                                                                                                                                                                                                           |
| `CLAUDE_CODE_SKIP_VERTEX_AUTH`             | Skip Google authentication for Vertex (e.g. when using an LLM gateway)                                                                                                                                                                                                                                                                         |
| `CLAUDE_CODE_SUBAGENT_MODEL`               | See [Model configuration](/en/docs/claude-code/model-config)                                                                                                                                                                                                                                                                                   |
| `CLAUDE_CODE_USE_BEDROCK`                  | Use [Bedrock](/en/docs/claude-code/amazon-bedrock)                                                                                                                                                                                                                                                                                             |
| `CLAUDE_CODE_USE_VERTEX`                   | Use [Vertex](/en/docs/claude-code/google-vertex-ai)                                                                                                                                                                                                                                                                                            |
| `DISABLE_AUTOUPDATER`                      | Set to `1` to disable automatic updates. This takes precedence over the `autoUpdates` configuration setting.                                                                                                                                                                                                                                   |
| `DISABLE_BUG_COMMAND`                      | Set to `1` to disable the `/bug` command                                                                                                                                                                                                                                                                                                       |
| `DISABLE_COST_WARNINGS`                    | Set to `1` to disable cost warning messages                                                                                                                                                                                                                                                                                                    |
| `DISABLE_ERROR_REPORTING`                  | Set to `1` to opt out of Sentry error reporting                                                                                                                                                                                                                                                                                                |
| `DISABLE_NON_ESSENTIAL_MODEL_CALLS`        | Set to `1` to disable model calls for non-critical paths like flavor text                                                                                                                                                                                                                                                                      |
| `DISABLE_TELEMETRY`                        | Set to `1` to opt out of Statsig telemetry (note that Statsig events do not include user data like code, file paths, or bash commands)                                                                                                                                                                                                         |
| `HTTP_PROXY`                               | Specify HTTP proxy server for network connections                                                                                                                                                                                                                                                                                              |
| `HTTPS_PROXY`                              | Specify HTTPS proxy server for network connections                                                                                                                                                                                                                                                                                             |
| `MAX_MCP_OUTPUT_TOKENS`                    | Maximum number of tokens allowed in MCP tool responses. Claude Code displays a warning when output exceeds 10,000 tokens (default: 25000)                                                                                                                                                                                                      |
| `MAX_THINKING_TOKENS`                      | Enable [extended thinking](/en/docs/build-with-claude/extended-thinking) and set the token budget for the thinking process. Extended thinking improves performance on complex reasoning and coding tasks but impacts [prompt caching efficiency](/en/docs/build-with-claude/prompt-caching#caching-with-thinking-blocks). Disabled by default. |
| `MCP_TIMEOUT`                              | Timeout in milliseconds for MCP server startup                                                                                                                                                                                                                                                                                                 |
| `MCP_TOOL_TIMEOUT`                         | Timeout in milliseconds for MCP tool execution                                                                                                                                                                                                                                                                                                 |
| `NO_PROXY`                                 | List of domains and IPs to which requests will be directly issued, bypassing proxy                                                                                                                                                                                                                                                             |
| `SLASH_COMMAND_TOOL_CHAR_BUDGET`           | Maximum number of characters for slash command metadata shown to [SlashCommand tool](/en/docs/claude-code/slash-commands#slashcommand-tool) (default: 15000)                                                                                                                                                                                   |
| `USE_BUILTIN_RIPGREP`                      | Set to `0` to use system-installed `rg` intead of `rg` included with Claude Code                                                                                                                                                                                                                                                               |
| `VERTEX_REGION_CLAUDE_3_5_HAIKU`           | Override region for Claude 3.5 Haiku when using Vertex AI                                                                                                                                                                                                                                                                                      |
| `VERTEX_REGION_CLAUDE_3_5_SONNET`          | Override region for Claude Sonnet 3.5 when using Vertex AI                                                                                                                                                                                                                                                                                     |
| `VERTEX_REGION_CLAUDE_3_7_SONNET`          | Override region for Claude 3.7 Sonnet when using Vertex AI                                                                                                                                                                                                                                                                                     |
| `VERTEX_REGION_CLAUDE_4_0_OPUS`            | Override region for Claude 4.0 Opus when using Vertex AI                                                                                                                                                                                                                                                                                       |
| `VERTEX_REGION_CLAUDE_4_0_SONNET`          | Override region for Claude 4.0 Sonnet when using Vertex AI                                                                                                                                                                                                                                                                                     |
| `VERTEX_REGION_CLAUDE_4_1_OPUS`            | Override region for Claude 4.1 Opus when using Vertex AI                                                                                                                                                                                                                                                                                       |

## Tools available to Claude

Claude Code has access to a set of powerful tools that help it understand and modify your codebase:

| Tool             | Description                                                                          | Permission Required |
| :--------------- | :----------------------------------------------------------------------------------- | :------------------ |
| **Bash**         | Executes shell commands in your environment                                          | Yes                 |
| **Edit**         | Makes targeted edits to specific files                                               | Yes                 |
| **Glob**         | Finds files based on pattern matching                                                | No                  |
| **Grep**         | Searches for patterns in file contents                                               | No                  |
| **MultiEdit**    | Performs multiple edits on a single file atomically                                  | Yes                 |
| **NotebookEdit** | Modifies Jupyter notebook cells                                                      | Yes                 |
| **NotebookRead** | Reads and displays Jupyter notebook contents                                         | No                  |
| **Read**         | Reads the contents of files                                                          | No                  |
| **SlashCommand** | Runs a [custom slash command](/en/docs/claude-code/slash-commands#slashcommand-tool) | Yes                 |
| **Task**         | Runs a sub-agent to handle complex, multi-step tasks                                 | No                  |
| **TodoWrite**    | Creates and manages structured task lists                                            | No                  |
| **WebFetch**     | Fetches content from a specified URL                                                 | Yes                 |
| **WebSearch**    | Performs web searches with domain filtering                                          | Yes                 |
| **Write**        | Creates or overwrites files                                                          | Yes                 |

Permission rules can be configured using `/allowed-tools` or in [permission settings](/en/docs/claude-code/settings#available-settings). Also see [Tool-specific permission rules](/en/docs/claude-code/iam#tool-specific-permission-rules).

### Extending tools with hooks

You can run custom commands before or after any tool executes using
[Claude Code hooks](/en/docs/claude-code/hooks-guide).

For example, you could automatically run a Python formatter after Claude
modifies Python files, or prevent modifications to production configuration
files by blocking Write operations to certain paths.

## See also

- [Identity and Access Management](/en/docs/claude-code/iam#configuring-permissions) - Learn about Claude Code's permission system
- [IAM and access control](/en/docs/claude-code/iam#enterprise-managed-policy-settings) - Enterprise policy management
- [Troubleshooting](/en/docs/claude-code/troubleshooting#auto-updater-issues) - Solutions for common configuration issues
