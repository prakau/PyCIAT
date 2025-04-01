# PyCIAT: A Configurable Python Framework for Scalable, Multi-Model Assessment of Climate Change Impacts and Adaptations in Agriculture

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10-blue)](https://www.python.org)
[![CI Status](https://github.com/username/pyciat/actions/workflows/ci.yml/badge.svg)](https://github.com/username/pyciat/actions/workflows/ci.yml)
[![Coverage Status](https://codecov.io/gh/username/pyciat/branch/main/graph/badge.svg)](https://codecov.io/gh/username/pyciat)
[![Documentation Status](https://readthedocs.org/projects/pyciat/badge/?version=latest)](https://pyciat.readthedocs.io/en/latest/?badge=latest)

## Overview

PyCIAT (Python Climate Impact and Adaptation Toolkit for Agriculture) is an open-source, configuration-driven framework designed to orchestrate complex agricultural impact assessments under climate change. It addresses the need for scalable, reproducible, and robust exploration of uncertainty through multi-model ensembles.

Synthesizing climate change impacts on agriculture requires integrating diverse climate projections, spatial data, multiple process-based crop models, and various management scenarios. Existing approaches often rely on cumbersome, specific scripting, hindering scalability and reproducibility. PyCIAT provides a modular Python architecture, driven by a central YAML configuration file, to manage workflows encompassing:

*   **Climate Data Processing:** Handling GCMs/RCMs (e.g., CMIP6, CORDEX) with subsetting, variable selection, and point extraction.
*   **Soil Data Integration:** Incorporating spatial soil data and profile information.
*   **Simulation Setup:** Generating model-specific inputs across multiple locations and scenarios.
*   **Multi-Model Execution:** Parallelized execution of crop simulation models (placeholders for DSSAT, APSIM, STICS provided) via standardized interfaces.
*   **HPC Readiness:** Support for cluster job arrays (e.g., SLURM).
*   **Post-Processing:** Automated analysis for impacts (vs. baseline) and adaptation strategy effectiveness.
*   **Standardization:** Consistent output variable mapping across models.
*   **Extensibility:** Optional integration points for advanced modules (e.g., detailed water dynamics, biotic stress) and machine learning surrogates.

This framework significantly reduces boilerplate code, enhances reproducibility, and facilitates large-scale, systematic exploration of climate impacts and adaptation strategies across diverse agricultural systems.

**Keywords:** Climate Change Impacts, Crop Modeling, Integrated Assessment Framework, Scientific Workflow, Multi-Model Ensemble, High-Performance Computing, Agricultural Systems Modeling, Python, Reproducibility.

**NOTE:** This repository provides the framework structure, configuration, command-line scripts, and utility functions. The core scientific logic within the **crop model interfaces** (`src/crop_model_interface/`), **advanced simulation modules** (e.g., `src/advanced_modules/`), and **machine learning surrogate training/prediction** (`src/surrogate_model/`) are provided as **detailed placeholders**. Users **must implement** this logic based on their specific model versions, data, and scientific requirements for the framework to be fully functional.

## Directory Structure

```
pyciat/
│
├── .github/                    # GitHub Actions workflows
│   └── workflows/
│       └── ci.yml
├── .coveragerc                 # Test coverage configuration
├── .gitignore                  # Files excluded from Git
├── .pre-commit-config.yaml     # Pre-commit hook configuration
├── CHANGELOG.md                # Project changes history
├── CODE_OF_CONDUCT.md          # Contributor code of conduct
├── CONTRIBUTING.md             # Guidelines for contributing
├── LICENSE                     # Project license (MIT)
├── Makefile                    # Development and automation tasks
├── MANIFEST.in                 # Packaging manifest
├── pyproject.toml              # Build system and tool configuration
├── README.md                   # This file
├── requirements.txt            # Python dependencies
│
├── config/                     # Configuration files
│   └── config_template.yaml    # *** Central control file template (EDIT THIS) ***
│
├── data/                       # (Not in Git) Input data - User managed
│   ├── climate/                # Raw/processed climate model outputs
│   ├── experimental/           # Crop trial data for calibration (optional)
│   ├── gis/                    # Shapefiles, reference grids etc.
│   ├── soil/                   # Soil map, profile data
│   └── templates/              # Model-specific template files (e.g., APSIM .apsimx)
│       └── README.md
│
├── docs/                       # Documentation source files (Sphinx)
│   ├── conf.py
│   ├── index.rst
│   ├── requirements-docs.txt
│   └── ...
│
├── examples/                   # Example configurations and use cases
│   ├── single_site/
│   ├── regional_assessment/
│   └── adaptation_study/
│
├── logs/                       # (Not in Git) Runtime log files
│
├── models/                     # (Not in Git) Trained model artifacts / Model executables
│   └── surrogates/            # Saved ML surrogate models
│
├── notebooks/                  # Jupyter notebooks for exploration, tutorials
│   ├── README.md
│   └── notebook_requirements.txt
│
├── scripts/                    # Main executable pipeline scripts
│   ├── 00_setup_environment.py   # Setup checks
│   ├── 01_prepare_climate_data.py # Climate processing & point extraction
│   ├── 02_setup_simulations.py   # Generate simulation inputs & status file
│   ├── 03_run_simulations_parallel.py # Execute crop models (local/HPC)
│   ├── 04_process_outputs.py     # Parse outputs, standardize variables
│   ├── 05_analyze_impacts.py     # Calculate impacts vs baseline
│   ├── 06_analyze_adaptations.py # Analyze adaptation effectiveness
│   ├── 07_generate_visualizations.py # Create plots/maps
│   ├── 08_train_surrogate.py     # Optional: Train ML model
│   ├── 09_predict_surrogate.py   # Optional: Predict with ML model
│   ├── run_all.py                # Script to run all steps
│   ├── run_hpc.sh               # HPC job submission template
│   └── setup_directories.py      # Utility to create needed dirs
│
├── simulations/                # (Not in Git) Generated simulation files
│   ├── setup/                  # Organized inputs per run
│   ├── output/                 # Raw model outputs per run
│   └── simulation_status.csv   # Tracking file for all runs (or .db)
│
├── src/                        # Source code library
│   ├── advanced_modules/       # Advanced integrations (placeholders)
│   │   ├── __init__.py
│   │   ├── biotic_stress/
│   │   └── hydrus/
│   ├── analysis.py             # Impact and adaptation analysis functions
│   ├── climate_processing.py   # Climate data loading and processing
│   ├── config_loader.py        # YAML configuration loading and validation
│   ├── crop_model_interface/   # Model interfaces (placeholders)
│   │   ├── __init__.py
│   │   ├── apsim_interface.py
│   │   ├── base_interface.py
│   │   ├── dssat_interface.py
│   │   ├── status_codes.py     # Simulation status definitions
│   │   └── stics_interface.py
│   ├── soil_processing.py      # Soil data handling (placeholder)
│   ├── surrogate_model/        # ML logic (placeholders)
│   │   ├── __init__.py
│   │   ├── evaluation.py
│   │   ├── feature_engineering.py
│   │   └── model_selection.py
│   ├── utils.py                # Utility functions (logging, paths, etc.)
│   ├── visualization.py        # Plotting functions
│   └── __init__.py
│
└── tests/                      # Unit and integration tests
    ├── conftest.py
    └── test_*.py
```

## Setup

1.  **Clone the Repository:**
    git clone https://github.com/username/pyciat.git
    cd pyciat
    ```

2.  **Create a Virtual Environment:** (Recommended)
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/Mac
    # venv\Scripts\activate  # On Windows
    ```

3.  **Install Dependencies:**
    ```bash
    # Install core dependencies
    pip install -r requirements.txt

    # For development (testing, linting, docs):
    make install-dev
    # Or: pip install -r requirements.txt -r docs/requirements-docs.txt -r notebooks/notebook_requirements.txt pytest black flake8 mypy pre-commit ...
    ```

4.  **Configure:**
    *   **Crucially, copy `config/config_template.yaml` to `config/config.yaml` and edit it**:
        *   Set the `base_dir` to the **absolute path** of the cloned repository on your system.
        *   Update all paths in the `paths:` section to point to your actual data locations (or ensure data is placed according to the structure under `base_dir/data/`). Remember `data/` is ignored by Git, so you need to manage this data separately.
        *   Verify/Edit the `executable_path` for each crop model you intend to run in `crop_model_configs:`. Make sure these point to the correct executables on your system or cluster.
        *   Review and adjust climate sources, models, scenarios, crop models to run, simulation settings, adaptation scenarios, analysis variables, and ML settings as needed.

5.  **Obtain Input Data:**
    *   Download or prepare the necessary climate data (GCM/RCM), soil data, GIS files, and experimental data (if needed for calibration).
    *   Organize the data according to the structure defined in `config/config.yaml` (typically within the `data/` directory).

6.  **(IMPORTANT) Implement Placeholders:**
    *   Navigate to `src/crop_model_interface/` and implement the Python logic within `dssat_interface.py`, `apsim_interface.py`, `stics_interface.py` for the specific models you are using. Focus on the methods defined in the base interface (`generate_weather`, `generate_soil`, `generate_experiment`, `run_model`, `parse_output`).
    *   If using advanced features, implement the logic in `src/soil_processing.py`, `src/advanced_modules/`, and the core training/prediction algorithms in `src/surrogate_model/`.

## Workflow and Usage

The framework is designed to be run as a sequence of scripts from the terminal. Ensure your virtual environment is activated and you are in the project's root directory (`pyciat/`). You can use the provided `Makefile` for convenience or run scripts directly.

**Using Makefile:**

```bash
# Check environment setup
make setup-env

# Prepare climate data
make prepare-climate

# Setup simulation input files
make setup-sims

# Run simulations (uses local parallel settings from config)
make run-sims
# For HPC, configure config.yaml and submit scripts/03... via scheduler (see HPC section)

# Process simulation outputs
make process-outputs

# Analyze impacts vs baseline
make analyze-impacts

# Analyze adaptation effectiveness
make analyze-adaptations

# Generate visualizations
make generate-visualizations

# Run the entire pipeline
make run-all # Executes scripts/run_all.py

# Optional: Train surrogate model
make train-surrogate

# Optional: Predict with surrogate model (requires input feature file)
make predict-surrogate
```

**Running Scripts Directly:**

1.  **Setup Environment Check:**
    ```bash
    python scripts/00_setup_environment.py --config config/config.yaml
    ```
    *(Checks directories, config validity, executable paths)*

2.  **Prepare Climate Data:**
    ```bash
    python scripts/01_prepare_climate_data.py --config config/config.yaml
    ```
    *(Processes climate grids, extracts point data, saves cached data)*
    *Optional filters: `--sources`, `--models`, `--scenarios`, `--periods`*

3.  **Setup Simulation Inputs:**
    ```bash
    python scripts/02_setup_simulations.py --config config/config.yaml
    ```
    *(Generates input files, creates/updates `simulations/simulation_status.csv`)*

4.  **Run Simulations:**
    ```bash
    # Using local multiprocessing (uses num_workers from config)
    python scripts/03_run_simulations_parallel.py --config config/config.yaml

    # Or using an HPC scheduler (see HPC Usage section)
    ```
    *(Executes models based on status file, updates status)*

5.  **Process Model Outputs:**
    ```bash
    python scripts/04_process_outputs.py --config config/config.yaml
    ```
    *(Parses raw outputs, maps variables, combines results, updates status)*

6.  **Analyze Impacts:**
    ```bash
    python scripts/05_analyze_impacts.py --config config/config.yaml
    ```
    *(Calculates baseline stats, future changes, ensemble stats)*

7.  **Analyze Adaptations:**
    ```bash
    python scripts/06_analyze_adaptations.py --config config/config.yaml
    ```
    *(Compares adaptation scenarios to baseline under future conditions)*

8.  **Generate Visualizations:**
    ```bash
    python scripts/07_generate_visualizations.py --config config/config.yaml
    ```
    *(Creates plots and maps, saves figures)*

9.  **(Optional) Train Surrogate Model:**
    ```bash
    # Ensure surrogate_model.enabled is true in config.yaml
    python scripts/08_train_surrogate.py --config config/config.yaml
    ```
    *(Trains ML models, saves artifacts)*

10. **(Optional) Predict with Surrogate:**
    ```bash
    # Requires an input feature file
    python scripts/09_predict_surrogate.py --config config/config.yaml --input_feature_file path/to/features.csv --output_prediction_file analysis_outputs/surrogate_predictions.csv
    ```
    *(Loads trained models, makes predictions)*

## HPC Usage

*   Set `parallel: use_hpc_env_vars: true` in `config.yaml`.
*   Configure `hpc_task_id_var` and `hpc_num_tasks_var` to match your scheduler (e.g., `SLURM_ARRAY_TASK_ID`, `SLURM_ARRAY_TASK_COUNT`).
*   A SLURM job submission script template is provided at `scripts/run_hpc.sh`. Modify this script to match your HPC environment configuration (modules, paths, resource requirements).
*   Submit the job script as an array job (e.g., `sbatch --array=1-N jobscript.sh`, where N is the desired number of parallel tasks).
*   The Python script `03_run_simulations_parallel.py` will automatically detect the environment variables and divide the simulations marked `READY_TO_RUN` among the job tasks based on the task ID.
*   Ensure the project directory (especially `simulations/simulation_status.csv` and the `simulations/setup/` directories) is on a shared filesystem accessible by all cluster nodes/jobs.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines.

## Code of Conduct

Please note that this project is released with a [Contributor Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## Contact

Dr. Prashant Kaushik (prashantumri@gmail.com)
