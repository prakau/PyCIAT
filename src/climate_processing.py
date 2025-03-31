##############################################################################
### File: src/climate_processing.py
##############################################################################
"""
Functions for processing climate data from various sources (GCMs, RCMs).
Handles data loading, variable mapping, unit conversions, and point extraction.
"""

import logging
import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

from .utils import Timer, ensure_dir_exists, parse_date_string

logger = logging.getLogger(__name__)

def load_climate_data(source_path: str,
                     model: str,
                     scenario: str,
                     variables: List[str],
                     lat_range: Tuple[float, float],
                     lon_range: Tuple[float, float],
                     time_range: Optional[Tuple[str, str]] = None,
                     use_dask: bool = True) -> Optional[xr.Dataset]:
    """
    Load climate data from NetCDF/similar files with optional subsetting.

    Args:
        source_path: Base path to climate data
        model: Climate model name
        scenario: Scenario name (e.g., ssp245)
        variables: List of variables to load
        lat_range: (min_lat, max_lat) for spatial subsetting
        lon_range: (min_lon, max_lon) for spatial subsetting
        time_range: Optional (start_date, end_date) for temporal subsetting
        use_dask: Whether to use dask for lazy loading

    Returns:
        xr.Dataset: Combined dataset with requested variables
    """
    try:
        with Timer(f"Loading climate data for {model} {scenario}"):
            # Implementation would handle different source formats/structures
            # This is a placeholder assuming a specific directory structure
            data_dir = Path(source_path) / model / scenario
            if not data_dir.exists():
                raise FileNotFoundError(f"Climate data directory not found: {data_dir}")
            
            # Load each variable
            datasets = []
            for var in variables:
                # Example pattern - adjust based on actual file organization
                pattern = f"*{var}*.nc"
                var_files = list(data_dir.glob(pattern))
                if not var_files:
                    logger.warning(f"No files found for variable {var}")
                    continue
                
                # Load with proper chunking if using dask
                if use_dask:
                    ds = xr.open_mfdataset(
                        var_files,
                        chunks={'time': 'auto'},
                        parallel=True
                    )
                else:
                    ds = xr.open_mfdataset(var_files)
                
                # Subset spatially
                ds = ds.sel(
                    lat=slice(lat_range[0], lat_range[1]),
                    lon=slice(lon_range[0], lon_range[1])
                )
                
                # Subset temporally if specified
                if time_range:
                    ds = ds.sel(time=slice(time_range[0], time_range[1]))
                
                datasets.append(ds)
            
            # Merge all variables
            combined = xr.merge(datasets)
            return combined
    
    except Exception as e:
        logger.error(f"Error loading climate data: {e}")
        return None

def extract_point_data(dataset: xr.Dataset,
                      lat: float,
                      lon: float,
                      method: str = 'nearest') -> pd.DataFrame:
    """
    Extract time series for a single point from gridded data.

    Args:
        dataset: xarray Dataset with climate data
        lat: Latitude of point
        lon: Longitude of point
        method: Interpolation method ('nearest', 'linear', etc.)

    Returns:
        pd.DataFrame: Time series of all variables at point
    """
    try:
        # Extract point data
        point_data = dataset.sel(lat=lat, lon=lon, method=method)
        
        # Convert to DataFrame
        df = point_data.to_dataframe()
        
        # Reset index to get time as column
        df = df.reset_index()
        
        # Set time as index
        df = df.set_index('time')
        
        # Drop lat/lon columns if present
        df = df.drop(columns=['lat', 'lon'], errors='ignore')
        
        return df
    
    except Exception as e:
        logger.error(f"Error extracting point data at {lat}, {lon}: {e}")
        return pd.DataFrame()

def process_point_climate(df: pd.DataFrame,
                        output_vars: Dict[str, str],
                        unit_conversions: Optional[Dict[str, Callable]] = None) -> pd.DataFrame:
    """
    Process extracted point data (rename variables, convert units).

    Args:
        df: Input DataFrame with climate variables
        output_vars: Mapping of input to output variable names
        unit_conversions: Optional dict of conversion functions

    Returns:
        pd.DataFrame: Processed climate data
    """
    try:
        # Create copy to avoid modifying input
        processed = df.copy()
        
        # Rename variables according to mapping
        processed = processed.rename(columns=output_vars)
        
        # Apply unit conversions if specified
        if unit_conversions:
            for var, convert_func in unit_conversions.items():
                if var in processed.columns:
                    processed[var] = convert_func(processed[var])
        
        return processed
    
    except Exception as e:
        logger.error(f"Error processing point climate data: {e}")
        return df

def calculate_derived_variables(df: pd.DataFrame,
                              latitude: float,
                              required_vars: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Calculate derived variables (e.g., ET0, solar radiation if missing).

    Args:
        df: Input DataFrame with climate variables
        latitude: Latitude of point (for radiation calculations)
        required_vars: List of variables that must be calculated

    Returns:
        pd.DataFrame: Data with additional calculated variables
    """
    try:
        # Create copy to avoid modifying input
        result = df.copy()
        
        # Example: Calculate solar radiation if missing and required
        if 'rsds' not in result.columns and (not required_vars or 'rsds' in required_vars):
            logger.info("Calculating solar radiation from temperature and latitude")
            # Implementation would go here
            # result['rsds'] = calculate_solar_radiation(result, latitude)
        
        # Example: Calculate reference ET if needed
        if 'et0' not in result.columns and (not required_vars or 'et0' in required_vars):
            logger.info("Calculating reference evapotranspiration")
            # Implementation would go here
            # result['et0'] = calculate_et0(result)
        
        return result
    
    except Exception as e:
        logger.error(f"Error calculating derived variables: {e}")
        return df

def validate_climate_data(df: pd.DataFrame,
                        required_vars: List[str],
                        checks: Optional[Dict[str, Dict[str, float]]] = None) -> Tuple[bool, List[str]]:
    """
    Validate processed climate data for completeness and basic QC.

    Args:
        df: Climate DataFrame to validate
        required_vars: List of required variables
        checks: Optional dict of validation checks (e.g., min/max values)

    Returns:
        Tuple[bool, List[str]]: (is_valid, list of error messages)
    """
    errors = []
    
    # Check required variables exist
    missing = [var for var in required_vars if var not in df.columns]
    if missing:
        errors.append(f"Missing required variables: {missing}")
    
    # Check for missing values
    na_cols = df.columns[df.isna().any()].tolist()
    if na_cols:
        errors.append(f"Missing values found in columns: {na_cols}")
    
    # Apply range checks if specified
    if checks:
        for var, limits in checks.items():
            if var in df.columns:
                if 'min' in limits and (df[var] < limits['min']).any():
                    errors.append(f"{var} contains values below minimum {limits['min']}")
                if 'max' in limits and (df[var] > limits['max']).any():
                    errors.append(f"{var} contains values above maximum {limits['max']}")
    
    return len(errors) == 0, errors

# Add more functions as needed for specific processing requirements...
