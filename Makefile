.PHONY: install test lint fmt clean

install:
	python -m pip install -e ".[dev]"
	pre-commit install

test:
	pytest

lint:
	ruff check .

fmt:
	ruff check --fix . && ruff format .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
