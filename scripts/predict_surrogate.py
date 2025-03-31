#!/usr/bin/env python
##############################################################################
### File: scripts/predict_surrogate.py
##############################################################################
"""
Use trained surrogate model for rapid predictions and scenario exploration.
Generate predictions for new scenarios without running full crop models.
"""

import os
import sys
import logging
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Add parent directory to Python path
repo_root = str(Path(__file__).parent.parent)
sys.path.insert(0, repo_root)

from src.config_loader import load_config, ConfigurationError
from src.utils import setup_logging, ensure_dir_exists, Timer
from src.surrogate_model import SurrogateModel

def load_prediction_scenarios(scenario_file: str,
                            config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load scenarios for prediction from CSV file.
    
    Args:
        scenario_file: Path to CSV file with scenarios
        config: Configuration dictionary
    
    Returns:
        DataFrame with scenarios to predict
    """
    try:
        # Load scenarios
        scenarios = pd.read_csv(scenario_file)
        
        # Get required features from config
        features = config['surrogate_model']['features']
        
        # Check required columns exist
        missing = [f for f in features if f not in scenarios.columns]
        if missing:
            raise ValueError(f"Missing required features in scenarios: {missing}")
        
        # Validate data types and ranges if specified in config
        validation = config['surrogate_model'].get('validation', {})
        for feature, constraints in validation.items():
            if feature not in scenarios.columns:
                continue
                
            # Check data type
            if 'dtype' in constraints:
                try:
                    scenarios[feature] = scenarios[feature].astype(constraints['dtype'])
                except Exception as e:
                    raise ValueError(f"Invalid data type for {feature}: {e}")
            
            # Check value range
            if 'min' in constraints:
                if (scenarios[feature] < constraints['min']).any():
                    raise ValueError(f"{feature} contains values below minimum {constraints['min']}")
            
            if 'max' in constraints:
                if (scenarios[feature] > constraints['max']).any():
                    raise ValueError(f"{feature} contains values above maximum {constraints['max']}")
        
        return scenarios
    
    except Exception as e:
        logging.error(f"Error loading prediction scenarios: {e}")
        raise

def generate_predictions(model: SurrogateModel,
                       scenarios: pd.DataFrame,
                       config: Dict[str, Any]) -> pd.DataFrame:
    """
    Generate predictions for scenarios using surrogate model.
    
    Args:
        model: Trained surrogate model
        scenarios: DataFrame with scenarios to predict
        config: Configuration dictionary
    
    Returns:
        DataFrame with predictions
    """
    try:
        # Make predictions
        predictions = model.predict(scenarios)
        
        # Convert predictions to DataFrame
        pred_df = pd.DataFrame(predictions)
        
        # Add scenario features to output
        for col in scenarios.columns:
            pred_df[col] = scenarios[col]
        
        # Reorder columns: features first, then predictions
        feature_cols = scenarios.columns.tolist()
        target_cols = [c for c in pred_df.columns if c not in feature_cols]
        pred_df = pred_df[feature_cols + target_cols]
        
        return pred_df
    
    except Exception as e:
        logging.error(f"Error generating predictions: {e}")
        raise

def analyze_predictions(predictions: pd.DataFrame,
                      config: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """
    Generate summary statistics and analyses of predictions.
    
    Args:
        predictions: DataFrame with model predictions
        config: Configuration dictionary
    
    Returns:
        Dict with analysis DataFrames
    """
    try:
        analyses = {}
        targets = config['surrogate_model']['targets']
        
        # Calculate summary statistics
        summary = predictions[targets].describe()
        analyses['summary'] = summary
        
        # Calculate correlations between features and predictions
        features = config['surrogate_model']['features']
        corr = predictions[features + targets].corr()
        analyses['correlations'] = corr
        
        # Optional: Group by categorical features if specified
        groupby_cols = config['surrogate_model'].get('analysis_groupby', [])
        if groupby_cols:
            group_stats = predictions.groupby(groupby_cols)[targets].agg([
                'count', 'mean', 'std', 'min', 'max'
            ]).round(3)
            analyses['group_statistics'] = group_stats
        
        return analyses
    
    except Exception as e:
        logging.error(f"Error analyzing predictions: {e}")
        raise

def save_results(predictions: pd.DataFrame,
                analyses: Dict[str, pd.DataFrame],
                output_dir: Path) -> None:
    """
    Save prediction results and analyses.
    
    Args:
        predictions: DataFrame with predictions
        analyses: Dict with analysis DataFrames
        output_dir: Directory to save results
    """
    try:
        # Create output directory
        ensure_dir_exists(output_dir)
        
        # Save predictions
        predictions.to_csv(output_dir / 'surrogate_predictions.csv', index=False)
        
        # Save analyses
        for name, df in analyses.items():
            df.to_csv(output_dir / f'analysis_{name}.csv')
        
        logging.info(f"Results saved to {output_dir}")
        
        # Log summary statistics
        logging.info("\nPrediction Summary:")
        for target in analyses['summary'].columns:
            logging.info(f"\n{target}:")
            for stat, value in analyses['summary'][target].items():
                logging.info(f"  {stat}: {value:.3f}")
    
    except Exception as e:
        logging.error(f"Error saving results: {e}")
        raise

def main(config_file: str,
         scenario_file: str,
         output_dir: Optional[str] = None) -> int:
    """
    Main function to generate surrogate model predictions.
    
    Args:
        config_file: Path to configuration file
        scenario_file: Path to scenario CSV file
        output_dir: Optional custom output directory
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        with Timer("Surrogate model prediction"):
            # Load configuration
            config = load_config(config_file)
            
            # Load scenarios
            scenarios = load_prediction_scenarios(scenario_file, config)
            logging.info(f"Loaded {len(scenarios)} scenarios for prediction")
            
            # Load trained model
            model = SurrogateModel(
                config=config['surrogate_model'],
                model_dir=config['paths']['models_dir']
            )
            model.load()
            logging.info("Loaded trained surrogate model")
            
            # Generate predictions
            with Timer("Generating predictions"):
                predictions = generate_predictions(model, scenarios, config)
                logging.info(f"Generated predictions for {len(predictions)} scenarios")
            
            # Analyze predictions
            analyses = analyze_predictions(predictions, config)
            
            # Save results
            if output_dir is None:
                output_dir = Path(config['paths']['analysis_output_dir']) / 'surrogate_predictions'
            else:
                output_dir = Path(output_dir)
            
            save_results(predictions, analyses, output_dir)
            
            return 0
    
    except ConfigurationError as e:
        logging.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error during prediction: {e}")
        return 1

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Generate predictions using trained surrogate model"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to configuration YAML file"
    )
    parser.add_argument(
        "--scenarios",
        required=True,
        help="Path to scenario CSV file"
    )
    parser.add_argument(
        "--output-dir",
        help="Optional custom output directory"
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
        log_file="logs/predict_surrogate.log",
        level=args.log_level
    )
    
    # Run main function
    exit_code = main(
        config_file=args.config,
        scenario_file=args.scenarios,
        output_dir=args.output_dir
    )
    sys.exit(exit_code)
