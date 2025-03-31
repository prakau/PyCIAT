# Contributing to Crop Model Climate Impact Framework

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/pyciat.git # Replace your-username
   cd pyciat
   ```
3. Set up the development environment

## Development Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Install development dependencies:
   ```bash
   make install-dev
   ```

3. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, following our coding standards

3. Run tests and checks:
   ```bash
   make check  # Runs format, lint, typecheck, and test
   ```

4. Commit your changes using conventional commit messages:
   ```bash
   git commit -m "feat: add new feature"
   git commit -m "fix: resolve issue with..."
   git commit -m "docs: update documentation"
   ```

## Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Run the test suite
4. Push to your fork
5. Submit a Pull Request (PR)
6. Address review comments

### PR Requirements

- [ ] Tests pass
- [ ] Code is formatted and linted
- [ ] Documentation is updated
- [ ] Changes are described in PR description
- [ ] Conventional commit messages used

## Coding Standards

### Python Style Guide

- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters (Black default)
- Use docstrings (NumPy format)

### Example Code Style

```python
from typing import List, Optional

def process_data(data: List[float], threshold: Optional[float] = None) -> List[float]:
    """
    Process data using the specified threshold.

    Parameters
    ----------
    data : List[float]
        Input data to process
    threshold : Optional[float]
        Processing threshold, by default None

    Returns
    -------
    List[float]
        Processed data
    """
    if threshold is None:
        threshold = 0.0
    
    return [x for x in data if x > threshold]
```

## Testing Guidelines

1. Write tests for new features
2. Maintain test coverage
3. Use pytest fixtures
4. Mock external dependencies

### Test Example

```python
import pytest
from src.utils import process_data

def test_process_data():
    data = [1.0, 2.0, 3.0]
    threshold = 2.0
    result = process_data(data, threshold)
    assert len(result) == 1
    assert result[0] == 3.0
```

## Documentation

1. Update docstrings for new/modified functions
2. Update relevant documentation files
3. Add examples where appropriate

### Building Documentation

```bash
# Build HTML documentation
make docs

# Build PDF documentation
make docs-pdf

# Live documentation preview
make docs-live
```

## Project Structure

```
.
├── config/            # Configuration files
├── data/             # Data directory
├── docs/             # Documentation
├── notebooks/        # Jupyter notebooks
├── scripts/          # Pipeline scripts
├── src/             # Source code
│   ├── crop_model_interface/
│   └── ...
└── tests/           # Test files
```

## Adding New Features

1. **New Crop Models**
   - Add interface in `src/crop_model_interface/`
   - Implement required methods
   - Add tests
   - Update documentation

2. **New Analysis Tools**
   - Add module in appropriate location
   - Follow existing patterns
   - Include examples

## Release Process

1. Update version in relevant files
2. Update CHANGELOG.md
3. Create and push tag
4. GitHub Actions will handle the release

## Questions and Support

- Open an issue for bugs
- Use discussions for questions
- Join our community chat

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
