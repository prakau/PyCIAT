# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial framework structure
- Support for DSSAT, APSIM, and STICS crop models
- Climate data processing pipeline
- Impact analysis tools
- Adaptation evaluation functionality
- Surrogate model training and prediction
- Documentation system
- CI/CD pipeline
- Multiple model interfaces

### Changed
- Standardized script naming:
  - Scripts now follow numbered sequence (00-09)
  - Renamed adaptations script to use consistent terminology (analyze vs evaluate)
  - Renamed visualizations script to match implementation
- Improved HPC documentation and added SLURM template

### Deprecated
- Deprecated standalone train_surrogate.py in favor of 08_train_surrogate.py
- Deprecated standalone predict_surrogate.py in favor of 09_predict_surrogate.py

### Removed
- None

### Fixed
- None

### Security
- None

## [0.1.0] - 2025-03-31

### Added
- Basic project structure
- Core interfaces for crop models:
  - Base interface class
  - DSSAT implementation
  - APSIM implementation
  - STICS implementation
- Climate data processing:
  - Support for ERA5 reanalysis
  - Support for CMIP6 data
  - Data extraction and validation
- Simulation management:
  - Configuration system
  - Parallel execution support
  - Progress tracking
- Analysis tools:
  - Impact calculations
  - Ensemble statistics
  - Regional aggregation
- Visualization capabilities:
  - Spatial impact maps
  - Time series plots
  - Ensemble agreement plots
- Documentation:
  - User guides
  - API reference
  - Example notebooks
- Development tools:
  - Testing framework
  - Code formatting
  - Type checking
  - CI/CD pipeline

### Changed
- None (initial release)

### Deprecated
- None

### Removed
- None

### Fixed
- None

### Security
- None

[Unreleased]: https://github.com/username/pyciat/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/username/pyciat/releases/tag/v0.1.0
