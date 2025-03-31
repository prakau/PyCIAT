#!/usr/bin/env python
##############################################################################
### File: scripts/setup_directories.py
##############################################################################
"""
Create required directory structure for the framework.
"""

import os
from pathlib import Path

# Define directory structure
DIRECTORIES = [
    # Data directories
    "data/climate/era5",
    "data/climate/cmip6",
    "data/gis",
    "data/soil",
    "data/templates/dssat",
    "data/templates/apsim",
    "data/templates/stics",
    
    # Simulation directories
    "simulations/setup",
    "simulations/output",
    
    # Analysis directories
    "analysis/results",
    "analysis/figures/impacts",
    "analysis/figures/adaptations",
    
    # Model directories
    "models/surrogate",
    
    # Log directory
    "logs",
    
    # Documentation
    "docs/figures",
    "docs/_static",
    "docs/_templates",
    
    # Notebooks for examples
    "notebooks"
]

def create_directories():
    """Create all required directories if they don't exist."""
    base_dir = Path(__file__).parent.parent
    
    print("Creating directory structure...")
    for directory in DIRECTORIES:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {directory}")
    
    print("\nDirectory structure created successfully!")
    print("\nNext steps:")
    print("1. Copy config_template.yaml to config.yaml")
    print("2. Configure settings in config.yaml")
    print("3. Run scripts/00_setup_environment.py to validate setup")

if __name__ == "__main__":
    create_directories()
