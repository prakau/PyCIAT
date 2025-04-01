#!/bin/bash
#SBATCH --job-name=pyciat_sim    # Job name
#SBATCH --output=logs/slurm_%A_%a.out    # Standard output file (%A: job ID, %a: array index)
#SBATCH --error=logs/slurm_%A_%a.err     # Standard error file
#SBATCH --time=24:00:00          # Time limit (adjust as needed)
#SBATCH --nodes=1                # Number of nodes per task
#SBATCH --ntasks=1               # Number of tasks per node
#SBATCH --cpus-per-task=1        # Number of CPU cores per task
#SBATCH --mem=4G                 # Memory per node (adjust as needed)
#SBATCH --array=1-100           # Array job size (adjust based on number of simulations)

# Load any required modules (uncomment and modify as needed for your HPC environment)
# module load python/3.10
# module load netcdf4
# etc...

# Activate virtual environment (modify path as needed)
source /path/to/your/venv/bin/activate

# Navigate to project directory (modify path as needed)
cd /path/to/pyciat

# Run the simulation script
python scripts/03_run_simulations_parallel.py --config config/config.yaml

# Note: The script will automatically detect SLURM_ARRAY_TASK_ID and SLURM_ARRAY_TASK_COUNT
# to divide work among array jobs
