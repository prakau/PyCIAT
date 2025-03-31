"""
Functions for training and selecting surrogate models in PyCIAT.
"""

import logging
import os
from typing import Dict, Any, Optional, List, Union

import joblib
import pandas as pd
import numpy as np
# Import necessary ML libraries
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor # Example
# from xgboost import XGBRegressor # Example
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler # Example scaler
# from sklearn.compose import ColumnTransformer # If needed for mixed types
# from sklearn.metrics import mean_squared_error, r2_score # Moved to evaluation

from src.utils import ensure_dir_exists, Timer

logger = logging.getLogger(__name__)

def prepare_surrogate_data(
    df_engineered: pd.DataFrame,
    feature_list: List[str],
    config: Dict[str, Any]
    ) -> tuple[Optional[pd.DataFrame], Optional[Union[pd.DataFrame, pd.Series]], List[str], List[str]]:
    """
    Prepares data for surrogate model training.

    - Selects features and targets.
    - Handles missing values (e.g., imputation or dropping).
    - Returns X (features) and y (targets) DataFrames/Series.

    Args:
        df_engineered: DataFrame with engineered features and target variables.
        feature_list: List of final feature column names to use.
        config: Project configuration dictionary.

    Returns:
        A tuple containing:
        - X (features DataFrame) or None on failure.
        - y (targets DataFrame/Series) or None on failure.
        - List of features actually used (after checking existence).
        - List of targets actually used.
    """
    logger.info("Preparing data for surrogate training...")
    sm_config = config.get('surrogate_model', {})
    target_list = sm_config.get('targets', [])

    if not target_list:
        logger.error("No target variables specified in config['surrogate_model']['targets'].")
        return None, None, [], []

    # Ensure features and targets exist in the dataframe
    features_present = [f for f in feature_list if f in df_engineered.columns]
    targets_present = [t for t in target_list if t in df_engineered.columns]

    missing_features = set(feature_list) - set(features_present)
    missing_targets = set(target_list) - set(targets_present)

    if missing_features:
        logger.warning(f"Features specified in list but missing from engineered data: {missing_features}")
    if missing_targets:
        logger.error(f"Target variables missing from engineered data: {missing_targets}. Cannot train.")
        return None, None, [], []
    if not features_present or not targets_present:
        logger.error("No valid features or targets found in the data.")
        return None, None, [], []

    logger.debug(f"Using features: {features_present}")
    logger.debug(f"Using targets: {targets_present}")

    X = df_engineered[features_present].copy()
    y = df_engineered[targets_present].copy()

    # Handle missing values
    # Option 1: Drop rows with any NaNs in features or targets
    initial_rows = len(X)
    combined = pd.concat([X, y], axis=1)
    combined.dropna(inplace=True)
    if len(combined) < initial_rows:
        logger.warning(f"Dropped {initial_rows - len(combined)} rows due to NaN values in features or targets.")
        if len(combined) == 0:
             logger.error("All rows dropped due to NaNs. Cannot train.")
             return None, None, [], []

    X = combined[features_present]
    y = combined[targets_present]

    # Option 2: Imputation (more complex, requires fitting imputer)
    # Example:
    # from sklearn.impute import SimpleImputer
    # imputer = SimpleImputer(strategy='mean')
    # X = pd.DataFrame(imputer.fit_transform(X), columns=features_present, index=X.index)
    # # Impute targets? Usually less common, depends on strategy.

    logger.info(f"Data preparation complete. X shape: {X.shape}, y shape: {y.shape}")
    # Squeeze y if it's a single target
    if y.shape[1] == 1:
        y = y.squeeze()

    return X, y, features_present, targets_present


