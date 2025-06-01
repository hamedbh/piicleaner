.PHONY: help install dev build test lint format clean check

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev:  ## Install in development mode
	uv run maturin develop

check:  ## Check Rust code
	cargo check

build:  ## Build release version
	uv run maturin build --release

test:
	cargo test
	uv run pytest -v

clean:  ## Clean build artifacts
	cargo clean
	find . -name "*.so" -delete
	find . -name "__pycache__" -delete

format:  ## Format code (when we add it later)
	cargo fmt
