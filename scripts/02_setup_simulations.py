#!/usr/bin/env python
##############################################################################
### File: scripts/02_setup_simulations.py
##############################################################################
"""
Generate simulation input files and create simulation tracking database.
Sets up required files for each model, location, and scenario combination.
"""

import os
import sys
import logging
import argparse
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from itertools import product

# Add parent directory to Python path
repo_root = str(Path(__file__).parent.parent)
sys.path.insert(0, repo_root)

from src.config_loader import load_config, ConfigurationError
from src.utils import setup_logging, ensure_dir_exists, Timer
from src.crop_model_interface.status_codes import Status
from src import get_model_interface

def load_climate_point_data(climate_dir: str,
                          location_id: str,
                          model: str,
                          scenario: str) -> Optional[pd.DataFrame]:
    """
    Load processed climate data for a specific location and scenario.
    
    Args:
        climate_dir: Directory containing processed climate files
        location_id: Location identifier
        model: Climate model name
        scenario: Scenario name
    
    Returns:
        Optional[pd.DataFrame]: Climate data or None if file not found
    """
    try:
        filename = f"{location_id}_{model}_{scenario}_climate.csv"
        filepath = Path(climate_dir) / filename
        
        if not filepath.exists():
            logging.error(f"Climate file not found: {filepath}")
            return None
        
        return pd.read_csv(filepath, parse_dates=['time'])
    
    except Exception as e:
        logging.error(f"Error loading climate data for {location_id}: {e}")
        return None

def load_soil_data(soil_file: str,
                  soil_id: str) -> Optional[Dict[str, Any]]:
    """
    Load soil profile data for a specific soil.
    
    Args:
        soil_file: Path to soil data file
        soil_id: Soil identifier
    
    Returns:
        Optional[Dict]: Soil profile data or None if not found
    """
    try:
        # Implementation depends on soil data format
        # This is a placeholder that would need to be implemented
        logging.warning("soil data loading not implemented - using dummy data")
        return {
            'soil_id': soil_id,
            'layers': [
                {'depth': 20, 'sand': 40, 'clay': 30},
                {'depth': 40, 'sand': 42, 'clay': 32}
            ]
        }
    
    except Exception as e:
        logging.error(f"Error loading soil data for {soil_id}: {e}")
        return None

