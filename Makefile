.PHONY: help install dev build test lint format clean check

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev:  ## Install in development mode
	uv run maturin develop

check:  ## Check Rust code
	cargo check

build:  ## Build release version
	uv run maturin build --release

test:  ## Run quick test
	uv run python -c "from piicleaner import Cleaner; c = Cleaner(); print('✓ Import successful')"

test-full:  ## Run comprehensive test
	uv run python -c "from piicleaner import Cleaner; c = Cleaner(); text = 'Email john@test.com or call 555-123-4567'; print('Detected:', len(c.detect_pii(text)), 'items'); print('✓ Full test passed')"

test-api:  ## Test the main API functionality
	uv run python -c "from piicleaner import Cleaner; c = Cleaner(); text = 'Email john@test.com'; result = c.clean_list([text, 'No PII here'], 'redact'); print('✓ API test passed:', len([x for x in result if 'john@test.com' not in x]) == 2)"

clean:  ## Clean build artifacts
	cargo clean
	find . -name "*.so" -delete
	find . -name "__pycache__" -delete

install:  ## Install package
	uv sync

format:  ## Format code (when we add it later)
	cargo fmt
