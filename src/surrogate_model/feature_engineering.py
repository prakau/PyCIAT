"""
Functions for feature engineering for surrogate models in PyCIAT.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
# Import necessary libraries for feature engineering (e.g., sklearn)
# from sklearn.preprocessing import StandardScaler, OneHotEncoder
# from sklearn.compose import ColumnTransformer

logger = logging.getLogger(__name__)

def engineer_features(
    df: pd.DataFrame,
    config: Dict[str, Any]
    ) -> Tuple[Optional[pd.DataFrame], Optional[List[str]]]:
    """
    Performs feature engineering on the input DataFrame based on configuration.

    This might include:
    - Calculating derived features (e.g., growing season summaries from daily climate).
    - Handling categorical features (e.g., one-hot encoding).
    - Scaling numerical features.
    - Selecting final features based on config['surrogate_model']['features'].

    Args:
        df: DataFrame containing simulation results and potential features.
        config: Project configuration dictionary.

    Returns:
        A tuple containing:
        - DataFrame with engineered features.
        - List of final feature names used.
        Returns (None, None) on failure.
    """
    logger.info("Starting feature engineering for surrogate model...")
    sm_config = config.get('surrogate_model', {})
    required_features = sm_config.get('features', [])

    if not required_features:
        logger.error("No features specified in config['surrogate_model']['features'].")
        return None, None

    df_engineered = df.copy()

    # *** Placeholder: Implement actual feature engineering logic ***

    # 1. Calculate derived features (e.g., sowing DOY, climate summaries)
    # Example: Convert sowing date string to DOY
    if 'sowing_date' in df_engineered.columns:
        try:
            df_engineered['sowing_doy'] = pd.to_datetime(df_engineered['sowing_date'], format='%m-%d').dt.dayofyear
            logger.debug("Calculated 'sowing_doy'.")
        except Exception as e:
            logger.warning(f"Could not calculate sowing_doy from sowing_date: {e}")

    # Example: Calculate growing season climate summaries (requires climate data join)
    # This is complex and likely needs climate data linked here or pre-calculated features.
    # Placeholder columns assumed to exist for now if listed in config:
    climate_summary_features = [
        "AvgTmax_C", "AvgTmin_C", "TotalPrecip_mm"
        # Add others if defined in config and calculated elsewhere
    ]
    for f in climate_summary_features:
        if f in required_features and f not in df_engineered.columns:
            logger.warning(f"Required climate summary feature '{f}' not found in input data. Surrogate training might fail.")
            # Optionally add NaN column?
            # df_engineered[f] = np.nan

    # 2. Handle categorical features (One-Hot Encoding example)
    categorical_features = [
        'climate_source', 'gcm', 'scenario', 'period', 'soil_id', 'adaptation'
        # Add others if needed
    ]
    categorical_features_present = [f for f in categorical_features if f in df_engineered.columns]

    if categorical_features_present:
        logger.debug(f"Applying One-Hot Encoding to: {categorical_features_present}")
        try:
            df_engineered = pd.get_dummies(df_engineered, columns=categorical_features_present, dummy_na=False) # Handle potential NaNs if needed
            logger.info(f"DataFrame shape after OHE: {df_engineered.shape}")
        except Exception as e:
            logger.error(f"One-Hot Encoding failed: {e}", exc_info=True)
            return None, None

    # 3. Select final features
    # The final feature list includes original numeric features + newly created OHE features
    # We need to determine the full list of columns generated by get_dummies
    final_feature_list = []
    missing_features = []
    for feature in required_features:
        if feature in df_engineered.columns:
            final_feature_list.append(feature)
        # Check if the feature was categorical and now exists as multiple OHE columns
        elif feature in categorical_features_present:
             ohe_cols = [col for col in df_engineered.columns if col.startswith(f"{feature}_")]
             if ohe_cols:
                  final_feature_list.extend(ohe_cols)
                  logger.debug(f"Expanded categorical feature '{feature}' to OHE columns: {ohe_cols}")
             else:
                  # This case might happen if a category had only one value or all NaNs
                  logger.warning(f"Categorical feature '{feature}' specified but no corresponding OHE columns found after encoding.")
                  missing_features.append(feature)
        else:
            logger.warning(f"Required feature '{feature}' not found in DataFrame after engineering.")
            missing_features.append(feature)

    if missing_features:
        logger.error(f"Could not find or engineer all required features: {missing_features}. Check config and data.")
        # Decide whether to proceed with available features or fail
        # return None, None # Fail strict

    # Ensure no duplicates in final list
    final_feature_list = sorted(list(set(final_feature_list)))

    logger.info(f"Feature engineering complete. Final features ({len(final_feature_list)}): {final_feature_list[:10]}...") # Log first few

    # Return only the columns needed (features + potentially targets if they exist)
    # Targets are handled in prepare_surrogate_data
    cols_to_keep = final_feature_list + sm_config.get('targets', []) + ['simulation_id'] # Keep ID for potential joins
    cols_to_keep = [c for c in cols_to_keep if c in df_engineered.columns] # Ensure columns exist

    return df_engineered[cols_to_keep], final_feature_list
