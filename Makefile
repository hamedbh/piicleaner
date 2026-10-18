.PHONY: help dev check build docs test test_performance test_all clean lint format

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# uv rebuilds the extension by itself whenever the Rust code changes (see
# [tool.uv] cache-keys in pyproject.toml); this forces a fresh release build.
# Old version-specific builds (_internal.cpython-3XX-*.so) are removed first,
# as Python would load them in preference to the current _internal.abi3.so
dev:  ## Install in development mode (fresh release build)
	find python -name "*.so" -delete
	uv sync --reinstall-package piicleaner

check:  ## Check Rust code
	uv run cargo check

build:  ## Build release version
	uv run maturin build --release

docs: ## Render the docs
	uv export --only-group docs -o docs/requirements.txt
	uv run --directory docs sphinx-build -b html . _build/html

test:  ## Run tests (no performance)
	uv run cargo test
	uv run pytest -v -m "not performance"

# Performance tests take c. 4-5 mins to run
test_performance: dev ## Run performance and benchmarking tests
	uv run cargo test --release -- --ignored
	uv run pytest -v -m "performance"
	uv run cargo bench

test_all: test test_performance ## Run all tests (including performance)

clean:  ## Clean build artifacts
	cargo clean
	find python -name "*.so" -delete
	find python tests -name "__pycache__" -type d -exec rm -rf {} +
	@echo "Run 'make dev' to rebuild the extension"

lint: ## Lint code
	uv run cargo clippy
	uv run ruff check

format:  ## Format code
	uv run cargo fmt
	uv run ruff format
