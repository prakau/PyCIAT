# Makefile for Crop Model Climate Impact Framework

# Variables
PYTHON := python
VENV_NAME := venv
VENV_BIN := $(VENV_NAME)/bin
PIP := $(VENV_BIN)/pip
PYTEST := $(VENV_BIN)/pytest
BLACK := $(VENV_BIN)/black
FLAKE8 := $(VENV_BIN)/flake8
MYPY := $(VENV_BIN)/mypy
SPHINX_BUILD := $(VENV_BIN)/sphinx-build

# Installation and setup
.PHONY: install
install:
	$(PYTHON) -m venv $(VENV_NAME)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PYTHON) scripts/setup_directories.py

.PHONY: install-dev
install-dev: install
	$(PIP) install -r notebooks/notebook_requirements.txt
	$(PIP) install -r docs/requirements-docs.txt

# Development tasks
.PHONY: format
format:
	$(BLACK) src/ scripts/ tests/

.PHONY: lint
lint:
	$(FLAKE8) src/ scripts/ tests/

.PHONY: typecheck
typecheck:
	$(MYPY) src/ scripts/

.PHONY: test
test:
	$(PYTEST) tests/ --cov=src --cov-report=html

.PHONY: check
check: format lint typecheck test

# Documentation
.PHONY: docs
docs:
	$(SPHINX_BUILD) -b html docs/ docs/_build/html

.PHONY: docs-pdf
docs-pdf:
	$(SPHINX_BUILD) -b latex docs/ docs/_build/latex
	cd docs/_build/latex && make all-pdf

.PHONY: docs-live
docs-live:
	$(SPHINX_BUILD) -b html docs/ docs/_build/html -a -W --watch docs/

.PHONY: docs-clean
docs-clean:
	rm -rf docs/_build/

# Pipeline execution
.PHONY: run-pipeline
run-pipeline:
	$(PYTHON) scripts/run_all.py --config config/config.yaml

.PHONY: setup-env
setup-env:
	$(PYTHON) scripts/00_setup_environment.py --config config/config.yaml

.PHONY: prepare-climate
prepare-climate:
	$(PYTHON) scripts/01_prepare_climate_data.py --config config/config.yaml

.PHONY: setup-sims
setup-sims:
	$(PYTHON) scripts/02_setup_simulations.py --config config/config.yaml

.PHONY: run-sims
run-sims:
	$(PYTHON) scripts/03_run_simulations_parallel.py --config config/config.yaml

.PHONY: process-outputs
process-outputs:
	$(PYTHON) scripts/04_process_outputs.py --config config/config.yaml

.PHONY: analyze-impacts
analyze-impacts:
	$(PYTHON) scripts/05_analyze_impacts.py --config config/config.yaml

.PHONY: analyze-adaptations
analyze-adaptations:
	$(PYTHON) scripts/06_analyze_adaptations.py --config config/config.yaml

.PHONY: generate-visualizations
generate-visualizations:
	$(PYTHON) scripts/07_generate_visualizations.py --config config/config.yaml

# Surrogate model tasks
.PHONY: train-surrogate
train-surrogate:
	$(PYTHON) scripts/train_surrogate.py --config config/config.yaml

.PHONY: predict-surrogate
predict-surrogate:
	$(PYTHON) scripts/predict_surrogate.py --config config/config.yaml --scenarios scenarios.csv

# Clean-up tasks
.PHONY: clean
clean:
	rm -rf simulations/setup/*
	rm -rf simulations/output/*
	rm -rf analysis/results/*
	rm -rf analysis/figures/*
	rm -rf logs/*
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

.PHONY: clean-all
clean-all: clean docs-clean
	rm -rf $(VENV_NAME)
	rm -rf models/*

# Help target
.PHONY: help
help:
	@echo "PyCIAT Framework Makefile"
	@echo ""
	@echo "Installation:"
	@echo "  make install      Install basic dependencies"
	@echo "  make install-dev  Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make format      Format code with black"
	@echo "  make lint        Run flake8 linter"
	@echo "  make typecheck   Run mypy type checker"
	@echo "  make test        Run tests with coverage"
	@echo "  make check       Run all code quality checks"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs        Build HTML documentation"
	@echo "  make docs-pdf    Build PDF documentation"
	@echo "  make docs-live   Build docs with live reload"
	@echo "  make docs-clean  Clean documentation build"
	@echo ""
	@echo "Pipeline:"
	@echo "  make run-pipeline          Run complete pipeline"
	@echo "  make setup-env            Setup environment"
	@echo "  make prepare-climate      Prepare climate data"
	@echo "  make setup-sims          Setup simulations"
	@echo "  make run-sims            Run simulations"
	@echo "  make process-outputs     Process outputs"
	@echo "  make analyze-impacts     Analyze impacts"
	@echo "  make analyze-adaptations Analyze adaptations"
	@echo "  make generate-visualizations Generate visualizations"
	@echo ""
	@echo "Surrogate Models:"
	@echo "  make train-surrogate    Train surrogate model"
	@echo "  make predict-surrogate  Make predictions"
	@echo ""
	@echo "Clean-up:"
	@echo "  make clean      Clean temporary files"
	@echo "  make clean-all  Clean everything including venv"
