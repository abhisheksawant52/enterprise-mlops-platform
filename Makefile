.DEFAULT_GOAL := help
.PHONY: help install lint format test build clean docker-build tf-fmt tf-validate helm-lint

IMAGE ?= ghcr.io/abhisheksawant52/enterprise-mlops-platform:dev
TF_DIR ?= terraform
CHART ?= helm/mlops-platform

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install package with dev dependencies
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

lint: ## Run ruff and black in check mode
	ruff check src tests
	black --check src tests

format: ## Auto-format the codebase
	ruff check --fix src tests
	black src tests

test: ## Run the test suite
	pytest

build: ## Build distribution artifacts
	python -m pip install --upgrade build
	python -m build

docker-build: ## Build the container image
	docker build -t $(IMAGE) .

tf-fmt: ## Check Terraform formatting
	terraform -chdir=$(TF_DIR) fmt -recursive -check

tf-validate: ## Validate Terraform configuration
	terraform -chdir=$(TF_DIR) init -backend=false
	terraform -chdir=$(TF_DIR) validate

helm-lint: ## Lint the Helm chart
	helm lint $(CHART)

clean: ## Remove build and cache artifacts
	rm -rf build dist *.egg-info src/*.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
