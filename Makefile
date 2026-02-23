# Code Review Benchmark - Development Makefile
# Run 'make help' for a list of available commands

.PHONY: help
help: ## Show this help message
	@echo "Code Review Benchmark - Development Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

.PHONY: install
install: ## Install the package in development mode
	pip install -e ".[dev]"

.PHONY: setup
setup: install ## Full development setup
	crb setup
	@echo "✅ Development environment ready!"

.PHONY: test
test: ## Run all tests
	pytest tests/ -v

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	pytest tests/ -v --cov=code_review_benchmark --cov-report=html --cov-report=term

.PHONY: lint
lint: ## Run code linting
	ruff check src/

.PHONY: format
format: ## Format code with ruff
	ruff format src/

.PHONY: check
check: lint test ## Run all checks (lint + test)
	@echo "✅ All checks passed!"

.PHONY: validate
validate: ## Validate all challenges
	crb validate-challenges

.PHONY: run
run: ## Run benchmark (all tools × all challenges)
	crb run

.PHONY: run-quick
run-quick: ## Quick run (1 iteration, 2 challenges)
	crb run --runs 1 --challenges sql-injection-express,hardcoded-secrets

.PHONY: clean
clean: ## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

.PHONY: build
build: clean ## Build distribution packages
	python -m build

.PHONY: docs
docs: ## Generate documentation
	@echo "📚 Documentation is in the docs/ folder"
	@echo "- Adding Tools: docs/adding-tools.md"
	@echo "- Adding Challenges: docs/adding-challenges.md"
	@echo "- Evaluation Method: docs/evaluation-methodology.md"

.PHONY: serve-docs
serve-docs: ## Serve documentation locally (requires mkdocs)
	@if command -v mkdocs &> /dev/null; then \
		mkdocs serve; \
	else \
		echo "❌ mkdocs not installed. Run: pip install mkdocs"; \
	fi

.PHONY: pr-check
pr-check: lint test validate ## Pre-PR checks
	@echo "✅ Ready to create a pull request!"

.PHONY: tool-status
tool-status: ## Check tool availability
	@python -c "from code_review_benchmark.cli.main import app; import typer; typer.main.get_command(app)(['setup'])"

.PHONY: list-tools
list-tools: ## List available tools
	crb list-tools

.PHONY: list-challenges
list-challenges: ## List available challenges
	crb list-challenges

.PHONY: dev-install
dev-install: ## Install all development tools
	pip install --upgrade pip
	pip install -e ".[dev]"
	pip install pre-commit
	pre-commit install

.PHONY: update-deps
update-deps: ## Update dependencies
	pip install --upgrade pip
	pip list --outdated

# Docker commands (optional)
.PHONY: docker-build
docker-build: ## Build Docker image
	docker build -t code-review-benchmark:latest .

.PHONY: docker-run
docker-run: ## Run in Docker container
	docker run --rm -it -v $(PWD)/results:/app/results code-review-benchmark:latest

# Git shortcuts
.PHONY: branch
branch: ## Create a new feature branch
	@read -p "Enter branch name (feature/): " name; \
	git checkout -b feature/$$name

.PHONY: sync
sync: ## Sync with upstream main
	git fetch upstream
	git checkout main
	git merge upstream/main
	git push origin main