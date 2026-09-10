.PHONY: install install-dev test lint format typecheck clean build publish-docs run docker-build docker-run

# ── Installation ──────────────────────────────────────────────────────────────

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-all:
	pip install -e ".[all]"

# ── Quality ───────────────────────────────────────────────────────────────────

test:
	pytest tests/ -v --tb=short --cov=veni --cov-report=term --cov-report=html

test-quick:
	pytest tests/ -v --tb=short -x

coverage:
	pytest tests/ --cov=veni --cov-report=html --cov-report=term

lint:
	ruff check veni/ tests/

lint-fix:
	ruff check veni/ tests/ --fix

format:
	black veni/ tests/

format-check:
	black --check veni/ tests/

typecheck:
	mypy veni/ --ignore-missing-imports --no-error-summary

security:
	bandit -c pyproject.toml -r veni/

check: format-check lint typecheck test security

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -rf htmlcov/ .coverage .coverage.*
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# ── Build & Publish ──────────────────────────────────────────────────────────

build: clean
	pip install --quiet build
	python -m build

publish: build
	pip install --quiet twine
	twine upload dist/*

# ── Docs ──────────────────────────────────────────────────────────────────────

docs-install:
	pip install mkdocs mkdocs-material

docs-serve: docs-install
	mkdocs serve

docs-build: docs-install
	mkdocs build

publish-docs: docs-build
	mkdocs gh-deploy

# ── Docker ────────────────────────────────────────────────────────────────────

docker-build:
	docker build -t veni-ai .

docker-run:
	docker run -it --rm -v "$(PWD):/workspace" veni-ai

docker-compose-up:
	docker compose up -d

docker-compose-down:
	docker compose down

# ── Pre-commit ────────────────────────────────────────────────────────────────

precommit-install:
	pip install pre-commit && pre-commit install

precommit-update:
	pre-commit autoupdate

precommit-run:
	pre-commit run --all-files
