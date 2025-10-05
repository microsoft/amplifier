.PHONY: install test clean lint check

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/

lint:
	ruff check amplifier/
	ruff format amplifier/

check:
	pyright amplifier/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

run:
	python -m amplifier

help:
	@echo "Available commands:"
	@echo "  make install      - Install the package"
	@echo "  make install-dev  - Install with development dependencies"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linting and formatting"
	@echo "  make check       - Run type checking"
	@echo "  make clean       - Clean build artifacts"
	@echo "  make run         - Run the CLI in interactive mode"