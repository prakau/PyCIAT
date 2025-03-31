"""
Functions for making predictions using trained surrogate models in PyCIAT.
"""

import logging
import os
from typing import Dict, Any, Optional, List

import joblib
import pandas as pd
import numpy as np
# Import necessary ML libraries (Pipeline)
from sklearn.pipeline import Pipeline

from src.utils import Timer

logger = logging.getLogger(__name__)

def predict_with_surrogate(
    df_features: pd.DataFrame,
    config: Dict[str, Any]
    ) -> Optional[pd.DataFrame]:
    """
    Makes predictions using a pre-trained surrogate model pipeline.

    - Loads the saved pipeline object (including scaler and model).
    - Ensures input features match the features used during training.
    - Applies the pipeline's transform and predict methods.
    - Returns a DataFrame with predictions.

    Args:
        df_features: DataFrame containing the features for the scenarios to predict.
                     Must have undergone the same feature engineering steps as the training data.
        config: Project configuration dictionary.

    Returns:
        DataFrame containing the predictions, indexed like df_features,
        with columns corresponding to the target variables, or None on failure.
    """
    logger.info("Starting prediction with surrogate model...")
    sm_config = config.get('surrogate_model', {})
    model_type = sm_config.get('model_type', 'RandomForest') # Get model type used for training
    model_load_dir = config.get('paths', {}).get('surrogate_model_dir')

    if not model_load_dir:
        logger.error("Path 'surrogate_model_dir' not defined in config['paths']. Cannot load models.")
        return None

    # Resolve path relative to base_dir if necessary
    base_dir = config.get('base_dir')
    if not os.path.isabs(model_load_dir) and base_dir:
        model_load_dir = os.path.join(base_dir, model_load_dir)

    # Define the expected filename based on model type
    pipeline_filename = f"surrogate_pipeline_{model_type}.joblib"
    load_path = os.path.join(model_load_dir, pipeline_filename)

    if not os.path.exists(load_path):
        logger.error(f"Trained surrogate model pipeline not found at: {load_path}. Run training step first.")
        return None

    # --- Load the trained pipeline and metadata ---
    logger.info(f"Loading trained pipeline from: {load_path}")
    try:
        saved_object = joblib.load(load_path)
        pipeline: Pipeline = saved_object['pipeline']
        trained_features: List[str] = saved_object['features']
        trained_targets: List[str] = saved_object['targets']
        logger.info(f"Pipeline loaded successfully. Trained on {len(trained_features)} features for targets: {trained_targets}.")
    except Exception as e:
        logger.error(f"Failed to load pipeline object from {load_path}: {e}", exc_info=True)
        return None

    # --- Prepare Input Features ---
    # Ensure the input DataFrame has the same columns (features) as the training data, in the same order.
    missing_features = set(trained_features) - set(df_features.columns)
    extra_features = set(df_features.columns) - set(trained_features)

    if missing_features:
        logger.error(f"Input data for prediction is missing required features used during training: {missing_features}")
        return None
    if extra_features:
        logger.warning(f"Input data has extra columns not used during training: {extra_features}. These will be ignored.")

    # Reorder input columns to match training order
    try:
        X_pred = df_features[trained_features].copy()
    except KeyError:
        # This should be caught by missing_features check, but as a safeguard
        logger.error("Error selecting/reordering features for prediction. Columns might not match training.")
        return None

    # Handle potential NaNs in prediction input (should ideally be handled by feature engineering)
    if X_pred.isnull().values.any():
        nan_counts = X_pred.isnull().sum()
        logger.warning(f"NaN values found in input features for prediction:\n{nan_counts[nan_counts > 0]}")
        # Option 1: Fail
        # logger.error("Cannot make predictions with NaN values in input features.")
        # return None
        # Option 2: Attempt imputation (using scaler's mean? Risky without proper imputer)
        # Option 3: Allow model to handle (some models might, others will error) - Current approach
        logger.warning("Proceeding with prediction despite NaNs. Model might fail or produce NaNs.")


    # --- Make Predictions ---
    logger.info(f"Making predictions for {len(X_pred)} scenarios...")
    try:
        with Timer(f"PredictSurrogate_{model_type}"):
            predictions_array = pipeline.predict(X_pred)
        logger.info("Prediction complete.")
    except Exception as e:
        logger.error(f"Error during prediction: {e}", exc_info=True)
        return None

    # --- Format Output ---
    # Convert numpy array output to DataFrame with correct target names and index
    if predictions_array.ndim == 1 and len(trained_targets) == 1:
        predictions_df = pd.DataFrame(predictions_array, index=X_pred.index, columns=trained_targets)
    elif predictions_array.ndim == 2 and predictions_array.shape[1] == len(trained_targets):
        predictions_df = pd.DataFrame(predictions_array, index=X_pred.index, columns=trained_targets)
    else:
        logger.error(f"Unexpected prediction output shape: {predictions_array.shape}. Expected ({len(X_pred)}, {len(trained_targets)}).")
        return None

    # Optionally join predictions back to original features?
    # For now, just return the predictions DataFrame.
    # predictions_df = df_features.join(predictions_df) # Join based on index

    return predictions_df
