#!/usr/bin/env python
##############################################################################
### File: scripts/07_generate_figures.py
##############################################################################
"""
Generate standardized figures from analysis results.
Creates maps, plots, and summary visualizations for reports/publications.
"""

import os
import sys
import logging
import argparse
import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Add parent directory to Python path
repo_root = str(Path(__file__).parent.parent)
sys.path.insert(0, repo_root)

from src.config_loader import load_config, ConfigurationError
from src.utils import setup_logging, ensure_dir_exists, Timer
from src.visualization import (
    setup_figure_style,
    plot_spatial_impacts,
    plot_impact_boxplots,
    plot_adaptation_effectiveness,
    plot_ensemble_agreement,
    plot_time_series
)

def load_analysis_results(config: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """
    Load all analysis results needed for plotting.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Dict with loaded DataFrames
    """
    try:
        analysis_dir = Path(config['paths']['analysis_output_dir'])
        results = {}
        
        # Load main impact results
        for period in config['climate']['future_periods'].keys():
            period_dir = analysis_dir / period
            if not period_dir.exists():
                continue
            
            # Load key result files
            for result_type in ['location_impacts', 'ensemble_stats']:
                file_path = period_dir / f"{result_type}.csv"
                if file_path.exists():
                    results[f"{period}_{result_type}"] = pd.read_csv(file_path)
        
        # Load adaptation results if available
        adaptation_dir = analysis_dir / 'adaptations'
        if adaptation_dir.exists():
            for file_name in ['adaptation_effectiveness_detailed.csv',
                            'adaptation_summary_ensemble.csv',
                            'adaptation_summary_ranking.csv']:
                file_path = adaptation_dir / file_name
                if file_path.exists():
                    key = file_name.replace('.csv', '')
                    results[key] = pd.read_csv(file_path)
        
        return results
    
    except Exception as e:
        logging.error(f"Error loading analysis results: {e}")
        raise

def load_spatial_data(config: Dict[str, Any]) -> Dict[str, gpd.GeoDataFrame]:
    """
    Load GIS data for spatial plotting.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Dict with GeoDataFrames
    """
    try:
        spatial_data = {}
        
        # Load simulation locations
        locations = pd.read_csv(config['paths']['locations_file'])
        # Convert to GeoDataFrame
        spatial_data['locations'] = gpd.GeoDataFrame(
            locations,
            geometry=gpd.points_from_xy(locations.lon, locations.lat),
            crs="EPSG:4326"
        )
        
        # Load district boundaries if available
        district_file = config['paths'].get('gis_districts')
        if district_file and os.path.exists(district_file):
            spatial_data['districts'] = gpd.read_file(district_file)
        
        # Load state boundary if available
        boundary_file = config['paths'].get('gis_karnataka_boundary')
        if boundary_file and os.path.exists(boundary_file):
            spatial_data['state_boundary'] = gpd.read_file(boundary_file)
        
        return spatial_data
    
    except Exception as e:
        logging.error(f"Error loading spatial data: {e}")
        raise

def generate_impact_figures(results: Dict[str, pd.DataFrame],
                          spatial_data: Dict[str, gpd.GeoDataFrame],
                          config: Dict[str, Any],
                          output_dir: Path) -> None:
    """
    Generate figures showing climate change impacts.
    
    Args:
        results: Dict with analysis results
        spatial_data: Dict with GIS data
        config: Configuration dictionary
        output_dir: Directory to save figures
    """
    try:
        # Create subdirectory for impact figures
        impacts_dir = output_dir / 'impacts'
        ensure_dir_exists(impacts_dir)
        
        # Get variables to plot
        impact_vars = config['analysis']['output_variables']
        
        # Process each future period
        for period in config['climate']['future_periods'].keys():
            period_dir = impacts_dir / period
            ensure_dir_exists(period_dir)
            
            # Get period results
            impacts = results.get(f"{period}_location_impacts")
            ensemble = results.get(f"{period}_ensemble_stats")
            
            if impacts is None or ensemble is None:
                logging.warning(f"Missing results for period {period}")
                continue
            
            # Generate spatial impact maps
            for var in impact_vars:
                # Plot absolute changes
                plot_spatial_impacts(
                    results=impacts,
                    shape_df=spatial_data['locations'],
                    variable=f"{var}_abs_change",
                    output_path=str(period_dir / f"{var}_absolute_change_map.png"),
                    title=f"Absolute Change in {var} ({period})"
                )
                
                # Plot relative changes
                plot_spatial_impacts(
                    results=impacts,
                    shape_df=spatial_data['locations'],
                    variable=f"{var}_rel_change",
                    output_path=str(period_dir / f"{var}_relative_change_map.png"),
                    title=f"Relative Change in {var} ({period})"
                )
            
            # Generate boxplots for each variable
            for var in impact_vars:
                plot_impact_boxplots(
                    data=impacts,
                    variable=f"{var}_rel_change",
                    groupby='climate_model',
                    output_path=str(period_dir / f"{var}_model_boxplots.png"),
                    title=f"{var} Changes by Model ({period})"
                )
            
            # Generate ensemble agreement plots
            for var in impact_vars:
                plot_ensemble_agreement(
                    data=ensemble,
                    variable=var,
                    shape_df=spatial_data['locations'],
                    output_path=str(period_dir / f"{var}_ensemble_agreement.png"),
                    title=f"Ensemble Agreement for {var} ({period})"
                )
    
    except Exception as e:
        logging.error(f"Error generating impact figures: {e}")
        raise

def generate_adaptation_figures(results: Dict[str, pd.DataFrame],
                             spatial_data: Dict[str, gpd.GeoDataFrame],
                             config: Dict[str, Any],
                             output_dir: Path) -> None:
    """
    Generate figures showing adaptation effectiveness.
    
    Args:
        results: Dict with analysis results
        spatial_data: Dict with GIS data
        config: Configuration dictionary
        output_dir: Directory to save figures
    """
    try:
        # Create subdirectory for adaptation figures
        adapt_dir = output_dir / 'adaptations'
        ensure_dir_exists(adapt_dir)
        
        # Get adaptation effectiveness results
        effectiveness = results.get('adaptation_effectiveness_detailed')
        if effectiveness is None:
            logging.warning("No adaptation effectiveness results available")
            return
        
        # Generate overall effectiveness plot
        plot_adaptation_effectiveness(
            data=effectiveness,
            output_path=str(adapt_dir / "adaptation_effectiveness_overall.png"),
            title="Overall Adaptation Effectiveness",
            error_bars=True,
            sort_by='mean_impact_reduction'
        )
        
        # Generate spatial effectiveness maps
        for adaptation in effectiveness['adaptation'].unique():
            adapt_data = effectiveness[effectiveness['adaptation'] == adaptation]
            
            plot_spatial_impacts(
                results=adapt_data,
                shape_df=spatial_data['locations'],
                variable='relative_effectiveness',
                output_path=str(adapt_dir / f"{adaptation}_spatial_effectiveness.png"),
                title=f"Spatial Effectiveness of {adaptation}"
            )
            
            # Generate boxplots by climate scenario
            plot_impact_boxplots(
                data=adapt_data,
                variable='relative_effectiveness',
                groupby='scenario',
                output_path=str(adapt_dir / f"{adaptation}_scenario_boxplots.png"),
                title=f"Effectiveness of {adaptation} by Scenario"
            )
    
    except Exception as e:
        logging.error(f"Error generating adaptation figures: {e}")
        raise

def main(config_file: str) -> int:
    """
    Main function to generate figures.
    
    Args:
        config_file: Path to configuration YAML file
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        with Timer("Figure generation"):
            # Load configuration
            config = load_config(config_file)
            
            # Set up figure style
            setup_figure_style()
            
            # Load analysis results
            results = load_analysis_results(config)
            if not results:
                raise ValueError("No analysis results available")
            
            # Load spatial data
            spatial_data = load_spatial_data(config)
            if not spatial_data:
                raise ValueError("No spatial data available")
            
            # Create figure output directory
            output_dir = Path(config['paths']['figure_output_dir'])
            ensure_dir_exists(output_dir)
            
            # Generate impact figures
            generate_impact_figures(results, spatial_data, config, output_dir)
            
            # Generate adaptation figures
            generate_adaptation_figures(results, spatial_data, config, output_dir)
            
            logging.info("Figure generation completed successfully")
            return 0
    
    except ConfigurationError as e:
        logging.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error during figure generation: {e}")
        return 1

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Generate standardized figures from analysis results"
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
        log_file="logs/07_generate_figures.log",
        level=args.log_level
    )
    
    # Run main function
    exit_code = main(args.config)
    sys.exit(exit_code)
