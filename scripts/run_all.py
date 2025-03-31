#!/usr/bin/env python
##############################################################################
### File: scripts/run_all.py
##############################################################################
"""
Main script to run the complete modeling pipeline.
Coordinates execution of all steps with error handling and logging.
"""

import os
import sys
import time
import logging
import argparse
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

# Add parent directory to Python path
repo_root = str(Path(__file__).parent.parent)
sys.path.insert(0, repo_root)

from src.utils import setup_logging, Timer

# Define pipeline steps
PIPELINE_STEPS = [
    {
        'script': '00_setup_environment.py',
        'description': 'Environment setup and validation',
        'required': True
    },
    {
        'script': '01_prepare_climate_data.py',
        'description': 'Climate data preparation',
        'required': True
    },
    {
        'script': '02_setup_simulations.py',
        'description': 'Simulation setup',
        'required': True
    },
    {
        'script': '03_run_simulations_parallel.py',
        'description': 'Run simulations',
        'required': True
    },
    {
        'script': '04_process_outputs.py',
        'description': 'Process simulation outputs',
        'required': True
    },
    {
        'script': '05_analyze_impacts.py',
        'description': 'Impact analysis',
        'required': True
    },
    {
        'script': '06_evaluate_adaptations.py',
        'description': 'Adaptation evaluation',
        'required': False
    },
    {
        'script': '07_generate_figures.py',
        'description': 'Generate figures',
        'required': False
    }
]

def run_pipeline_step(script: str,
                     config_file: str,
                     log_level: str,
                     step_args: Optional[List[str]] = None) -> Tuple[int, float]:
    """
    Run a single pipeline step.
    
    Args:
        script: Name of script to run
        config_file: Path to configuration file
        log_level: Logging level
        step_args: Additional arguments for this step
    
    Returns:
        Tuple[int, float]: (exit code, execution time in seconds)
    """
    script_path = Path(__file__).parent / script
    
    if not script_path.exists():
        logging.error(f"Script not found: {script_path}")
        return 1, 0.0
    
    # Build command
    cmd = [
        sys.executable,
        str(script_path),
        '--config', config_file,
        '--log-level', log_level
    ]
    
    if step_args:
        cmd.extend(step_args)
    
    # Run script and time execution
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        exit_code = result.returncode
        
        # Log output
        if result.stdout:
            logging.info(result.stdout)
        if result.stderr:
            logging.error(result.stderr)
            
    except subprocess.CalledProcessError as e:
        logging.error(f"Step failed with exit code {e.returncode}")
        logging.error(f"Error output: {e.stderr}")
        exit_code = e.returncode
        
    except Exception as e:
        logging.error(f"Error running step: {e}")
        exit_code = 1
    
    execution_time = time.time() - start_time
    return exit_code, execution_time

def main(config_file: str,
         steps: Optional[List[str]] = None,
         log_level: str = "INFO",
         continue_on_error: bool = False) -> int:
    """
    Run complete modeling pipeline.
    
    Args:
        config_file: Path to configuration file
        steps: Optional list of specific steps to run
        log_level: Logging level
        continue_on_error: Whether to continue if a step fails
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        with Timer("Complete pipeline execution"):
            logging.info("Starting modeling pipeline")
            
            # Track failures
            failed_steps = []
            
            # Run each step
            for step in PIPELINE_STEPS:
                script = step['script']
                
                # Skip if not in requested steps
                if steps and script not in steps:
                    logging.info(f"Skipping step: {script}")
                    continue
                
                logging.info(f"\n{'='*80}\nRunning: {step['description']} ({script})\n{'='*80}")
                
                # Run step
                exit_code, runtime = run_pipeline_step(script, config_file, log_level)
                
                if exit_code != 0:
                    failed_steps.append(script)
                    msg = f"Step failed: {script} (runtime: {runtime:.1f}s)"
                    if step['required'] and not continue_on_error:
                        logging.error(msg)
                        return 1
                    else:
                        logging.warning(msg)
                else:
                    logging.info(f"Step completed successfully: {script} (runtime: {runtime:.1f}s)")
            
            # Final summary
            if failed_steps:
                logging.warning("Pipeline completed with failures:")
                for step in failed_steps:
                    logging.warning(f"  - {step}")
                return 1
            else:
                logging.info("Pipeline completed successfully")
                return 0
    
    except Exception as e:
        logging.error(f"Pipeline execution failed: {e}")
        return 1

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Run complete modeling pipeline"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to configuration YAML file"
    )
    parser.add_argument(
        "--steps",
        nargs="+",
        help="Specific steps to run (e.g., 00_setup_environment.py)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level"
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue pipeline execution if a non-required step fails"
    )
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    # Setup logging
    setup_logging(
        log_file="logs/run_all.log",
        level=args.log_level
    )
    
    # Run pipeline
    exit_code = main(
        config_file=args.config,
        steps=args.steps,
        log_level=args.log_level,
        continue_on_error=args.continue_on_error
    )
    sys.exit(exit_code)
