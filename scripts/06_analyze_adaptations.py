#!/usr/bin/env python
##############################################################################
### File: scripts/06_evaluate_adaptations.py
##############################################################################
"""
Evaluate effectiveness of adaptation strategies.
Analyzes adaptation outcomes across climate scenarios and locations.
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
    evaluate_adaptation_effectiveness,
    calculate_ensemble_statistics,
    aggregate_to_regions
)

def load_analysis_data(config: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """
    Load processed impact analysis results.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Dict with loaded DataFrames
    """
    try:
        analysis_dir = Path(config['paths']['analysis_output_dir'])
        data = {}
        
        # Load baseline statistics
        baseline_file = analysis_dir / 'baseline_statistics.csv'
        if baseline_file.exists():
            data['baseline'] = pd.read_csv(baseline_file)
        
        # Load period-specific results
        for period in config['climate']['future_periods'].keys():
            period_dir = analysis_dir / period
            if not period_dir.exists():
                continue
            
            # Load impact results
            impacts_file = period_dir / 'location_impacts.csv'
            if impacts_file.exists():
                data[f"{period}_impacts"] = pd.read_csv(impacts_file)
            
            # Load ensemble statistics
            ensemble_file = period_dir / 'ensemble_stats.csv'
            if ensemble_file.exists():
                data[f"{period}_ensemble"] = pd.read_csv(ensemble_file)
        
        return data
    
    except Exception as e:
        logging.error(f"Error loading analysis data: {e}")
        raise

def evaluate_adaptation_strategy(adaptation_name: str,
                              adaptation_results: pd.DataFrame,
                              baseline_impacts: pd.DataFrame,
                              config: Dict[str, Any]) -> pd.DataFrame:
    """
    Evaluate effectiveness of a single adaptation strategy.
    
    Args:
        adaptation_name: Name of adaptation strategy
        adaptation_results: DataFrame with adaptation simulation results
        baseline_impacts: DataFrame with baseline impact results
        config: Configuration dictionary
    
    Returns:
        DataFrame with adaptation effectiveness metrics
    """
    try:
        logging.info(f"Evaluating adaptation strategy: {adaptation_name}")
        
        # Get target variables from config
        target_vars = config['analysis']['output_variables']
        
        # Default grouping columns
        groupby_cols = ['location_id', 'climate_source', 'scenario', 'period']
        
        # Calculate effectiveness metrics
        effectiveness = evaluate_adaptation_effectiveness(
            adaptation_data=adaptation_results,
            baseline_impacts=baseline_impacts,
            target_vars=target_vars,
            adaptation_id_col='adaptation',
            groupby_cols=groupby_cols
        )
        
        # Add metadata
        effectiveness['adaptation'] = adaptation_name
        
        return effectiveness
    
    except Exception as e:
        logging.error(f"Error evaluating adaptation {adaptation_name}: {e}")
        raise

def summarize_adaptation_results(effectiveness_data: pd.DataFrame,
                               config: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """
    Generate summary statistics for adaptation effectiveness.
    
    Args:
        effectiveness_data: DataFrame with adaptation effectiveness metrics
        config: Configuration dictionary
    
    Returns:
        Dict with summary DataFrames
    """
    try:
        summaries = {}
        
        # Calculate ensemble statistics across climate models
        ensemble_stats = calculate_ensemble_statistics(
            data=effectiveness_data,
            groupby_cols=['adaptation', 'location_id'],
            value_cols=['mean_impact_reduction', 'relative_effectiveness'],
            model_col='climate_model',
            agreement_threshold=0.75
        )
        summaries['ensemble'] = ensemble_stats
        
        # Optional: Aggregate to regions if mapping available
        if 'region_mapping' in config['analysis']:
            region_stats = aggregate_to_regions(
                data=ensemble_stats,
                region_mapping=pd.read_csv(config['paths']['region_mapping']),
                value_cols=['mean_impact_reduction', 'relative_effectiveness']
            )
            summaries['regional'] = region_stats
        
        # Calculate overall effectiveness ranking
        ranking = effectiveness_data.groupby('adaptation').agg({
            'mean_impact_reduction': ['mean', 'std'],
            'relative_effectiveness': ['mean', 'std'],
            'significant': 'mean'  # Fraction of cases where adaptation was significant
        }).round(3)
        summaries['ranking'] = ranking
        
        return summaries
    
    except Exception as e:
        logging.error(f"Error summarizing adaptation results: {e}")
        raise

def main(config_file: str) -> int:
    """
    Main function to evaluate adaptation strategies.
    
    Args:
        config_file: Path to configuration YAML file
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        with Timer("Adaptation evaluation"):
            # Load configuration
            config = load_config(config_file)
            
            # Load analysis results
            analysis_data = load_analysis_data(config)
            if not analysis_data:
                raise ValueError("No analysis data available")
            
            # Process each adaptation strategy
            adaptation_results = []
            for adaptation in config['adaptations']:
                if adaptation['name'] == 'baseline':
                    continue  # Skip baseline case
                
                # Evaluate adaptation effectiveness
                effectiveness = evaluate_adaptation_strategy(
                    adaptation_name=adaptation['name'],
                    adaptation_results=analysis_data['adaptation_results'],
                    baseline_impacts=analysis_data['baseline_impacts'],
                    config=config
                )
                adaptation_results.append(effectiveness)
            
            if not adaptation_results:
                logging.warning("No adaptation results to process")
                return 0
            
            # Combine results
            combined_results = pd.concat(adaptation_results, ignore_index=True)
            
            # Generate summaries
            summaries = summarize_adaptation_results(combined_results, config)
            
            # Save results
            output_dir = Path(config['paths']['analysis_output_dir']) / 'adaptations'
            ensure_dir_exists(output_dir)
            
            # Save detailed results
            combined_results.to_csv(
                output_dir / 'adaptation_effectiveness_detailed.csv',
                index=False
            )
            
            # Save summaries
            for name, df in summaries.items():
                df.to_csv(output_dir / f"adaptation_summary_{name}.csv")
            
            logging.info("Adaptation evaluation completed successfully")
            return 0
    
    except ConfigurationError as e:
        logging.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error during adaptation evaluation: {e}")
        return 1

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Evaluate effectiveness of adaptation strategies"
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
        log_file="logs/06_evaluate_adaptations.log",
        level=args.log_level
    )
    
    # Run main function
    exit_code = main(args.config)
    sys.exit(exit_code)
