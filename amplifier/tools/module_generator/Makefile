.PHONY: test check run
test:
	uv run pytest -q amplifier/tools/module_generator/tests
check:
	@echo "No local checks for this tool; use repo root 'make check'"
run:
	uv run python -m amplifier.tools.module_generator generate $(CONTRACT) $(SPEC) $(if $(NAME),--module-name $(NAME),) $(if $(PLAN_ONLY),--plan-only,) $(if $(FORCE),--force,) $(if $(YES),--yes,)
