# Example Notebooks

This directory contains Jupyter notebooks demonstrating the usage of the framework and providing examples for common tasks.

## Contents

### 1. Framework Basics
- `01_configuration.ipynb`: Setting up and customizing the framework configuration
- `02_model_interfaces.ipynb`: Working with different crop model interfaces

### 2. Climate Data Processing
- `03_climate_data_loading.ipynb`: Loading and processing climate model outputs
- `04_climate_data_visualization.ipynb`: Visualizing climate data and scenarios

### 3. Simulation Management
- `05_simulation_setup.ipynb`: Setting up crop model simulations
- `06_parallel_execution.ipynb`: Running simulations in parallel
- `07_output_processing.ipynb`: Processing and analyzing simulation outputs

### 4. Impact Analysis
- `08_baseline_analysis.ipynb`: Analyzing baseline period simulations
- `09_climate_impacts.ipynb`: Calculating and visualizing climate change impacts
- `10_adaptation_evaluation.ipynb`: Evaluating adaptation strategies

### 5. Surrogate Models
- `11_surrogate_training.ipynb`: Training and validating surrogate models
- `12_surrogate_predictions.ipynb`: Using surrogate models for rapid assessment

## Usage

1. Ensure you have Jupyter installed:
```bash
pip install jupyter
```

2. Launch Jupyter:
```bash
jupyter notebook
```

3. Navigate to the notebooks directory and open desired example

## Requirements

The notebooks require all framework dependencies plus:
- jupyter
- matplotlib
- seaborn
- plotly (for interactive visualizations)

Install additional requirements:
```bash
pip install -r notebook_requirements.txt
```

## Notes

- These notebooks are for demonstration purposes
- Some examples may require specific data files
- Adjust paths and parameters for your setup
- See framework documentation for detailed reference
