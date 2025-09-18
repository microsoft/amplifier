# Module Generator (Amplifier)

Generate a new Amplifier module from a **contract** and **implementation spec** using Claude Code SDK.

## Usage

```bash
# Plan only (no writes)
uv run python -m amplifier.tools.module_generator generate       ai_working/idea_synthesizer/IDEA_SYNTHESIZER.contract.md       ai_working/idea_synthesizer/IDEA_SYNTHESIZER.impl_spec.md       --plan-only

# Full generation (writes files under amplifier/<module_name>/)
uv run python -m amplifier.tools.module_generator generate       ai_working/idea_synthesizer/IDEA_SYNTHESIZER.contract.md       ai_working/idea_synthesizer/IDEA_SYNTHESIZER.impl_spec.md       --yes --force
```

- The generator auto-detects the repo **root** (by walking up to find `Makefile` or `.git`) and sets Claude Code's `cwd` there.
- Planning is done with **read-only tools** (`Read`, `Grep`). Generation uses **`acceptEdits`** with `Write`/`Edit`/`MultiEdit`/`Bash` enabled.

## Makefile integration

In the **repo root Makefile**, add a convenience target:

```makefile
.PHONY: module-generate
module-generate: ## Generate a module with CONTRACT=<file> SPEC=<file> [NAME=<name>] [FORCE=1] [YES=1]
	uv run python -m amplifier.tools.module_generator generate $(CONTRACT) $(SPEC) $(if $(NAME),--module-name $(NAME),) $(if $(FORCE),--force,) $(if $(YES),--yes,)
```

Then run:

```bash
make module-generate CONTRACT=ai_working/idea_synthesizer/IDEA_SYNTHESIZER.contract.md       SPEC=ai_working/idea_synthesizer/IDEA_SYNTHESIZER.impl_spec.md YES=1 FORCE=1
```

## Notes

- The SDK's `plan` permission mode is not currently supported; plan is enforced by restricting allowed tools to read-only.
- Ensure the `claude_code_sdk` Python package and the `claude` CLI are installed and the API key is configured.

## Pipeline Mode (NEW)

The module generator now supports a multi-stage pipeline with checkpoints for more reliable generation:

```bash
# Run with pipeline mode
uv run python -m amplifier.tools.module_generator generate \
    contract.md spec.md \
    --pipeline \
    --yes --force

# Resume from last checkpoint if interrupted
uv run python -m amplifier.tools.module_generator generate \
    contract.md spec.md \
    --pipeline --resume
```

### Pipeline Features

- **Multi-stage generation**: Requirements → Design → Implementation → Tests → Docs → Verification
- **Checkpoints**: Saves progress after each stage
- **Philosophy injection**: Ensures adherence to project principles at each stage
- **Drift detection**: Identifies and corrects deviations from requirements
- **Stage evaluation**: Validates quality at each checkpoint
- **Resume capability**: Continue from last successful stage after failures

### Options

- `--pipeline`: Enable multi-stage pipeline mode
- `--resume`: Resume from last checkpoint (requires --pipeline)
- `--enhanced`: Use enhanced contract parsing (legacy mode)
- `--plan-only`: Generate plan without writing files
- `--force`: Overwrite existing module directory
- `--yes/-y`: Skip confirmation prompts

## Requirements

1. **Python Package**: `uv add claude-code-sdk`
2. **Claude CLI**: `npm install -g @anthropic-ai/claude-code`
3. **API Key**: Configured in Claude Code environment

## Timeout Configuration

All Claude Code SDK operations use a 120-second timeout to ensure reliable generation even for complex modules.

