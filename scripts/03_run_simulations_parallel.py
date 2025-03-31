#!/usr/bin/env python
##############################################################################
### File: scripts/03_run_simulations_parallel.py
##############################################################################
"""
Execute crop model simulations in parallel.
Supports both local multiprocessing and HPC job arrays (e.g., SLURM).
"""

import os
import sys
import logging
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed

# Add parent directory to Python path
repo_root = str(Path(__file__).parent.parent)
sys.path.insert(0, repo_root)

from src.config_loader import load_config, ConfigurationError
from src.utils import setup_logging, Timer
from src.crop_model_interface.status_codes import Status
from src import get_model_interface

def get_task_simulations(tracking_df: pd.DataFrame,
                        task_id: Optional[int] = None,
                        num_tasks: Optional[int] = None) -> pd.DataFrame:
    """
    Get subset of simulations to run for this task/process.
    
    Args:
        tracking_df: DataFrame with all simulations
        task_id: Current task ID (for HPC array jobs)
        num_tasks: Total number of tasks (for HPC array jobs)
    
    Returns:
        DataFrame with simulations for this task
    """
    # Filter for simulations ready to run
    ready_mask = tracking_df['status'].isin([
        Status.READY_TO_RUN.name,
        Status.SETUP_SUCCESS.name  # Alternative status that might be used
    ])
    ready_sims = tracking_df[ready_mask].copy()
    
    if task_id is not None and num_tasks is not None:
        # Distribute simulations among HPC tasks
        sim_indices = np.array_split(ready_sims.index, num_tasks)[task_id - 1]
        return ready_sims.loc[sim_indices]
    
    return ready_sims

def run_single_simulation(sim_info: pd.Series,
                        config: Dict[str, Any]) -> Tuple[str, Status, str, float]:
    """
    Run a single simulation.
    
    Args:
        sim_info: Series with simulation parameters
        config: Configuration dictionary
    
    Returns:
        Tuple[str, Status, str, float]: (simulation_id, status, message, runtime)
    """
    sim_id = sim_info['simulation_id']
    
    try:
        with Timer(f"Running simulation {sim_id}") as timer:
            # Get model interface
            model_interface = get_model_interface(sim_info['crop_model'])
            if model_interface is None:
                return sim_id, Status.RUN_ERROR, "Could not initialize model interface", 0.0
            
            # Get paths
            sim_dir = Path(config['paths']['simulation_setup_dir']) / sim_id
            executable = config['crop_model_configs'][sim_info['crop_model']]['executable_path']
            
            # Get experiment file name (model-specific)
            experiment_file = "experiment.txt"  # This would depend on the model
            
            # Run simulation
            status, message = model_interface.run_model(
                experiment_file=experiment_file,
                executable_path=executable,
                working_dir=str(sim_dir)
            )
            
            return sim_id, status, message, timer.duration
    
    except Exception as e:
        return sim_id, Status.RUN_ERROR, str(e), 0.0

def run_parallel_local(task_sims: pd.DataFrame,
                      config: Dict[str, Any],
                      num_workers: int) -> pd.DataFrame:
    """
    Run simulations in parallel using local processes.
    
    Args:
        task_sims: DataFrame with simulations to run
        config: Configuration dictionary
        num_workers: Number of parallel processes
    
    Returns:
        DataFrame with updated simulation status
    """
    results = []
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit all simulations
        future_to_sim = {
            executor.submit(run_single_simulation, row, config): row['simulation_id']
            for _, row in task_sims.iterrows()
        }
        
        # Process results as they complete
        for future in as_completed(future_to_sim):
            sim_id = future_to_sim[future]
            try:
                results.append(future.result())
            except Exception as e:
                results.append((sim_id, Status.RUN_ERROR, str(e), 0.0))
    
    # Create results DataFrame
    results_df = pd.DataFrame(
        results,
        columns=['simulation_id', 'status', 'message', 'run_time']
    )
    
    return results_df

def update_tracking_file(tracking_file: str,
                        results: pd.DataFrame,
                        lock_file: bool = True) -> None:
    """
    Update simulation tracking file with results.
    
    Args:
        tracking_file: Path to tracking CSV file
        results: DataFrame with simulation results
        lock_file: Whether to use file locking (for parallel updates)
    """
    try:
        # Read current tracking data
        tracking_df = pd.read_csv(tracking_file)
        
        # Update with new results
        for _, result in results.iterrows():
            mask = tracking_df['simulation_id'] == result['simulation_id']
            tracking_df.loc[mask, 'status'] = result['status'].name
            tracking_df.loc[mask, 'message'] = result['message']
            tracking_df.loc[mask, 'run_time'] = result['run_time']
        
        if lock_file:
            # Implementation would need proper file locking mechanism
            # This is a placeholder
            tracking_df.to_csv(tracking_file, index=False)
        else:
            tracking_df.to_csv(tracking_file, index=False)
        
    except Exception as e:
        logging.error(f"Error updating tracking file: {e}")
        raise

def main(config_file: str) -> int:
    """
    Main function to run simulations in parallel.
    
    Args:
        config_file: Path to configuration YAML file
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        with Timer("Parallel simulation execution"):
            # Load configuration
            config = load_config(config_file)
            
            # Load simulation tracking data
            tracking_file = config['paths']['simulation_status_file']
            tracking_df = pd.read_csv(tracking_file)
            
            # Check for HPC environment variables
            task_id = None
            num_tasks = None
            if config['parallel'].get('use_hpc_env_vars', False):
                task_id = int(os.environ.get(
                    config['parallel']['hpc_task_id_var'],
                    0
                ))
                num_tasks = int(os.environ.get(
                    config['parallel']['hpc_num_tasks_var'],
                    0
                ))
                if task_id > 0 and num_tasks > 0:
                    logging.info(f"Running as HPC task {task_id} of {num_tasks}")
            
            # Get simulations for this task
            task_sims = get_task_simulations(tracking_df, task_id, num_tasks)
            if task_sims.empty:
                logging.info("No simulations to run")
                return 0
            
            logging.info(f"Running {len(task_sims)} simulations")
            
            # Run simulations
            if task_id is None:
                # Local parallel execution
                num_workers = config['parallel'].get('num_workers', -1)
                if num_workers < 1:
                    num_workers = os.cpu_count()
                results = run_parallel_local(task_sims, config, num_workers)
            else:
                # Serial execution for HPC task
                results = pd.DataFrame([
                    run_single_simulation(row, config)
                    for _, row in task_sims.iterrows()
                ], columns=['simulation_id', 'status', 'message', 'run_time'])
            
            # Update tracking file
            update_tracking_file(
                tracking_file,
                results,
                lock_file=(task_id is not None)  # Use locking for HPC
            )
            
            # Log summary
            success_count = sum(r.is_success() for r in results['status'])
            error_count = len(results) - success_count
            logging.info(f"Completed: {success_count} successful, {error_count} failed")
            
            return 0 if error_count == 0 else 1
    
    except ConfigurationError as e:
        logging.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error during simulation execution: {e}")
        return 1

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Run crop model simulations in parallel"
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
    log_file = "logs/03_run_simulations_parallel.log"
    if "SLURM_ARRAY_TASK_ID" in os.environ:
        # Separate log file for each HPC task
        task_id = os.environ["SLURM_ARRAY_TASK_ID"]
        log_file = f"logs/03_run_simulations_parallel_task{task_id}.log"
    
    setup_logging(
        log_file=log_file,
        level=args.log_level
    )
    
    # Run main function
    exit_code = main(args.config)
    sys.exit(exit_code)
