.DEFAULT_GOAL := test

.PHONY: dist test-unit test-integration test-docker test test-all typecheck check clean format

dist: ## Build distribution packages.
	uv build

test-unit: ## Run unit tests.
	uv run python -m unittest discover tests/unit -v

test-integration: ## Run integration tests.
	uv run python -m unittest discover tests/integration -v

test-docker: ## Run Docker-based integration tests.
	uv run python -m unittest discover tests/docker_tests -v

test: test-unit test-integration ## Run fast tests.

test-all: test test-docker ## Run all tests, including Docker tests.

typecheck: ## Run mypy type checking.
	uv run mypy taidy/

check: typecheck test ## Run type checks and fast tests.

clean: ## Remove build and Python cache artifacts.
	rm -rf dist/ build/ *.egg-info/ __pycache__/ *.pyc taidy/__pycache__/ taidy/*.pyc

# args: files?=.
format: ## Format files or the entire repository with Taidy.
	uv run python -m taidy format "$(if $(FILES),$(FILES),.)"
