##############################################################################
### File: scripts/08_train_surrogate.py
##############################################################################
import argparse
import logging
import pandas as pd
import os
import sys
from typing import Dict, Any, Tuple, List, Optional

# Add project root if needed
# project_root = str(Path(__file__).parent.parent)
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)

try:
    from src.config_loader import load_config
    from src.utils import setup_logging, ensure_dir_exists, Timer
    # Import from the new surrogate model structure
    from src.surrogate_model.feature_engineering import engineer_features
    from src.surrogate_model.model_selection import prepare_surrogate_data, train_surrogate_model
    # Import evaluation if needed here, or keep it separate
    # from src.surrogate_model.evaluation import evaluate_surrogate
except ImportError as e:
    print(f"ERROR: Cannot import 'src' modules ({e}). Make sure you are running from the project root directory"
          " or have the 'src' directory in your PYTHONPATH.", file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger(__name__)

def main(args):
    """Main function to train machine learning surrogate models."""
    try:
        config = load_config(args.config)
        # setup_logging called inside load_config
        logger.info("--- Starting Step 8: Train Surrogate Models (Optional) ---")

        sm_config = config.get('surrogate_model', {})
        if not sm_config.get('enabled', False):
            logger.info("Surrogate model training is disabled in the configuration ('surrogate_model.enabled: false'). Skipping.")
            sys.exit(0)

        base_dir = config.get('base_dir')
        def resolve_path(rel_path):
            if not rel_path: return None
            if os.path.isabs(rel_path): return rel_path
            if base_dir: return os.path.join(base_dir, rel_path)
            return os.path.abspath(rel_path)

        paths_cfg = config['paths']
        analysis_out_dir = resolve_path(paths_cfg.get('analysis_output_dir'))
        model_save_dir = resolve_path(paths_cfg.get('surrogate_model_dir'))

        # Input file: Combined results with standardized variables
        combined_results_file = os.path.join(analysis_out_dir, "combined_results_std_vars.parquet")

        if not analysis_out_dir or not model_save_dir:
             logger.critical("Configuration paths for 'analysis_output_dir' or 'surrogate_model_dir' missing.")
             sys.exit(1)
        if not combined_results_file:
             logger.critical("Could not determine path for combined results file.")
             sys.exit(1)


        ensure_dir_exists(model_save_dir) # Ensure save directory exists

        # --- Load Combined Simulation Results ---
        logger.info(f"Loading combined simulation results from: {combined_results_file}")
        if not os.path.exists(combined_results_file):
            logger.critical(f"Combined results file not found: {combined_results_file}. Run Step 4 first.")
            sys.exit(1)
        try:
            with Timer("LoadCombinedResultsForSurrogate"):
                df_results = pd.read_parquet(combined_results_file)
            logger.info(f"Loaded results for training with shape: {df_results.shape}")
        except Exception as e_load:
            logger.critical(f"Failed to load combined results Parquet file: {e_load}", exc_info=True)
            sys.exit(1)

        # --- Feature Engineering ---
        logger.info("Performing feature engineering...")
        df_engineered, final_feature_list = engineer_features(df_results, config)
        if df_engineered is None or df_engineered.empty or final_feature_list is None:
             logger.error("Feature engineering failed or produced empty dataframe/feature list. Cannot train model.")
             sys.exit(1)

        # --- Prepare Data (Select Features/Targets, Handle NaNs) ---
        logger.info("Preparing data for training...")
        X, y, final_feature_list_used, target_list = prepare_surrogate_data(df_engineered, final_feature_list, config)

        if X is None or y is None:
            logger.error("Data preparation failed. Cannot train model.")
            sys.exit(1)

        # --- Train Models ---
        logger.info(f"Starting model training for targets: {target_list}")
        # train_surrogate_model now handles splitting, training, evaluation (basic), and saving
        trained_pipelines = train_surrogate_model(X, y, final_feature_list_used, target_list, config)

        if trained_pipelines:
            logger.info(f"Successfully trained and saved {len(trained_pipelines)} surrogate model pipelines.")
            # Optional: Perform more detailed evaluation using the test split returned by train_test_split
            # This would require train_surrogate_model to return the test set or saving it.
            # Or, have a separate evaluation script/step.
            # Example:
            # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=sm_config.get('test_size', 0.2), random_state=42)
            # pipeline = trained_pipelines['main_pipeline'] # Assuming single pipeline saved
            # y_pred_test = pipeline.predict(X_test)
            # evaluation_metrics = evaluate_surrogate(y_test, y_pred_test, target_list)
            # logger.info(f"Detailed Test Set Evaluation:\n{pd.DataFrame(evaluation_metrics).T}")

        else:
            logger.error("Surrogate model training failed or produced no models.")
            # Decide if this should be a critical error
            sys.exit(1) # Exit with error if training failed

        logger.info("--- Finished Step 8: Train Surrogate Models ---")

    except FileNotFoundError as e:
         logger.critical(f"Input file error: {e}. Ensure previous steps ran successfully.", exc_info=False)
         sys.exit(1)
    except (ValueError, KeyError) as e:
         logger.critical(f"Configuration or Data Error: {e}. Please check config file and input data.", exc_info=True)
         sys.exit(1)
    except Exception as e:
        logger.critical(f"An unexpected error occurred during surrogate model training: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train machine learning surrogate models based on simulation results."
        )
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to the configuration file.'
        )
    # Add optional arguments if needed (e.g., override model type, hyperparameters)

    args = parser.parse_args()
    main(args)
