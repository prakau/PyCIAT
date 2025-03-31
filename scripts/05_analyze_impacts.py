#!/usr/bin/env python
##############################################################################
### File: scripts/05_analyze_impacts.py
##############################################################################
"""
Analyze climate change impacts from simulation results.
Calculates impacts relative to baseline period and generates ensemble statistics.
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
from src.analysis import (
    calculate_baseline_statistics,
    calculate_climate_impacts,
    calculate_ensemble_statistics,
    aggregate_to_regions
)

def load_simulation_results(results_file: str) -> pd.DataFrame:
    """
    Load processed simulation results.
    
    Args:
        results_file: Path to combined results file
    
    Returns:
        DataFrame with simulation results
    """
    try:
        # Load parquet file with processed results
        results = pd.read_parquet(results_file)
        
        if results.empty:
            raise ValueError("Results file is empty")
        
        # Verify required columns exist
        required_cols = [
            'simulation_id', 'location_id', 'crop_model',
            'climate_source', 'climate_model', 'scenario'
        ]
        missing = [col for col in required_cols if col not in results.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        return results
    
    except Exception as e:
        logging.error(f"Error loading simulation results: {e}")
        raise

def filter_analysis_period(data: pd.DataFrame,
                         period: str,
                         config: Dict[str, Any]) -> pd.DataFrame:
    """
    Filter results for specific analysis period.
    
    Args:
        data: DataFrame with simulation results
        period: Period identifier ('historical' or future period name)
        config: Configuration dictionary
    
    Returns:
        DataFrame filtered for specified period
    """
    try:
        # Get date range for period
        if period == 'historical':
            date_range = config['climate']['historical_period']
        else:
            date_range = config['climate']['future_periods'][period]
        
        # Implementation would need to handle how periods are encoded in results
        # This is a placeholder assuming results have period markers
        period_data = data[data['period'] == period].copy()
        
        if period_data.empty:
            logging.warning(f"No data found for period {period}")
        
        return period_data
    
    except Exception as e:
        logging.error(f"Error filtering period {period}: {e}")
        raise

def calculate_period_impacts(baseline_data: pd.DataFrame,
                           future_data: pd.DataFrame,
                           config: Dict[str, Any],
                           future_period: str) -> Dict[str, pd.DataFrame]:
    """
    Calculate impacts for a specific future period.
    
    Args:
        baseline_data: DataFrame with baseline results
        future_data: DataFrame with future period results
        config: Configuration dictionary
        future_period: Name of future period
    
    Returns:
        Dict with various impact metrics DataFrames
    """
    try:
        analysis_config = config['analysis']
        groupby_cols = ['location_id', 'climate_source', 'climate_model']
        impact_vars = analysis_config['output_variables']
        
        # Calculate baseline statistics
        baseline_stats = calculate_baseline_statistics(
            data=baseline_data,
            groupby_cols=groupby_cols,
            value_cols=impact_vars
        )
        
        # Calculate impacts relative to baseline
        impacts = calculate_climate_impacts(
            future_data=future_data,
            baseline_data=baseline_data,
            impact_vars=impact_vars,
            groupby_cols=groupby_cols
        )
        
        # Calculate ensemble statistics
        ensemble_stats = calculate_ensemble_statistics(
            data=impacts,
            groupby_cols=['location_id'],
            value_cols=[f"{var}_rel_change" for var in impact_vars],
            model_col='climate_model',
            agreement_threshold=0.75
        )
        
        # Optional: Aggregate to regions if mapping provided
        if 'region_mapping' in analysis_config:
            region_impacts = aggregate_to_regions(
                data=ensemble_stats,
                region_mapping=pd.read_csv(config['paths']['region_mapping']),
                value_cols=[f"{var}_rel_change" for var in impact_vars]
            )
        else:
            region_impacts = pd.DataFrame()
        
        return {
            'baseline_stats': baseline_stats,
            'location_impacts': impacts,
            'ensemble_stats': ensemble_stats,
            'region_impacts': region_impacts
        }
    
    except Exception as e:
        logging.error(f"Error calculating impacts for {future_period}: {e}")
        raise

def main(config_file: str) -> int:
    """
    Main function to analyze climate change impacts.
    
    Args:
        config_file: Path to configuration YAML file
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        with Timer("Impact analysis"):
            # Load configuration
            config = load_config(config_file)
            
            # Load processed results
            results = load_simulation_results(
                os.path.join(
                    config['paths']['analysis_output_dir'],
                    'combined_results_std_vars.parquet'
                )
            )
            
            # Get baseline data
            baseline_data = filter_analysis_period(
                results,
                config['analysis']['baseline_period_name'],
                config
            )
            
            if baseline_data.empty:
                raise ValueError("No baseline data available for analysis")
            
            # Process each future period
            period_results = {}
            for period in config['climate']['future_periods'].keys():
                logging.info(f"Analyzing period: {period}")
                
                # Get future period data
                future_data = filter_analysis_period(results, period, config)
                if future_data.empty:
                    logging.warning(f"No data available for period {period}")
                    continue
                
                # Calculate impacts
                period_results[period] = calculate_period_impacts(
                    baseline_data=baseline_data,
                    future_data=future_data,
                    config=config,
                    future_period=period
                )
            
            # Save results
            output_dir = Path(config['paths']['analysis_output_dir'])
            ensure_dir_exists(output_dir)
            
            # Save baseline statistics
            baseline_stats = period_results[next(iter(period_results))]['baseline_stats']
            baseline_stats.to_csv(output_dir / 'baseline_statistics.csv', index=False)
            
            # Save impact results for each period
            for period, results_dict in period_results.items():
                period_dir = output_dir / period
                ensure_dir_exists(period_dir)
                
                for result_type, df in results_dict.items():
                    if not df.empty:
                        df.to_csv(period_dir / f"{result_type}.csv", index=False)
            
            logging.info("Impact analysis completed successfully")
            return 0
    
    except ConfigurationError as e:
        logging.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error during impact analysis: {e}")
        return 1

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Analyze climate change impacts from simulation results"
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
        log_file="logs/05_analyze_impacts.log",
        level=args.log_level
    )
    
    # Run main function
    exit_code = main(args.config)
    sys.exit(exit_code)
