.PHONY: format

format: ## Format the entire repository with Taidy, then normalize Python formatting with Ruff.
	uv run python -m taidy format .
	uv run ruff format .
