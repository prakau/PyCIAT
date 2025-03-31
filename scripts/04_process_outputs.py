#!/usr/bin/env python
##############################################################################
### File: scripts/04_process_outputs.py
##############################################################################
"""
Process crop model outputs into standardized format.
Parses model-specific output files and combines results into a standard dataset.
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
from src.utils import setup_logging, ensure_dir_exists, Timer
from src.crop_model_interface.status_codes import Status
from src import get_model_interface

def load_simulation_tracking(tracking_file: str) -> pd.DataFrame:
    """
    Load simulation tracking data and filter for completed simulations.
    
    Args:
        tracking_file: Path to tracking CSV file
    
    Returns:
        DataFrame with completed simulation info
    """
    try:
        tracking_df = pd.read_csv(tracking_file)
        
        # Filter for successfully completed simulations
        success_mask = tracking_df['status'].isin([
            Status.SUCCESS.name,  # Basic success
            'COMPLETE'  # Alternative success status that might be used
        ])
        success_sims = tracking_df[success_mask].copy()
        
        if success_sims.empty:
            logging.warning("No successfully completed simulations found")
        else:
            logging.info(f"Found {len(success_sims)} completed simulations to process")
        
        return success_sims
    
    except Exception as e:
        logging.error(f"Error loading tracking data: {e}")
        raise

def process_single_simulation(sim_info: pd.Series,
                            config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process outputs from a single simulation.
    
    Args:
        sim_info: Series with simulation parameters
        config: Configuration dictionary
    
    Returns:
        Optional[Dict]: Processed outputs or None if processing fails
    """
    try:
        # Get model interface
        model_interface = get_model_interface(sim_info['crop_model'])
        if model_interface is None:
            logging.error(f"Could not initialize interface for {sim_info['crop_model']}")
            return None
        
        # Get output directory
        sim_dir = Path(config['paths']['simulation_setup_dir']) / sim_info['simulation_id']
        if not sim_dir.exists():
            logging.error(f"Simulation directory not found: {sim_dir}")
            return None
        
        # Get output file configuration for this model
        output_files = config['crop_model_configs'][sim_info['crop_model']]['outputs']
        
        # Parse model outputs
        outputs = model_interface.parse_output(
            output_dir=str(sim_dir),
            output_files_config=output_files
        )
        
        if outputs is None:
            logging.error(f"Failed to parse outputs for {sim_info['simulation_id']}")
            return None
        
        # Add simulation metadata
        metadata = {
            'simulation_id': sim_info['simulation_id'],
            'location_id': sim_info['location_id'],
            'crop_model': sim_info['crop_model'],
            'climate_source': sim_info['climate_source'],
            'climate_model': sim_info['climate_model'],
            'scenario': sim_info['scenario'],
            'sowing_date': sim_info['sowing_date'],
            'soil_id': sim_info['soil_id']
        }
        
        return {**metadata, **outputs}
    
    except Exception as e:
        logging.error(f"Error processing simulation {sim_info['simulation_id']}: {e}")
        return None

def standardize_variables(results_df: pd.DataFrame,
                        config: Dict[str, Any]) -> pd.DataFrame:
    """
    Map model-specific variable names to standard names.
    
    Args:
        results_df: DataFrame with model outputs
        config: Configuration dictionary
    
    Returns:
        DataFrame with standardized variable names
    """
    try:
        # Create copy to avoid modifying input
        std_df = results_df.copy()
        
        # Get variable mapping for each model
        var_mappings = config['analysis']['variable_mapping']
        
        # Process each model's outputs
        for model in results_df['crop_model'].unique():
            model_mask = results_df['crop_model'] == model
            mapping = var_mappings.get(model, {})
            
            if not mapping:
                logging.warning(f"No variable mapping found for {model}")
                continue
            
            # Rename columns according to mapping
            for std_name, model_name in mapping.items():
                if model_name in results_df.columns:
                    std_df.loc[model_mask, std_name] = results_df.loc[model_mask, model_name]
        
        # Verify all standard variables are present
        required_vars = config['analysis']['output_variables']
        missing = [var for var in required_vars if var not in std_df.columns]
        if missing:
            logging.warning(f"Missing standard variables: {missing}")
        
        return std_df
    
    except Exception as e:
        logging.error(f"Error standardizing variables: {e}")
        raise

def main(config_file: str) -> int:
    """
    Main function to process simulation outputs.
    
    Args:
        config_file: Path to configuration YAML file
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        with Timer("Processing simulation outputs"):
            # Load configuration
            config = load_config(config_file)
            
            # Load tracking data
            tracking_df = load_simulation_tracking(config['paths']['simulation_status_file'])
            if tracking_df.empty:
                return 0  # No simulations to process
            
            # Process each simulation
            results = []
            for _, sim_info in tracking_df.iterrows():
                with Timer(f"Processing {sim_info['simulation_id']}"):
                    sim_results = process_single_simulation(sim_info, config)
                    if sim_results:
                        results.append(sim_results)
            
            if not results:
                logging.error("No simulation outputs were successfully processed")
                return 1
            
            # Combine results
            combined_df = pd.DataFrame(results)
            
            # Standardize variable names
            std_df = standardize_variables(combined_df, config)
            
            # Save processed results
            output_dir = Path(config['paths']['analysis_output_dir'])
            ensure_dir_exists(output_dir)
            
            output_file = output_dir / "combined_results_std_vars.parquet"
            std_df.to_parquet(
                output_file,
                compression=config['analysis'].get('output_compression', 'snappy')
            )
            logging.info(f"Saved standardized results to {output_file}")
            
            # Update tracking file with processing status
            tracking_df = pd.read_csv(config['paths']['simulation_status_file'])
            for sim_id in std_df['simulation_id']:
                mask = tracking_df['simulation_id'] == sim_id
                tracking_df.loc[mask, 'status'] = Status.OUTPUT_PARSED.name
            
            tracking_df.to_csv(config['paths']['simulation_status_file'], index=False)
            
            # Log summary
            logging.info(f"Processed outputs from {len(results)} simulations")
            return 0
    
    except ConfigurationError as e:
        logging.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error during output processing: {e}")
        return 1

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Process and standardize crop model outputs"
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
        log_file="logs/04_process_outputs.log",
        level=args.log_level
    )
    
    # Run main function
    exit_code = main(args.config)
    sys.exit(exit_code)
