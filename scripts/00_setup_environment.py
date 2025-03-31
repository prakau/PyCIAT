#!/usr/bin/env python
##############################################################################
### File: scripts/00_setup_environment.py
##############################################################################
"""
Initial setup script to validate environment and configuration.
Checks paths, dependencies, and model executables before pipeline execution.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add parent directory to Python path
repo_root = str(Path(__file__).parent.parent)
sys.path.insert(0, repo_root)

from src.config_loader import load_config, ConfigurationError
from src.utils import setup_logging, ensure_dir_exists, Timer
from src import get_model_interface

def check_python_dependencies() -> Tuple[bool, List[str]]:
    """
    Check if all required Python packages are installed.
    
    Returns:
        Tuple[bool, List[str]]: Success flag and list of missing packages
    """
    required_packages = [
        'numpy',
        'pandas',
        'xarray',
        'netCDF4',
        'geopandas',
        'matplotlib',
        'seaborn',
        'scikit-learn',
        'pyyaml'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return len(missing) == 0, missing

def validate_input_data(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if required input data files exist.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Tuple[bool, List[str]]: Success flag and list of missing files
    """
    missing_files = []
    
    # Check critical input files
    paths = config.get('paths', {})
    
    # Check soil/GIS files
    critical_files = [
        paths.get('soil_shapefile'),
        paths.get('soil_profiles'),
        paths.get('locations_file')
    ]
    
    for file_path in critical_files:
        if file_path and not os.path.exists(file_path):
            missing_files.append(file_path)
    
    # Check at least one climate source exists
    climate_sources = paths.get('climate_sources', {})
    if not climate_sources:
        missing_files.append("No climate sources defined in config")
    else:
        for source_name, source_info in climate_sources.items():
            if not os.path.exists(source_info.get('path', '')):
                missing_files.append(f"Climate source path: {source_info.get('path')}")
    
    return len(missing_files) == 0, missing_files

def create_required_directories(config: Dict[str, Any]) -> None:
    """
    Create required output directories if they don't exist.
    
    Args:
        config: Configuration dictionary
    """
    paths = config.get('paths', {})
    
    directories = [
        paths.get('simulation_setup_dir'),
        paths.get('simulation_output_dir'),
        paths.get('analysis_output_dir'),
        paths.get('figure_output_dir'),
        paths.get('models_dir'),
        'logs'
    ]
    
    for directory in directories:
        if directory:
            ensure_dir_exists(directory)
            logging.info(f"Created directory: {directory}")

def check_model_executables(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate crop model executables.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Tuple[bool, List[str]]: Success flag and list of issues
    """
    issues = []
    
    # Check each model that's configured to run
    for model in config.get('crop_models_to_run', []):
        # Get model interface
        interface = get_model_interface(model)
        if interface is None:
            issues.append(f"Could not initialize interface for {model}")
            continue
        
        # Get executable path from config
        exe_path = config.get('crop_model_configs', {}).get(model, {}).get('executable_path')
        if not exe_path:
            issues.append(f"No executable path configured for {model}")
            continue
        
        # Check executable
        if not interface.validate_executable(exe_path):
            issues.append(f"Invalid executable for {model}: {exe_path}")
    
    return len(issues) == 0, issues

def main(config_file: str) -> int:
    """
    Main function to validate environment setup.
    
    Args:
        config_file: Path to configuration YAML file
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        with Timer("Environment setup validation"):
            # Load and validate configuration
            config = load_config(config_file)
            logging.info("Configuration loaded successfully")
            
            # Check Python dependencies
            deps_ok, missing_deps = check_python_dependencies()
            if not deps_ok:
                logging.error(f"Missing Python packages: {missing_deps}")
                return 1
            logging.info("All required Python packages found")
            
            # Create required directories
            create_required_directories(config)
            logging.info("Required directories created/verified")
            
            # Validate input data
            data_ok, missing_files = validate_input_data(config)
            if not data_ok:
                logging.error(f"Missing required input files: {missing_files}")
                return 1
            logging.info("Required input data files found")
            
            # Check model executables
            exes_ok, exe_issues = check_model_executables(config)
            if not exes_ok:
                logging.error(f"Issues with model executables: {exe_issues}")
                return 1
            logging.info("Model executables validated")
            
            logging.info("Environment setup validation completed successfully")
            return 0
    
    except ConfigurationError as e:
        logging.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error during setup: {e}")
        return 1

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Validate environment and configuration setup"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to configuration YAML file"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level"
    )
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(
        log_file="logs/00_setup_environment.log",
        level=args.log_level
    )
    
    # Run main function
    exit_code = main(args.config)
    sys.exit(exit_code)
