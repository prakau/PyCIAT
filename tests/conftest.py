"""
Global pytest configuration and fixtures.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator

import pytest
import yaml

# Add project root to Python path
repo_root = str(Path(__file__).parent.parent)
sys.path.insert(0, repo_root)

@pytest.fixture
def test_config() -> Dict[str, Any]:
    """
    Provide a basic configuration dictionary for testing.

    Returns:
        Dict with test configuration settings
    """
    return {
        'base_dir': '/test/path',
        'name': 'test_study',
        'paths': {
            'locations_file': 'data/study_sites.csv',
            'soil_profiles': 'data/soil_profiles.json',
            'simulation_setup_dir': 'simulations/setup',
            'simulation_output_dir': 'simulations/output',
            'analysis_output_dir': 'analysis/results',
            'figure_output_dir': 'analysis/figures',
            'models_dir': 'models',
            'simulation_status_file': 'simulations/simulation_status.csv',
        },
        'crop_models_to_run': ['dssat', 'apsim'],
        'climate': {
            'active_sources': ['era5', 'cmip6'],
            'variables': ['tasmax', 'tasmin', 'pr', 'rsds'],
            'lat_range': [11.5, 18.5],
            'lon_range': [74.0, 78.5],
            'historical_period': ['1991-01-01', '2020-12-31'],
            'future_periods': {
                'near_future': ['2021-01-01', '2050-12-31'],
            }
        },
        'simulation': {
            'crop': 'maize',
            'sowing_dates': ['2020-06-15'],
            'fertilizer_n': 150,
            'irrigation': False,
        },
        'parallel': {
            'use_hpc_env_vars': False,
            'num_workers': 2
        }
    }

@pytest.fixture
def temp_config_file(test_config: Dict[str, Any]) -> Generator[str, None, None]:
    """
    Create a temporary configuration file.

    Args:
        test_config: Configuration dictionary

    Yields:
        Path to temporary config file
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
        yaml.safe_dump(test_config, temp_file)
        temp_path = temp_file.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass

@pytest.fixture
def temp_working_dir() -> Generator[Path, None, None]:
    """
    Create a temporary working directory.

    Yields:
        Path to temporary directory
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        orig_dir = os.getcwd()
        os.chdir(temp_dir)
        
        # Create basic directory structure
        for dir_name in [
            'data/climate',
            'data/soil',
            'simulations/setup',
            'simulations/output',
            'analysis/results',
            'analysis/figures',
            'models',
            'logs'
        ]:
            os.makedirs(dir_name)
        
        yield Path(temp_dir)
        
        # Restore original directory
        os.chdir(orig_dir)

@pytest.fixture
def sample_climate_data() -> Dict[str, Any]:
    """
    Provide sample climate data for testing.

    Returns:
        Dict with sample data
    """
    return {
        'tasmax': {
            'data': [[25.0, 26.0], [27.0, 28.0]],
            'dims': ['time', 'location'],
            'coords': {
                'time': ['2020-01-01', '2020-01-02'],
                'location': ['loc1', 'loc2']
            }
        },
        'tasmin': {
            'data': [[15.0, 16.0], [17.0, 18.0]],
            'dims': ['time', 'location'],
            'coords': {
                'time': ['2020-01-01', '2020-01-02'],
                'location': ['loc1', 'loc2']
            }
        },
        'pr': {
            'data': [[0.0, 1.0], [2.0, 3.0]],
            'dims': ['time', 'location'],
            'coords': {
                'time': ['2020-01-01', '2020-01-02'],
                'location': ['loc1', 'loc2']
            }
        }
    }

@pytest.fixture
def sample_simulation_status() -> Dict[str, Any]:
    """
    Provide sample simulation tracking data.

    Returns:
        Dict with sample tracking data
    """
    return {
        'simulation_id': ['sim001', 'sim002', 'sim003'],
        'status': ['SUCCESS', 'FAILED', 'READY_TO_RUN'],
        'message': ['Completed', 'Error in setup', ''],
        'start_time': ['2025-03-31 10:00:00', '2025-03-31 10:01:00', ''],
        'end_time': ['2025-03-31 10:05:00', '2025-03-31 10:02:00', ''],
        'location_id': ['loc1', 'loc2', 'loc3'],
        'crop_model': ['dssat', 'apsim', 'dssat']
    }