def generate_simulation_matrix(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Generate matrix of all simulation combinations to run.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        DataFrame with all simulation combinations
    """
    try:
        # Load locations
        locations = pd.read_csv(config['paths']['locations_file'])
        
        # Get simulation parameters
        climate_config = config['climate']
        sim_config = config['simulation']
        
        # Create all combinations
        combinations = list(product(
            locations['location_id'],
            config['crop_models_to_run'],
            climate_config['active_sources'],
            climate_config['models_to_run'],
            climate_config['scenarios_to_run'],
            sim_config['sowing_dates']
        ))
        
        # Create DataFrame
        matrix = pd.DataFrame(combinations, columns=[
            'location_id',
            'crop_model',
            'climate_source',
            'climate_model',
            'scenario',
            'sowing_date'
        ])
        
        # Add soil IDs from locations
        matrix = matrix.merge(
            locations[['location_id', 'soil_id']],
            on='location_id'
        )
        
        # Generate unique simulation IDs
        matrix['simulation_id'] = matrix.apply(
            lambda row: f"{row['location_id']}_{row['crop_model']}_{row['climate_model']}_"
                       f"{row['scenario']}_{row['sowing_date'].replace('-', '')}",
            axis=1
        )
        
        return matrix
    
    except Exception as e:
        logging.error(f"Error generating simulation matrix: {e}")
        raise

def setup_single_simulation(sim_info: pd.Series,
                          config: Dict[str, Any],
                          base_dir: str) -> Tuple[Status, str]:
    """
    Set up input files for a single simulation.
    
    Args:
        sim_info: Series with simulation parameters
        config: Configuration dictionary
        base_dir: Base directory for simulation files
    
    Returns:
        Tuple[Status, str]: Status code and message
    """
    try:
        # Get model interface
        model_interface = get_model_interface(sim_info['crop_model'])
        if model_interface is None:
            return Status.SETUP_ERROR, f"Could not initialize interface for {sim_info['crop_model']}"
        
        # Create simulation directory
        sim_dir = Path(base_dir) / sim_info['simulation_id']
        ensure_dir_exists(sim_dir)
        
        # Load climate data
        climate_dir = Path(config['paths']['simulation_setup_dir']) / "_climate_point_data"
        climate_data = load_climate_point_data(
            climate_dir=climate_dir,
            location_id=sim_info['location_id'],
            model=sim_info['climate_model'],
            scenario=sim_info['scenario']
        )
        if climate_data is None:
            return Status.SETUP_ERROR, "Failed to load climate data"
        
        # Load soil data
        soil_data = load_soil_data(
            soil_file=config['paths']['soil_profiles'],
            soil_id=sim_info['soil_id']
        )
        if soil_data is None:
            return Status.SETUP_ERROR, "Failed to load soil data"
        
        # Generate weather file
        weather_success = model_interface.generate_weather(
            climate_data=climate_data,
            site_info={'lat': sim_info['lat'], 'lon': sim_info['lon']},
            output_path=str(sim_dir / "weather.txt")  # Filename depends on model
        )
        if not weather_success:
            return Status.SETUP_ERROR, "Failed to generate weather file"
        
        # Generate soil file
        soil_success = model_interface.generate_soil(
            soil_profile=soil_data,
            output_path=str(sim_dir / "soil.txt")  # Filename depends on model
        )
        if not soil_success:
            return Status.SETUP_ERROR, "Failed to generate soil file"
        
        # Generate experiment file
        exp_success = model_interface.generate_experiment(
            exp_details={
                'sowing_date': sim_info['sowing_date'],
                'simulation_id': sim_info['simulation_id'],
                **config['simulation']  # Include other simulation parameters
            },
            output_path=str(sim_dir / "experiment.txt"),  # Filename depends on model
            template_path=config['crop_model_configs'][sim_info['crop_model']].get('simulation_template'),
            config=config
        )
        if not exp_success:
            return Status.SETUP_ERROR, "Failed to generate experiment file"
        
        return Status.READY_TO_RUN, "Setup completed successfully"
    
    except Exception as e:
        logging.error(f"Error in setup_single_simulation: {e}")
        return Status.SETUP_ERROR, str(e)

def main(config_file: str) -> int:
    """
    Main function to set up simulation files.
    
    Args:
        config_file: Path to configuration YAML file
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        with Timer("Simulation setup"):
            # Load configuration
            config = load_config(config_file)
            
            # Generate simulation matrix
            sim_matrix = generate_simulation_matrix(config)
            logging.info(f"Generated {len(sim_matrix)} simulation combinations")
            
            # Create simulation tracking DataFrame
            tracking_df = sim_matrix.copy()
            tracking_df['status'] = Status.PENDING.name
            tracking_df['message'] = ""
            tracking_df['setup_time'] = pd.NaT
            tracking_df['run_time'] = pd.NaT
            
            # Create base simulation directory
            setup_dir = Path(config['paths']['simulation_setup_dir'])
            ensure_dir_exists(setup_dir)
            
            # Set up each simulation
            for idx, sim_info in sim_matrix.iterrows():
                with Timer(f"Setting up simulation {sim_info['simulation_id']}") as timer:
                    status, message = setup_single_simulation(
                        sim_info=sim_info,
                        config=config,
                        base_dir=setup_dir
                    )
                    
                    # Update tracking information
                    tracking_df.loc[idx, 'status'] = status.name
                    tracking_df.loc[idx, 'message'] = message
                    tracking_df.loc[idx, 'setup_time'] = timer.duration
            
            # Save tracking DataFrame
            tracking_file = Path(config['paths']['simulation_status_file'])
            ensure_dir_exists(tracking_file.parent)
            tracking_df.to_csv(tracking_file, index=False)
            
            # Log summary
            setup_count = sum(tracking_df['status'] == Status.READY_TO_RUN.name)
            error_count = sum(tracking_df['status'] == Status.SETUP_ERROR.name)
            logging.info(f"Setup complete: {setup_count} ready, {error_count} errors")
            
            return 0 if error_count == 0 else 1
    
    except ConfigurationError as e:
        logging.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error during simulation setup: {e}")
        return 1

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Set up simulation input files and tracking database"
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
        log_file="logs/02_setup_simulations.log",
        level=args.log_level
    )
    
    # Run main function
    exit_code = main(args.config)
    sys.exit(exit_code)
