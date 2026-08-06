.PHONY: format

format: ## Format the entire repository with Taidy.
	uv run python -m taidy format .