def train_surrogate_model(
    X: pd.DataFrame,
    y: Union[pd.DataFrame, pd.Series],
    features_used: List[str],
    targets_used: List[str],
    config: Dict[str, Any]
    ) -> Optional[Dict[str, Pipeline]]:
    """
    Trains surrogate models based on the configuration.

    - Splits data into training and testing sets.
    - Defines model pipeline (e.g., scaling + regressor).
    - Trains a model for each target variable (or uses MultiOutputRegressor).
    - Saves trained model pipelines.
    - Returns dictionary of trained pipelines {target_name: pipeline}.

    Args:
        X: DataFrame of features.
        y: DataFrame or Series of targets.
        features_used: List of feature names used.
        targets_used: List of target names used.
        config: Project configuration dictionary.

    Returns:
        Dictionary mapping target variable names to trained scikit-learn Pipelines,
        or None on failure.
    """
    sm_config = config.get('surrogate_model', {})
    model_type = sm_config.get('model_type', 'RandomForest')
    hyperparameters = sm_config.get('hyperparameters', {})
    test_size = sm_config.get('test_size', 0.2)
    model_save_dir = config.get('paths', {}).get('surrogate_model_dir')

    if not model_save_dir:
        logger.error("Path 'surrogate_model_dir' not defined in config['paths']. Cannot save models.")
        return None

    # Resolve path relative to base_dir if necessary
    base_dir = config.get('base_dir')
    if not os.path.isabs(model_save_dir) and base_dir:
        model_save_dir = os.path.join(base_dir, model_save_dir)
    ensure_dir_exists(model_save_dir)

    logger.info(f"Splitting data into train/test sets (test_size={test_size})...")
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42 # Use random state for reproducibility
        )
        logger.info(f"Train shapes: X={X_train.shape}, y={y_train.shape}")
        logger.info(f"Test shapes: X={X_test.shape}, y={y_test.shape}")
    except Exception as e:
        logger.error(f"Failed to split data: {e}", exc_info=True)
        return None

    # --- Define Model Pipeline ---
    # Example pipeline: StandardScaler + RandomForestRegressor
    # TODO: Make pipeline steps configurable
    logger.info(f"Defining model pipeline with {model_type}...")
    steps = []
    # 1. Scaler (optional, depends on model)
    # Check if features need scaling (e.g., for MLP, not strictly for RF/XGB)
    steps.append(('scaler', StandardScaler())) # Example

    # 2. Regressor
    if model_type == 'RandomForest':
        # Filter hyperparameters for RandomForestRegressor
        valid_rf_params = {k: v for k, v in hyperparameters.items() if k in RandomForestRegressor().get_params()}
        logger.debug(f"Using RandomForestRegressor with params: {valid_rf_params}")
        regressor = RandomForestRegressor(random_state=42, n_jobs=-1, **valid_rf_params) # Use all cores
    elif model_type == 'XGBoost':
        # *** Placeholder: Implement XGBoost ***
        # try:
        #     from xgboost import XGBRegressor
        #     valid_xgb_params = {k: v for k, v in hyperparameters.items() if k in XGBRegressor().get_params()}
        #     logger.debug(f"Using XGBRegressor with params: {valid_xgb_params}")
        #     regressor = XGBRegressor(random_state=42, n_jobs=-1, **valid_xgb_params)
        # except ImportError:
        #     logger.error("XGBoost not installed. Install with 'pip install xgboost'")
        #     return None
        logger.error(f"Model type '{model_type}' not implemented yet.")
        return None # Placeholder
    elif model_type == 'MLP':
         # *** Placeholder: Implement MLP ***
        logger.error(f"Model type '{model_type}' not implemented yet.")
        return None # Placeholder
    else:
        logger.error(f"Unsupported model_type '{model_type}' specified in config.")
        return None

    # Handle multi-output targets if y is a DataFrame
    is_multioutput = isinstance(y_train, pd.DataFrame) and y_train.shape[1] > 1
    if is_multioutput:
        logger.info("Using MultiOutputRegressor for multiple targets.")
        final_model = MultiOutputRegressor(regressor, n_jobs=-1) # Parallelize across targets if possible
        steps.append(('multi_regressor', final_model))
    else:
        steps.append(('regressor', regressor))

    pipeline = Pipeline(steps)
    logger.debug(f"Pipeline steps: {pipeline.steps}")

    # --- Train the Model ---
    logger.info(f"Training {model_type} model pipeline...")
    try:
        with Timer(f"TrainSurrogate_{model_type}"):
            pipeline.fit(X_train, y_train)
        logger.info("Model training complete.")
    except Exception as e:
        logger.error(f"Failed to train model pipeline: {e}", exc_info=True)
        return None

    # --- Evaluate (Basic evaluation here, more detailed in evaluation.py) ---
    # Moved detailed evaluation to separate module/step
    logger.info("Performing basic evaluation on test set...")
    try:
        score = pipeline.score(X_test, y_test) # R^2 score
        logger.info(f"Test set R^2 score: {score:.4f}")
        # y_pred = pipeline.predict(X_test)
        # mse = mean_squared_error(y_test, y_pred)
        # logger.info(f"Test set MSE: {mse:.4f}")
    except Exception as e:
        logger.error(f"Failed during basic evaluation: {e}", exc_info=True)
        # Continue to save model even if evaluation fails? Yes.

    # --- Save Trained Pipeline and Metadata ---
    # Save one pipeline (handles multi-output internally if needed)
    # Include features and targets in the saved object or metadata file
    save_object = {
        'pipeline': pipeline,
        'features': features_used,
        'targets': targets_used,
        'model_type': model_type,
        'training_config': sm_config # Save relevant config part
    }
    # Define a consistent filename
    pipeline_filename = f"surrogate_pipeline_{model_type}.joblib"
    save_path = os.path.join(model_save_dir, pipeline_filename)

    logger.info(f"Saving trained pipeline and metadata to: {save_path}")
    try:
        joblib.dump(save_object, save_path)
        logger.info("Pipeline saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save pipeline: {e}", exc_info=True)
        return None # Fail if saving fails

    # Return dictionary (even if single pipeline, for consistency)
    # Key could be model_type or a generic name
    return {"main_pipeline": pipeline} # Or return the save_object? Pipeline is more useful directly.
