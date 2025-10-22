# Welcome to the project Codespace

The steps below will help you get started with the project.

## Post-Create Setup

When the dev container builds, a post-create script automatically runs to:
- ✅ Install the Claude CLI (`@anthropic-ai/claude-code`)
- ✅ Configure Git settings (auto-setup remote on push)

**Container Name**: The dev container is configured to always use the name `amplifier_devcontainer` in Docker Desktop (instead of random names like "sharp_galois").

### Verifying Installation

To verify everything installed correctly:

```bash
# Check Claude CLI is installed
claude --version

# View the post-create logs
cat /tmp/devcontainer-post-create.log
```

If the `claude` command is not found, the post-create script may have failed. Check the logs at `/tmp/devcontainer-post-create.log` for details, or manually run:

```bash
./.devcontainer/post-create.sh
```

## How to use

See the [README](../README.md) for more details on how to use the project.

### Connecting to the Codespace in the future

- Launch VS Code and open the command palette with the `F1` key or `Ctrl/Cmd+Shift+P`
- Type `Codespaces: Connect to Codespace...` and select it
- After the Codespace is ready, you will be prompted to open the workspace; click `Open Workspace`

### Optimizing your Codespaces experience

See [OPTIMIZING_FOR_CODESPACES.md](./OPTIMIZING_FOR_CODESPACES.md) for tips on optimizing your Codespaces experience.

## Deleting a Codespace

When you are done with a Codespace, you can delete it to free up resources.

- Visit the source repository on GitHub
- Click on the `Code` button and select the Codespaces tab
- Click on the `...` button next to the Codespace you want to delete
- Select `Delete`
