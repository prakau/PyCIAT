#!/usr/bin/env python
##############################################################################
### File: scripts/train_surrogate.py
##############################################################################
"""
Train and validate surrogate models using simulation results.
Optional script to build machine learning models for rapid scenario exploration.
"""

import os
import sys
import logging
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error

# Add parent directory to Python path
repo_root = str(Path(__file__).parent.parent)
sys.path.insert(0, repo_root)

from src.config_loader import load_config, ConfigurationError
from src.utils import setup_logging, ensure_dir_exists, Timer
from src.surrogate_model import SurrogateModel

def load_training_data(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load and prepare data for surrogate model training.
    
    Args:
        config: Configuration dictionary
    
    Returns:
        DataFrame with features and targets
    """
    try:
        # Load processed simulation results
        results_file = Path(config['paths']['analysis_output_dir']) / 'combined_results_std_vars.parquet'
        if not results_file.exists():
            raise FileNotFoundError(f"Results file not found: {results_file}")
        
        data = pd.read_parquet(results_file)
        
        # Get feature and target variables from config
        surrogate_config = config.get('surrogate_model', {})
        features = surrogate_config.get('features', [])
        targets = surrogate_config.get('targets', [])
        
        if not features or not targets:
            raise ConfigurationError("Features and targets must be specified in config")
        
        # Verify all required columns exist
        missing_features = [f for f in features if f not in data.columns]
        missing_targets = [t for t in targets if t not in data.columns]
        
        if missing_features or missing_targets:
            raise ValueError(
                f"Missing columns in data:\n"
                f"Features: {missing_features}\n"
                f"Targets: {missing_targets}"
            )
        
        # Select required columns
        training_data = data[features + targets].copy()
        
        # Check for missing values
        if training_data.isna().any().any():
            logging.warning("Data contains missing values - will be handled in preprocessing")
        
        return training_data
    
    except Exception as e:
        logging.error(f"Error loading training data: {e}")
        raise

def evaluate_surrogate(model: SurrogateModel,
                      test_data: pd.DataFrame,
                      config: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Evaluate surrogate model performance on test data.
    
    Args:
        model: Trained surrogate model
        test_data: Test dataset
        config: Configuration dictionary
    
    Returns:
        Dict of metrics for each target variable
    """
    try:
        # Get target variables
        targets = config['surrogate_model']['targets']
        
        # Make predictions
        predictions = model.predict(test_data)
        
        # Calculate metrics for each target
        metrics = {}
        for target in targets:
            target_metrics = {}
            
            # Calculate R2 score
            target_metrics['r2'] = r2_score(
                test_data[target],
                predictions[target]
            )
            
            # Calculate RMSE
            target_metrics['rmse'] = np.sqrt(mean_squared_error(
                test_data[target],
                predictions[target]
            ))
            
            # Calculate bias
            target_metrics['bias'] = np.mean(
                predictions[target] - test_data[target]
            )
            
            metrics[target] = target_metrics
        
        return metrics
    
    except Exception as e:
        logging.error(f"Error evaluating surrogate model: {e}")
        raise

def save_evaluation_results(metrics: Dict[str, Dict[str, float]],
                          output_dir: Path) -> None:
    """
    Save model evaluation results.
    
    Args:
        metrics: Dictionary of metrics by target
        output_dir: Directory to save results
    """
    try:
        # Convert metrics to DataFrame
        results = []
        for target, target_metrics in metrics.items():
            row = {'target': target}
            row.update(target_metrics)
            results.append(row)
        
        df = pd.DataFrame(results)
        
        # Save to CSV
        output_file = output_dir / 'surrogate_evaluation.csv'
        df.to_csv(output_file, index=False)
        logging.info(f"Saved evaluation results to {output_file}")
        
        # Log summary
        logging.info("\nModel Performance Summary:")
        for _, row in df.iterrows():
            logging.info(f"\nTarget: {row['target']}")
            logging.info(f"  R2 Score: {row['r2']:.3f}")
            logging.info(f"  RMSE: {row['rmse']:.3f}")
            logging.info(f"  Bias: {row['bias']:.3f}")
    
    except Exception as e:
        logging.error(f"Error saving evaluation results: {e}")
        raise

def main(config_file: str,
         test_size: float = 0.2,
         random_seed: int = 42) -> int:
    """
    Main function to train and evaluate surrogate models.
    
    Args:
        config_file: Path to configuration file
        test_size: Fraction of data to use for testing
        random_seed: Random seed for reproducibility
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        with Timer("Surrogate model training and evaluation"):
            # Load configuration
            config = load_config(config_file)
            
            # Load training data
            data = load_training_data(config)
            logging.info(f"Loaded {len(data)} samples for training")
            
            # Split features and targets
            features = config['surrogate_model']['features']
            targets = config['surrogate_model']['targets']
            
            # Split training and test data
            train_data, test_data = train_test_split(
                data,
                test_size=test_size,
                random_state=random_seed
            )
            
            logging.info(f"Training set: {len(train_data)} samples")
            logging.info(f"Test set: {len(test_data)} samples")
            
            # Initialize surrogate model
            model = SurrogateModel(
                config=config['surrogate_model'],
                model_dir=config['paths']['models_dir']
            )
            
            # Train model
            with Timer("Model training"):
                metrics = model.train(
                    training_data=train_data,
                    validation_frac=0.2,
                    random_seed=random_seed
                )
                logging.info("Training completed successfully")
            
            # Save trained model
            model.save()
            logging.info("Model saved successfully")
            
            # Evaluate on test set
            test_metrics = evaluate_surrogate(model, test_data, config)
            
            # Save evaluation results
            output_dir = Path(config['paths']['models_dir'])
            save_evaluation_results(test_metrics, output_dir)
            
            return 0
    
    except ConfigurationError as e:
        logging.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error during surrogate model training: {e}")
        return 1

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Train and evaluate surrogate models"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to configuration YAML file"
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of data to use for testing"
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
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
        log_file="logs/train_surrogate.log",
        level=args.log_level
    )
    
    # Run main function
    exit_code = main(
        config_file=args.config,
        test_size=args.test_size,
        random_seed=args.random_seed
    )
    sys.exit(exit_code)
