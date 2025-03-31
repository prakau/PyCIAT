"""Tests for visualization functionality."""

import os
from pathlib import Path
from typing import Dict, Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

# Add project root to sys.path if needed
# import sys
# sys.path.insert(0, str(Path(__file__).parent.parent))

# Assuming visualization functions are in src.visualization
# Adjust import path if necessary
from src.visualization import (
    plot_spatial_impacts,
    plot_impact_boxplots,
    plot_adaptation_effectiveness,
    plot_ensemble_agreement,
    plot_time_series
)
# Import setup_figure_style if you want to test its effect
# from src.visualization import setup_figure_style

# Mock GeoDataFrame for spatial plots
class MockGeoDataFrame(pd.DataFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add a dummy geometry column if needed by the plot function
        # This might need adjustment based on how plot_spatial_impacts uses it
        if 'geometry' not in self.columns and not self.empty:
             # Create dummy points based on lat/lon if available
             if 'longitude' in self.columns and 'latitude' in self.columns:
                  try:
                       import geopandas as gpd
                       self['geometry'] = gpd.points_from_xy(self['longitude'], self['latitude'])
                  except ImportError:
                       self['geometry'] = None # Fallback if geopandas not installed
             else:
                  self['geometry'] = None


    def merge(self, *args, **kwargs):
        # Override merge to return a MockGeoDataFrame
        result = super().merge(*args, **kwargs)
        return MockGeoDataFrame(result)

    def plot(self, *args, **kwargs):
        # Mock the plot method to avoid actual plotting
        ax = kwargs.get('ax', plt.gca())
        # Simulate adding something to the plot for assertion checks
        ax.plot([0, 1], [0, 1], label='mock_plot')
        return ax


@pytest.fixture
def sample_impact_data() -> pd.DataFrame:
    """Create sample impact data for visualization testing."""
    np.random.seed(42)
    data = pd.DataFrame({
        'location_id': [f'loc_{i:02d}' for i in range(20)],
        'latitude': np.linspace(12.0, 15.0, 20),
        'longitude': np.linspace(75.0, 78.0, 20),
        'yield_change_mean': np.random.normal(-15, 10, 20),
        'yield_change_std': np.random.uniform(2, 8, 20),
        'yield_high_agreement': np.random.choice([True, False], 20),
        'scenario': ['ssp245', 'ssp585'] * 10,
        'period': ['near_future'] * 20
    })
    return data

@pytest.fixture
def sample_effectiveness_data() -> pd.DataFrame:
    """Create sample adaptation effectiveness data."""
    np.random.seed(42)
    data = pd.DataFrame({
        'adaptation': ['early_sowing', 'drip_irrigation', 'new_cultivar'] * 5,
        'mean_impact_reduction': np.random.normal(500, 200, 15),
        'impact_reduction_std': np.random.uniform(50, 150, 15),
        'significant': np.random.choice([True, False], 15, p=[0.7, 0.3])
    })
    return data

@pytest.fixture
def sample_time_series() -> pd.DataFrame:
    """Create sample time series data for visualization testing."""
    np.random.seed(42)
    years = np.arange(1991, 2051)
    data = pd.DataFrame({
        'year': years,
        'yield_mean': 4000 + np.random.normal(0, 200, len(years)) - 5 * (years - 1991),
        'yield_std': np.random.uniform(100, 300, len(years)),
        'scenario': ['historical'] * 30 + ['ssp245'] * 30
    })
    return data

@pytest.fixture
def mock_spatial_df(sample_impact_data) -> MockGeoDataFrame:
    """Create a mock GeoDataFrame for spatial plots."""
    # Use the sample impact data and convert to mock GeoDataFrame
    return MockGeoDataFrame(sample_impact_data)


def test_plot_spatial_impacts(sample_impact_data: pd.DataFrame, mock_spatial_df: MockGeoDataFrame, tmp_path: Path):
    """Test spatial impact map plotting."""
    output_file = tmp_path / "spatial_impact_map.png"
    plot_spatial_impacts(
        results=sample_impact_data,
        shape_df=mock_spatial_df,
        variable='yield_change_mean',
        output_path=str(output_file),
        title='Test Spatial Plot'
    )
    assert output_file.exists()
    plt.close('all')

def test_plot_impact_boxplots(sample_impact_data: pd.DataFrame, tmp_path: Path):
    """Test impact distribution boxplot."""
    output_file = tmp_path / "impact_boxplot.png"
    plot_impact_boxplots(
        data=sample_impact_data,
        variable='yield_change_mean',
        groupby='scenario',
        output_path=str(output_file),
        title='Test Boxplot'
    )
    assert output_file.exists()
    plt.close('all')

def test_plot_adaptation_effectiveness(sample_effectiveness_data: pd.DataFrame, tmp_path: Path):
    """Test adaptation effectiveness bar plot."""
    output_file = tmp_path / "adaptation_effectiveness.png"
    plot_adaptation_effectiveness(
        data=sample_effectiveness_data,
        output_path=str(output_file),
        title='Test Adaptation Plot'
    )
    assert output_file.exists()
    plt.close('all')

def test_plot_ensemble_agreement(sample_impact_data: pd.DataFrame, mock_spatial_df: MockGeoDataFrame, tmp_path: Path):
    """Test ensemble agreement plot."""
    output_file = tmp_path / "ensemble_agreement.png"
    # Ensure the agreement column exists for the test
    sample_impact_data['yield_high_agreement'] = sample_impact_data['yield_high_agreement'].astype(float) # Plotting might expect numeric

    plot_ensemble_agreement(
        data=sample_impact_data,
        variable='yield', # Base variable name
        shape_df=mock_spatial_df,
        output_path=str(output_file),
        title='Test Ensemble Agreement'
    )
    assert output_file.exists()
    plt.close('all')

def test_plot_time_series(sample_time_series: pd.DataFrame, tmp_path: Path):
    """Test time series plotting."""
    output_file = tmp_path / "time_series.png"
    plot_time_series(
        data=sample_time_series,
        x_column='year',
        y_column='yield_mean',
        output_path=str(output_file),
        title='Test Time Series'
    )
    assert output_file.exists()
    plt.close('all')

    # Test with grouping
    output_file_grouped = tmp_path / "time_series_grouped.png"
    plot_time_series(
        data=sample_time_series,
        x_column='year',
        y_column='yield_mean',
        groupby='scenario',
        output_path=str(output_file_grouped),
        title='Test Grouped Time Series'
    )
    assert output_file_grouped.exists()
    plt.close('all')

# Add tests for error handling, missing data, different plot options etc.
def test_plot_error_handling(tmp_path: Path):
    """Test error handling in plotting functions."""
    # Test with empty dataframe
    empty_df = pd.DataFrame()
    mock_empty_gdf = MockGeoDataFrame(empty_df)
    output_file = tmp_path / "empty.png"

    # Expect warnings or graceful handling, not necessarily errors depending on implementation
    # Using try-except blocks to check if functions run without crashing
    try:
        plot_spatial_impacts(empty_df, mock_empty_gdf, 'yield', str(output_file))
        plot_impact_boxplots(empty_df, 'yield', 'scenario', str(output_file))
        # plot_adaptation_effectiveness requires specific columns, might error if empty
        # plot_ensemble_agreement requires specific columns, might error if empty
        plot_time_series(empty_df, 'year', 'yield', str(output_file))
    except Exception as e:
        pytest.fail(f"Plotting function raised unexpected error on empty data: {e}")

    # Test with missing columns
    missing_cols_df = pd.DataFrame({'year': [2000, 2001]})
    try:
        plot_time_series(missing_cols_df, 'year', 'yield_mean', str(output_file))
        # Depending on implementation, this might raise KeyError or plot nothing
    except KeyError:
        pass # Expected if column is strictly required
    except Exception as e:
         pytest.fail(f"Plotting function raised unexpected error on missing columns: {e}")

    plt.close('all')
