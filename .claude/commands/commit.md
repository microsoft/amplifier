---
description: Create well-formatted git commits with conventional commit messages
category: version-control-git
allowed-tools: Bash, Read, Glob
---

# Claude Command: Commit

This command helps you create well-formatted commits with conventional commit messages.

## Usage

To create a commit, just type:

```
/commit
```

Or with options:

```
/commit --no-verify
```

## What This Command Does

1. Unless specified with `--no-verify`, automatically runs pre-commit checks:
   - Detect package manager (npm, pnpm, yarn, bun) and run appropriate commands
   - Run lint/format checks if available
   - Run build verification if build script exists
   - Update documentation if generation script exists
2. Checks which files are staged with `git status`
3. If 0 files are staged, automatically adds all modified and new files with `git add`
4. Performs a `git diff` to understand what changes are being committed
5. Ensures there are is no sensitive data (like passwords, API keys, personal info, secrets, etc.) in the staged changes, if so, aborts the commit and informs the user
6. Analyzes the diff to determine if multiple distinct logical changes are present
7. If multiple distinct changes are detected, suggests breaking the commit into multiple smaller commits
8. For each commit (or the single commit if not split), creates a commit message using conventional commit format (ensuring there is no sensitive data within the message) and considering the available conversation history for additional context as appropriate, don't perform the commit yet, just generate the message and show it to the user for review
9. Presents the generated commit message(s) to the user for review and editing
10. Upon user confirmation, executes the `git commit` command with the finalized message(s)

## Best Practices for Commits

- **Verify before committing**: Ensure code is linted, builds correctly, and documentation is updated
  - IMPORTANT: If verification fails, DO NOT proceed with the commit and instead provide feedback on what needs to be fixed so that user can decide how to proceed
  - IMPORTANT: Do not actually fix issues yourself, just inform the user of what needs to be done and give them choice to do so or to proceed with commit anyway
- **Atomic commits**: Each commit should contain related changes that serve a single purpose
- **Split large changes**: If changes touch multiple concerns, split them into separate commits
- **Conventional commit format**: Use the format `<type>: <description>` where type is one of:
  - `feat`: A new feature
  - `fix`: A bug fix
  - `docs`: Documentation changes
  - `style`: Code style changes (formatting, etc)
  - `refactor`: Code changes that neither fix bugs nor add features
  - `perf`: Performance improvements
  - `test`: Adding or fixing tests
  - `chore`: Changes to the build process, tools, etc.
- **Present tense, imperative mood**: Write commit messages as commands (e.g., "add feature" not "added feature")
- **Leverage context**: Use conversation history to inform commit messages when relevant, especially where the content of the conversation could be useful for understanding the intent of the changes when reviewing the full commit history later, especially when reviewed by other AI tools that are attempting to understand the context behind the changes to understand rationale, decision making, intent, problem being solved, etc.
- **Concise first line**: Keep the first line under 72 characters

## Additional Guidance

$ARGUMENTS
