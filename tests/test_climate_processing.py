"""Tests for climate data processing functionality."""

import os
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from src.climate_processing import (
    load_climate_data,
    validate_climate_data,
    extract_locations,
    compute_climate_statistics,
    prepare_model_inputs
)

def create_test_climate_data() -> xr.Dataset:
    """Create a test climate dataset."""
    # Create time and location coordinates
    times = pd.date_range('2020-01-01', '2020-12-31', freq='D')
    lats = np.array([12.0, 13.0, 14.0])
    lons = np.array([75.0, 76.0, 77.0])
    
    # Create sample data
    tasmax = np.random.normal(30, 5, size=(len(times), len(lats), len(lons)))
    tasmin = np.random.normal(20, 5, size=(len(times), len(lats), len(lons)))
    pr = np.random.exponential(5, size=(len(times), len(lats), len(lons)))
    
    # Create dataset
    ds = xr.Dataset(
        {
            'tasmax': (('time', 'latitude', 'longitude'), tasmax),
            'tasmin': (('time', 'latitude', 'longitude'), tasmin),
            'pr': (('time', 'latitude', 'longitude'), pr)
        },
        coords={
            'time': times,
            'latitude': lats,
            'longitude': lons
        }
    )
    
    return ds

def test_load_climate_data(tmp_path: Path, test_config: Dict[str, Any]):
    """Test loading climate data."""
    # Create test data
    ds = create_test_climate_data()
    
    # Save to netCDF file
    test_file = tmp_path / "test_climate.nc"
    ds.to_netcdf(test_file)
    
    # Test loading
    loaded_data = load_climate_data(
        file_path=str(test_file),
        variables=['tasmax', 'tasmin', 'pr']
    )
    
    assert isinstance(loaded_data, xr.Dataset)
    assert all(var in loaded_data.data_vars for var in ['tasmax', 'tasmin', 'pr'])
    assert loaded_data.dims['time'] == 366  # 2020 is leap year

def test_validate_climate_data():
    """Test climate data validation."""
    # Create valid data
    ds = create_test_climate_data()
    
    # Test valid data
    assert validate_climate_data(ds, required_vars=['tasmax', 'tasmin', 'pr'])
    
    # Test missing variable
    with pytest.raises(ValueError):
        validate_climate_data(ds, required_vars=['invalid_var'])
    
    # Test invalid values
    ds_invalid = ds.copy()
    ds_invalid['tasmax'].values[0, 0, 0] = 100  # Unrealistic temperature
    with pytest.raises(ValueError):
        validate_climate_data(
            ds_invalid,
            required_vars=['tasmax'],
            valid_ranges={'tasmax': (-50, 60)}
        )

def test_extract_locations(test_config: Dict[str, Any]):
    """Test location data extraction."""
    # Create test data
    ds = create_test_climate_data()
    
    # Create test locations
    locations = pd.DataFrame({
        'id': ['loc1', 'loc2'],
        'lat': [13.0, 14.0],
        'lon': [76.0, 77.0]
    })
    
    # Extract data
    extracted = extract_locations(
        data=ds,
        locations=locations,
        lat_col='lat',
        lon_col='lon'
    )
    
    assert isinstance(extracted, xr.Dataset)
    assert extracted.dims['location'] == 2
    assert all(var in extracted.data_vars for var in ['tasmax', 'tasmin', 'pr'])

def test_compute_climate_statistics():
    """Test computation of climate statistics."""
    # Create test data
    ds = create_test_climate_data()
    
    # Compute statistics
    stats = compute_climate_statistics(
        data=ds,
        variables=['tasmax', 'tasmin', 'pr'],
        freq='M'  # Monthly statistics
    )
    
    assert isinstance(stats, xr.Dataset)
    assert 'tasmax_mean' in stats.data_vars
    assert 'pr_sum' in stats.data_vars
    assert stats.dims['time'] == 12  # Monthly data

def test_prepare_model_inputs(temp_working_dir: Path):
    """Test preparation of model-specific climate inputs."""
    # Create test data
    ds = create_test_climate_data()
    
    # Create test location
    location = {
        'id': 'test_loc',
        'lat': 13.0,
        'lon': 76.0
    }
    
    # Prepare inputs
    output_file = prepare_model_inputs(
        data=ds,
        location=location,
        output_dir=temp_working_dir,
        model_type='dssat'
    )
    
    assert output_file.exists()
    assert output_file.suffix == '.WTH'  # DSSAT weather file

def test_climate_data_interpolation():
    """Test spatial interpolation of climate data."""
    # Create test data with gaps
    ds = create_test_climate_data()
    ds['tasmax'].values[0, 1, 1] = np.nan  # Create missing value
    
    # Create test location at point requiring interpolation
    location = pd.DataFrame({
        'id': ['loc1'],
        'lat': [13.5],  # Between grid points
        'lon': [76.5]   # Between grid points
    })
    
    # Extract with interpolation
    extracted = extract_locations(
        data=ds,
        locations=location,
        lat_col='lat',
        lon_col='lon',
        method='linear'  # Linear interpolation
    )
    
    assert not np.isnan(extracted['tasmax'].values).any()

def test_temporal_aggregation():
    """Test temporal aggregation of climate data."""
    # Create test data
    ds = create_test_climate_data()
    
    # Test different aggregation periods
    for freq in ['M', 'Y']:
        stats = compute_climate_statistics(
            data=ds,
            variables=['tasmax', 'tasmin', 'pr'],
            freq=freq
        )
        
        expected_periods = 12 if freq == 'M' else 1
        assert stats.dims['time'] == expected_periods

def test_variable_derivation():
    """Test derivation of additional variables."""
    # Create test data
    ds = create_test_climate_data()
    
    # Add derived variable (e.g., daily temperature range)
    ds['dtr'] = ds['tasmax'] - ds['tasmin']
    
    # Validate new variable
    assert 'dtr' in ds.data_vars
    assert not np.isnan(ds['dtr'].values).any()
    assert (ds['dtr'].values >= 0).all()  # DTR should be positive

def test_error_handling():
    """Test error handling in climate processing."""
    ds = create_test_climate_data()
    
    # Test invalid frequency
    with pytest.raises(ValueError):
        compute_climate_statistics(
            data=ds,
            variables=['tasmax'],
            freq='invalid'
        )
    
    # Test invalid interpolation method
    locations = pd.DataFrame({'id': ['loc1'], 'lat': [13.5], 'lon': [76.5]})
    with pytest.raises(ValueError):
        extract_locations(
            data=ds,
            locations=locations,
            lat_col='lat',
            lon_col='lon',
            method='invalid'
        )
