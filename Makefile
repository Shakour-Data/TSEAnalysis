.PHONY: help install dev-install test test-cov clean lint format docs build deploy

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

dev-install:  ## Install development dependencies
	pip install -r requirements.txt
	pip install -e .[dev]

test:  ## Run tests
	pytest tests/

test-cov:  ## Run tests with coverage
	pytest --cov=app --cov-report=html --cov-report=term-missing tests/

clean:  ## Clean up cache and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +

lint:  ## Run linting
	flake8 app/ tests/
	mypy app/

format:  ## Format code
	black app/ tests/
	isort app/ tests/

docs:  ## Build documentation
	sphinx-build -b html docs/ docs/_build/html

build:  ## Build package
	python -m build

deploy: clean build  ## Build and prepare for deployment
	@echo "Package built successfully. Ready for deployment."

run:  ## Run the Flask application
	python app.py

# Windows-specific commands (use with make -f Makefile.win)
.PHONY: win-install win-dev-install win-test win-clean

win-install:
	pip install -r requirements.txt

win-dev-install:
	pip install -r requirements.txt
	pip install -e .[dev]

win-test:
	pytest tests/

win-clean:
	if exist __pycache__ rmdir /s /q __pycache__
	if exist *.pyc del /q *.pyc
	if exist *.pyo del /q *.pyo
	if exist *.pyd del /q *.pyd
	if exist .pytest_cache rmdir /s /q .pytest_cache
	if exist htmlcov rmdir /s /q htmlcov
	if exist dist rmdir /s /q dist
	if exist build rmdir /s /q build
	if exist .coverage del /q .coverage