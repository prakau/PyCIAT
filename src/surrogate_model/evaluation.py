"""
Functions for evaluating surrogate model performance in PyCIAT.
"""

import logging
from typing import Dict, Any, Optional, List, Union

import pandas as pd
import numpy as np
# Import necessary evaluation metrics
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
# Import plotting libraries if generating plots here
# import matplotlib.pyplot as plt
# import seaborn as sns

logger = logging.getLogger(__name__)

def evaluate_surrogate(
    y_true: Union[pd.DataFrame, pd.Series],
    y_pred: Union[np.ndarray, pd.DataFrame, pd.Series],
    target_names: List[str] # List of target variable names
    ) -> Optional[Dict[str, Dict[str, float]]]:
    """
    Evaluates surrogate model predictions against true values.

    Calculates common regression metrics (RMSE, MAE, R^2) for each target variable.

    Args:
        y_true: True target values (DataFrame or Series).
        y_pred: Predicted target values (Numpy array, DataFrame, or Series).
                Should have the same shape/columns as y_true.
        target_names: List of names corresponding to the target columns/outputs.

    Returns:
        A dictionary where keys are target variable names and values are
        dictionaries of performance metrics (e.g., {'RMSE': value, 'R2': value}),
        or None on failure.
    """
    logger.info("Evaluating surrogate model performance...")

    # Input validation
    if isinstance(y_true, pd.Series):
        y_true = y_true.to_frame(name=target_names[0])
    if isinstance(y_pred, pd.Series):
         y_pred = y_pred.to_frame(name=target_names[0])
    if isinstance(y_pred, np.ndarray):
        if y_pred.ndim == 1:
            y_pred = pd.DataFrame(y_pred, index=y_true.index, columns=[target_names[0]])
        elif y_pred.ndim == 2 and y_pred.shape[1] == len(target_names):
            y_pred = pd.DataFrame(y_pred, index=y_true.index, columns=target_names)
        else:
            logger.error(f"Shape mismatch for y_pred numpy array ({y_pred.shape}) and target names ({len(target_names)}).")
            return None

    if not isinstance(y_true, pd.DataFrame) or not isinstance(y_pred, pd.DataFrame):
        logger.error("y_true and y_pred must be convertible to pandas DataFrames.")
        return None
    if y_true.shape != y_pred.shape:
        logger.error(f"Shape mismatch between y_true ({y_true.shape}) and y_pred ({y_pred.shape}).")
        return None
    if not all(col in y_pred.columns for col in target_names) or not all(col in y_true.columns for col in target_names):
         logger.error(f"Predicted or true values missing columns for specified targets: {target_names}")
         return None

    evaluation_results = {}
    logger.info("Calculating metrics for each target variable:")

    for target in target_names:
        y_true_target = y_true[target]
        y_pred_target = y_pred[target]

        # Drop NaNs separately for each target if they exist
        mask = y_true_target.notna() & y_pred_target.notna()
        if mask.sum() == 0:
             logger.warning(f"No valid (non-NaN) true/predicted pairs for target '{target}'. Skipping evaluation.")
             evaluation_results[target] = {'RMSE': np.nan, 'MAE': np.nan, 'R2': np.nan, 'Count': 0}
             continue

        y_true_target = y_true_target[mask]
        y_pred_target = y_pred_target[mask]
        count = len(y_true_target)

        try:
            rmse = np.sqrt(mean_squared_error(y_true_target, y_pred_target))
            mae = mean_absolute_error(y_true_target, y_pred_target)
            r2 = r2_score(y_true_target, y_pred_target)

            evaluation_results[target] = {
                'RMSE': rmse,
                'MAE': mae,
                'R2': r2,
                'Count': count
            }
            logger.info(f"  - {target}: RMSE={rmse:.4f}, MAE={mae:.4f}, R2={r2:.4f} (Count={count})")

        except Exception as e:
            logger.error(f"Error calculating metrics for target '{target}': {e}", exc_info=True)
            evaluation_results[target] = {'RMSE': np.nan, 'MAE': np.nan, 'R2': np.nan, 'Count': 0}

    # *** Placeholder: Add plotting functionality if desired ***
    # Example: Scatter plot of true vs predicted for each target
    # for target in target_names:
    #     if evaluation_results.get(target, {}).get('Count', 0) > 0:
    #         plt.figure()
    #         sns.scatterplot(x=y_true[target], y=y_pred[target], alpha=0.5)
    #         # Add 1:1 line
    #         lims = [min(y_true[target].min(), y_pred[target].min()), max(y_true[target].max(), y_pred[target].max())]
    #         plt.plot(lims, lims, 'r--', alpha=0.75, zorder=0)
    #         plt.title(f"True vs Predicted: {target}")
    #         plt.xlabel("True Value")
    #         plt.ylabel("Predicted Value")
    #         # Save plot?
    #         plt.close()

    logger.info("Surrogate model evaluation complete.")
    return evaluation_results

# Add other evaluation functions if needed, e.g.,
# - Feature importance analysis
# - Residual analysis
# - Comparison across different models
