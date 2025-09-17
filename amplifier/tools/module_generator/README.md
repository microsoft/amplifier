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
