.PHONY: help dev check build test test_performance test_all clean format

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev:  ## Install in development mode
	uv run maturin develop

check:  ## Check Rust code
	cargo check

build:  ## Build release version
	uv run maturin build --release

test:  ## Run tests (no performance)
	cargo test
	uv run pytest -v -m "not performance"

test_performance: ## Run performance and benchmarking tests
	uv run pytest -v -m "performance"
	cargo bench

test_all: test test_performance ## Run all tests (including performance)

clean:  ## Clean build artifacts
	cargo clean
	find . -name "*.so" -delete
	find . -name "__pycache__" -delete

lint: ## Lint code
	cargo clippy
	uv run ruff check

format:  ## Format code
	cargo fmt
	uv run ruff format
