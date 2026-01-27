.PHONY: help install install-dev install-all test test-cov format lint clean lock upgrade venv

help:  ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

venv:  ## Create virtual environment
	uv venv
	@echo ""
	@echo "Virtual environment created. Activate with:"
	@echo "  source .venv/bin/activate  # macOS/Linux"
	@echo "  .venv\\Scripts\\activate     # Windows"

install:  ## Install package in editable mode
	uv pip install -e .

install-dev:  ## Install package with dev dependencies
	uv pip install -e ".[dev]"

install-all:  ## Install package with all optional dependencies
	uv pip install -e ".[dev,notebooks,config]"

test:  ## Run tests
	pytest

test-cov:  ## Run tests with coverage report
	pytest --cov=yalab_procedures --cov-report=term-missing --cov-report=html
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

format:  ## Format code with black
	black src tests examples

format-check:  ## Check code formatting without changes
	black --check src tests examples

lint:  ## Lint code with ruff
	ruff check src tests examples

lint-fix:  ## Lint and auto-fix issues
	ruff check src tests examples --fix

qa: format-check lint test  ## Run all quality checks

lock:  ## Update lock file
	uv lock

upgrade:  ## Upgrade all dependencies
	uv lock --upgrade
	@echo ""
	@echo "Dependencies upgraded. Run 'make install-dev' to install updates."

sync:  ## Sync environment with lock file
	uv pip sync

clean:  ## Remove build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

clean-venv:  ## Remove virtual environment
	rm -rf .venv

notebook:  ## Start Jupyter notebook server
	jupyter notebook notebooks/

lab:  ## Start Jupyter lab server
	jupyter lab notebooks/

docs:  ## Open main documentation files
	@echo "Documentation files:"
	@echo "  README.md - Main documentation"
	@echo "  DEVELOPMENT.md - Development guide"
	@echo "  UV_QUICKSTART.md - Quick start with uv"
	@echo "  ARCHITECTURE.md - Architecture documentation"
	@echo "  notebooks/README.md - Notebook examples"

setup: venv install-dev  ## Complete setup: create venv and install dev dependencies
	@echo ""
	@echo "Setup complete! Don't forget to activate the virtual environment:"
	@echo "  source .venv/bin/activate"

# Development workflow targets
dev-start:  ## Start development session (activate venv, show status)
	@echo "Development environment ready!"
	@echo ""
	@echo "Quick commands:"
	@echo "  make test      - Run tests"
	@echo "  make format    - Format code"
	@echo "  make lint      - Lint code"
	@echo "  make qa        - Run all quality checks"
	@echo ""

# CI targets
ci: format-check lint test  ## Run CI checks (format, lint, test)
	@echo ""
	@echo "✅ All CI checks passed!"

# Build targets
build:  ## Build distribution packages
	uv build

publish-test:  ## Publish to Test PyPI
	uv publish --publish-url https://test.pypi.org/legacy/

publish:  ## Publish to PyPI
	uv publish

# Info targets
info:  ## Show package and environment info
	@echo "Package: yalab-procedures"
	@echo "Version: $$(grep '^version = ' pyproject.toml | cut -d'"' -f2)"
	@echo ""
	@echo "Python: $$(python --version 2>&1)"
	@echo "uv: $$(uv --version 2>&1)"
	@echo ""
	@echo "Virtual environment:"
	@if [ -d .venv ]; then \
		echo "  Status: ✅ Exists"; \
		echo "  Path: $$(pwd)/.venv"; \
	else \
		echo "  Status: ❌ Not created (run 'make venv')"; \
	fi
