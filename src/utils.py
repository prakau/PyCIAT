##############################################################################
### File: src/utils.py
##############################################################################
"""
Utility functions used across the modeling framework.
Provides common functionality for file handling, logging, and other shared operations.
"""

import os
import sys
import time
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable
import pandas as pd
import numpy as np

def setup_logging(log_file: Optional[str] = None,
                 level: str = "INFO",
                 format_str: Optional[str] = None) -> None:
    """
    Sets up logging configuration for the framework.

    Args:
        log_file: Path to log file (None for console only)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_str: Custom format string for log messages
    """
    if format_str is None:
        format_str = "%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s"

    handlers = []
    
    # Always add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(format_str))
    handlers.append(console_handler)
    
    # Add file handler if log_file specified
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            ensure_dir_exists(log_dir)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(format_str))
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers,
        force=True  # Override any existing handlers
    )

def ensure_dir_exists(directory: Union[str, Path]) -> None:
    """
    Creates directory if it doesn't exist.

    Args:
        directory: Path to directory
    """
    Path(directory).mkdir(parents=True, exist_ok=True)

class Timer:
    """Context manager for timing code blocks."""
    
    def __init__(self, description: str = "Operation"):
        """
        Args:
            description: Description of the operation being timed
        """
        self.description = description
        self.logger = logging.getLogger(__name__)

    def __enter__(self) -> 'Timer':
        self.start = time.time()
        return self

    def __exit__(self, *args: Any) -> None:
        self.end = time.time()
        self.duration = self.end - self.start
        self.logger.info(f"{self.description} completed in {self.duration:.2f} seconds")

def safe_file_copy(src: Union[str, Path],
                   dst: Union[str, Path],
                   overwrite: bool = False) -> bool:
    """
    Safely copy a file with error handling.

    Args:
        src: Source file path
        dst: Destination file path
        overwrite: Whether to overwrite existing files

    Returns:
        bool: True if copy successful
    """
    try:
        if not overwrite and os.path.exists(dst):
            return False
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Error copying {src} to {dst}: {e}")
        return False

def parse_date_string(date_str: str) -> datetime:
    """
    Parses date string in various formats.

    Args:
        date_str: Date string (e.g., "2024-01-01", "20240101")

    Returns:
        datetime: Parsed datetime object

    Raises:
        ValueError: If date string cannot be parsed
    """
    formats = [
        "%Y-%m-%d",
        "%Y%m%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Could not parse date string: {date_str}")

def check_required_columns(df: pd.DataFrame,
                         required_cols: List[str],
                         df_name: str = "DataFrame") -> None:
    """
    Checks if DataFrame has required columns.

    Args:
        df: DataFrame to check
        required_cols: List of required column names
        df_name: Name of DataFrame for error messages

    Raises:
        ValueError: If any required columns are missing
    """
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"{df_name} missing required columns: {missing}")

def ensure_numeric(df: pd.DataFrame,
                  columns: List[str],
                  errors: str = 'coerce') -> pd.DataFrame:
    """
    Ensures specified columns are numeric, with optional error handling.

    Args:
        df: DataFrame to process
        columns: List of columns to convert
        errors: How to handle errors ('raise', 'coerce', 'ignore')

    Returns:
        DataFrame with numeric columns
    """
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors=errors)
    return df

def calculate_growing_season_climate(daily_data: pd.DataFrame,
                                  start_date: Union[str, datetime],
                                  end_date: Union[str, datetime]) -> Dict[str, float]:
    """
    Calculates climate statistics for a growing season period.

    Args:
        daily_data: DataFrame with daily climate data
        start_date: Start date of growing season
        end_date: End date of growing season

    Returns:
        Dict of climate statistics
    """
    # Convert dates if needed
    if isinstance(start_date, str):
        start_date = parse_date_string(start_date)
    if isinstance(end_date, str):
        end_date = parse_date_string(end_date)
    
    # Filter to growing season
    mask = (daily_data.index >= start_date) & (daily_data.index <= end_date)
    season_data = daily_data[mask]
    
    # Calculate statistics
    stats = {
        'GrowingDays': len(season_data),
        'TotalPrecip_mm': season_data['pr'].sum() if 'pr' in season_data else np.nan,
        'AvgTmax_C': season_data['tasmax'].mean() if 'tasmax' in season_data else np.nan,
        'AvgTmin_C': season_data['tasmin'].mean() if 'tasmin' in season_data else np.nan,
        'TotalRad_MJ': season_data['rsds'].sum() if 'rsds' in season_data else np.nan,
    }
    
    return stats

def retry_with_backoff(func: Callable,
                      max_tries: int = 3,
                      initial_delay: float = 1.0,
                      backoff_factor: float = 2.0,
                      exceptions: tuple = (Exception,)) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        func: Function to retry
        max_tries: Maximum number of attempts
        initial_delay: Initial delay between retries (seconds)
        backoff_factor: Factor to increase delay by each retry
        exceptions: Tuple of exceptions to catch

    Returns:
        Wrapped function with retry logic
    """
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_tries):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt + 1 == max_tries:
                    break
                
                logging.getLogger(__name__).warning(
                    f"Attempt {attempt + 1}/{max_tries} failed: {e}. "
                    f"Retrying in {delay:.1f} seconds..."
                )
                
                time.sleep(delay)
                delay *= backoff_factor
        
        raise last_exception
    
    return wrapper

# Add more utility functions as needed...
