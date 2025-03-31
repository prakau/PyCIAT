#!/usr/bin/env python
##############################################################################
### File: scripts/01_prepare_climate_data.py
##############################################################################
"""
Process climate data from GCM/RCM sources and extract point data for locations.
"""

import os
import sys
import logging
import argparse
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Add parent directory to Python path
repo_root = str(Path(__file__).parent.parent)
sys.path.insert(0, repo_root)

from src.config_loader import load_config, ConfigurationError
from src.utils import setup_logging, ensure_dir_exists, Timer, parse_date_string
from src.climate_processing import (
    load_climate_data,
    extract_point_data,
    process_point_climate,
    validate_climate_data
)

def load_locations(locations_file: str) -> pd.DataFrame:
    """
    Load simulation locations from CSV file.
    
    Args:
        locations_file: Path to CSV file with location information
    
    Returns:
        DataFrame with location data
    """
    try:
        locations = pd.read_csv(locations_file)
        required_cols = ['location_id', 'lat', 'lon']
        
        missing = [col for col in required_cols if col not in locations.columns]
        if missing:
            raise ValueError(f"Missing required columns in locations file: {missing}")
        
        return locations
    
    except Exception as e:
        logging.error(f"Error loading locations file: {e}")
        raise

def process_climate_source(source_info: Dict[str, Any],
                         models: List[str],
                         scenarios: List[str],
                         locations: pd.DataFrame,
                         config: Dict[str, Any],
                         output_dir: str) -> None:
    """
    Process climate data for a single source (GCM/RCM).
    
    Args:
        source_info: Dictionary with source configuration
        models: List of models to process
        scenarios: List of scenarios to process
        locations: DataFrame with simulation locations
        config: Full configuration dictionary
        output_dir: Directory to save processed data
    """
    source_type = source_info.get('type', 'Unknown')
    source_path = source_info.get('path')
    logging.info(f"Processing {source_type} source from {source_path}")
    
    # Get spatial and temporal settings
    climate_config = config['climate']
    lat_range = climate_config['lat_range']
    lon_range = climate_config['lon_range']
    variables = climate_config['variables']
    use_dask = climate_config.get('use_dask', False)
    
    # Process each model
    for model in models:
        logging.info(f"Processing model: {model}")
        
        # Process each scenario
        for scenario in scenarios:
            logging.info(f"Processing scenario: {scenario}")
            
            # Set time ranges based on scenario
            if scenario == 'historical':
                time_range = climate_config['historical_period']
            else:
                # Get appropriate future period
                for period, dates in climate_config['future_periods'].items():
                    # Logic to match scenario with appropriate period
                    # This is a placeholder - implement based on your needs
                    time_range = dates
                    break
            
            try:
                # Load gridded data
                dataset = load_climate_data(
                    source_path=source_path,
                    model=model,
                    scenario=scenario,
                    variables=variables,
                    lat_range=lat_range,
                    lon_range=lon_range,
                    time_range=time_range,
                    use_dask=use_dask
                )
                
                if dataset is None:
                    logging.error(f"Failed to load data for {model} {scenario}")
                    continue
                
                # Extract and process point data for each location
                for _, location in locations.iterrows():
                    loc_id = location['location_id']
                    lat = location['lat']
                    lon = location['lon']
                    
                    # Extract point data
                    point_data = extract_point_data(
                        dataset=dataset,
                        lat=lat,
                        lon=lon
                    )
                    
                    if point_data.empty:
                        logging.error(f"Failed to extract data for location {loc_id}")
                        continue
                    
                    # Process extracted data
                    processed_data = process_point_climate(
                        df=point_data,
                        output_vars=source_info.get('variable_mapping', {})
                    )
                    
                    # Validate processed data
                    valid, issues = validate_climate_data(
                        processed_data,
                        variables,
                        source_info.get('validation_checks', {})
                    )
                    
                    if not valid:
                        logging.error(f"Data validation failed for {loc_id}: {issues}")
                        continue
                    
                    # Save processed data
                    output_file = Path(output_dir) / f"{loc_id}_{model}_{scenario}_climate.csv"
                    processed_data.to_csv(output_file)
                    logging.info(f"Saved processed data to {output_file}")
            
            except Exception as e:
                logging.error(f"Error processing {model} {scenario}: {e}")
                continue

def main(config_file: str,
         sources: Optional[List[str]] = None,
         models: Optional[List[str]] = None,
         scenarios: Optional[List[str]] = None) -> int:
    """
    Main function to prepare climate data.
    
    Args:
        config_file: Path to configuration YAML file
        sources: Optional list of sources to process (defaults to all active)
        models: Optional list of models to process (defaults to all configured)
        scenarios: Optional list of scenarios to process (defaults to all configured)
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        with Timer("Climate data preparation"):
            # Load configuration
            config = load_config(config_file)
            
            # Get climate configuration
            climate_config = config['climate']
            
            # Filter sources if specified
            active_sources = sources or climate_config['active_sources']
            process_models = models or climate_config['models_to_run']
            process_scenarios = scenarios or climate_config['scenarios_to_run']
            
            # Load locations
            locations = load_locations(config['paths']['locations_file'])
            logging.info(f"Loaded {len(locations)} simulation locations")
            
            # Create output directory
            output_dir = Path(config['paths']['simulation_setup_dir']) / "_climate_point_data"
            ensure_dir_exists(output_dir)
            
            # Process each active source
            for source_name in active_sources:
                source_info = config['paths']['climate_sources'].get(source_name)
                if not source_info:
                    logging.error(f"Source {source_name} not found in configuration")
                    continue
                
                process_climate_source(
                    source_info=source_info,
                    models=process_models,
                    scenarios=process_scenarios,
                    locations=locations,
                    config=config,
                    output_dir=output_dir
                )
            
            logging.info("Climate data preparation completed successfully")
            return 0
    
    except ConfigurationError as e:
        logging.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error during climate data preparation: {e}")
        return 1

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Process climate data and extract for simulation locations"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to configuration YAML file"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        help="Optional: List of sources to process"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        help="Optional: List of models to process"
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        help="Optional: List of scenarios to process"
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
        log_file="logs/01_prepare_climate_data.log",
        level=args.log_level
    )
    
    # Run main function
    exit_code = main(
        config_file=args.config,
        sources=args.sources,
        models=args.models,
        scenarios=args.scenarios
    )
    sys.exit(exit_code)
