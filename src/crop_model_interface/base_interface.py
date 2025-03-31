##############################################################################
### File: src/crop_model_interface/base_interface.py
##############################################################################
"""
Abstract base class defining the interface that all crop model implementations must follow.
This ensures consistent behavior across different model interfaces.
"""

from abc import ABC, abstractmethod
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from .status_codes import Status

class BaseCropModelInterface(ABC):
    """
    Abstract base class for crop model interfaces.
    Defines required methods for file generation, model execution, and output parsing.
    """
    
    @abstractmethod
    def generate_weather(self, 
                        climate_data: pd.DataFrame,
                        site_info: Dict[str, Any],
                        output_path: str) -> bool:
        """
        Generate weather input file in model-specific format.

        Args:
            climate_data: DataFrame with daily weather variables
            site_info: Dictionary with site metadata (lat, lon, elev, etc.)
            output_path: Path where weather file should be written

        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError("Subclass must implement generate_weather")

    @abstractmethod
    def generate_soil(self,
                     soil_profile: Dict[str, Any],
                     output_path: str) -> bool:
        """
        Generate soil input file in model-specific format.

        Args:
            soil_profile: Dictionary containing soil profile data (layers, properties)
            output_path: Path where soil file should be written

        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError("Subclass must implement generate_soil")

    @abstractmethod
    def generate_experiment(self,
                          exp_details: Dict[str, Any],
                          output_path: str,
                          template_path: Optional[str] = None,
                          config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Generate experiment/simulation control file in model-specific format.

        Args:
            exp_details: Dictionary containing experiment parameters
            output_path: Path where experiment file should be written
            template_path: Optional path to template file (e.g., for APSIM)
            config: Optional full configuration dictionary for additional settings

        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError("Subclass must implement generate_experiment")

    @abstractmethod
    def run_model(self,
                  experiment_file: str,
                  executable_path: str,
                  working_dir: str) -> Tuple[Status, str]:
        """
        Execute the crop model for a single simulation.

        Args:
            experiment_file: Name of the experiment file to run
            executable_path: Path to model executable
            working_dir: Working directory containing all input files

        Returns:
            Tuple[Status, str]: Status enum and message describing outcome
        """
        raise NotImplementedError("Subclass must implement run_model")

    @abstractmethod
    def parse_output(self,
                    output_dir: str,
                    output_files_config: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Parse model outputs into a standardized dictionary format.

        Args:
            output_dir: Directory containing model output files
            output_files_config: Dictionary mapping output types to filenames

        Returns:
            Optional[Dict[str, Any]]: Dictionary of parsed outputs or None if parsing fails
        """
        raise NotImplementedError("Subclass must implement parse_output")

    # --- Optional Utility Methods ---

    def validate_executable(self, executable_path: str) -> bool:
        """
        Check if model executable exists and is runnable.
        
        Args:
            executable_path: Path to model executable

        Returns:
            bool: True if executable is valid
        """
        exe_path = Path(executable_path)
        return exe_path.exists() and exe_path.is_file() and os.access(exe_path, os.X_OK)

    def check_required_files(self, working_dir: str, required_files: list) -> bool:
        """
        Check if all required input files exist.
        
        Args:
            working_dir: Working directory containing input files
            required_files: List of required filenames

        Returns:
            bool: True if all files exist
        """
        work_path = Path(working_dir)
        return all((work_path / fname).exists() for fname in required_files)

    # Add other common utility methods as needed...
