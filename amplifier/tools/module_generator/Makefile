.PHONY: test check run
test:
	PYTHONPATH=../../.. uv run pytest -q tests
check:
	@echo "No local checks for this tool; use repo root 'make check'"
run:
	uv run python -m amplifier.tools.module_generator generate $(CONTRACT) $(SPEC) $(if $(NAME),--module-name $(NAME),) $(if $(PLAN_ONLY),--plan-only,) $(if $(FORCE),--force,) $(if $(YES),--yes,)
