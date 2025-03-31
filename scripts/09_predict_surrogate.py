##############################################################################
### File: scripts/09_predict_surrogate.py
##############################################################################
import argparse
import logging
import pandas as pd
import os
import sys
from typing import Dict, Any

# Add project root if needed
# project_root = str(Path(__file__).parent.parent)
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)

try:
    from src.config_loader import load_config
    from src.utils import setup_logging, ensure_dir_exists, Timer
    # Import from the new surrogate model structure
    from src.surrogate_model.feature_engineering import engineer_features
    from src.surrogate_model.predict import predict_with_surrogate
except ImportError as e:
    print(f"ERROR: Cannot import 'src' modules ({e}). Make sure you are running from the project root directory"
          " or have the 'src' directory in your PYTHONPATH.", file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger(__name__)

def main(args):
    """Main function to make predictions using trained surrogate models."""
    try:
        config = load_config(args.config)
        # setup_logging called inside load_config
        logger.info("--- Starting Step 9: Predict with Surrogate Models (Optional) ---")

        sm_config = config.get('surrogate_model', {})
        if not sm_config.get('enabled', False):
            logger.info("Surrogate model prediction is disabled in the configuration ('surrogate_model.enabled: false'). Skipping.")
            sys.exit(0)

        base_dir = config.get('base_dir')
        def resolve_path(rel_path):
            if not rel_path: return None
            if os.path.isabs(rel_path): return rel_path
            if base_dir: return os.path.join(base_dir, rel_path)
            return os.path.abspath(rel_path) # Use relative if no base_dir

        paths_cfg = config['paths']
        model_load_dir = resolve_path(paths_cfg.get('surrogate_model_dir'))
        # Output prediction file path comes from args, resolve it if relative
        output_prediction_file = resolve_path(args.output_prediction_file)

        # Input file containing features for scenarios to predict (from args)
        input_feature_file = resolve_path(args.input_feature_file)

        if not input_feature_file or not output_prediction_file:
            logger.critical("Arguments --input_feature_file and --output_prediction_file are required for surrogate prediction.")
            sys.exit(1)
        if not os.path.exists(input_feature_file):
             logger.critical(f"Input feature file not found: {input_feature_file}")
             sys.exit(1)
        if not model_load_dir or not os.path.isdir(model_load_dir):
             logger.critical(f"Model loading directory not found or invalid: {model_load_dir}. Ensure models are trained (Step 8).")
             sys.exit(1)

        ensure_dir_exists(os.path.dirname(output_prediction_file)) # Ensure output dir exists

        # --- Load Input Feature Data ---
        logger.info(f"Loading input features from: {input_feature_file}")
        try:
            with Timer("LoadInputFeatures"):
                 # Determine file type and load
                 if input_feature_file.lower().endswith('.csv'):
                      df_features = pd.read_csv(input_feature_file)
                 elif input_feature_file.lower().endswith('.parquet'):
                      df_features = pd.read_parquet(input_feature_file)
                 else:
                      raise ValueError("Unsupported file format for input features (use .csv or .parquet)")
            logger.info(f"Loaded input features with shape: {df_features.shape}")
        except Exception as e_load:
            logger.critical(f"Failed to load input feature file: {e_load}", exc_info=True)
            sys.exit(1)

        # --- Feature Engineering (Apply the SAME steps as in training) ---
        logger.info("Applying feature engineering to input data...")
        # We don't need the returned feature list here, as predict_with_surrogate loads it
        df_engineered_pred, _ = engineer_features(df_features, config)
        if df_engineered_pred is None or df_engineered_pred.empty:
             logger.error("Feature engineering failed for prediction data.")
             sys.exit(1)

        # --- Make Predictions ---
        # The predict_with_surrogate function handles loading models and the feature list
        logger.info("Making predictions using loaded surrogate models...")
        df_predictions = predict_with_surrogate(df_engineered_pred, config)

        if df_predictions is None:
            logger.error("Surrogate model prediction failed.")
            # Decide if critical
            sys.exit(1) # Exit with error if prediction failed
        elif df_predictions.empty:
             logger.warning("Surrogate prediction returned an empty DataFrame.")
             # Save empty file? Or just log? Log for now.
        else:
            # Save predictions
            logger.info(f"Saving predictions to: {output_prediction_file}")
            try:
                 # Use output compression from config for parquet
                 compression_method = config['analysis'].get('output_compression')
                 if output_prediction_file.lower().endswith('.csv'):
                      df_predictions.to_csv(output_prediction_file, index=False)
                 elif output_prediction_file.lower().endswith('.parquet'):
                      df_predictions.to_parquet(output_prediction_file, index=False, compression=compression_method)
                 else:
                      logger.warning(f"Output filename '{output_prediction_file}' does not end with .csv or .parquet. Saving as CSV.")
                      df_predictions.to_csv(output_prediction_file, index=False)
                 logger.info("Predictions saved successfully.")
            except Exception as e_save:
                 logger.error(f"Failed to save predictions: {e_save}", exc_info=True)


        logger.info("--- Finished Step 9: Predict with Surrogate Models ---")

    except FileNotFoundError as e:
         logger.critical(f"File not found error: {e}. Check paths in config and arguments.", exc_info=False)
         sys.exit(1)
    except (ValueError, KeyError) as e:
         logger.critical(f"Configuration or Data Error: {e}. Please check config file and input data.", exc_info=True)
         sys.exit(1)
    except Exception as e:
        logger.critical(f"An unexpected error occurred during surrogate prediction: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Use trained surrogate models to make predictions for new scenarios."
        )
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to the configuration file.'
        )
    parser.add_argument(
        '--input_feature_file',
        type=str,
        required=True,
        help='Path to the input CSV or Parquet file containing features for prediction scenarios.'
        )
    parser.add_argument(
        '--output_prediction_file',
        type=str,
        required=True,
        help='Path to save the output predictions (CSV or Parquet).'
        )
    # Add optional arguments if needed

    args = parser.parse_args()
    main(args)
