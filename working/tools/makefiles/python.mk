mkfile_dir = $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))
include $(mkfile_dir)/shell.mk

.DEFAULT_GOAL ?= install

ifdef UV_PROJECT_DIR
uv_project_args = --directory $(UV_PROJECT_DIR)
venv_dir = $(UV_PROJECT_DIR)/.venv
else
venv_dir = .venv
endif

UV_SYNC_INSTALL_ARGS ?= --all-extras --frozen
UV_RUN_ARGS ?= --all-extras --frozen

PYTEST_ARGS ?= --color=yes

## Rules

.PHONY: install
install:
	uv sync $(uv_project_args) $(UV_SYNC_INSTALL_ARGS)

.PHONY: lock-upgrade
lock-upgrade:
	uv lock --upgrade $(uv_project_args)

.PHONY: lock
lock:
	uv sync $(uv_project_args) $(UV_SYNC_LOCK_ARGS)

.PHONY: clean
clean:
	$(rm_dir) $(venv_dir) $(ignore_failure)

.PHONY: check
check:
	@echo "Running code quality checks..."
	@echo ""
	@echo "→ Formatting code..."
	@uvx ruff format --no-cache .
	@echo ""
	@echo "→ Linting code..."
	@uvx ruff check --no-cache --fix .
	@echo ""
	@echo "→ Type checking code..."
	@uv run $(uv_project_args) $(UV_RUN_ARGS) pyright $(PYRIGHT_ARGS) || (echo ""; echo "❌ Type check failed!"; exit 1)
	@echo ""
	@echo "✅ All checks passed!"

ifneq ($(findstring pytest,$(if $(shell $(call command_exists,uv) $(stderr_redirect_null)),$(shell uv tree --depth 1 $(stderr_redirect_null)),)),)
PYTEST_EXISTS=true
endif
ifneq ($(findstring pyright,$(if $(shell $(call command_exists,uv) $(stderr_redirect_null)),$(shell uv tree --depth 1 $(stderr_redirect_null)),)),)
PYRIGHT_EXISTS=true
endif


ifeq ($(PYTEST_EXISTS),true)
.PHONY: test pytest
test: pytest
pytest:
	uv run $(uv_project_args) $(UV_RUN_ARGS) pytest $(PYTEST_ARGS)
endif
