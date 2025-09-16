# Amplifier Tool Builder

Generates new CLI tools using AI assistance with modular "bricks and studs" architecture.

## Usage

### Create a new tool

```bash
make tool-builder ARGS="create my-tool 'Tool description'"
```

### With automatic Makefile integration

```bash
make tool-builder ARGS="create my-tool 'Tool description' --auto-add-makefile"
```

Or set environment variable:
```bash
AUTO_ADD_TO_MAKEFILE=1 make tool-builder ARGS="create my-tool 'Tool description'"
```

## Makefile Integration

Generated tools include:

1. **Makefile.snippet** - Ready-to-use Makefile target in `~/.amplifier/generated_tools/{tool-name}/`
2. **Auto-add option** - Use `--auto-add-makefile` flag to automatically append to main Makefile
3. **Make command** - Run tools with `make {tool-name} ARGS='...'` after adding to Makefile

### Manual Integration

```bash
# Add generated target to Makefile
cat ~/.amplifier/generated_tools/my-tool/Makefile.snippet >> Makefile

# Test the tool
make my-tool ARGS='--help'
```

### Generated Makefile Target Format

```makefile
# Generated tool: my-tool
my-tool: ## Run the My Tool tool
	@cd ~/.amplifier/generated_tools/my-tool && python cli.py $(ARGS)
```

## Tool Locations

- **Generated tools**: `~/.amplifier/generated_tools/{tool-name}/`
- **Production tools**: `amplifier/tools/{tool-name}/` (after testing and approval)

## Moving to Production

After testing a generated tool:

```bash
cp -r ~/.amplifier/generated_tools/my-tool amplifier/tools/
```

Then update the Makefile target to use the production location.